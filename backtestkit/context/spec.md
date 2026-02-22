# Specification — Historical Backtesting Engine + Signal Generator

---

## Overview

This project is a **deterministic historical backtesting engine** paired with a **modular signal generator**. The engine is strategy-agnostic — it receives signals and executes them faithfully against historical data. Any strategy that implements the `BaseStrategy` interface can plug into it.

The first strategy being developed is **MA Crossover (MSA)**, but the architecture supports unlimited future strategies without modifying the engine.

**Key principles:**
- No real-time execution — historical simulation only
- No lookahead bias — signal at candle `i` executes at candle `i+1` open
- Fully deterministic — same input always produces identical output
- Worst-case assumptions — when ambiguity exists (both SL and TP hit), assume the worse outcome
- Everything is rule-based — no hidden logic, no implicit behavior

---

## Project Structure

```
backtestkit/
├── backtester/                     # Strategy-agnostic execution engine
│   ├── engine.py                   # Main simulation loop
│   ├── execution_modes.py          # Price resolution per mode
│   ├── portfolio.py                # Capital accounting
│   ├── sl_tp.py                    # Stop loss / take profit engine
│   ├── metrics.py                  # Performance calculations
│   └── visualization.py           # Charts
├── strategies/                     # Trading strategies (MA Crossover, future strategies)
│   ├── base_strategy.py            # Abstract interface (all strategies extend this)
│   ├── ma_crossover.py             # MA Crossover implementation
│   └── signals.py                  # Signal dataclass
├── common/                         # Shared across engine and strategies
│   ├── models.py                   # Enums (ExecutionMode, SignalType)
│   └── data_loader.py             # CSV loading, OHLC resampling
├── data/
│   └── nas100_m1_mid_test.csv
├── context/                        # Project documentation
├── summaries/                      # Phase completion summaries
├── tests/
│   ├── test_data_loader.py         # Phase 1 tests (38)
│   ├── test_strategy.py            # Phase 2 tests (32)
│   └── (future test files)
└── run_backtest.py                 # CLI entry point (future)
```

---

## Part I — Backtester Engine

The backtester is **completely independent** of any strategy. It receives:
- Historical OHLC data (DataFrame)
- A list of `Signal` objects ("class Signal:
    timestamp_index: int
    signal_type: SignalType ->long/short/close
    stop_loss_level: float
    take_profit_level: float
    size: float
)
- Configuration (execution mode, initial capital)

It does not know or care which strategy produced the signals.

### 1. Input Data

The engine operates on **1-minute mid-price OHLC candles** with spread:

| Column | Description |
|---|---|
| `timestamp` | DatetimeIndex, 1-minute frequency |
| `open` | Mid-price open |
| `high` | Mid-price high |
| `low` | Mid-price low |
| `close` | Mid-price close |
| `spread` | `ask - bid` for that candle |

Mid-price = `(bid + ask) / 2`

### 2. Execution Modes

Three transaction cost models are supported:

**Mode A — Spread ON (realistic)**
- LONG entry = `mid + spread/2` (buy at ask), exit = `mid - spread/2` (sell at bid)
- SHORT entry = `mid - spread/2` (sell at bid), exit = `mid + spread/2` (buy at ask)
- Fee = 0
- Entering and immediately exiting results in a loss equal to the full spread

**Mode B — Spread OFF (fee-based)**
- Entry and exit at mid-price (no spread adjustment)
- Fee = 0.1% of position value, applied on both entry and exit

**Mode C — Static Custom Spread**
- Same logic as Mode A, but `spread` is replaced by a user-defined constant
- Fee = 0

### 3. Trading Constraints

- No leverage
- Single instrument at a time
- **Strategy controls allocation** — the engine does not impose any allocation cap. If the strategy says `size=1.0`, the engine allocates 100% of available cash
- Position stacking allowed (additive): two LONG signals = doubled position, with weighted average entry price
- Cannot exceed available cash

### 4. Execution Timing

Strict signal delay rule:
- Strategy emits signal at candle index `i`
- Engine executes at **open of candle `i+1`**
- No same-candle execution ever

### 5. Stop Loss / Take Profit

SL and TP levels are defined per signal and remain fixed per position unit.

Default calculation (MA Crossover):
- LONG: SL = `close * (1 - sl_pct)`, TP = `close * (1 + tp_pct)`
- SHORT: SL = `close * (1 + sl_pct)`, TP = `close * (1 - tp_pct)`

Default `sl_pct` and `tp_pct` = 0.02 (2%).

### 6. Intrabar SL/TP Evaluation

For each candle, evaluate:

**LONG position:**
- SL hit if `candle.low <= SL_level`
- TP hit if `candle.high >= TP_level`

**SHORT position:**
- SL hit if `candle.high >= SL_level`
- TP hit if `candle.low <= TP_level`

**If both trigger on the same candle:** SL executes (worst-case assumption). This prevents unrealistic profit bias.

**SL/TP execution prices (Mode A):**
- LONG SL/TP exit at `level - spread/2` (sold at bid)
- SHORT SL/TP exit at `level + spread/2` (bought at ask)

### 7. Engine Loop (per candle)

Strict execution order:

```
1. Update unrealized PnL
2. Check SL/TP for each position unit → execute if hit
3. Execute pending signals from previous candle (CLOSE first, then entries)
4. Collect new signals at this candle index → store as pending
5. Record state snapshot (cash, position, equity)
```

Multiple signals can share the same candle index (e.g., CLOSE + LONG on reversal). They are processed in list order.

### 8. Capital Accounting

**State variables:**

| Variable | Meaning |
|---|---|
| `cash` | Free capital not in positions |
| `position_size` | Units held (positive = long, negative = short, zero = flat) |
| `avg_entry_price` | Weighted average entry price across stacked entries |
| `realized_pnl` | Cumulative closed trade profit/loss |
| `unrealized_pnl` | Current open position profit/loss |
| `position_notional` | Capital locked in position: `abs(position_size) * avg_entry_price` |
| `equity` | `cash + position_notional + unrealized_pnl` (total account value) |

**Position opening:**
- `allocation = cash * signal.size`
- `units = allocation / entry_price`
- Cash reduced by allocation amount

**Position stacking:**
- `new_avg = (old_avg * old_size + new_price * new_size) / (old_size + new_size)`

**Position closing (CLOSE signal):**
- `signal.size` = fraction of position to close (1.0 = full, 0.5 = half)
- Realized PnL credited to cash on close

### 9. PnL Formulas

**Unrealized (mark-to-market):**
- LONG: `(current_bid - avg_entry_price) * position_size`
- SHORT: `(avg_entry_price - current_ask) * abs(position_size)`

Bid = `mid - spread/2`, Ask = `mid + spread/2`

### 10. CLOSE Signal

The CLOSE signal closes a fraction (or all) of the current position:
- `CLOSE` with `size=1.0` = close entire position
- `CLOSE` with `size=0.5` = close half the position (future strategies)
- CLOSE signals have `stop_loss_level=0.0` and `take_profit_level=0.0`
- Execution: close at next candle open, apply spread/fees, update realized PnL

### 11. Performance Metrics

Computed after simulation completes:

| Metric | Formula |
|---|---|
| Total Return | `(final_equity - initial_capital) / initial_capital` |
| Annualized Return | `(1 + total_return) ^ (252*390 / total_candles) - 1` |
| Max Drawdown | `max((peak - equity) / peak)` over the equity curve |
| Sharpe Ratio | `mean(returns) / std(returns) * sqrt(252*390)` (annualized from 1-min) |
| Win Rate | `winning_trades / total_trades` |
| Profit Factor | `sum(winning_pnl) / abs(sum(losing_pnl))` |
| Avg Trade | `total_realized_pnl / total_trades` |
| Total Trades | Count of completed round-trips |
| Exposure Time | `candles_with_position / total_candles` |

### 12. Visualization

Four charts generated via matplotlib:
1. **Equity curve** — equity over time (line plot)
2. **Drawdown curve** — drawdown % over time (filled area)
3. **Price chart with markers** — close price + buy (green triangle up), sell (red triangle down), SL hit (red X), TP hit (green star)
4. **Trade distribution histogram** — per-trade PnL

### 13. Console Logging

Engine prints trade events during simulation:
```
[2024-01-15 09:31] BUY 100 units at 150.25 (spread mode, ask=150.50)
[2024-01-15 10:14] STOP LOSS hit at 147.25 — closed 100 units, PnL: -3.00
[2024-01-15 11:02] SELL 95 units at 152.10 (spread mode, bid=151.85)
[2024-01-15 14:30] TAKE PROFIT hit at 155.00 — closed 95 units, PnL: +2.75
[2024-01-15 14:30] CLOSE at 148.50 — closed 95 units (100%), PnL: -1.20
```

Configurable verbosity: `silent` | `normal` | `debug`

---

## Part II — Strategy Module

### Architecture

The backtester accepts signals from **any strategy** that implements the `BaseStrategy` interface:

```python
class BaseStrategy(ABC):
    @abstractmethod
    def generate(self, df: pd.DataFrame) -> List[Signal]:
        ...
```

A strategy:
- Receives OHLC data (any timeframe)
- Returns a list of `Signal` objects
- Does **not** know about cash, positions, or PnL
- Does **not** execute trades — only produces signals
- Controls both **direction** (LONG/SHORT/CLOSE) and **sizing** (via `signal.size`)

### Signal Format

```python
@dataclass
class Signal:
    timestamp_index: int      # candle index where signal was generated
    signal_type: SignalType   # LONG | SHORT | CLOSE
    stop_loss_level: float    # 0.0 for CLOSE signals
    take_profit_level: float  # 0.0 for CLOSE signals
    size: float               # fraction of available cash (entries) or position (closes)
```

- `size=1.0` on LONG/SHORT means 100% of available cash
- `size=1.0` on CLOSE means close the entire position
- `size=0.5` on CLOSE means close half (for future strategies that support partial exits)

### Current Strategy: MA Crossover (MSA)

The first implemented strategy. Located in `strategies/`. Future strategies (RSI, Bollinger, etc.) will also live in this package.

**Parameters:**
- `fast_period` (default: 10) — fast moving average window
- `slow_period` (default: 30) — slow moving average window
- `sl_pct` (default: 0.02) — stop loss percentage from close
- `tp_pct` (default: 0.02) — take profit percentage from close

**Signal rules:**
- Fast MA crosses above slow MA → LONG signal
- Fast MA crosses below slow MA → SHORT signal
- On reversal (e.g., was LONG, now SHORT): emits CLOSE(size=1.0) + new direction(size=1.0) at the same candle index
- First entry: direction only, no CLOSE needed
- Always uses `size=1.0` (full allocation)
- Tracks its own `last_direction` to detect reversals

**Multi-timeframe support:** The data loader can resample 1m data to 5m, 15m, 30m, 60m. Strategies can operate on any timeframe. Execution is always based on 1-minute data.

### Future Strategies

Any new strategy just needs to:
1. Extend `BaseStrategy`
2. Implement `generate(df) -> List[Signal]`
3. Be placed in the `strategies/` package (e.g., `strategies/rsi_strategy.py`, `strategies/bollinger_strategy.py`)

The engine requires zero modifications to support new strategies.

---

## System Integration Flow

```
1. Load 1-minute CSV data
2. (Optional) Resample to desired timeframe(s)
3. Strategy processes data → produces List[Signal]
4. Backtester receives data + signals + config
5. Backtester runs deterministic simulation
6. Metrics computed, charts generated, log printed
```

---

## Explicit Design Decisions

These are explicitly defined to prevent ambiguity:

| Question | Decision |
|---|---|
| Unrealized PnL: bid or mid? | **Bid for LONG**, **Ask for SHORT** — consistent with exit price |
| Capital rounding | No rounding during simulation. Round to 2 decimals only in final report |
| Execution order per candle | Unrealized PnL → SL/TP check → SL/TP execute → Signal execute → State update |
| Stacking logic | Additive size, weighted average entry, independent SL/TP per unit |
| Spread application | Entry: pay the spread (buy at ask, sell at bid). Exit: same. |
| Position size unit | Fractional units allowed (float) |
| Opposite signal handling | Strategy emits CLOSE(size=1.0) + new direction at same candle. Engine processes in order. |
| Who controls sizing? | **The strategy**, via `signal.size`. Engine has no allocation cap. |
| What does size mean? | LONG/SHORT: fraction of available cash. CLOSE: fraction of position to close. |
| SL/TP execution price | At SL/TP level ± spread/2 (not at candle open) |
| Multiple signals per candle | Allowed. Processed in list order (CLOSE first, then entry). |
| Opposite-direction stacking | **Rejected** — `open_position()` raises `ValueError` if direction opposes current position. Strategy must emit CLOSE first. Prevents silent accounting corruption from blending long/short entries into a meaningless weighted average. |

# Implementation Plan — Historical Backtesting Engine + Signal Generator

## Master Checklist

### Phase 1: Project Scaffolding & Data Layer
- [x] 1.1 Initialize Python project structure (`pyproject.toml`, virtual env)
- [x] 1.2 Create `backtester/` package skeleton (`__init__.py`, modules)
- [x] 1.3 Create `strategies/` package skeleton (`__init__.py`, modules)
- [x] 1.4 Define shared data models / types (`models.py`)
- [x] 1.5 Build data loader — read 1-min OHLC CSV into DataFrame -> test
- [x] 1.6 Build multi-timeframe resampler (1m → 5m, 15m, 30m, 60m) -> test
- [x] 1.7 Add sample/test CSV data for development

### Phase 2: Signal Generator (strategies/ — supports multiple strategies)
- [x] 2.1 Define signal output dataclass (`Signal`: timestamp_index, signal_type, sl_level, tp_level, size)
- [x] 2.2 Implement base strategy interface / abstract class
- [x] 2.3 Implement MA Crossover strategy (fast MA / slow MA, configurable periods)
- [x] 2.4 Implement crossover detection logic (cross above → LONG, cross below → SHORT)
- [x] 2.5 Implement SL/TP level calculation (entry ± 2%)
- [x] 2.6 Implement edge case: only first valid signal per candle
- [x] 2.7 Implement CLOSE signal emission on reversal (CLOSE + new direction at same candle)
- [x] 2.8 Unit tests for signal generator

### Phase 3: Backtester Core — Execution Modes
- [x] 3.1 Define execution mode enum (SPREAD_ON, SPREAD_OFF, STATIC_SPREAD)
- [x] 3.2 Implement Mode A — Spread ON (bid/ask from mid ± spread/2)
- [x] 3.3 Implement Mode B — Spread OFF (flat 0.1% fee on entry + exit)
- [x] 3.4 Implement Mode C — Static Custom Spread (user-defined constant spread)
- [x] 3.5 Build price resolver module that returns correct entry/exit prices per mode and direction
- [x] 3.6 Unit tests for each execution mode's price calculations

### Phase 4: Backtester Core — Capital Accounting
- [x] 4.1 Define portfolio state dataclass (`cash`, `position_size`, `avg_entry_price`, `realized_pnl`, `unrealized_pnl`, `equity`)
- [x] 4.2 Implement position opening logic (allocation = cash * signal.size, no engine cap)
- [x] 4.3 Implement position stacking logic (additive sizing, weighted avg entry price recalculation)
- [x] 4.4 Implement position closing logic (CLOSE signal: close signal.size fraction of position)
- [x] 4.5 Implement reversal handling (engine processes CLOSE + direction signals in order)
- [x] 4.6 Implement unrealized PnL formulas (long: bid-based, short: ask-based)
- [x] 4.7 Implement realized PnL tracking on every close
- [x] 4.8 Implement equity calculation (`cash + position_notional + unrealized_pnl`)
- [x] 4.9 Unit tests for capital accounting

### Phase 5: Backtester Core — SL/TP Engine
- [ ] 5.1 Implement per-position-unit SL/TP level storage
- [ ] 5.2 Implement intrabar SL check (LONG: low <= SL, SHORT: high >= SL)
- [ ] 5.3 Implement intrabar TP check (LONG: high >= TP, SHORT: low <= TP)
- [ ] 5.4 Implement worst-case rule: if both triggered in same candle → SL executes first
- [ ] 5.5 Implement SL/TP execution price with spread logic
- [ ] 5.6 Unit tests for SL/TP edge cases (both triggered, exact boundary hits)

### Phase 6: Backtester Core — Main Engine Loop
- [ ] 6.1 Implement signal-to-execution delay (signal at candle `i` → execute at open of `i+1`)
- [ ] 6.2 Implement the main loop with strict ordering:
  - 6.2.1 Update unrealized PnL
  - 6.2.2 Check SL/TP conditions
  - 6.2.3 Execute SL/TP if hit
  - 6.2.4 Execute pending signals in order (CLOSE first, then directional entry)
  - 6.2.5 Update cash, position size, equity
- [ ] 6.3 Implement CLOSE signal handling (partial/full close based on signal.size)
- [ ] 6.4 Implement per-candle state snapshot recording (for equity curve, etc.)
- [ ] 6.5 Integration test: full loop with known data and expected results

### Phase 7: Console Logging
- [ ] 7.1 Implement structured log messages:
  - `BUY at ...`
  - `SELL at ...`
  - `STOP LOSS hit at ...`
  - `TAKE PROFIT hit at ...`
  - `CLOSE at ...`
- [ ] 7.2 Add configurable verbosity level (silent / normal / debug)

### Phase 8: Performance Metrics
- [ ] 8.1 Implement Total Return calculation
- [ ] 8.2 Implement Annualized Return calculation
- [ ] 8.3 Implement Max Drawdown calculation (from equity curve)
- [ ] 8.4 Implement Sharpe Ratio calculation
- [ ] 8.5 Implement Win Rate calculation
- [ ] 8.6 Implement Profit Factor calculation
- [ ] 8.7 Implement Average Trade PnL calculation
- [ ] 8.8 Implement Total Trades count
- [ ] 8.9 Implement Exposure Time calculation (% of time in market)
- [ ] 8.10 Build metrics summary report (print + return as dict)
- [ ] 8.11 Unit tests for metric calculations against known values

### Phase 9: Visualization
- [ ] 9.1 Implement equity curve plot
- [ ] 9.2 Implement drawdown curve plot
- [ ] 9.3 Implement price chart with buy/sell markers, SL hit markers, TP hit markers
- [ ] 9.4 Implement trade distribution histogram (PnL per trade)
- [ ] 9.5 Build combined dashboard layout (subplots or multi-figure)
- [ ] 9.6 Add save-to-file option (PNG/HTML)

### Phase 10: System Integration & Runner
- [ ] 10.1 Build main runner script (`run_backtest.py`) that wires everything:
  - Load data
  - Run strategy → signals
  - Feed signals + data into backtester
  - Print metrics
  - Show/save charts
- [ ] 10.2 Add CLI argument support (data path, mode, MA periods, initial capital, etc.)
- [ ] 10.3 Add configuration file support (YAML/JSON)
- [ ] 10.4 End-to-end integration test with sample data

### Phase 11: Validation & Hardening
- [ ] 11.1 Determinism validation (same input → identical output, run twice and diff)
- [ ] 11.2 No-lookahead-bias audit (review all data access patterns)
- [ ] 11.3 Edge case testing: zero trades, single trade, all SL hits, all TP hits
- [ ] 11.4 Edge case testing: position stacking to capital exhaustion
- [ ] 11.5 Edge case testing: signals on last candle, empty signal list
- [ ] 11.6 Floating-point precision review (rounding rules for capital)

---

## Detailed Phase Breakdown

---

### Phase 1: Project Scaffolding & Data Layer

**Goal:** Establish the project structure, dependencies, and data ingestion pipeline.

**Files to create:**
```
backtestkit/
├── pyproject.toml
├── requirements.txt
├── run_backtest.py              (entry point — stubbed)
├── backtester/
│   ├── __init__.py
│   ├── engine.py                (main loop — stubbed)
│   ├── execution_modes.py       (price resolution)
│   ├── portfolio.py             (capital accounting)
│   ├── sl_tp.py                 (stop loss / take profit)
│   ├── metrics.py               (performance calculations)
│   └── visualization.py         (charts)
├── strategies/
│   ├── __init__.py
│   ├── base_strategy.py         (abstract interface)
│   ├── ma_crossover.py          (MA crossover implementation)
│   └── signals.py               (signal dataclass)
├── common/
│   ├── __init__.py
│   ├── models.py                (shared types, enums)
│   └── data_loader.py           (CSV loading, resampling)
├── data/
│   └── nas100_m1_mid_test.csv   (test data)
├── summaries/
│   └── phase1.md
└── tests/
    ├── __init__.py
    ├── test_data_loader.py
    ├── test_strategy.py
    ├── test_execution_modes.py
    ├── test_portfolio.py
    ├── test_sl_tp.py
    ├── test_metrics.py
    ├── test_engine.py
    └── manual/
        └── manualtest_data_loader.py
```

**Dependencies:** `pandas`, `numpy`, `matplotlib`, `pytest`

**Data loader responsibilities:**
- Read CSV with columns: `timestamp, open, high, low, close, spread`
- Validate no missing values, correct dtypes
- Set timestamp as DatetimeIndex
- Resample 1m → 5m, 15m, 30m, 60m using standard OHLC aggregation (open=first, high=max, low=min, close=last, spread=mean)

---

### Phase 2: Signal Generator (strategies/ — supports multiple strategies)

**Goal:** Produce a list of `Signal` objects from historical multi-timeframe OHLC data. Each signal carries both **direction** (LONG/SHORT/CLOSE) and **sizing** (percentage of available cash or position).

**Two-phase strategy design:**
1. **Direction model** — decides LONG, SHORT, or CLOSE
2. **Sizing model** — decides what percentage of available cash to allocate (for entries) or what percentage of position to close (for CLOSE signals)

Both phases are the strategy's responsibility. The engine does not impose allocation caps — it executes exactly the size the strategy requests.

**Signal dataclass:**
```python
@dataclass
class Signal:
    timestamp_index: int      # candle index in 1m DataFrame
    signal_type: SignalType   # LONG | SHORT | CLOSE
    stop_loss_level: float
    take_profit_level: float
    size: float               # 0.0–1.0: % of available cash (LONG/SHORT) or % of position (CLOSE)
```

**MA Crossover logic:**
- Compute fast MA and slow MA on the chosen timeframe (default: 1m)
- Detect crossover: `fast[i-1] <= slow[i-1]` AND `fast[i] > slow[i]` → LONG
- Detect crossunder: `fast[i-1] >= slow[i-1]` AND `fast[i] < slow[i]` → SHORT
- SL/TP levels are computed relative to the **close price at signal candle** (approximation of expected entry): `close ± 2%`
- On **reversal** (direction change), the strategy emits **two signals at the same candle index**: a CLOSE(size=1.0) followed by the new direction signal. The engine processes CLOSE first, then the entry — both execute at candle i+1 open.
- First entry has no CLOSE (no position to close yet)
- MA Crossover always uses **size=1.0** (100% of available cash)
- Strategy has **no knowledge** of cash, position state, or PnL (but tracks its own last emitted direction to know when to emit CLOSE)

---

### Phase 3: Execution Modes

**Goal:** Build a price resolver that computes exact entry/exit prices depending on mode and direction.

**Interface:**
```python
def resolve_entry_price(mid_price: float, spread: float, direction: str, mode: ExecutionMode) -> float
def resolve_exit_price(mid_price: float, spread: float, direction: str, mode: ExecutionMode) -> float
def calculate_fee(position_value: float, mode: ExecutionMode) -> float
```

**Mode A (SPREAD_ON):**
- LONG entry = mid + spread/2, exit = mid - spread/2
- SHORT entry = mid - spread/2, exit = mid + spread/2
- Fee = 0

**Mode B (SPREAD_OFF):**
- Entry = mid, Exit = mid
- Fee = 0.1% of position value (applied on entry AND exit)

**Mode C (STATIC_SPREAD):**
- Same as Mode A but `spread` replaced with user-defined constant
- Fee = 0

---

### Phase 4: Capital Accounting

**Goal:** Track all financial state throughout the simulation.

**Portfolio state:**
```python
@dataclass
class PortfolioState:
    cash: float
    position_size: float          # +N = long, -N = short, 0 = flat
    avg_entry_price: float
    realized_pnl: float
    unrealized_pnl: float
    position_notional: float      # abs(position_size) * avg_entry_price
    equity: float                 # cash + position_notional + unrealized_pnl
```

**Key rules:**
- Allocation per trade is determined by the signal's `size` field: `allocation = cash * signal.size`
- Position size in units = `(cash * signal.size) / entry_price`
- The engine does **not** impose any cap — the strategy has full control over sizing
- Stacking: new entry adds to `position_size`, `avg_entry_price` recalculated as weighted average
- On CLOSE signal: closes `signal.size` fraction of position (1.0 = full close, 0.5 = half). Realized PnL credited to cash.
- Reversal: strategy emits CLOSE(size=1.0) + opposite direction at same candle. Engine processes CLOSE first (returns cash), then opens new position with fresh capital.

**Weighted average entry on stacking:**
```
new_avg = (old_avg * old_size + new_price * new_size) / (old_size + new_size)
```

---

### Phase 5: SL/TP Engine

**Goal:** Evaluate stop loss and take profit conditions per candle, per position unit.

**Per-position tracking:** Each "unit" (entry event) has its own SL and TP level. When stacking, each layer has independent SL/TP.

**Intrabar evaluation order:**
1. Check SL condition first
2. Check TP condition second
3. If **both** triggered on same candle → **SL executes** (worst-case assumption)

**SL/TP execution prices (Mode A):**
- LONG SL hit → exit at `SL_level - spread/2` (sold at bid)
- LONG TP hit → exit at `TP_level - spread/2` (sold at bid)
- SHORT SL hit → exit at `SL_level + spread/2` (bought at ask)
- SHORT TP hit → exit at `TP_level + spread/2` (bought at ask)

**Design decision:** Store position as a list of `PositionUnit` objects, each with its own entry price, size, SL, and TP. When SL/TP fires, only that unit is closed.

---

### Phase 6: Main Engine Loop

**Goal:** The deterministic core — iterate over every 1-min candle and execute the simulation.

**Pseudocode:**
```
pending_signals = []

for i in range(len(candles)):
    candle = candles[i]

    # Step 1: Update unrealized PnL using current candle's prices
    update_unrealized_pnl(portfolio, candle, mode)

    # Step 2: Check and execute SL/TP for each position unit
    for unit in position_units:
        check_and_execute_sl_tp(unit, candle, portfolio, mode)

    # Step 3: Execute pending signals (from previous candle)
    # Multiple signals may share the same candle index (e.g. CLOSE + LONG on reversal)
    # They are processed in order: CLOSE first, then directional entry
    for sig in pending_signals:
        execute_signal(sig, candle.open, candle.spread, portfolio, mode)
    pending_signals = []

    # Step 4: Collect all signals at this candle index
    pending_signals = get_signals_at(i)  # will execute at i+1

    # Step 5: Record snapshot
    record_snapshot(i, portfolio, candle)
```

**Critical invariant:** Signals at candle `i` are stored, then executed at candle `i+1` open. No same-candle execution. Multiple signals at the same index are processed in list order (CLOSE before directional entry).

---

### Phase 7: Console Logging

**Goal:** Human-readable trade log printed during simulation.

**Format examples:**
```
[2024-01-15 09:31] BUY 100 units at 150.25 (spread mode, ask=150.50)
[2024-01-15 10:14] STOP LOSS hit at 147.25 — closed 100 units, PnL: -3.00
[2024-01-15 11:02] SELL 95 units at 152.10 (spread mode, bid=151.85)
[2024-01-15 14:30] TAKE PROFIT hit at 155.00 — closed 95 units, PnL: +2.75
[2024-01-16 09:31] CLOSE at 148.50 — closed 95 units (100%), PnL: -1.20
```

---

### Phase 8: Performance Metrics

**Goal:** Compute all required metrics from the completed simulation.

**Formulas:**

| Metric | Formula |
|---|---|
| Total Return | `(final_equity - initial_capital) / initial_capital` |
| Annualized Return | `(1 + total_return) ^ (252*390 / total_candles) - 1` |
| Max Drawdown | `max((peak - equity) / peak)` over equity curve |
| Sharpe Ratio | `mean(returns) / std(returns) * sqrt(252*390)` (1-min returns, annualized) |
| Win Rate | `winning_trades / total_trades` |
| Profit Factor | `sum(winning_pnl) / abs(sum(losing_pnl))` |
| Avg Trade | `total_realized_pnl / total_trades` |
| Total Trades | count of completed round-trips |
| Exposure Time | `candles_with_position / total_candles` |

---

### Phase 9: Visualization

**Goal:** Generate 4 charts using matplotlib.

1. **Equity Curve** — `equity` over time (line plot)
2. **Drawdown Curve** — drawdown % over time (filled area, inverted)
3. **Price Chart with Markers** — close price line + scatter markers:
   - Green triangle up = BUY entry
   - Red triangle down = SELL entry
   - Red X = SL hit
   - Green star = TP hit
4. **Trade Distribution** — histogram of per-trade PnL values

---

### Phase 10: System Integration

**Goal:** Wire everything into a single runnable command.

**`run_backtest.py` flow:**
```
1. Parse CLI args / load config
2. Load CSV → DataFrame
3. Resample to multi-timeframe dict
4. Instantiate strategy → generate signals
5. Instantiate backtester engine with mode, capital, signals, data
6. Run engine loop
7. Print metrics summary
8. Show / save charts
```

**CLI arguments:**
- `--data` — path to 1m CSV
- `--mode` — `spread_on` | `spread_off` | `static_spread`
- `--static-spread` — value for mode C
- `--capital` — initial capital (default: 10000)
- `--fast-ma` — fast MA period (default: 10)
- `--slow-ma` — slow MA period (default: 30)
- `--sl-pct` — SL percentage (default: 0.02)
- `--tp-pct` — TP percentage (default: 0.02)
- `--output` — save charts to directory

---

### Phase 11: Validation & Hardening

**Goal:** Ensure the engine is deterministic, correct, and handles all edge cases.

**Tests:**
- Run same data twice → byte-identical output
- Manually verify 3-5 trades against hand calculations
- Test with zero signals → equity stays flat (minus nothing)
- Test with 1 signal → single trade lifecycle
- Test position stacking with size=1.0 → cash never negative
- Test signal on last candle → should not execute (no i+1)
- Test empty DataFrame → graceful exit with message

---

## Explicit Design Decisions (per spec requirements)

These are explicitly defined to prevent ambiguity:

| Question | Decision |
|---|---|
| Unrealized PnL uses bid or mid? | **Bid for LONG** (`mid - spread/2`), **Ask for SHORT** (`mid + spread/2`) — consistent with exit price |
| Capital rounding rules | **No rounding** during simulation. Round to 2 decimals only in final report |
| Order of execution steps per candle | Unrealized PnL → SL/TP check → SL/TP execute → Signal execute → State update |
| Stacking logic | Additive position size, weighted average entry, independent SL/TP per unit |
| Spread application side | Entry: pay the spread (buy at ask, sell at bid). Exit: pay the spread (sell at bid, buy at ask) |
| Position size unit | Fractional units allowed (float), representing notional exposure |
| What happens on opposite signal | Strategy emits CLOSE(size=1.0) + new direction at same candle index. Engine processes in order. |
| Who controls position sizing? | **The strategy**, via `signal.size`. Engine has no allocation cap. |
| What does signal.size mean? | For LONG/SHORT: fraction of available cash. For CLOSE: fraction of position to close. |
| SL/TP execution price | At the SL/TP level ± spread/2 (not at candle open) |
| Opposite-direction stacking | **Rejected with ValueError** — `open_position()` refuses to open opposite direction while a position is held. Strategy must emit CLOSE first. Prevents silent accounting corruption. |

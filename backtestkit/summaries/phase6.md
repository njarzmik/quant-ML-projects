# Phase 6: Main Engine Loop

## What Was Implemented

### `backtester/engine.py` — The deterministic backtesting engine

Four components:

#### `Trade` dataclass

Records each trade (open or completed):
- `direction`: "LONG" or "SHORT"
- `entry_price`: Actual entry price (after spread)
- `entry_index`: Candle index where the trade was opened
- `size`: Number of units
- `sl`, `tp`: Stop loss and take profit levels
- `exit_price`, `exit_index`, `exit_reason`, `pnl`: Filled on close (None while open)

`exit_reason` can be `"SL"`, `"TP"`, `"CLOSE"`, or `None` (still open at end of simulation).

#### `Snapshot` dataclass

Per-candle state capture:
- `index`: Candle index
- `cash`, `position_size`, `unrealized_pnl`, `equity`

One snapshot is recorded after every candle, regardless of whether any action occurred.

#### `BacktestResult` dataclass

Returned by `engine.run()`:
- `trades`: List of all Trade records
- `snapshots`: List of all per-candle Snapshots
- `final_equity`: Portfolio equity at end of simulation
- `realized_pnl`, `unrealized_pnl`: Final PnL state

#### `BacktestEngine` class

The main simulation engine. Constructor takes:
- `data`: DataFrame of 1-min OHLC candles
- `signals`: List of Signal objects from a strategy
- `mode`: ExecutionMode (SPREAD_ON, SPREAD_OFF, STATIC_SPREAD)
- `initial_capital`: Starting cash
- `verbosity`: "silent" (default), "normal", or "debug"

### Main loop — strict execution order per candle

```
for each candle i:
    1. Update unrealized PnL (using candle close + spread)
    2. Check SL/TP for each PositionUnit → execute if triggered
    3. Execute pending signals from previous candle:
       a. CLOSE signals first
       b. Directional entries second
    4. Collect new signals at this candle index → store as pending
    5. Record state snapshot
```

### Signal delay enforcement

Signals at candle `i` are stored in `pending_signals`, then executed at candle `i+1` open. No same-candle execution. Signals on the last candle are never executed (no `i+1` exists).

### SL/TP execution via PositionUnit

Each entry signal creates a `PositionUnit` with the signal's SL/TP levels. When stacking, multiple units exist independently. SL/TP is checked per-unit each candle. When triggered, the unit is closed at the SL/TP exit price (with spread applied), cash is returned, and the trade record is updated.

### CLOSE signal handling

- Full close (`size=1.0`): Closes entire position via `portfolio.close_position()`, clears all position units, records exit on all open trades.
- Partial close (`size<1.0`): Reduces each unit proportionally, updates portfolio accounting.

### Signal map optimization

Signals are pre-indexed into a `dict[int, List[Signal]]` at construction time for O(1) lookup per candle, avoiding linear scans over the signal list.

### Empty data handling

If the DataFrame is empty, returns immediately with `final_equity = initial_capital` and no trades/snapshots.

## Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Signal execution timing | At candle `i+1` open | No lookahead bias; signal at `i` cannot see `i+1` data |
| SL/TP checked before signals | Yes | Per spec: unrealized PnL → SL/TP → signals → snapshot |
| CLOSE before entry on same candle | Yes | Ensures clean reversal: close old position, then open new |
| Per-unit SL/TP tracking | PositionUnit list | Each stacked entry has independent risk levels |
| SL/TP exit bypasses Portfolio.close_position | Yes | SL/TP exits at the level price, not at candle open; requires direct cash manipulation |
| Signal map pre-built | dict keyed by timestamp_index | Avoids O(n) scan per candle |
| Default verbosity | "silent" | Tests run cleanly without output noise |

## Test Coverage

**121 total tests** across Phase 1 (38), Phase 2 (32), Phase 3 (13), Phase 4 (19), Phase 5 (11), and Phase 6 (8). All passing.

### Phase 6 tests (`tests/test_engine.py`) — 8 tests

**TestSignalDelay (2 tests):**
- `test_signal_executes_next_candle` — LONG signal at candle 0 executes at candle 1 open (101.0, not 100.0)
- `test_signal_on_last_candle_not_executed` — Signal at the final candle produces no trade

**TestExecutionOrder (1 test):**
- `test_sl_checked_before_signal` — SL triggers and closes position before any pending signal at the same candle

**TestNoTradeScenario (1 test):**
- `test_empty_signals` — Zero signals → zero trades, equity unchanged at 10000.0

**TestCloseAndReverse (1 test):**
- `test_long_then_short_reversal` — CLOSE + SHORT at same index: LONG closed first, then SHORT opened

**TestClose (1 test):**
- `test_close_signal` — CLOSE(size=1.0) at candle 2 → executes at candle 3 → position is 0 at candle 3 and 4

**TestDeterminism (1 test):**
- `test_same_result_twice` — Two identical runs produce identical final_equity, trade count, entry/exit prices

**TestEquitySnapshot (1 test):**
- `test_snapshots_recorded_every_candle` — 5 candles → 5 snapshots

## What Comes Next

- **Phase 7** — Console Logging: Structured trade log messages with configurable verbosity (silent/normal/debug). The logging hooks are already in the engine (currently silent by default).

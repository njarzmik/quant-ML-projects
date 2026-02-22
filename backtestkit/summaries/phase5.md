# Phase 5: SL/TP Engine

## What Was Implemented

### `backtester/sl_tp.py` — Stop loss / take profit engine

Three components:

#### `PositionUnit` dataclass

Stores a single position entry with its own SL/TP levels:
- `direction`: "LONG" or "SHORT"
- `entry_price`: Actual entry price (after spread adjustment)
- `size`: Number of units in this position layer
- `sl`: Stop loss price level
- `tp`: Take profit price level

When stacking, each entry event creates a separate `PositionUnit`. Each unit has independent SL/TP that can trigger independently.

#### `SLTPResult` dataclass

Return type from `check_sl_tp()`:
- `triggered`: `None` if neither triggered, `"SL"` or `"TP"` if one fired
- `exit_price`: The execution price (with spread applied), or `None` if not triggered

#### `check_sl_tp(unit, candle, mode)` function

Evaluates SL/TP conditions for a position unit against a candle.

**Intrabar evaluation logic:**
- LONG: SL hit if `candle.low <= SL level`, TP hit if `candle.high >= TP level`
- SHORT: SL hit if `candle.high >= SL level`, TP hit if `candle.low <= TP level`

**Worst-case rule:** If BOTH SL and TP trigger on the same candle, SL executes. This is deliberate pessimism — prevents the backtest from showing unrealistically good results.

**Boundary conditions:** Uses `<=` and `>=` (inclusive), so exact touches at SL/TP levels trigger.

**SL/TP execution prices (spread-adjusted):**
- LONG SL/TP hit → exit at `level - spread/2` (sold at bid)
- SHORT SL/TP hit → exit at `level + spread/2` (bought at ask)
- Mode B (SPREAD_OFF) → exit at the level itself (no spread adjustment)

#### `_apply_exit_spread(level, direction, spread, mode)` helper

Applies spread adjustment to the exit price based on direction and execution mode. Internal function used by `check_sl_tp`.

### Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| SL checked before TP | Yes (worst-case) | Prevents optimistic bias when both could trigger |
| Boundary comparison | Inclusive (`<=`, `>=`) | Exact touches at SL/TP level must trigger |
| Spread on SL/TP exits | Applied | Realistic: selling at bid, buying at ask |
| Mode B SL/TP exit | At level, no spread | Consistent with Mode B's "no spread" design |
| Per-unit SL/TP | Independent | Each stack layer has its own risk levels |

### Verification: hand-calculated reference values

**Scenario A: LONG SL hit, spread=0.50**
```
Entry = 100.0, SL = 98.0, TP = 102.0
Candle: low = 97.0 (below SL)
→ SL triggered
→ Exit price = 98.0 - 0.25 = 97.75 (bid at SL level)
```

**Scenario B: SHORT SL hit, spread=0.50**
```
Entry = 100.0, SL = 102.0, TP = 98.0
Candle: high = 102.5 (above SL)
→ SL triggered
→ Exit price = 102.0 + 0.25 = 102.25 (ask at SL level)
```

**Scenario C: Both triggered (LONG), worst-case**
```
Entry = 100.0, SL = 98.0, TP = 102.0
Candle: low = 97.0, high = 103.0 (both levels breached)
→ SL fires (worst case for LONG)
→ PnL = negative (loss, not the profit from TP)
```

All values match the implemented functions.

## Test Coverage

**113 total tests** across Phase 1 (38), Phase 2 (32), Phase 3 (13), Phase 4 (19), and Phase 5 (11). All passing.

### Phase 5 tests (`tests/test_sl_tp.py`) — 11 tests

**TestLongSLTP (6 tests):**
- `test_sl_triggered` — candle low breaches SL → SL fires
- `test_tp_triggered` — candle high reaches TP → TP fires
- `test_both_triggered_worst_case` — both breached → SL fires (worst case)
- `test_neither_triggered` — price stays within range → no trigger
- `test_exact_sl_boundary` — low == SL exactly → SL fires (inclusive)
- `test_exact_tp_boundary` — high == TP exactly → TP fires (inclusive)

**TestShortSLTP (3 tests):**
- `test_sl_triggered` — candle high breaches SL → SL fires for SHORT
- `test_tp_triggered` — candle low reaches TP → TP fires for SHORT
- `test_both_triggered_worst_case_short` — both breached → SL fires (worst case for SHORT)

**TestSLTPWithSpread (2 tests):**
- `test_long_sl_exit_at_bid` — LONG SL exit = SL_level - spread/2 = 97.75
- `test_short_sl_exit_at_ask` — SHORT SL exit = SL_level + spread/2 = 102.25

## What Comes Next

- **Phase 6** — Main Engine Loop: `BacktestEngine` class that orchestrates the per-candle simulation loop. Uses `PositionUnit` objects to track SL/TP per entry. Enforces strict execution order: update unrealized PnL → check SL/TP → execute pending signals → record snapshot. Implements signal delay (signal at candle `i` → execute at candle `i+1` open).

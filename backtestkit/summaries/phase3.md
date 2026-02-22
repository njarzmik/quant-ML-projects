# Phase 3: Execution Modes

## What Was Implemented

### Price resolver module (`backtester/execution_modes.py`)

Three functions that answer the question: "given a mid-price, a spread, a direction, and an execution mode, what exact price do I pay or receive?"

#### `resolve_entry_price(mid, spread, direction, mode) -> float`
Returns the price at which a position is opened:

| Mode | LONG | SHORT |
|---|---|---|
| SPREAD_ON (A) | `mid + spread/2` (buy at ask) | `mid - spread/2` (sell at bid) |
| SPREAD_OFF (B) | `mid` (no adjustment) | `mid` (no adjustment) |
| STATIC_SPREAD (C) | `mid + spread/2` (same as A, spread is the static value) | `mid - spread/2` |

#### `resolve_exit_price(mid, spread, direction, mode) -> float`
Returns the price at which a position is closed:

| Mode | LONG | SHORT |
|---|---|---|
| SPREAD_ON (A) | `mid - spread/2` (sell at bid) | `mid + spread/2` (buy at ask) |
| SPREAD_OFF (B) | `mid` (no adjustment) | `mid` (no adjustment) |
| STATIC_SPREAD (C) | `mid - spread/2` (same as A) | `mid + spread/2` |

#### `calculate_fee(position_value, mode) -> float`
Returns the transaction fee:

| Mode | Fee |
|---|---|
| SPREAD_ON (A) | 0 |
| SPREAD_OFF (B) | `position_value * 0.001` (0.1%) |
| STATIC_SPREAD (C) | 0 |

### How the three modes work conceptually

**Mode A (SPREAD_ON)** models realistic market conditions. You always "pay the spread" — buying at the ask (higher than mid) and selling at the bid (lower than mid). A round-trip immediately costs one full spread. This is the most conservative and realistic mode.

**Mode B (SPREAD_OFF)** replaces the spread with a flat 0.1% fee per transaction. Entry and exit both happen at the mid-price, but a fee is charged on both sides. A round-trip costs 0.2% of position value. This is useful for testing strategies on markets where fees are more relevant than spreads.

**Mode C (STATIC_SPREAD)** uses the exact same logic as Mode A, but the `spread` parameter passed in is a user-defined constant rather than the per-candle spread from the CSV data. This allows testing with a consistent cost assumption regardless of the dataset's actual spread values. The caller is responsible for passing the static spread value instead of the candle's spread.

### Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Mode C reuses Mode A logic | Yes | The only difference is what spread value is passed in — the math is identical |
| SPREAD_OFF fee rate | 0.1% (0.001) | Per spec; applied on both entry and exit |
| Direction as string | `"LONG"` / `"SHORT"` | Matches the rest of the codebase; engine passes direction as string |
| No state in module | Stateless functions | Price resolution is a pure calculation — no side effects, no dependencies |

### Verification: hand-calculated reference values

Using `mid_price = 100.0, spread = 0.50`:

| | Mode A (Spread ON) | Mode B (Spread OFF) | Mode C (Static=0.30) |
|---|---|---|---|
| LONG entry | 100.25 | 100.00 | 100.15 |
| LONG exit | 99.75 | 100.00 | 99.85 |
| SHORT entry | 99.75 | 100.00 | 99.85 |
| SHORT exit | 100.25 | 100.00 | 100.15 |
| Fee on 10000 | 0.00 | 10.00 | 0.00 |

All 15 values match the implemented functions.

## Test Coverage

**83 total tests** across Phase 1 (38), Phase 2 (32), and Phase 3 (13). All passing.

### Phase 3 tests (`tests/test_execution_modes.py`) — 13 tests

**TestModeA_SpreadOn (7 tests):**
- `test_long_entry` — LONG entry = mid + spread/2 = 100.25
- `test_long_exit` — LONG exit = mid - spread/2 = 99.75
- `test_short_entry` — SHORT entry = mid - spread/2 = 99.75
- `test_short_exit` — SHORT exit = mid + spread/2 = 100.25
- `test_zero_spread` — zero spread degenerates to mid-price execution
- `test_no_fee` — Mode A charges no fee (cost is via spread)
- `test_instant_loss_on_entry` — buy and immediately sell at same mid = loss of exactly one spread

**TestModeB_SpreadOff (4 tests):**
- `test_long_entry_at_mid` — entry at mid, no spread adjustment
- `test_long_exit_at_mid` — exit at mid, no spread adjustment
- `test_fee_calculation` — 0.1% fee on 10000 = 10.0
- `test_fee_on_small_position` — 0.1% fee on 500 = 0.50 (scales linearly)

**TestModeC_StaticSpread (2 tests):**
- `test_uses_custom_spread` — uses the passed spread value (0.30), not dataset spread
- `test_no_fee` — Mode C charges no fee (cost is via static spread)

## What Comes Next

- **Phase 4** — Capital Accounting: `Portfolio` class tracking cash, position_size, avg_entry_price, realized_pnl, unrealized_pnl, equity. Position opening with strategy-controlled sizing, stacking with weighted average entry, closing with realized PnL settlement.
- **Phase 5** — SL/TP Engine: per-position-unit SL/TP storage, intrabar evaluation (LONG: low <= SL, SHORT: high >= SL), worst-case rule (both triggered = SL fires), spread-adjusted exit prices.
- **Phase 6** — Main Engine Loop: signal delay (i+1 execution), strict ordering (unrealized PnL -> SL/TP -> signal -> snapshot), deterministic simulation.

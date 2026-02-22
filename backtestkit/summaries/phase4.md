# Phase 4: Capital Accounting

## What Was Implemented

### Portfolio class (`backtester/portfolio.py`)

A `Portfolio` class that tracks all financial state throughout the backtesting simulation. It manages cash, position sizing, entry price averaging, realized/unrealized PnL, and equity — the complete accounting layer that sits between the execution mode price resolver (Phase 3) and the future engine loop (Phase 6).

#### Constructor: `Portfolio(initial_capital, mode)`

Creates a fresh portfolio with:
- `cash` = initial_capital (all money starts as free cash)
- `position_size` = 0.0 (no position open)
- `avg_entry_price` = 0.0 (no entry yet)
- `realized_pnl` = 0.0 (no trades completed)
- `unrealized_pnl` = 0.0 (no open position to mark-to-market)
- `position_notional` = abs(position_size) * avg_entry_price (property, capital locked in position)
- `equity` = cash + position_notional + unrealized_pnl (property, total account value)

#### `open_position(entry_price, spread, direction, size=1.0)`

Opens a new position or adds to an existing one (stacking).

How it works step by step:
1. Calculates `allocation = cash * size` (strategy controls what fraction of cash to use)
2. Resolves the actual entry price via the Phase 3 price resolver (applies spread for Mode A/C, or uses mid for Mode B)
3. Calculates any fee (0.1% for Mode B, 0 for others)
4. Computes units: `effective_allocation / actual_entry_price`
5. For SHORT: units are stored as negative (convention: +N = long, -N = short)
6. If stacking onto an existing position: recalculates the weighted average entry price
7. Deducts the full allocation from cash

**Stacking formula:**
```
new_avg = (old_avg * old_size + new_price * new_size) / (old_size + new_size)
```

**Safety:** If available cash is zero or negative, the method returns without doing anything (no implicit leverage).

#### `close_position(exit_price, spread, size=1.0)`

Closes all or part of the current position.

How it works step by step:
1. Determines direction from the sign of `position_size`
2. Resolves actual exit price via the Phase 3 price resolver
3. Calculates units to close: `abs(position_size) * size`
4. Computes realized PnL:
   - LONG: `(exit_price - avg_entry) * units_to_close`
   - SHORT: `(avg_entry - exit_price) * units_to_close`
5. Calculates exit fee (Mode B only)
6. Credits cash with the position value plus/minus PnL, minus fee
7. Accumulates PnL into `realized_pnl`
8. On full close (size=1.0): resets `position_size` and `avg_entry_price` to 0

#### `update_unrealized(current_mid, spread)`

Marks the open position to market using current prices.

- **LONG positions:** uses the bid price (`mid - spread/2`) — what you'd actually receive if you sold right now
- **SHORT positions:** uses the ask price (`mid + spread/2`) — what you'd actually pay to buy back

This is consistent with the spec's requirement that unrealized PnL reflects realistic exit prices, not the mid-price.

#### `position_notional` (property)

Capital locked in the open position at entry cost: `abs(position_size) * avg_entry_price`. When flat, this is 0.

#### `equity` (property)

`equity = cash + position_notional + unrealized_pnl`

This is the true total account value:
- `cash` — free capital not in positions
- `position_notional` — capital deployed in the position (what was originally allocated)
- `unrealized_pnl` — how much the position has gained or lost since entry

**Why not just `cash + unrealized_pnl`?** Because when `open_position` deducts an allocation from `cash`, that capital moves into the position — it's not gone. The old formula was missing the locked capital, producing negative equity on a fresh position (e.g., -49.88 instead of ~9950.12 after buying with a small spread). The fix adds `position_notional` to account for the deployed capital.

### Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Position sign convention | +N = long, -N = short | Simple, standard, makes direction checks trivial |
| Fee deducted from allocation on entry | Yes | Matches spec: fee reduces effective allocation, not a separate charge |
| Fee deducted from cash return on exit | Yes | Exit fee reduces the cash you get back |
| Realized PnL includes fees | Yes (fees subtracted from PnL) | Realized PnL reflects actual profit after all costs |
| Cash return on close | `avg_entry * units + pnl - fee` | Returns the capital deployed plus profit, minus exit costs |
| Zero-cash guard | Returns early, no error | Prevents implicit leverage silently |
| Weighted average uses `abs()` | Yes | Works correctly for both long and short stacking |
| Opposite-direction stacking | **Rejected with ValueError** | See section below |

### Opposite-direction stacking guard

`open_position()` raises a `ValueError` if called with a direction opposite to the current position (e.g., opening SHORT while holding LONG). This is a deliberate safety check.

**Why it's needed:** The stacking logic computes a weighted average entry price, which only makes financial sense for same-direction entries. If you blend a LONG entry at 100 with a SHORT entry at 99.75, the resulting "average" is meaningless — it's neither a valid long entry nor a valid short entry. Additionally, no realized PnL would be calculated on the units that were effectively closed, leading to silent accounting corruption.

**What strategies must do instead:** Emit a `CLOSE` signal before reversing direction. The MA Crossover strategy already does this correctly — on reversal it emits `CLOSE(size=1.0)` followed by the new direction signal at the same candle index. The engine processes CLOSE first, which resets the position to flat, and then the opposite-direction open works correctly on a fresh position.

**Future consideration:** If a future strategy needs opposite-direction reduction (e.g., "I'm long 10, reduce by 2 without fully closing"), this guard would need to be replaced with proper partial-close-then-reopen logic. For now, the explicit rejection prevents silent accounting bugs.

### Verification: hand-calculated reference values

**Scenario: SPREAD_ON mode, initial capital = 10000**

```
Open LONG at mid=100.0, spread=0.0, size=0.9:
  → allocation = 10000 * 0.9 = 9000
  → entry = 100.0 (no spread)
  → units = 9000 / 100 = 90
  → cash = 10000 - 9000 = 1000
  → position_size = +90

Stack LONG at mid=200.0, spread=0.0, size=1.0:
  → allocation = 1000 * 1.0 = 1000
  → units = 1000 / 200 = 5
  → new_avg = (100*90 + 200*5) / 95 = 10000/95 = 105.263...
  → cash = 0

Close at mid=110.0, spread=0.0:
  → exit = 110.0
  → PnL = (110 - 105.263) * 95 = 450.0
  → cash = 105.263*95 + 450 = 10000 + 450 = 10450
  → realized_pnl = 450
```

All values match the implemented functions.

## Test Coverage

**100 total tests** across Phase 1 (38), Phase 2 (32), Phase 3 (13), and Phase 4 (17). All passing.

### Phase 4 tests (`tests/test_portfolio.py`) — 17 tests

**TestPositionOpening (5 tests):**
- `test_initial_state` — fresh portfolio: cash=10000, position=0, pnl=0, equity=10000
- `test_long_entry_deducts_cash` — LONG size=1.0 reduces cash to ~0, position_size > 0
- `test_size_controls_allocation` — size=1.0 with spread=0: units = cash/price exactly
- `test_90_percent_allocation` — size=0.9: 90% allocated, 10% retained as cash
- `test_cannot_exceed_cash` — second open with zero cash remaining does nothing (no leverage)

**TestOppositeDirectionRejection (2 tests):**
- `test_long_then_short_raises` — opening SHORT while LONG raises ValueError
- `test_short_then_long_raises` — opening LONG while SHORT raises ValueError

**TestPositionStacking (2 tests):**
- `test_stacking_increases_size` — two opens produce larger position than one
- `test_weighted_average_entry` — stacked avg = (price1*units1 + price2*units2) / total_units

**TestPositionClosing (4 tests):**
- `test_close_credits_cash` — profitable close: cash = remaining + entry_value + profit
- `test_losing_trade_reduces_cash` — losing close: cash < initial capital
- `test_realized_pnl_tracked` — realized_pnl accumulates correctly
- `test_close_resets_position` — full close: position_size=0, avg_entry=0

**TestCloseAndReverse (1 test):**
- `test_long_to_short` — close long then open short: position_size < 0

**TestUnrealizedPnL (5 tests):**
- `test_long_unrealized_profit` — price up = positive unrealized for longs
- `test_long_unrealized_uses_bid` — uses bid (mid-spread/2), not mid, for mark-to-market
- `test_equity_is_total_account_value` — equity = cash + position_notional + unrealized
- `test_equity_after_open_reflects_spread_cost` — opening with spread reduces equity by ~spread cost, not to negative
- `test_equity_unchanged_when_flat` — when flat, equity = cash

## What Comes Next

- **Phase 5** — SL/TP Engine: `PositionUnit` dataclass storing per-unit SL/TP levels, `check_sl_tp()` function for intrabar evaluation (LONG: low <= SL, SHORT: high >= SL), worst-case rule (both triggered = SL fires), spread-adjusted exit prices at SL/TP levels.
- **Phase 6** — Main Engine Loop: `BacktestEngine` class orchestrating the signal delay (i+1 execution), strict per-candle ordering (unrealized PnL -> SL/TP check -> signal execute -> snapshot), and deterministic simulation.

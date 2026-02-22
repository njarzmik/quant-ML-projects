# Changes to Equity Calculation After Phase 4

## The Bug

The original equity formula was:

```
equity = cash + unrealized_pnl
```

This is **wrong** because `cash` in our implementation means "free capital not in positions." When you open a position, `cash` decreases by the allocation amount — but that money isn't gone, it's locked in the position. The formula was missing this locked capital entirely.

### Example of the bug

```
Initial: cash = 10000
Open LONG at ask = 100.25, size = 1.0
  → allocation = 10000 (deducted from cash)
  → units = 99.75
  → cash = 0

Mark-to-market at bid = 99.75:
  → unrealized_pnl = (99.75 - 100.25) * 99.75 = -49.88

OLD equity = 0 + (-49.88) = -49.88       ← WRONG (negative?!)
NEW equity = 0 + 10000 + (-49.88) = 9950.12  ← CORRECT (lost ~50 on spread)
```

The old formula said your account was worth -49.88 after putting 10000 into a position. In reality, you still had ~9950 worth of assets — it's just that ~50 was lost to the spread.

## The Fix

The corrected formula is:

```
equity = cash + position_notional + unrealized_pnl
```

Where `position_notional = abs(position_size) * avg_entry_price` — the capital deployed in the open position at entry cost.

The three components:
- **cash** — free capital not in any position
- **position_notional** — capital locked in the position (what was originally allocated)
- **unrealized_pnl** — how much the position has gained or lost since entry

When flat (no position), `position_notional = 0` and `unrealized_pnl = 0`, so equity degenerates to just `cash`. This is correct.

## Every Change Made

### 1. `backtester/portfolio.py` — the implementation

**Added `position_notional` property (new):**
```python
@property
def position_notional(self) -> float:
    """Capital locked in the open position (at entry cost)."""
    return abs(self.position_size) * self.avg_entry_price
```

**Changed `equity` property:**
```python
# OLD:
return self.cash + self.unrealized_pnl

# NEW:
return self.cash + self.position_notional + self.unrealized_pnl
```

**Changed docstring** in the class (line 16):
```python
# OLD: equity: cash + unrealized_pnl
# NEW: equity: cash + position_notional + unrealized_pnl
```

### 2. `tests/test_portfolio.py` — the automated tests

**Removed** `test_equity_equals_cash_plus_unrealized` — this test asserted the old broken formula.

**Added** three new tests in its place:

- `test_equity_is_total_account_value` — asserts `equity == cash + position_notional + unrealized_pnl` with exact numbers: LONG at 100 (90 units, cash=1000), mid=110 gives equity = 1000 + 9000 + 900 = 10900.

- `test_equity_after_open_reflects_spread_cost` — asserts that opening a position with spread=0.5 makes equity slightly less than 10000 (the spread cost) but NOT negative. This is the test that would have caught the original bug directly.

- `test_equity_unchanged_when_flat` — asserts that when no position is open, equity simply equals cash (the formula degenerates correctly).

### 3. `tests/manual/manualtest_portfolio.py` — manual test script

**Fixed print labels** — the original file had `portfolio.realized_pnl` printed with the label "unrealized pnl:" and vice versa on every block. All labels now correctly match their values.

**Added `sys.path` fix** — added `sys.path.insert(0, ...)` at the top so the file can be run directly with `python file.py` instead of requiring `python -m tests.manual.manualtest_portfolio`.

**Restructured** into clean steps with a `print_state()` helper function for consistent output.

### 4. `context/spec.md` — the specification

**Changed the equity row** in the Capital Accounting state variables table (section 8):
```
# OLD:
| equity | cash + unrealized_pnl |

# NEW:
| position_notional | Capital locked in position: abs(position_size) * avg_entry_price |
| equity | cash + position_notional + unrealized_pnl (total account value) |
```

### 5. `context/plan.md` — the implementation plan

**Changed the PortfolioState dataclass** (Phase 4 section):
```python
# OLD:
equity: float  # cash + unrealized_pnl

# NEW:
position_notional: float  # abs(position_size) * avg_entry_price
equity: float              # cash + position_notional + unrealized_pnl
```

**Changed checklist item 4.8:**
```
# OLD: Implement equity calculation (cash + unrealized_pnl)
# NEW: Implement equity calculation (cash + position_notional + unrealized_pnl)
```

### 6. `context/plan_explained.md` — the plain English explanation

**Changed the Equity definition** (section "Why we track both realized and unrealized PnL"):
```
# OLD:
Equity = cash + unrealized PnL. This is your "net worth" at any moment.

# NEW:
Equity = cash + position_notional + unrealized PnL. This is your total account value
at any moment. cash is the free capital, position_notional is the capital locked in
the open position, and unrealized PnL is how much that position has gained or lost.
```

### 7. `context/tests_explained.md` — test explanations

**Updated TestUnrealizedPnL section** from 3 tests to 5 tests. Replaced the explanation for `test_equity_equals_cash_plus_unrealized` with explanations for the three new tests: `test_equity_is_total_account_value`, `test_equity_after_open_reflects_spread_cost`, and `test_equity_unchanged_when_flat`.

### 8. `context/tests.md` — test checklist and code templates

**Updated the Phase 4 checklist** — replaced `test_equity_equals_cash_plus_unrealized` with the three new test names.

**Updated the code template** for the equity test to use the new formula.

**Updated the Phase 10 manual check** — changed the capital preservation identity from `final_equity == cash + unrealized_pnl` to `final_equity == cash + position_notional + unrealized_pnl`.

### 9. `summaries/phase4.md` — the phase summary

**Updated constructor description** — added `position_notional` to the list of initial state variables.

**Updated the equity property description** — full explanation of the three-component formula and why the old formula was wrong.

**Updated test coverage section** — from 3 to 5 unrealized PnL tests, with correct test names.

## Verification

After all changes:
- **102 automated tests** all passing (38 Phase 1 + 32 Phase 2 + 13 Phase 3 + 19 Phase 4)
- **Manual test** (`manualtest_portfolio.py`) produces correct equity values at every step

### Manual test results (before vs after):

| Step | Old equity (broken) | New equity (correct) |
|---|---|---|
| OPEN LONG (mid=100, spread=0.5) | -49.88 | 9950.12 |
| CLOSE LONG (mid=110) — flat | 10947.63 | 10947.63 |
| OPEN SHORT (mid=110, size=0.5) | 5448.88 | 10922.69 |
| STACK SHORT (mid=120, size=1.0) | -546.55 | 10401.08 |
| CLOSE SHORT (mid=130) — flat | 9445.23 | 9445.23 |

Note: flat positions (after close) show the same value in both — the bug only manifested when a position was open.

## Current Status

Phase 4 (Capital Accounting) is now **complete and correct**. All accounting — cash tracking, position sizing, stacking with weighted averages, closing with realized PnL, unrealized mark-to-market, and equity — is verified against hand calculations.

The project is ready to move into the next phases:

- **Phase 5 (SL/TP Engine)** — will add `PositionUnit` objects that store per-unit stop loss and take profit levels, with intrabar evaluation logic (does the candle's low breach the SL? does the high reach the TP?) and the worst-case rule: if both SL and TP could trigger on the same candle, SL fires (conservative assumption).

- **Phase 6 (Main Engine Loop)** — will wire everything together into the `BacktestEngine` class: the main per-candle loop that enforces the strict execution order (update unrealized PnL, check SL/TP, execute pending signals, record snapshot) and the critical signal delay rule (signal at candle i executes at candle i+1 open).

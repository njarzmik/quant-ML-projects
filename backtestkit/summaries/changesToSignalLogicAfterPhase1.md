# Changes to Signal Logic After Phase 1

This document describes all signal-system changes made after Phase 1 was completed.

---

## Why the Change Was Needed

Phase 1 was built with the original `spec.md` assumptions:
- One signal per candle, one signal type at a time
- `CLOSE_FULL` as the only close signal (always 100%, no partial)
- A fixed 90% allocation cap enforced by the engine
- On reversal, a single "close-and-reverse" signal

After analyzing the trading strategy design, we decided that:
1. Strategies should control **both direction and sizing** (two-phase model)
2. Partial exits should be possible for future strategies
3. The engine should not impose an allocation cap - strategy decides

---

## Summary of Changes

### 1. `CLOSE_FULL` renamed to `CLOSE`
- **File:** `common/models.py`
- **Before:** `SignalType.CLOSE_FULL = "CLOSE_FULL"`
- **After:** `SignalType.CLOSE = "CLOSE"`
- **Reason:** The `_FULL` suffix was misleading now that partial closes are supported via the `size` field. `CLOSE` with `size=1.0` = full close. `CLOSE` with `size=0.5` = close half the position.

### 2. `size` field added to Signal
- **File:** `strategies/signals.py`
- **Before:** Signal had 4 fields: `timestamp_index`, `signal_type`, `stop_loss_level`, `take_profit_level`
- **After:** Signal has 5 fields, adding `size: float`
- **Meaning:**
  - For LONG/SHORT: `size` = fraction of **available cash** to allocate (1.0 = 100%)
  - For CLOSE: `size` = fraction of **current position** to close (1.0 = full close, 0.5 = half)
- **MA Crossover always uses `size=1.0`** for all signals

### 3. 90% allocation cap removed
- **Before:** Engine would cap allocation at 90% of available cash regardless of strategy
- **After:** Strategy fully controls allocation via `signal.size`. If strategy says `size=1.0`, that means 100% of available cash. No engine-level cap.
- **Files updated:** `context/plan.md` (Phase 4), `context/plan_explained.md`, `context/tests.md` (Phase 4 tests), `context/tests_explained.md`

### 4. Reversal logic: explicit CLOSE signal before new direction
- **Before:** On reversal (e.g. LONG to SHORT), a single signal would implicitly close the old position and open the new one
- **After:** On reversal, the strategy emits **two signals** at the same candle index:
  1. `CLOSE` with `size=1.0` (close old position fully)
  2. New direction (LONG or SHORT) with `size=1.0`
- **Engine processes them in list order** (CLOSE first, then entry)
- **File:** `strategies/ma_crossover.py` - complete rewrite of `generate()` with `last_direction` tracking

### 5. CLOSE signal properties
- `stop_loss_level = 0.0` and `take_profit_level = 0.0` (no SL/TP on a close)
- `size = 1.0` for full close (MA Crossover always does full close)
- Future strategies may use fractional sizes for partial exits

### 6. Multiple signals per candle now supported
- **Before:** One signal per candle was a hard rule
- **After:** Multiple signals can share the same `timestamp_index` (specifically CLOSE + direction pairs on reversals)
- **Engine design:** Will process a `pending_signals` list per candle, executing in order

---

## Files Modified

| File | What Changed |
|---|---|
| `common/models.py` | `CLOSE_FULL` -> `CLOSE` |
| `strategies/signals.py` | Added `size: float` field |
| `strategies/ma_crossover.py` | Rewritten: CLOSE on reversal, `last_direction` tracking, size=1.0 |
| `context/plan.md` | Phase 2 checked off, Phase 4/6/11 updated |
| `context/plan_explained.md` | All CLOSE_FULL refs, 90% refs, one-signal-per-candle refs updated |
| `context/tests.md` | Phase 2 tests checked, Phase 4/6 test code updated |
| `context/tests_explained.md` | Phase 2 status, all refs updated |
| `summaries/phase1.md` | CLOSE_FULL -> CLOSE, Phase 4 preview updated |
| `tests/test_strategy.py` | Rewritten: 32 tests covering new signal logic |

---

## What Stayed the Same

- `spec.md` — left as the **original spec** document. The plan supersedes it.
- Signal execution delay — signals at candle `i` still execute at candle `i+1` open
- SL/TP calculation — LONG: SL = close * (1 - sl_pct), TP = close * (1 + tp_pct); SHORT inverted
- No lookahead bias principle
- OHLC resampling logic (Phase 1 untouched)

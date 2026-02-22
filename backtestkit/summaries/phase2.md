# Phase 2: Signal Generator

## What Was Implemented

### Signal dataclass (`strategies/signals.py`)
A `Signal` is the core output of any strategy. Fields:
- `timestamp_index: int` — which candle the signal was generated at
- `signal_type: SignalType` — LONG, SHORT, or CLOSE
- `stop_loss_level: float` — SL price (0.0 for CLOSE signals)
- `take_profit_level: float` — TP price (0.0 for CLOSE signals)
- `size: float` — allocation fraction (1.0 = 100% of available cash for entries, 100% of position for closes)

### Abstract base strategy (`strategies/base_strategy.py`)
`BaseStrategy` is an abstract base class (ABC) that defines the interface:
- `generate(df: pd.DataFrame) -> List[Signal]` — all strategies must implement this
- Accepts OHLC DataFrame, returns a list of Signal objects

### MA Crossover strategy (`strategies/ma_crossover.py`)
`MACrossoverStrategy(BaseStrategy)` — the first concrete strategy:
- **Parameters:** `fast_period` (default 10), `slow_period` (default 30), `sl_pct` (default 0.02), `tp_pct` (default 0.02)
- **Logic:**
  1. Compute fast and slow simple moving averages on `close`
  2. Scan for crossover (fast crosses above slow) -> LONG
  3. Scan for crossunder (fast crosses below slow) -> SHORT
  4. On reversal: emit CLOSE(size=1.0) then new direction(size=1.0) at same index
  5. First entry: just direction, no CLOSE needed
  6. All entries use `size=1.0` (100% of available cash)
- **SL/TP calculation:**
  - LONG: SL = close * (1 - sl_pct), TP = close * (1 + tp_pct)
  - SHORT: SL = close * (1 + sl_pct), TP = close * (1 - tp_pct)
- **CLOSE signals:** SL=0.0, TP=0.0, size=1.0
- Tracks `last_direction` to know when a reversal happens

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Signal carries `size` | Yes | Supports two-phase model (direction + sizing) |
| CLOSE_FULL vs CLOSE | Renamed to CLOSE | Enables partial exits via size<1.0 |
| 90% allocation cap | Removed | Strategy controls sizing fully |
| Reversal flow | Two signals (CLOSE + direction) | Explicit, not implicit; engine processes in order |
| Signal timing on reversal | Same candle index | Both CLOSE and new entry at same `timestamp_index` |
| size=1.0 meaning | 100% of AVAILABLE CASH | Not total equity, not capped |

## Test Coverage

**70 total tests** across Phase 1 (38) and Phase 2 (32). All passing.

### Phase 2 tests (`tests/test_strategy.py`) — 32 tests

**TestMACrossover (11 core tests):**
- Single LONG signal on uptrend
- Crossunder produces SHORT after LONG
- Reversal emits CLOSE before new direction
- CLOSE and direction share same candle index
- First entry has no preceding CLOSE
- All signals carry `size` field
- CLOSE signals have zero SL/TP
- LONG SL/TP at +/-2% of close
- Flat market produces zero signals
- Signal indices within DataFrame bounds
- No side effects (idempotent)

**TestMACrossoverEdgeCases (16 tests):**
- Too few candles returns empty
- Exactly slow_period candles
- SHORT SL/TP levels (inverted from LONG)
- Custom sl_pct/tp_pct respected
- No signal ever at index 0
- Monotonically rising prices
- Monotonically falling prices
- CLOSE always followed by directional signal
- Directional signals have positive SL and TP
- LONG: SL < TP
- SHORT: SL > TP
- Signal count on reversal data (exactly 3: LONG + CLOSE + SHORT)
- Different instances, same result
- Default parameter values
- Signals ordered by timestamp_index
- Input DataFrame not mutated

**TestSignalDataclass (5 tests):**
- All 5 fields exist and accessible
- Equality comparison works
- Inequality comparison works
- SignalType.CLOSE exists
- Fractional size accepted (e.g. 0.5)


ALSO manually tested. and plotted everything. everything seems to be good. remember that the strategy doesnt close the final position by itself.
## What Comes Next

- **Phase 3** — Execution Modes: price resolution for SPREAD_ON, SPREAD_OFF (0.1% fee), STATIC_SPREAD
- **Phase 4** — Capital Accounting: portfolio state, position opening/closing, strategy-controlled sizing, stacking with weighted average entry
- **Phase 5** — SL/TP Engine: candle-level SL/TP checking, worst-case logic when both trigger

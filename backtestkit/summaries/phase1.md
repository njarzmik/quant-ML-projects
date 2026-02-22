# Phase 1: Project Scaffolding & Data Layer

## What was implemented

- **Project structure** — Python project with `pyproject.toml`, `requirements.txt`, and package skeletons for `backtester/`, `strategies/`, `common/`, and `tests/`.
- **Shared data models** (`common/models.py`) — `ExecutionMode` enum (SPREAD_ON, SPREAD_OFF, STATIC_SPREAD) and `SignalType` enum (LONG, SHORT, CLOSE).
- **CSV data loader** (`common/data_loader.py`) — Reads 1-minute OHLC CSV files into a pandas DataFrame with DatetimeIndex. Validates required columns (open, high, low, close, spread), checks for NaNs, positive spreads, and OHLC sanity (high >= max(open,close), low <= min(open,close)).
- **Multi-timeframe resampler** (`common/data_loader.py`) — Resamples 1-minute data to any larger timeframe (5m, 15m, 30m, 60m) using standard OHLC aggregation (open=first, high=max, low=min, close=last, spread=mean).

############### -> and these were checked and working correctly. 100% manualy and automaticaly.



=================================================================
ALSO TODAY WHAT HAS CHANGED:
-added summeries folder
-added manual folder in tests.
-added nas100_m1_mid_test.csv file. -> changed so its the primary test source.
================================================================

- **Tests** (`tests/test_data_loader.py`) — 13 automated tests covering CSV loading validation and resampling correctness. All passing.

## What comes next

- **Phase 2** — Signal generator: `Signal` dataclass, base strategy interface, MA crossover strategy with crossover/crossunder detection, SL/TP level calculation (entry +/- 2%), and one-signal-per-candle enforcement.
- **Phase 3** — Execution modes: price resolver for spread-on, spread-off (0.1% fee), and static custom spread modes.
- **Phase 4** — Capital accounting: portfolio state tracking, strategy-controlled allocation via signal.size, position stacking with weighted average entry, CLOSE signal handling (partial/full).


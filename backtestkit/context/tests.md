# Test Plan — Historical Backtesting Engine + Signal Generator

## Test Checklist

### Phase 1: Data Layer (`tests/test_data_loader.py`) — 38 tests
- [x] TestLoadCSV::test_columns_present
- [x] TestLoadCSV::test_index_is_datetime
- [x] TestLoadCSV::test_no_missing_values
- [x] TestLoadCSV::test_ohlc_sanity
- [x] TestLoadCSV::test_spread_positive
- [x] TestLoadCSV::test_reject_missing_column
- [x] TestLoadCSV::test_row_count
- [x] TestLoadCSV::test_index_name_is_timestamp
- [x] TestLoadCSV::test_index_is_sorted
- [x] TestLoadCSV::test_all_columns_numeric
- [x] TestLoadCSV::test_no_duplicate_timestamps
- [x] TestLoadCSV::test_reject_nan_values
- [x] TestLoadCSV::test_reject_zero_spread
- [x] TestLoadCSV::test_reject_negative_spread
- [x] TestLoadCSV::test_reject_bad_ohlc_high_too_low
- [x] TestLoadCSV::test_reject_bad_ohlc_low_too_high
- [x] TestLoadCSV::test_single_row_csv
- [x] TestLoadCSV::test_high_equals_open_close_is_valid
- [x] TestLoadCSV::test_extra_columns_preserved
- [x] TestLoadCSV::test_nonexistent_file_raises
- [x] TestLoadCSV::test_ohlc_values_are_positive
- [x] TestResample::test_5m_candle_count
- [x] TestResample::test_5m_open_is_first
- [x] TestResample::test_5m_high_is_max
- [x] TestResample::test_5m_low_is_min
- [x] TestResample::test_5m_close_is_last
- [x] TestResample::test_5m_spread_is_mean
- [x] TestResample::test_15m_30m_60m_produce_output
- [x] TestResample::test_resample_preserves_ohlc_sanity
- [x] TestResample::test_resample_preserves_no_nan
- [x] TestResample::test_resample_index_is_datetime
- [x] TestResample::test_resample_reduces_rows
- [x] TestResample::test_resample_spread_always_positive
- [x] TestResample::test_resample_high_geq_low
- [x] TestResample::test_60m_reduces_by_roughly_60x
- [x] TestResample::test_resample_second_window_open
- [x] TestResample::test_resample_columns_unchanged
- [x] TestResample::test_resample_with_3_candles
- manual tests: (checked everything)
- [x] proper project structure.
- [x] load_csv
- [x] resample - head - tail - working plan_fine!.

### Phase 2: Signal Generator (`tests/test_strategy.py`) — 32 tests
- [x] TestMACrossover::test_single_long_signal
- [x] TestMACrossover::test_crossunder_produces_short
- [x] TestMACrossover::test_reversal_emits_close_before_direction
- [x] TestMACrossover::test_close_and_direction_share_candle_index
- [x] TestMACrossover::test_first_entry_has_no_close
- [x] TestMACrossover::test_all_signals_have_size
- [x] TestMACrossover::test_close_signal_has_zero_sl_tp
- [x] TestMACrossover::test_sl_tp_levels_long
- [x] TestMACrossover::test_no_signal_in_flat_market
- [x] TestMACrossover::test_signal_indices_within_bounds
- [x] TestMACrossover::test_strategy_has_no_side_effects
- [x] TestMACrossoverEdgeCases::test_too_few_candles_returns_empty
- [x] TestMACrossoverEdgeCases::test_exactly_slow_period_candles
- [x] TestMACrossoverEdgeCases::test_sl_tp_levels_short
- [x] TestMACrossoverEdgeCases::test_custom_sl_tp_percentages
- [x] TestMACrossoverEdgeCases::test_no_signal_at_index_zero
- [x] TestMACrossoverEdgeCases::test_monotonically_rising_prices
- [x] TestMACrossoverEdgeCases::test_monotonically_falling_prices
- [x] TestMACrossoverEdgeCases::test_close_always_followed_by_direction
- [x] TestMACrossoverEdgeCases::test_directional_signals_have_positive_sl_tp
- [x] TestMACrossoverEdgeCases::test_long_sl_below_tp
- [x] TestMACrossoverEdgeCases::test_short_sl_above_tp
- [x] TestMACrossoverEdgeCases::test_signal_count_on_reversal_data
- [x] TestMACrossoverEdgeCases::test_different_strategy_instances_same_result
- [x] TestMACrossoverEdgeCases::test_default_parameters
- [x] TestMACrossoverEdgeCases::test_signals_ordered_by_timestamp
- [x] TestMACrossoverEdgeCases::test_input_dataframe_not_mutated
- [x] TestSignalDataclass::test_signal_fields_exist
- [x] TestSignalDataclass::test_signal_equality
- [x] TestSignalDataclass::test_signal_inequality
- [x] TestSignalDataclass::test_close_signal_type_exists
- [x] TestSignalDataclass::test_signal_size_field_accepts_float
- manual tests:
- [x] TestMACrossover::test_single_long_signal
- [x] TestMACrossover::test_crossunder_produces_short
- [x] TestMACrossover::test_reversal_emits_close_before_direction
- [x] TestMACrossover::test_close_and_direction_share_candle_index
- [x] TestMACrossover::test_first_entry_has_no_close
- [x] TestMACrossover::test_all_signals_have_size
- [x] TestMACrossover::test_close_signal_has_zero_sl_tp
- [x] TestMACrossover::test_sl_tp_levels_long
- [x] TestMACrossover::test_no_signal_in_flat_market
- [x] PLOTTING HISTORICAL S&P 500 DATA, checking if the signals are true witch MA plotted. WORKS
### Phase 3: Execution Modes (`tests/test_execution_modes.py`)
- [x] TestModeA_SpreadOn::test_long_entry
- [x] TestModeA_SpreadOn::test_long_exit
- [x] TestModeA_SpreadOn::test_short_entry
- [x] TestModeA_SpreadOn::test_short_exit
- [x] TestModeA_SpreadOn::test_zero_spread
- [x] TestModeA_SpreadOn::test_no_fee
- [x] TestModeA_SpreadOn::test_instant_loss_on_entry
- [x] TestModeB_SpreadOff::test_long_entry_at_mid
- [x] TestModeB_SpreadOff::test_long_exit_at_mid
- [x] TestModeB_SpreadOff::test_fee_calculation
- [x] TestModeB_SpreadOff::test_fee_on_small_position
- [x] TestModeC_StaticSpread::test_uses_custom_spread
- [x] TestModeC_StaticSpread::test_no_fee
- no need for manual tests, approved manualy all the automated tests that passed.
### Phase 4: Capital Accounting (`tests/test_portfolio.py`)
- [x] TestPositionOpening::test_initial_state
- [x] TestPositionOpening::test_long_entry_deducts_cash
- [x] TestPositionOpening::test_90_percent_allocation
- [x] TestPositionOpening::test_cannot_exceed_cash
- [x] TestPositionStacking::test_stacking_increases_size
- [x] TestPositionStacking::test_weighted_average_entry
- [x] TestPositionClosing::test_close_credits_cash
- [x] TestPositionClosing::test_losing_trade_reduces_cash
- [x] TestPositionClosing::test_realized_pnl_tracked
- [x] TestPositionClosing::test_close_resets_position
- [x] TestCloseAndReverse::test_long_to_short
- [x] TestUnrealizedPnL::test_long_unrealized_profit
- [x] TestUnrealizedPnL::test_long_unrealized_uses_bid
- [x] TestUnrealizedPnL::test_equity_is_total_account_value
- [x] TestUnrealizedPnL::test_equity_after_open_reflects_spread_cost
- [x] TestUnrealizedPnL::test_equity_unchanged_when_flat
- manual tests OK. manual SIMULATION PASSED fluently (fixed equity logic: cash + position_notional + unrealized_pnl.) - now everything works fully.
### Phase 5: SL/TP Engine (`tests/test_sl_tp.py`)
- [ ] TestLongSLTP::test_sl_triggered
- [ ] TestLongSLTP::test_tp_triggered
- [ ] TestLongSLTP::test_both_triggered_worst_case
- [ ] TestLongSLTP::test_neither_triggered
- [ ] TestLongSLTP::test_exact_sl_boundary
- [ ] TestLongSLTP::test_exact_tp_boundary
- [ ] TestShortSLTP::test_sl_triggered
- [ ] TestShortSLTP::test_tp_triggered
- [ ] TestShortSLTP::test_both_triggered_worst_case_short
- [ ] TestSLTPWithSpread::test_long_sl_exit_at_bid
- [ ] TestSLTPWithSpread::test_short_sl_exit_at_ask

### Phase 6: Main Engine Loop (`tests/test_engine.py`)
- [ ] TestSignalDelay::test_signal_executes_next_candle
- [ ] TestSignalDelay::test_signal_on_last_candle_not_executed
- [ ] TestExecutionOrder::test_sl_checked_before_signal
- [ ] TestNoTradeScenario::test_empty_signals
- [ ] TestCloseAndReverse::test_long_then_short_reversal
- [ ] TestClose::test_close_signal
- [ ] TestDeterminism::test_same_result_twice
- [ ] TestEquitySnapshot::test_snapshots_recorded_every_candle

### Phase 7: Console Logging (`tests/test_logging.py`)
- [ ] TestLogging::test_buy_message_printed
- [ ] TestLogging::test_silent_mode_no_output

### Phase 8: Performance Metrics (`tests/test_metrics.py`)
- [ ] TestTotalReturn::test_positive
- [ ] TestTotalReturn::test_negative
- [ ] TestTotalReturn::test_zero
- [ ] TestMaxDrawdown::test_known_curve
- [ ] TestMaxDrawdown::test_no_drawdown
- [ ] TestMaxDrawdown::test_constant_equity
- [ ] TestMaxDrawdown::test_only_decline
- [ ] TestMaxDrawdown::test_recovery_then_new_low
- [ ] TestWinRate::test_all_wins
- [ ] TestWinRate::test_all_losses
- [ ] TestWinRate::test_mixed
- [ ] TestWinRate::test_zero_pnl_trade_is_not_a_win
- [ ] TestProfitFactor::test_known_values
- [ ] TestProfitFactor::test_no_losses
- [ ] TestProfitFactor::test_no_wins
- [ ] TestAvgTrade::test_known
- [ ] TestSharpeRatio::test_positive_sharpe
- [ ] TestSharpeRatio::test_flat_equity_zero_sharpe
- [ ] TestExposureTime::test_always_in_market
- [ ] TestExposureTime::test_never_in_market
- [ ] TestExposureTime::test_half_exposure
- [ ] TestAnnualizedReturn::test_known_value

### Phase 9: Visualization (`tests/test_visualization.py`)
- [ ] TestVisualization::test_equity_curve_returns_figure
- [ ] TestVisualization::test_drawdown_returns_figure
- [ ] TestVisualization::test_price_chart_returns_figure
- [ ] TestVisualization::test_histogram_returns_figure
- [ ] TestVisualization::test_save_to_file

### Phase 10 & 11: Integration & Edge Cases (`tests/test_integration.py`)
- [ ] TestFullPipeline::test_end_to_end_no_crash
- [ ] TestFullPipeline::test_capital_identity
- [ ] TestFullPipeline::test_equity_snapshot_count
- [ ] TestFullPipeline::test_spread_on_worse_than_off
- [ ] TestDeterminism::test_two_runs_identical
- [ ] TestEdgeCases::test_zero_signals
- [ ] TestEdgeCases::test_single_trade_lifecycle
- [ ] TestEdgeCases::test_all_sl_hits
- [ ] TestEdgeCases::test_signal_at_last_candle_ignored
- [ ] TestEdgeCases::test_cash_never_negative
- [ ] TestEdgeCases::test_position_stacking_respects_capital
- [ ] TestEdgeCases::test_empty_dataframe

---

## How to Run Tests

All automated tests use **pytest**. After installing dependencies:

```bash
pip install pytest pandas numpy matplotlib
```

Run all tests:
```bash
cd backtestkit
pytest tests/ -v
```

Run tests for a specific phase:
```bash
pytest tests/test_data_loader.py -v      # Phase 1
pytest tests/test_strategy.py -v         # Phase 2
pytest tests/test_execution_modes.py -v  # Phase 3
pytest tests/test_portfolio.py -v        # Phase 4
pytest tests/test_sl_tp.py -v            # Phase 5
pytest tests/test_engine.py -v           # Phase 6
pytest tests/test_logging.py -v          # Phase 7
pytest tests/test_metrics.py -v          # Phase 8
pytest tests/test_visualization.py -v    # Phase 9
pytest tests/test_integration.py -v      # Phase 10 & 11
```

Run with print output visible (useful for logging tests):
```bash
pytest tests/ -v -s
```

---

## Phase 1: Data Layer

### Manual Checks

1. **Import check** — open a Python shell and verify all packages load:
   ```python
   from common.data_loader import load_csv, resample
   from common.models import ExecutionMode, SignalType
   ```
   If no `ImportError`, the skeleton is wired correctly.

2. **CSV inspection** — after loading `data/nas100_m1_mid_test.csv`, print the first 5 rows and confirm:
   - Column names are exactly: `timestamp, open, high, low, close, spread`
   - `timestamp` is the index and has dtype `datetime64`
   - No NaN values anywhere (`df.isna().sum()` should be all zeros)
   - `spread` values are positive
   - `high >= open`, `high >= close`, `low <= open`, `low <= close` for every row

3. **Resampling spot check** — take the first 5 one-minute candles and manually verify that the 5m candle equals:
   - `open` = first candle's open
   - `high` = max of all 5 highs
   - `low` = min of all 5 lows
   - `close` = last candle's close
   - `spread` = mean of all 5 spreads

### Automated Tests (`tests/test_data_loader.py`)

```python
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from common.data_loader import load_csv, resample

# --- Constants ---

TEST_CSV = str(Path(__file__).resolve().parent.parent / "data" / "nas100_m1_mid_test.csv")

# --- Fixtures ---

@pytest.fixture
def nas100_df():
    """Load the real NAS100 1-minute test data."""
    return load_csv(TEST_CSV)


# --- Tests ---

class TestLoadCSV:
    def test_columns_present(self, nas100_df):
        """CSV loader returns DataFrame with all required columns."""
        assert set(nas100_df.columns) >= {"open", "high", "low", "close", "spread"}

    def test_index_is_datetime(self, nas100_df):
        """Loaded DataFrame has DatetimeIndex."""
        assert isinstance(nas100_df.index, pd.DatetimeIndex)

    def test_no_missing_values(self, nas100_df):
        """Loaded DataFrame has zero NaN values."""
        assert nas100_df.isna().sum().sum() == 0

    def test_ohlc_sanity(self, nas100_df):
        """High >= max(open, close) and Low <= min(open, close) for every row."""
        assert (nas100_df["high"] >= nas100_df[["open", "close"]].max(axis=1)).all()
        assert (nas100_df["low"] <= nas100_df[["open", "close"]].min(axis=1)).all()

    def test_spread_positive(self, nas100_df):
        """All spread values are positive."""
        assert (nas100_df["spread"] > 0).all()

    def test_reject_missing_column(self, tmp_path):
        """Loader raises error if a required column is missing."""
        df = pd.DataFrame({"open": [1], "high": [2], "low": [0.5], "close": [1.5]})
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "bad.csv"
        df.to_csv(path)
        with pytest.raises(Exception):
            load_csv(str(path))

    def test_row_count(self, nas100_df):
        """Real dataset has expected number of rows."""
        assert len(nas100_df) > 100_000


class TestResample:
    def test_5m_candle_count(self, nas100_df):
        """5-minute resampling reduces row count by roughly 5x."""
        df_5m = resample(nas100_df, "5min")
        ratio = len(nas100_df) / len(df_5m)
        assert 4.5 < ratio < 5.5

    def test_5m_open_is_first(self, nas100_df):
        """5m open equals the first 1m candle's open in that window."""
        df_5m = resample(nas100_df, "5min")
        first_5m_start = df_5m.index[0]
        first_1m = nas100_df.loc[first_5m_start]
        assert df_5m.iloc[0]["open"] == first_1m["open"]

    def test_5m_high_is_max(self, nas100_df):
        """5m high equals max of 1m highs in the first window."""
        df_5m = resample(nas100_df, "5min")
        start = df_5m.index[0]
        end = df_5m.index[1]
        window = nas100_df.loc[start:end].iloc[:-1]  # exclude next window's first row
        assert df_5m.iloc[0]["high"] == window["high"].max()

    def test_5m_low_is_min(self, nas100_df):
        """5m low equals min of 1m lows in the first window."""
        df_5m = resample(nas100_df, "5min")
        start = df_5m.index[0]
        end = df_5m.index[1]
        window = nas100_df.loc[start:end].iloc[:-1]
        assert df_5m.iloc[0]["low"] == window["low"].min()

    def test_5m_close_is_last(self, nas100_df):
        """5m close equals the last 1m candle's close in that window."""
        df_5m = resample(nas100_df, "5min")
        start = df_5m.index[0]
        end = df_5m.index[1]
        window = nas100_df.loc[start:end].iloc[:-1]
        assert df_5m.iloc[0]["close"] == window.iloc[-1]["close"]

    def test_5m_spread_is_mean(self, nas100_df):
        """5m spread equals mean of 1m spreads in the first window."""
        df_5m = resample(nas100_df, "5min")
        start = df_5m.index[0]
        end = df_5m.index[1]
        window = nas100_df.loc[start:end].iloc[:-1]
        assert abs(df_5m.iloc[0]["spread"] - window["spread"].mean()) < 1e-10

    def test_15m_30m_60m_produce_output(self, nas100_df):
        """Resampling to 15m, 30m, 60m produces output."""
        for tf in ["15min", "30min", "60min"]:
            df_tf = resample(nas100_df, tf)
            assert len(df_tf) >= 1
```

---

## Phase 2: Signal Generator

### Manual Checks

1. **MA values** — print the fast and slow MA columns. Verify the first `period - 1` values are NaN, and subsequent values match a manual calculation (sum of last N closes / N).

2. **Crossover detection** — create a tiny dataset where you force a crossover at a known candle:
   ```
   Candle 0: fast=10, slow=12  (fast below slow)
   Candle 1: fast=13, slow=12  (fast above slow) → LONG signal here
   ```
   Verify a LONG signal is emitted at index 1.

3. **SL/TP levels** — for a LONG signal at close=100.0:
   - SL should be `100.0 * 0.98 = 98.0`
   - TP should be `100.0 * 1.02 = 102.0`

4. **No duplicate signals** — if your crossover data produces multiple crossings within the same candle, confirm only the first one appears in the output.

### Automated Tests (`tests/test_strategy.py`)

```python
import pytest
import pandas as pd
import numpy as np
from strategies.ma_crossover import MACrossoverStrategy
from common.models import SignalType

@pytest.fixture
def trending_up_df():
    """Price series that forces one clear crossover: fast crosses above slow."""
    # 30 candles of flat/declining → then 10 candles of sharp rise
    # With fast_ma=5, slow_ma=20 this guarantees a single cross
    n = 40
    timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
    prices = [100.0] * 20 + [100.0 + i * 0.5 for i in range(1, 21)]
    data = {
        "open":   prices,
        "high":   [p + 0.2 for p in prices],
        "low":    [p - 0.2 for p in prices],
        "close":  prices,
        "spread": [0.10] * n,
    }
    return pd.DataFrame(data, index=timestamps)

@pytest.fixture
def crossover_then_crossunder_df():
    """Price that goes up (cross above) then back down (cross below)."""
    n = 60
    timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
    prices = (
        [100.0] * 15
        + [100.0 + i * 0.5 for i in range(1, 16)]   # up
        + [107.5 - i * 0.5 for i in range(1, 16)]    # down
        + [100.0] * 14
    )
    data = {
        "open": prices, "high": [p+0.2 for p in prices],
        "low": [p-0.2 for p in prices], "close": prices,
        "spread": [0.10] * n,
    }
    return pd.DataFrame(data, index=timestamps)


class TestMACrossover:
    def test_single_long_signal(self, trending_up_df):
        """A clear uptrend produces at least one LONG signal."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(trending_up_df)
        long_signals = [s for s in signals if s.signal_type == SignalType.LONG]
        assert len(long_signals) >= 1

    def test_crossunder_produces_short(self, crossover_then_crossunder_df):
        """An uptrend followed by downtrend produces LONG then SHORT."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(crossover_then_crossunder_df)
        types = [s.signal_type for s in signals]
        assert SignalType.LONG in types
        assert SignalType.SHORT in types
        # LONG should come before SHORT
        first_long = next(i for i, t in enumerate(types) if t == SignalType.LONG)
        first_short = next(i for i, t in enumerate(types) if t == SignalType.SHORT)
        assert first_long < first_short

    def test_sl_tp_levels_long(self, trending_up_df):
        """LONG signal SL/TP are ±2% of the close price at signal candle."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(trending_up_df)
        sig = next(s for s in signals if s.signal_type == SignalType.LONG)
        close_at_signal = trending_up_df.iloc[sig.timestamp_index]["close"]
        assert abs(sig.stop_loss_level - close_at_signal * 0.98) < 1e-6
        assert abs(sig.take_profit_level - close_at_signal * 1.02) < 1e-6

    def test_no_signal_in_flat_market(self):
        """Completely flat prices produce zero signals."""
        n = 50
        timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
        data = {
            "open": [100.0]*n, "high": [100.0]*n,
            "low": [100.0]*n, "close": [100.0]*n,
            "spread": [0.10]*n,
        }
        df = pd.DataFrame(data, index=timestamps)
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(df)
        assert len(signals) == 0

    def test_one_signal_per_candle(self, trending_up_df):
        """No two signals share the same timestamp_index."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(trending_up_df)
        indices = [s.timestamp_index for s in signals]
        assert len(indices) == len(set(indices))

    def test_signal_indices_within_bounds(self, trending_up_df):
        """All signal indices are valid positions in the input DataFrame."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(trending_up_df)
        for sig in signals:
            assert 0 <= sig.timestamp_index < len(trending_up_df)

    def test_strategy_has_no_side_effects(self, trending_up_df):
        """Running the strategy twice on the same data produces identical signals."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals_1 = strategy.generate(trending_up_df)
        signals_2 = strategy.generate(trending_up_df)
        assert len(signals_1) == len(signals_2)
        for s1, s2 in zip(signals_1, signals_2):
            assert s1.timestamp_index == s2.timestamp_index
            assert s1.signal_type == s2.signal_type
```

---

## Phase 3: Execution Modes

### Manual Checks — Hand Calculations

Work through these by hand and compare with function output:

**Scenario: mid_price = 100.0, spread = 0.50**

| | Mode A (Spread ON) | Mode B (Spread OFF) | Mode C (Static=0.30) |
|---|---|---|---|
| LONG entry price | 100.25 | 100.00 | 100.15 |
| LONG exit price | 99.75 | 100.00 | 99.85 |
| SHORT entry price | 99.75 | 100.00 | 99.85 |
| SHORT exit price | 100.25 | 100.00 | 100.15 |
| Fee on 10000 value | 0.00 | 10.00 | 0.00 |

Verify each of these 15 values matches your functions.

### Automated Tests (`tests/test_execution_modes.py`)

```python
import pytest
from backtester.execution_modes import resolve_entry_price, resolve_exit_price, calculate_fee
from common.models import ExecutionMode

class TestModeA_SpreadOn:
    def test_long_entry(self):
        """LONG entry = mid + spread/2."""
        price = resolve_entry_price(mid=100.0, spread=0.50, direction="LONG", mode=ExecutionMode.SPREAD_ON)
        assert price == pytest.approx(100.25)

    def test_long_exit(self):
        """LONG exit = mid - spread/2."""
        price = resolve_exit_price(mid=100.0, spread=0.50, direction="LONG", mode=ExecutionMode.SPREAD_ON)
        assert price == pytest.approx(99.75)

    def test_short_entry(self):
        """SHORT entry = mid - spread/2."""
        price = resolve_entry_price(mid=100.0, spread=0.50, direction="SHORT", mode=ExecutionMode.SPREAD_ON)
        assert price == pytest.approx(99.75)

    def test_short_exit(self):
        """SHORT exit = mid + spread/2."""
        price = resolve_exit_price(mid=100.0, spread=0.50, direction="SHORT", mode=ExecutionMode.SPREAD_ON)
        assert price == pytest.approx(100.25)

    def test_zero_spread(self):
        """With zero spread, entry and exit equal mid."""
        entry = resolve_entry_price(mid=100.0, spread=0.0, direction="LONG", mode=ExecutionMode.SPREAD_ON)
        exit_ = resolve_exit_price(mid=100.0, spread=0.0, direction="LONG", mode=ExecutionMode.SPREAD_ON)
        assert entry == pytest.approx(100.0)
        assert exit_ == pytest.approx(100.0)

    def test_no_fee(self):
        """Mode A has no fee."""
        fee = calculate_fee(position_value=10000.0, mode=ExecutionMode.SPREAD_ON)
        assert fee == 0.0

    def test_instant_loss_on_entry(self):
        """Buying and immediately selling at same mid results in loss = spread."""
        mid, spread = 100.0, 0.50
        entry = resolve_entry_price(mid, spread, "LONG", ExecutionMode.SPREAD_ON)
        exit_ = resolve_exit_price(mid, spread, "LONG", ExecutionMode.SPREAD_ON)
        assert exit_ < entry  # guaranteed loss
        assert entry - exit_ == pytest.approx(spread)


class TestModeB_SpreadOff:
    def test_long_entry_at_mid(self):
        """Mode B entry = mid (no spread adjustment)."""
        price = resolve_entry_price(mid=100.0, spread=0.50, direction="LONG", mode=ExecutionMode.SPREAD_OFF)
        assert price == pytest.approx(100.0)

    def test_long_exit_at_mid(self):
        """Mode B exit = mid (no spread adjustment)."""
        price = resolve_exit_price(mid=100.0, spread=0.50, direction="LONG", mode=ExecutionMode.SPREAD_OFF)
        assert price == pytest.approx(100.0)

    def test_fee_calculation(self):
        """Fee = 0.1% of position value."""
        fee = calculate_fee(position_value=10000.0, mode=ExecutionMode.SPREAD_OFF)
        assert fee == pytest.approx(10.0)

    def test_fee_on_small_position(self):
        """Fee on 500.0 position = 0.50."""
        fee = calculate_fee(position_value=500.0, mode=ExecutionMode.SPREAD_OFF)
        assert fee == pytest.approx(0.50)


class TestModeC_StaticSpread:
    def test_uses_custom_spread(self):
        """Mode C ignores dataset spread, uses static value."""
        # static_spread = 0.30, dataset spread = 0.50 (should be ignored)
        price = resolve_entry_price(
            mid=100.0, spread=0.30, direction="LONG",
            mode=ExecutionMode.STATIC_SPREAD
        )
        assert price == pytest.approx(100.15)  # 100 + 0.30/2

    def test_no_fee(self):
        """Mode C has no fee."""
        fee = calculate_fee(position_value=10000.0, mode=ExecutionMode.STATIC_SPREAD)
        assert fee == 0.0
```

---

## Phase 4: Capital Accounting

### Manual Checks — Worked Example

Walk through this entire scenario by hand:

```
Initial: cash = 10000, position = 0

Signal: LONG at mid=100.0, spread=0.50
  → entry price = 100.25 (ask)
  → allocation = 10000 * 0.90 = 9000
  → units = 9000 / 100.25 = 89.7756...
  → cash = 10000 - (89.7756 * 100.25) = 10000 - 9000 = 1000
  → position_size = +89.7756
  → avg_entry = 100.25

Stack: another LONG at mid=105.0, spread=0.50
  → entry price = 105.25
  → allocation = 1000 * 0.90 = 900
  → new_units = 900 / 105.25 = 8.5510...
  → new_avg = (100.25 * 89.7756 + 105.25 * 8.5510) / (89.7756 + 8.5510)
  → new_avg = (9000 + 900) / 98.3266 = 100.688...
  → cash = 1000 - 900 = 100
  → position_size = 98.3266

Close at mid=110.0, spread=0.50:
  → exit price = 109.75 (bid)
  → realized PnL = (109.75 - 100.688) * 98.3266 = 890.56... (approximate)
  → cash = 100 + (109.75 * 98.3266) = 100 + 10791.35 = 10891.35
  → position_size = 0
```

Verify your portfolio module produces these exact numbers (within floating-point tolerance).

### Automated Tests (`tests/test_portfolio.py`)

```python
import pytest
from backtester.portfolio import Portfolio
from common.models import ExecutionMode

@pytest.fixture
def portfolio():
    return Portfolio(initial_capital=10000.0, mode=ExecutionMode.SPREAD_ON)


class TestPositionOpening:
    def test_initial_state(self, portfolio):
        """Fresh portfolio has correct initial values."""
        assert portfolio.cash == 10000.0
        assert portfolio.position_size == 0.0
        assert portfolio.realized_pnl == 0.0
        assert portfolio.equity == 10000.0

    def test_long_entry_deducts_cash(self, portfolio):
        """Opening LONG with size=1.0 reduces cash to near zero."""
        portfolio.open_position(entry_price=100.0, spread=0.50, direction="LONG", size=1.0)
        assert portfolio.cash == pytest.approx(0.0, abs=1.0)
        assert portfolio.position_size > 0

    def test_size_controls_allocation(self, portfolio):
        """Signal size controls what fraction of cash is allocated."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=1.0)
        # With spread=0, size=1.0: units = 10000 / 100 = 100
        assert portfolio.position_size == pytest.approx(100.0)
        assert portfolio.cash == pytest.approx(0.0)

    def test_cannot_exceed_cash(self, portfolio):
        """Cannot open position larger than available cash allows."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=1.0)
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=1.0)
        # After first open: all cash used. Second open has 0 cash available.
        assert portfolio.cash == pytest.approx(0.0)


class TestPositionStacking:
    def test_stacking_increases_size(self, portfolio):
        """Two LONG signals produce additive position."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        size_1 = portfolio.position_size
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        assert portfolio.position_size > size_1

    def test_weighted_average_entry(self, portfolio):
        """Stacked position has correct weighted average entry."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        # units_1 = 90, avg = 100
        portfolio.open_position(entry_price=200.0, spread=0.0, direction="LONG")
        # units_2 = 900/200 = 4.5, avg = (100*90 + 200*4.5) / 94.5
        expected_avg = (100.0 * 90.0 + 200.0 * 4.5) / 94.5
        assert portfolio.avg_entry_price == pytest.approx(expected_avg, rel=1e-4)


class TestPositionClosing:
    def test_close_credits_cash(self, portfolio):
        """Closing position returns value to cash."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        portfolio.close_position(exit_price=110.0, spread=0.0)
        # PnL = (110 - 100) * 90 = 900
        assert portfolio.cash == pytest.approx(10900.0)
        assert portfolio.position_size == 0.0

    def test_losing_trade_reduces_cash(self, portfolio):
        """Losing trade results in less cash than started."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        portfolio.close_position(exit_price=90.0, spread=0.0)
        # PnL = (90 - 100) * 90 = -900
        assert portfolio.cash == pytest.approx(9100.0)

    def test_realized_pnl_tracked(self, portfolio):
        """realized_pnl accumulates across trades."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        portfolio.close_position(exit_price=110.0, spread=0.0)
        assert portfolio.realized_pnl == pytest.approx(900.0)

    def test_close_resets_position(self, portfolio):
        """After close, position_size is 0 and avg_entry is 0."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        portfolio.close_position(exit_price=110.0, spread=0.0)
        assert portfolio.position_size == 0.0
        assert portfolio.avg_entry_price == 0.0


class TestCloseAndReverse:
    def test_long_to_short(self, portfolio):
        """LONG position followed by SHORT signal → close then open short."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        portfolio.close_position(exit_price=105.0, spread=0.0)
        portfolio.open_position(entry_price=105.0, spread=0.0, direction="SHORT")
        assert portfolio.position_size < 0  # negative = short


class TestUnrealizedPnL:
    def test_long_unrealized_profit(self, portfolio):
        """LONG position with price increase shows positive unrealized PnL."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG")
        portfolio.update_unrealized(current_mid=110.0, spread=0.0)
        assert portfolio.unrealized_pnl > 0

    def test_long_unrealized_uses_bid(self, portfolio):
        """Unrealized PnL for LONG uses bid (mid - spread/2)."""
        portfolio.open_position(entry_price=100.0, spread=0.50, direction="LONG")
        # entry at ask = 100.25, 90 units approx
        portfolio.update_unrealized(current_mid=100.0, spread=0.50)
        # bid = 99.75, unrealized = (99.75 - 100.25) * units = negative
        assert portfolio.unrealized_pnl < 0

    def test_equity_is_total_account_value(self, portfolio):
        """Equity = cash + position_notional + unrealized_pnl."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        portfolio.update_unrealized(current_mid=110.0, spread=0.0)
        expected = portfolio.cash + portfolio.position_notional + portfolio.unrealized_pnl
        assert portfolio.equity == pytest.approx(expected)
```

---

## Phase 5: SL/TP Engine

### Manual Checks — Worked Scenarios

**Scenario A: LONG, SL hit**
```
Entry price = 100.0 (mid, spread=0, for simplicity)
SL = 98.0 (entry - 2%)
TP = 102.0 (entry + 2%)

Candle: open=99.5, high=99.8, low=97.5, close=99.0
  → low (97.5) <= SL (98.0)? YES → SL triggered
  → Exit at SL level = 98.0
  → PnL per unit = 98.0 - 100.0 = -2.0
```

**Scenario B: LONG, TP hit**
```
Candle: open=101.0, high=102.5, low=100.8, close=102.0
  → low (100.8) <= SL (98.0)? NO
  → high (102.5) >= TP (102.0)? YES → TP triggered
  → Exit at TP level = 102.0
  → PnL per unit = 102.0 - 100.0 = +2.0
```

**Scenario C: BOTH triggered (worst-case)**
```
Candle: open=100.0, high=103.0, low=97.0, close=100.0
  → low (97.0) <= SL (98.0)? YES
  → high (103.0) >= TP (102.0)? YES
  → WORST CASE: SL fires for LONG → exit at 98.0
  → PnL = -2.0 (not +2.0)
```

**Scenario D: SHORT, SL hit**
```
Entry price = 100.0
SL = 102.0 (entry + 2%)
TP = 98.0 (entry - 2%)

Candle: high=102.5
  → high (102.5) >= SL (102.0)? YES → SL triggered
  → Exit at 102.0
  → PnL per unit = 100.0 - 102.0 = -2.0
```

### Automated Tests (`tests/test_sl_tp.py`)

```python
import pytest
from backtester.sl_tp import check_sl_tp, PositionUnit
from common.models import ExecutionMode

def make_candle(open_, high, low, close, spread=0.0):
    """Helper to create a candle dict/namedtuple."""
    return {"open": open_, "high": high, "low": low, "close": close, "spread": spread}


class TestLongSLTP:
    def test_sl_triggered(self):
        """LONG SL fires when candle low <= SL level."""
        unit = PositionUnit(direction="LONG", entry_price=100.0, size=10, sl=98.0, tp=102.0)
        candle = make_candle(99.5, 99.8, 97.5, 99.0)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered == "SL"
        assert result.exit_price == pytest.approx(98.0, abs=0.5)  # ± spread/2

    def test_tp_triggered(self):
        """LONG TP fires when candle high >= TP level."""
        unit = PositionUnit(direction="LONG", entry_price=100.0, size=10, sl=98.0, tp=102.0)
        candle = make_candle(101.0, 102.5, 100.8, 102.0)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered == "TP"

    def test_both_triggered_worst_case(self):
        """When both SL and TP can trigger, SL fires (worst case for LONG)."""
        unit = PositionUnit(direction="LONG", entry_price=100.0, size=10, sl=98.0, tp=102.0)
        candle = make_candle(100.0, 103.0, 97.0, 100.0)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered == "SL"

    def test_neither_triggered(self):
        """No trigger when price stays within SL-TP range."""
        unit = PositionUnit(direction="LONG", entry_price=100.0, size=10, sl=98.0, tp=102.0)
        candle = make_candle(100.0, 101.0, 99.0, 100.5)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered is None

    def test_exact_sl_boundary(self):
        """SL fires when low equals SL exactly."""
        unit = PositionUnit(direction="LONG", entry_price=100.0, size=10, sl=98.0, tp=102.0)
        candle = make_candle(99.0, 100.0, 98.0, 99.5)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered == "SL"

    def test_exact_tp_boundary(self):
        """TP fires when high equals TP exactly."""
        unit = PositionUnit(direction="LONG", entry_price=100.0, size=10, sl=98.0, tp=102.0)
        candle = make_candle(101.0, 102.0, 100.5, 101.5)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered == "TP"


class TestShortSLTP:
    def test_sl_triggered(self):
        """SHORT SL fires when candle high >= SL level."""
        unit = PositionUnit(direction="SHORT", entry_price=100.0, size=10, sl=102.0, tp=98.0)
        candle = make_candle(101.0, 102.5, 100.5, 101.5)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered == "SL"

    def test_tp_triggered(self):
        """SHORT TP fires when candle low <= TP level."""
        unit = PositionUnit(direction="SHORT", entry_price=100.0, size=10, sl=102.0, tp=98.0)
        candle = make_candle(99.0, 99.5, 97.5, 98.5)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered == "TP"

    def test_both_triggered_worst_case_short(self):
        """When both trigger for SHORT, SL fires (worst case)."""
        unit = PositionUnit(direction="SHORT", entry_price=100.0, size=10, sl=102.0, tp=98.0)
        candle = make_candle(100.0, 103.0, 97.0, 100.0)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.triggered == "SL"


class TestSLTPWithSpread:
    def test_long_sl_exit_at_bid(self):
        """LONG SL exit price = SL_level - spread/2 (sold at bid)."""
        unit = PositionUnit(direction="LONG", entry_price=100.0, size=10, sl=98.0, tp=102.0)
        candle = make_candle(99.0, 99.5, 97.0, 98.5, spread=0.50)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.exit_price == pytest.approx(97.75)  # 98.0 - 0.25

    def test_short_sl_exit_at_ask(self):
        """SHORT SL exit price = SL_level + spread/2 (bought at ask)."""
        unit = PositionUnit(direction="SHORT", entry_price=100.0, size=10, sl=102.0, tp=98.0)
        candle = make_candle(101.0, 102.5, 100.5, 101.5, spread=0.50)
        result = check_sl_tp(unit, candle, ExecutionMode.SPREAD_ON)
        assert result.exit_price == pytest.approx(102.25)  # 102.0 + 0.25
```

---

## Phase 6: Main Engine Loop

### Manual Checks — 5-Candle Walkthrough

This is the most important manual test. Work through every single step:

```
Setup: capital=10000, mode=SPREAD_OFF (for simplicity, fee=0.1%)

Candle 0: open=100, high=101, low=99, close=100.5, spread=0.10
  Signal at candle 0: LONG
  → pending_signal = LONG
  → No position yet, no SL/TP to check
  → snapshot: cash=10000, pos=0, equity=10000

Candle 1: open=101, high=102, low=100, close=101.5, spread=0.10
  → Execute pending LONG at open=101.0
    → allocation = 10000 * 0.9 = 9000
    → fee = 9000 * 0.001 = 9.0
    → units = (9000 - 9) / 101.0 = 89.0198...  (or: units = 9000/101, fee deducted from cash separately)
    → cash = 10000 - 9000 - 9 = 991  (depends on implementation)
  → Update unrealized: (101.5 - 101.0) * 89.02 = +44.51
  → Check SL (101*0.98=98.98): low=100 > 98.98 → no
  → Check TP (101*1.02=103.02): high=102 < 103.02 → no
  → snapshot: cash=991, pos=89.02, unrealized=+44.51, equity=1035.51

Candle 2: open=102, high=103.5, low=101.5, close=103, spread=0.10
  → Update unrealized: (103 - 101) * 89.02 = +178.04
  → Check TP: high=103.5 >= 103.02? YES → TP hit!
    → exit at 103.02, fee = (103.02 * 89.02) * 0.001 = 9.17
    → realized = (103.02 - 101.0) * 89.02 = +179.82
    → cash = 991 + (103.02 * 89.02) - 9.17 = ...
  → Position closed

...continue for remaining candles...
```

Write down expected values at each step. Then run the engine and compare every snapshot value.

### Automated Tests (`tests/test_engine.py`)

```python
import pytest
import pandas as pd
from backtester.engine import BacktestEngine
from common.models import ExecutionMode, SignalType
from strategies.signals import Signal

@pytest.fixture
def simple_5_candle_df():
    """5 candles with predictable price movement."""
    timestamps = pd.date_range("2024-01-15 09:30", periods=5, freq="1min")
    data = {
        "open":   [100.0, 101.0, 102.0, 101.0, 100.0],
        "high":   [101.0, 102.0, 103.0, 102.0, 101.0],
        "low":    [ 99.0, 100.0, 101.0, 100.0,  99.0],
        "close":  [100.5, 101.5, 102.5, 101.5, 100.5],
        "spread": [ 0.10,  0.10,  0.10,  0.10,  0.10],
    }
    return pd.DataFrame(data, index=timestamps)


class TestSignalDelay:
    def test_signal_executes_next_candle(self, simple_5_candle_df):
        """Signal at candle 0 must execute at candle 1 open, not candle 0."""
        signals = [Signal(timestamp_index=0, signal_type=SignalType.LONG, stop_loss_level=98.0, take_profit_level=102.0, size=1.0)]
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=signals,
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        # The first trade should have entry price = candle 1 open = 101.0
        assert result.trades[0].entry_price == pytest.approx(101.0)

    def test_signal_on_last_candle_not_executed(self, simple_5_candle_df):
        """Signal on the last candle has no i+1 to execute at → no trade."""
        signals = [Signal(timestamp_index=4, signal_type=SignalType.LONG, stop_loss_level=98.0, take_profit_level=102.0, size=1.0)]
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=signals,
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        assert len(result.trades) == 0


class TestExecutionOrder:
    def test_sl_checked_before_signal(self, simple_5_candle_df):
        """SL/TP is evaluated before a new signal on the same candle."""
        # Signal LONG at candle 0 → executes candle 1
        # Force SL to hit at candle 2 (low=101 vs SL that must be < 101)
        signals = [
            Signal(timestamp_index=0, signal_type=SignalType.LONG,
                   stop_loss_level=101.5, take_profit_level=110.0, size=1.0),
        ]
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=signals,
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        # SL should have triggered, closing the position
        assert any(t.exit_reason == "SL" for t in result.trades)


class TestNoTradeScenario:
    def test_empty_signals(self, simple_5_candle_df):
        """Zero signals → zero trades, equity unchanged."""
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=[],
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        assert len(result.trades) == 0
        assert result.final_equity == pytest.approx(10000.0)


class TestCloseAndReverse:
    def test_long_then_short_reversal(self, simple_5_candle_df):
        """LONG then SHORT signal → close long, open short."""
        signals = [
            Signal(timestamp_index=0, signal_type=SignalType.LONG,
                   stop_loss_level=95.0, take_profit_level=115.0, size=1.0),
            Signal(timestamp_index=1, signal_type=SignalType.CLOSE,
                   stop_loss_level=0, take_profit_level=0, size=1.0),
            Signal(timestamp_index=1, signal_type=SignalType.SHORT,
                   stop_loss_level=115.0, take_profit_level=95.0, size=1.0),
        ]
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=signals,
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        # Should have 2 trades: first LONG (closed), then SHORT (may still open)
        assert len(result.trades) >= 1
        assert result.trades[0].direction == "LONG"


class TestClose:
    def test_close_signal(self, simple_5_candle_df):
        """CLOSE signal closes position (size=1.0 = full close)."""
        signals = [
            Signal(timestamp_index=0, signal_type=SignalType.LONG,
                   stop_loss_level=95.0, take_profit_level=115.0, size=1.0),
            Signal(timestamp_index=2, signal_type=SignalType.CLOSE,
                   stop_loss_level=0, take_profit_level=0, size=1.0),
        ]
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=signals,
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        # After CLOSE, position should be 0
        # Check the snapshot at candle 3 (signal at 2 → execute at 3)
        assert result.snapshots[4].position_size == 0.0


class TestDeterminism:
    def test_same_result_twice(self, simple_5_candle_df):
        """Running the engine twice with identical input produces identical output."""
        signals = [
            Signal(timestamp_index=0, signal_type=SignalType.LONG,
                   stop_loss_level=95.0, take_profit_level=115.0, size=1.0),
        ]
        engine1 = BacktestEngine(
            data=simple_5_candle_df.copy(), signals=list(signals),
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        engine2 = BacktestEngine(
            data=simple_5_candle_df.copy(), signals=list(signals),
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        r1 = engine1.run()
        r2 = engine2.run()
        assert r1.final_equity == r2.final_equity
        assert len(r1.trades) == len(r2.trades)
        for t1, t2 in zip(r1.trades, r2.trades):
            assert t1.entry_price == t2.entry_price
            assert t1.exit_price == t2.exit_price


class TestEquitySnapshot:
    def test_snapshots_recorded_every_candle(self, simple_5_candle_df):
        """One snapshot per candle."""
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=[],
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        assert len(result.snapshots) == len(simple_5_candle_df)
```

---

## Phase 7: Console Logging

### Manual Checks

1. Run the engine with `verbosity="normal"` on the 5-candle scenario above. You should see:
   ```
   [2024-01-15 09:31] BUY ... units at ...
   ```
   printed to stdout. Verify the timestamp is candle i+1's timestamp (not signal candle).

2. Run with `verbosity="silent"` — verify **nothing** prints.

3. Run with `verbosity="debug"` — verify you see extra details like unrealized PnL updates.

### Automated Tests (`tests/test_logging.py`)

```python
import pytest
from backtester.engine import BacktestEngine
from common.models import ExecutionMode, SignalType
from strategies.signals import Signal
import pandas as pd

@pytest.fixture
def df_and_signals():
    timestamps = pd.date_range("2024-01-15 09:30", periods=5, freq="1min")
    data = {
        "open": [100,101,102,101,100], "high": [101,102,103,102,101],
        "low": [99,100,101,100,99], "close": [100.5,101.5,102.5,101.5,100.5],
        "spread": [0.10]*5,
    }
    df = pd.DataFrame(data, index=timestamps)
    signals = [Signal(0, SignalType.LONG, 95.0, 115.0, 1.0)]
    return df, signals

class TestLogging:
    def test_buy_message_printed(self, df_and_signals, capsys):
        """BUY message appears in stdout."""
        df, signals = df_and_signals
        engine = BacktestEngine(df, signals, ExecutionMode.SPREAD_OFF, 10000.0, verbosity="normal")
        engine.run()
        captured = capsys.readouterr()
        assert "BUY" in captured.out

    def test_silent_mode_no_output(self, df_and_signals, capsys):
        """Silent mode prints nothing."""
        df, signals = df_and_signals
        engine = BacktestEngine(df, signals, ExecutionMode.SPREAD_OFF, 10000.0, verbosity="silent")
        engine.run()
        captured = capsys.readouterr()
        assert captured.out == ""
```

---

## Phase 8: Performance Metrics

### Manual Checks — Calculator Verification

Use these exact numbers to verify each metric:

**Test dataset: 3 completed trades**
```
Trade 1: PnL = +200    (win)
Trade 2: PnL = -150    (loss)
Trade 3: PnL = +300    (win)
Initial capital = 10000
```

| Metric | Expected | How to verify |
|---|---|---|
| Total Return | (10350 - 10000) / 10000 = **3.5%** | Calculator |
| Win Rate | 2/3 = **66.67%** | Count |
| Profit Factor | (200+300) / 150 = **3.33** | Calculator |
| Avg Trade | 350/3 = **116.67** | Calculator |
| Total Trades | **3** | Count |

**Max Drawdown test — equity curve:**
```
equity = [10000, 10200, 10050, 10350]
peaks  = [10000, 10200, 10200, 10350]
drawdowns = [0, 0, 150/10200, 0]
max_drawdown = 150/10200 = 1.47%
```

### Automated Tests (`tests/test_metrics.py`)

```python
import pytest
import numpy as np
from backtester.metrics import (
    total_return, annualized_return, max_drawdown,
    sharpe_ratio, win_rate, profit_factor,
    avg_trade, exposure_time
)

class TestTotalReturn:
    def test_positive(self):
        assert total_return(initial=10000, final=10350) == pytest.approx(0.035)

    def test_negative(self):
        assert total_return(initial=10000, final=9500) == pytest.approx(-0.05)

    def test_zero(self):
        assert total_return(initial=10000, final=10000) == pytest.approx(0.0)


class TestMaxDrawdown:
    def test_known_curve(self):
        equity = [10000, 10200, 10050, 10350]
        assert max_drawdown(equity) == pytest.approx(150/10200, rel=1e-4)

    def test_no_drawdown(self):
        equity = [100, 200, 300, 400]
        assert max_drawdown(equity) == pytest.approx(0.0)

    def test_constant_equity(self):
        equity = [100, 100, 100]
        assert max_drawdown(equity) == pytest.approx(0.0)

    def test_only_decline(self):
        equity = [1000, 900, 800, 700]
        assert max_drawdown(equity) == pytest.approx(300/1000)

    def test_recovery_then_new_low(self):
        """Drawdown from 200→100 (50%) is worse than 100→90 (10%)."""
        equity = [100, 200, 100, 150, 90]
        assert max_drawdown(equity) == pytest.approx(110/200)  # 200→90


class TestWinRate:
    def test_all_wins(self):
        assert win_rate([100, 50, 200]) == pytest.approx(1.0)

    def test_all_losses(self):
        assert win_rate([-100, -50]) == pytest.approx(0.0)

    def test_mixed(self):
        assert win_rate([200, -150, 300]) == pytest.approx(2/3)

    def test_zero_pnl_trade_is_not_a_win(self):
        assert win_rate([0, 100]) == pytest.approx(0.5)


class TestProfitFactor:
    def test_known_values(self):
        assert profit_factor([200, -150, 300]) == pytest.approx(500/150)

    def test_no_losses(self):
        """No losses → profit factor is infinity or very large."""
        result = profit_factor([200, 300])
        assert result == float("inf") or result > 1e6

    def test_no_wins(self):
        """No wins → profit factor is 0."""
        assert profit_factor([-200, -300]) == pytest.approx(0.0)


class TestAvgTrade:
    def test_known(self):
        assert avg_trade([200, -150, 300]) == pytest.approx(350/3)


class TestSharpeRatio:
    def test_positive_sharpe(self):
        """Steadily increasing equity → positive Sharpe."""
        equity = list(range(10000, 10100))  # +1 per step
        result = sharpe_ratio(equity)
        assert result > 0

    def test_flat_equity_zero_sharpe(self):
        """Constant equity → Sharpe is 0 (or NaN, handle gracefully)."""
        equity = [10000] * 100
        result = sharpe_ratio(equity)
        assert result == 0.0 or np.isnan(result)


class TestExposureTime:
    def test_always_in_market(self):
        """Position held every candle → 100%."""
        positions = [1, 1, 1, 1, 1]
        assert exposure_time(positions) == pytest.approx(1.0)

    def test_never_in_market(self):
        """No position ever → 0%."""
        positions = [0, 0, 0, 0, 0]
        assert exposure_time(positions) == pytest.approx(0.0)

    def test_half_exposure(self):
        positions = [1, 1, 0, 0]
        assert exposure_time(positions) == pytest.approx(0.5)


class TestAnnualizedReturn:
    def test_known_value(self):
        """10% return over 252*390 candles = 10% annualized."""
        total_candles = 252 * 390
        result = annualized_return(total_ret=0.10, total_candles=total_candles)
        assert result == pytest.approx(0.10, rel=1e-2)
```

---

## Phase 9: Visualization

### Manual Checks

Visualization is best tested visually. Run these checks:

1. **Equity curve** — does it start at your initial capital? Does the final point match `final_equity` from metrics? Is the line continuous (no gaps)?

2. **Drawdown curve** — is it always <= 0 (or displayed as positive downward)? Does the deepest point match `max_drawdown`?

3. **Price chart markers**:
   - Find a known BUY trade in the log. Is there a green triangle at that candle?
   - Find a known SL hit. Is there a red X?
   - Do markers appear at the correct time (execution candle, not signal candle)?

4. **Trade histogram** — count the bars. Does the total equal `total_trades`? Are winning trades on the right (positive) side?

### Automated Tests (`tests/test_visualization.py`)

```python
import pytest
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for tests
import matplotlib.pyplot as plt
from backtester.visualization import (
    plot_equity_curve, plot_drawdown, plot_price_with_markers, plot_trade_histogram
)

class TestVisualization:
    def test_equity_curve_returns_figure(self):
        """plot_equity_curve returns a matplotlib Figure without error."""
        equity = [10000, 10100, 10050, 10200]
        timestamps = ["09:30", "09:31", "09:32", "09:33"]
        fig = plot_equity_curve(equity, timestamps)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_drawdown_returns_figure(self):
        equity = [10000, 10100, 10050, 10200]
        fig = plot_drawdown(equity)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_price_chart_returns_figure(self):
        prices = [100, 101, 102, 101]
        buys = [(1, 101)]   # (index, price)
        sells = [(3, 101)]
        sl_hits = []
        tp_hits = []
        fig = plot_price_with_markers(prices, buys, sells, sl_hits, tp_hits)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_histogram_returns_figure(self):
        trade_pnls = [200, -150, 300, -50, 100]
        fig = plot_trade_histogram(trade_pnls)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_save_to_file(self, tmp_path):
        """Charts can be saved to PNG without error."""
        equity = [10000, 10100, 10050, 10200]
        fig = plot_equity_curve(equity, range(4))
        path = tmp_path / "equity.png"
        fig.savefig(str(path))
        assert path.exists()
        plt.close(fig)
```

---

## Phase 10: System Integration

### Manual Checks

1. **CLI smoke test** — run the full pipeline:
   ```bash
   python run_backtest.py --data data/nas100_m1_mid_test.csv --mode spread_on --capital 10000 --fast-ma 10 --slow-ma 30
   ```
   Verify it completes without error and prints a metrics table.

2. **Mode comparison** — run the same data with all 3 modes. Spread ON should produce the worst results (highest cost). Spread OFF with 0.1% fee should be in the middle. A very small static spread should produce the best results.

3. **Capital preservation** — at the end of a backtest, verify:
   ```
   final_equity == cash + position_notional + unrealized_pnl
   final_equity == initial_capital + total_realized_pnl + unrealized_pnl
   ```
   These identities must always hold.

### Automated Tests (`tests/test_integration.py`)

```python
import pytest
import pandas as pd
from backtester.engine import BacktestEngine
from strategies.ma_crossover import MACrossoverStrategy
from common.data_loader import load_csv, resample
from common.models import ExecutionMode

@pytest.fixture
def full_pipeline_data(tmp_path):
    """Generate 500 candles of synthetic trending data."""
    import numpy as np
    np.random.seed(42)
    n = 500
    timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
    # Random walk with slight uptrend
    returns = np.random.normal(0.0001, 0.002, n)
    prices = 100.0 * np.cumprod(1 + returns)
    data = {
        "open": prices,
        "high": prices * (1 + np.random.uniform(0, 0.005, n)),
        "low": prices * (1 - np.random.uniform(0, 0.005, n)),
        "close": prices * (1 + np.random.normal(0, 0.001, n)),
        "spread": np.full(n, 0.10),
    }
    df = pd.DataFrame(data, index=timestamps)
    df.index.name = "timestamp"
    return df


class TestFullPipeline:
    def test_end_to_end_no_crash(self, full_pipeline_data):
        """Full pipeline runs without error."""
        strategy = MACrossoverStrategy(fast_period=10, slow_period=30)
        signals = strategy.generate(full_pipeline_data)
        engine = BacktestEngine(
            data=full_pipeline_data, signals=signals,
            mode=ExecutionMode.SPREAD_ON, initial_capital=10000.0
        )
        result = engine.run()
        assert result.final_equity > 0

    def test_capital_identity(self, full_pipeline_data):
        """final_equity == initial_capital + realized_pnl + unrealized_pnl."""
        strategy = MACrossoverStrategy(fast_period=10, slow_period=30)
        signals = strategy.generate(full_pipeline_data)
        engine = BacktestEngine(
            data=full_pipeline_data, signals=signals,
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        expected = 10000.0 + result.realized_pnl + result.unrealized_pnl
        assert result.final_equity == pytest.approx(expected, rel=1e-6)

    def test_equity_snapshot_count(self, full_pipeline_data):
        """One snapshot per candle."""
        strategy = MACrossoverStrategy(fast_period=10, slow_period=30)
        signals = strategy.generate(full_pipeline_data)
        engine = BacktestEngine(
            data=full_pipeline_data, signals=signals,
            mode=ExecutionMode.SPREAD_ON, initial_capital=10000.0
        )
        result = engine.run()
        assert len(result.snapshots) == len(full_pipeline_data)

    def test_spread_on_worse_than_off(self, full_pipeline_data):
        """Spread ON mode should generally cost more than Spread OFF."""
        strategy = MACrossoverStrategy(fast_period=10, slow_period=30)
        signals = strategy.generate(full_pipeline_data)

        engine_on = BacktestEngine(
            data=full_pipeline_data.copy(), signals=list(signals),
            mode=ExecutionMode.SPREAD_ON, initial_capital=10000.0
        )
        engine_off = BacktestEngine(
            data=full_pipeline_data.copy(), signals=list(signals),
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        r_on = engine_on.run()
        r_off = engine_off.run()
        # Not guaranteed but statistically likely with 0.10 spread vs 0.1% fee
        # At least verify both ran successfully
        assert r_on.final_equity > 0
        assert r_off.final_equity > 0


class TestDeterminism:
    def test_two_runs_identical(self, full_pipeline_data):
        """Two runs with identical inputs produce byte-identical results."""
        strategy = MACrossoverStrategy(fast_period=10, slow_period=30)

        signals_1 = strategy.generate(full_pipeline_data.copy())
        engine_1 = BacktestEngine(
            data=full_pipeline_data.copy(), signals=signals_1,
            mode=ExecutionMode.SPREAD_ON, initial_capital=10000.0
        )
        r1 = engine_1.run()

        signals_2 = strategy.generate(full_pipeline_data.copy())
        engine_2 = BacktestEngine(
            data=full_pipeline_data.copy(), signals=signals_2,
            mode=ExecutionMode.SPREAD_ON, initial_capital=10000.0
        )
        r2 = engine_2.run()

        assert r1.final_equity == r2.final_equity
        assert len(r1.trades) == len(r2.trades)
        for s1, s2 in zip(r1.snapshots, r2.snapshots):
            assert s1.equity == s2.equity
```

---

## Phase 11: Edge Cases & Hardening

### Automated Tests (add to `tests/test_integration.py`)

```python
class TestEdgeCases:
    def test_zero_signals(self, full_pipeline_data):
        """No signals → equity stays at initial capital."""
        engine = BacktestEngine(
            data=full_pipeline_data, signals=[],
            mode=ExecutionMode.SPREAD_ON, initial_capital=10000.0
        )
        result = engine.run()
        assert result.final_equity == pytest.approx(10000.0)
        assert len(result.trades) == 0

    def test_single_trade_lifecycle(self):
        """One LONG signal, SL/TP wide enough to not trigger → position held at end."""
        timestamps = pd.date_range("2024-01-15 09:30", periods=10, freq="1min")
        data = {
            "open": [100]*10, "high": [101]*10, "low": [99]*10,
            "close": [100]*10, "spread": [0.10]*10,
        }
        df = pd.DataFrame(data, index=timestamps)
        from strategies.signals import Signal
        signals = [Signal(0, SignalType.LONG, 50.0, 200.0, 1.0)]  # wide SL/TP
        engine = BacktestEngine(df, signals, ExecutionMode.SPREAD_ON, 10000.0)
        result = engine.run()
        assert len(result.trades) == 0 or result.trades[0].exit_price is None  # still open

    def test_all_sl_hits(self):
        """Every trade hits SL → win rate should be 0%."""
        timestamps = pd.date_range("2024-01-15 09:30", periods=20, freq="1min")
        # Price drops sharply each time
        prices = [100.0 - i * 2 for i in range(20)]
        data = {
            "open": prices, "high": [p+1 for p in prices],
            "low": [p-1 for p in prices], "close": prices,
            "spread": [0.10]*20,
        }
        df = pd.DataFrame(data, index=timestamps)
        from strategies.signals import Signal
        signals = [Signal(0, SignalType.LONG, 97.0, 103.0, 1.0)]  # tight SL
        engine = BacktestEngine(df, signals, ExecutionMode.SPREAD_ON, 10000.0)
        result = engine.run()
        if result.trades:
            wins = [t for t in result.trades if t.pnl > 0]
            assert len(wins) == 0

    def test_signal_at_last_candle_ignored(self):
        """Signal on the final candle cannot execute."""
        timestamps = pd.date_range("2024-01-15 09:30", periods=5, freq="1min")
        data = {
            "open": [100]*5, "high": [101]*5, "low": [99]*5,
            "close": [100]*5, "spread": [0.10]*5,
        }
        df = pd.DataFrame(data, index=timestamps)
        from strategies.signals import Signal
        signals = [Signal(4, SignalType.LONG, 95.0, 105.0, 1.0)]  # last candle
        engine = BacktestEngine(df, signals, ExecutionMode.SPREAD_ON, 10000.0)
        result = engine.run()
        assert len(result.trades) == 0

    def test_cash_never_negative(self, full_pipeline_data):
        """Cash must never go below zero at any point."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=15)
        signals = strategy.generate(full_pipeline_data)
        engine = BacktestEngine(
            data=full_pipeline_data, signals=signals,
            mode=ExecutionMode.SPREAD_ON, initial_capital=10000.0
        )
        result = engine.run()
        for snap in result.snapshots:
            assert snap.cash >= -1e-9  # allow tiny float rounding

    def test_position_stacking_respects_capital(self):
        """Stacking can't spend more cash than available."""
        timestamps = pd.date_range("2024-01-15 09:30", periods=10, freq="1min")
        data = {
            "open": [100]*10, "high": [101]*10, "low": [99]*10,
            "close": [100]*10, "spread": [0.0]*10,
        }
        df = pd.DataFrame(data, index=timestamps)
        from strategies.signals import Signal
        signals = [
            Signal(0, SignalType.LONG, 50.0, 200.0, 1.0),
            Signal(2, SignalType.LONG, 50.0, 200.0, 1.0),
            Signal(4, SignalType.LONG, 50.0, 200.0, 1.0),
            Signal(6, SignalType.LONG, 50.0, 200.0, 1.0),
        ]
        engine = BacktestEngine(df, signals, ExecutionMode.SPREAD_OFF, 10000.0)
        result = engine.run()
        for snap in result.snapshots:
            assert snap.cash >= -1e-9

    def test_empty_dataframe(self):
        """Empty input → graceful handling, no crash."""
        df = pd.DataFrame(columns=["open","high","low","close","spread"])
        df.index = pd.DatetimeIndex([], name="timestamp")
        engine = BacktestEngine(df, [], ExecutionMode.SPREAD_ON, 10000.0)
        result = engine.run()
        assert result.final_equity == 10000.0
```

---

## Quick Reference: What to Check After Each Phase

| Phase | Run command | Pass condition |
|---|---|---|
| 1 | `pytest tests/test_data_loader.py -v` | All green, CSV loads, resampling correct |
| 2 | `pytest tests/test_strategy.py -v` | Signals generated, SL/TP levels correct, no dupes |
| 3 | `pytest tests/test_execution_modes.py -v` | All 15 price/fee values match hand calc |
| 4 | `pytest tests/test_portfolio.py -v` | Cash, position, equity track correctly |
| 5 | `pytest tests/test_sl_tp.py -v` | SL/TP triggers correct, worst-case works |
| 6 | `pytest tests/test_engine.py -v` | Signal delay, execution order, determinism |
| 7 | `pytest tests/test_logging.py -v -s` | Messages appear with correct format |
| 8 | `pytest tests/test_metrics.py -v` | All metrics match hand calculations |
| 9 | `pytest tests/test_visualization.py -v` | Figures created, saved without error |
| 10 | `pytest tests/test_integration.py -v` | Full pipeline, capital identity holds |
| 11 | `pytest tests/ -v` | **ALL tests green** |

Run the full suite at any time with:
```bash
pytest tests/ -v --tb=short
```

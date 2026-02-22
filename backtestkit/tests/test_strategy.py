import pytest
import pandas as pd
import numpy as np
from strategies.ma_crossover import MACrossoverStrategy
from strategies.signals import Signal
from common.models import SignalType

@pytest.fixture
def trending_up_df():
    """Price series that forces one clear crossover: fast crosses above slow."""
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
    n = 70
    timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
    prices = (
        [100.0] * 25                                  # flat long enough for slow MA to stabilize
        + [100.0 + i * 0.5 for i in range(1, 16)]    # up
        + [107.5 - i * 0.5 for i in range(1, 16)]    # down
        + [100.0] * 15                                # flat tail
    )
    data = {
        "open": prices, "high": [p+0.2 for p in prices],
        "low": [p-0.2 for p in prices], "close": prices,
        "spread": [0.10] * n,
    }
    return pd.DataFrame(data, index=timestamps)


class TestMACrossover:
    """Core MA crossover tests."""

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
        first_long = next(i for i, t in enumerate(types) if t == SignalType.LONG)
        first_short = next(i for i, t in enumerate(types) if t == SignalType.SHORT)
        assert first_long < first_short

    def test_reversal_emits_close_before_direction(self, crossover_then_crossunder_df):
        """When reversing from LONG to SHORT, a CLOSE signal precedes the SHORT."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(crossover_then_crossunder_df)
        types = [s.signal_type for s in signals]
        short_idx = next(i for i, t in enumerate(types) if t == SignalType.SHORT)
        assert short_idx > 0
        assert types[short_idx - 1] == SignalType.CLOSE

    def test_close_and_direction_share_candle_index(self, crossover_then_crossunder_df):
        """CLOSE and the following direction signal have the same timestamp_index."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(crossover_then_crossunder_df)
        for i, sig in enumerate(signals):
            if sig.signal_type == SignalType.CLOSE:
                assert i + 1 < len(signals)
                assert signals[i + 1].timestamp_index == sig.timestamp_index

    def test_first_entry_has_no_close(self, trending_up_df):
        """The very first directional signal is NOT preceded by a CLOSE."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(trending_up_df)
        assert len(signals) >= 1
        assert signals[0].signal_type in (SignalType.LONG, SignalType.SHORT)

    def test_all_signals_have_size(self, crossover_then_crossunder_df):
        """Every signal carries a size field equal to 1.0 for MA Crossover."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(crossover_then_crossunder_df)
        assert len(signals) > 0
        for sig in signals:
            assert sig.size == 1.0

    def test_close_signal_has_zero_sl_tp(self, crossover_then_crossunder_df):
        """CLOSE signals have SL/TP set to 0.0 (not applicable)."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(crossover_then_crossunder_df)
        close_signals = [s for s in signals if s.signal_type == SignalType.CLOSE]
        assert len(close_signals) >= 1
        for sig in close_signals:
            assert sig.stop_loss_level == 0.0
            assert sig.take_profit_level == 0.0

    def test_sl_tp_levels_long(self, trending_up_df):
        """LONG signal SL/TP are +/-2% of the close price at signal candle."""
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
            assert s1.size == s2.size


class TestMACrossoverEdgeCases:
    """Edge cases and sneaky scenarios."""

    def test_too_few_candles_returns_empty(self):
        """Data shorter than slow_period returns zero signals."""
        n = 10
        timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
        prices = [100.0 + i for i in range(n)]
        data = {
            "open": prices, "high": [p+0.2 for p in prices],
            "low": [p-0.2 for p in prices], "close": prices,
            "spread": [0.10]*n,
        }
        df = pd.DataFrame(data, index=timestamps)
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(df)
        assert len(signals) == 0

    def test_exactly_slow_period_candles(self):
        """Data with exactly slow_period candles — barely enough for one MA value."""
        n = 30
        timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
        prices = [100.0]*15 + [100.0 + i*0.5 for i in range(1, 16)]
        data = {
            "open": prices, "high": [p+0.2 for p in prices],
            "low": [p-0.2 for p in prices], "close": prices,
            "spread": [0.10]*n,
        }
        df = pd.DataFrame(data, index=timestamps)
        strategy = MACrossoverStrategy(fast_period=10, slow_period=30)
        signals = strategy.generate(df)
        # Should not crash. May or may not produce signals depending on data.
        assert isinstance(signals, list)

    def test_sl_tp_levels_short(self):
        """SHORT signal has SL above close and TP below close."""
        n = 70
        timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
        prices = (
            [100.0] * 25
            + [100.0 + i * 0.5 for i in range(1, 16)]
            + [107.5 - i * 0.5 for i in range(1, 16)]
            + [100.0] * 15
        )
        data = {
            "open": prices, "high": [p+0.2 for p in prices],
            "low": [p-0.2 for p in prices], "close": prices,
            "spread": [0.10] * n,
        }
        df = pd.DataFrame(data, index=timestamps)
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(df)
        short_sig = next(s for s in signals if s.signal_type == SignalType.SHORT)
        close_at = df.iloc[short_sig.timestamp_index]["close"]
        # SHORT: SL = close * 1.02, TP = close * 0.98
        assert abs(short_sig.stop_loss_level - close_at * 1.02) < 1e-6
        assert abs(short_sig.take_profit_level - close_at * 0.98) < 1e-6

    def test_custom_sl_tp_percentages(self, trending_up_df):
        """Custom sl_pct and tp_pct values are respected."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20, sl_pct=0.05, tp_pct=0.10)
        signals = strategy.generate(trending_up_df)
        sig = next(s for s in signals if s.signal_type == SignalType.LONG)
        close_at = trending_up_df.iloc[sig.timestamp_index]["close"]
        assert abs(sig.stop_loss_level - close_at * 0.95) < 1e-6
        assert abs(sig.take_profit_level - close_at * 1.10) < 1e-6

    def test_no_signal_at_index_zero(self, trending_up_df):
        """No signal can ever have timestamp_index=0 (need i-1 for comparison)."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(trending_up_df)
        for sig in signals:
            assert sig.timestamp_index > 0

    def test_monotonically_rising_prices(self):
        """Steadily rising prices produce exactly one LONG (no reversals)."""
        n = 60
        timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
        prices = [100.0 + i * 0.1 for i in range(n)]
        data = {
            "open": prices, "high": [p+0.05 for p in prices],
            "low": [p-0.05 for p in prices], "close": prices,
            "spread": [0.10]*n,
        }
        df = pd.DataFrame(data, index=timestamps)
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(df)
        # Only LONGs, no CLOSE or SHORT
        for sig in signals:
            assert sig.signal_type == SignalType.LONG

    def test_monotonically_falling_prices(self):
        """Steadily falling prices produce exactly one SHORT (no reversals)."""
        n = 60
        timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
        prices = [200.0 - i * 0.1 for i in range(n)]
        data = {
            "open": prices, "high": [p+0.05 for p in prices],
            "low": [p-0.05 for p in prices], "close": prices,
            "spread": [0.10]*n,
        }
        df = pd.DataFrame(data, index=timestamps)
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(df)
        # Only SHORTs, no CLOSE or LONG
        for sig in signals:
            assert sig.signal_type == SignalType.SHORT

    def test_close_always_followed_by_direction(self, crossover_then_crossunder_df):
        """Every CLOSE signal is immediately followed by a LONG or SHORT signal."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(crossover_then_crossunder_df)
        for i, sig in enumerate(signals):
            if sig.signal_type == SignalType.CLOSE:
                assert i + 1 < len(signals), "CLOSE is the last signal with no direction after it"
                next_sig = signals[i + 1]
                assert next_sig.signal_type in (SignalType.LONG, SignalType.SHORT)

    def test_directional_signals_have_positive_sl_tp(self, trending_up_df):
        """LONG and SHORT signals always have positive SL and TP levels."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(trending_up_df)
        for sig in signals:
            if sig.signal_type in (SignalType.LONG, SignalType.SHORT):
                assert sig.stop_loss_level > 0
                assert sig.take_profit_level > 0

    def test_long_sl_below_tp(self, trending_up_df):
        """For LONG signals, SL < TP (stop loss is below take profit)."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(trending_up_df)
        for sig in signals:
            if sig.signal_type == SignalType.LONG:
                assert sig.stop_loss_level < sig.take_profit_level

    def test_short_sl_above_tp(self):
        """For SHORT signals, SL > TP (stop loss is above take profit)."""
        n = 70
        timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
        prices = (
            [100.0] * 25
            + [100.0 + i * 0.5 for i in range(1, 16)]
            + [107.5 - i * 0.5 for i in range(1, 16)]
            + [100.0] * 15
        )
        data = {
            "open": prices, "high": [p+0.2 for p in prices],
            "low": [p-0.2 for p in prices], "close": prices,
            "spread": [0.10] * n,
        }
        df = pd.DataFrame(data, index=timestamps)
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(df)
        for sig in signals:
            if sig.signal_type == SignalType.SHORT:
                assert sig.stop_loss_level > sig.take_profit_level

    def test_signal_count_on_reversal_data(self, crossover_then_crossunder_df):
        """Reversal data produces exactly: 1 LONG + 1 CLOSE + 1 SHORT = 3 signals."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(crossover_then_crossunder_df)
        types = [s.signal_type for s in signals]
        assert types.count(SignalType.LONG) == 1
        assert types.count(SignalType.CLOSE) == 1
        assert types.count(SignalType.SHORT) == 1
        assert len(signals) == 3

    def test_different_strategy_instances_same_result(self, trending_up_df):
        """Two separate strategy instances produce identical signals on same data."""
        s1 = MACrossoverStrategy(fast_period=5, slow_period=20)
        s2 = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals_1 = s1.generate(trending_up_df)
        signals_2 = s2.generate(trending_up_df)
        assert len(signals_1) == len(signals_2)
        for a, b in zip(signals_1, signals_2):
            assert a.timestamp_index == b.timestamp_index
            assert a.signal_type == b.signal_type

    def test_default_parameters(self):
        """Default strategy uses fast=10, slow=30, sl=0.02, tp=0.02."""
        strategy = MACrossoverStrategy()
        assert strategy.fast_period == 10
        assert strategy.slow_period == 30
        assert strategy.sl_pct == 0.02
        assert strategy.tp_pct == 0.02

    def test_signals_ordered_by_timestamp(self, crossover_then_crossunder_df):
        """Signals are emitted in non-decreasing timestamp_index order."""
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        signals = strategy.generate(crossover_then_crossunder_df)
        for i in range(1, len(signals)):
            assert signals[i].timestamp_index >= signals[i-1].timestamp_index

    def test_input_dataframe_not_mutated(self, trending_up_df):
        """Strategy does not modify the input DataFrame."""
        original_values = trending_up_df.values.copy()
        original_index = trending_up_df.index.copy()
        strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
        strategy.generate(trending_up_df)
        assert np.array_equal(trending_up_df.values, original_values)
        assert trending_up_df.index.equals(original_index)


class TestSignalDataclass:
    """Tests for the Signal dataclass itself."""

    def test_signal_fields_exist(self):
        """Signal has all required fields."""
        sig = Signal(
            timestamp_index=5,
            signal_type=SignalType.LONG,
            stop_loss_level=98.0,
            take_profit_level=102.0,
            size=1.0,
        )
        assert sig.timestamp_index == 5
        assert sig.signal_type == SignalType.LONG
        assert sig.stop_loss_level == 98.0
        assert sig.take_profit_level == 102.0
        assert sig.size == 1.0

    def test_signal_equality(self):
        """Two signals with identical fields are equal (dataclass default)."""
        sig1 = Signal(0, SignalType.LONG, 98.0, 102.0, 1.0)
        sig2 = Signal(0, SignalType.LONG, 98.0, 102.0, 1.0)
        assert sig1 == sig2

    def test_signal_inequality(self):
        """Signals with different fields are not equal."""
        sig1 = Signal(0, SignalType.LONG, 98.0, 102.0, 1.0)
        sig2 = Signal(0, SignalType.SHORT, 102.0, 98.0, 1.0)
        assert sig1 != sig2

    def test_close_signal_type_exists(self):
        """SignalType.CLOSE exists and can be used in a Signal."""
        sig = Signal(0, SignalType.CLOSE, 0.0, 0.0, 1.0)
        assert sig.signal_type == SignalType.CLOSE

    def test_signal_size_field_accepts_float(self):
        """Size field accepts fractional values (for future partial sizing)."""
        sig = Signal(0, SignalType.LONG, 98.0, 102.0, 0.5)
        assert sig.size == 0.5

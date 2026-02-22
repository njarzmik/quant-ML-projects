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
        signals = [Signal(timestamp_index=0, signal_type=SignalType.LONG,
                          stop_loss_level=98.0, take_profit_level=102.0, size=1.0)]
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=signals,
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        # The first trade should have entry price = candle 1 open = 101.0
        assert result.trades[0].entry_price == pytest.approx(101.0)

    def test_signal_on_last_candle_not_executed(self, simple_5_candle_df):
        """Signal on the last candle has no i+1 to execute at -> no trade."""
        signals = [Signal(timestamp_index=4, signal_type=SignalType.LONG,
                          stop_loss_level=98.0, take_profit_level=102.0, size=1.0)]
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=signals,
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        assert len(result.trades) == 0


class TestExecutionOrder:
    def test_sl_checked_before_signal(self, simple_5_candle_df):
        """SL/TP is evaluated before a new signal on the same candle."""
        # Signal LONG at candle 0 -> executes candle 1
        # SL at 101.5 means: for LONG, SL hit if low <= 101.5
        # Candle 2: low=101.0 <= 101.5 -> SL fires
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
        """Zero signals -> zero trades, equity unchanged."""
        engine = BacktestEngine(
            data=simple_5_candle_df, signals=[],
            mode=ExecutionMode.SPREAD_OFF, initial_capital=10000.0
        )
        result = engine.run()
        assert len(result.trades) == 0
        assert result.final_equity == pytest.approx(10000.0)


class TestCloseAndReverse:
    def test_long_then_short_reversal(self, simple_5_candle_df):
        """LONG then SHORT signal -> close long, open short."""
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
        # After CLOSE executes at candle 3, position should be 0
        # Snapshot at candle 3 (index 3) and candle 4 (index 4) should have 0 position
        assert result.snapshots[3].position_size == 0.0
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

import pytest
from backtester.sl_tp import check_sl_tp, PositionUnit
from common.models import ExecutionMode


def make_candle(open_, high, low, close, spread=0.0):
    """Helper to create a candle dict."""
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

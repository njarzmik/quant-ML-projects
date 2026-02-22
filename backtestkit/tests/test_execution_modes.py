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

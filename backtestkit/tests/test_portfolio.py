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

    def test_90_percent_allocation(self, portfolio):
        """size=0.9 allocates 90% of cash."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        # allocation = 10000 * 0.9 = 9000, units = 9000 / 100 = 90
        assert portfolio.position_size == pytest.approx(90.0)
        assert portfolio.cash == pytest.approx(1000.0)

    def test_cannot_exceed_cash(self, portfolio):
        """Cannot open position larger than available cash allows."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=1.0)
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=1.0)
        # After first open: all cash used. Second open has 0 cash available.
        assert portfolio.cash == pytest.approx(0.0)


class TestOppositeDirectionRejection:
    def test_long_then_short_raises(self, portfolio):
        """Opening SHORT while LONG raises ValueError."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.5)
        with pytest.raises(ValueError, match="CLOSE signal before reversing"):
            portfolio.open_position(entry_price=100.0, spread=0.0, direction="SHORT", size=0.5)

    def test_short_then_long_raises(self, portfolio):
        """Opening LONG while SHORT raises ValueError."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="SHORT", size=0.5)
        with pytest.raises(ValueError, match="CLOSE signal before reversing"):
            portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.5)


class TestPositionStacking:
    def test_stacking_increases_size(self, portfolio):
        """Two LONG signals produce additive position."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.5)
        size_1 = portfolio.position_size
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.5)
        assert portfolio.position_size > size_1

    def test_weighted_average_entry(self, portfolio):
        """Stacked position has correct weighted average entry."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        # units_1 = 9000/100 = 90, avg = 100, cash = 1000
        portfolio.open_position(entry_price=200.0, spread=0.0, direction="LONG", size=1.0)
        # units_2 = 1000/200 = 5, avg = (100*90 + 200*5) / 95
        expected_avg = (100.0 * 90.0 + 200.0 * 5.0) / 95.0
        assert portfolio.avg_entry_price == pytest.approx(expected_avg, rel=1e-4)


class TestPositionClosing:
    def test_close_credits_cash(self, portfolio):
        """Closing position returns value to cash."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        # units = 9000/100 = 90, cash = 1000
        portfolio.close_position(exit_price=110.0, spread=0.0)
        # PnL = (110 - 100) * 90 = 900
        # cash = 1000 + 100*90 + 900 = 1000 + 9900 = 10900
        assert portfolio.cash == 10900.0
        assert portfolio.position_size == 0.0

    def test_losing_trade_reduces_cash(self, portfolio):
        """Losing trade results in less cash than started."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        # units = 90, cash = 1000
        portfolio.close_position(exit_price=90.0, spread=0.0)
        # PnL = (90 - 100) * 90 = -900
        # cash = 1000 + 100*90 - 900 = 1000 + 8100 = 9100
        assert portfolio.cash == 9100.0

    def test_realized_pnl_tracked(self, portfolio):
        """realized_pnl accumulates across trades."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        portfolio.close_position(exit_price=110.0, spread=0.0)
        assert portfolio.realized_pnl == pytest.approx(900.0)

    def test_close_resets_position(self, portfolio):
        """After close, position_size is 0 and avg_entry is 0."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        portfolio.close_position(exit_price=110.0, spread=0.0)
        assert portfolio.position_size == 0.0
        assert portfolio.avg_entry_price == 0.0


class TestCloseAndReverse:
    def test_long_to_short(self, portfolio):
        """LONG position followed by SHORT signal -> close then open short."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        portfolio.close_position(exit_price=105.0, spread=0.0)
        portfolio.open_position(entry_price=105.0, spread=0.0, direction="SHORT", size=1.0)
        assert portfolio.position_size < 0  # negative = short


class TestUnrealizedPnL:
    def test_long_unrealized_profit(self, portfolio):
        """LONG position with price increase shows positive unrealized PnL."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        portfolio.update_unrealized(current_mid=110.0, spread=0.0)
        assert portfolio.unrealized_pnl > 0

    def test_long_unrealized_uses_bid(self, portfolio):
        """Unrealized PnL for LONG uses bid (mid - spread/2)."""
        portfolio.open_position(entry_price=100.0, spread=0.50, direction="LONG", size=0.9)
        # entry at ask = 100.25, units = 9000/100.25 ~ 89.776
        portfolio.update_unrealized(current_mid=100.0, spread=0.50)
        # bid = 99.75, unrealized = (99.75 - 100.25) * units = negative
        assert portfolio.unrealized_pnl < 0

    def test_equity_is_total_account_value(self, portfolio):
        """Equity = cash + position_notional + unrealized_pnl."""
        portfolio.open_position(entry_price=100.0, spread=0.0, direction="LONG", size=0.9)
        # units=90, avg_entry=100, cash=1000
        portfolio.update_unrealized(current_mid=110.0, spread=0.0)
        # unrealized = (110-100)*90 = 900, notional = 90*100 = 9000
        # equity = 1000 + 9000 + 900 = 10900
        expected = portfolio.cash + portfolio.position_notional + portfolio.unrealized_pnl
        assert portfolio.equity == pytest.approx(expected)
        assert portfolio.equity == pytest.approx(10900.0)

    def test_equity_after_open_reflects_spread_cost(self, portfolio):
        """Opening a position with spread immediately reduces equity by the spread cost."""
        portfolio.open_position(entry_price=100.0, spread=0.5, direction="LONG", size=1.0)
        portfolio.update_unrealized(current_mid=100.0, spread=0.5)
        # Bought at ask=100.25, mark-to-market at bid=99.75
        # equity should be ~10000 - spread_cost, NOT negative
        assert portfolio.equity < 10000.0
        assert portfolio.equity > 9900.0  # lost ~50 on spread, not 10000

    def test_equity_unchanged_when_flat(self, portfolio):
        """When no position is open, equity equals cash."""
        assert portfolio.equity == 10000.0
        assert portfolio.equity == portfolio.cash

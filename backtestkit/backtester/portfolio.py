# backtester/portfolio.py — Capital accounting (Phase 4)

from common.models import ExecutionMode
from backtester.execution_modes import resolve_entry_price, resolve_exit_price, calculate_fee


class Portfolio:
    """Tracks all financial state throughout the simulation.

    State variables:
        cash: Free capital not in positions
        position_size: Units held (+N = long, -N = short, 0 = flat)
        avg_entry_price: Weighted average entry price across stacked entries
        realized_pnl: Cumulative closed trade profit/loss
        unrealized_pnl: Current open position profit/loss
        equity: cash + position_notional + unrealized_pnl
    """

    def __init__(self, initial_capital: float, mode: ExecutionMode):
        self.initial_capital = initial_capital
        self.mode = mode
        self.cash = initial_capital
        self.position_size = 0.0
        self.avg_entry_price = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0

    @property
    def position_notional(self) -> float:
        """Capital locked in the open position (at entry cost)."""
        return abs(self.position_size) * self.avg_entry_price

    @property
    def equity(self) -> float:
        """Equity = cash + position_notional + unrealized_pnl.

        - cash: free capital not in positions
        - position_notional: capital deployed in the position (units * avg_entry)
        - unrealized_pnl: how much the position gained/lost since entry
        """
        return self.cash + self.position_notional + self.unrealized_pnl

    def open_position(self, entry_price: float, spread: float, direction: str, size: float = 1.0):
        """Open or stack a position.

        Args:
            entry_price: Mid-price at execution candle open.
            spread: Spread at execution candle.
            direction: "LONG" or "SHORT".
            size: Fraction of available cash to allocate (0.0 to 1.0).
        """
        allocation = self.cash * size
        if allocation <= 0:
            return

        actual_entry = resolve_entry_price(entry_price, spread, direction, self.mode)
        fee = calculate_fee(allocation, self.mode)

        # Units bought with the allocation minus fee
        effective_allocation = allocation - fee
        if effective_allocation <= 0:
            return

        new_units = effective_allocation / actual_entry

        if direction == "SHORT":
            new_units = -new_units

        # Reject opposite-direction stacking — strategy must emit CLOSE first
        if self.position_size != 0.0:
            is_long = self.position_size > 0
            if (is_long and direction == "SHORT") or (not is_long and direction == "LONG"):
                raise ValueError(
                    f"Cannot open {direction} while holding {'LONG' if is_long else 'SHORT'} position. "
                    f"Strategy must emit a CLOSE signal before reversing direction."
                )

        if self.position_size == 0.0:
            # Fresh position
            self.avg_entry_price = actual_entry
            self.position_size = new_units
        else:
            # Same-direction stacking: weighted average entry price
            old_size = abs(self.position_size)
            new_size = abs(new_units)
            self.avg_entry_price = (
                (self.avg_entry_price * old_size + actual_entry * new_size)
                / (old_size + new_size)
            )
            self.position_size += new_units

        self.cash -= allocation

    def close_position(self, exit_price: float, spread: float, size: float = 1.0):
        """Close all or part of the current position.

        Args:
            exit_price: Mid-price at execution candle open.
            spread: Spread at execution candle.
            size: Fraction of position to close (1.0 = full close).
        """
        if self.position_size == 0.0:
            return

        direction = "LONG" if self.position_size > 0 else "SHORT"
        actual_exit = resolve_exit_price(exit_price, spread, direction, self.mode)

        units_to_close = abs(self.position_size) * size

        # Calculate realized PnL
        if direction == "LONG":
            pnl = (actual_exit - self.avg_entry_price) * units_to_close
        else:  # SHORT
            pnl = (self.avg_entry_price - actual_exit) * units_to_close

        # Calculate position value for fee
        position_value = actual_exit * units_to_close
        fee = calculate_fee(position_value, self.mode)

        # Credit cash: return the position value plus/minus pnl, minus fee
        cash_return = self.avg_entry_price * units_to_close + pnl - fee
        self.cash += cash_return
        self.realized_pnl += pnl - fee

        # Update position
        if size >= 1.0:
            self.position_size = 0.0
            self.avg_entry_price = 0.0
        else:
            if direction == "LONG":
                self.position_size -= units_to_close
            else:
                self.position_size += units_to_close

    def update_unrealized(self, current_mid: float, spread: float):
        """Update unrealized PnL based on current market prices.

        LONG: uses bid (mid - spread/2) for mark-to-market.
        SHORT: uses ask (mid + spread/2) for mark-to-market.
        """
        if self.position_size == 0.0:
            self.unrealized_pnl = 0.0
            return

        if self.position_size > 0:  # LONG
            current_bid = current_mid - spread / 2.0
            self.unrealized_pnl = (current_bid - self.avg_entry_price) * self.position_size
        else:  # SHORT
            current_ask = current_mid + spread / 2.0
            self.unrealized_pnl = (self.avg_entry_price - current_ask) * abs(self.position_size)

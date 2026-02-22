# backtester/engine.py — Main backtest loop (Phase 6)

from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd

from backtester.portfolio import Portfolio
from backtester.sl_tp import PositionUnit, check_sl_tp
from backtester.execution_modes import resolve_entry_price, calculate_fee
from common.models import ExecutionMode, SignalType
from strategies.signals import Signal


@dataclass
class Trade:
    """A completed (or still-open) trade record."""
    direction: str
    entry_price: float
    entry_index: int
    size: float
    sl: float
    tp: float
    exit_price: Optional[float] = None
    exit_index: Optional[int] = None
    exit_reason: Optional[str] = None  # "SL", "TP", "CLOSE", or None if still open
    pnl: Optional[float] = None


@dataclass
class Snapshot:
    """Per-candle state snapshot."""
    index: int
    cash: float
    position_size: float
    unrealized_pnl: float
    equity: float


@dataclass
class BacktestResult:
    """Result returned by the engine after running the simulation."""
    trades: List[Trade] = field(default_factory=list)
    snapshots: List[Snapshot] = field(default_factory=list)
    final_equity: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0


class BacktestEngine:
    """Deterministic backtesting engine.

    Iterates over every 1-min candle and executes the simulation with strict ordering:
        1. Update unrealized PnL
        2. Check and execute SL/TP for each position unit
        3. Execute pending signals from previous candle (CLOSE first, then entries)
        4. Collect new signals at this candle index -> store as pending
        5. Record state snapshot

    Critical invariant: signals at candle i are stored, then executed at candle i+1 open.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        signals: List[Signal],
        mode: ExecutionMode,
        initial_capital: float,
        verbosity: str = "silent",
    ):
        self.data = data
        self.signals = signals
        self.mode = mode
        self.initial_capital = initial_capital
        self.verbosity = verbosity

        self.portfolio = Portfolio(initial_capital=initial_capital, mode=mode)
        self.position_units: List[PositionUnit] = []
        self.trades: List[Trade] = []
        self.snapshots: List[Snapshot] = []

        # Build signal lookup: index -> list of signals at that index
        self._signal_map: dict[int, List[Signal]] = {}
        for sig in signals:
            self._signal_map.setdefault(sig.timestamp_index, []).append(sig)

    def run(self) -> BacktestResult:
        """Run the backtest simulation and return results."""
        if len(self.data) == 0:
            return BacktestResult(
                trades=[],
                snapshots=[],
                final_equity=self.initial_capital,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
            )

        pending_signals: List[Signal] = []

        for i in range(len(self.data)):
            candle = self.data.iloc[i]
            candle_dict = {
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "spread": candle["spread"],
            }

            # Step 1: Update unrealized PnL using current candle's close
            self.portfolio.update_unrealized(candle["close"], candle["spread"])

            # Step 2: Check and execute SL/TP for each position unit
            self._check_and_execute_sl_tp(candle_dict, i)

            # Step 3: Execute pending signals (from previous candle)
            # Sort: CLOSE signals first, then directional entries
            close_signals = [s for s in pending_signals if s.signal_type == SignalType.CLOSE]
            entry_signals = [s for s in pending_signals if s.signal_type != SignalType.CLOSE]

            for sig in close_signals:
                self._execute_close_signal(sig, candle_dict, i)

            for sig in entry_signals:
                self._execute_entry_signal(sig, candle_dict, i)

            pending_signals = []

            # Step 4: Collect all signals at this candle index
            if i in self._signal_map:
                pending_signals = list(self._signal_map[i])

            # Step 5: Record snapshot
            self.snapshots.append(Snapshot(
                index=i,
                cash=self.portfolio.cash,
                position_size=self.portfolio.position_size,
                unrealized_pnl=self.portfolio.unrealized_pnl,
                equity=self.portfolio.equity,
            ))

        return BacktestResult(
            trades=self.trades,
            snapshots=self.snapshots,
            final_equity=self.portfolio.equity,
            realized_pnl=self.portfolio.realized_pnl,
            unrealized_pnl=self.portfolio.unrealized_pnl,
        )

    def _check_and_execute_sl_tp(self, candle: dict, candle_index: int):
        """Check SL/TP for each position unit and execute if triggered."""
        units_to_remove = []

        for unit in self.position_units:
            result = check_sl_tp(unit, candle, self.mode)
            if result.triggered is not None:
                # Close this unit at the SL/TP exit price
                self._close_unit_at_price(unit, result.exit_price, candle["spread"],
                                          candle_index, result.triggered)
                units_to_remove.append(unit)

        for unit in units_to_remove:
            self.position_units.remove(unit)

    def _close_unit_at_price(self, unit: PositionUnit, exit_price: float,
                              spread: float, candle_index: int, reason: str):
        """Close a specific position unit at a given exit price (SL/TP)."""
        # Calculate realized PnL for this unit
        if unit.direction == "LONG":
            pnl = (exit_price - unit.entry_price) * unit.size
        else:  # SHORT
            pnl = (unit.entry_price - exit_price) * unit.size

        # Calculate fee
        position_value = exit_price * unit.size
        fee = calculate_fee(position_value, self.mode)
        pnl -= fee

        # Return cash: notional + pnl (notional = entry_price * units)
        cash_return = unit.entry_price * unit.size + pnl
        self.portfolio.cash += cash_return
        self.portfolio.realized_pnl += pnl

        # Update portfolio position size
        if unit.direction == "LONG":
            self.portfolio.position_size -= unit.size
        else:
            self.portfolio.position_size += unit.size

        # If position fully closed, reset avg_entry
        if abs(self.portfolio.position_size) < 1e-12:
            self.portfolio.position_size = 0.0
            self.portfolio.avg_entry_price = 0.0

        # Record the trade
        # Find the matching open trade record, or create one
        open_trade = None
        for t in self.trades:
            if (t.exit_price is None and t.direction == unit.direction
                    and t.entry_price == unit.entry_price and t.size == unit.size):
                open_trade = t
                break

        if open_trade:
            open_trade.exit_price = exit_price
            open_trade.exit_index = candle_index
            open_trade.exit_reason = reason
            open_trade.pnl = pnl
        else:
            # Create a complete trade record
            self.trades.append(Trade(
                direction=unit.direction,
                entry_price=unit.entry_price,
                entry_index=candle_index,
                size=unit.size,
                sl=unit.sl,
                tp=unit.tp,
                exit_price=exit_price,
                exit_index=candle_index,
                exit_reason=reason,
                pnl=pnl,
            ))

        self._log_sl_tp(unit, exit_price, pnl, reason, candle_index)

    def _execute_close_signal(self, sig: Signal, candle: dict, candle_index: int):
        """Execute a CLOSE signal."""
        if self.portfolio.position_size == 0.0:
            return

        direction = "LONG" if self.portfolio.position_size > 0 else "SHORT"

        # Close through portfolio (handles spread, fee, pnl)
        exit_mid = candle["open"]
        spread = candle["spread"]

        # Calculate the exit price for recording
        from backtester.execution_modes import resolve_exit_price
        actual_exit = resolve_exit_price(exit_mid, spread, direction, self.mode)

        # Calculate PnL before closing
        units_to_close = abs(self.portfolio.position_size) * sig.size
        if direction == "LONG":
            pnl = (actual_exit - self.portfolio.avg_entry_price) * units_to_close
        else:
            pnl = (self.portfolio.avg_entry_price - actual_exit) * units_to_close

        position_value = actual_exit * units_to_close
        fee = calculate_fee(position_value, self.mode)
        pnl -= fee

        # Use portfolio.close_position for accounting
        self.portfolio.close_position(exit_price=exit_mid, spread=spread, size=sig.size)

        # Close out position units proportionally
        if sig.size >= 1.0:
            # Full close: record trades for all units, clear units
            for unit in self.position_units:
                # Find matching open trade
                for t in self.trades:
                    if (t.exit_price is None and t.direction == unit.direction
                            and t.entry_price == unit.entry_price and t.size == unit.size):
                        unit_pnl = self._calc_unit_pnl(unit, actual_exit)
                        t.exit_price = actual_exit
                        t.exit_index = candle_index
                        t.exit_reason = "CLOSE"
                        t.pnl = unit_pnl
                        break
            self.position_units.clear()
        else:
            # Partial close: reduce each unit proportionally
            new_units = []
            for unit in self.position_units:
                closed_size = unit.size * sig.size
                remaining_size = unit.size - closed_size
                if remaining_size > 1e-12:
                    unit.size = remaining_size
                    new_units.append(unit)
            self.position_units = new_units

        self._log_close(direction, units_to_close, actual_exit, pnl, candle_index)

    def _execute_entry_signal(self, sig: Signal, candle: dict, candle_index: int):
        """Execute a LONG or SHORT entry signal."""
        if self.portfolio.cash <= 0:
            return

        direction = "LONG" if sig.signal_type == SignalType.LONG else "SHORT"
        entry_mid = candle["open"]
        spread = candle["spread"]

        # Calculate actual entry price for PositionUnit
        actual_entry = resolve_entry_price(entry_mid, spread, direction, self.mode)

        # Calculate allocation
        allocation = self.portfolio.cash * sig.size
        fee = calculate_fee(allocation, self.mode)
        effective_allocation = allocation - fee
        if effective_allocation <= 0:
            return

        new_units = effective_allocation / actual_entry

        # Open through portfolio (handles stacking, weighted average, cash deduction)
        self.portfolio.open_position(
            entry_price=entry_mid, spread=spread,
            direction=direction, size=sig.size,
        )

        # Create a PositionUnit with the signal's SL/TP levels
        unit = PositionUnit(
            direction=direction,
            entry_price=actual_entry,
            size=new_units,
            sl=sig.stop_loss_level,
            tp=sig.take_profit_level,
        )
        self.position_units.append(unit)

        # Record trade (open, no exit yet)
        self.trades.append(Trade(
            direction=direction,
            entry_price=actual_entry,
            entry_index=candle_index,
            size=new_units,
            sl=sig.stop_loss_level,
            tp=sig.take_profit_level,
        ))

        self._log_entry(direction, new_units, actual_entry, entry_mid, spread, candle_index)

    def _calc_unit_pnl(self, unit: PositionUnit, exit_price: float) -> float:
        """Calculate PnL for a single position unit."""
        if unit.direction == "LONG":
            pnl = (exit_price - unit.entry_price) * unit.size
        else:
            pnl = (unit.entry_price - exit_price) * unit.size
        position_value = exit_price * unit.size
        fee = calculate_fee(position_value, self.mode)
        return pnl - fee

    # --- Logging ---

    def _log_entry(self, direction: str, units: float, entry_price: float,
                   mid: float, spread: float, candle_index: int):
        if self.verbosity == "silent":
            return
        timestamp = self.data.index[candle_index]
        action = "BUY" if direction == "LONG" else "SELL"
        print(f"[{timestamp}] {action} {units:.2f} units at {entry_price:.2f}")

    def _log_close(self, direction: str, units: float, exit_price: float,
                   pnl: float, candle_index: int):
        if self.verbosity == "silent":
            return
        timestamp = self.data.index[candle_index]
        print(f"[{timestamp}] CLOSE at {exit_price:.2f} — closed {units:.2f} units, PnL: {pnl:+.2f}")

    def _log_sl_tp(self, unit: PositionUnit, exit_price: float,
                   pnl: float, reason: str, candle_index: int):
        if self.verbosity == "silent":
            return
        timestamp = self.data.index[candle_index]
        label = "STOP LOSS" if reason == "SL" else "TAKE PROFIT"
        print(f"[{timestamp}] {label} hit at {exit_price:.2f} — closed {unit.size:.2f} units, PnL: {pnl:+.2f}")

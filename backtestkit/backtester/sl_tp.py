# backtester/sl_tp.py — Stop loss / take profit engine (Phase 5)

from dataclasses import dataclass
from typing import Optional

from common.models import ExecutionMode


@dataclass
class PositionUnit:
    """A single position entry with its own SL/TP levels.

    When stacking, each entry event creates a separate PositionUnit.
    Each unit has independent SL/TP that can trigger independently.

    Attributes:
        direction: "LONG" or "SHORT"
        entry_price: Actual entry price (after spread adjustment)
        size: Number of units in this position layer
        sl: Stop loss price level
        tp: Take profit price level
    """
    direction: str
    entry_price: float
    size: float
    sl: float
    tp: float


@dataclass
class SLTPResult:
    """Result of checking SL/TP conditions for a position unit.

    Attributes:
        triggered: None if neither triggered, "SL" or "TP" if one fired
        exit_price: The execution price (with spread applied), or None if not triggered
    """
    triggered: Optional[str]
    exit_price: Optional[float]


def check_sl_tp(unit: PositionUnit, candle: dict, mode: ExecutionMode) -> SLTPResult:
    """Evaluate SL/TP conditions for a position unit against a candle.

    Intrabar evaluation:
        LONG:  SL hit if candle low  <= SL level
               TP hit if candle high >= TP level
        SHORT: SL hit if candle high >= SL level
               TP hit if candle low  <= TP level

    Worst-case rule: if BOTH trigger on the same candle, SL executes.

    SL/TP execution prices (with spread):
        LONG  SL/TP hit -> exit at level - spread/2 (sold at bid)
        SHORT SL/TP hit -> exit at level + spread/2 (bought at ask)

    For Mode B (SPREAD_OFF): exit at the level itself (no spread adjustment).

    Args:
        unit: The position unit to check.
        candle: Dict with keys: open, high, low, close, spread.
        mode: Execution mode for spread handling.

    Returns:
        SLTPResult with triggered type and exit price.
    """
    low = candle["low"]
    high = candle["high"]
    spread = candle["spread"]

    sl_hit = False
    tp_hit = False

    if unit.direction == "LONG":
        sl_hit = low <= unit.sl
        tp_hit = high >= unit.tp
    else:  # SHORT
        sl_hit = high >= unit.sl
        tp_hit = low <= unit.tp

    # Worst-case rule: if both triggered, SL fires
    if sl_hit:
        level = unit.sl
        exit_price = _apply_exit_spread(level, unit.direction, spread, mode)
        return SLTPResult(triggered="SL", exit_price=exit_price)

    if tp_hit:
        level = unit.tp
        exit_price = _apply_exit_spread(level, unit.direction, spread, mode)
        return SLTPResult(triggered="TP", exit_price=exit_price)

    return SLTPResult(triggered=None, exit_price=None)


def _apply_exit_spread(level: float, direction: str, spread: float, mode: ExecutionMode) -> float:
    """Apply spread to the SL/TP exit level.

    LONG exit  -> sold at bid: level - spread/2
    SHORT exit -> bought at ask: level + spread/2
    Mode B (SPREAD_OFF): no spread adjustment, exit at level itself.
    """
    if mode == ExecutionMode.SPREAD_OFF:
        return level

    half_spread = spread / 2.0
    if direction == "LONG":
        return level - half_spread
    else:  # SHORT
        return level + half_spread

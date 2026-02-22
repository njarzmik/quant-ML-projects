# backtester/execution_modes.py — Price resolution per execution mode (Phase 3)

from common.models import ExecutionMode


def resolve_entry_price(
    mid: float, spread: float, direction: str, mode: ExecutionMode
) -> float:
    """Return the entry price given mid-price, spread, direction, and mode.

    Mode A (SPREAD_ON):  LONG -> ask (mid + spread/2), SHORT -> bid (mid - spread/2)
    Mode B (SPREAD_OFF): always mid (no spread adjustment)
    Mode C (STATIC_SPREAD): same as Mode A (spread param is the static value)
    """
    if mode == ExecutionMode.SPREAD_OFF:
        return mid

    half_spread = spread / 2.0
    if direction == "LONG":
        return mid + half_spread
    else:  # SHORT
        return mid - half_spread


def resolve_exit_price(
    mid: float, spread: float, direction: str, mode: ExecutionMode
) -> float:
    """Return the exit price given mid-price, spread, direction, and mode.

    Mode A (SPREAD_ON):  LONG -> bid (mid - spread/2), SHORT -> ask (mid + spread/2)
    Mode B (SPREAD_OFF): always mid (no spread adjustment)
    Mode C (STATIC_SPREAD): same as Mode A (spread param is the static value)
    """
    if mode == ExecutionMode.SPREAD_OFF:
        return mid

    half_spread = spread / 2.0
    if direction == "LONG":
        return mid - half_spread
    else:  # SHORT
        return mid + half_spread


def calculate_fee(position_value: float, mode: ExecutionMode) -> float:
    """Return the transaction fee for a given position value and mode.

    Mode A (SPREAD_ON):     fee = 0
    Mode B (SPREAD_OFF):    fee = 0.1% of position value
    Mode C (STATIC_SPREAD): fee = 0
    """
    if mode == ExecutionMode.SPREAD_OFF:
        return position_value * 0.001
    return 0.0

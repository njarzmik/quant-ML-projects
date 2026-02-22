from dataclasses import dataclass

from common.models import SignalType


@dataclass
class Signal:
    timestamp_index: int
    signal_type: SignalType
    stop_loss_level: float
    take_profit_level: float
    size: float

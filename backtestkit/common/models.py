from enum import Enum


class ExecutionMode(Enum):
    SPREAD_ON = "spread_on"
    SPREAD_OFF = "spread_off"
    STATIC_SPREAD = "static_spread"


class SignalType(Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    CLOSE = "CLOSE"

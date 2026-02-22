from typing import List, Optional

import pandas as pd

from common.models import SignalType
from strategies.base_strategy import BaseStrategy
from strategies.signals import Signal


class MACrossoverStrategy(BaseStrategy):
    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 30,
        sl_pct: float = 0.02,
        tp_pct: float = 0.02,
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.sl_pct = sl_pct
        self.tp_pct = tp_pct

    def generate(self, df: pd.DataFrame) -> List[Signal]:
        """Generate LONG/SHORT signals based on fast/slow MA crossover.

        Crossover (fast crosses above slow) -> LONG
        Crossunder (fast crosses below slow) -> SHORT

        On reversal (direction change), emits a CLOSE signal followed by
        the new direction signal at the same candle index. The engine
        processes CLOSE first, then the new entry.

        All signals use size=1.0 (100% of available cash).
        SL/TP levels are computed relative to the close price at the signal candle.
        """
        if len(df) < self.slow_period:
            return []

        close = df["close"]
        fast_ma = close.rolling(window=self.fast_period).mean()
        slow_ma = close.rolling(window=self.slow_period).mean()

        signals: List[Signal] = []
        last_direction: Optional[SignalType] = None

        for i in range(1, len(df)):
            if pd.isna(fast_ma.iloc[i - 1]) or pd.isna(slow_ma.iloc[i - 1]):
                continue
            if pd.isna(fast_ma.iloc[i]) or pd.isna(slow_ma.iloc[i]):
                continue

            prev_fast = fast_ma.iloc[i - 1]
            prev_slow = slow_ma.iloc[i - 1]
            curr_fast = fast_ma.iloc[i]
            curr_slow = slow_ma.iloc[i]

            signal_close = close.iloc[i]
            new_direction: Optional[SignalType] = None

            # Cross above: fast was <= slow, now fast > slow -> LONG
            if prev_fast <= prev_slow and curr_fast > curr_slow:
                new_direction = SignalType.LONG
                sl = signal_close * (1 - self.sl_pct)
                tp = signal_close * (1 + self.tp_pct)

            # Cross below: fast was >= slow, now fast < slow -> SHORT
            elif prev_fast >= prev_slow and curr_fast < curr_slow:
                new_direction = SignalType.SHORT
                sl = signal_close * (1 + self.sl_pct)
                tp = signal_close * (1 - self.tp_pct)

            if new_direction is None:
                continue

            # If reversing, emit CLOSE first at the same candle index
            if last_direction is not None and last_direction != new_direction:
                signals.append(Signal(
                    timestamp_index=i,
                    signal_type=SignalType.CLOSE,
                    stop_loss_level=0.0,
                    take_profit_level=0.0,
                    size=1.0,
                ))

            # Emit the directional signal
            signals.append(Signal(
                timestamp_index=i,
                signal_type=new_direction,
                stop_loss_level=sl,
                take_profit_level=tp,
                size=1.0,
            ))

            last_direction = new_direction

        return signals

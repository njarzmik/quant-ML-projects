from abc import ABC, abstractmethod
from typing import List

import pandas as pd

from strategies.signals import Signal


class BaseStrategy(ABC):
    @abstractmethod
    def generate(self, df: pd.DataFrame) -> List[Signal]:
        """Generate trading signals from OHLC data.

        Args:
            df: DataFrame with DatetimeIndex and columns: open, high, low, close, spread.

        Returns:
            List of Signal objects ordered by timestamp_index.
        """
        ...

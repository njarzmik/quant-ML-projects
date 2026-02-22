import pandas as pd

REQUIRED_COLUMNS = {"open", "high", "low", "close", "spread"}


def load_csv(path: str) -> pd.DataFrame:
    """Load a 1-minute OHLC CSV file into a DataFrame.

    Expected columns: timestamp, open, high, low, close, spread.
    The timestamp column becomes a DatetimeIndex.

    Raises ValueError if required columns are missing or data is invalid.
    """
    df = pd.read_csv(path, parse_dates=True, index_col=0)
    df.index = pd.to_datetime(df.index)
    df.index.name = "timestamp"

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df.isna().any().any():
        raise ValueError("Dataset contains NaN values")

    if not (df["spread"] > 0).all():
        raise ValueError("All spread values must be positive")

    if not (df["high"] >= df[["open", "close"]].max(axis=1)).all():
        raise ValueError("OHLC sanity check failed: high < max(open, close)")

    if not (df["low"] <= df[["open", "close"]].min(axis=1)).all():
        raise ValueError("OHLC sanity check failed: low > min(open, close)")

    return df


def resample(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Resample a 1-minute OHLC DataFrame to a larger timeframe.

    Args:
        df: DataFrame with DatetimeIndex and OHLC + spread columns.
        timeframe: Pandas-compatible frequency string (e.g. '5min', '15min', '30min', '60min').

    Returns:
        Resampled DataFrame with standard OHLC aggregation.
    """
    agg_rules = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "spread": "mean",
    }
    resampled = df.resample(timeframe).agg(agg_rules)
    resampled.dropna(inplace=True)
    return resampled

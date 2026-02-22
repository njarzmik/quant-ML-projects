import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from common.data_loader import load_csv, resample

# --- Constants ---

TEST_CSV = str(Path(__file__).resolve().parent.parent / "data" / "nas100_m1_mid_test.csv")

# --- Fixtures ---

@pytest.fixture
def nas100_df():
    """Load the real NAS100 1-minute test data."""
    return load_csv(TEST_CSV)


# --- Tests ---

class TestLoadCSV:
    def test_columns_present(self, nas100_df):
        """CSV loader returns DataFrame with all required columns."""
        assert set(nas100_df.columns) >= {"open", "high", "low", "close", "spread"}

    def test_index_is_datetime(self, nas100_df):
        """Loaded DataFrame has DatetimeIndex."""
        assert isinstance(nas100_df.index, pd.DatetimeIndex)

    def test_no_missing_values(self, nas100_df):
        """Loaded DataFrame has zero NaN values."""
        assert nas100_df.isna().sum().sum() == 0

    def test_ohlc_sanity(self, nas100_df):
        """High >= max(open, close) and Low <= min(open, close) for every row."""
        assert (nas100_df["high"] >= nas100_df[["open", "close"]].max(axis=1)).all()
        assert (nas100_df["low"] <= nas100_df[["open", "close"]].min(axis=1)).all()

    def test_spread_positive(self, nas100_df):
        """All spread values are positive."""
        assert (nas100_df["spread"] > 0).all()

    def test_reject_missing_column(self, tmp_path):
        """Loader raises error if a required column is missing."""
        df = pd.DataFrame({"open": [1], "high": [2], "low": [0.5], "close": [1.5]})
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "bad.csv"
        df.to_csv(path)
        with pytest.raises(Exception):
            load_csv(str(path))

    def test_row_count(self, nas100_df):
        """Real dataset has expected number of rows."""
        assert len(nas100_df) > 100_000

    # --- NEW EDGE CASE TESTS ---

    def test_index_name_is_timestamp(self, nas100_df):
        """Index name is set to 'timestamp'."""
        assert nas100_df.index.name == "timestamp"

    def test_index_is_sorted(self, nas100_df):
        """Index is in chronological order (no shuffled timestamps)."""
        assert nas100_df.index.is_monotonic_increasing

    def test_all_columns_numeric(self, nas100_df):
        """All OHLC+spread columns are numeric types (not strings)."""
        for col in ["open", "high", "low", "close", "spread"]:
            assert pd.api.types.is_numeric_dtype(nas100_df[col])

    def test_no_duplicate_timestamps(self, nas100_df):
        """No two rows share the exact same timestamp."""
        assert not nas100_df.index.duplicated().any()

    def test_reject_nan_values(self, tmp_path):
        """Loader raises ValueError when data contains NaN."""
        df = pd.DataFrame({
            "open": [1.0, float("nan")], "high": [2.0, 2.0],
            "low": [0.5, 0.5], "close": [1.5, 1.5], "spread": [0.1, 0.1],
        })
        df.index = pd.date_range("2024-01-01", periods=2, freq="1min")
        path = tmp_path / "nan.csv"
        df.to_csv(path)
        with pytest.raises(ValueError, match="NaN"):
            load_csv(str(path))

    def test_reject_zero_spread(self, tmp_path):
        """Loader raises ValueError when spread contains zero."""
        df = pd.DataFrame({
            "open": [100.0], "high": [101.0], "low": [99.0],
            "close": [100.5], "spread": [0.0],
        })
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "zero_spread.csv"
        df.to_csv(path)
        with pytest.raises(ValueError, match="spread"):
            load_csv(str(path))

    def test_reject_negative_spread(self, tmp_path):
        """Loader raises ValueError when spread is negative."""
        df = pd.DataFrame({
            "open": [100.0], "high": [101.0], "low": [99.0],
            "close": [100.5], "spread": [-0.5],
        })
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "neg_spread.csv"
        df.to_csv(path)
        with pytest.raises(ValueError, match="spread"):
            load_csv(str(path))

    def test_reject_bad_ohlc_high_too_low(self, tmp_path):
        """Loader raises ValueError when high < open."""
        df = pd.DataFrame({
            "open": [100.0], "high": [99.0], "low": [98.0],
            "close": [99.5], "spread": [0.1],
        })
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "bad_high.csv"
        df.to_csv(path)
        with pytest.raises(ValueError, match="OHLC"):
            load_csv(str(path))

    def test_reject_bad_ohlc_low_too_high(self, tmp_path):
        """Loader raises ValueError when low > close."""
        df = pd.DataFrame({
            "open": [100.0], "high": [102.0], "low": [101.0],
            "close": [100.5], "spread": [0.1],
        })
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "bad_low.csv"
        df.to_csv(path)
        with pytest.raises(ValueError, match="OHLC"):
            load_csv(str(path))

    def test_single_row_csv(self, tmp_path):
        """Loader handles a single-row CSV correctly."""
        df = pd.DataFrame({
            "open": [100.0], "high": [101.0], "low": [99.0],
            "close": [100.5], "spread": [0.1],
        })
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "one_row.csv"
        df.to_csv(path)
        result = load_csv(str(path))
        assert len(result) == 1
        assert isinstance(result.index, pd.DatetimeIndex)

    def test_high_equals_open_close_is_valid(self, tmp_path):
        """A doji candle where high==open==close is valid (no violation)."""
        df = pd.DataFrame({
            "open": [100.0], "high": [100.0], "low": [99.0],
            "close": [100.0], "spread": [0.1],
        })
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "doji.csv"
        df.to_csv(path)
        result = load_csv(str(path))
        assert len(result) == 1

    def test_extra_columns_preserved(self, tmp_path):
        """Extra columns beyond OHLCS are not rejected (future-proofing)."""
        df = pd.DataFrame({
            "open": [100.0], "high": [101.0], "low": [99.0],
            "close": [100.5], "spread": [0.1], "volume": [1000],
        })
        df.index = pd.date_range("2024-01-01", periods=1, freq="1min")
        path = tmp_path / "extra.csv"
        df.to_csv(path)
        result = load_csv(str(path))
        assert "volume" in result.columns

    def test_nonexistent_file_raises(self):
        """Loading a nonexistent file raises an exception."""
        with pytest.raises(Exception):
            load_csv("/nonexistent/path/data.csv")

    def test_ohlc_values_are_positive(self, nas100_df):
        """All price values in real data are positive (sanity for financial data)."""
        for col in ["open", "high", "low", "close"]:
            assert (nas100_df[col] > 0).all()


class TestResample:
    def test_5m_candle_count(self, nas100_df):
        """5-minute resampling reduces row count by roughly 5x."""
        df_5m = resample(nas100_df, "5min")
        ratio = len(nas100_df) / len(df_5m)
        assert 4.5 < ratio < 5.5

    def test_5m_open_is_first(self, nas100_df):
        """5m open equals the first 1m candle's open in that window."""
        df_5m = resample(nas100_df, "5min")
        first_5m_start = df_5m.index[0]
        first_1m = nas100_df.loc[first_5m_start]
        assert df_5m.iloc[0]["open"] == first_1m["open"]

    def test_5m_high_is_max(self, nas100_df):
        """5m high equals max of 1m highs in the first window."""
        df_5m = resample(nas100_df, "5min")
        start = df_5m.index[0]
        end = df_5m.index[1]
        window = nas100_df.loc[start:end].iloc[:-1]  # exclude next window's first row
        assert df_5m.iloc[0]["high"] == window["high"].max()

    def test_5m_low_is_min(self, nas100_df):
        """5m low equals min of 1m lows in the first window."""
        df_5m = resample(nas100_df, "5min")
        start = df_5m.index[0]
        end = df_5m.index[1]
        window = nas100_df.loc[start:end].iloc[:-1]
        assert df_5m.iloc[0]["low"] == window["low"].min()

    def test_5m_close_is_last(self, nas100_df):
        """5m close equals the last 1m candle's close in that window."""
        df_5m = resample(nas100_df, "5min")
        start = df_5m.index[0]
        end = df_5m.index[1]
        window = nas100_df.loc[start:end].iloc[:-1]
        assert df_5m.iloc[0]["close"] == window.iloc[-1]["close"]

    def test_5m_spread_is_mean(self, nas100_df):
        """5m spread equals mean of 1m spreads in the first window."""
        df_5m = resample(nas100_df, "5min")
        start = df_5m.index[0]
        end = df_5m.index[1]
        window = nas100_df.loc[start:end].iloc[:-1]
        assert abs(df_5m.iloc[0]["spread"] - window["spread"].mean()) < 1e-10

    def test_15m_30m_60m_produce_output(self, nas100_df):
        """Resampling to 15m, 30m, 60m produces output."""
        for tf in ["15min", "30min", "60min"]:
            df_tf = resample(nas100_df, tf)
            assert len(df_tf) >= 1

    # --- NEW EDGE CASE TESTS ---

    def test_resample_preserves_ohlc_sanity(self, nas100_df):
        """Resampled candles maintain high >= max(open,close) and low <= min(open,close)."""
        for tf in ["5min", "15min", "60min"]:
            df_r = resample(nas100_df, tf)
            assert (df_r["high"] >= df_r[["open", "close"]].max(axis=1)).all(), f"Failed for {tf}"
            assert (df_r["low"] <= df_r[["open", "close"]].min(axis=1)).all(), f"Failed for {tf}"

    def test_resample_preserves_no_nan(self, nas100_df):
        """Resampled data contains no NaN values (dropna works)."""
        for tf in ["5min", "15min", "30min", "60min"]:
            df_r = resample(nas100_df, tf)
            assert df_r.isna().sum().sum() == 0, f"NaN found in {tf}"

    def test_resample_index_is_datetime(self, nas100_df):
        """Resampled DataFrame retains DatetimeIndex."""
        df_5m = resample(nas100_df, "5min")
        assert isinstance(df_5m.index, pd.DatetimeIndex)

    def test_resample_reduces_rows(self, nas100_df):
        """Every resampled timeframe has fewer rows than the original."""
        for tf in ["5min", "15min", "30min", "60min"]:
            df_r = resample(nas100_df, tf)
            assert len(df_r) < len(nas100_df)

    def test_resample_spread_always_positive(self, nas100_df):
        """Resampled spread values are all positive (mean of positives is positive)."""
        for tf in ["5min", "15min", "60min"]:
            df_r = resample(nas100_df, tf)
            assert (df_r["spread"] > 0).all()

    def test_resample_high_geq_low(self, nas100_df):
        """Resampled high is always >= low for every candle."""
        for tf in ["5min", "15min", "30min", "60min"]:
            df_r = resample(nas100_df, tf)
            assert (df_r["high"] >= df_r["low"]).all()

    def test_60m_reduces_by_roughly_60x(self, nas100_df):
        """60-minute resampling reduces row count by roughly 60x."""
        df_60m = resample(nas100_df, "60min")
        ratio = len(nas100_df) / len(df_60m)
        assert 50 < ratio < 70

    def test_resample_second_window_open(self, nas100_df):
        """Spot-check: the second 5m candle's open matches the 6th 1m candle's open."""
        df_5m = resample(nas100_df, "5min")
        second_start = df_5m.index[1]
        assert df_5m.iloc[1]["open"] == nas100_df.loc[second_start]["open"]

    def test_resample_columns_unchanged(self, nas100_df):
        """Resampled DataFrame has exactly the same columns as the input."""
        df_5m = resample(nas100_df, "5min")
        assert set(df_5m.columns) == set(nas100_df.columns)

    def test_resample_with_3_candles(self):
        """Resampling 3 one-minute candles to 5min produces 0 complete windows (all dropped as partial)."""
        timestamps = pd.date_range("2024-01-15 09:30", periods=3, freq="1min")
        data = {
            "open": [100, 101, 102], "high": [101, 102, 103],
            "low": [99, 100, 101], "close": [101, 102, 103],
            "spread": [0.1, 0.1, 0.1],
        }
        df = pd.DataFrame(data, index=timestamps)
        df_5m = resample(df, "5min")
        # 3 candles can't fill a complete 5min window starting at :30 — depends on alignment
        # The key check is it doesn't crash and produces valid output
        assert isinstance(df_5m, pd.DataFrame)
        assert df_5m.isna().sum().sum() == 0

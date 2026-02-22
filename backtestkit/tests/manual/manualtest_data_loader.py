from common.data_loader import load_csv,resample
import numpy as np

df = load_csv("C:/Users/rjarz/Documents/backtestkit/data/nas100_m1_mid_test.csv")
df_5m = resample(df,"5min")
df_15m = resample(df,"15min")
df_30m = resample(df,"30min")
df_60m = resample(df,"60min")
print(df.head(121).to_string())
print(df_5m.head(25))
print(df_15m.head(9))
print(df_30m.head(5))
print(df_60m.head(3))
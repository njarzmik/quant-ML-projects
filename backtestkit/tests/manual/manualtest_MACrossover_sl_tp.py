import pytest
import pandas as pd
import numpy as np
from strategies.ma_crossover import MACrossoverStrategy
from strategies.signals import Signal
from common.models import SignalType

from backtester.sl_tp import check_sl_tp, PositionUnit
from common.models import ExecutionMode

def trending_up_df():
    """Price series that forces one clear crossover: fast crosses above slow."""
    n = 40
    timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
    prices = [100.0] * 20 + [100.0 + i * 0.5 for i in range(1, 21)]
    data = {
        "open":   prices,
        "high":   [p + 0.2 for p in prices],
        "low":    [p - 0.2 for p in prices],
        "close":  prices,
        "spread": [0.10] * n,
    }
    return pd.DataFrame(data, index=timestamps)


def crossover_then_crossunder_df():
    """Price that goes up (cross above) then back down (cross below)."""
    n = 70
    timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
    prices = (
        [100.0] * 25                                  # flat long enough for slow MA to stabilize
        + [100.0 + i * 0.5 for i in range(1, 16)]    # up
        + [107.5 - i * 0.5 for i in range(1, 16)]    # down
        + [100.0] * 15                                # flat tail
    )
    data = {
        "open": prices, "high": [p+0.2 for p in prices],
        "low": [p-0.2 for p in prices], "close": prices,
        "spread": [0.10] * n,
    }
    return pd.DataFrame(data, index=timestamps)



def test_single_long_signal(trending_up_df):
    """A clear uptrend produces at least one LONG signal."""
    strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
    signals = strategy.generate(trending_up_df)
    long_signals = [s for s in signals if s.signal_type == SignalType.LONG]
    df = trending_up_df
    df["fast_ma"] = df["close"].rolling(window=5).mean()
    df["slow_ma"] = df["close"].rolling(window=20).mean()

    print(df)
    print(signals)

def test_crossunder_produces_short(crossover_then_crossunder_df):
    """An uptrend followed by downtrend produces LONG then SHORT."""
    strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
    signals = strategy.generate(crossover_then_crossunder_df)
    df = crossover_then_crossunder_df
    df["fast_ma"] = df["close"].rolling(window=5).mean()
    df["slow_ma"] = df["close"].rolling(window=20).mean()
    print(df)
    print(signals)
   # types = [s.signal_type for s in signals]
    #assert SignalType.LONG in types
   # assert SignalType.SHORT in types
  #  first_long = next(i for i, t in enumerate(types) if t == SignalType.LONG)
 #   first_short = next(i for i, t in enumerate(types) if t == SignalType.SHORT)
#    assert first_long < first_short


#print(test_single_long_signal(trending_up_df()))
##print(test_crossunder_produces_short(crossover_then_crossunder_df()))

print("hola")

def test_no_signal_in_flat_market():
    """Completely flat prices produce zero signals."""
    n = 50
    timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
    data = {
        "open": [100.0]*n, "high": [100.0]*n,
        "low": [100.0]*n, "close": [100.0]*n,
        "spread": [0.10]*n,
    }
    df = pd.DataFrame(data, index=timestamps)
    strategy = MACrossoverStrategy(fast_period=5, slow_period=20)
    signals = strategy.generate(df)
    df["fast_ma"] = df["close"].rolling(window=5).mean()
    df["slow_ma"] = df["close"].rolling(window=20).mean()

    print(df)
    print(signals)

#print(test_no_signal_in_flat_market())


def test_exactly_slow_period_candles():
    """Data with exactly slow_period candles — barely enough for one MA value."""
    n = 30
    timestamps = pd.date_range("2024-01-15 09:30", periods=n, freq="1min")
    prices = [100.0]*15 + [100.0 + i*0.5 for i in range(1, 16)]
    data = {
        "open": prices, "high": [p+0.2 for p in prices],
        "low": [p-0.2 for p in prices], "close": prices,
        "spread": [0.10]*n,
    }
    df = pd.DataFrame(data, index=timestamps)
    strategy = MACrossoverStrategy(fast_period=10, slow_period=30)
    signals = strategy.generate(df)
    # Should not crash. May or may not produce signals depending on data.

    df["fast_ma"] = df["close"].rolling(window=10).mean()
    df["slow_ma"] = df["close"].rolling(window=30).mean()

    print(df.head(121).to_string())
    print(signals)
    

#test_exactly_slow_period_candles()

############################################## testing MA_crossover signas + sl_tp signal###################################
df = pd.read_csv(
    "C:/Users/rjarz/Documents/backtestkit/data/nas100_m1_mid_test.csv",
    parse_dates=True,
    index_col=0
)
df = df.head(200)
strategy = MACrossoverStrategy(fast_period=10, slow_period=30,sl_pct=0.001,tp_pct=0.001)
signals = strategy.generate(df)

mode = ExecutionMode.SPREAD_ON
sl_tp_events = []  # collect (candle_idx, direction, triggered, exit_price, sl, tp) for plotting

for sig in signals:
    
    if sig.signal_type.value not in ["LONG", "SHORT"]:
        continue

    ### ONLY ANALYZIG OPEN SIGNAL POSITIONS.
    ### STACKING -> NOT POSSIBLE IN MSA CROSSOVER. ONLY SIGNALS: OPEN -> CLOSE -> OPEN => CLOSE.

    ### RETRIEVIE UNIT INFORMATION ## DIRECTION, ENTRY_PRICE, SIZE, SL, TP.
    unit =  {direction: sig.signal_type.value, }
    direction = sig.signal_type.value
    entry_idx = sig.timestamp_index

    if entry_idx < 0 or entry_idx >= len(df):
        continue
    
    for ibartracking in range(entry_idx,len(df)):
        candle = df[ibartracking] #possible sl/tp signal at the SAME bar
        result = check_sl_tp()
         
    

#### sl_tp execution signals ####


df["fast_ma"] = df["close"].rolling(window=10).mean()
df["slow_ma"] = df["close"].rolling(window=30).mean()

import matplotlib.pyplot as plt
import matplotlib.patches as patches


N = len(df)

plt.figure()

# --- price + MAs ---
plt.plot(df.index, df["close"], label="Close")
plt.plot(df.index, df["fast_ma"], label="SMA-10")
plt.plot(df.index, df["slow_ma"], label="SMA-30")

# --- signals ---
for sig in signals:
    i = sig.timestamp_index

    # pomijamy sygnały spoza zakresu head(200)
    if i < 0 or i >= N:
        continue

    ts = df.index[i]
    price = df["close"].iloc[i]

    st = sig.signal_type.value  # Enum -> "LONG"/"SHORT"/"CLOSE"

    if st == "LONG":
        plt.scatter(ts, price, marker="^", color="green", s=80,
                    label="LONG" if "LONG" not in plt.gca().get_legend_handles_labels()[1] else "")
    elif st == "SHORT":
        plt.scatter(ts, price, marker="v", color="red", s=80,
                    label="SHORT" if "SHORT" not in plt.gca().get_legend_handles_labels()[1] else "")
    elif st == "CLOSE":
        plt.scatter(ts, price, marker="s", color="blue", s=60,
                    label="CLOSE" if "CLOSE" not in plt.gca().get_legend_handles_labels()[1] else "")

ax = plt.gca()

for i, sig in enumerate(signals):

    if sig.signal_type.value not in ["LONG", "SHORT"]:
        continue

    entry_idx = sig.timestamp_index
    if entry_idx < 0 or entry_idx >= len(df):
        continue

    entry_time = df.index[entry_idx]
    entry_price = df["close"].iloc[entry_idx]

    sl = sig.stop_loss_level
    tp = sig.take_profit_level

    # --- znajdź najbliższy CLOSE po wejściu ---
    exit_idx = None
    for j in range(i+1, len(signals)):
        if signals[j].signal_type.value == "CLOSE":
            exit_idx = signals[j].timestamp_index
            break

    if exit_idx is None or exit_idx >= len(df):
        continue

    exit_time = df.index[exit_idx]

    # szerokość w czasie (matplotlib liczy w liczbach)
    width = exit_time - entry_time

    # --- STOP LOSS BOX ---
    sl_bottom = min(entry_price, sl)
    sl_height = abs(entry_price - sl)

    rect_sl = patches.Rectangle(
        (entry_time, sl_bottom),
        width,
        sl_height,
        linewidth=0,
        edgecolor=None,
        facecolor="red",
        alpha=0.2
    )
    ax.add_patch(rect_sl)

    # --- TAKE PROFIT BOX ---
    tp_bottom = min(entry_price, tp)
    tp_height = abs(entry_price - tp)

    rect_tp = patches.Rectangle(
        (entry_time, tp_bottom),
        width,
        tp_height,
        linewidth=0,
        edgecolor=None,
        facecolor="green",
        alpha=0.2
    )
    ax.add_patch(rect_tp)

plt.title("Close + SMA(10/30) with Signals")
plt.xlabel("Time")
plt.ylabel("Price")
plt.legend()
plt.show()




###WORKS


############################################## SL/TP ENGINE MANUAL TEST ###################################
# Uses the same df and signals from above.
# For each directional signal, creates a PositionUnit and walks forward candle-by-candle
# calling check_sl_tp() until something triggers (or a CLOSE signal is reached).
# Prints a detailed log and plots trigger points on a second chart.

from backtester.sl_tp import check_sl_tp, PositionUnit
from common.models import ExecutionMode

print("\n" + "="*80)
print("SL/TP ENGINE TEST — walking through candles with check_sl_tp()")
print("="*80)

mode = ExecutionMode.SPREAD_ON
sl_tp_events = []  # collect (candle_idx, direction, triggered, exit_price, sl, tp) for plotting

for i, sig in enumerate(signals):
    if sig.signal_type.value not in ["LONG", "SHORT"]:
        continue

    direction = sig.signal_type.value
    entry_idx = sig.timestamp_index
    if entry_idx < 0 or entry_idx >= len(df):
        continue

    entry_close = df["close"].iloc[entry_idx]
    sl = sig.stop_loss_level
    tp = sig.take_profit_level
    spread_at_entry = df["spread"].iloc[entry_idx]

    # Find the next CLOSE signal index (the strategy's exit) as a boundary
    close_idx = len(df)  # default: end of data
    for j in range(i + 1, len(signals)):
        if signals[j].signal_type.value == "CLOSE":
            close_idx = signals[j].timestamp_index
            break

    # Create a PositionUnit (simulate entry at next candle open, as the engine would)
    exec_idx = entry_idx + 1
    if exec_idx >= len(df):
        continue

    exec_open = df["open"].iloc[exec_idx]
    unit = PositionUnit(
        direction=direction,
        entry_price=exec_open,  # engine executes at i+1 open
        size=10.0,              # arbitrary for this test
        sl=sl,
        tp=tp,
    )

    print(f"\n--- {direction} signal at candle {entry_idx} ({df.index[entry_idx]}) ---")
    print(f"    Entry close: {entry_close:.2f}, Exec open (i+1): {exec_open:.2f}")
    print(f"    SL: {sl:.4f}, TP: {tp:.4f}, Spread: {spread_at_entry:.2f}")
    print(f"    Walking candles {exec_idx} to {min(close_idx, len(df)-1)}...")

    triggered = False
    for c in range(exec_idx, min(close_idx + 1, len(df))):
        candle = {
            "open":   df["open"].iloc[c],
            "high":   df["high"].iloc[c],
            "low":    df["low"].iloc[c],
            "close":  df["close"].iloc[c],
            "spread": df["spread"].iloc[c],
        }
        result = check_sl_tp(unit, candle, mode)

        if result.triggered is not None:
            pnl_per_unit = (result.exit_price - unit.entry_price) if direction == "LONG" \
                           else (unit.entry_price - result.exit_price)
            print(f"    >> Candle {c} ({df.index[c]}): {result.triggered} TRIGGERED!")
            print(f"       H={candle['high']:.2f} L={candle['low']:.2f} spread={candle['spread']:.2f}")
            print(f"       Exit price: {result.exit_price:.4f}")
            print(f"       PnL per unit: {pnl_per_unit:.4f}")
            sl_tp_events.append((c, direction, result.triggered, result.exit_price, sl, tp))
            triggered = True
            break

    if not triggered:
        print(f"    >> No SL/TP trigger before CLOSE signal at candle {close_idx}")
        sl_tp_events.append(None)

print(f"\n{'='*80}")
print(f"Summary: {len([e for e in sl_tp_events if e is not None])} SL/TP triggers "
      f"out of {len([s for s in signals if s.signal_type.value in ['LONG','SHORT']])} directional signals")
sl_count = len([e for e in sl_tp_events if e is not None and e[2] == "SL"])
tp_count = len([e for e in sl_tp_events if e is not None and e[2] == "TP"])
print(f"  SL hits: {sl_count}, TP hits: {tp_count}")
print(f"{'='*80}")


# --- SECOND CHART: same price chart but with SL/TP trigger markers ---
plt.figure()
plt.plot(df.index, df["close"], label="Close", color="gray", alpha=0.7)
plt.plot(df.index, df["fast_ma"], label="SMA-10", alpha=0.5)
plt.plot(df.index, df["slow_ma"], label="SMA-30", alpha=0.5)

# Plot entry signals
for sig in signals:
    idx = sig.timestamp_index
    if idx < 0 or idx >= len(df):
        continue
    ts = df.index[idx]
    price = df["close"].iloc[idx]
    st = sig.signal_type.value
    if st == "LONG":
        plt.scatter(ts, price, marker="^", color="green", s=60, zorder=5)
    elif st == "SHORT":
        plt.scatter(ts, price, marker="v", color="red", s=60, zorder=5)

# Plot SL/TP trigger points
for event in sl_tp_events:
    if event is None:
        continue
    c_idx, direction, trig_type, exit_price, sl_lvl, tp_lvl = event
    ts = df.index[c_idx]

    if trig_type == "SL":
        plt.scatter(ts, exit_price, marker="x", color="red", s=120, linewidths=2, zorder=10,
                    label="SL hit" if "SL hit" not in plt.gca().get_legend_handles_labels()[1] else "")
    elif trig_type == "TP":
        plt.scatter(ts, exit_price, marker="*", color="lime", s=120, zorder=10,
                    label="TP hit" if "TP hit" not in plt.gca().get_legend_handles_labels()[1] else "")

plt.title("SL/TP Engine Test — Trigger Points on Price Chart")
plt.xlabel("Time")
plt.ylabel("Price")
plt.legend()
plt.show()
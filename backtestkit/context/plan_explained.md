# Implementation Plan — Explained

This document walks through every phase of `plan.md` in plain English. It explains **what** each piece does, **why** it exists, **why it's in that order**, and what the tricky parts are. If you understand this document, you understand the entire system.

---

## The Big Picture First

You are building two completely separate things that talk to each other:

1. **A strategy** (`strategies/`) — this looks at historical price data and says "buy here", "sell here", "close everything here". That's all it does. It has no idea how much money you have, what your position is, or what the spread costs. It just looks at charts and produces signals.

2. **A backtester** (`backtester/`) — this takes those signals, takes the price data, and simulates what would have happened if you had actually traded those signals with real money. It tracks your cash, your positions, your profits and losses, and at the end tells you how well you did.

The reason they are separate is the same reason you separate a chef from a waiter. The chef (strategy) decides what food to make. The waiter (backtester) serves it and handles the bill. If you want a different chef later, you swap them out without touching the waiter. If you want to change how billing works, you don't touch the kitchen.

The flow is always:

```
CSV file → load data → strategy reads data → strategy outputs signals → backtester reads signals + data → backtester simulates trades → results
```

Nothing ever goes backwards. The strategy never asks the backtester "how much money do I have?" — that would break the separation.

---

## Why This Order of Phases?

The phases are ordered by **dependency**. Each phase only needs things built in earlier phases. You could not build them in a different order without hitting blockers:

- **Phase 1 (Data)** comes first because literally everything else needs data to work with. You can't test a strategy without price data. You can't test a backtester without price data.

- **Phase 2 (Strategy/Signals)** comes second because the backtester needs signals to consume. Without signals, the backtester has nothing to do.

- **Phases 3-5 (Execution Modes, Capital, SL/TP)** are the building blocks of the backtester engine. They're separate modules because each one does one job. Phase 3 answers "what price do I buy/sell at?", Phase 4 answers "how much money do I have and how many units can I buy?", Phase 5 answers "should I exit this trade because it hit my stop loss or take profit?"

- **Phase 6 (Main Loop)** glues Phases 3-5 together. It's the conductor — it calls the price resolver, the portfolio manager, and the SL/TP checker in the right order for every candle. It couldn't be built before those pieces exist.

- **Phases 7-9 (Logging, Metrics, Visualization)** are output layers. They don't affect the simulation, they just report on it. They come after the engine works.

- **Phase 10 (Integration)** wires the whole thing into a single command. This is last (before validation) because all pieces must exist first.

- **Phase 11 (Hardening)** is the final check — making sure everything is correct, deterministic, and handles weird edge cases.

---

## Phase 1: Project Scaffolding & Data Layer — Explained

### What it is

This phase creates the folder structure, installs dependencies, and builds the code that reads your CSV files and turns them into usable DataFrames.

### Why `pyproject.toml` and `requirements.txt`

`pyproject.toml` defines your project as a proper Python package. This matters because your code is split across multiple folders (`backtester/`, `strategies/`, `common/`), and Python needs to know that these folders are importable packages. Without it, `from common.data_loader import load_csv` would fail with an ImportError.

`requirements.txt` lists exactly which libraries you need: `pandas` (DataFrames), `numpy` (math), `matplotlib` (charts), `pytest` (testing). Anyone who clones your project can run `pip install -r requirements.txt` and have everything they need.

### Why `common/` exists as a third folder

The spec defines two folders: `backtester/` and `strategies/`. But both of them need to share some things — the data loader, the signal types (LONG, SHORT, CLOSE), the execution mode enum. If you put these shared types inside `backtester/`, then `strategies/` would have to import from `backtester/`, which creates a dependency in the wrong direction (the strategy shouldn't depend on the backtester). So we create a third folder `common/` that both can import from without depending on each other.

### Why the data is mid-price candles with a separate spread column

In real markets, there's always a **bid** (what buyers will pay) and an **ask** (what sellers want). The difference is the **spread** — this is the broker's fee, essentially. The **mid-price** is the average of bid and ask: `(bid + ask) / 2`.

The data stores mid-prices because mid-prices are a neutral reference point. When you actually trade, you don't get the mid — if you're buying, you pay the ask (higher), and if you're selling, you get the bid (lower). The spread column tells us how far apart bid and ask were at that minute, so we can reconstruct them: `bid = mid - spread/2`, `ask = mid + spread/2`.

This matters because it means every trade you make costs you half the spread on each side. Buy at ask, sell at bid — you lose the full spread on a round trip. This is realistic. A backtester that ignores spread will show way better results than you'd actually get.

### Why resampling 1m to 5m, 15m, 30m, 60m

The strategy specification says it receives multi-timeframe data. A moving average on 1-minute candles is very noisy and reacts to every tiny price tick. A moving average on 60-minute candles is much smoother and captures bigger trends. Strategies often combine multiple timeframes — for example, using the 60m trend to decide direction and the 1m data to time the entry.

Resampling takes five 1-minute candles and compresses them into one 5-minute candle. The rules are standard in finance:
- **Open** = first candle's open (the price at the start of that 5-minute window)
- **High** = highest high across all 5 candles (the peak during that window)
- **Low** = lowest low across all 5 candles (the trough during that window)
- **Close** = last candle's close (the price at the end of that window)
- **Spread** = mean of all 5 spreads (average spread during that window)

The open/high/low/close rules are not arbitrary — they're how candles are universally defined in financial markets.

### Why test CSV data

You need something to test with during development. The project uses real NAS100 1-minute market data (`data/nas100_m1_mid_test.csv`, ~161k rows) as the test dataset. This ensures tests validate against real-world data with realistic spreads, price movements, and edge cases that synthetic data might miss. All Phase 1 automated tests load this file directly.

---

## Phase 2: Signal Generator — Explained

### What it is

The strategy module. It looks at price data and emits a list of signals: "go long at candle 47", "go short at candle 103", etc.

### Why an abstract base class (`base_strategy.py`)

The spec says Phase 1 is a Moving Average Crossover strategy. But the word "Phase 1" implies there will be Phase 2, Phase 3 — different strategies in the future. An abstract base class defines the contract: "every strategy must have a `generate(data)` method that takes price data and returns a list of Signal objects." Then the MA Crossover strategy implements that contract. If you later build an RSI strategy or a Bollinger Bands strategy, they also implement the same contract, and the backtester doesn't need to change at all — it just consumes signals regardless of which strategy produced them.

- class BaseStrategy(ABC) -> means that it creates a class, taht inherits its features from ABC. You are tellin python "this class is abstract! - its a blueprint, of how strategies are supposed to look like, this class is not meant to be used directly"
-@abstractmethod is used above a function that tells python "Any child class MUST provide its own version of this mmethod

We combine this two, and when creating a strategy class for eg ma_crossover(BaseStrategy), we force this class to look like the blueprint class: BaseStrategy - with a function generate, hat takes a dataframe, and returns a list of Signals!! (Signal is a dataclass. Check signals.py)

  The chain is:
  ABC  (Python built-in: "I'm abstract")
   └── BaseStrategy  (our blueprint: "strategies must have generate()")
        └── MACrossoverStrategy  (actual implementation: "here's my generate()")

Why are they in separate files?
  Think of it this way:
  - base_strategy.py = the contract/rule book. It says "every strategy must have a generate() method." It doesn't know anything about moving
  averages, RSI, or any specific technique.
  - ma_crossover.py = one specific implementation of that contract, using MA crossovers.

  Tomorrow you might want to add an RSI strategy:
  strategies/
      base_strategy.py          # the contract (unchanged)
      ma_crossover.py           # implementation #1
      rsi_strategy.py           # implementation #2 (new!)
      bollinger_strategy.py     # implementation #3 (new!)

  All three would inherit from BaseStrategy, all three must have generate(), but each does it differently. The rest of the codebase (the
  backtester engine) doesn't care which strategy it gets — it just calls .generate() and knows it'll get back a List[Signal].

  If they were in the same file, adding new strategies would make that file grow endlessly.


### How Moving Average Crossover works

A **moving average** (MA) is the average of the last N closing prices. A **fast** MA uses a small N (like 10), so it reacts quickly to price changes. A **slow** MA uses a large N (like 30), so it moves slowly and represents the longer-term trend.

When the fast MA **crosses above** the slow MA, it means short-term price momentum is now above the long-term average — the price is accelerating upward. This is a buy signal (LONG).

When the fast MA **crosses below** the slow MA, the opposite is happening — price momentum is turning down. This is a sell signal (SHORT).

The "crossover" is specifically the moment of crossing: the candle where `fast > slow` but on the previous candle `fast <= slow`. This is detected by comparing consecutive values.

### Why SL/TP levels are set at signal time, not entry time

The strategy says "go long here" and also says "if the price drops 2%, cut the loss (stop loss), and if the price rises 2%, take the profit (take profit)." These levels are calculated from the **close price at the signal candle**, which is an approximation of where the entry will happen. The actual entry happens at the next candle's open, which might be slightly different, but the strategy doesn't know the future open price — it only knows the current close. In a real implementation, the backtester could recalculate SL/TP from the actual entry price, and the plan accounts for this (the backtester uses the actual entry ± 2% from the spec's section 5).

### Why multiple signals can share a candle (CLOSE + direction)

When the strategy detects a reversal (e.g., was LONG, now crossing to SHORT), it emits two signals at the **same candle index**: a CLOSE signal (to close the existing position) followed by the new direction signal (to open the opposite position). The engine processes them in order — CLOSE first, then the entry — both executing at candle i+1 open. This is intentional: it avoids losing a candle of execution between closing and reopening. However, only one directional signal (LONG/SHORT) can exist per candle, and contradictory same-direction duplicates are not allowed.

### Why the strategy "doesn't know about cash"

This is a critical architectural boundary. If the strategy knew about cash, it could make decisions like "I don't have enough money for this trade, so I'll skip this signal." But that couples the strategy to the portfolio logic, making it harder to test, harder to replace, and potentially introducing lookahead bias. Instead, the strategy always produces signals as if you have infinite money, and the backtester decides whether it can actually execute them based on available capital. Clean separation.

---

## Phase 3: Execution Modes — Explained

### What it is

A module that answers one question: "given a mid-price and a spread, what exact price do I buy or sell at?" The answer depends on which execution mode you're using.

### Why three modes exist

They serve different purposes:

**Mode A (Spread ON)** is the most realistic. It simulates actual market conditions where you always lose the spread on every trade. When you buy, you pay the **ask** (higher than mid). When you sell, you get the **bid** (lower than mid). This means the moment you enter a trade, you're already at a loss equal to the spread. This is how real brokers work. Use this mode to get the most honest performance estimate.

**Mode B (Spread OFF)** replaces the spread with a flat percentage fee. Some markets or brokers charge a commission instead of (or in addition to) a spread. The 0.1% fee on entry and exit means a round trip costs 0.2% of your position value. This is useful for testing strategies on markets where the spread model doesn't apply, or for simplification. You trade at the exact mid-price, but you pay a fixed fee from your cash.

**Mode C (Static Spread)** uses a constant spread that you define, ignoring whatever spread the data has. Why would you want this? Real spread data can be noisy — it might spike during volatile moments, be missing for some candles, or be unreliable. A static spread lets you test with a consistent cost assumption. For example, "assume spread is always 0.20" regardless of what the CSV says. The math works the same as Mode A, just with a fixed number instead of the per-candle value.

### Why this is a separate module

Because the rest of the backtester shouldn't care which mode is active. The portfolio module says "I want to buy at this candle" and the price resolver says "ok, that costs this much." If you want to add Mode D later (say, variable commission tiers), you only change this module.

### What "instant negative PnL on entry" means

Say mid-price is 100.00 and spread is 0.50. You buy (LONG) at 100.25 (ask). If you immediately sell, you sell at 99.75 (bid). You lost 0.50 per unit just by entering and exiting. This is realistic — in real trading, the moment you open a trade, you're down by the spread. The price has to move in your favor by at least the spread before you break even. A backtester that ignores this will show false profits.

---

## Phase 4: Capital Accounting — Explained

### What it is

This module tracks your money. How much cash you have, how many units you're holding, what your average entry price is, how much profit or loss you've realized, and what your total equity is.

### Why the strategy controls position sizing

Each signal carries a `size` field (0.0–1.0) that determines what fraction of available cash to allocate. The engine does **not** impose any cap — it executes exactly the size the strategy requests. For example, the MA Crossover strategy uses `size=1.0` (100% of available cash) for every signal. A future strategy might use `size=0.5` (50%) to be more conservative. This design means sizing decisions live inside the strategy (where domain knowledge is), not in the engine (which just executes). The engine's job is to be a faithful executor, not a risk manager.

### What position stacking means and why it matters

Stacking means: if you're already long and another LONG signal arrives, you don't ignore it — you buy more units with whatever cash is available (based on the signal's `size` field). Your position grows additively.

But stacking creates a complication: your two "layers" of position were opened at different prices. The first at 100, the second at 105. Your **average entry price** is now a weighted average:

```
avg = (100 * 90 + 105 * 9) / (90 + 9) = (9000 + 945) / 99 = 100.45
```

This matters for PnL calculation. When you close the entire position, your profit per unit is based on this average.

### Why we track both realized and unrealized PnL

**Unrealized PnL** is your profit or loss on positions you still hold. If you bought at 100 and the price is now 110, you have +10 per unit of unrealized profit. But it's not real yet — the price could drop back. It changes every candle.

**Realized PnL** is locked-in profit from trades you've completed (entered and exited). Once you sell those units at 110, the +10 per unit becomes realized. It never changes.

**Equity** = cash + position_notional + unrealized PnL. This is your total account value at any moment. `cash` is the free capital, `position_notional` (`abs(position_size) * avg_entry_price`) is the capital locked in the open position, and `unrealized PnL` is how much that position has gained or lost. It's what the equity curve plots. It goes up and down with the market even between trades.

### Why unrealized PnL uses bid for LONG and ask for SHORT

This is a conservative accounting choice. If you're long (you own something), the price you'd actually get if you sold right now is the **bid** (the lower price). So your unrealized PnL should reflect that — not the mid-price, which you can't actually sell at. Similarly, if you're short (you owe something), the price you'd actually pay to buy it back is the **ask** (the higher price). This prevents the equity curve from showing better numbers than you'd really get. The spec's PnL formulas confirm this explicitly:
- Long: `(current_bid - avg_entry) * size`
- Short: `(avg_entry - current_ask) * abs(size)`

### What close-and-reverse means

When the strategy detects a reversal (e.g., LONG→SHORT crossover), it explicitly emits **two signals at the same candle index**:
1. A `CLOSE` signal with `size=1.0` (close the entire long position)
2. A `SHORT` signal with `size=1.0` (open a new short with all available cash)

The engine processes them in order. It does NOT "net" them. The close settles the realized PnL from the long trade first, then the short trade begins with a clean slate and full capital. This explicit two-signal approach is clearer than having the engine implicitly close positions — the strategy is fully in control of what happens.

---

## Phase 5: SL/TP Engine — Explained

### What it is

The module that checks, every single candle, whether any open position has hit its stop loss or take profit level, and closes it if so.

### What stop loss and take profit are

**Stop loss (SL)** is a safety net. It says: "if the price moves against me by 2%, close the trade to prevent further loss." For a LONG position (you bought at 100), SL is at 98. For a SHORT position (you sold at 100), SL is at 102 (because price going UP is bad for shorts).

**Take profit (TP)** is the opposite. It says: "if the price moves in my favor by 2%, close the trade to lock in the profit." For a LONG at 100, TP is at 102. For a SHORT at 100, TP is at 98.

### Why "per position unit"

When you stack positions (buy once at 100, buy again at 105), each layer has its own SL/TP:
- Layer 1: entry=100, SL=98, TP=102
- Layer 2: entry=105, SL=102.9, TP=107.1

They're independent. Layer 1's SL might get hit while Layer 2 is still fine. In that case, only Layer 1 is closed. This is more realistic than having a single SL for the whole position, because each entry happened at a different price.

### Why intrabar checking matters

We're using 1-minute candles. Each candle tells us: the open price, the highest price during that minute, the lowest price during that minute, and the close price. But we don't know the exact path within that minute. Did it go up first then down? Or down first then up?

For SL/TP checking:
- LONG SL triggers if the **low** of the candle went at or below the SL level (the price dipped to our stop)
- LONG TP triggers if the **high** of the candle went at or above the TP level (the price reached our target)

But what if BOTH happen in the same candle? The candle's high was above TP and its low was below SL. This can happen with a very volatile minute. We don't know which happened first. The spec says: **assume worst case**. For a LONG, the worst case is that SL hit (you lose). For a SHORT, the worst case is also SL hit. This is deliberate pessimism — it prevents the backtest from showing unrealistically good results by always taking the profit. Any strategy that looks good even with this pessimistic rule is probably genuinely good.

### Why SL/TP execution uses spread

When your LONG stop loss hits at 98.0, you're selling your units. In spread mode, selling happens at the bid, which is `98.0 - spread/2`. So you actually get slightly less than the SL level. This is realistic — in real trading, hitting a stop loss at a specific level means a market order at that level, and market orders fill at the bid. This makes the backtest slightly worse, which is correct.

---

## Phase 6: Main Engine Loop — Explained

### What it is

This is the heart of the backtester. It's a `for` loop that iterates over every 1-minute candle and, at each step, runs the simulation logic in a specific order.

### Why the order matters so much

The spec emphasizes "strictly ordered" because changing the order produces different results. Here's why each step is in its position:

**Step 1: Update unrealized PnL.** Before doing anything, we mark-to-market. We calculate what our open position is worth right now at this candle's prices. This ensures our equity is accurate before any decisions are made.

**Step 2-3: Check and execute SL/TP.** This comes before processing new signals because stop losses are safety mechanisms — they must fire before anything else. Imagine a scenario: the price crashes, hitting your stop loss, and a new signal also arrives at this candle. The stop loss must close your position first (protecting you from the crash), and then the new signal is handled after. If you processed the new signal first, you might stack onto a losing position before the SL had a chance to close it.

**Step 3: Execute pending signal.** This is the signal that was emitted on the **previous** candle. The spec says execution happens at the open of the next candle (`i+1`). So when we're at candle `i`, we execute whatever signal was queued from candle `i-1`. We use `candle.open` as the execution price — this is the first available price at the start of this candle. This is critical for no-lookahead-bias: the strategy saw candle `i-1`'s data, decided to trade, and we execute at the very next available price.

**Step 4: Queue new signal.** If the strategy emitted a signal at this candle, we store it as `pending_signal`. It will not execute now — it will execute at the next iteration (Step 3 of the next candle). This is the "no same-candle execution" rule.

**Step 5: Record snapshot.** Save the current state (cash, position, equity, etc.) for this candle. This data is used later to build the equity curve, drawdown chart, and other reports.

### Why signal delay (i+1) is critical

This prevents **lookahead bias** — the most dangerous bug in backtesting. Lookahead bias is when the backtest uses information it shouldn't have yet.

Consider: the strategy sees candle `i`'s close at 105.0 and generates a LONG signal. If we executed at candle `i`'s open (100.0), we'd be buying at 100.0 based on information (the close at 105) that wasn't available at the open. In real life, at 100.0, you didn't know the close would be 105. By executing at candle `i+1`'s open, we ensure the decision was made with all of candle `i`'s data complete, and the first price we could realistically act on is the open of the next candle.

### What the `pending_signal` variable does

It's a one-slot buffer. It holds at most one signal waiting to be executed. When the strategy emits at candle 10, `pending_signal` gets set. On candle 11, the loop sees `pending_signal` is not None, executes the trade, and clears it. If a new signal arrives at candle 11 too, it goes into `pending_signal` for candle 12. There's never a backlog — only the most recent unexecuted signal exists.

### Why snapshots are needed

Without snapshots, you'd only have the final state of the portfolio — the end result. But you need the intermediate states to:
- Plot the equity curve (equity at every candle)
- Calculate max drawdown (need the full equity history to find the deepest drop)
- Calculate Sharpe ratio (need candle-by-candle returns)
- Calculate exposure time (need to know when position was non-zero)
- Debug issues (if something looks wrong, you can inspect any candle's state)

---

## Phase 7: Console Logging — Explained

### What it is

Text output to the terminal during the backtest run, printing what trades happened.

### Why it exists

Debugging and trust. When you run a backtest and see a final return of -15%, you want to know what happened. The log lets you trace through: "bought at 101.5, stop loss hit at 99.47, sold at 105.2..." If the log shows something that contradicts your expectations, you've found a bug. Without logging, the backtester is a black box — you get a number at the end but no idea how it got there.

### Why configurable verbosity

During development and debugging, you want to see everything (debug mode). During normal runs, you want to see just the trades (normal mode). During automated testing (running 1000 backtests with different parameters), you want silence (silent mode) — printing thousands of trade logs would be extremely slow and fill your terminal with megabytes of text.

### Why the timestamp in the log is the execution candle

The log says `[2024-01-15 09:31] BUY ...` — this is the candle where the trade actually happened (i+1), not the candle where the signal was generated (i). This matches what you'd see in a real broker's trade log: the timestamp of when the order was filled.

---

## Phase 8: Performance Metrics — Explained

### What it is

After the backtest finishes, this module takes the results (trade history, equity snapshots) and computes 9 numbers that summarize how the strategy performed.

### Why each metric matters

**Total Return** — the most basic measure. "I started with 10000, ended with 10350, so I made 3.5%." Simple but incomplete. It doesn't tell you how risky the journey was.

**Annualized Return** — normalizes the total return to a yearly rate. If your backtest covered 6 months and made 5%, the annualized return is roughly 10.25% (not exactly 10% because compounding). This lets you compare backtests of different lengths on equal footing.

The formula `(1 + total_return) ^ (252*390 / total_candles) - 1` works because:
- 252 = trading days per year
- 390 = minutes per trading day (6.5 hours)
- 252*390 = total 1-minute candles in a year
- The exponent scales the return to one year using compound growth

**Max Drawdown** — the worst peak-to-trough decline in equity during the backtest. If your equity went from 12000 to 10000 at some point, that's a drawdown of 16.7%. This tells you the worst pain you would have experienced. A strategy with 50% return but 40% max drawdown is much scarier than one with 30% return and 10% max drawdown.

**Sharpe Ratio** — measures return per unit of risk. It takes the average of your per-candle returns, divides by the standard deviation (volatility) of those returns, and annualizes it. A Sharpe above 1.0 is generally considered acceptable, above 2.0 is good, above 3.0 is exceptional. A Sharpe near 0 means the returns are basically noise. This is the single most important metric in quantitative finance.

**Win Rate** — percentage of trades that were profitable. A win rate of 40% sounds bad, but if your winning trades average +500 and your losing trades average -100, you're still making money. Win rate alone is misleading, which is why profit factor exists.

**Profit Factor** — total winning PnL divided by total losing PnL. If you won 5000 and lost 2000, profit factor is 2.5. Above 1.0 means you're net profitable. This combines win rate with win/loss size into a single number. It's more useful than win rate alone.

**Avg Trade** — total realized PnL divided by number of trades. Tells you the expected value of a single trade. If it's negative, the strategy loses money on average, regardless of occasional big wins.

**Total Trades** — raw count. Matters because: too few trades (say, 3) means your results aren't statistically significant. Too many trades (thousands) might mean excessive trading that gets killed by spread/fees in reality.

**Exposure Time** — percentage of candles where you held a position. 100% means you were always in the market. 10% means you were mostly in cash. A strategy with 50% return and 10% exposure is incredibly efficient — it captured those returns while being safe in cash 90% of the time.

---

## Phase 9: Visualization — Explained

### What it is

Four charts that visually show how the backtest went.

### Why these specific charts

**Equity Curve** — the single most important chart. It shows your portfolio value over time. A good strategy has a smooth upward-sloping equity curve. A bad one looks like a roller coaster or trends downward. You can instantly see: when did the strategy make money, when did it lose, how volatile was the ride.

**Drawdown Curve** — shows how far below its peak the equity was at any point. It's always zero or negative. Deep sustained drawdowns indicate dangerous periods. Even if the equity curve ends up nicely, a drawdown chart might reveal that at one point you were down 30% for three weeks straight — that's information you need to decide if you can stomach this strategy.

**Price Chart with Markers** — overlays your trades on the actual price movement. Green triangles where you bought, red triangles where you sold, X marks where stop losses hit, stars where take profits hit. This lets you visually see: "is the strategy buying at bottoms and selling at tops, or doing the opposite?" It's intuitive pattern recognition that numbers alone can't give you.

**Trade Distribution Histogram** — shows the distribution of individual trade PnL values. A good strategy has a bell curve shifted to the right (most trades are slightly positive, with a few big winners). A bad one is shifted left or has fat tails on the negative side (occasional catastrophic losses). This tells you about the character of the strategy beyond just the average.

---

## Phase 10: System Integration — Explained

### What it is

A single `run_backtest.py` script that connects everything and makes the whole system usable from the command line.

### Why a CLI runner

During development, you're testing individual modules. But eventually you need to run the whole thing as one command: "here's my data file, here's my configuration, go." The CLI runner is that glue. It:

1. Parses command-line arguments (which data file, which mode, how much starting capital, etc.)
2. Loads and prepares the data
3. Runs the strategy to get signals
4. Passes signals + data to the backtester
5. Runs the simulation
6. Prints the metrics table
7. Shows or saves the charts

### Why CLI arguments

So you can quickly experiment: "what happens if I change the fast MA from 10 to 20?" Instead of editing code, you just change the command:
```bash
python run_backtest.py --data data.csv --fast-ma 20 --slow-ma 50
```

This also enables automated parameter sweeps — a script that runs the backtest 100 times with different MA periods and collects the results.

### Why configuration file support

CLI arguments work for quick changes, but if you have 10+ parameters, typing them all every time is tedious. A config file (YAML or JSON) lets you save a full configuration and reuse it:
```yaml
data: data/SPY_1m.csv
mode: spread_on
capital: 50000
fast_ma: 10
slow_ma: 30
sl_pct: 0.02
tp_pct: 0.02
```

You can have different config files for different experiments and keep a record of what you tested.

---

## Phase 11: Validation & Hardening — Explained

### What it is

The final quality check. Making sure the system is correct, deterministic, and doesn't break on unusual inputs.

### Why determinism validation matters

"Deterministic" means: same input, same output, every single time. No randomness, no dependence on system time, no floating-point quirks causing different results on different machines. You run the backtest twice with identical data and parameters — the final equity, every trade, every snapshot must be exactly the same. If they're not, there's a bug (possibly a hidden source of randomness like unordered dict iteration or race condition).

### Why no-lookahead-bias audit

This is a manual code review where you trace every data access in the engine and verify that at candle `i`, you're only using data from candles 0 through `i`. Common mistakes:
- Using `close[i]` to decide an entry that happens at `open[i]` (the close wasn't known at the open)
- Using future signal information to avoid a bad trade
- Accidentally reading `i+1` data during SL/TP evaluation at candle `i`

This is the single most important correctness property. A backtest with lookahead bias is worthless — it shows performance that was only achievable by knowing the future.

### Why edge case testing

**Zero signals** — the simplest case. If the strategy produces nothing, the backtester should just pass through all candles doing nothing, and end with exactly the initial capital. If it doesn't, something's wrong with your initialization.

**Single trade** — one signal, one trade lifecycle. Easy to verify by hand. If this is wrong, nothing else can be right.

**All SL hits** — tests the losing path. Every trade should stop out, the account should gradually lose money, win rate should be 0%.

**Position stacking to exhaustion** — 4 LONG signals in a row, each with `size=1.0`. First uses 100% of 10000. With `size=1.0` the first trade consumes all available cash. Subsequent signals can only use whatever cash remains (which may be zero if 100% was allocated). Cash must never go negative. Tests that the capital constraint works correctly regardless of what size the strategy requests.

**Signal on last candle** — signal at the very last candle has no `i+1` to execute at. The engine must silently ignore it, not crash with an index-out-of-bounds error.

**Empty DataFrame** — zero candles. The engine should return immediately with the initial state, not crash.

### Why floating-point precision review

Computers don't store decimal numbers perfectly. `0.1 + 0.2` in Python equals `0.30000000000000004`, not `0.3`. Over thousands of trades, tiny rounding errors can accumulate. The plan specifies: no rounding during simulation (to avoid compounding rounding errors), round only in the final report for display. But you should still check that accumulated float errors don't cause nonsensical results like negative cash of -0.00000001 (which could trigger a bug if you check `cash < 0`).

---

## The Design Decisions Table — Explained

The spec explicitly demanded that certain things be stated, not assumed. Here's why each decision was made:

**Unrealized PnL uses bid for LONG, ask for SHORT** — because that's the price you'd actually get if you closed the position right now. Using mid would overstate your PnL by half the spread. This is the conservative, realistic choice.

**No rounding during simulation** — rounding after every operation (e.g., to 2 decimal places) introduces systematic error. Over 100,000 candles, rounding `0.005` up every time could add up to significant phantom profit or loss. Keep full float precision internally, round only for display.

**Execution order: unrealized PnL → SL/TP → signal → state update** — explained in Phase 6 above. SL/TP must fire before new signals because they're safety mechanisms.

**Stacking: additive size, weighted avg entry, independent SL/TP** — each stack layer is essentially a separate mini-trade within the same position. This is the clearest and most debuggable approach.

**Spread: entry pays spread, exit pays spread** — this is how real markets work. Buying costs ask, selling gets bid. Always worse than mid. Always costs you money.

**Fractional units allowed** — in simulation, there's no reason to restrict to whole units. If your allocation is 10000 and the price is 101.37, you buy 98.65 units. This is more accurate than rounding to 98 units, which would leave unexplained excess cash.

**Opposite signal: strategy emits CLOSE + new direction** — the strategy explicitly emits a CLOSE signal followed by the new direction at the same candle index. The engine processes CLOSE first (settling PnL), then opens the new position. This is clearer than implicit close-and-reverse because the strategy is fully in control.

**SL/TP exit price: at the SL/TP level ± spread** — not at candle open. If your SL was 98.0, you exit at 98.0 (minus spread for LONG). You don't wait until the next candle open, because stop losses are supposed to trigger immediately when the level is breached. Using the SL level as the exit price is the standard backtesting convention.

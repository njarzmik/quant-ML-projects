# Tests Explained — Historical Backtesting Engine

This document explains **what** every test does, **why** it exists, and **what failure would mean** for the system.

---

## Phase 1: Data Layer (`tests/test_data_loader.py`)

**Status:** Implemented
**Module under test:** `common/data_loader.py` (`load_csv`, `resample`)
**Why this phase first:** Every other component depends on correctly loaded and structured market data. If the data layer is broken, nothing downstream can be trusted.

### Fixture: `nas100_df`

Loads the real NAS100 1-minute test data from `data/nas100_m1_mid_test.csv` (~161k rows). This fixture is reused across all Phase 1 tests so they all operate on the same real market dataset.

---

### TestLoadCSV (7 tests)

These tests validate that the CSV loader produces a DataFrame that the rest of the system can safely consume. The backtester, strategy, and all metrics depend on the data having a specific shape and contract.

#### `test_columns_present`
- **What:** Loads a CSV and checks that the resulting DataFrame contains at least `open`, `high`, `low`, `close`, `spread`.
- **Why:** The entire engine hardcodes access to these five columns. If any column is missing or renamed, every downstream operation (`resample`, signal generation, SL/TP checks, price execution) will crash with a `KeyError`. This test is the first line of defense against schema drift.
- **Failure means:** The loader is silently dropping or renaming columns.

#### `test_index_is_datetime`
- **What:** Verifies the loaded DataFrame's index is a `pd.DatetimeIndex`.
- **Why:** Resampling (`resample()`) uses `df.resample(timeframe)` which **requires** a `DatetimeIndex`. The engine loop iterates candles in chronological order. Signal timestamps reference index positions. If the index is a plain integer or string, resampling will crash, and the entire time-ordering assumption of the backtester breaks.
- **Failure means:** The CSV parser didn't convert the timestamp column to datetime, so resampling and chronological iteration will fail.

#### `test_no_missing_values`
- **What:** Asserts zero NaN values anywhere in the loaded DataFrame.
- **Why:** NaN values propagate silently through arithmetic. A single NaN spread would make entry/exit price calculations produce NaN, which would corrupt portfolio accounting. A NaN high/low would make SL/TP checks meaningless (comparisons with NaN return False). The loader must reject dirty data upfront rather than letting corruption flow through 10 modules.
- **Failure means:** The loader allows NaN-contaminated data through, leading to silent calculation errors everywhere.

#### `test_ohlc_sanity`
- **What:** Checks that for every row: `high >= max(open, close)` and `low <= min(open, close)`.
- **Why:** This is a fundamental property of candlestick data. The high is the highest price reached during the candle; it must be at least as high as both the open and close. Same logic for low. If this invariant is violated, the data is malformed (columns are swapped, data is corrupted, or the source is wrong). The SL/TP engine checks whether `low <= SL` or `high >= TP` — if high/low values are wrong, SL/TP triggers become unpredictable.
- **Failure means:** The data source is providing impossible candles, and all intrabar execution logic becomes unreliable.

#### `test_spread_positive`
- **What:** Asserts all spread values are strictly greater than zero.
- **Why:** Spread represents the bid-ask gap (`ask - bid`). In real markets, spread is always positive. A zero spread would mean no transaction cost in Mode A (unrealistic). A negative spread would invert bid/ask prices, causing LONG entries to be cheaper than exits (free money — a simulation bug). The spec explicitly requires spread to represent a real cost.
- **Failure means:** The data contains zero or negative spreads, which would make Mode A execution unrealistic or produce inverted bid/ask prices.

#### `test_reject_missing_column`
- **What:** Creates a CSV without the `spread` column and verifies that `load_csv()` raises an exception.
- **Why:** This is the negative counterpart to `test_columns_present`. The system must **fail loudly** when given incomplete data, rather than silently proceeding with missing columns. Without this test, someone could accidentally load a 4-column OHLC file (no spread) and get `KeyError` deep inside the engine instead of a clear error at load time. Fail-fast prevents debugging nightmares.
- **Failure means:** The loader silently accepts incomplete data, deferring the crash to some random point deep in the engine.

#### `test_row_count`
- **What:** Verifies the real NAS100 dataset has more than 100,000 rows.
- **Why:** This is a sanity check that the test fixture is loading the full real dataset, not a truncated or empty file. If the CSV is corrupted, partially downloaded, or replaced with a smaller file, this test catches it immediately. All other tests depend on having a substantial dataset.
- **Failure means:** The test data file is missing, corrupted, or has been replaced with a smaller file.

---

### TestResample (7 tests)

These tests validate the OHLC resampling logic. The strategy module needs multi-timeframe data (5m, 15m, 30m, 60m) built from the base 1-minute candles. If resampling is wrong, the strategy sees incorrect prices and generates wrong signals.

#### `test_5m_candle_count`
- **What:** 5-minute resampling of the full NAS100 dataset reduces row count by roughly 5x (ratio between 4.5 and 5.5).
- **Why:** This validates the basic grouping logic on real data. If the ratio is wrong, candles are being merged incorrectly (overlapping windows, missing data, off-by-one errors). A wrong count means the strategy would see a different number of candles than expected, shifting all indicator calculations.
- **Failure means:** The resampling window boundaries are wrong — candles are being split or merged incorrectly.

#### `test_5m_open_is_first`
- **What:** The 5-minute candle's `open` must equal the first 1-minute candle's `open` in that window.
- **Why:** By definition, a resampled candle's open is the price at which the period began — the open of the first sub-candle. If this is wrong (e.g., using the average or the last open), every MA calculation on the resampled timeframe will be shifted, producing wrong crossover signals.
- **Failure means:** The aggregation rule for `open` is wrong (using `last`, `mean`, or `max` instead of `first`).

#### `test_5m_high_is_max`
- **What:** The 5-minute candle's `high` must equal the maximum of all five 1-minute highs.
- **Why:** The high of a resampled candle represents the highest price reached in that entire period. If it uses `first` or `mean` instead of `max`, the candle would understate the true range. This matters for SL/TP: if the 5m high is wrong, strategies using higher-timeframe resistance levels would set incorrect TP targets.
- **Failure means:** The aggregation rule for `high` is wrong — understating the actual price range.

#### `test_5m_low_is_min`
- **What:** The 5-minute candle's `low` must equal the minimum of all five 1-minute lows.
- **Why:** Mirror of the high test. The low represents the lowest price reached. If wrong, support-level calculations and SL placement on higher timeframes would be incorrect. Using `mean` or `last` would overstate the low, hiding how far price actually dipped.
- **Failure means:** The aggregation rule for `low` is wrong — overstating the actual price floor.

#### `test_5m_close_is_last`
- **What:** The 5-minute candle's `close` must equal the last 1-minute candle's `close` in that window.
- **Why:** The close of a resampled candle is the final price of the period. Moving averages are calculated on close prices. If the resampled close uses `first` or `mean`, every MA value on the higher timeframe is wrong, and crossover signals fire at the wrong moments.
- **Failure means:** The aggregation rule for `close` is wrong — MA calculations on resampled data will be incorrect.

#### `test_5m_spread_is_mean`
- **What:** The 5-minute candle's `spread` must equal the average of all five 1-minute spreads.
- **Why:** Spread is aggregated as `mean` because it represents the average transaction cost over the period. Using `max` would overstate costs; using `min` would understate them; using `first` or `last` would be arbitrary. The mean is the most representative value for cost estimation over a window.
- **Failure means:** The spread aggregation is wrong, leading to biased transaction cost estimates on higher timeframes.

#### `test_15m_30m_60m_produce_output`
- **What:** Resampling the full NAS100 dataset to 15m, 30m, and 60m doesn't crash and produces at least 1 candle each.
- **Why:** This is a smoke test for larger timeframes. The function must not crash, return empty DataFrames, or raise errors. The strategy module calls `resample()` for all these timeframes during initialization. If any of them fail, multi-timeframe analysis becomes impossible.
- **Failure means:** The resampling function doesn't handle larger timeframe intervals correctly.

---

## Phase 2: Signal Generator (`tests/test_strategy.py`)

**Status:** Implemented
**Module under test:** `strategies/ma_crossover.py` (`MACrossoverStrategy`)
**Why this phase:** The strategy is the brain of the system — it decides when to buy and sell. If signals are wrong, the backtest results are meaningless regardless of how perfect the engine is.

### Fixtures

- **`trending_up_df`:** 40 candles — 20 flat at 100.0, then 20 rising by 0.5 each. With `fast_ma=5, slow_ma=20`, this guarantees exactly one clear crossover where the fast MA crosses above the slow MA (first entry, no prior position to close).
- **`crossover_then_crossunder_df`:** 70 candles — 25 flat (enough for slow MA to stabilize), then 15 rising, then 15 falling, then 15 flat. Guarantees both a crossover (LONG) and a crossunder (SHORT), with the crossunder triggering a CLOSE+SHORT reversal pair.

---

#### `test_single_long_signal`
- **What:** An uptrending price series produces at least one LONG signal.
- **Why:** This is the most fundamental test of the MA crossover strategy. If a clear uptrend (flat then rising prices) doesn't produce a LONG signal, the crossover detection is completely broken. This is the "does the strategy do anything at all" test.
- **Failure means:** The crossover detection logic is fundamentally broken — the strategy can't detect a basic trend change.

#### `test_crossunder_produces_short`
- **What:** A price series that goes up then down produces both a LONG and a SHORT signal, with the LONG appearing first.
- **Why:** The strategy must detect both directions. A system that only goes long misses half the market. The ordering check (LONG before SHORT) verifies that the strategy correctly identifies the sequence of events — first the uptrend crossover, then the downtrend crossunder.
- **Failure means:** Either the SHORT signal detection is broken, or the signals are emitted in the wrong order (the strategy sees the future).

#### `test_reversal_emits_close_before_direction`
- **What:** When the strategy reverses from LONG to SHORT, a CLOSE signal appears immediately before the SHORT signal in the list.
- **Why:** The strategy must explicitly close the existing position before opening the opposite. The engine processes signals in list order, so CLOSE must come first. Without this, the engine would try to open a SHORT while still LONG — conflicting positions.
- **Failure means:** The strategy doesn't emit CLOSE on reversal, or emits it in the wrong order.

#### `test_close_and_direction_share_candle_index`
- **What:** Every CLOSE signal has the same `timestamp_index` as the directional signal that follows it.
- **Why:** Both signals originate from the same crossover event. They execute together at candle i+1 open. If they had different indices, there would be a candle gap between closing and reopening, losing execution time.
- **Failure means:** CLOSE and direction signals are at different candle indices — unnecessary execution delay.

#### `test_first_entry_has_no_close`
- **What:** The very first signal emitted is a directional signal (LONG or SHORT), not a CLOSE.
- **Why:** On the first crossover, there's no existing position to close. Emitting a CLOSE when flat would be meaningless and could confuse the engine.
- **Failure means:** The strategy emits a spurious CLOSE at the start when no position exists.

#### `test_all_signals_have_size`
- **What:** Every signal (CLOSE, LONG, SHORT) carries `size=1.0`.
- **Why:** The MA Crossover strategy always uses 100% of available cash. The `size` field is how the strategy communicates its sizing decision to the engine. If any signal has a different size, the allocation would be wrong.
- **Failure means:** The size field is not being set correctly on all signals.

#### `test_close_signal_has_zero_sl_tp`
- **What:** CLOSE signals have `stop_loss_level=0.0` and `take_profit_level=0.0`.
- **Why:** CLOSE signals just close a position — they don't open one, so SL/TP levels are meaningless. Setting them to 0.0 makes this explicit and prevents the engine from trying to register SL/TP for a closing action.
- **Failure means:** CLOSE signals carry SL/TP values that could confuse the engine.

#### `test_sl_tp_levels_long`
- **What:** For a LONG signal, SL = close * 0.98 and TP = close * 1.02 (exactly 2% from the close price at the signal candle).
- **Why:** The spec mandates SL/TP at +/-2% of entry. If these levels are calculated wrong, the risk/reward ratio is distorted. The exact 2% value must match the spec.
- **Failure means:** The SL/TP calculation formula is wrong — the strategy is producing positions with incorrect risk parameters.

#### `test_no_signal_in_flat_market`
- **What:** 50 candles of identical prices (all OHLC = 100.0) produce zero signals.
- **Why:** When prices are perfectly flat, both MAs equal the close price and never cross. Generating signals in a flat market would mean false positives.
- **Failure means:** The strategy generates phantom signals in trendless markets — a critical false-positive bug.

#### `test_signal_indices_within_bounds`
- **What:** Every signal's `timestamp_index` is a valid position (0 to len(df)-1) in the input DataFrame.
- **Why:** An out-of-bounds index would cause an `IndexError` when the engine tries to look up the candle data at that index.
- **Failure means:** The strategy references candles that don't exist, causing crashes in the engine.

#### `test_strategy_has_no_side_effects`
- **What:** Running `strategy.generate()` twice on the same data produces identical signals (same indices, types, and sizes).
- **Why:** The strategy must be a pure function — deterministic and side-effect-free. The strategy tracks `last_direction` internally, but this is reset on each call. If internal state leaked between calls, the second run would produce different results.
- **Failure means:** The strategy mutates internal state between runs, violating the determinism requirement.

---

## Phase 3: Execution Modes (`tests/test_execution_modes.py`)

**Status:** Planned
**Module under test:** `backtester/execution_modes.py` (`resolve_entry_price`, `resolve_exit_price`, `calculate_fee`)
**Why this phase:** The execution mode determines how trades are priced. A bug here directly corrupts every PnL calculation in the system.

---

### TestModeA_SpreadOn (7 tests)

Mode A is the "realistic" execution mode — it simulates real-market bid/ask dynamics where entering a trade always costs half the spread.

#### `test_long_entry`
- **What:** LONG entry at mid=100.0, spread=0.50 produces price 100.25 (mid + spread/2).
- **Why:** Going long means buying at the ask price. Ask = mid + spread/2. This is how real markets work: you always buy at the higher price. If this formula is wrong (e.g., subtracting instead of adding), longs would enter at artificially good prices, inflating backtest results.
- **Failure means:** The ask price calculation is wrong — backtest results are unrealistically optimistic for long trades.

#### `test_long_exit`
- **What:** LONG exit at mid=100.0, spread=0.50 produces price 99.75 (mid - spread/2).
- **Why:** Closing a long means selling at the bid price. Bid = mid - spread/2. Combined with the entry at ask, this creates the realistic "buy high, sell low" cost of the spread. If exit uses mid instead of bid, the backtest understates transaction costs.
- **Failure means:** The bid price calculation is wrong — the spread cost of closing positions is not properly modeled.

#### `test_short_entry`
- **What:** SHORT entry at mid=100.0, spread=0.50 produces price 99.75 (mid - spread/2).
- **Why:** Going short means selling at the bid price. The short entry is the mirror of long entry. If this uses the ask price, shorts would enter at worse prices than reality.
- **Failure means:** Short entry pricing is inverted — shorts are either too cheap or too expensive to open.

#### `test_short_exit`
- **What:** SHORT exit at mid=100.0, spread=0.50 produces price 100.25 (mid + spread/2).
- **Why:** Closing a short means buying at the ask price. This is the mirror of long exit. The same spread cost applies in the opposite direction.
- **Failure means:** Short exit pricing is wrong — closing short positions doesn't properly account for the spread.

#### `test_zero_spread`
- **What:** With spread=0.0, both entry and exit equal mid (100.0).
- **Why:** Zero spread is a boundary case. If the formula has a bug that only manifests with non-zero spread (e.g., division by zero, or a hardcoded minimum spread), this test catches it. Zero spread should degenerate to simple mid-price execution.
- **Failure means:** The formula doesn't handle zero spread correctly — there's a division error or hardcoded offset.

#### `test_no_fee`
- **What:** Mode A has no fee (fee = 0.0 regardless of position size).
- **Why:** Mode A models costs via the spread, not via fees. Adding a fee on top of the spread would double-count transaction costs. This test ensures Mode A and Mode B cost models are kept separate and don't leak into each other.
- **Failure means:** Mode A is incorrectly charging fees on top of spread — double-counting transaction costs.

#### `test_instant_loss_on_entry`
- **What:** Buying and immediately selling at the same mid price results in a loss exactly equal to the spread.
- **Why:** This is the key economic property of Mode A: entering and exiting at the same price always costs one full spread. This test verifies the spread cost model end-to-end. If the loss is more or less than the spread, the bid/ask formulas are inconsistent with each other.
- **Failure means:** The entry and exit formulas are inconsistent — the round-trip cost doesn't equal the spread.

---

### TestModeB_SpreadOff (4 tests)

Mode B ignores the bid/ask spread and instead charges a flat 0.1% fee per transaction. This models a simplified fee-based broker.

#### `test_long_entry_at_mid`
- **What:** LONG entry in Mode B equals the mid price exactly (no spread adjustment).
- **Why:** Mode B's defining feature is that it ignores the spread. If entry uses ask instead of mid, Mode B is behaving like Mode A, defeating its purpose. Mode B exists to test strategy performance without spread impact.
- **Failure means:** Mode B is applying spread adjustments when it shouldn't — it's not actually "spread off."

#### `test_long_exit_at_mid`
- **What:** LONG exit in Mode B equals the mid price exactly.
- **Why:** Same rationale as entry. Both sides of the trade must use mid price for Mode B to be a true "no spread" mode.
- **Failure means:** Mode B exit is still using bid/ask pricing.

#### `test_fee_calculation`
- **What:** Fee on a 10,000 position value = 10.0 (0.1%).
- **Why:** The 0.1% fee rate is specified in the spec. This test pins the exact fee formula: `fee = position_value * 0.001`. If the rate is wrong (e.g., 1% instead of 0.1%), all Mode B backtests will be dramatically off.
- **Failure means:** The fee rate is wrong — all Mode B cost calculations are incorrect.

#### `test_fee_on_small_position`
- **What:** Fee on a 500.0 position = 0.50.
- **Why:** Tests the fee calculation with a smaller position to verify it scales linearly. This catches bugs like minimum fee floors, rounding errors, or fixed fees that don't scale with position size.
- **Failure means:** The fee doesn't scale linearly with position size — there's a rounding or minimum-fee bug.

---

### TestModeC_StaticSpread (2 tests)

Mode C uses a user-defined constant spread instead of the per-candle spread from the dataset. Useful for testing "what if spread was always X?"

#### `test_uses_custom_spread`
- **What:** With static spread = 0.30 and LONG entry, price is 100.15 (mid + 0.30/2), regardless of the dataset's actual spread.
- **Why:** Mode C's defining feature is ignoring the dataset spread and using a fixed value. If it accidentally reads the candle's spread column, the mode is broken. This test passes a different dataset spread to verify it's ignored.
- **Failure means:** Mode C is reading the dataset spread instead of the configured static value.

#### `test_no_fee`
- **What:** Mode C has no fee (like Mode A).
- **Why:** Mode C uses spread-based costs (just with a static spread), not fee-based costs. Charging fees would mix two cost models. This test ensures Mode C behaves like "Mode A but with a custom spread."
- **Failure means:** Mode C is charging fees — mixing cost models incorrectly.

---

## Phase 4: Capital Accounting (`tests/test_portfolio.py`)

**Status:** Planned
**Module under test:** `backtester/portfolio.py` (`Portfolio`)
**Why this phase:** The portfolio tracks cash, position size, and equity. If accounting is wrong, reported PnL is wrong, and the backtest results are fiction.

---

### TestPositionOpening (4 tests)

#### `test_initial_state`
- **What:** A fresh portfolio has cash=10000, position_size=0, realized_pnl=0, equity=10000.
- **Why:** The initial state is the baseline for all calculations. If any initial value is wrong (e.g., equity starts at 0 instead of initial_capital), every subsequent equity calculation will be offset. This is the "known starting point" test.
- **Failure means:** The portfolio constructor doesn't initialize state correctly — all subsequent calculations start from the wrong baseline.

#### `test_long_entry_deducts_cash`
- **What:** Opening a LONG position with `size=1.0` reduces cash to near zero (100% allocated).
- **Why:** When you buy, cash goes down and position goes up. If cash isn't deducted, the system thinks it has infinite money and can open unlimited positions. The `size` field from the signal determines the allocation percentage — the engine has no cap of its own.
- **Failure means:** Cash isn't being deducted on position open — the portfolio allows infinite trading.

#### `test_size_controls_allocation`
- **What:** With spread=0, opening a position at price 100.0 with `size=1.0` uses all cash. With `size=0.5`, only half the cash is used.
- **Why:** The strategy controls sizing via `signal.size`. The engine must faithfully allocate exactly `cash * signal.size`. If the engine ignores the size field or applies its own cap, the strategy loses control of position sizing.
- **Failure means:** The engine doesn't respect the signal's size field — strategy sizing decisions are ignored.

#### `test_cannot_exceed_cash`
- **What:** Opening a position with `size=1.0` uses all cash. A second signal can only use whatever cash remains (which may be zero).
- **Why:** Even with `size=1.0`, the engine must not allocate more than available cash. If the first trade used everything, the second trade gets nothing. Cash must never go negative (no leverage).
- **Failure means:** The portfolio allocates more than available cash — implicit leverage.

---

### TestPositionStacking (2 tests)

#### `test_stacking_increases_size`
- **What:** Two consecutive LONG opens produce a position larger than one open alone.
- **Why:** The spec allows position stacking (adding to an existing position). This test verifies that the second open actually adds to the position rather than replacing it or being ignored.
- **Failure means:** The portfolio replaces the position on the second signal instead of adding to it.

#### `test_weighted_average_entry`
- **What:** After opening at 100.0 (90 units) then at 200.0 (4.5 units), the average entry price is the weighted average: (100*90 + 200*4.5) / 94.5.
- **Why:** When stacking, the average entry must be recalculated as a weighted average. Using simple average (150.0) would be wrong. Using only the latest entry (200.0) would be wrong. The PnL calculation depends on `avg_entry_price` — if it's wrong, realized and unrealized PnL are both wrong.
- **Failure means:** The average entry calculation is wrong — PnL for the stacked position will be miscalculated.

---

### TestPositionClosing (4 tests)

#### `test_close_credits_cash`
- **What:** Opening at 100.0 and closing at 110.0 produces cash = 10900 (initial 10000 + profit of 900).
- **Why:** When a position is closed, the proceeds must be added back to cash. The profit is `(exit - entry) * units = (110 - 100) * 90 = 900`. If cash isn't credited, the portfolio loses track of money.
- **Failure means:** Cash isn't being credited on position close — money disappears from the system.

#### `test_losing_trade_reduces_cash`
- **What:** Opening at 100.0 and closing at 90.0 produces cash = 9100 (initial 10000 - loss of 900).
- **Why:** Losses must reduce cash symmetrically to how profits increase it. If only winning trades affect cash, the portfolio is always-profitable (a critical bug). This test ensures negative PnL is properly accounted for.
- **Failure means:** Losses aren't being deducted — the portfolio is immune to losing trades.

#### `test_realized_pnl_tracked`
- **What:** After a profitable close, `realized_pnl` equals the profit (900.0).
- **Why:** `realized_pnl` is a separate accumulator used for reporting metrics. It must match the actual profit/loss. If it only tracks the last trade (instead of accumulating), the total return metric will be wrong. If it's always zero, the win rate and profit factor can't be calculated.
- **Failure means:** Realized PnL isn't being tracked — performance metrics can't be computed.

#### `test_close_resets_position`
- **What:** After closing, `position_size` = 0 and `avg_entry_price` = 0.
- **Why:** A closed position must fully reset. If `position_size` isn't zeroed, the engine thinks there's still an open position and might try to check SL/TP on a ghost position. If `avg_entry_price` isn't zeroed, the next position open might use a stale average.
- **Failure means:** State from the previous position leaks into the next one — ghost positions or wrong averages.

---

### TestCloseAndReverse (1 test)

#### `test_long_to_short`
- **What:** After opening LONG, closing, then opening SHORT, `position_size` is negative.
- **Why:** The spec requires that when a SHORT signal arrives while LONG, the engine closes the long and opens a short. The negative position_size convention (positive = long, negative = short) must be maintained. If reversals don't work, the system can only go long or only go short.
- **Failure means:** The portfolio can't handle direction reversals — the close-and-reverse mechanism is broken.

---

### TestUnrealizedPnL (5 tests)

#### `test_long_unrealized_profit`
- **What:** LONG position at 100.0, current mid at 110.0, shows positive unrealized PnL.
- **Why:** Unrealized PnL represents paper profit. It's used to calculate equity (cash + position_notional + unrealized) and is displayed in the equity curve. If it's always zero, the equity curve is flat even when positions are profitable.
- **Failure means:** Unrealized PnL calculation is broken — the equity curve doesn't reflect open position value.

#### `test_long_unrealized_uses_bid`
- **What:** LONG at entry 100.25 (ask), current mid=100.0, spread=0.50 (bid=99.75) shows negative unrealized PnL.
- **Why:** The spec explicitly requires unrealized PnL for longs to use the bid price (what you'd get if you sold now). Using mid instead of bid would overstate the position value by half the spread. This test catches the common mistake of using mid price for unrealized calculations.
- **Failure means:** Unrealized PnL uses mid instead of bid — overstating open position value by half the spread.

#### `test_equity_is_total_account_value`
- **What:** `equity == cash + position_notional + unrealized_pnl` always holds. With a LONG at 100 (90 units, cash=1000), mid=110: equity = 1000 + 9000 + 900 = 10900.
- **Why:** This is the fundamental accounting identity. Equity is the total account value: free cash + capital locked in the position + unrealized gains/losses. If this identity breaks, the reporting is inconsistent.
- **Failure means:** The accounting identity is violated — the portfolio's internal state is inconsistent.

#### `test_equity_after_open_reflects_spread_cost`
- **What:** Opening a LONG with spread immediately reduces equity by approximately the spread cost (not by the full allocation).
- **Why:** The old formula `cash + unrealized_pnl` produced negative equity (-49.88) after opening a 10000 position. The correct equity should be ~9950 (initial capital minus the spread cost). This test ensures equity represents the true account value.
- **Failure means:** Equity doesn't account for capital locked in positions — showing nonsensical negative values.

#### `test_equity_unchanged_when_flat`
- **What:** When no position is open, equity equals cash (position_notional is 0, unrealized is 0).
- **Why:** Verifies the formula degenerates correctly to just `cash` when flat.
- **Failure means:** Equity formula breaks for the simplest case (no position).

---

## Phase 5: SL/TP Engine (`tests/test_sl_tp.py`)

**Status:** Planned
**Module under test:** `backtester/sl_tp.py` (`check_sl_tp`, `PositionUnit`)
**Why this phase:** Stop-loss and take-profit are the primary risk management tools. If SL doesn't fire when it should, losses run unchecked. If TP doesn't fire, profits are left on the table.

---

### TestLongSLTP (6 tests)

#### `test_sl_triggered`
- **What:** LONG position at 100.0 with SL=98.0. Candle low=97.5 (below SL). Result: SL triggered.
- **Why:** When the candle's low penetrates the SL level, the stop loss must fire. This is the most basic SL functionality — if a candle's low is below SL, the position should be closed at a loss. Without this working, there is no downside protection.
- **Failure means:** Stop losses don't fire — positions can lose unlimited money.

#### `test_tp_triggered`
- **What:** LONG position at 100.0 with TP=102.0. Candle high=102.5 (above TP). Result: TP triggered.
- **Why:** When the candle's high reaches the TP level, profits should be taken. This locks in gains automatically. Without TP, profitable positions can reverse before being closed.
- **Failure means:** Take profits don't fire — the system doesn't lock in gains.

#### `test_both_triggered_worst_case`
- **What:** Candle with low=97.0 (hits SL=98.0) AND high=103.0 (hits TP=102.0). Result: SL fires (not TP).
- **Why:** This is the critical "worst-case assumption" from the spec. When a single candle spans both SL and TP, we don't know which was hit first (we only have OHLC, not tick data). The spec mandates assuming the worst: SL fires. For longs, the worst case is a loss (SL). This prevents the backtest from having an optimistic bias by always assuming TP fires first.
- **Failure means:** The backtester assumes the best case when both trigger — optimistic bias in results, overstating strategy performance.

#### `test_neither_triggered`
- **What:** Candle stays within the SL-TP range (low=99.0 > SL=98.0, high=101.0 < TP=102.0). Result: no trigger.
- **Why:** When price doesn't reach either level, the position must stay open. If SL/TP fires erroneously on non-touching candles, positions would be closed prematurely for no reason.
- **Failure means:** SL/TP fires when it shouldn't — positions are closed prematurely on normal price action.

#### `test_exact_sl_boundary`
- **What:** Candle low equals SL exactly (low=98.0, SL=98.0). Result: SL triggered.
- **Why:** The spec uses `<=` for SL check. The boundary case (exact touch) must trigger the SL. Using strict `<` instead of `<=` would miss this case, meaning a candle that perfectly touches SL would leave the position open — a subtle but real bug.
- **Failure means:** The comparison uses strict `<` instead of `<=` — exact SL touches are missed.

#### `test_exact_tp_boundary`
- **What:** Candle high equals TP exactly (high=102.0, TP=102.0). Result: TP triggered.
- **Why:** Same boundary logic as SL. The spec uses `>=` for TP. An exact touch at the TP level must trigger profit-taking. Missing this means the position stays open when it should have been closed at target.
- **Failure means:** The comparison uses strict `>` instead of `>=` — exact TP touches are missed.

---

### TestShortSLTP (3 tests)

#### `test_sl_triggered` (SHORT)
- **What:** SHORT position at 100.0 with SL=102.0. Candle high=102.5 (above SL). Result: SL triggered.
- **Why:** For shorts, SL is ABOVE the entry (price going against you = going up). The check is `high >= SL` (not `low <= SL` like for longs). If the long SL logic is reused without inverting, shorts will never stop out.
- **Failure means:** Short SL checks use the wrong comparison direction — shorts have no downside protection.

#### `test_tp_triggered` (SHORT)
- **What:** SHORT position at 100.0 with TP=98.0. Candle low=97.5 (below TP). Result: TP triggered.
- **Why:** For shorts, TP is BELOW the entry (price going in your favor = going down). The check is `low <= TP`. If the long TP logic is reused, shorts would need price to go UP to take profit — completely inverted.
- **Failure means:** Short TP checks use the wrong direction — shorts can never take profit.

#### `test_both_triggered_worst_case_short`
- **What:** Both SL and TP touched for a SHORT position. Result: SL fires (worst case for short).
- **Why:** Same worst-case principle as for longs, but for shorts: the worst case is SL (a loss), not TP (a profit). This ensures short positions also get the conservative treatment, preventing optimistic bias for short trades.
- **Failure means:** Short positions get optimistic treatment when both levels are touched — asymmetric bias.

---

### TestSLTPWithSpread (2 tests)

#### `test_long_sl_exit_at_bid`
- **What:** LONG SL exit with spread=0.50 produces exit price = 97.75 (SL level 98.0 - spread/2 = 97.75).
- **Why:** When closing a long (selling), you sell at the bid price. The SL level is where mid-price is, but actual execution happens at bid = SL - spread/2. Ignoring spread on SL exits would understate losses — in reality, the spread makes SL exits slightly worse than the SL level itself.
- **Failure means:** SL exits ignore the spread — actual execution price is better than it would be in reality.

#### `test_short_sl_exit_at_ask`
- **What:** SHORT SL exit with spread=0.50 produces exit price = 102.25 (SL level 102.0 + spread/2 = 102.25).
- **Why:** When closing a short (buying), you buy at the ask price. The ask is SL + spread/2. For shorts, SL exit is also made worse by the spread — you buy back at a higher price than the SL level. This ensures spread costs are properly modeled even on stop-loss exits.
- **Failure means:** Short SL exits ignore the spread — losses are understated.

---

## Phase 6: Main Engine Loop (`tests/test_engine.py`)

**Status:** Planned
**Module under test:** `backtester/engine.py` (`BacktestEngine`)
**Why this phase:** The engine orchestrates all components (signals, execution, portfolio, SL/TP). This is where timing bugs, ordering bugs, and integration issues surface.

---

### TestSignalDelay (2 tests)

#### `test_signal_executes_next_candle`
- **What:** Signal at candle 0 executes at candle 1's open price (101.0, not 100.0 or 100.5).
- **Why:** The spec's most critical timing rule: signals execute at candle i+1's open, NOT at the signal candle's price. This prevents look-ahead bias — in live trading, you can't act on information from a candle before it closes. If the engine executes at candle 0's close (100.5), the backtest assumes perfect timing that's impossible in reality.
- **Failure means:** The engine has look-ahead bias — trades execute at prices that wouldn't be available in live trading, inflating results.

#### `test_signal_on_last_candle_not_executed`
- **What:** Signal on candle 4 (the last one) produces zero trades.
- **Why:** There is no candle 5 to execute at. If the engine tries to execute, it will either crash (index out of bounds) or use the last candle's close (look-ahead bias). The correct behavior is to silently ignore the signal.
- **Failure means:** The engine crashes on signals at the end of data, or executes at an impossible price.

---

### TestExecutionOrder (1 test)

#### `test_sl_checked_before_signal`
- **What:** SL is evaluated before new signals on the same candle.
- **Why:** The engine loop order matters: first check SL/TP on existing positions, then process new signals. If a new signal is processed first (opening a new position), and then SL fires on the old position, the accounting gets confused — two positions might exist simultaneously when only one should.
- **Failure means:** The engine processes signals before checking SL/TP — race conditions between position closing and opening.

---

### TestNoTradeScenario (1 test)

#### `test_empty_signals`
- **What:** Zero signals produce zero trades and equity remains at initial capital.
- **Why:** The engine must handle the no-signal case gracefully. If it crashes on empty signal lists, strategies that produce no signals (flat markets) can't be tested. The equity must stay at exactly the initial capital — not drift, not become NaN, not become zero.
- **Failure means:** The engine can't handle strategies that produce no signals.

---

### TestCloseAndReverse (1 test)

#### `test_long_then_short_reversal`
- **What:** LONG signal then SHORT signal produces a closed LONG trade and a new SHORT position.
- **Why:** When a SHORT signal arrives while LONG, the engine must: (1) close the long, (2) open the short. If it tries to open a short without closing the long, the portfolio would have conflicting positions. This tests the full reversal flow through the engine.
- **Failure means:** The engine can't handle direction changes — positions accumulate instead of reversing.

---

### TestClose (1 test)

#### `test_close_signal`
- **What:** A `CLOSE` signal with `size=1.0` closes the entire position, resulting in `position_size = 0`.
- **Why:** The CLOSE signal type closes a position (fully or partially based on `size`). With `size=1.0`, it's a full close. The strategy emits CLOSE explicitly before reversals. If CLOSE doesn't work, there's no way to explicitly exit a position.
- **Failure means:** The `CLOSE` signal type is not properly handled by the engine.

---

### TestDeterminism (1 test)

#### `test_same_result_twice`
- **What:** Two identical engine runs produce byte-identical results (same equity, same trades, same entry/exit prices).
- **Why:** The spec demands determinism — same input must always produce the same output. If there's hidden randomness (random seed, dict ordering, floating-point non-determinism), backtesting results become unreliable and unreproducible. This is foundational for trust in the system.
- **Failure means:** The engine has non-deterministic behavior — results change between runs with the same input.

---

### TestEquitySnapshot (1 test)

#### `test_snapshots_recorded_every_candle`
- **What:** The number of equity snapshots equals the number of candles.
- **Why:** The equity curve needs one data point per candle for visualization and drawdown calculation. If snapshots are only recorded on trade events, the equity curve has gaps. If they're recorded more than once per candle, the curve is distorted. Exactly one-per-candle is required.
- **Failure means:** The equity curve has missing or duplicate points — visualization and drawdown metrics are wrong.

---

## Phase 7: Console Logging (`tests/test_logging.py`)

**Status:** Planned
**Module under test:** `backtester/engine.py` (logging behavior)
**Why this phase:** Logging is how users observe what the engine is doing in real-time. It's also useful for debugging. But it must be controllable.

---

#### `test_buy_message_printed`
- **What:** With `verbosity="normal"`, running a LONG signal prints "BUY" to stdout.
- **Why:** Users need to see what trades the engine is executing. Without trade logging, the engine is a black box. The test uses pytest's `capsys` to capture stdout and verify the message appears.
- **Failure means:** The engine doesn't log trades — users can't see what's happening during a backtest.

#### `test_silent_mode_no_output`
- **What:** With `verbosity="silent"`, running produces zero stdout output.
- **Why:** Silent mode is needed for batch runs, optimization loops, and performance benchmarks where printing thousands of trade messages would slow things down and flood the terminal. If silent mode still prints, it defeats its purpose.
- **Failure means:** Silent mode isn't actually silent — output leaks through, slowing batch operations.

---

## Phase 8: Performance Metrics (`tests/test_metrics.py`)

**Status:** Planned
**Module under test:** `backtester/metrics.py`
**Why this phase:** Metrics are the final output users see. If they're wrong, users will make incorrect decisions about their strategy's performance.

---

### TestTotalReturn (3 tests)

#### `test_positive`
- **What:** 10000 → 10350 = +3.5% return.
- **Why:** Total return is the most basic metric. `(final - initial) / initial`. If this is wrong, every other derived metric is suspect. The test uses exact numbers to pin the formula.
- **Failure means:** The total return formula is wrong.

#### `test_negative`
- **What:** 10000 → 9500 = -5.0% return.
- **Why:** Negative returns must be handled correctly. A bug that takes the absolute value would hide losses.
- **Failure means:** Negative returns are not properly calculated.

#### `test_zero`
- **What:** 10000 → 10000 = 0.0% return.
- **Why:** Zero return is a boundary case. If the formula divides by zero or produces NaN for no-change scenarios, the metric breaks on flat strategies.
- **Failure means:** Zero return edge case produces an error.

---

### TestMaxDrawdown (5 tests)

#### `test_known_curve`
- **What:** Equity [10000, 10200, 10050, 10350] has max drawdown = 150/10200 = 1.47%.
- **Why:** Drawdown measures peak-to-trough decline. The equity peaked at 10200, then dropped to 10050 (a drop of 150). The drawdown is measured as percentage from peak: 150/10200. This test pins the exact calculation with a known curve.
- **Failure means:** The drawdown calculation formula is wrong.

#### `test_no_drawdown`
- **What:** Monotonically increasing equity [100, 200, 300, 400] has zero drawdown.
- **Why:** If equity only goes up, there's never a decline from peak. The function must return 0.0, not NaN or a negative number.
- **Failure means:** The function reports drawdown on upward-only curves.

#### `test_constant_equity`
- **What:** Flat equity [100, 100, 100] has zero drawdown.
- **Why:** No change = no drawdown. This tests the edge case where the denominator (peak) and numerator (peak - current) are related but the division should produce zero.
- **Failure means:** Division issues with flat equity curves.

#### `test_only_decline`
- **What:** Equity [1000, 900, 800, 700] has drawdown = 300/1000 = 30%.
- **Why:** A purely declining equity curve should show the full decline as drawdown. The peak is the first value (1000), the trough is the last (700). This is the worst-case scenario for a strategy.
- **Failure means:** The function doesn't handle pure-decline curves correctly.

#### `test_recovery_then_new_low`
- **What:** Equity [100, 200, 100, 150, 90] has drawdown = 110/200 = 55% (from peak 200 to trough 90).
- **Why:** This tests the tricky case where there's a partial recovery (200→100→150) followed by a new low (90). The max drawdown is from the highest peak (200) to the lowest subsequent trough (90) = 110 points. A naive implementation might only look at the first drop (200→100 = 50%) and miss the deeper overall decline.
- **Failure means:** The function doesn't properly track the running peak and worst decline.

---

### TestWinRate (4 tests)

#### `test_all_wins`
- **What:** [100, 50, 200] → win rate = 1.0 (100%).
- **Why:** All positive PnL trades are wins. Simple counting test.
- **Failure means:** The win counting is broken.

#### `test_all_losses`
- **What:** [-100, -50] → win rate = 0.0 (0%).
- **Why:** All negative PnL trades are losses.
- **Failure means:** The loss counting is broken.

#### `test_mixed`
- **What:** [200, -150, 300] → win rate = 2/3 = 66.7%.
- **Why:** Standard mixed case. 2 winners out of 3 trades.
- **Failure means:** The win/total ratio is calculated incorrectly.

#### `test_zero_pnl_trade_is_not_a_win`
- **What:** [0, 100] → win rate = 0.5 (50%), not 1.0.
- **Why:** A breakeven trade (PnL = 0) is NOT counted as a win. This is a deliberate design decision — the test enforces that `> 0` is used for win counting, not `>= 0`. This matters for strategies with many breakeven trades (e.g., tight SL at entry level).
- **Failure means:** Breakeven trades are counted as wins — inflating the win rate metric.

---

### TestProfitFactor (3 tests)

#### `test_known_values`
- **What:** [200, -150, 300] → profit factor = 500/150 = 3.33.
- **Why:** Profit factor = gross profit / gross loss = (200+300) / 150. This is one of the most important metrics — a profit factor > 1 means the strategy is profitable. Pinning exact values ensures the formula is right.
- **Failure means:** The profit factor formula is wrong.

#### `test_no_losses`
- **What:** [200, 300] → profit factor = infinity (or very large).
- **Why:** When there are no losses, the denominator is zero. The function must handle this gracefully — returning `inf` or a very large number, not crashing with a ZeroDivisionError.
- **Failure means:** Division by zero when there are no losing trades.

#### `test_no_wins`
- **What:** [-200, -300] → profit factor = 0.0.
- **Why:** When there are no wins, gross profit is 0, so profit factor is 0/500 = 0. This represents a completely unprofitable strategy.
- **Failure means:** The function doesn't handle the no-wins case.

---

### TestAvgTrade (1 test)

#### `test_known`
- **What:** [200, -150, 300] → average trade = 350/3 = 116.67.
- **Why:** Average trade = total PnL / number of trades. Simple but important — tells you what to expect per trade on average.
- **Failure means:** The average calculation is wrong.

---

### TestSharpeRatio (2 tests)

#### `test_positive_sharpe`
- **What:** Steadily increasing equity produces a positive Sharpe ratio.
- **Why:** The Sharpe ratio measures risk-adjusted return (return per unit of volatility). A steadily increasing equity has high return and low volatility, so the Sharpe must be positive. This is a directional test — we don't pin the exact value because Sharpe calculation can vary by annualization method.
- **Failure means:** The Sharpe ratio calculation produces wrong signs or crashes on normal data.

#### `test_flat_equity_zero_sharpe`
- **What:** Constant equity [10000]*100 produces Sharpe = 0 (or NaN handled gracefully).
- **Why:** Zero volatility means the denominator of Sharpe is zero. The function must handle this — returning 0.0 or NaN, not crashing. A flat equity curve technically has zero return and zero risk, so Sharpe should be zero.
- **Failure means:** Division by zero on flat equity curves.

---

### TestExposureTime (3 tests)

#### `test_always_in_market`
- **What:** Position held every candle → exposure = 100%.
- **Why:** Exposure time = fraction of candles with an open position. If every candle has a position, exposure is 1.0.
- **Failure means:** The exposure calculation is wrong.

#### `test_never_in_market`
- **What:** No position ever → exposure = 0%.
- **Why:** No trades = no exposure. If the function returns non-zero for zero positions, it's counting wrong.
- **Failure means:** The function reports exposure when there's no position.

#### `test_half_exposure`
- **What:** [1, 1, 0, 0] → exposure = 50%.
- **Why:** Half the candles have a position, half don't. Tests the counting logic with a mix.
- **Failure means:** The ratio calculation is wrong.

---

### TestAnnualizedReturn (1 test)

#### `test_known_value`
- **What:** 10% return over exactly 1 year of 1-minute candles (252 days * 390 minutes) = 10% annualized.
- **Why:** Annualized return converts a raw return to a yearly basis. If the total period is exactly 1 year, the annualized return should equal the raw return. The test uses `252 * 390` candles (252 trading days, 390 minutes per day) which is the standard US market year in 1-minute candles.
- **Failure means:** The annualization formula is wrong — the time-scaling factor is incorrect.

---

## Phase 9: Visualization (`tests/test_visualization.py`)

**Status:** Planned
**Module under test:** `backtester/visualization.py`
**Why this phase:** Charts are the primary way users consume backtest results. These tests verify that chart generation doesn't crash — visual correctness is checked manually.

---

#### `test_equity_curve_returns_figure`
- **What:** `plot_equity_curve()` returns a `matplotlib.Figure` object without crashing.
- **Why:** This is a smoke test. We can't automatically verify that the chart "looks right," but we can verify it doesn't crash and returns the correct type. If the function throws on normal data, users can't generate equity charts.
- **Failure means:** The equity curve plotting function crashes on valid data.

#### `test_drawdown_returns_figure`
- **What:** `plot_drawdown()` returns a Figure without crashing.
- **Why:** Same rationale. Drawdown charts need different data processing than equity charts — this test ensures that processing works.
- **Failure means:** Drawdown chart generation crashes.

#### `test_price_chart_returns_figure`
- **What:** `plot_price_with_markers()` returns a Figure, given prices and buy/sell marker coordinates.
- **Why:** The price chart overlays trade markers (entry/exit points) on the price line. This tests that the marker-overlay logic doesn't crash when given buy points, sell points, and empty SL/TP hit lists.
- **Failure means:** Price chart with trade markers crashes.

#### `test_histogram_returns_figure`
- **What:** `plot_trade_histogram()` returns a Figure for a list of trade PnLs.
- **Why:** The histogram shows the distribution of trade outcomes. This tests that the binning and plotting logic works for a typical mix of positive and negative PnLs.
- **Failure means:** Trade distribution histogram crashes.

#### `test_save_to_file`
- **What:** An equity curve chart can be saved to a PNG file that actually exists on disk.
- **Why:** Users need to export charts for reports and sharing. If `fig.savefig()` silently fails or produces empty files, the export workflow is broken. This test verifies the file is actually created.
- **Failure means:** Chart export to PNG doesn't work.

---

## Phase 10 & 11: Integration & Edge Cases (`tests/test_integration.py`)

**Status:** Planned
**Module under test:** The entire system end-to-end
**Why these phases:** Individual unit tests can all pass while the system as a whole is broken (integration errors, timing mismatches between components). These tests run the full pipeline and stress-test edge cases.

### Fixture: `full_pipeline_data`

Generates 500 candles of synthetic data using a random walk with slight uptrend (seed=42 for reproducibility). This creates realistic-looking price data with enough candles for the MA crossover strategy (with periods 10/30) to generate multiple signals.

---

### TestFullPipeline (4 tests)

#### `test_end_to_end_no_crash`
- **What:** Strategy generates signals from data, engine runs with those signals, and `final_equity > 0`.
- **Why:** This is the ultimate smoke test — does the entire system work together without crashing? Each component was tested individually, but this tests the glue: data flows correctly from strategy to engine, signal format matches what the engine expects, portfolio updates happen at the right time.
- **Failure means:** The components don't work together — interface mismatches, type errors, or integration bugs.

#### `test_capital_identity`
- **What:** `final_equity == initial_capital + realized_pnl + unrealized_pnl` (within floating-point tolerance).
- **Why:** This is the master accounting identity. Money can't appear from nowhere or disappear. If this identity is violated after a full 500-candle run with multiple trades, there's a leak in the accounting — cash is being lost or created somewhere. This catches subtle bugs that only appear after many trades compound.
- **Failure means:** The accounting has a leak — money is being created or destroyed during the simulation.

#### `test_equity_snapshot_count`
- **What:** Exactly 500 snapshots for 500 candles.
- **Why:** Validates that the engine records one snapshot per candle even in a full integration run (not just the simple 5-candle unit test). With signals firing, positions opening/closing, and SL/TP triggering, the snapshot recording must remain consistent.
- **Failure means:** The snapshot recording skips or duplicates under real workload conditions.

#### `test_spread_on_worse_than_off`
- **What:** Both Mode A (spread on) and Mode B (spread off) complete successfully on the same data.
- **Why:** This is a comparative sanity check. Mode A includes spread cost while Mode B uses 0.1% fee. Both should work on the same data. The test doesn't assert which is better (that depends on the spread vs fee magnitude), but it verifies both modes are functional in a full pipeline context.
- **Failure means:** One of the execution modes doesn't work in the full pipeline.

---

### TestDeterminism (1 test)

#### `test_two_runs_identical`
- **What:** Two complete pipeline runs (strategy + engine) on copied data produce identical equity at every snapshot and identical trade counts.
- **Why:** This is the integration-level determinism test. Unit-level determinism was tested in Phase 6, but this tests the full pipeline — including strategy signal generation. If the strategy or engine introduces any randomness (even Python dict ordering or float accumulation differences), this test catches it.
- **Failure means:** The full system is non-deterministic — results vary between runs with the same input.

---

### TestEdgeCases (7 tests)

These tests deliberately push the system into unusual or extreme scenarios to verify graceful handling.

#### `test_zero_signals`
- **What:** Running the full pipeline with no signals produces equity = initial capital and zero trades.
- **Why:** A strategy might produce zero signals for certain data (e.g., completely flat market). The engine must handle this gracefully — no crash, no NaN equity, no phantom trades.
- **Failure means:** The engine can't handle empty signal lists in a full pipeline context.

#### `test_single_trade_lifecycle`
- **What:** One LONG signal with very wide SL/TP (50.0 and 200.0) on flat data — the position stays open at the end.
- **Why:** Tests the case where a trade opens but never closes. At backtest end, the position is still open (unrealized). The system must handle open positions at end-of-data without crashing or losing track of the position.
- **Failure means:** The engine can't handle positions that are still open when data ends.

#### `test_all_sl_hits`
- **What:** Sharply declining prices with a tight SL — every trade hits stop loss, win rate is 0%.
- **Why:** Tests the worst-case scenario where the strategy is completely wrong. The system must still produce valid output (not crash, not produce NaN metrics). A 0% win rate is a valid result that must be reportable.
- **Failure means:** The system crashes or produces invalid metrics when all trades lose.

#### `test_signal_at_last_candle_ignored`
- **What:** Signal on the very last candle of a 5-candle dataset produces zero trades.
- **Why:** Duplicate of the Phase 6 test but in an integration context. Verifies that the boundary check works in the full pipeline, not just in the unit test.
- **Failure means:** The last-candle boundary check fails in the full pipeline.

#### `test_cash_never_negative`
- **What:** After a full 500-candle run with many trades, cash is >= 0 at every single snapshot.
- **Why:** The spec says "no leverage." Negative cash means the system spent more than it had — implicit leverage. This test iterates all 500 snapshots to verify the no-leverage invariant holds at every point in time, not just at the end.
- **Failure means:** The system allows implicit leverage — spending more cash than available at some point during the simulation.

#### `test_position_stacking_respects_capital`
- **What:** Four consecutive LONG signals with `size=1.0` on flat prices — each stack uses 100% of remaining cash, and cash never goes negative.
- **Why:** With `size=1.0`, the first trade consumes all available cash. Subsequent signals have no cash left to allocate. Cash must never go below zero regardless of how many signals the strategy emits. This tests the capital constraint under aggressive stacking.
- **Failure means:** Position stacking doesn't properly check remaining cash — the system creates implicit leverage through stacking.

#### `test_empty_dataframe`
- **What:** Completely empty DataFrame (zero rows) → final equity = initial capital, no crash.
- **Why:** The most extreme edge case. An empty dataset means zero candles to iterate. The engine must return immediately with the initial state intact. This catches off-by-one errors, empty-loop assumptions, and null-reference bugs.
- **Failure means:** The engine crashes on empty input — it assumes at least one candle exists.

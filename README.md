# quant-ML-projects

A collection of quantitative finance and machine learning projects documenting research, experimentation, and learning.

---

## Projects

### [BacktestKit](./backtestkit/)

A modular stock market backtesting engine with pluggable strategy modules.

- Custom backtesting engine with realistic execution modes (spread, fees)
- Stop-loss / take-profit logic
- MA Crossover strategy implementation
- 121 unit tests covering engine, portfolio, execution, and strategy layers
- Data loader with OHLC validation and resampling

---

### [ML-Based Signal Generator](./ML-based-signal-generator/)

A research pipeline for building ML-driven trading signals, inspired by *Advances in Financial Machine Learning*.

**Status: In Progress**

- Transforms raw financial transaction data into structured, information-driven datasets
- Information-driven bar construction (Dollar Imbalance, Dollar/Tick Run Bars)
- CUSUM event sampling & double filtering
- Triple Barrier Method for labeling (direction + playability)
- Two-model architecture: M1 (direction) → M2 (risk gate & sizing)
- Purged cross-validation with embargo to prevent look-ahead bias

**Pipeline:**
\`\`\`
Raw Transactions → Information Bars → Feature Extraction → CUSUM Sampling
→ Triple Barrier Labels → Model 1 (Direction) → Model 2 (Risk & Sizing)
→ Execution → Outcome Logging → Retraining Loop
\`\`\`

# ML-Based Strategy Research Pipeline

⚠️ **Project status: In Progress**  
This is an educational project built as part of my learning process while studying *Advances in Financial Machine Learning*.  
The full implementation is currently under development.

---

## 🧠 Project Purpose

This project explores how to transform noisy, unstructured financial transaction data into a structured, information-driven dataset suitable for machine learning.

The goal is not to "predict the market blindly", but to:

- Reduce noise
- Extract meaningful information
- Create informative labels
- Train ML models in a statistically disciplined way
- Avoid data leakage
- Integrate risk management directly into the modeling pipeline

This is a research-driven implementation inspired by modern ML practices.

---

# 🔁 High-Level Architecture

The most stable conceptual architecture currently looks like:


Event Sampling
↓
Feature Extraction
↓
Symmetric Triple Barrier → Directional Label
↓
Model 1 (M1) → Predict Side (Long / Short / Pass)
↓
Asymmetric TBM / Path Filters → Playability Label
↓
Model 2 (M2) → Act / Pass + Confidence
↓
Dynamic Sizing & Execution
↓
Validation (Purged CV + Embargo)


Each stage focuses on eliminating noise and extracting information with consistent statistical properties.

---

# 📦 1. Raw Data → Structured Information

**Garbage in, garbage out.**

Financial transaction data is unstructured and noisy.  
To apply ML effectively, we:

1. Parse raw transaction data
2. Create information-driven bars
3. Regularize data into feature matrices

Instead of time-based bars, this project explores:

- Dollar Imbalance Bars
- Dollar / Tick Run Bars
- Information-driven sampling

The purpose is to recover better statistical properties:
- More stable variance
- More IID-like returns
- Equal information weight per observation

---

# 🔍 2. Feature Sampling & Double Filtering

After constructing statistically consistent bars:

### Step 1 — Feature Extraction

Each bar produces features describing market behavior:
- Imbalance measures
- Volatility measures
- Derived indicators
- Potential order-flow–inspired features (planned)

ML models only see what we give them.  
Features must encode meaningful structure.

---

### Step 2 — CUSUM Filter (Persistence Detection)

Bars alone are not enough.

We apply a CUSUM filter to detect persistence:
- Only events where cumulative movement exceeds threshold `h`
- Threshold dynamically adjusted by volatility

This creates a **double filter**:

1. Information-driven bars
2. Persistence filter (CUSUM)

Result:
ML is trained only on statistically meaningful events — not random noise.

---

# 🏷 3. Labels & Model 1 — Direction Prediction

Once events are sampled and features extracted:

We need informative labels.

### Triple Barrier Method (Symmetric)

For each event:
- Upper barrier (TP)
- Lower barrier (SL)
- Time barrier (timeout)

Label encodes:
- Long
- Short
- No trade

Model 1 (M1) learns:
> Given these features at event time → which direction historically had higher probability of hitting a barrier?

Key constraint:
- No forward data leakage
- Only past information available at decision time

---

# 🧮 4. Model 2 — Risk Gate & Playability

Model 1 predicts *direction*.  
Model 2 evaluates *trade quality*.

Model 2 may use:
- Volatility features
- Regime context
- Path-dependent information
- Additional risk signals

It answers:
> Is this trade reasonable and executable under current conditions?

Outputs:
- Act / Pass
- Confidence score
- Risk-adjusted probability

---

# 📊 5. Dynamic Position Sizing

Position sizing is determined by:

- Model 1 direction probability
- Model 2 confidence
- Volatility context
- Expected reward-to-risk profile

Decision thresholds are evaluated with:
- PnL-weighted error analysis
- FP/FN impact analysis
- Decision-theory–based calibration

The system aims to:
- Reduce trades with high SL probability
- Scale size based on probabilistic edge
- Avoid overconfident entries in unstable regimes

---

# 🔁 6. Trade Monitoring After Entry

After entry:

Each new bar:
- New features computed
- Updated probability estimates
- Optional tightening of SL
- Optional reduction or exit

Final outcomes logged for training:
- Barrier hit (TP / SL)
- Time expiry
- Return structure

Sequential modeling ensures:
- Proper information flow
- No leakage
- Realistic simulation

---

# 🧪 7. Validation Framework

Validation uses:

- Purged cross-validation
- Embargo techniques
- Proper temporal splits

Goal:
Prevent look-ahead bias and overfitting.

---

# 🧱 Conceptual Pipeline Summary


Raw Transactions
↓
Information-Driven Bars
↓
Feature Extraction
↓
CUSUM Event Sampling
↓
Triple Barrier Labeling
↓
Model 1 (Direction)
↓
Model 2 (Risk & Sizing)
↓
Execution Logic
↓
Outcome Logging
↓
Retraining Loop


Every stage focuses on:

- Noise reduction
- Statistical consistency
- Information extraction
- Probabilistic decision-making

---

# 📌 Current Status

🚧 Implementation in progress.  
Core components under development:

- Modular backtesting engine
- Event sampling module
- Feature extraction pipeline
- Label generation system
- ML model integration
- Validation framework

This project is a structured learning exercise inspired by *Advances in Financial Machine Learning*, designed to deeply understand ML-based decision systems rather than merely replicate trading heuristics.

---

## 🎓 Learning Objective

The goal is not to build a production trading system.

The goal is to:

- Understand how to structure unstructured data
- Learn disciplined ML pipeline design
- Practice proper labeling and validation
- Integrate risk management into modeling
- Develop research-oriented thinking

---

More updates coming soon.
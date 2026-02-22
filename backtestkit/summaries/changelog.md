# Changelog

---

## 2026-02-11
- **Phase 1:** Project scaffolding, data loader, resampler
- **Post-Phase 1:** CLOSE_FULL renamed to CLOSE, added size field

## 2026-02-13
- **Phase 2:** Signal dataclass, BaseStrategy, MA crossover

## 2026-02-14
- **Phase 3:** Execution modes (spread on/off/static)
- **Phase 4:** Portfolio capital accounting
- **Post-Phase 4:** Fixed equity formula (added position_notional)
- **Post-Phase 4:** `smacrossoverstrategy/` -> `strategies/` (multi-strategy support)

## 2026-02-16
- **Phase 5:** SL/TP engine (PositionUnit, check_sl_tp, worst-case rule, spread-adjusted exits)
- **Phase 6:** Main engine loop (BacktestEngine, signal delay, per-candle execution order, snapshots, trade recording,sl_tp engine executor.)

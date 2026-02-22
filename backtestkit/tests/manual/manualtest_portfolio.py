import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backtester.portfolio import Portfolio
from common.models import ExecutionMode


def print_state(portfolio, label=""):
    if label:
        print(f"\n--- {label} ---")
    print(f"  avg entry price:  {portfolio.avg_entry_price}")
    print(f"  position size:    {portfolio.position_size}")
    print(f"  cash:             {portfolio.cash}")
    print(f"  realized pnl:     {portfolio.realized_pnl}")
    print(f"  unrealized pnl:   {portfolio.unrealized_pnl}")
    print(f"  equity:           {portfolio.equity}")


portfolio = Portfolio(initial_capital=10000, mode=ExecutionMode.SPREAD_ON)

# === STEP 1: Open LONG ===
portfolio.open_position(entry_price=100.0, spread=0.5, direction="LONG", size=1.0)
portfolio.update_unrealized(100.0, spread=0.5)
print_state(portfolio, "STEP 1: OPEN LONG at mid=100, spread=0.5, size=1.0")

# === STEP 2: Close LONG ===
portfolio.close_position(exit_price=110.0, spread=0.5, size=1.0)
portfolio.update_unrealized(110.0, spread=0.5)
print_state(portfolio, "STEP 2: CLOSE LONG at mid=110, spread=0.5, size=1.0")

# === STEP 3: Open SHORT (half) ===
portfolio.open_position(entry_price=110.0, spread=0.5, direction="SHORT", size=0.5)
portfolio.update_unrealized(110.0, spread=0.5)
print_state(portfolio, "STEP 3: OPEN SHORT at mid=110, spread=0.5, size=0.5")

# === STEP 4: Stack SHORT (rest) ===
portfolio.open_position(entry_price=120.0, spread=0.5, direction="SHORT", size=1.0)
portfolio.update_unrealized(120.0, spread=0.5)
print_state(portfolio, "STEP 4: STACK SHORT at mid=120, spread=0.5, size=1.0")

# === STEP 5: Close SHORT ===
portfolio.close_position(exit_price=130.0, spread=0.5, size=1.0)
portfolio.update_unrealized(130.0, spread=0.5)
print_state(portfolio, "STEP 5: CLOSE SHORT at mid=130, spread=0.5, size=1.0")

"""integration/portfolio_stub.py

Minimal portfolio state model for paper/sim.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PortfolioStub:
    equity_usd: float
    peak_equity_usd: float
    open_positions: int = 0
    day_pnl_usd: float = 0.0

    @property
    def drawdown_pct(self) -> float:
        if self.peak_equity_usd <= 0:
            return 0.0
        dd = (self.peak_equity_usd - self.equity_usd) / self.peak_equity_usd
        return max(0.0, dd * 100.0)

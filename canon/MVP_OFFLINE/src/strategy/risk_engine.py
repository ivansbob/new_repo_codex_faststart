from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PortfolioState:
    bankroll_usd: float
    open_positions: int = 0
    exposure_by_token: Dict[str, float] | None = None
    daily_pnl_usd: float = 0.0

    def __post_init__(self) -> None:
        if self.exposure_by_token is None:
            self.exposure_by_token = {}


def compute_position_size_usd(bankroll_usd: float, cfg: Dict) -> float:
    # MVP: fixed % of bankroll
    pct = float(cfg["risk"]["fixed_pos_pct"])
    return max(0.0, bankroll_usd * pct)


def allow_new_position(port: PortfolioState, token: str, size_usd: float, cfg: Dict) -> bool:
    if port.open_positions >= int(cfg["risk"]["max_open_positions"]):
        return False

    # kill-switch on daily loss (simple approximation in offline mode)
    max_daily = abs(port.bankroll_usd * float(cfg["risk"]["max_daily_loss_pct"]))
    if port.daily_pnl_usd <= -max_daily:
        return False

    token_cap = port.bankroll_usd * float(cfg["risk"]["max_exposure_per_token_pct"])
    cur = float(port.exposure_by_token.get(token, 0.0))
    return (cur + size_usd) <= token_cap

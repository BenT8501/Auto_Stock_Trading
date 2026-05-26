from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    reason: str


class RiskManager:
    def __init__(self, config: dict):
        self.config = config
        self.risk = config["risk"]

    @property
    def initial_cash(self) -> float:
        return float(self.risk["initial_cash"])

    @property
    def stop_loss_pct(self) -> float:
        return float(self.risk["stop_loss_pct"])

    @property
    def take_profit_pct(self) -> float:
        return float(self.risk["take_profit_pct"])

    def position_budget(self, equity: float) -> float:
        return equity * float(self.risk["position_size_pct"])

    def validate_new_position(
        self,
        *,
        cash: float,
        equity: float,
        open_positions: int,
        new_positions_today: int,
    ) -> RiskDecision:
        if open_positions >= int(self.risk["max_positions"]):
            return RiskDecision(False, "max_positions_reached")
        if new_positions_today >= int(self.risk["max_new_positions_per_day"]):
            return RiskDecision(False, "max_new_positions_per_day_reached")
        if cash <= 0:
            return RiskDecision(False, "no_cash")
        if self.position_budget(equity) <= 0:
            return RiskDecision(False, "position_budget_zero")
        return RiskDecision(True, "allowed")

from __future__ import annotations

from src.broker.base import BrokerInterface


class PaperBroker(BrokerInterface):
    def __init__(self) -> None:
        self.orders: list[dict] = []

    def submit_order(self, order: dict) -> dict:
        simulated = {**order, "status": "accepted_paper_only"}
        self.orders.append(simulated)
        return simulated

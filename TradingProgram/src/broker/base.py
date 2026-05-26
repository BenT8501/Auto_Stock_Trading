from __future__ import annotations

from abc import ABC, abstractmethod


class BrokerInterface(ABC):
    @abstractmethod
    def submit_order(self, order: dict) -> dict:
        raise NotImplementedError

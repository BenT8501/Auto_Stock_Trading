from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid


@dataclass(frozen=True)
class PaperOrder:
    id: str
    created_at: str
    market: str
    symbol: str
    side: str
    quantity: float
    reference_price: float
    reason: str
    name: str = ""
    status: str = "paper_created"
    dedupe_key: str = ""


class OrderManagerBase:
    def buy(self, symbol: str, quantity: float, limit_price: float):
        raise NotImplementedError

    def sell(self, symbol: str, quantity: float, limit_price: float | None = None):
        raise NotImplementedError


class PaperOrderManager(OrderManagerBase):
    def __init__(self, path: str | Path = "outputs/paper_order_manager.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def create_order(
        self,
        *,
        market: str,
        symbol: str,
        side: str,
        quantity: float,
        reference_price: float,
        reason: str,
        name: str = "",
        dedupe_key: str = "",
    ) -> PaperOrder:
        if dedupe_key:
            existing = self.find_by_dedupe_key(dedupe_key)
            if existing is not None:
                fields = PaperOrder.__dataclass_fields__
                return PaperOrder(**{key: existing[key] for key in fields if key in existing})

        order = PaperOrder(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            market=market,
            symbol=symbol,
            name=name,
            side=side,
            quantity=quantity,
            reference_price=reference_price,
            reason=reason,
            dedupe_key=dedupe_key,
        )
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(order), ensure_ascii=False) + "\n")
        return order

    def buy(self, symbol: str, quantity: float, limit_price: float):
        return self.create_order(
            market="",
            symbol=symbol,
            name=symbol,
            side="BUY",
            quantity=quantity,
            reference_price=limit_price,
            reason="paper_buy",
        )

    def sell(self, symbol: str, quantity: float, limit_price: float | None = None):
        return self.create_order(
            market="",
            symbol=symbol,
            name=symbol,
            side="SELL",
            quantity=quantity,
            reference_price=float(limit_price or 0),
            reason="paper_sell",
        )

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def find_by_dedupe_key(self, dedupe_key: str) -> dict[str, Any] | None:
        for row in self.read_all():
            if row.get("dedupe_key") == dedupe_key:
                return row
        return None


def calculate_limit_price(trigger_price: float, current_price: float, config: dict) -> float:
    order = config.get("order", {})
    if order.get("buy_order_type", "limit") != "limit":
        raise RuntimeError("Market orders are disabled. Only limit orders are allowed.")
    basis = order.get("limit_price_basis", "current_price")
    buffer_pct = float(order.get("limit_price_buffer_pct", 0.001))
    base_price = current_price if basis == "current_price" else trigger_price
    return base_price * (1 + buffer_pct)


def calculate_quantity(limit_price: float, total_equity: float, config: dict) -> int:
    if limit_price <= 0:
        return 0
    position_size_pct = float(config.get("risk", {}).get("position_size_pct", 0.05))
    buy_amount = total_equity * position_size_pct
    return int(buy_amount // limit_price)


class BrokerOrderManager(OrderManagerBase):
    def create_order(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError("Real broker order submission is TODO and intentionally disabled.")

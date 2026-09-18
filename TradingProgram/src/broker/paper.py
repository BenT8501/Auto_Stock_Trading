from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid

from src.broker.base import BrokerInterface


@dataclass(frozen=True)
class PaperFill:
    id: str
    order_id: str
    created_at: str
    market: str
    symbol: str
    name: str
    side: str
    quantity: float
    price: float
    gross_amount: float
    status: str = "filled_paper"


class PaperBroker(BrokerInterface):
    def __init__(
        self,
        state_path: str | Path = "outputs/paper_account.json",
        initial_cash_by_market: dict[str, float] | None = None,
    ) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.initial_cash_by_market = initial_cash_by_market or {"KR": 10_000_000.0, "US": 10_000.0}
        self.orders: list[dict] = []
        if not self.state_path.exists():
            self._write_state(
                {
                    "cash": dict(self.initial_cash_by_market),
                    "positions": {},
                    "fills": [],
                }
            )

    @classmethod
    def from_config(cls, config: dict, state_path: str | Path = "outputs/paper_account.json") -> "PaperBroker":
        risk = config.get("risk", {})
        initial_cash = float(risk.get("initial_cash", 10_000_000))
        allocation = risk.get("market_allocation", {})
        kr_weight = float(allocation.get("KR", 0.4))
        us_weight = float(allocation.get("US", 0.6))
        return cls(
            state_path=state_path,
            initial_cash_by_market={
                "KR": initial_cash * kr_weight,
                "US": initial_cash * us_weight,
            },
        )

    def submit_order(self, order: dict) -> dict:
        fill = self._fill_order(order)
        simulated = {**order, **asdict(fill)}
        self.orders.append(simulated)
        return simulated

    def snapshot(self) -> dict[str, Any]:
        return self._read_state()

    def _fill_order(self, order: dict) -> PaperFill:
        market = str(order.get("market") or "US").upper()
        symbol = str(order["symbol"]).upper()
        side = str(order.get("side", "BUY")).upper()
        quantity = float(order["quantity"])
        price = float(order.get("reference_price") or order.get("price") or 0)
        if side not in {"BUY", "SELL"}:
            raise ValueError(f"Unsupported paper order side: {side}")
        if quantity <= 0:
            raise ValueError("Paper order quantity must be positive")
        if price <= 0:
            raise ValueError("Paper order price must be positive")

        state = self._read_state()
        state.setdefault("cash", {})
        state.setdefault("positions", {})
        state.setdefault("fills", [])
        state["cash"].setdefault(market, float(self.initial_cash_by_market.get(market, 0.0)))
        state["positions"].setdefault(market, {})

        gross = quantity * price
        position = state["positions"][market].get(symbol, {"quantity": 0.0, "avg_price": 0.0, "name": ""})
        if side == "BUY":
            if state["cash"][market] < gross:
                raise RuntimeError(f"Insufficient paper cash for {market}: required {gross:.2f}")
            previous_quantity = float(position.get("quantity", 0.0))
            previous_cost = previous_quantity * float(position.get("avg_price", 0.0))
            new_quantity = previous_quantity + quantity
            position["quantity"] = new_quantity
            position["avg_price"] = (previous_cost + gross) / new_quantity
            position["name"] = str(order.get("name") or position.get("name") or symbol)
            state["positions"][market][symbol] = position
            state["cash"][market] -= gross
        else:
            held_quantity = float(position.get("quantity", 0.0))
            if held_quantity < quantity:
                raise RuntimeError(f"Insufficient paper position for {symbol}: held {held_quantity:g}")
            remaining = held_quantity - quantity
            if remaining:
                position["quantity"] = remaining
                state["positions"][market][symbol] = position
            else:
                state["positions"][market].pop(symbol, None)
            state["cash"][market] += gross

        fill = PaperFill(
            id=str(uuid.uuid4()),
            order_id=str(order.get("id") or ""),
            created_at=datetime.now(timezone.utc).isoformat(),
            market=market,
            symbol=symbol,
            name=str(order.get("name") or symbol),
            side=side,
            quantity=quantity,
            price=price,
            gross_amount=gross,
        )
        state["fills"].append(asdict(fill))
        self._write_state(state)
        return fill

    def _read_state(self) -> dict[str, Any]:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _write_state(self, state: dict[str, Any]) -> None:
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import uuid


@dataclass(frozen=True)
class OrderCandidate:
    id: str
    created_at: str
    market: str
    symbol: str
    name: str
    side: str
    quantity: float
    reference_price: float
    estimated_amount: float
    reason: str
    status: str = "pending_approval"

    @classmethod
    def create(
        cls,
        *,
        market: str,
        symbol: str,
        name: str,
        side: str,
        quantity: float,
        reference_price: float,
        reason: str,
    ) -> "OrderCandidate":
        return cls(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            market=market,
            symbol=symbol,
            name=name,
            side=side,
            quantity=quantity,
            reference_price=reference_price,
            estimated_amount=quantity * reference_price,
            reason=reason,
        )


class OrderQueue:
    def __init__(self, path: str | Path = "outputs/paper_orders.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_many(self, orders: list[OrderCandidate]) -> None:
        if not orders:
            return
        with self.path.open("a", encoding="utf-8") as file:
            for order in orders:
                file.write(json.dumps(asdict(order), ensure_ascii=False) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def replace_all(self, rows: list[dict[str, Any]]) -> None:
        with self.path.open("w", encoding="utf-8") as file:
            for row in rows:
                file.write(json.dumps(row, ensure_ascii=False) + "\n")

    def update_status(self, order_id: str, status: str, note: str = "") -> dict[str, Any]:
        rows = self.read_all()
        for row in rows:
            if row.get("id") == order_id:
                row["status"] = status
                row["status_note"] = note
                row["updated_at"] = datetime.now(timezone.utc).isoformat()
                self.replace_all(rows)
                return row
        raise KeyError(f"Order not found: {order_id}")

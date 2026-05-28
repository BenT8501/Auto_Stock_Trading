from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class Position:
    market: str
    symbol: str
    quantity: float
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    name: str = ""


class PositionManager:
    def __init__(self, path: str | Path = "outputs/paper_positions.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return data if isinstance(data, list) else []

    def is_holding(self, symbol: str, market: str | None = None) -> bool:
        symbol_key = str(symbol)
        market_key = str(market).upper() if market else None
        for position in self.read_all():
            if str(position.get("symbol")) != symbol_key:
                continue
            if market_key and str(position.get("market", "")).upper() != market_key:
                continue
            return True
        return False

    def count(self) -> int:
        return len(self.read_all())

    def add(self, position: Position) -> None:
        rows = self.read_all()
        rows.append(asdict(position))
        self.path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    def exit_candidates(self, current_prices: dict[str, float]) -> list[dict[str, Any]]:
        candidates = []
        for position in self.read_all():
            symbol = str(position.get("symbol"))
            current = float(current_prices.get(symbol, 0))
            if current <= 0:
                continue
            if current <= float(position.get("stop_loss_price", 0)):
                candidates.append({**position, "current_price": current, "exit_reason": "stop_loss"})
            elif current >= float(position.get("take_profit_price", 0)):
                candidates.append({**position, "current_price": current, "exit_reason": "take_profit"})
        return candidates

from __future__ import annotations

from pathlib import Path
import uuid

from src.trading.order_queue import OrderCandidate, OrderQueue


def test_order_queue_updates_status() -> None:
    path = Path("outputs") / f"test_orders_{uuid.uuid4().hex}.jsonl"
    queue = OrderQueue(path)
    order = OrderCandidate.create(
        market="us",
        symbol="AAPL",
        name="Apple",
        side="BUY",
        quantity=1,
        reference_price=100,
        reason="test",
    )
    queue.append_many([order])

    updated = queue.update_status(order.id, "approved_paper", "manual approval")
    rows = queue.read_all()

    assert updated["status"] == "approved_paper"
    assert rows[0]["status"] == "approved_paper"
    assert rows[0]["status_note"] == "manual approval"


def test_order_queue_keeps_one_pending_order_per_market_symbol_side() -> None:
    path = Path("outputs") / f"test_orders_{uuid.uuid4().hex}.jsonl"
    queue = OrderQueue(path)
    first = OrderCandidate.create(
        market="kr",
        symbol="005930",
        name="Samsung Electronics",
        side="BUY",
        quantity=1,
        reference_price=70000,
        reason="first",
    )
    second = OrderCandidate.create(
        market="KR",
        symbol="005930",
        name="Samsung Electronics",
        side="BUY",
        quantity=2,
        reference_price=71000,
        reason="second",
    )

    queue.append_many([first])
    queue.append_many([second])

    pending = queue.read_pending()
    assert len(pending) == 1
    assert pending[0]["id"] == second.id
    assert pending[0]["quantity"] == 2

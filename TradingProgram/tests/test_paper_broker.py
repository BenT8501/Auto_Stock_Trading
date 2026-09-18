from __future__ import annotations

from pathlib import Path
import uuid

from src.broker.paper import PaperBroker
from src.trading.order_manager import approve_paper_order
from src.trading.order_queue import OrderCandidate, OrderQueue


def test_paper_broker_buy_updates_cash_and_position() -> None:
    path = Path("outputs") / f"test_paper_account_{uuid.uuid4().hex}.json"
    broker = PaperBroker(path, {"US": 1_000.0})

    result = broker.submit_order(
        {
            "id": "order-1",
            "market": "us",
            "symbol": "AAPL",
            "name": "Apple",
            "side": "BUY",
            "quantity": 2,
            "reference_price": 100,
        }
    )

    snapshot = broker.snapshot()
    assert result["status"] == "filled_paper"
    assert snapshot["cash"]["US"] == 800
    assert snapshot["positions"]["US"]["AAPL"]["quantity"] == 2
    assert snapshot["positions"]["US"]["AAPL"]["avg_price"] == 100


def test_approve_paper_order_fills_queue_order() -> None:
    queue_path = Path("outputs") / f"test_orders_{uuid.uuid4().hex}.jsonl"
    account_path = Path("outputs") / f"test_paper_account_{uuid.uuid4().hex}.json"
    queue = OrderQueue(queue_path)
    broker = PaperBroker(account_path, {"KR": 1_000_000.0})
    order = OrderCandidate.create(
        market="kr",
        symbol="005930",
        name="삼성전자",
        side="BUY",
        quantity=3,
        reference_price=70000,
        reason="test approval",
    )
    queue.append_many([order])

    updated = approve_paper_order(queue, order.id, broker)

    rows = queue.read_all()
    snapshot = broker.snapshot()
    assert updated["status"] == "filled_paper"
    assert rows[0]["paper_fill_status"] == "filled_paper"
    assert rows[0]["filled_quantity"] == 3
    assert snapshot["cash"]["KR"] == 790000
    assert snapshot["positions"]["KR"]["005930"]["quantity"] == 3

from __future__ import annotations

from datetime import date
from pathlib import Path
import uuid

import pandas as pd

from src.trading import desktop_automation
from src.trading.order_manager import PaperOrderManager
from src.trading.position_manager import Position, PositionManager


def test_desktop_automation_creates_paper_buy_once(monkeypatch) -> None:
    watchlist = pd.DataFrame(
        [
            {
                "market": "KR",
                "symbol": "005930",
                "name": "Samsung Electronics",
                "trigger_price": 70000,
                "setup_signal": True,
            }
        ]
    )
    monkeypatch.setattr(
        desktop_automation,
        "build_watchlist",
        lambda *_args, **_kwargs: {"watchlist": watchlist},
    )
    output_dir = Path("outputs/test_desktop_automation")
    output_dir.mkdir(parents=True, exist_ok=True)
    order_path = output_dir / f"paper_orders_{uuid.uuid4().hex}.jsonl"
    manager = PaperOrderManager(order_path)
    position_manager = PositionManager(output_dir / f"paper_positions_{uuid.uuid4().hex}.json")
    config = {"results": {"output_dir": str(output_dir)}}

    first = desktop_automation.run_desktop_automation_cycle(
        config,
        available_buy_amount=100000,
        auto_buy=True,
        refresh_data=False,
        run_date=date(2026, 5, 29),
        order_manager=manager,
        position_manager=position_manager,
        notify=False,
    )
    second = desktop_automation.run_desktop_automation_cycle(
        config,
        available_buy_amount=100000,
        auto_buy=True,
        refresh_data=False,
        run_date=date(2026, 5, 29),
        order_manager=manager,
        position_manager=position_manager,
        notify=False,
    )

    assert first.buy_orders_created == 1
    assert first.buy_orders_skipped_duplicate == 0
    assert second.buy_orders_created == 0
    assert second.buy_orders_skipped_duplicate == 1
    assert len(manager.read_all()) == 1


def test_desktop_automation_creates_paper_sell_for_exit_candidate(monkeypatch) -> None:
    monkeypatch.setattr(
        desktop_automation,
        "build_watchlist",
        lambda *_args, **_kwargs: {"watchlist": pd.DataFrame()},
    )
    output_dir = Path("outputs/test_desktop_automation")
    output_dir.mkdir(parents=True, exist_ok=True)
    ohlcv_path = output_dir / f"ohlcv_{uuid.uuid4().hex}.csv"
    pd.DataFrame(
        [
            {
                "date": "2026-05-29",
                "symbol": "AAA",
                "open": 100,
                "high": 111,
                "low": 99,
                "close": 110,
                "volume": 1000,
            }
        ]
    ).to_csv(ohlcv_path, index=False)
    order_manager = PaperOrderManager(output_dir / f"paper_orders_{uuid.uuid4().hex}.jsonl")
    position_manager = PositionManager(output_dir / f"paper_positions_{uuid.uuid4().hex}.json")
    position_manager.add(
        Position(
            market="US",
            symbol="AAA",
            quantity=1,
            entry_price=100,
            stop_loss_price=95,
            take_profit_price=105,
        )
    )
    config = {
        "data": {"universe_ohlcv_file": str(ohlcv_path)},
        "results": {"output_dir": str(output_dir)},
    }

    result = desktop_automation.run_desktop_automation_cycle(
        config,
        auto_sell=True,
        refresh_data=False,
        run_date=date(2026, 5, 29),
        order_manager=order_manager,
        position_manager=position_manager,
        notify=False,
    )

    rows = order_manager.read_all()
    assert result.sell_orders_created == 1
    assert rows[0]["side"] == "SELL"
    assert rows[0]["reason"] == "desktop_auto_sell_take_profit_paper_only"

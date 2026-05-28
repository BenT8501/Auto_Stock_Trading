from __future__ import annotations

import pandas as pd
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.trading.realtime_scanner import Quote, evaluate_trigger, update_realtime_status


def _config() -> dict:
    return {
        "risk": {"max_positions": 10, "max_new_positions_per_day": 3},
        "realtime": {"entry_delay_minutes": {"US": 15, "KR": 10}},
    }


def _after_us_entry_delay() -> datetime:
    return datetime(2026, 5, 28, 10, 0, tzinfo=ZoneInfo("America/New_York"))


def _row() -> pd.Series:
    return pd.Series(
        {
            "watch_date": "2026-05-29",
            "setup_date": "2026-05-28",
            "symbol": "AAA",
            "name": "Alpha",
            "market": "US",
            "trigger_price": 100.1,
            "gap_limit_price": 103.0,
        }
    )


def test_evaluate_trigger_requires_breakout_and_gap_limit() -> None:
    result = evaluate_trigger(_row(), Quote(current_price=100.2, open_price=102.0), _config(), now=_after_us_entry_delay())

    assert result["trigger_signal"] is True
    assert result["trigger_reason"] == "trigger_price_breakout"


def test_evaluate_trigger_rejects_gap_up_above_limit() -> None:
    result = evaluate_trigger(_row(), Quote(current_price=104.0, open_price=103.1), _config(), now=_after_us_entry_delay())

    assert result["trigger_signal"] is False


def test_evaluate_trigger_rejects_daily_buy_limit() -> None:
    result = evaluate_trigger(
        _row(),
        Quote(current_price=100.2, open_price=102.0),
        {"risk": {"max_positions": 10, "max_new_positions_per_day": 3}},
        daily_buys=3,
        now=_after_us_entry_delay(),
    )

    assert result["trigger_signal"] is False
    assert result["trigger_reason"] == "risk_limit_failed"


def test_evaluate_trigger_rejects_entry_delay() -> None:
    before_delay = datetime(2026, 5, 28, 9, 35, tzinfo=ZoneInfo("America/New_York"))

    result = evaluate_trigger(_row(), Quote(current_price=100.2, open_price=102.0), _config(), now=before_delay)

    assert result["trigger_signal"] is False
    assert result["trigger_reason"] == "entry_delay_not_elapsed"


def test_update_realtime_status_writes_status_file() -> None:
    watchlist = pd.DataFrame([{"symbol": "AAA"}])
    triggered = pd.DataFrame([{"symbol": "AAA", "trigger_signal": True}])

    status = update_realtime_status({}, watchlist, triggered, watch_date=datetime(2026, 5, 29).date())

    assert status.loc[0, "watchlist_count"] == 1
    assert status.loc[0, "triggered_count"] == 1
    assert Path("data/logs/realtime_status_2026-05-29.csv").exists()

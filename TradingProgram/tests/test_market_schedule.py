from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.market_schedule import next_refresh_runs


def _config() -> dict:
    return {
        "schedule": {
            "timezone": "Asia/Seoul",
            "refresh": {
                "KR": {"enabled": True, "local_time": "15:50"},
                "US": {
                    "enabled": True,
                    "market_timezone": "America/New_York",
                    "market_close_time": "16:00",
                    "buffer_minutes_after_close": 15,
                },
            },
        }
    }


def test_next_kr_refresh_uses_close_based_kst_time() -> None:
    now = datetime(2026, 5, 28, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))

    runs = {run.market: run.run_at for run in next_refresh_runs(_config(), now)}

    assert runs["KR"] == datetime(2026, 5, 28, 15, 50, tzinfo=ZoneInfo("Asia/Seoul"))


def test_next_us_refresh_converts_dst_close_to_kst() -> None:
    now = datetime(2026, 5, 28, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))

    runs = {run.market: run.run_at for run in next_refresh_runs(_config(), now)}

    assert runs["US"] == datetime(2026, 5, 29, 5, 15, tzinfo=ZoneInfo("Asia/Seoul"))


def test_next_us_refresh_converts_standard_time_close_to_kst() -> None:
    now = datetime(2026, 12, 1, 12, 0, tzinfo=ZoneInfo("Asia/Seoul"))

    runs = {run.market: run.run_at for run in next_refresh_runs(_config(), now)}

    assert runs["US"] == datetime(2026, 12, 2, 6, 15, tzinfo=ZoneInfo("Asia/Seoul"))

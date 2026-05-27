from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class RefreshRun:
    market: str
    run_at: datetime


def next_refresh_runs(config: dict, now: datetime | None = None) -> list[RefreshRun]:
    schedule = config.get("schedule", {})
    timezone = ZoneInfo(schedule.get("timezone", "Asia/Seoul"))
    current = now.astimezone(timezone) if now else datetime.now(timezone)
    refresh = schedule.get("refresh", {})

    runs: list[RefreshRun] = []
    kr_config = refresh.get("KR", {})
    if kr_config.get("enabled", True):
        runs.append(RefreshRun("KR", _next_kr_run(current, kr_config, timezone)))

    us_config = refresh.get("US", {})
    if us_config.get("enabled", True):
        runs.append(RefreshRun("US", _next_us_run(current, us_config, timezone)))

    return sorted(runs, key=lambda item: item.run_at)


def _next_kr_run(now: datetime, market_config: dict, timezone: ZoneInfo) -> datetime:
    target = _parse_time(market_config.get("local_time", "15:50"))
    day = now.date()
    candidate = datetime.combine(day, target, timezone)
    if candidate <= now or candidate.weekday() >= 5:
        day += timedelta(days=1)
        while day.weekday() >= 5:
            day += timedelta(days=1)
        candidate = datetime.combine(day, target, timezone)
    return candidate


def _next_us_run(now: datetime, market_config: dict, output_timezone: ZoneInfo) -> datetime:
    market_timezone = ZoneInfo(market_config.get("market_timezone", "America/New_York"))
    close_time = _parse_time(market_config.get("market_close_time", "16:00"))
    buffer_minutes = int(market_config.get("buffer_minutes_after_close", 15))
    market_now = now.astimezone(market_timezone)
    day = market_now.date()

    while True:
        candidate_market = datetime.combine(day, close_time, market_timezone) + timedelta(minutes=buffer_minutes)
        candidate = candidate_market.astimezone(output_timezone)
        if candidate > now and day.weekday() < 5:
            return candidate
        day += timedelta(days=1)


def _parse_time(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(hour=int(hour), minute=int(minute))

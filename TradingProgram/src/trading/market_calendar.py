from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


MARKET_TIMEZONES = {
    "KR": "Asia/Seoul",
    "US": "America/New_York",
}

MARKET_OPEN_TIMES = {
    "KR": time(9, 0),
    "US": time(9, 30),
}

MARKET_CLOSE_TIMES = {
    "KR": time(15, 30),
    "US": time(16, 0),
}


def is_regular_session(market: str, now: datetime | None = None) -> bool:
    local_now = _market_now(market, now)
    if local_now.weekday() >= 5:
        return False
    return MARKET_OPEN_TIMES[_market(market)] <= local_now.time() <= MARKET_CLOSE_TIMES[_market(market)]


def entry_delay_elapsed(config: dict, market: str, now: datetime | None = None) -> bool:
    market_key = _market(market)
    local_now = _market_now(market_key, now)
    if local_now.weekday() >= 5:
        return False
    open_at = datetime.combine(local_now.date(), MARKET_OPEN_TIMES[market_key], local_now.tzinfo)
    delay_minutes = int(config.get("realtime", {}).get("entry_delay_minutes", {}).get(market_key, 0))
    return local_now >= open_at + timedelta(minutes=delay_minutes)


def next_trading_date_from_data(symbol_rows) -> str:
    dates = sorted({str(value)[:10] for value in symbol_rows})
    return dates[-1] if dates else ""


def _market_now(market: str, now: datetime | None) -> datetime:
    market_key = _market(market)
    timezone = ZoneInfo(MARKET_TIMEZONES[market_key])
    return now.astimezone(timezone) if now else datetime.now(timezone)


def _market(market: str) -> str:
    value = str(market).upper()
    if value not in MARKET_TIMEZONES:
        return "US"
    return value

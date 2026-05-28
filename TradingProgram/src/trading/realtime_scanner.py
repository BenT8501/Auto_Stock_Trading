from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from src.trading.market_calendar import entry_delay_elapsed
from src.trading.order_manager import PaperOrderManager, calculate_limit_price, calculate_quantity
from src.trading.position_manager import PositionManager


class ScannerBroker(Protocol):
    def get_domestic_price(self, symbol: str) -> dict[str, Any]:
        ...

    def get_overseas_price(self, symbol: str, exchange: str = "NAS") -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class Quote:
    current_price: float
    open_price: float


def latest_watchlist_path(config: dict, watch_date: date | None = None) -> Path:
    output_dir = Path(config.get("watchlist", {}).get("output_dir", "data/watchlist"))
    if watch_date:
        return output_dir / f"watchlist_{watch_date.isoformat()}.csv"
    files = sorted(output_dir.glob("watchlist_*.csv"))
    if not files:
        return output_dir / f"watchlist_{date.today().isoformat()}.csv"
    return files[-1]


def load_watchlist(config: dict, watch_date: date | None = None, market: str | None = None) -> pd.DataFrame:
    path = latest_watchlist_path(config, watch_date)
    if not path.exists():
        return pd.DataFrame()
    watchlist = pd.read_csv(path, dtype={"symbol": str})
    if market and market.upper() != "ALL":
        watchlist = watchlist[watchlist["market"].astype(str).str.upper() == market.upper()]
    return watchlist.reset_index(drop=True)


def load_today_watchlist(config: dict, trade_date: str | None = None, market: str | None = None) -> pd.DataFrame:
    parsed_date = date.fromisoformat(trade_date) if trade_date else None
    return load_watchlist(config, watch_date=parsed_date, market=market)


def calculate_trigger_prices(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    result = df.copy()
    setup = config.get("setup", {})
    trigger_buffer = float(setup.get("trigger_buffer_pct", config.get("execution", {}).get("breakout_buffer_pct", 0.001)))
    gap_limit = float(setup.get("gap_limit_pct", config.get("execution", {}).get("max_gap_up_pct", 0.03)))
    high_column = "prev_high" if "prev_high" in result.columns else "high"
    result["trigger_price"] = result[high_column].astype(float) * (1 + trigger_buffer)
    result["gap_limit_price"] = result[high_column].astype(float) * (1 + gap_limit)
    return result


def scan_watchlist_once(
    config: dict,
    broker: ScannerBroker,
    *,
    watch_date: date | None = None,
    market: str | None = None,
    position_manager: PositionManager | None = None,
    order_manager: PaperOrderManager | None = None,
) -> pd.DataFrame:
    watchlist = load_watchlist(config, watch_date=watch_date, market=market)
    if watchlist.empty:
        triggered = _empty_triggered_frame()
        update_realtime_status(config, watchlist, triggered, watch_date=watch_date)
        return triggered

    rows = []
    position_manager = position_manager or PositionManager()
    order_manager = order_manager or PaperOrderManager()
    current_positions = position_manager.count()
    daily_buys = 0
    for _, row in watchlist.iterrows():
        quote = fetch_quote(broker, row)
        is_holding = position_manager.is_holding(str(row["symbol"]), str(row.get("market", "")))
        evaluated = evaluate_trigger(
            row,
            quote,
            config,
            current_positions=current_positions,
            daily_buys=daily_buys,
            is_holding=is_holding,
        )
        if bool(evaluated["trigger_signal"]):
            limit_price = calculate_limit_price(float(row["trigger_price"]), quote.current_price, config)
            quantity = calculate_quantity(limit_price, float(config.get("risk", {}).get("initial_cash", 0)), config)
            evaluated["limit_price"] = limit_price
            evaluated["quantity"] = quantity
            if quantity > 0:
                order_manager.create_order(
                    market=str(row.get("market", "")),
                    symbol=str(row["symbol"]),
                    side="BUY",
                    quantity=quantity,
                    reference_price=limit_price,
                    reason=str(evaluated["trigger_reason"]),
                )
            rows.append(evaluated)
            daily_buys += 1

    triggered = pd.DataFrame(rows) if rows else _empty_triggered_frame()
    output_dir = Path(config.get("results", {}).get("output_dir", "data/results"))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_date = watch_date or date.today()
    triggered.to_csv(output_dir / f"triggered_candidates_{output_date.isoformat()}.csv", index=False)
    update_realtime_status(config, watchlist, triggered, watch_date=output_date)
    return triggered


def evaluate_trigger(
    row: pd.Series,
    quote: Quote,
    config: dict | None = None,
    *,
    current_positions: int = 0,
    daily_buys: int = 0,
    is_holding: bool = False,
    now: datetime | None = None,
) -> dict[str, Any]:
    trigger_price = float(row["trigger_price"])
    gap_limit_price = float(row["gap_limit_price"])
    market = str(row.get("market", "US")).upper()
    entry_delay_ok = entry_delay_elapsed(config or {}, market, now=now)
    breakout_ok = quote.current_price >= trigger_price
    gap_ok = quote.open_price <= gap_limit_price and quote.current_price <= gap_limit_price
    risk_ok = _risk_allows_trigger(config or {}, current_positions=current_positions, daily_buys=daily_buys)
    holding_ok = not is_holding
    trigger_signal = entry_delay_ok and breakout_ok and gap_ok and risk_ok and holding_ok
    result = row.to_dict()
    result.update(
        {
            "current_price": quote.current_price,
            "open_price": quote.open_price,
            "trigger_signal": bool(trigger_signal),
            "trigger_reason": _trigger_reason(entry_delay_ok, breakout_ok, gap_ok, risk_ok, holding_ok),
        }
    )
    return result


def evaluate_trigger_signal(row: pd.Series, current_price: float, today_open: float, now: datetime | None, config: dict) -> dict[str, Any]:
    return evaluate_trigger(row, Quote(current_price=current_price, open_price=today_open), config, now=now)


def update_realtime_status(
    config: dict,
    watchlist_status: pd.DataFrame,
    triggered: pd.DataFrame | None = None,
    *,
    watch_date: date | None = None,
) -> pd.DataFrame:
    output_dir = Path("data/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_date = watch_date or date.today()
    triggered_count = 0 if triggered is None else len(triggered)
    now = datetime.now().isoformat(timespec="seconds")
    status = pd.DataFrame(
        [
            {
                "timestamp": now,
                "watch_date": output_date.isoformat(),
                "watchlist_count": len(watchlist_status),
                "triggered_count": triggered_count,
                "last_price_check_at": now,
                "last_status_refresh_at": now,
            }
        ]
    )
    status.to_csv(output_dir / f"realtime_status_{output_date.isoformat()}.csv", index=False)
    return status


def _risk_allows_trigger(config: dict, *, current_positions: int, daily_buys: int) -> bool:
    risk = config.get("risk", {})
    max_positions = int(risk.get("max_positions", 999999))
    max_daily_buys = int(risk.get("max_new_positions_per_day", 999999))
    return current_positions < max_positions and daily_buys < max_daily_buys


def _trigger_reason(entry_delay_ok: bool, breakout_ok: bool, gap_ok: bool, risk_ok: bool, holding_ok: bool) -> str:
    if entry_delay_ok and breakout_ok and gap_ok and risk_ok and holding_ok:
        return "trigger_price_breakout"
    if not entry_delay_ok:
        return "entry_delay_not_elapsed"
    if not breakout_ok:
        return "price_below_trigger"
    if not gap_ok:
        return "gap_limit_failed"
    if not holding_ok:
        return "already_holding"
    return "risk_limit_failed"


def fetch_quote(broker: ScannerBroker, row: pd.Series) -> Quote:
    market = str(row.get("market", "US")).upper()
    symbol = str(row["symbol"])
    if market == "KR":
        return _domestic_quote(broker.get_domestic_price(symbol))
    exchange = str(row.get("exchange") or "NAS")
    return _overseas_quote(broker.get_overseas_price(symbol, exchange))


def _domestic_quote(response: dict[str, Any]) -> Quote:
    output = response.get("output", {})
    current = _number(output.get("stck_prpr") or output.get("last") or output.get("base"))
    open_ = _number(output.get("stck_oprc") or output.get("open") or output.get("ovrs_nmix_oprc"))
    return Quote(current_price=current, open_price=open_ or current)


def _overseas_quote(response: dict[str, Any]) -> Quote:
    output = response.get("output", {})
    current = _number(output.get("last") or output.get("base") or output.get("stck_prpr"))
    open_ = _number(output.get("open") or output.get("ovrs_nmix_oprc") or output.get("stck_oprc"))
    return Quote(current_price=current, open_price=open_ or current)


def _empty_triggered_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "setup_date",
            "trade_date",
            "symbol",
            "name",
            "market",
            "trigger_price",
            "gap_limit_price",
            "current_price",
            "open_price",
            "limit_price",
            "quantity",
            "trigger_signal",
            "trigger_reason",
        ]
    )


def _number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0

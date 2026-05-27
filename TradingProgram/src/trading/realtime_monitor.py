from __future__ import annotations

from typing import Any, Protocol

import pandas as pd

from src.data_loader import load_ohlcv_csv
from src.indicators import add_indicators
from src.patterns import add_patterns
from src.signals import add_signals
from src.trading.automation import load_recommendation_universe
from src.trading.order_queue import OrderCandidate, OrderQueue


class LivePriceBroker(Protocol):
    def get_domestic_price(self, symbol: str) -> dict[str, Any]:
        ...

    def get_overseas_price(self, symbol: str, exchange: str = "NAS") -> dict[str, Any]:
        ...


def load_breakout_watchlist(config: dict, market: str | None = None) -> pd.DataFrame:
    ohlcv = load_ohlcv_csv(config["data"]["universe_ohlcv_file"])
    if ohlcv.empty:
        return pd.DataFrame()

    universe = pd.concat(
        [load_recommendation_universe(config, "KR"), load_recommendation_universe(config, "US")],
        ignore_index=True,
    )
    if universe.empty:
        return pd.DataFrame()

    allowed_symbols = set(universe["symbol"].astype(str))
    ohlcv = ohlcv[ohlcv["symbol"].astype(str).isin(allowed_symbols)]
    if ohlcv.empty:
        return pd.DataFrame()

    prepared = add_signals(add_patterns(add_indicators(ohlcv, config)), config)
    latest_rows = prepared.sort_values("date").groupby("symbol", as_index=False).tail(1)
    latest_rows = latest_rows[latest_rows["buy_signal"].astype(bool)].copy()
    if latest_rows.empty:
        return pd.DataFrame()

    metadata = universe[["symbol", "name", "market", "exchange"]].copy()
    metadata["symbol"] = metadata["symbol"].astype(str)
    latest_rows["symbol"] = latest_rows["symbol"].astype(str)
    watchlist = latest_rows.merge(metadata, on="symbol", how="left", suffixes=("", "_universe"))
    if market and market.upper() != "ALL":
        watchlist = watchlist[watchlist["market"].astype(str).str.upper() == market.upper()]
    return watchlist.sort_values(["market", "symbol"]).reset_index(drop=True)


def run_breakout_monitor_once(
    config: dict,
    broker: LivePriceBroker,
    queue: OrderQueue | None = None,
    market: str | None = None,
) -> list[OrderCandidate]:
    monitor_config = config.get("realtime_monitor", {})
    if not monitor_config.get("manual_approval_required", True):
        raise RuntimeError("realtime_monitor.manual_approval_required must remain true")

    watchlist = load_breakout_watchlist(config, market=market)
    if watchlist.empty:
        return []

    max_candidates = int(monitor_config.get("max_candidates_per_cycle", 20))
    orders: list[OrderCandidate] = []
    for _, row in watchlist.head(max_candidates).iterrows():
        current_price = _fetch_current_price(broker, row)
        order = evaluate_breakout_candidate(row, current_price, config)
        if order is not None:
            orders.append(order)

    if queue is not None:
        queue.append_many(orders)
    return orders


def evaluate_breakout_candidate(row: pd.Series, current_price: float, config: dict) -> OrderCandidate | None:
    if current_price <= 0:
        return None

    monitor_config = config.get("realtime_monitor", {})
    automation = config.get("automation", {})
    breakout_buffer = float(monitor_config.get("breakout_buffer_pct", config["execution"].get("breakout_buffer_pct", 0.001)))
    trigger_price = float(row["high"]) * (1 + breakout_buffer)
    if current_price < trigger_price:
        return None

    market = str(row.get("market", "US")).upper()
    max_amount = float(automation["max_order_amount_krw"] if market == "KR" else automation["max_order_amount_usd"])
    quantity = float(int(max_amount // current_price))
    if quantity <= 0:
        return None

    symbol = str(row["symbol"])
    name = str(row.get("name") or symbol)
    return OrderCandidate.create(
        market=market.lower(),
        symbol=symbol,
        name=name,
        side="BUY",
        quantity=quantity,
        reference_price=current_price,
        reason=(
            f"realtime_breakout current_price={current_price:.4f} >= "
            f"signal_high_buffer={trigger_price:.4f}; "
            f"signal_date={row.get('date')}; buy_signal={row.get('buy_pattern', '')}"
        ),
    )


def _fetch_current_price(broker: LivePriceBroker, row: pd.Series) -> float:
    market = str(row.get("market", "US")).upper()
    symbol = str(row["symbol"])
    if market == "KR":
        return _domestic_last_price(broker.get_domestic_price(symbol))
    exchange = str(row.get("exchange") or "NAS")
    return _overseas_last_price(broker.get_overseas_price(symbol, exchange))


def _domestic_last_price(response: dict[str, Any]) -> float:
    output = response.get("output", {})
    return _number(output.get("stck_prpr") or output.get("last") or output.get("base"))


def _overseas_last_price(response: dict[str, Any]) -> float:
    output = response.get("output", {})
    return _number(output.get("last") or output.get("base") or output.get("stck_prpr"))


def _number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0

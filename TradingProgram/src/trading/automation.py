from __future__ import annotations

from typing import Any, Protocol

import pandas as pd

from src.data_loader import load_ohlcv_csv, load_universe_frame
from src.indicators import add_indicators
from src.patterns import add_patterns
from src.signals import add_signals
from src.trading.order_queue import OrderCandidate


class PriceBroker(Protocol):
    def get_domestic_price(self, symbol: str) -> dict[str, Any]:
        ...

    def get_overseas_price(self, symbol: str, exchange: str = "NAS") -> dict[str, Any]:
        ...


def run_automation_cycle(config: dict, broker: PriceBroker) -> list[OrderCandidate]:
    return run_recommendation_cycle(config)


def run_recommendation_cycle(config: dict) -> list[OrderCandidate]:
    automation = config.get("automation", {})
    if not automation.get("enabled", False):
        return []
    if automation.get("mode") != "paper":
        raise RuntimeError("Only paper automation mode is allowed")
    if not automation.get("manual_approval_required", True):
        raise RuntimeError("manual_approval_required must remain true")

    ohlcv_path = config["data"]["universe_ohlcv_file"]
    ohlcv = load_ohlcv_csv(ohlcv_path)
    if ohlcv.empty:
        return []

    universe = pd.concat(
        [load_recommendation_universe(config, "KR"), load_recommendation_universe(config, "US")],
        ignore_index=True,
    )
    allowed_symbols = set(universe["symbol"].astype(str))
    ohlcv = ohlcv[ohlcv["symbol"].astype(str).isin(allowed_symbols)]
    if ohlcv.empty:
        return []

    prepared = add_signals(add_patterns(add_indicators(ohlcv, config)), config)
    latest_rows = prepared.sort_values("date").groupby("symbol", as_index=False).tail(1)
    name_map = dict(zip(universe["symbol"].astype(str), universe["name"].astype(str), strict=False))
    market_map = dict(zip(universe["symbol"].astype(str), universe["market"].astype(str), strict=False))

    orders: list[OrderCandidate] = []
    for _, row in latest_rows.iterrows():
        if not bool(row.get("buy_signal", False)):
            continue
        symbol = str(row["symbol"])
        market = market_map.get(symbol, "US")
        max_amount = float(automation["max_order_amount_krw"] if market == "KR" else automation["max_order_amount_usd"])
        price = float(row["close"])
        quantity = max(1.0, float(int(max_amount // price))) if price > 0 else 0.0
        if quantity <= 0:
            continue
        orders.append(
            OrderCandidate.create(
                market=market.lower(),
                symbol=symbol,
                name=name_map.get(symbol, symbol),
                side="BUY",
                quantity=quantity,
                reference_price=price,
                reason=f"buy_signal={row.get('buy_pattern', '')}; close>MA trend and volume filter passed",
            )
        )

    return orders


def load_recommendation_universe(config: dict, market: str) -> pd.DataFrame:
    automation = config.get("automation", {})
    universe_config = config["universe"]
    if market == "US":
        if not automation.get("scan_us", True):
            return pd.DataFrame()
        frame = load_universe_frame(universe_config["us_file"])
        limit = int(automation.get("max_scan_us", 100))
        default_exchange = "NAS"
    elif market == "KR":
        if not automation.get("scan_kr", True):
            return pd.DataFrame()
        frame = load_universe_frame(universe_config["kr_file"])
        limit = int(automation.get("max_scan_kr", 80))
        default_exchange = ""
    else:
        raise ValueError(f"Unsupported market: {market}")

    active = frame["active"].astype(str).str.lower().isin({"true", "1", "yes", "y"})
    frame = frame[active].sort_values("rank").head(limit).copy()
    if "name" not in frame.columns:
        frame["name"] = frame["symbol"]
    if "quantity" not in frame.columns:
        frame["quantity"] = 1
    if "buy_below" not in frame.columns:
        frame["buy_below"] = 0
    if "sell_above" not in frame.columns:
        frame["sell_above"] = 0
    if "exchange" not in frame.columns:
        frame["exchange"] = default_exchange
    return frame


def _evaluate_item(market: str, item: dict, price: float, max_order_amount: float) -> list[OrderCandidate]:
    if price <= 0:
        return []

    quantity = float(item.get("quantity", 0))
    if quantity <= 0:
        return []

    estimated_amount = price * quantity
    if estimated_amount > max_order_amount:
        return []

    symbol = str(item["symbol"])
    name = str(item.get("name", symbol))
    buy_below = float(item.get("buy_below", 0) or 0)
    sell_above = float(item.get("sell_above", 0) or 0)

    if buy_below > 0 and price <= buy_below:
        return [
            OrderCandidate.create(
                market=market,
                symbol=symbol,
                name=name,
                side="BUY",
                quantity=quantity,
                reference_price=price,
                reason=f"current_price <= buy_below ({price} <= {buy_below})",
            )
        ]
    if sell_above > 0 and price >= sell_above:
        return [
            OrderCandidate.create(
                market=market,
                symbol=symbol,
                name=name,
                side="SELL",
                quantity=quantity,
                reference_price=price,
                reason=f"current_price >= sell_above ({price} >= {sell_above})",
            )
        ]
    return []


def _domestic_last_price(response: dict[str, Any]) -> float:
    output = response.get("output", {})
    return _number(output.get("stck_prpr"))


def _overseas_last_price(response: dict[str, Any]) -> float:
    output = response.get("output", {})
    return _number(output.get("last") or output.get("base"))


def _number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0

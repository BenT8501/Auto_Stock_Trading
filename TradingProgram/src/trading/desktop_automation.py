from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.data_loader import load_ohlcv_csv
from src.external_data_collector import collect_external_universe_ohlcv
from src.search.manual_search import has_meaningful_filter, search_by_conditions
from src.search.query_parser import parse_search_query
from src.trading.notifier import CompositeNotifier
from src.trading.order_manager import PaperOrder, PaperOrderManager
from src.trading.position_manager import Position, PositionManager
from src.trading.watchlist_builder import build_watchlist


@dataclass(frozen=True)
class DesktopAutomationResult:
    refreshed_rows: int
    watchlist_count: int
    filtered_count: int
    buy_orders_created: int
    buy_orders_skipped_duplicate: int
    sell_orders_created: int
    logs_path: str
    message: str


def run_desktop_automation_cycle(
    config: dict,
    *,
    search_query: str = "",
    available_buy_amount: float = 0,
    auto_buy: bool = False,
    auto_sell: bool = False,
    refresh_data: bool = True,
    run_date: date | None = None,
    order_manager: PaperOrderManager | None = None,
    position_manager: PositionManager | None = None,
    notify: bool = True,
) -> DesktopAutomationResult:
    """Run one desktop automation cycle in paper/log mode only."""
    run_date = run_date or date.today()
    refreshed_rows = 0
    if refresh_data:
        refreshed_rows = len(collect_external_universe_ohlcv(config))

    watchlist = build_watchlist(config, run_date=run_date)["watchlist"]
    filtered = _apply_search_filter(config, watchlist, search_query)

    order_manager = order_manager or PaperOrderManager()
    position_manager = position_manager or PositionManager()
    buy_orders: list[PaperOrder] = []
    duplicate_count = 0
    if auto_buy:
        buy_orders, duplicate_count = _create_paper_buy_orders(
            filtered,
            order_manager=order_manager,
            position_manager=position_manager,
            available_buy_amount=available_buy_amount,
            run_date=run_date,
        )

    sell_orders: list[PaperOrder] = []
    if auto_sell:
        sell_orders = _create_paper_sell_orders(
            config,
            order_manager=order_manager,
            position_manager=position_manager,
            run_date=run_date,
        )

    log_path = _write_cycle_log(
        config,
        run_date=run_date,
        rows=filtered,
        buy_orders=buy_orders,
        sell_orders=sell_orders,
        duplicate_count=duplicate_count,
        auto_buy=auto_buy,
        auto_sell=auto_sell,
    )
    message = (
        f"자동 감시 완료: 갱신 {refreshed_rows}행, 감시 {len(watchlist)}건, "
        f"조건 통과 {len(filtered)}건, paper 매수 {len(buy_orders)}건, 중복 제외 {duplicate_count}건"
    )
    if auto_sell:
        message += f", paper 매도 {len(sell_orders)}건"
    if notify and (buy_orders or sell_orders):
        CompositeNotifier.from_config(config).notify(message)

    return DesktopAutomationResult(
        refreshed_rows=refreshed_rows,
        watchlist_count=len(watchlist),
        filtered_count=len(filtered),
        buy_orders_created=len(buy_orders),
        buy_orders_skipped_duplicate=duplicate_count,
        sell_orders_created=len(sell_orders),
        logs_path=str(log_path),
        message=message,
    )


def _apply_search_filter(config: dict, watchlist: pd.DataFrame, search_query: str) -> pd.DataFrame:
    if watchlist.empty:
        return watchlist
    query = search_query.strip()
    if not query:
        return watchlist.reset_index(drop=True)

    defaults = config.get("manual_search", {})
    filters = parse_search_query(query, defaults)
    if not has_meaningful_filter(filters):
        return watchlist.iloc[0:0].copy()

    search_result = search_by_conditions(config, filters)
    if search_result.empty:
        return watchlist.iloc[0:0].copy()

    symbols = {str(symbol).upper() for symbol in search_result["symbol"].astype(str)}
    filtered = watchlist[watchlist["symbol"].astype(str).str.upper().isin(symbols)].copy()
    return filtered.reset_index(drop=True)


def _create_paper_buy_orders(
    rows: pd.DataFrame,
    *,
    order_manager: PaperOrderManager,
    position_manager: PositionManager,
    available_buy_amount: float,
    run_date: date,
) -> tuple[list[PaperOrder], int]:
    if rows.empty or available_buy_amount <= 0:
        return [], 0

    remaining = float(available_buy_amount)
    created: list[PaperOrder] = []
    duplicates = 0
    for _, row in rows.sort_values(["market", "symbol"]).iterrows():
        price = _number(row.get("trigger_price") or row.get("prev_close"))
        if price <= 0 or remaining < price:
            continue
        quantity = int(remaining // price)
        if quantity <= 0:
            continue

        market = str(row.get("market", "")).upper()
        symbol = str(row.get("symbol", "")).upper()
        name = str(row.get("name", symbol))
        dedupe_key = f"{run_date.isoformat()}:{market}:{symbol}:BUY"
        existed = order_manager.find_by_dedupe_key(dedupe_key) is not None
        order = order_manager.create_order(
            market=market,
            symbol=symbol,
            name=name,
            side="BUY",
            quantity=float(quantity),
            reference_price=price,
            reason="desktop_auto_buy_setup_condition_paper_only",
            dedupe_key=dedupe_key,
        )
        if existed:
            duplicates += 1
            continue
        created.append(order)
        if not position_manager.is_holding(symbol, market):
            position_manager.add(
                Position(
                    market=market,
                    symbol=symbol,
                    name=name,
                    quantity=float(quantity),
                    entry_price=price,
                    stop_loss_price=_number(row.get("stop_loss_price")),
                    take_profit_price=_number(row.get("take_profit_price")),
                )
            )
        remaining -= quantity * price
    return created, duplicates


def _create_paper_sell_orders(
    config: dict,
    *,
    order_manager: PaperOrderManager,
    position_manager: PositionManager,
    run_date: date,
) -> list[PaperOrder]:
    current_prices = _latest_close_prices(config)
    exits = position_manager.exit_candidates(current_prices)
    created: list[PaperOrder] = []
    for row in exits:
        market = str(row.get("market", "")).upper()
        symbol = str(row.get("symbol", "")).upper()
        name = str(row.get("name") or symbol)
        reason = str(row.get("exit_reason", "exit"))
        dedupe_key = f"{run_date.isoformat()}:{market}:{symbol}:SELL:{reason}"
        if order_manager.find_by_dedupe_key(dedupe_key) is not None:
            continue
        created.append(
            order_manager.create_order(
                market=market,
                symbol=symbol,
                name=name,
                side="SELL",
                quantity=float(row.get("quantity", 0)),
                reference_price=_number(row.get("current_price")),
                reason=f"desktop_auto_sell_{reason}_paper_only",
                dedupe_key=dedupe_key,
            )
        )
    return created


def _latest_close_prices(config: dict) -> dict[str, float]:
    ohlcv = load_ohlcv_csv(config["data"]["universe_ohlcv_file"])
    if ohlcv.empty:
        return {}
    latest = ohlcv.sort_values("date").groupby("symbol", as_index=False).tail(1)
    return {str(row["symbol"]).upper(): _number(row["close"]) for _, row in latest.iterrows()}


def _write_cycle_log(
    config: dict,
    *,
    run_date: date,
    rows: pd.DataFrame,
    buy_orders: list[PaperOrder],
    sell_orders: list[PaperOrder],
    duplicate_count: int,
    auto_buy: bool,
    auto_sell: bool,
) -> Path:
    log_dir = Path(config.get("results", {}).get("output_dir", "data/results"))
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"desktop_automation_{run_date.isoformat()}.csv"
    frame = rows.copy()
    if frame.empty:
        frame = pd.DataFrame(columns=["date", "market", "symbol", "name", "event", "created_at"])
    frame["event"] = "condition_pass"
    frame["auto_buy"] = auto_buy
    frame["auto_sell"] = auto_sell
    frame["buy_orders_created"] = len(buy_orders)
    frame["sell_orders_created"] = len(sell_orders)
    frame["buy_orders_skipped_duplicate"] = duplicate_count
    frame["created_at"] = datetime.now(timezone.utc).isoformat()
    frame.to_csv(path, index=False)
    return path


def _number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0

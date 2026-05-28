from __future__ import annotations

from pathlib import Path
from typing import Callable, Any

import pandas as pd

from src.search.manual_search import search_by_conditions
from src.search.query_parser import parse_search_query
from src.trading.realtime_scanner import latest_watchlist_path
from src.trading.watchlist_builder import prepare_universe_signals


SAFE_TOOL_NAMES = {
    "get_setup_candidates",
    "get_triggered_candidates",
    "search_by_conditions",
    "explain_stock_status",
    "get_stock_latest_metrics",
    "compare_strategy_conditions",
    "get_trigger_price",
}


class AgentTools:
    def __init__(self, config: dict) -> None:
        self.config = config

    def registry(self) -> dict[str, Callable[..., Any]]:
        return {
            "get_setup_candidates": self.get_setup_candidates,
            "get_triggered_candidates": self.get_triggered_candidates,
            "search_by_conditions": self.search_by_conditions,
            "explain_stock_status": self.explain_stock_status,
            "get_stock_latest_metrics": self.get_stock_latest_metrics,
            "compare_strategy_conditions": self.compare_strategy_conditions,
            "get_trigger_price": self.get_trigger_price,
        }

    def get_setup_candidates(self) -> pd.DataFrame:
        path = latest_watchlist_path(self.config)
        if path.exists():
            return pd.read_csv(path, dtype={"symbol": str})
        return pd.DataFrame()

    def get_triggered_candidates(self) -> pd.DataFrame:
        output_dir = Path(self.config.get("results", {}).get("output_dir", "data/results"))
        files = sorted(output_dir.glob("triggered_candidates_*.csv"))
        if not files:
            return pd.DataFrame()
        return pd.read_csv(files[-1], dtype={"symbol": str})

    def search_by_conditions(self, filters: dict | None = None, query: str | None = None) -> pd.DataFrame:
        if query:
            defaults = self.config.get("manual_search", {})
            filters = parse_search_query(query, defaults)
        return search_by_conditions(self.config, filters or {})

    def explain_stock_status(self, symbol: str) -> dict:
        metrics = self.get_stock_latest_metrics(symbol)
        trigger = self.get_trigger_price(symbol)
        return {"symbol": symbol, "latest_metrics": metrics, "trigger": trigger}

    def get_stock_latest_metrics(self, symbol: str) -> dict:
        prepared = prepare_universe_signals(self.config)
        if prepared.empty:
            return {}
        symbol_key = _symbol_key(symbol)
        rows = prepared[prepared["symbol"].astype(str).map(_symbol_key) == symbol_key].sort_values("date")
        if rows.empty:
            return {}
        row = rows.iloc[-1]
        return {
            "date": str(row.get("date", ""))[:10],
            "symbol": str(row.get("symbol", "")),
            "name": str(row.get("name", "")),
            "market": str(row.get("market", "")),
            "close": _float(row.get("close")),
            "ma20": _float(row.get("ma_short")),
            "ma60": _float(row.get("ma_long")),
            "ma20_slope": _float(row.get("ma_short_slope")),
            "volume_ratio": _float(row.get("volume")) / max(_float(row.get("volume_ma")), 1.0),
            "buy_pattern": str(row.get("buy_pattern", "")),
            "setup_signal": bool(row.get("setup_signal", False)),
        }

    def compare_strategy_conditions(self, symbol: str, relaxed: bool = False) -> dict:
        metrics = self.get_stock_latest_metrics(symbol)
        if not metrics:
            return {}
        volume_threshold = 1.0 if relaxed else 1.2
        return {
            "symbol": metrics["symbol"],
            "close_above_ma20": metrics["close"] > metrics["ma20"],
            "ma20_above_ma60": metrics["ma20"] > metrics["ma60"],
            "ma20_slope_positive": metrics["ma20_slope"] > 0,
            "volume_ratio_pass": metrics["volume_ratio"] > volume_threshold,
            "buy_pattern": metrics["buy_pattern"],
            "relaxed": relaxed,
        }

    def get_trigger_price(self, symbol: str) -> dict:
        setup = self.get_setup_candidates()
        if setup.empty:
            return {}
        symbol_key = _symbol_key(symbol)
        rows = setup[setup["symbol"].astype(str).map(_symbol_key) == symbol_key]
        if rows.empty:
            return {}
        row = rows.iloc[-1]
        return {
            "symbol": str(row.get("symbol", "")),
            "name": str(row.get("name", "")),
            "trigger_price": _float(row.get("trigger_price")),
            "gap_limit_price": _float(row.get("gap_limit_price")),
            "setup_date": str(row.get("setup_date", "")),
            "trade_date": str(row.get("trade_date", "")),
        }


def _symbol_key(symbol: str) -> str:
    value = str(symbol).strip().upper()
    return value.zfill(6) if value.isdigit() else value


def _float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

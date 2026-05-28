from __future__ import annotations

import pandas as pd

from src.search.search_schema import SearchFilters
from src.search.themes import expand_theme
from src.trading.watchlist_builder import prepare_universe_signals


DISPLAY_COLUMNS = [
    "date",
    "symbol",
    "name",
    "market",
    "rank",
    "close",
    "ma_short",
    "ma_long",
    "ma_short_slope",
    "volume",
    "volume_ma",
    "volume_ratio",
    "buy_pattern",
    "setup_signal",
]


def search_by_conditions(config: dict, filters: dict | SearchFilters) -> pd.DataFrame:
    search_filters = filters if isinstance(filters, SearchFilters) else SearchFilters.from_dict(filters)
    prepared = prepare_universe_signals(config)
    if prepared.empty:
        return pd.DataFrame(columns=DISPLAY_COLUMNS)

    result = prepared.copy()
    result["volume_ratio"] = result["volume"] / result["volume_ma"].replace(0, pd.NA)

    if search_filters.latest_only:
        result = result.sort_values("date").groupby("symbol", as_index=False).tail(1)
    if search_filters.market:
        result = result[result["market"].astype(str).str.upper() == search_filters.market]
    if search_filters.keyword:
        result = _filter_keyword(result, search_filters.keyword)
    if search_filters.max_rank is not None and "rank" in result.columns:
        result = result[pd.to_numeric(result["rank"], errors="coerce") <= search_filters.max_rank]
    if search_filters.min_volume_ratio is not None:
        result = result[result["volume_ratio"] >= search_filters.min_volume_ratio]
    if search_filters.close_above_ma20 is True:
        result = result[result["close"] > result["ma_short"]]
    elif search_filters.close_above_ma20 is False:
        result = result[result["close"] <= result["ma_short"]]
    if search_filters.ma20_above_ma60 is True:
        result = result[result["ma_short"] > result["ma_long"]]
    elif search_filters.ma20_above_ma60 is False:
        result = result[result["ma_short"] <= result["ma_long"]]
    if search_filters.patterns:
        valid_patterns = [pattern for pattern in search_filters.patterns if pattern in result.columns]
        if valid_patterns:
            result = result[result[valid_patterns].any(axis=1)]

    result = result.sort_values(["market", "rank", "symbol"], na_position="last")
    if search_filters.max_results:
        result = result.head(search_filters.max_results)
    return _display_frame(result)


def has_meaningful_filter(filters: dict | SearchFilters) -> bool:
    search_filters = filters if isinstance(filters, SearchFilters) else SearchFilters.from_dict(filters)
    return any(
        [
            search_filters.max_rank is not None,
            search_filters.min_volume_ratio is not None,
            search_filters.close_above_ma20 is not None,
            search_filters.ma20_above_ma60 is not None,
            bool(search_filters.patterns),
            bool(search_filters.keyword),
        ]
    )


def _display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in DISPLAY_COLUMNS:
        if column not in result.columns:
            result[column] = ""
    return result[DISPLAY_COLUMNS].reset_index(drop=True)


def _filter_keyword(frame: pd.DataFrame, keyword: str) -> pd.DataFrame:
    expanded = expand_theme(keyword)
    terms = [str(term).lower() for term in expanded.get("terms", []) if str(term).strip()]
    symbols = {_symbol_key(symbol) for symbol in expanded.get("symbols", [])}
    symbol_series = frame["symbol"].astype(str)
    mask = symbol_series.map(_symbol_key).isin(symbols)

    searchable_columns = [
        column
        for column in ["symbol", "name", "market", "exchange", "sector", "industry", "theme", "tags", "keywords"]
        if column in frame.columns
    ]
    for term in terms:
        for column in searchable_columns:
            mask = mask | frame[column].astype(str).str.lower().str.contains(term, regex=False)
    return frame[mask]


def _symbol_key(symbol: str) -> str:
    value = str(symbol).strip().upper()
    return value.zfill(6) if value.isdigit() else value

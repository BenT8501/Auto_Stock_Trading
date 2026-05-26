from __future__ import annotations

import pandas as pd


def add_signals(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    result = df.copy()
    buy_patterns = config["strategy"]["buy_patterns"]
    sell_patterns = config["strategy"]["sell_patterns"]
    volume_multiplier = float(config["strategy"]["volume"]["multiplier"])
    recent_buy_window = _recent_buy_signal_window(result, config)

    trend_ok = (result["close"] > result["ma_long"]) & (result["ma_short_slope"] > 0)
    volume_ok = result["volume"] >= result["volume_ma"] * volume_multiplier

    buy_pattern_mask = result[buy_patterns].any(axis=1)
    sell_pattern_mask = result[sell_patterns].any(axis=1)

    result["buy_signal"] = buy_pattern_mask & trend_ok & volume_ok & recent_buy_window
    result["sell_signal"] = sell_pattern_mask | (result["close"] < result["ma_short"])
    result["buy_pattern"] = result.apply(lambda row: _first_true(row, buy_patterns), axis=1)
    result["sell_pattern"] = result.apply(lambda row: _first_true(row, sell_patterns), axis=1)
    return result


def _first_true(row: pd.Series, columns: list[str]) -> str:
    for column in columns:
        if bool(row.get(column, False)):
            return column
    return ""


def _recent_buy_signal_window(df: pd.DataFrame, config: dict) -> pd.Series:
    window_config = config["strategy"].get("data_window", {})
    recent_days = int(window_config.get("buy_signal_recent_days", 90))
    dates = pd.to_datetime(df["date"])
    latest_by_symbol = dates.groupby(df["symbol"]).transform("max")
    earliest_signal_date = latest_by_symbol - pd.to_timedelta(recent_days, unit="D")
    return dates >= earliest_signal_date

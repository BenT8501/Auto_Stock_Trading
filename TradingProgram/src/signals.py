from __future__ import annotations

import pandas as pd

GRADE_VALUES = {"A", "B", "C", "ETF_A", "ETF_B", "NONE"}


def add_signals(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    result = df.copy()
    buy_patterns = config["strategy"]["buy_patterns"]
    sell_patterns = config["strategy"]["sell_patterns"]
    volume_multiplier = float(config["strategy"]["volume"]["multiplier"])
    recent_buy_window = _recent_buy_signal_window(result, config)

    result["buy_pattern"] = result.apply(lambda row: _first_true(row, buy_patterns), axis=1)
    result["sell_pattern"] = result.apply(lambda row: _first_true(row, sell_patterns), axis=1)

    trend_ok = (
        (result["close"] > result["ma_short"])
        & (result["ma_short"] > result["ma_long"])
        & (result["ma_short_slope"] > 0)
    )
    volume_ok = result["volume"] > result["volume_ma"] * volume_multiplier

    buy_pattern_mask = result[buy_patterns].any(axis=1)
    sell_pattern_mask = result[sell_patterns].any(axis=1)

    result["volume_ratio"] = (result["volume"] / result["volume_ma"].replace(0, pd.NA)).fillna(0)
    add_bollinger_bands(result)
    add_candidate_grades(result, buy_pattern_mask, trend_ok, config)

    result["trend_filter_pass"] = trend_ok
    result["volume_filter_pass"] = volume_ok
    result["buy_pattern_signal"] = buy_pattern_mask
    result["setup_signal"] = result["candidate_grade"].isin(["A", "B", "C", "ETF_A", "ETF_B"]) & recent_buy_window
    result["order_candidate_signal"] = result["candidate_grade"].eq("A")
    result["buy_signal"] = result["setup_signal"]
    result["trigger_signal"] = False
    result["sell_signal"] = sell_pattern_mask | (result["close"] < result["ma_short"])
    return result


def add_bollinger_bands(result: pd.DataFrame) -> None:
    grouped = result.groupby("symbol", group_keys=False)
    result["bb_middle"] = grouped["close"].transform(lambda series: series.rolling(20, min_periods=1).mean())
    bb_std = grouped["close"].transform(lambda series: series.rolling(20, min_periods=2).std()).fillna(0)
    result["bb_upper"] = result["bb_middle"] + bb_std * 2
    result["bb_lower"] = result["bb_middle"] - bb_std * 2
    band_range = result["bb_upper"] - result["bb_lower"]
    safe_band_range = band_range.where(band_range != 0)
    safe_middle = result["bb_middle"].where(result["bb_middle"] != 0)
    result["bb_width"] = (band_range / safe_middle).fillna(0)
    result["bb_width_ma20"] = (
        result["bb_width"]
        .groupby(result["symbol"])
        .transform(lambda series: series.rolling(20, min_periods=1).mean())
        .fillna(0)
    )
    bb_position = (result["close"] - result["bb_lower"]) / safe_band_range
    result["bb_position"] = bb_position.fillna(0.5).astype(float)

    result["is_bb_upper_breakout"] = result["close"] > result["bb_upper"]
    result["is_bb_upper_near"] = result["bb_position"] >= 0.8
    result["is_bb_squeeze"] = result["bb_width"] < result["bb_width_ma20"] * 0.8
    previous_width = result["bb_width"].groupby(result["symbol"]).shift(1)
    result["is_bb_width_expanding"] = result["bb_width"] > previous_width.fillna(result["bb_width"])
    recent_squeeze = result["is_bb_squeeze"].astype(int).groupby(result["symbol"]).transform(
        lambda series: series.rolling(5, min_periods=1).max()
    )
    volume_ma = result["volume_ma"].replace(0, pd.NA)
    result["is_bb_squeeze_breakout"] = (
        recent_squeeze.astype(bool)
        & result["is_bb_upper_breakout"]
        & (result["volume"] > volume_ma.fillna(0) * 1.0)
    )
    result["bb_signal_summary"] = result.apply(make_bb_signal_summary, axis=1)


def make_bb_signal_summary(row: pd.Series) -> str:
    signals: list[str] = []
    volume_ratio = _safe_float(row.get("volume_ratio", 0))
    if bool(row.get("is_bb_squeeze_breakout", False)):
        suffix = f", volume {volume_ratio:.2f}x" if volume_ratio else ""
        signals.append(f"squeeze breakout{suffix}")
    elif bool(row.get("is_bb_upper_breakout", False)):
        suffix = f", volume {volume_ratio:.2f}x" if volume_ratio else ""
        signals.append(f"upper breakout{suffix}")
    elif bool(row.get("is_bb_upper_near", False)):
        signals.append(f"near upper band, position {_safe_float(row.get('bb_position', 0)):.2f}")

    if bool(row.get("is_bb_squeeze", False)):
        signals.append(f"squeeze watch, width {_safe_float(row.get('bb_width', 0)):.3f}")

    if bool(row.get("is_bb_width_expanding", False)):
        signals.append("width expanding")

    if not signals:
        return "BB: neutral"
    return "BB: " + " + ".join(signals)


def add_candidate_grades(result: pd.DataFrame, buy_pattern_mask: pd.Series, trend_ok: pd.Series, config: dict) -> None:
    volume_ratio = result["volume"] / result["volume_ma"].replace(0, pd.NA)
    volume_ratio = volume_ratio.fillna(0)
    volume_a_ok = volume_ratio > 1.2
    volume_b_ok = volume_ratio > 1.0
    etf_volume_b_ok = volume_ratio > 0.8
    recent_signal_3d = _recent_pattern_signal(result, buy_pattern_mask, days=3)
    recent_high = result.groupby("symbol")["high"].transform(lambda series: series.shift(1).rolling(20, min_periods=1).max())
    high_20d = result.groupby("symbol")["high"].transform(lambda series: series.rolling(20, min_periods=1).max())
    near_recent_high = result["close"] >= recent_high.fillna(result["high"]) * 0.98
    near_breakout = result["close"] >= recent_high.fillna(result["high"]) * 0.995
    recent_high_breakout = result["close"] > recent_high.fillna(result["high"])
    near_20day_high = result["close"] >= high_20d.fillna(result["high"]) * 0.98
    is_etf = _detect_etf_symbols(result, config)

    result["is_buy_pattern"] = buy_pattern_mask
    result["buy_pattern_names"] = result["buy_pattern"]
    result["is_trend_ok"] = trend_ok
    result["is_volume_a_ok"] = volume_a_ok
    result["is_volume_b_ok"] = volume_b_ok
    result["is_recent_signal_3d"] = recent_signal_3d
    result["is_near_recent_high"] = near_recent_high
    result["is_near_breakout"] = near_breakout
    result["is_recent_high_breakout"] = recent_high_breakout
    result["is_near_20day_high"] = near_20day_high
    result["is_etf"] = is_etf
    result["volume_ratio"] = volume_ratio

    grades: list[str] = []
    reasons: list[str] = []
    for idx, row in result.iterrows():
        if bool(row["is_etf"]):
            grade, reason = _classify_etf_candidate(row, etf_volume_b_ok.loc[idx])
        else:
            grade, reason = _classify_stock_candidate(row)
        grades.append(grade)
        reasons.append(f"{reason} | {row.get('bb_signal_summary', 'BB: neutral')}")
    result["candidate_grade"] = grades
    result["candidate_reason"] = reasons
    result["bb_confirmed"] = (
        result["is_bb_upper_near"].astype(bool)
        | result["is_bb_upper_breakout"].astype(bool)
        | result["is_bb_squeeze_breakout"].astype(bool)
    )


def _classify_stock_candidate(row: pd.Series) -> tuple[str, str]:
    pattern = str(row.get("buy_pattern") or "buy pattern")
    volume_ratio = float(row.get("volume_ratio", 0))
    if bool(row["is_buy_pattern"]) and bool(row["is_trend_ok"]) and bool(row["is_volume_a_ok"]):
        return "A", f"A Grade: {pattern} + trend ok + volume {volume_ratio:.2f}x"
    if bool(row["is_recent_signal_3d"]) and bool(row["is_trend_ok"]) and bool(row["is_volume_b_ok"]):
        return "B", f"B Grade: buy pattern within 3 days + trend ok + volume {volume_ratio:.2f}x"
    if bool(row["is_trend_ok"]) and bool(row["is_volume_b_ok"]) and (bool(row["is_near_recent_high"]) or bool(row["is_near_breakout"])):
        return "C", f"C Grade: trend ok + volume {volume_ratio:.2f}x + near high/breakout"
    return "NONE", "conditions not met"


def _classify_etf_candidate(row: pd.Series, etf_volume_b_ok: bool) -> tuple[str, str]:
    volume_ratio = float(row.get("volume_ratio", 0))
    if bool(row["is_trend_ok"]) and bool(row["is_volume_b_ok"]) and (bool(row["is_recent_high_breakout"]) or bool(row["is_near_20day_high"])):
        return "ETF_A", f"ETF_A: trend ok + volume {volume_ratio:.2f}x + near/break high"
    if (float(row["close"]) > float(row["ma_short"])) and (float(row["ma_short_slope"]) > 0) and etf_volume_b_ok:
        return "ETF_B", f"ETF_B: close>MA20 + MA20 slope positive + volume {volume_ratio:.2f}x"
    return "NONE", "ETF conditions not met"


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


def _recent_pattern_signal(df: pd.DataFrame, pattern_mask: pd.Series, days: int) -> pd.Series:
    signal = pattern_mask.astype(int)
    return signal.groupby(df["symbol"]).transform(lambda series: series.rolling(days, min_periods=1).max()).astype(bool)


def _detect_etf_symbols(df: pd.DataFrame, config: dict) -> pd.Series:
    symbol = df["symbol"].astype(str).str.upper()
    name = df.get("name", pd.Series("", index=df.index)).astype(str).str.upper()
    etf_symbols = {str(value).upper() for value in config.get("etf", {}).get("symbols", [])}
    known_us_etfs = {"SPY", "QQQ", "VTI", "IWM", "XLK", "SMH", "XLF", "XLE", "XLV"}
    known_kr_etfs = {"069500", "133690", "381180", "229200"}
    return symbol.isin(etf_symbols | known_us_etfs | known_kr_etfs) | name.str.contains("ETF|KODEX|TIGER|ACE|SOL", regex=True)


def _safe_float(value: object) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0

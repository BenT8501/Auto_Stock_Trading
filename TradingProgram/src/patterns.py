from __future__ import annotations

import pandas as pd


def detect_hammer(df: pd.DataFrame) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    lower_shadow = df[["open", "close"]].min(axis=1) - df["low"]
    upper_shadow = df["high"] - df[["open", "close"]].max(axis=1)
    candle_range = (df["high"] - df["low"]).replace(0, pd.NA)
    return (lower_shadow >= body * 2) & (upper_shadow <= body * 0.75) & (body / candle_range <= 0.4)


def detect_bullish_engulfing(df: pd.DataFrame) -> pd.Series:
    prev_open = df.groupby("symbol")["open"].shift(1)
    prev_close = df.groupby("symbol")["close"].shift(1)
    prev_bearish = prev_close < prev_open
    current_bullish = df["close"] > df["open"]
    engulfs_body = (df["open"] <= prev_close) & (df["close"] >= prev_open)
    return prev_bearish & current_bullish & engulfs_body


def detect_morning_star(df: pd.DataFrame) -> pd.Series:
    grouped = df.groupby("symbol")
    first_open = grouped["open"].shift(2)
    first_close = grouped["close"].shift(2)
    middle_open = grouped["open"].shift(1)
    middle_close = grouped["close"].shift(1)
    middle_body = (middle_close - middle_open).abs()
    first_body = (first_close - first_open).abs()
    midpoint_first = (first_open + first_close) / 2
    return (
        (first_close < first_open)
        & (middle_body <= first_body * 0.5)
        & (df["close"] > df["open"])
        & (df["close"] >= midpoint_first)
    )


def detect_piercing_line(df: pd.DataFrame) -> pd.Series:
    grouped = df.groupby("symbol")
    prev_open = grouped["open"].shift(1)
    prev_close = grouped["close"].shift(1)
    prev_midpoint = (prev_open + prev_close) / 2
    prev_bearish = prev_close < prev_open
    current_bullish = df["close"] > df["open"]
    return prev_bearish & current_bullish & (df["open"] < prev_close) & (df["close"] > prev_midpoint) & (df["close"] < prev_open)


def detect_inverted_hammer(df: pd.DataFrame) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    lower_shadow = df[["open", "close"]].min(axis=1) - df["low"]
    upper_shadow = df["high"] - df[["open", "close"]].max(axis=1)
    candle_range = (df["high"] - df["low"]).replace(0, pd.NA)
    prev_close = df.groupby("symbol")["close"].shift(1)
    down_context = df["close"] < prev_close
    return down_context & (upper_shadow >= body * 2) & (lower_shadow <= body * 0.5) & (body / candle_range <= 0.35)


def detect_tweezer_bottom(df: pd.DataFrame) -> pd.Series:
    grouped = df.groupby("symbol")
    prev_open = grouped["open"].shift(1)
    prev_close = grouped["close"].shift(1)
    prev_low = grouped["low"].shift(1)
    low_tolerance = ((df["high"] - df["low"]).abs() * 0.01).fillna(0)
    return (prev_close < prev_open) & (df["close"] > df["open"]) & ((df["low"] - prev_low).abs() <= low_tolerance)


def detect_bearish_engulfing(df: pd.DataFrame) -> pd.Series:
    prev_open = df.groupby("symbol")["open"].shift(1)
    prev_close = df.groupby("symbol")["close"].shift(1)
    prev_bullish = prev_close > prev_open
    current_bearish = df["close"] < df["open"]
    engulfs_body = (df["open"] >= prev_close) & (df["close"] <= prev_open)
    return prev_bullish & current_bearish & engulfs_body


def detect_shooting_star(df: pd.DataFrame) -> pd.Series:
    body = (df["close"] - df["open"]).abs()
    lower_shadow = df[["open", "close"]].min(axis=1) - df["low"]
    upper_shadow = df["high"] - df[["open", "close"]].max(axis=1)
    candle_range = (df["high"] - df["low"]).replace(0, pd.NA)
    return (upper_shadow >= body * 2) & (lower_shadow <= body * 0.75) & (body / candle_range <= 0.4)


def detect_dark_cloud_cover(df: pd.DataFrame) -> pd.Series:
    grouped = df.groupby("symbol")
    prev_open = grouped["open"].shift(1)
    prev_close = grouped["close"].shift(1)
    prev_midpoint = (prev_open + prev_close) / 2
    prev_bullish = prev_close > prev_open
    current_bearish = df["close"] < df["open"]
    return prev_bullish & current_bearish & (df["open"] > prev_close) & (df["close"] < prev_midpoint) & (df["close"] > prev_open)


def detect_evening_star(df: pd.DataFrame) -> pd.Series:
    grouped = df.groupby("symbol")
    first_open = grouped["open"].shift(2)
    first_close = grouped["close"].shift(2)
    middle_open = grouped["open"].shift(1)
    middle_close = grouped["close"].shift(1)
    middle_body = (middle_close - middle_open).abs()
    first_body = (first_close - first_open).abs()
    midpoint_first = (first_open + first_close) / 2
    return (
        (first_close > first_open)
        & (middle_body <= first_body * 0.5)
        & (df["close"] < df["open"])
        & (df["close"] <= midpoint_first)
    )


def detect_tweezer_top(df: pd.DataFrame) -> pd.Series:
    grouped = df.groupby("symbol")
    prev_open = grouped["open"].shift(1)
    prev_close = grouped["close"].shift(1)
    prev_high = grouped["high"].shift(1)
    high_tolerance = ((df["high"] - df["low"]).abs() * 0.01).fillna(0)
    return (prev_close > prev_open) & (df["close"] < df["open"]) & ((df["high"] - prev_high).abs() <= high_tolerance)


PATTERN_DETECTORS = {
    "hammer": detect_hammer,
    "bullish_engulfing": detect_bullish_engulfing,
    "morning_star": detect_morning_star,
    "piercing_line": detect_piercing_line,
    "inverted_hammer": detect_inverted_hammer,
    "tweezer_bottom": detect_tweezer_bottom,
    "bearish_engulfing": detect_bearish_engulfing,
    "shooting_star": detect_shooting_star,
    "dark_cloud_cover": detect_dark_cloud_cover,
    "evening_star": detect_evening_star,
    "tweezer_top": detect_tweezer_top,
}


def add_patterns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for name, detector in PATTERN_DETECTORS.items():
        result[name] = detector(result).fillna(False).astype(bool)
    return result

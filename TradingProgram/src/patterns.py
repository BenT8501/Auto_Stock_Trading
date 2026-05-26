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


PATTERN_DETECTORS = {
    "hammer": detect_hammer,
    "bullish_engulfing": detect_bullish_engulfing,
    "morning_star": detect_morning_star,
    "bearish_engulfing": detect_bearish_engulfing,
    "shooting_star": detect_shooting_star,
}


def add_patterns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for name, detector in PATTERN_DETECTORS.items():
        result[name] = detector(result).fillna(False).astype(bool)
    return result

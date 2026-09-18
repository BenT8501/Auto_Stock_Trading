from __future__ import annotations

import pandas as pd

from src.patterns import add_patterns


def test_bullish_engulfing_detected() -> None:
    df = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "AAA", "open": 10, "high": 11, "low": 8, "close": 9, "volume": 100},
            {"date": "2024-01-02", "symbol": "AAA", "open": 8.5, "high": 12, "low": 8, "close": 11.5, "volume": 200},
        ]
    )
    result = add_patterns(df)
    assert bool(result.loc[1, "bullish_engulfing"])


def test_bearish_engulfing_detected() -> None:
    df = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "AAA", "open": 9, "high": 11, "low": 8, "close": 10, "volume": 100},
            {"date": "2024-01-02", "symbol": "AAA", "open": 10.5, "high": 11, "low": 8, "close": 8.5, "volume": 200},
        ]
    )
    result = add_patterns(df)
    assert bool(result.loc[1, "bearish_engulfing"])


def test_piercing_line_detected() -> None:
    df = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "AAA", "open": 10, "high": 10.5, "low": 8, "close": 8, "volume": 100},
            {"date": "2024-01-02", "symbol": "AAA", "open": 7.8, "high": 9.5, "low": 7.5, "close": 9.2, "volume": 200},
        ]
    )
    result = add_patterns(df)
    assert bool(result.loc[1, "piercing_line"])


def test_dark_cloud_cover_detected() -> None:
    df = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "AAA", "open": 8, "high": 10.5, "low": 7.8, "close": 10, "volume": 100},
            {"date": "2024-01-02", "symbol": "AAA", "open": 10.2, "high": 10.5, "low": 8.7, "close": 8.9, "volume": 200},
        ]
    )
    result = add_patterns(df)
    assert bool(result.loc[1, "dark_cloud_cover"])


def test_evening_star_detected() -> None:
    df = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "AAA", "open": 8, "high": 10.2, "low": 7.8, "close": 10, "volume": 100},
            {"date": "2024-01-02", "symbol": "AAA", "open": 10.1, "high": 10.4, "low": 9.9, "close": 10.2, "volume": 120},
            {"date": "2024-01-03", "symbol": "AAA", "open": 10, "high": 10.1, "low": 8.5, "close": 8.8, "volume": 200},
        ]
    )
    result = add_patterns(df)
    assert bool(result.loc[2, "evening_star"])


def test_inverted_hammer_detected() -> None:
    df = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "AAA", "open": 10, "high": 10.2, "low": 9.5, "close": 9.7, "volume": 100},
            {"date": "2024-01-02", "symbol": "AAA", "open": 9.4, "high": 10.8, "low": 9.35, "close": 9.6, "volume": 200},
        ]
    )
    result = add_patterns(df)
    assert bool(result.loc[1, "inverted_hammer"])


def test_tweezer_bottom_and_top_detected() -> None:
    bottom = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "AAA", "open": 10, "high": 10.1, "low": 8, "close": 8.5, "volume": 100},
            {"date": "2024-01-02", "symbol": "AAA", "open": 8.4, "high": 9.5, "low": 8.01, "close": 9.2, "volume": 200},
        ]
    )
    top = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "BBB", "open": 8, "high": 10, "low": 7.9, "close": 9.5, "volume": 100},
            {"date": "2024-01-02", "symbol": "BBB", "open": 9.6, "high": 9.99, "low": 8.6, "close": 8.8, "volume": 200},
        ]
    )

    result = add_patterns(pd.concat([bottom, top], ignore_index=True))

    assert bool(result.loc[1, "tweezer_bottom"])
    assert bool(result.loc[3, "tweezer_top"])

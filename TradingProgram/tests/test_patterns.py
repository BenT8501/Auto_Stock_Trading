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

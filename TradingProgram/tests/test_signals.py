from __future__ import annotations

import pandas as pd

from src.signals import add_signals


def test_buy_signal_only_uses_recent_window() -> None:
    config = {
        "strategy": {
            "buy_patterns": ["hammer"],
            "sell_patterns": ["shooting_star"],
            "volume": {"multiplier": 1.2},
            "data_window": {"buy_signal_recent_days": 30},
        }
    }
    df = pd.DataFrame(
        [
            {
                "date": "2024-01-01",
                "symbol": "AAA",
                "close": 100,
                "high": 101,
                "ma_long": 90,
                "ma_short": 95,
                "ma_short_slope": 1,
                "volume": 130,
                "volume_ma": 100,
                "hammer": True,
                "shooting_star": False,
            },
            {
                "date": "2024-04-01",
                "symbol": "AAA",
                "close": 110,
                "high": 111,
                "ma_long": 100,
                "ma_short": 105,
                "ma_short_slope": 1,
                "volume": 130,
                "volume_ma": 100,
                "hammer": True,
                "shooting_star": False,
            },
        ]
    )

    result = add_signals(df, config)

    assert not bool(result.loc[0, "buy_signal"])
    assert bool(result.loc[1, "buy_signal"])
    assert bool(result.loc[1, "setup_signal"])
    assert result.loc[1, "candidate_grade"] == "A"


def test_candidate_grades_for_stock_rules() -> None:
    config = _config()
    df = pd.DataFrame(
        [
            _row("2024-01-01", "AAA", close=100, high=100, volume=130, hammer=True),
            _row("2024-01-02", "AAA", close=101, high=101, volume=105, hammer=False),
            _row("2024-01-03", "BBB", close=100, high=101, volume=110, hammer=False),
        ]
    )

    result = add_signals(df, config)

    assert result.loc[0, "candidate_grade"] == "A"
    assert result.loc[1, "candidate_grade"] == "B"
    assert result.loc[2, "candidate_grade"] == "C"
    assert "volume" in result.loc[0, "candidate_reason"]


def test_candidate_grades_for_etf_rules() -> None:
    config = _config()
    config["etf"] = {"symbols": ["SPY", "QQQ"]}
    df = pd.DataFrame(
        [
            _row("2024-01-01", "SPY", close=102, high=102, volume=105, hammer=False),
            _row("2024-01-01", "QQQ", close=102, high=110, volume=85, hammer=False),
        ]
    )

    result = add_signals(df, config)

    assert result.loc[0, "candidate_grade"] == "ETF_A"
    assert result.loc[1, "candidate_grade"] == "ETF_B"


def test_bollinger_bands_are_auxiliary_signals() -> None:
    config = _config()
    rows = []
    for idx in range(60):
        if idx < 30:
            close = 100 + ((idx % 2) - 0.5) * 4
        elif idx < 59:
            close = 100 + ((idx % 2) - 0.5) * 0.05
        else:
            close = 103
        rows.append(
            {
                "date": (pd.Timestamp("2024-02-01") + pd.Timedelta(days=idx)).strftime("%Y-%m-%d"),
                "symbol": "AAA",
                "close": close,
                "high": close + 1,
                "ma_long": 90,
                "ma_short": 95,
                "ma_short_slope": 1,
                "volume": 200 if idx == 59 else 100,
                "volume_ma": 100,
                "hammer": idx == 59,
                "shooting_star": False,
            }
        )

    result = add_signals(pd.DataFrame(rows), config)
    latest = result.iloc[-1]

    assert latest["candidate_grade"] == "A"
    assert latest["bb_middle"] > 0
    assert latest["bb_upper"] > latest["bb_middle"]
    assert latest["bb_lower"] < latest["bb_middle"]
    assert latest["bb_width"] > 0
    assert latest["bb_position"] > 1
    assert bool(latest["is_bb_upper_breakout"])
    assert bool(latest["is_bb_upper_near"])
    assert bool(latest["is_bb_squeeze_breakout"])
    assert "BB:" in latest["bb_signal_summary"]
    assert "BB:" in latest["candidate_reason"]


def _config() -> dict:
    return {
        "strategy": {
            "buy_patterns": ["hammer"],
            "sell_patterns": ["shooting_star"],
            "volume": {"multiplier": 1.2},
            "data_window": {"buy_signal_recent_days": 30},
        }
    }


def _row(date: str, symbol: str, *, close: float, high: float, volume: float, hammer: bool) -> dict:
    return {
        "date": date,
        "symbol": symbol,
        "close": close,
        "high": high,
        "ma_long": 90,
        "ma_short": 95,
        "ma_short_slope": 1,
        "volume": volume,
        "volume_ma": 100,
        "hammer": hammer,
        "shooting_star": False,
    }

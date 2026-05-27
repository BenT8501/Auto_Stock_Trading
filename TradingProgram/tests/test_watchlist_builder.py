from __future__ import annotations

from datetime import date

import pandas as pd

from src.indicators import add_indicators
from src.patterns import add_patterns
from src.signals import add_signals
from src.trading.watchlist_builder import _build_watchlist_frame


def _config() -> dict:
    return {
        "strategy": {
            "data_window": {"buy_signal_recent_days": 90},
            "moving_average": {"short_window": 2, "long_window": 3, "slope_period": 1},
            "volume": {"window": 2, "multiplier": 1.2},
            "candle": {"body_avg_window": 2},
            "buy_patterns": ["hammer", "bullish_engulfing", "morning_star"],
            "sell_patterns": ["bearish_engulfing", "shooting_star"],
        },
        "execution": {"breakout_buffer_pct": 0.001, "max_gap_up_pct": 0.03},
        "risk": {"stop_loss_pct": -0.03, "take_profit_pct": 0.07},
        "realtime_monitor": {"breakout_buffer_pct": 0.001, "max_gap_up_pct": 0.03},
    }


def test_setup_signal_uses_trend_volume_and_buy_pattern() -> None:
    df = pd.DataFrame(
        [
            {"date": "2026-01-01", "symbol": "AAA", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 100},
            {"date": "2026-01-02", "symbol": "AAA", "open": 99, "high": 100, "low": 98, "close": 98, "volume": 100},
            {"date": "2026-01-03", "symbol": "AAA", "open": 97, "high": 110, "low": 96, "close": 109, "volume": 300},
        ]
    )

    result = add_signals(add_patterns(add_indicators(df, _config())), _config())

    assert bool(result.loc[2, "setup_signal"])
    assert bool(result.loc[2, "buy_signal"])


def test_build_watchlist_frame_calculates_trigger_and_risk_prices() -> None:
    setup = pd.DataFrame(
        [
            {
                "date": "2026-05-28",
                "symbol": "AAA",
                "name": "Alpha",
                "market": "US",
                "exchange": "NAS",
                "open": 99.0,
                "high": 100.0,
                "low": 98.0,
                "close": 99.0,
                "volume": 1000,
                "ma_short": 95.0,
                "ma_long": 90.0,
                "ma_short_slope": 1.0,
                "volume_ma": 800.0,
                "buy_pattern": "hammer",
            }
        ]
    )

    watchlist = _build_watchlist_frame(setup, _config(), date(2026, 5, 29))

    assert watchlist.loc[0, "trigger_price"] == 100.1
    assert watchlist.loc[0, "gap_limit_price"] == 103.0
    assert round(watchlist.loc[0, "stop_loss_price"], 4) == 97.097
    assert round(watchlist.loc[0, "take_profit_price"], 4) == 107.107
    assert watchlist.loc[0, "trade_date"] == "2026-05-29"
    assert watchlist.loc[0, "pattern"] == "hammer"
    assert not bool(watchlist.loc[0, "trigger_signal"])

from __future__ import annotations

import pandas as pd

from src.signals import add_signals


def test_buy_signal_only_uses_recent_window() -> None:
    config = {
        "strategy": {
            "buy_patterns": ["hammer"],
            "sell_patterns": ["shooting_star"],
            "volume": {"multiplier": 1.0},
            "data_window": {"buy_signal_recent_days": 30},
        }
    }
    df = pd.DataFrame(
        [
            {
                "date": "2024-01-01",
                "symbol": "AAA",
                "close": 100,
                "ma_long": 90,
                "ma_short": 95,
                "ma_short_slope": 1,
                "volume": 100,
                "volume_ma": 100,
                "hammer": True,
                "shooting_star": False,
            },
            {
                "date": "2024-04-01",
                "symbol": "AAA",
                "close": 110,
                "ma_long": 100,
                "ma_short": 105,
                "ma_short_slope": 1,
                "volume": 100,
                "volume_ma": 100,
                "hammer": True,
                "shooting_star": False,
            },
        ]
    )

    result = add_signals(df, config)

    assert not bool(result.loc[0, "buy_signal"])
    assert bool(result.loc[1, "buy_signal"])

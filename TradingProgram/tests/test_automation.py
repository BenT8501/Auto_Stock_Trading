from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.trading.automation import load_recommendation_universe, run_recommendation_cycle


def test_automation_disabled_generates_no_orders() -> None:
    config = {"automation": {"enabled": False}}
    assert run_recommendation_cycle(config) == []


def test_automation_requires_paper_mode() -> None:
    config = {"automation": {"enabled": True, "mode": "live", "manual_approval_required": True}}
    try:
        run_recommendation_cycle(config)
    except RuntimeError as exc:
        assert "paper" in str(exc)
    else:
        raise AssertionError("live automation mode must be rejected")


def test_recommendation_universe_uses_active_ranked_rows() -> None:
    path = Path("outputs/test_universe_ranked.csv")
    path.write_text(
        "symbol,name,market,rank,active\n"
        "BBB,Beta,US,2,true\n"
        "AAA,Alpha,US,1,true\n"
        "CCC,Gamma,US,3,false\n",
        encoding="utf-8",
    )
    config = {
        "universe": {"us_file": str(path), "kr_file": str(path)},
        "automation": {"scan_us": True, "max_scan_us": 100},
    }

    result = load_recommendation_universe(config, "US")

    assert result["symbol"].tolist() == ["AAA", "BBB"]


def test_recommendation_cycle_uses_saved_ohlcv() -> None:
    universe_path = Path("outputs/test_recommendation_universe.csv")
    ohlcv_path = Path("outputs/test_recommendation_ohlcv.csv")
    universe_path.write_text(
        "symbol,name,market,rank,active\n"
        "AAA,Alpha,US,1,true\n",
        encoding="utf-8",
    )

    rows = []
    for idx in range(70):
        rows.append(
            {
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx),
                "symbol": "AAA",
                "open": 100 + idx,
                "high": 102 + idx,
                "low": 99 + idx,
                "close": 101 + idx,
                "volume": 100000 + idx,
            }
        )
    rows[-2].update({"open": 170, "high": 172, "low": 165, "close": 166, "volume": 300000})
    rows[-1].update({"open": 165, "high": 180, "low": 164, "close": 179, "volume": 350000})
    pd.DataFrame(rows).to_csv(ohlcv_path, index=False)

    config = {
        "data": {"universe_ohlcv_file": str(ohlcv_path)},
        "universe": {"us_file": str(universe_path), "kr_file": str(universe_path)},
        "strategy": {
            "buy_patterns": ["bullish_engulfing"],
            "sell_patterns": ["shooting_star"],
            "volume": {"window": 20, "multiplier": 1.0},
            "moving_average": {"short_window": 20, "long_window": 60, "slope_period": 1},
            "candle": {"body_avg_window": 20},
            "data_window": {"buy_signal_recent_days": 90},
        },
        "automation": {
            "enabled": True,
            "mode": "paper",
            "manual_approval_required": True,
            "max_order_amount_krw": 1000,
            "max_order_amount_usd": 10000,
            "scan_kr": False,
            "scan_us": True,
            "max_scan_kr": 80,
            "max_scan_us": 100,
        },
    }

    orders = run_recommendation_cycle(config)

    assert len(orders) == 1
    assert orders[0].symbol == "AAA"
    assert orders[0].side == "BUY"

from __future__ import annotations

from pathlib import Path
import uuid

import pandas as pd

from src.search.manual_search import has_meaningful_filter, search_by_conditions


def test_search_by_conditions_filters_latest_market_and_volume() -> None:
    base = Path("test_artifacts") / uuid.uuid4().hex
    base.mkdir(parents=True, exist_ok=True)
    ohlcv = base / "ohlcv.csv"
    universe = base / "universe.csv"
    ohlcv.write_text(
        "date,symbol,open,high,low,close,volume\n"
        "2026-01-01,AAA,100,101,99,100,100\n"
        "2026-01-02,AAA,101,103,100,102,250\n"
        "2026-01-03,AAA,101,104,100,103,400\n",
        encoding="utf-8",
    )
    universe.write_text("symbol,name,market,rank,active,exchange\nAAA,Alpha,US,1,true,NAS\n", encoding="utf-8")
    config = {
        "data": {"universe_ohlcv_file": str(ohlcv)},
        "universe": {"kr_file": str(universe), "us_file": str(universe)},
        "automation": {"scan_kr": False, "scan_us": True, "max_scan_us": 100},
        "strategy": {
            "data_window": {"buy_signal_recent_days": 90},
            "moving_average": {"short_window": 2, "long_window": 3, "slope_period": 1},
            "volume": {"window": 2, "multiplier": 1.2},
            "candle": {"body_avg_window": 2},
            "buy_patterns": ["hammer", "bullish_engulfing", "morning_star"],
            "sell_patterns": ["bearish_engulfing", "shooting_star"],
        },
    }

    result = search_by_conditions(config, {"market": "US", "min_volume_ratio": 1.2, "latest_only": True})

    assert len(result) == 1
    assert result.loc[0, "symbol"] == "AAA"
    assert result.loc[0, "market"] == "US"


def test_has_meaningful_filter_rejects_market_only() -> None:
    assert not has_meaningful_filter({"market": "KR", "latest_only": True, "max_results": 50})
    assert has_meaningful_filter({"market": "KR", "min_volume_ratio": 1.2})
    assert has_meaningful_filter({"keyword": "Apple", "latest_only": True})


def test_keyword_search_expands_semiconductor_theme() -> None:
    base = Path("test_artifacts") / uuid.uuid4().hex
    base.mkdir(parents=True, exist_ok=True)
    ohlcv = base / "ohlcv.csv"
    universe = base / "universe.csv"
    ohlcv.write_text(
        "date,symbol,open,high,low,close,volume\n"
        "2026-01-01,NVDA,100,101,99,100,100\n"
        "2026-01-02,NVDA,101,103,100,102,250\n"
        "2026-01-03,NVDA,101,104,100,103,400\n",
        encoding="utf-8",
    )
    universe.write_text("symbol,name,market,rank,active,exchange\nNVDA,NVIDIA Corp,US,1,true,NAS\n", encoding="utf-8")
    config = {
        "data": {"universe_ohlcv_file": str(ohlcv)},
        "universe": {"kr_file": str(universe), "us_file": str(universe)},
        "automation": {"scan_kr": False, "scan_us": True, "max_scan_us": 100},
        "strategy": {
            "data_window": {"buy_signal_recent_days": 90},
            "moving_average": {"short_window": 2, "long_window": 3, "slope_period": 1},
            "volume": {"window": 2, "multiplier": 1.2},
            "candle": {"body_avg_window": 2},
            "buy_patterns": ["hammer", "bullish_engulfing", "morning_star"],
            "sell_patterns": ["bearish_engulfing", "shooting_star"],
        },
    }

    result = search_by_conditions(config, {"keyword": "반도체", "latest_only": True})

    assert len(result) == 1
    assert result.loc[0, "symbol"] == "NVDA"

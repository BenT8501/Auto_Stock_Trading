from __future__ import annotations

import pandas as pd

from src.backtester import run_multi_symbol_backtest, run_single_symbol_backtest
from src.config import load_config
from src.data_loader import load_ohlcv_csv


def test_sample_backtest_runs() -> None:
    config = load_config("config.yaml")
    df = load_ohlcv_csv(config["data"]["sample_file"])
    result = run_single_symbol_backtest(df, config)
    assert not result["equity_curve"].empty
    assert set(result) == {"prepared_data", "trades", "equity_curve", "skipped_signals"}


def test_multi_symbol_backtest_runs() -> None:
    config = load_config("config.yaml")
    rows = []
    for symbol, offset in [("AAA", 0), ("BBB", 10)]:
        prices = [
            (100 + offset, 102 + offset, 99 + offset, 101 + offset, 100000),
            (101 + offset, 103 + offset, 100 + offset, 102 + offset, 105000),
            (102 + offset, 104 + offset, 101 + offset, 103 + offset, 110000),
            (103 + offset, 105 + offset, 102 + offset, 104 + offset, 115000),
            (104 + offset, 106 + offset, 103 + offset, 105 + offset, 120000),
            (105 + offset, 107 + offset, 104 + offset, 106 + offset, 125000),
            (106 + offset, 108 + offset, 105 + offset, 107 + offset, 130000),
            (107 + offset, 109 + offset, 106 + offset, 108 + offset, 135000),
            (108 + offset, 110 + offset, 107 + offset, 109 + offset, 140000),
            (109 + offset, 111 + offset, 108 + offset, 110 + offset, 145000),
            (110 + offset, 112 + offset, 109 + offset, 111 + offset, 150000),
            (111 + offset, 113 + offset, 110 + offset, 112 + offset, 155000),
            (112 + offset, 114 + offset, 111 + offset, 113 + offset, 160000),
            (113 + offset, 115 + offset, 112 + offset, 114 + offset, 165000),
            (114 + offset, 116 + offset, 113 + offset, 115 + offset, 170000),
            (115 + offset, 117 + offset, 114 + offset, 116 + offset, 175000),
            (116 + offset, 118 + offset, 115 + offset, 117 + offset, 180000),
            (117 + offset, 119 + offset, 116 + offset, 118 + offset, 185000),
            (118 + offset, 120 + offset, 117 + offset, 119 + offset, 190000),
            (119 + offset, 121 + offset, 118 + offset, 120 + offset, 195000),
            (121 + offset, 122 + offset, 115 + offset, 116 + offset, 300000),
            (115 + offset, 124 + offset, 114 + offset, 123 + offset, 350000),
            (123.3 + offset, 130 + offset, 122 + offset, 129 + offset, 250000),
            (129 + offset, 139 + offset, 128 + offset, 138 + offset, 230000),
            (138 + offset, 139 + offset, 132 + offset, 133 + offset, 220000),
        ]
        for idx, (open_, high, low, close, volume) in enumerate(prices):
            rows.append(
                {
                    "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx),
                    "symbol": symbol,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )

    result = run_multi_symbol_backtest(pd.DataFrame(rows), config, {"AAA": "US", "BBB": "US"})

    assert not result["equity_curve"].empty
    assert set(result) == {"prepared_data", "trades", "equity_curve", "skipped_signals", "open_positions"}

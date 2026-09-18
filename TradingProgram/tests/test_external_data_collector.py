from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import external_data_collector


def test_collect_external_universe_ohlcv_reports_progress(monkeypatch, tmp_path: Path) -> None:
    us_path = tmp_path / "us.csv"
    kr_path = tmp_path / "kr.csv"
    output_path = tmp_path / "ohlcv.csv"
    us_path.write_text("symbol,name,market,rank,active\nAAPL,Apple,US,1,true\n", encoding="utf-8")
    kr_path.write_text("symbol,name,market,rank,active\n005930,Samsung,KR,1,true\n", encoding="utf-8")
    config = {
        "strategy": {"data_window": {"history_days": 30}},
        "data": {"universe_ohlcv_file": str(output_path)},
        "universe": {"us_file": str(us_path), "kr_file": str(kr_path)},
    }
    events: list[tuple[int, int, str, str]] = []

    def fake_us_fetch(symbols, _start, _end, *, progress_callback=None, progress_start=0, progress_total=None):
        if progress_callback is not None:
            progress_callback(progress_start + 1, progress_total or len(symbols), symbols[0], "US")
        return _ohlcv(symbols[0])

    def fake_kr_fetch(symbols, _start, _end, *, progress_callback=None, progress_start=0, progress_total=None):
        if progress_callback is not None:
            progress_callback(progress_start + 1, progress_total or len(symbols), symbols[0], "KR")
        return _ohlcv(symbols[0])

    monkeypatch.setattr(external_data_collector, "fetch_yfinance_ohlcv", fake_us_fetch)
    monkeypatch.setattr(external_data_collector, "fetch_pykrx_ohlcv", fake_kr_fetch)

    result = external_data_collector.collect_external_universe_ohlcv(
        config,
        progress_callback=lambda completed, total, symbol, market: events.append((completed, total, symbol, market)),
    )

    assert len(result) == 2
    assert output_path.exists()
    assert events == [
        (0, 2, "", "start"),
        (1, 2, "AAPL", "US"),
        (2, 2, "005930", "KR"),
        (2, 2, "", "done"),
    ]


def _ohlcv(symbol: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2026-06-01",
                "symbol": symbol,
                "open": 100,
                "high": 110,
                "low": 90,
                "close": 105,
                "volume": 1000,
            }
        ]
    )

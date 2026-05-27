from __future__ import annotations

import pandas as pd

from src.trading.realtime_monitor import evaluate_breakout_candidate


def _config() -> dict:
    return {
        "execution": {"breakout_buffer_pct": 0.001},
        "automation": {"max_order_amount_krw": 1_000_000, "max_order_amount_usd": 1_000},
        "realtime_monitor": {"breakout_buffer_pct": 0.001, "manual_approval_required": True},
    }


def test_evaluate_breakout_candidate_creates_order_after_trigger() -> None:
    row = pd.Series(
        {
            "date": "2026-05-28",
            "symbol": "005930",
            "name": "삼성전자",
            "market": "KR",
            "high": 100_000,
            "buy_pattern": "bullish_engulfing",
        }
    )

    order = evaluate_breakout_candidate(row, 100_200, _config())

    assert order is not None
    assert order.market == "kr"
    assert order.symbol == "005930"
    assert order.quantity == 9
    assert "realtime_breakout" in order.reason


def test_evaluate_breakout_candidate_ignores_price_below_trigger() -> None:
    row = pd.Series(
        {
            "date": "2026-05-28",
            "symbol": "AAPL",
            "name": "Apple",
            "market": "US",
            "high": 100,
            "buy_pattern": "hammer",
        }
    )

    order = evaluate_breakout_candidate(row, 100.09, _config())

    assert order is None

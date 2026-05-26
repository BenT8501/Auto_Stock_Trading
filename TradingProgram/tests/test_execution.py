from __future__ import annotations

import pandas as pd

from src.execution import plan_sell


def test_stop_loss_precedes_take_profit_on_same_bar() -> None:
    row = pd.Series({"low": 95, "high": 110, "sell_signal": False, "close": 100})
    result = plan_sell(row, entry_price=100, stop_loss_pct=-0.03, take_profit_pct=0.07)
    assert result.should_sell
    assert result.reason == "stop_loss"
    assert result.price == 97

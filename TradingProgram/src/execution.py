from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BuyPlan:
    allowed: bool
    price: float | None
    reason: str


@dataclass(frozen=True)
class SellPlan:
    should_sell: bool
    price: float | None
    reason: str


def plan_next_day_buy(signal_row: pd.Series, next_row: pd.Series, config: dict) -> BuyPlan:
    execution = config["execution"]
    breakout_buffer = float(execution["breakout_buffer_pct"])
    max_gap_up = float(execution["max_gap_up_pct"])
    trigger = float(signal_row["high"])
    fill_price = trigger * (1 + breakout_buffer)

    if bool(execution.get("use_gap_filter", True)) and float(next_row["open"]) > trigger * (1 + max_gap_up):
        return BuyPlan(False, None, "gap_up_exceeded")
    if float(next_row["high"]) <= trigger:
        return BuyPlan(False, None, "breakout_not_touched")
    if float(next_row["low"]) > fill_price:
        return BuyPlan(False, None, "fill_price_not_available")
    return BuyPlan(True, fill_price, "breakout_fill")


def plan_sell(row: pd.Series, entry_price: float, stop_loss_pct: float, take_profit_pct: float) -> SellPlan:
    stop_price = entry_price * (1 + stop_loss_pct)
    target_price = entry_price * (1 + take_profit_pct)

    hit_stop = float(row["low"]) <= stop_price
    hit_target = float(row["high"]) >= target_price
    if hit_stop:
        return SellPlan(True, stop_price, "stop_loss")
    if hit_target:
        return SellPlan(True, target_price, "take_profit")
    if bool(row.get("sell_signal", False)):
        return SellPlan(True, float(row["close"]), "sell_signal")
    return SellPlan(False, None, "hold")

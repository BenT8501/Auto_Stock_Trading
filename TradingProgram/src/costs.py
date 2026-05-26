from __future__ import annotations


def buy_cost(price: float, shares: int, market_costs: dict) -> float:
    gross = price * shares
    return gross * (float(market_costs["buy_fee_pct"]) + float(market_costs["slippage_pct"]))


def sell_cost(price: float, shares: int, market_costs: dict) -> float:
    gross = price * shares
    return gross * (
        float(market_costs["sell_fee_pct"])
        + float(market_costs["sell_tax_pct"])
        + float(market_costs["slippage_pct"])
    )

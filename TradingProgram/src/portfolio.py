from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Position:
    symbol: str
    shares: int
    entry_price: float
    entry_date: object
    entry_cost: float


class Portfolio:
    def __init__(self, initial_cash: float):
        self.cash = float(initial_cash)
        self.position: Position | None = None
        self.trades: list[dict] = []
        self.equity_curve: list[dict] = []

    def equity(self, close_price: float) -> float:
        if self.position is None:
            return self.cash
        return self.cash + self.position.shares * close_price

    def buy(self, symbol: str, date, price: float, shares: int, cost: float) -> None:
        gross = price * shares
        self.cash -= gross + cost
        self.position = Position(symbol, shares, price, date, cost)

    def sell(self, date, price: float, cost: float, reason: str) -> None:
        if self.position is None:
            raise RuntimeError("Cannot sell without an open position")
        gross = price * self.position.shares
        self.cash += gross - cost
        pnl = (price - self.position.entry_price) * self.position.shares - self.position.entry_cost - cost
        self.trades.append(
            {
                "symbol": self.position.symbol,
                "entry_date": self.position.entry_date,
                "exit_date": date,
                "entry_price": self.position.entry_price,
                "exit_price": price,
                "shares": self.position.shares,
                "pnl": pnl,
                "return_pct": pnl / (self.position.entry_price * self.position.shares),
                "exit_reason": reason,
            }
        )
        self.position = None

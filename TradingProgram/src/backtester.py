from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.costs import buy_cost, sell_cost
from src.execution import plan_next_day_buy, plan_sell
from src.indicators import add_indicators
from src.patterns import add_patterns
from src.portfolio import Portfolio
from src.risk import RiskManager
from src.signals import add_signals


@dataclass
class MultiPosition:
    symbol: str
    market: str
    shares: int
    entry_price: float
    entry_date: object
    entry_cost: float


def run_single_symbol_backtest(df: pd.DataFrame, config: dict, market: str = "US") -> dict:
    if df["symbol"].nunique() != 1:
        raise ValueError("run_single_symbol_backtest expects exactly one symbol")

    prepared = add_signals(add_patterns(add_indicators(df, config)), config)
    risk = RiskManager(config)
    portfolio = Portfolio(risk.initial_cash)
    market_costs = config["costs"][market]
    skipped_signals: list[dict] = []
    new_positions_today = 0

    rows = list(prepared.iterrows())
    for idx, row in rows:
        date = row["date"]
        close = float(row["close"])

        if portfolio.position is not None:
            sell_plan = plan_sell(row, portfolio.position.entry_price, risk.stop_loss_pct, risk.take_profit_pct)
            if sell_plan.should_sell and sell_plan.price is not None:
                cost = sell_cost(sell_plan.price, portfolio.position.shares, market_costs)
                portfolio.sell(date, sell_plan.price, cost, sell_plan.reason)

        if portfolio.position is None and bool(row.get("buy_signal", False)):
            next_index = idx + 1
            if next_index >= len(prepared):
                skipped_signals.append(_skip(row, "no_next_trading_row"))
            else:
                decision = risk.validate_new_position(
                    cash=portfolio.cash,
                    equity=portfolio.equity(close),
                    open_positions=0,
                    new_positions_today=new_positions_today,
                )
                if not decision.allowed:
                    skipped_signals.append(_skip(row, decision.reason))
                else:
                    next_row = prepared.iloc[next_index]
                    buy_plan = plan_next_day_buy(row, next_row, config)
                    if not buy_plan.allowed or buy_plan.price is None:
                        skipped_signals.append(_skip(row, buy_plan.reason))
                    else:
                        budget = min(risk.position_budget(portfolio.equity(close)), portfolio.cash)
                        shares = int(budget // buy_plan.price)
                        if shares <= 0:
                            skipped_signals.append(_skip(row, "insufficient_budget_for_one_share"))
                        else:
                            cost = buy_cost(buy_plan.price, shares, market_costs)
                            portfolio.buy(str(row["symbol"]), next_row["date"], buy_plan.price, shares, cost)
                            new_positions_today += 1

        portfolio.equity_curve.append({"date": date, "equity": portfolio.equity(close)})
        new_positions_today = 0

    return {
        "prepared_data": prepared,
        "trades": pd.DataFrame(portfolio.trades),
        "equity_curve": pd.DataFrame(portfolio.equity_curve),
        "skipped_signals": pd.DataFrame(skipped_signals),
    }


def run_multi_symbol_backtest(df: pd.DataFrame, config: dict, market_map: dict[str, str] | None = None) -> dict:
    prepared = add_signals(add_patterns(add_indicators(df, config)), config)
    prepared = prepared.sort_values(["date", "symbol"]).reset_index(drop=True)
    market_map = market_map or {}

    risk = RiskManager(config)
    cash = risk.initial_cash
    positions: dict[str, MultiPosition] = {}
    trades: list[dict] = []
    skipped_signals: list[dict] = []
    equity_curve: list[dict] = []
    close_by_symbol: dict[str, float] = {}

    grouped = {symbol: group.reset_index(drop=True) for symbol, group in prepared.groupby("symbol")}
    next_rows: dict[tuple[str, object], pd.Series] = {}
    for symbol, group in grouped.items():
        for idx, row in group.iterrows():
            if idx + 1 < len(group):
                next_rows[(symbol, row["date"])] = group.iloc[idx + 1]

    for date, day in prepared.groupby("date", sort=True):
        new_positions_today = 0
        for _, row in day.iterrows():
            close_by_symbol[str(row["symbol"])] = float(row["close"])

        for symbol, position in list(positions.items()):
            row_match = day[day["symbol"] == symbol]
            if row_match.empty:
                continue
            row = row_match.iloc[0]
            sell_plan = plan_sell(row, position.entry_price, risk.stop_loss_pct, risk.take_profit_pct)
            if sell_plan.should_sell and sell_plan.price is not None:
                market_costs = config["costs"][position.market]
                cost = sell_cost(sell_plan.price, position.shares, market_costs)
                gross = sell_plan.price * position.shares
                cash += gross - cost
                pnl = (sell_plan.price - position.entry_price) * position.shares - position.entry_cost - cost
                trades.append(
                    {
                        "symbol": symbol,
                        "market": position.market,
                        "entry_date": position.entry_date,
                        "exit_date": date,
                        "entry_price": position.entry_price,
                        "exit_price": sell_plan.price,
                        "shares": position.shares,
                        "pnl": pnl,
                        "return_pct": pnl / (position.entry_price * position.shares),
                        "holding_days": (pd.Timestamp(date) - pd.Timestamp(position.entry_date)).days,
                        "exit_reason": sell_plan.reason,
                    }
                )
                del positions[symbol]

        for _, row in day[day["buy_signal"]].iterrows():
            symbol = str(row["symbol"])
            if symbol in positions:
                skipped_signals.append(_skip(row, "already_holding"))
                continue
            equity = _portfolio_equity(cash, positions, close_by_symbol)
            decision = risk.validate_new_position(
                cash=cash,
                equity=equity,
                open_positions=len(positions),
                new_positions_today=new_positions_today,
            )
            if not decision.allowed:
                skipped_signals.append(_skip(row, decision.reason))
                continue
            market = market_map.get(symbol, _infer_market(symbol))
            if not _market_allocation_allowed(market, positions, close_by_symbol, equity, config):
                skipped_signals.append(_skip(row, "market_allocation_limit"))
                continue
            next_row = next_rows.get((symbol, row["date"]))
            if next_row is None:
                skipped_signals.append(_skip(row, "no_next_trading_row"))
                continue
            buy_plan = plan_next_day_buy(row, next_row, config)
            if not buy_plan.allowed or buy_plan.price is None:
                skipped_signals.append(_skip(row, buy_plan.reason))
                continue
            budget = min(risk.position_budget(equity), cash)
            shares = int(budget // buy_plan.price)
            if shares <= 0:
                skipped_signals.append(_skip(row, "insufficient_budget_for_one_share"))
                continue
            market_costs = config["costs"][market]
            cost = buy_cost(buy_plan.price, shares, market_costs)
            total_cost = buy_plan.price * shares + cost
            if total_cost > cash:
                skipped_signals.append(_skip(row, "insufficient_cash_after_cost"))
                continue
            cash -= total_cost
            positions[symbol] = MultiPosition(symbol, market, shares, buy_plan.price, next_row["date"], cost)
            new_positions_today += 1

        equity_curve.append({"date": date, "equity": _portfolio_equity(cash, positions, close_by_symbol)})

    return {
        "prepared_data": prepared,
        "trades": pd.DataFrame(trades),
        "equity_curve": pd.DataFrame(equity_curve),
        "skipped_signals": pd.DataFrame(skipped_signals),
        "open_positions": pd.DataFrame([position.__dict__ for position in positions.values()]),
    }


def _skip(row: pd.Series, reason: str) -> dict:
    return {
        "date": row["date"],
        "symbol": row["symbol"],
        "buy_pattern": row.get("buy_pattern", ""),
        "reason": reason,
    }


def _portfolio_equity(cash: float, positions: dict[str, MultiPosition], close_by_symbol: dict[str, float]) -> float:
    market_value = sum(position.shares * close_by_symbol.get(symbol, position.entry_price) for symbol, position in positions.items())
    return cash + market_value


def _infer_market(symbol: str) -> str:
    return "KR" if symbol.endswith(".KS") or symbol.isdigit() else "US"


def _market_allocation_allowed(
    market: str,
    positions: dict[str, MultiPosition],
    close_by_symbol: dict[str, float],
    equity: float,
    config: dict,
) -> bool:
    allocation = config["risk"].get("market_allocation", {})
    limit = float(allocation.get(market, 1.0))
    exposure = 0.0
    for symbol, position in positions.items():
        if position.market == market:
            exposure += position.shares * close_by_symbol.get(symbol, position.entry_price)
    next_position_budget = equity * float(config["risk"]["position_size_pct"])
    return (exposure + next_position_budget) / equity <= limit if equity > 0 else False

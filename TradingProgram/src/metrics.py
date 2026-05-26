from __future__ import annotations

import pandas as pd


def compute_metrics(equity_curve: pd.DataFrame, trades: pd.DataFrame, initial_cash: float) -> dict:
    if equity_curve.empty:
        return {}

    final_equity = float(equity_curve["equity"].iloc[-1])
    total_return = final_equity / initial_cash - 1
    days = max(1, (pd.Timestamp(equity_curve["date"].iloc[-1]) - pd.Timestamp(equity_curve["date"].iloc[0])).days)
    cagr = (final_equity / initial_cash) ** (365 / days) - 1 if initial_cash > 0 else 0.0
    running_max = equity_curve["equity"].cummax()
    drawdown = equity_curve["equity"] / running_max - 1

    if trades.empty or "pnl" not in trades.columns:
        wins = pd.DataFrame()
        losses = pd.DataFrame()
    else:
        wins = trades[trades["pnl"] > 0]
        losses = trades[trades["pnl"] <= 0]
    gross_profit = float(wins["pnl"].sum()) if not wins.empty else 0.0
    gross_loss = abs(float(losses["pnl"].sum())) if not losses.empty else 0.0
    average_holding_days = float(trades["holding_days"].mean()) if not trades.empty and "holding_days" in trades.columns else 0.0
    avg_win = float(wins["pnl"].mean()) if not wins.empty else 0.0
    avg_loss = float(losses["pnl"].mean()) if not losses.empty else 0.0

    return {
        "initial_cash": initial_cash,
        "final_equity": final_equity,
        "total_return_pct": total_return * 100,
        "cagr_pct": cagr * 100,
        "max_drawdown_pct": float(drawdown.min()) * 100,
        "trade_count": int(len(trades)),
        "win_rate_pct": (len(wins) / len(trades) * 100) if len(trades) else 0.0,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "payoff_ratio": abs(avg_win / avg_loss) if avg_loss else None,
        "profit_factor": gross_profit / gross_loss if gross_loss else None,
        "average_holding_days": average_holding_days,
    }

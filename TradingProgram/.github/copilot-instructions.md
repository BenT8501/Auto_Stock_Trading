# GitHub Copilot Instructions

This repository is a stock trading research program.

## Principles

- Build backtesting and paper trading before any real broker execution.
- Keep strategy, data, risk, backtest, broker, and report code separated.
- Do not hardcode API keys, account numbers, tokens, or secrets.
- Do not implement live trading as enabled by default.
- Do not write profit guarantees or buy/sell recommendations for a specific stock.
- Every simulated order must pass risk checks before it is created.
- Keep signal generation independent from fill assumptions.
- Add tests when changing signal, execution, risk, or accounting behavior.

## Python Style

- Target Python 3.11 or newer.
- Prefer typed functions and pure, testable helpers.
- Use `logging` for operational events.
- Use pandas vectorized operations for indicators and candle patterns.

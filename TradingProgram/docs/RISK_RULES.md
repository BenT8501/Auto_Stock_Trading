# Risk Rules

Phase 1 risk controls:

- max open positions
- max new positions per day
- position size percentage
- stop loss
- take profit
- transaction cost and slippage inclusion

Rules:

- The risk manager must approve a simulated entry before the backtester creates it.
- If a daily bar touches both stop loss and take profit, the stop loss is assumed first.
- Real broker execution is disabled.

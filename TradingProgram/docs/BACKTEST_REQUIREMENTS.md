# Backtest Requirements

Required behavior:

- Use local normalized OHLCV data.
- Sort by symbol and date.
- Use the next available trading row for entry simulation.
- Include fees, taxes, and slippage.
- Export trades, equity curve, skipped signals, and metrics.
- Keep fill assumptions outside signal generation.

Known limitations:

- Single-symbol backtest only in the first implementation.
- No benchmark comparison yet.
- No walk-forward validation yet.
- No survivorship-bias-free universe construction yet.

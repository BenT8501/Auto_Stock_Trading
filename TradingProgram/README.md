# TradingProgram

Rule-driven stock trading research program focused on backtesting first.

This project intentionally disables real broker execution in the initial phase.
The system can generate signals, run conservative single-symbol backtests, and
produce review artifacts, but it must not place live orders.

## Run

```powershell
python main.py --config config.yaml
```

Windows shortcut scripts:

```text
chat.bat      Start the local review chat agent
backtest.bat  Run the sample backtest
review.bat    Generate the review report
ui.bat        Start the Streamlit UI at http://localhost:8501
broker_check.bat  Run KIS read-only price check
```

## KIS Read-Only API

Copy `.env.example` to `.env` and fill in your KIS credentials.

```text
KIS_APP_KEY=...
KIS_APP_SECRET=...
KIS_ACCOUNT_NO=...
KIS_ACCOUNT_PRODUCT_CODE=01
```

Only read-only calls are implemented:

- access token issue
- domestic stock price inquiry
- domestic account balance inquiry
- US stock price inquiry
- overseas stock balance inquiry

Order submission remains disabled by design.

Examples:

```powershell
python broker_check.py --asset domestic --symbol 005930
python broker_check.py --asset us --symbol AAPL --exchange NAS
python broker_check.py --asset us --symbol AAPL --exchange NAS --balance
```

## Test

```powershell
python -m pytest
```

## Safety Rules

- No live broker API calls in Phase 1.
- No same-day buy on a candle signal.
- Backtest fills use the next available trading row.
- Transaction costs and slippage are included.
- Risk checks must pass before any simulated order is created.
- The review agent audits design and code; it does not recommend specific stocks.

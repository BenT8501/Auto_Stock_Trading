# TradingProgram Structure Design

## 1. Goal

Build a Python-based rule-driven stock trading research program.

Phase 1 focuses only on backtesting. Real broker APIs are intentionally excluded until the strategy, accounting, and risk logic are verified.

The system should support:

- Daily OHLCV based candle pattern detection
- Trend and volume filters
- Single-symbol backtest first
- Multi-symbol portfolio backtest later
- Paper trading after backtest validation
- Real trading only after paper trading validation

## 2. Design Principles

- Keep strategy logic independent from data source and broker implementation.
- Do not hardcode strategy parameters in Python modules.
- Treat backtest fills conservatively.
- Include transaction costs from v1, even if the default values are rough.
- Make every pattern and signal function testable with small DataFrames.
- Keep broker modules as interfaces/stubs until Phase 2.

## 3. Proposed Directory Structure

```text
TradingProgram/
├── README.md
├── requirements.txt
├── config.yaml
├── main.py
├── app.py
│
├── data/
│   ├── universe/
│   │   ├── us_top100.csv
│   │   └── kr_top80.csv
│   ├── sample/
│   │   └── sample_ohlcv.csv
│   ├── raw/
│   └── processed/
│
├── outputs/
│   ├── trades/
│   ├── reports/
│   └── charts/
│
├── logs/
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data_loader.py
│   ├── calendar.py
│   ├── indicators.py
│   ├── patterns.py
│   ├── signals.py
│   ├── execution.py
│   ├── backtester.py
│   ├── portfolio.py
│   ├── risk.py
│   ├── metrics.py
│   ├── report.py
│   ├── costs.py
│   ├── logging_utils.py
│   └── broker/
│       ├── __init__.py
│       ├── base.py
│       ├── paper.py
│       └── kis.py
│
├── tests/
│   ├── test_patterns.py
│   ├── test_indicators.py
│   ├── test_signals.py
│   ├── test_execution.py
│   └── test_backtester.py
│
└── notebooks/
    └── research.ipynb
```

## 4. Module Responsibilities

### `app.py`

Runs the first user interface.

Recommended Phase 1 UI stack:

- Streamlit

Reason:

- Fast to build
- Good enough for backtest inspection
- Avoids spending early effort on frontend infrastructure before the strategy is validated

Initial UI scope:

- Load config
- Select sample/local CSV file
- Select symbol
- Run single-symbol backtest
- Show key metrics
- Show equity curve
- Show trade history table
- Show signal rows
- Export trade history/report CSV

Not included in Phase 1 UI:

- Real order buttons
- Broker login
- API key input
- Live position sync
- Automated scheduled trading

Those belong after paper trading architecture is stable.

### `src/config.py`

Loads and validates `config.yaml`.

Expected responsibilities:

- Read YAML
- Provide default values where safe
- Fail fast when required fields are missing
- Later replace plain dicts with Pydantic models if config grows

### `src/data_loader.py`

Loads universe and OHLCV data.

Phase 1 scope:

- Load CSV universe files
- Load local OHLCV CSV files
- Normalize columns to:
  - `date`
  - `symbol`
  - `open`
  - `high`
  - `low`
  - `close`
  - `volume`
- Sort by symbol/date

Out of Phase 1:

- yfinance download
- pykrx download
- automatic universe updates

### `src/calendar.py`

Market calendar helper.

Phase 1 can be minimal:

- Infer next trading day from available OHLCV rows

Later:

- NYSE holiday calendar
- KRX holiday calendar
- early close handling
- market-specific timezone logic

### `src/indicators.py`

Adds technical indicators.

Initial indicators:

- `ma20`
- `ma60`
- `ma20_slope`
- `volume_ma20`
- `body_avg20`

Important rule:

- Indicator calculations must be grouped by `symbol` in multi-symbol mode.

### `src/patterns.py`

Detects the five v1 candle patterns.

Buy patterns:

- `hammer`
- `bullish_engulfing`
- `morning_star`

Sell patterns:

- `bearish_engulfing`
- `shooting_star`

Implementation requirements:

- Return boolean Series
- Use vectorized pandas operations
- Use `&`, `|`, `~` for Series logic, not Python `and/or/not`
- Keep trend context filters separate from raw candle shape detection

### `src/signals.py`

Combines candle patterns, trend filters, and volume filters.

Expected output columns:

- `buy_signal`
- `buy_pattern`
- `sell_signal`
- `sell_pattern`

Signal generation should not decide actual fill price. That belongs in `execution.py`.

### `src/execution.py`

Handles backtest fill assumptions.

Initial buy rule:

- Signal on day `i`
- Evaluate buy on day `i+1`
- Buy only if `next_high > signal_high`
- Skip if `next_open > signal_high * (1 + max_gap_up_pct)`
- Default fill price: `signal_high * (1 + breakout_buffer_pct)`

Initial sell rules:

- Stop loss: intraday low reaches stop price
- Take profit: intraday high reaches take-profit price
- Trend exit: close below MA20
- Pattern exit: sell signal

Important conservative rule:

- If stop loss and take profit are both touched on the same daily bar, assume stop loss happened first.

### `src/costs.py`

Applies transaction costs.

Costs should exist from v1 because short-horizon strategies are sensitive to friction.

Recommended config fields:

```yaml
costs:
  US:
    buy_fee_pct: 0.001
    sell_fee_pct: 0.001
    sell_tax_pct: 0.0
    slippage_pct: 0.001
  KR:
    buy_fee_pct: 0.00015
    sell_fee_pct: 0.00015
    sell_tax_pct: 0.0015
    slippage_pct: 0.001
```

These are placeholders and must be updated to match the actual broker/tax regime.

### `src/portfolio.py`

Tracks portfolio state.

Initial fields:

- cash
- positions
- equity_curve
- trade_history

Phase 1 single-symbol mode can keep this simple.

### `src/risk.py`

Controls whether new positions are allowed.

Initial checks:

- max positions
- position size percentage
- max new positions per day
- market allocation limit

In single-symbol v1, most checks can be implemented but not heavily used.

### `src/backtester.py`

Coordinates the simulation.

Responsibilities:

- Receive prepared OHLCV DataFrame
- Run indicators
- Run patterns
- Run signals
- Apply execution rules
- Update portfolio
- Record trades
- Produce equity curve

It should not download data and should not know broker API details.

### `src/metrics.py`

Computes performance metrics.

Initial metrics:

- total return
- CAGR
- MDD
- win rate
- average win
- average loss
- profit factor
- trade count
- average holding days

Later additions:

- benchmark return
- excess return
- Sharpe ratio
- monthly returns
- rolling drawdown

### `src/report.py`

Prepares data for CLI and UI reports.

Responsibilities:

- Convert metrics dict to display table
- Format trade history
- Save backtest report CSV
- Save equity curve CSV
- Later generate HTML or PDF reports

### `src/broker/base.py`

Defines broker interface only.

No real trading in Phase 1.

### `src/broker/paper.py`

Internal paper broker.

Phase 2 only. In Phase 1, keep it as a minimal stub.

### `src/broker/kis.py`

Korea Investment & Securities API adapter.

Phase 3 or later. In Phase 1, keep as TODO/stub only.

## 5. Config Design

Initial `config.yaml` should include these sections:

```yaml
project:
  name: TradingProgram
  mode: backtest

data:
  start_date: "2018-01-01"
  end_date: "2025-12-31"
  timeframe: "1d"
  sample_file: data/sample/sample_ohlcv.csv

universe:
  us_file: data/universe/us_top100.csv
  kr_file: data/universe/kr_top80.csv

strategy:
  use_market_filter: false
  moving_average:
    short_window: 20
    long_window: 60
    slope_period: 1
  volume:
    window: 20
    multiplier: 1.2
  candle:
    body_avg_window: 20
  buy_patterns:
    - hammer
    - bullish_engulfing
    - morning_star
  sell_patterns:
    - bearish_engulfing
    - shooting_star

execution:
  breakout_buffer_pct: 0.001
  max_gap_up_pct: 0.03
  use_gap_filter: true
  same_day_stop_first: true

risk:
  initial_cash: 10000000
  max_positions: 10
  position_size_pct: 0.10
  max_new_positions_per_day: 3
  stop_loss_pct: -0.03
  take_profit_pct: 0.07
  market_allocation:
    US: 0.60
    KR: 0.40

costs:
  US:
    buy_fee_pct: 0.001
    sell_fee_pct: 0.001
    sell_tax_pct: 0.0
    slippage_pct: 0.001
  KR:
    buy_fee_pct: 0.00015
    sell_fee_pct: 0.00015
    sell_tax_pct: 0.0015
    slippage_pct: 0.001

broker:
  type: paper
```

## 6. Data Flow

```text
CSV/data source
  -> data_loader
  -> indicators
  -> patterns
  -> signals
  -> execution
  -> portfolio
  -> metrics
  -> reports/logs
```

UI data flow:

```text
Streamlit app.py
  -> config
  -> data_loader
  -> backtester
  -> metrics/report
  -> charts/tables/downloads
```

## 7. Phase 1 Implementation Order

1. Create folders and placeholder files.
2. Add `config.yaml` and `requirements.txt`.
3. Implement `config.py`.
4. Implement `indicators.py`.
5. Implement `patterns.py`.
6. Add unit tests for candle patterns.
7. Implement `signals.py`.
8. Implement `execution.py`.
9. Implement minimal single-symbol `backtester.py`.
10. Implement `metrics.py`.
11. Implement `report.py`.
12. Make `main.py` run on sample CSV.
13. Add `app.py` Streamlit UI for local backtest review.

## 8. Non-Negotiable Backtest Rules

- No same-day buy on a candle signal.
- No use of future rows in signal calculation.
- Use available next trading row, not calendar date plus one.
- Include costs from the first working backtest.
- If daily high and low hit both stop and target, assume the worse outcome.
- Keep raw candle pattern detection separate from trend/volume filters.
- Keep real broker API code out of Phase 1.
- UI must not send real orders in Phase 1.
- UI should display assumptions and costs used in the current backtest.

## 9. Main Risk in the Current Strategy

The trading logic is easy to implement, but the investment premise is weak until tested.

Common candle patterns plus moving averages are unlikely to provide durable excess return by themselves. The value of Phase 1 is not proving profitability. The value is creating a reliable test harness that can reject weak strategy assumptions quickly.

## 10. UI Roadmap

### Phase 1: Backtest Review UI

Purpose:

- Inspect local backtest results quickly
- Compare strategy parameter changes
- Find obvious bugs in signals, fills, and trade accounting

Screens:

- Backtest Setup
  - config file path
  - data file selector
  - symbol selector
  - date range
  - run button
- Summary
  - total return
  - CAGR
  - MDD
  - win rate
  - trade count
  - average holding days
- Charts
  - equity curve
  - drawdown curve
  - close price with buy/sell markers
- Tables
  - trade history
  - signal history
  - skipped signals with reason

### Phase 2: Paper Trading Monitor

Purpose:

- Monitor generated orders and paper positions
- Review what the system would do before real trading

Screens:

- Today signals
- Pending paper orders
- Paper positions
- Daily decision log
- Error log

### Phase 3: Real Trading Control Panel

Purpose:

- Operate small-capital real trading with explicit safety controls

Required controls:

- Read-only mode toggle
- Manual approval mode
- Max daily order amount
- Emergency stop
- Broker connection status
- Last sync time

Real trading UI must require explicit confirmation for every order until the system has passed a separate operating checklist.

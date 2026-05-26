from __future__ import annotations

import argparse
from pathlib import Path

from src.backtester import run_multi_symbol_backtest, run_single_symbol_backtest
from src.config import load_config
from src.data_loader import filter_ohlcv_by_universe, load_ohlcv_csv, load_universe_csv
from src.metrics import compute_metrics
from src.report import format_metrics, save_backtest_outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--market", default="US", choices=["US", "KR"])
    parser.add_argument("--multi", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    data_path = Path(config["data"]["sample_file"])
    df = load_ohlcv_csv(data_path)
    if args.multi:
        us_symbols = load_universe_csv(config["universe"]["us_file"])
        kr_symbols = load_universe_csv(config["universe"]["kr_file"])
        symbols = us_symbols + kr_symbols
        market_map = {symbol: "US" for symbol in us_symbols} | {symbol: "KR" for symbol in kr_symbols}
        df = filter_ohlcv_by_universe(df, symbols)
        if df.empty:
            raise RuntimeError("No OHLCV rows match the configured universe")
        result = run_multi_symbol_backtest(df, config, market_map)
    else:
        result = run_single_symbol_backtest(df, config, market=args.market)
    metrics = compute_metrics(result["equity_curve"], result["trades"], float(config["risk"]["initial_cash"]))
    save_backtest_outputs(result, metrics, "outputs/reports")
    print(format_metrics(metrics))


if __name__ == "__main__":
    main()

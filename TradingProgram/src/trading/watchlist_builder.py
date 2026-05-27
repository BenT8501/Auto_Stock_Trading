from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from src.data_loader import load_ohlcv_csv
from src.indicators import add_indicators
from src.patterns import add_patterns
from src.signals import add_signals
from src.trading.automation import load_recommendation_universe


def build_watchlist(config: dict, run_date: date | None = None, market: str | None = None) -> dict[str, pd.DataFrame]:
    run_date = run_date or date.today()
    prepared = prepare_universe_signals(config)
    latest = prepared.sort_values("date").groupby("symbol", as_index=False).tail(1).copy()
    if market and market.upper() != "ALL":
        latest = latest[latest["market"].astype(str).str.upper() == market.upper()]

    trend_candidates = latest[latest["trend_filter_pass"].astype(bool) & latest["volume_filter_pass"].astype(bool)].copy()
    setup_candidates = latest[latest["setup_signal"].astype(bool)].copy()
    watchlist = _build_watchlist_frame(setup_candidates, config, run_date)

    watchlist_dir = Path(config.get("watchlist", {}).get("output_dir", "data/watchlist"))
    results_dir = Path(config.get("results", {}).get("output_dir", "data/results"))
    watchlist_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    trend_candidates.to_csv(results_dir / f"trend_candidates_{run_date.isoformat()}.csv", index=False)
    setup_candidates.to_csv(watchlist_dir / f"setup_candidates_{run_date.isoformat()}.csv", index=False)
    watchlist.to_csv(watchlist_dir / f"watchlist_{run_date.isoformat()}.csv", index=False)

    return {
        "trend_candidates": trend_candidates,
        "setup_candidates": setup_candidates,
        "watchlist": watchlist,
    }


def prepare_universe_signals(config: dict) -> pd.DataFrame:
    ohlcv = load_ohlcv_csv(config["data"]["universe_ohlcv_file"])
    if ohlcv.empty:
        return pd.DataFrame()

    universe = pd.concat(
        [load_recommendation_universe(config, "KR"), load_recommendation_universe(config, "US")],
        ignore_index=True,
    )
    if universe.empty:
        return pd.DataFrame()

    universe["symbol"] = universe["symbol"].astype(str)
    ohlcv["symbol"] = ohlcv["symbol"].astype(str)
    ohlcv = ohlcv[ohlcv["symbol"].isin(set(universe["symbol"]))]
    if ohlcv.empty:
        return pd.DataFrame()

    prepared = add_signals(add_patterns(add_indicators(ohlcv, config)), config)
    metadata_columns = ["symbol", "name", "market", "exchange"]
    metadata = universe[[column for column in metadata_columns if column in universe.columns]].copy()
    return prepared.merge(metadata, on="symbol", how="left", suffixes=("", "_universe"))


def _build_watchlist_frame(setup_candidates: pd.DataFrame, config: dict, run_date: date) -> pd.DataFrame:
    if setup_candidates.empty:
        return pd.DataFrame(
            columns=[
                "setup_date",
                "trade_date",
                "market",
                "symbol",
                "name",
                "exchange",
                "pattern",
                "prev_open",
                "prev_high",
                "prev_low",
                "prev_close",
                "prev_volume",
                "ma20",
                "ma60",
                "ma20_slope",
                "volume_ma20",
                "trigger_price",
                "gap_limit_price",
                "stop_loss_price",
                "take_profit_price",
                "setup_signal",
                "trigger_signal",
            ]
        )

    execution = config.get("execution", {})
    monitor = config.get("realtime_monitor", {})
    risk = config.get("risk", {})
    breakout_buffer = float(monitor.get("breakout_buffer_pct", execution.get("breakout_buffer_pct", 0.001)))
    max_gap_up = float(monitor.get("max_gap_up_pct", execution.get("max_gap_up_pct", 0.03)))
    stop_loss_pct = float(risk.get("stop_loss_pct", -0.03))
    take_profit_pct = float(risk.get("take_profit_pct", 0.07))

    result = pd.DataFrame(
        {
            "setup_date": setup_candidates["date"],
            "trade_date": run_date.isoformat(),
            "market": setup_candidates.get("market", "US"),
            "symbol": setup_candidates["symbol"].astype(str),
            "name": setup_candidates.get("name", setup_candidates["symbol"]).astype(str),
            "exchange": setup_candidates.get("exchange", ""),
            "pattern": setup_candidates["buy_pattern"],
            "prev_open": setup_candidates["open"].astype(float),
            "prev_high": setup_candidates["high"].astype(float),
            "prev_low": setup_candidates["low"].astype(float),
            "prev_close": setup_candidates["close"].astype(float),
            "prev_volume": setup_candidates["volume"].astype(float),
            "ma20": setup_candidates["ma_short"].astype(float),
            "ma60": setup_candidates["ma_long"].astype(float),
            "ma20_slope": setup_candidates["ma_short_slope"].astype(float),
            "volume_ma20": setup_candidates["volume_ma"].astype(float),
            "trigger_price": setup_candidates["high"].astype(float) * (1 + breakout_buffer),
            "gap_limit_price": setup_candidates["high"].astype(float) * (1 + max_gap_up),
            "stop_loss_price": setup_candidates["high"].astype(float) * (1 + breakout_buffer) * (1 + stop_loss_pct),
            "take_profit_price": setup_candidates["high"].astype(float) * (1 + breakout_buffer) * (1 + take_profit_pct),
            "setup_signal": True,
            "trigger_signal": False,
        }
    )
    return result.sort_values(["market", "symbol"]).reset_index(drop=True)

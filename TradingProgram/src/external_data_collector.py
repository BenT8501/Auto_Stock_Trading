from __future__ import annotations

from datetime import date, timedelta
import os
from pathlib import Path

import pandas as pd

from src.data_loader import load_universe_frame


def collect_external_universe_ohlcv(
    config: dict,
    *,
    output_path: str | Path | None = None,
    history_days: int | None = None,
    limit_per_market: int | None = None,
) -> pd.DataFrame:
    _prepare_network_environment()
    history_days = history_days or int(config["strategy"]["data_window"]["history_days"])
    output_path = output_path or config["data"]["universe_ohlcv_file"]
    start = date.today() - timedelta(days=history_days)
    end = date.today() + timedelta(days=1)

    frames = []
    kr = _active_ranked(load_universe_frame(config["universe"]["kr_file"]), limit_per_market)
    us = _active_ranked(load_universe_frame(config["universe"]["us_file"]), limit_per_market)

    if not us.empty:
        frames.append(fetch_yfinance_ohlcv(us["symbol"].astype(str).tolist(), start.isoformat(), end.isoformat()))
    if not kr.empty:
        frames.append(fetch_pykrx_ohlcv(kr["symbol"].astype(str).tolist(), start.strftime("%Y%m%d"), end.strftime("%Y%m%d")))

    data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume"])
    data = data.dropna(subset=["date", "symbol", "open", "high", "low", "close", "volume"])
    data = data.sort_values(["symbol", "date"]).reset_index(drop=True)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output, index=False)
    return data


def _prepare_network_environment() -> None:
    for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
        os.environ.pop(key, None)
    mpl_dir = Path("outputs/matplotlib_cache")
    mpl_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_dir.resolve()))


def fetch_yfinance_ohlcv(symbols: list[str], start: str, end: str) -> pd.DataFrame:
    import yfinance as yf

    frames = []
    for symbol in symbols:
        raw = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False)
        if raw.empty:
            continue
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [col[0] for col in raw.columns]
        frame = raw.reset_index()
        frame = frame.rename(columns={frame.columns[0]: "date"})
        frame = frame.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        frame["symbol"] = symbol
        frames.append(frame[["date", "symbol", "open", "high", "low", "close", "volume"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def fetch_pykrx_ohlcv(symbols: list[str], start: str, end: str) -> pd.DataFrame:
    from pykrx import stock

    frames = []
    for symbol in symbols:
        raw = stock.get_market_ohlcv_by_date(start, end, symbol)
        if raw.empty:
            continue
        frame = raw.reset_index().rename(
            columns={
                "날짜": "date",
                "시가": "open",
                "고가": "high",
                "저가": "low",
                "종가": "close",
                "거래량": "volume",
            }
        )
        frame["symbol"] = symbol
        frames.append(frame[["date", "symbol", "open", "high", "low", "close", "volume"]])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _active_ranked(df: pd.DataFrame, limit: int | None) -> pd.DataFrame:
    active = df["active"].astype(str).str.lower().isin({"true", "1", "yes", "y"})
    result = df[active].sort_values("rank")
    return result.head(limit) if limit else result

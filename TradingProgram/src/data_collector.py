from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from src.broker.kis import KisBroker
from src.data_loader import load_universe_frame


@dataclass(frozen=True)
class CollectionResult:
    data: pd.DataFrame
    errors: pd.DataFrame


def collect_kis_universe_ohlcv(
    config: dict,
    broker: KisBroker,
    *,
    output_path: str | Path = "data/processed/kis_universe_ohlcv.csv",
    history_days: int | None = None,
    limit_per_market: int | None = None,
) -> CollectionResult:
    history_days = history_days or int(config["strategy"]["data_window"]["history_days"])
    end = date.today()
    start = end - timedelta(days=history_days)
    start_yyyymmdd = start.strftime("%Y%m%d")
    end_yyyymmdd = end.strftime("%Y%m%d")

    frames: list[pd.DataFrame] = []
    errors: list[dict[str, Any]] = []

    kr_universe = _active_ranked(load_universe_frame(config["universe"]["kr_file"]), limit_per_market)
    us_universe = _active_ranked(load_universe_frame(config["universe"]["us_file"]), limit_per_market)

    for row in kr_universe.to_dict("records"):
        symbol = str(row["symbol"])
        try:
            frame = fetch_domestic_history(broker, symbol, start_yyyymmdd, end_yyyymmdd)
            frames.append(frame)
        except Exception as exc:
            errors.append({"market": "KR", "symbol": symbol, "error": str(exc)})

    for row in us_universe.to_dict("records"):
        symbol = str(row["symbol"])
        exchange = str(row.get("exchange", "NAS") or "NAS")
        try:
            frame = fetch_overseas_history(broker, symbol, exchange, start_yyyymmdd, end_yyyymmdd)
            frames.append(frame)
        except Exception as exc:
            errors.append({"market": "US", "symbol": symbol, "exchange": exchange, "error": str(exc)})

    data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume"])
    data = data.dropna(subset=["date", "symbol", "open", "high", "low", "close", "volume"])
    data = data.sort_values(["symbol", "date"]).reset_index(drop=True)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output, index=False)
    errors_df = pd.DataFrame(errors)
    errors_df.to_csv(output.with_name(output.stem + "_errors.csv"), index=False)
    return CollectionResult(data=data, errors=errors_df)


def fetch_domestic_history(broker: KisBroker, symbol: str, start_yyyymmdd: str, end_yyyymmdd: str, max_pages: int = 6) -> pd.DataFrame:
    frames = []
    cursor = end_yyyymmdd
    start_ts = pd.to_datetime(start_yyyymmdd, format="%Y%m%d")
    for _ in range(max_pages):
        payload = broker.get_domestic_daily_ohlcv(symbol, start_yyyymmdd, cursor)
        frame = normalize_domestic_daily_ohlcv(payload, symbol)
        if frame.empty:
            break
        frames.append(frame)
        oldest = frame["date"].min()
        if pd.isna(oldest) or oldest <= start_ts:
            break
        cursor = (oldest - pd.Timedelta(days=1)).strftime("%Y%m%d")
    return _merge_history_frames(frames, start_ts)


def fetch_overseas_history(
    broker: KisBroker,
    symbol: str,
    exchange: str,
    start_yyyymmdd: str,
    end_yyyymmdd: str,
    max_pages: int = 6,
) -> pd.DataFrame:
    frames = []
    cursor = end_yyyymmdd
    start_ts = pd.to_datetime(start_yyyymmdd, format="%Y%m%d")
    for _ in range(max_pages):
        payload = broker.get_overseas_daily_ohlcv(symbol, exchange, cursor)
        frame = normalize_overseas_daily_ohlcv(payload, symbol)
        if frame.empty:
            break
        frames.append(frame)
        oldest = frame["date"].min()
        if pd.isna(oldest) or oldest <= start_ts:
            break
        cursor = (oldest - pd.Timedelta(days=1)).strftime("%Y%m%d")
    return _merge_history_frames(frames, start_ts)


def normalize_domestic_daily_ohlcv(payload: dict[str, Any], symbol: str) -> pd.DataFrame:
    rows = _rows(payload)
    normalized = []
    for row in rows:
        normalized.append(
            {
                "date": pd.to_datetime(_first(row, ["stck_bsop_date", "date"]), format="%Y%m%d", errors="coerce"),
                "symbol": symbol,
                "open": _number(_first(row, ["stck_oprc", "open"])),
                "high": _number(_first(row, ["stck_hgpr", "high"])),
                "low": _number(_first(row, ["stck_lwpr", "low"])),
                "close": _number(_first(row, ["stck_clpr", "close"])),
                "volume": _number(_first(row, ["acml_vol", "volume"])),
            }
        )
    return pd.DataFrame(normalized)


def normalize_overseas_daily_ohlcv(payload: dict[str, Any], symbol: str) -> pd.DataFrame:
    rows = _rows(payload)
    normalized = []
    for row in rows:
        normalized.append(
            {
                "date": pd.to_datetime(_first(row, ["xymd", "stck_bsop_date", "date"]), format="%Y%m%d", errors="coerce"),
                "symbol": symbol,
                "open": _number(_first(row, ["open", "ovrs_nmix_oprc"])),
                "high": _number(_first(row, ["high", "ovrs_nmix_hgpr"])),
                "low": _number(_first(row, ["low", "ovrs_nmix_lwpr"])),
                "close": _number(_first(row, ["clos", "last", "ovrs_nmix_prpr"])),
                "volume": _number(_first(row, ["tvol", "acml_vol"])),
            }
        )
    return pd.DataFrame(normalized)


def _active_ranked(df: pd.DataFrame, limit: int | None) -> pd.DataFrame:
    active = df["active"].astype(str).str.lower().isin({"true", "1", "yes", "y"})
    result = df[active].sort_values("rank")
    return result.head(limit) if limit else result


def _merge_history_frames(frames: list[pd.DataFrame], start_ts: pd.Timestamp) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=["date", "symbol", "open", "high", "low", "close", "volume"])
    result = pd.concat(frames, ignore_index=True)
    result = result[result["date"] >= start_ts]
    return result.drop_duplicates(subset=["date", "symbol"]).sort_values(["symbol", "date"]).reset_index(drop=True)


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ["output2", "output", "output1"]:
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _first(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in {None, ""}:
            return value
    return None


def _number(value: Any) -> float:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0

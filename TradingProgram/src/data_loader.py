from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_OHLCV_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume"]


def load_ohlcv_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return normalize_ohlcv(df)


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(col).strip().lower() for col in normalized.columns]

    missing = [col for col in REQUIRED_OHLCV_COLUMNS if col not in normalized.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {', '.join(missing)}")

    normalized = normalized[REQUIRED_OHLCV_COLUMNS].copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["symbol"] = normalized["symbol"].astype(str).map(_normalize_symbol)

    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce")

    normalized = normalized.dropna(subset=REQUIRED_OHLCV_COLUMNS)
    normalized = normalized.sort_values(["symbol", "date"]).reset_index(drop=True)
    return normalized


def load_universe_csv(path: str | Path) -> list[str]:
    df = pd.read_csv(path, dtype={"symbol": str})
    if "symbol" not in df.columns:
        raise ValueError("Universe CSV must include a 'symbol' column")
    if "active" in df.columns:
        active = df["active"].astype(str).str.lower().isin({"true", "1", "yes", "y"})
        df = df[active]
    if "rank" in df.columns:
        df = df.sort_values("rank")
    return df["symbol"].dropna().astype(str).map(_normalize_symbol).tolist()


def load_universe_frame(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"symbol": str})
    if "symbol" not in df.columns:
        raise ValueError("Universe CSV must include a 'symbol' column")
    if "active" not in df.columns:
        df["active"] = True
    if "rank" not in df.columns:
        df["rank"] = range(1, len(df) + 1)
    if "market" not in df.columns:
        df["market"] = ""
    df["symbol"] = df["symbol"].astype(str).map(_normalize_symbol)
    return df


def filter_ohlcv_by_universe(df: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    normalized_symbols = {_normalize_symbol(symbol) for symbol in symbols}
    return df[df["symbol"].astype(str).map(_normalize_symbol).isin(normalized_symbols)].copy()


def _normalize_symbol(symbol: str) -> str:
    value = str(symbol).strip()
    if value.isdigit():
        return value.zfill(6)
    return value

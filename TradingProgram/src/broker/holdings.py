from __future__ import annotations

from typing import Any

import pandas as pd


DISPLAY_COLUMNS = ["시장", "이름", "코드", "수량", "현재 가격", "평가 금액"]


def normalize_domestic_holdings(response: dict[str, Any]) -> pd.DataFrame:
    rows = _as_rows(response.get("output1") or response.get("output") or [])
    normalized = []
    for row in rows:
        quantity = _number(_first(row, ["hldg_qty", "ord_psbl_qty"]))
        if quantity <= 0:
            continue
        normalized.append(
            {
                "시장": "국내",
                "이름": _first(row, ["prdt_name", "hts_kor_isnm", "item_name"]),
                "코드": _first(row, ["pdno", "stck_shrn_iscd", "isu_cd"]),
                "수량": quantity,
                "현재 가격": _number(_first(row, ["prpr", "stck_prpr", "now_pric"])),
                "평가 금액": _number(_first(row, ["evlu_amt", "stck_evlu_amt"])),
                "_raw": row,
            }
        )
    return pd.DataFrame(normalized)


def normalize_overseas_holdings(response: dict[str, Any]) -> pd.DataFrame:
    rows = _as_rows(response.get("output1") or response.get("output") or [])
    normalized = []
    for row in rows:
        quantity = _number(_first(row, ["ovrs_cblc_qty", "cblc_qty", "ord_psbl_qty"]))
        if quantity <= 0:
            continue
        normalized.append(
            {
                "시장": "해외",
                "이름": _first(row, ["ovrs_item_name", "prdt_name", "item_name"]),
                "코드": _first(row, ["ovrs_pdno", "pdno", "symb"]),
                "수량": quantity,
                "현재 가격": _number(_first(row, ["now_pric", "ovrs_now_pric", "last"])),
                "평가 금액": _number(_first(row, ["ovrs_stck_evlu_amt", "frcr_evlu_amt2", "evlu_amt"])),
                "_raw": row,
            }
        )
    return pd.DataFrame(normalized)


def display_holdings(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=DISPLAY_COLUMNS)
    return df[DISPLAY_COLUMNS].copy()


def _as_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _first(row: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = row.get(key)
        if value not in {None, ""}:
            return str(value)
    return ""


def _number(value: Any) -> float:
    if value in {None, ""}:
        return 0.0
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return 0.0

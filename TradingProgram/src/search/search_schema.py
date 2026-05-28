from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchFilters:
    market: str | None = None
    keyword: str | None = None
    max_rank: int | None = None
    min_volume_ratio: float | None = None
    close_above_ma20: bool | None = None
    ma20_above_ma60: bool | None = None
    patterns: list[str] = field(default_factory=list)
    latest_only: bool = True
    max_results: int | None = None

    @classmethod
    def from_dict(cls, values: dict) -> "SearchFilters":
        patterns = values.get("patterns") or []
        if isinstance(patterns, str):
            patterns = [patterns]
        return cls(
            market=_optional_upper(values.get("market")),
            keyword=_optional_str(values.get("keyword")),
            max_rank=_optional_int(values.get("max_rank") or values.get("rank")),
            min_volume_ratio=_optional_float(values.get("min_volume_ratio") or values.get("volume_ratio")),
            close_above_ma20=_optional_bool(values.get("close_above_ma20")),
            ma20_above_ma60=_optional_bool(values.get("ma20_above_ma60")),
            patterns=[str(pattern) for pattern in patterns],
            latest_only=_optional_bool(values.get("latest_only"), default=True),
            max_results=_optional_int(values.get("max_results")),
        )

    def to_dict(self) -> dict:
        return {
            "market": self.market,
            "keyword": self.keyword,
            "max_rank": self.max_rank,
            "min_volume_ratio": self.min_volume_ratio,
            "close_above_ma20": self.close_above_ma20,
            "ma20_above_ma60": self.ma20_above_ma60,
            "patterns": self.patterns,
            "latest_only": self.latest_only,
            "max_results": self.max_results,
        }


def _optional_upper(value) -> str | None:
    if value in {None, ""}:
        return None
    normalized = str(value).upper()
    return None if normalized == "ALL" else normalized


def _optional_str(value) -> str | None:
    if value in {None, ""}:
        return None
    return str(value).strip()


def _optional_int(value) -> int | None:
    if value in {None, ""}:
        return None
    return int(value)


def _optional_float(value) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def _optional_bool(value, default: bool | None = None) -> bool | None:
    if value in {None, ""}:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}

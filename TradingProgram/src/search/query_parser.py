from __future__ import annotations

import re


PATTERN_ALIASES = {
    "hammer": "hammer",
    "망치": "hammer",
    "bullish_engulfing": "bullish_engulfing",
    "상승장악": "bullish_engulfing",
    "상승 장악": "bullish_engulfing",
    "morning_star": "morning_star",
    "샛별": "morning_star",
}


def parse_search_query(query: str, defaults: dict | None = None) -> dict:
    defaults = defaults or {}
    text = query.strip()
    filters = _normalize_defaults(defaults)
    if not text:
        return filters

    if "=" in text:
        filters.update(_parse_key_value(text))
    filters.update(_parse_natural_language(text))
    if not _has_explicit_search_term(filters, defaults) and _looks_like_plain_keyword(text):
        filters["keyword"] = text
    return filters


def _normalize_defaults(defaults: dict) -> dict:
    result = dict(defaults)
    if "market" not in result and result.get("default_market"):
        result["market"] = result["default_market"]
    return result


def _parse_key_value(text: str) -> dict:
    result = {}
    for token in re.split(r"[\s,]+", text):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key in {"market", "시장"}:
            result["market"] = _market(value)
        elif key in {"keyword", "키워드", "name", "symbol"}:
            result["keyword"] = value
        elif key in {"rank", "max_rank"}:
            result["max_rank"] = int(value)
        elif key in {"volume_ratio", "min_volume_ratio"}:
            result["min_volume_ratio"] = float(value)
        elif key in {"close_above_ma20"}:
            result["close_above_ma20"] = _bool(value)
        elif key in {"ma20_above_ma60"}:
            result["ma20_above_ma60"] = _bool(value)
        elif key in {"latest_only"}:
            result["latest_only"] = _bool(value)
        elif key in {"max_results"}:
            result["max_results"] = int(value)
        elif key in {"pattern", "patterns"}:
            result["patterns"] = [_pattern(value)]
    return result


def _parse_natural_language(text: str) -> dict:
    result = {}
    lowered = text.lower()
    if "한국" in text or "국내" in text or "kr" in lowered:
        result["market"] = "KR"
    elif "미국" in text or "us" in lowered:
        result["market"] = "US"

    volume_match = re.search(r"거래량[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*(?:배|이상|초과)?", text)
    if volume_match:
        result["min_volume_ratio"] = float(volume_match.group(1))
    elif "거래량" in text:
        result.setdefault("min_volume_ratio", 1.2)

    rank_match = re.search(r"(?:상위|rank)\s*([0-9]+)", text, flags=re.IGNORECASE)
    if rank_match:
        result["max_rank"] = int(rank_match.group(1))

    ma20_terms = ("ma20" in lowered) or ("20일" in text) or ("20선" in text) or ("20일선" in text)
    ma60_terms = ("ma60" in lowered) or ("60일" in text) or ("60선" in text) or ("60일선" in text)
    if ma20_terms and ("위" in text or "상회" in text or "above" in lowered):
        result["close_above_ma20"] = True
    if ma20_terms and ma60_terms and (">" in text or "위" in text or "상회" in text):
        result["ma20_above_ma60"] = True

    patterns = []
    for alias, pattern in PATTERN_ALIASES.items():
        if alias in lowered or alias in text:
            patterns.append(pattern)
    if patterns:
        result["patterns"] = sorted(set(patterns))
    keyword = _extract_keyword(text)
    if keyword:
        result["keyword"] = keyword
    return result


def _market(value: str) -> str:
    lowered = value.lower()
    if lowered in {"kr", "korea", "한국", "국내"}:
        return "KR"
    if lowered in {"us", "usa", "미국"}:
        return "US"
    return value.upper()


def _pattern(value: str) -> str:
    return PATTERN_ALIASES.get(value.lower(), value)


def _bool(value: str) -> bool:
    return value.lower() in {"true", "1", "yes", "y", "on"}


def _extract_keyword(text: str) -> str | None:
    quoted = re.search(r"['\"]([^'\"]+)['\"]", text)
    if quoted:
        return quoted.group(1).strip()
    match = re.search(r"(?:키워드|이름|회사|종목명|symbol|name)\s*[:=]?\s*([A-Za-z0-9가-힣.& -]+)", text, flags=re.IGNORECASE)
    if match:
        value = match.group(1).strip()
        for stop in ["중", "중에서", "검색", "찾아", "찾기"]:
            value = value.replace(stop, "").strip()
        return value or None
    return None


def _looks_like_plain_keyword(text: str) -> bool:
    if not text or len(text) > 40:
        return False
    blocked_terms = ["거래량", "ma20", "ma60", "20일", "60일", "위", "이상", "초과", "패턴", "상위"]
    lowered = text.lower()
    return not any(term in lowered or term in text for term in blocked_terms)


def _has_explicit_search_term(filters: dict, defaults: dict | None) -> bool:
    default_keys = set((defaults or {}).keys())
    meaningful_keys = set(filters.keys()) - default_keys - {"default_market", "latest_only", "max_results", "market"}
    return bool(meaningful_keys)

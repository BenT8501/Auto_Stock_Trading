from __future__ import annotations

from src.search.query_parser import parse_search_query


def test_parse_korean_volume_and_ma_query() -> None:
    result = parse_search_query("한국 종목 중 거래량 1.2배 이상이고 MA20 위에 있는 종목")

    assert result["market"] == "KR"
    assert result["min_volume_ratio"] == 1.2
    assert result["close_above_ma20"] is True


def test_parse_key_value_query() -> None:
    result = parse_search_query("market=US volume_ratio=1.5 close_above_ma20=true max_results=10")

    assert result["market"] == "US"
    assert result["min_volume_ratio"] == 1.5
    assert result["close_above_ma20"] is True
    assert result["max_results"] == 10


def test_default_market_maps_to_market() -> None:
    result = parse_search_query("", {"default_market": "ALL", "latest_only": True})

    assert result["market"] == "ALL"
    assert result["latest_only"] is True


def test_parse_korean_moving_average_terms() -> None:
    result = parse_search_query("국내 20일선 위 거래량 1.3 이상")

    assert result["market"] == "KR"
    assert result["close_above_ma20"] is True
    assert result["min_volume_ratio"] == 1.3


def test_parse_keyword_query() -> None:
    result = parse_search_query("회사 Apple 검색")

    assert result["keyword"] == "Apple"


def test_plain_text_becomes_keyword_search() -> None:
    result = parse_search_query("삼성", {"default_market": "ALL", "latest_only": True})

    assert result["keyword"] == "삼성"
    assert result["market"] == "ALL"

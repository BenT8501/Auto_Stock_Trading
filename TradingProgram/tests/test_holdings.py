from __future__ import annotations

from src.broker.holdings import display_holdings, normalize_domestic_holdings, normalize_overseas_holdings


def test_normalize_domestic_holdings() -> None:
    response = {
        "output1": [
            {
                "prdt_name": "삼성전자",
                "pdno": "005930",
                "hldg_qty": "3",
                "prpr": "70000",
                "evlu_amt": "210000",
            }
        ]
    }

    result = normalize_domestic_holdings(response)

    assert result.loc[0, "시장"] == "국내"
    assert result.loc[0, "이름"] == "삼성전자"
    assert result.loc[0, "코드"] == "005930"
    assert result.loc[0, "수량"] == 3
    assert result.loc[0, "현재 가격"] == 70000
    assert result.loc[0, "평가 금액"] == 210000


def test_normalize_overseas_holdings() -> None:
    response = {
        "output1": [
            {
                "ovrs_item_name": "APPLE INC",
                "ovrs_pdno": "AAPL",
                "ovrs_cblc_qty": "2",
                "now_pric": "190.5",
                "ovrs_stck_evlu_amt": "381.0",
            }
        ]
    }

    result = normalize_overseas_holdings(response)

    assert result.loc[0, "시장"] == "해외"
    assert result.loc[0, "이름"] == "APPLE INC"
    assert result.loc[0, "코드"] == "AAPL"
    assert result.loc[0, "수량"] == 2
    assert result.loc[0, "현재 가격"] == 190.5
    assert result.loc[0, "평가 금액"] == 381.0


def test_display_holdings_hides_raw_payload() -> None:
    response = {"output1": [{"prdt_name": "삼성전자", "pdno": "005930", "hldg_qty": "1"}]}
    result = display_holdings(normalize_domestic_holdings(response))
    assert "_raw" not in result.columns

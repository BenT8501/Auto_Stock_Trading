from __future__ import annotations

from src.broker.kis import KisBroker


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def post(self, url: str, json: dict, timeout: int) -> FakeResponse:
        self.calls.append({"method": "POST", "url": url, "json": json, "timeout": timeout})
        return FakeResponse({"rt_cd": "0", "access_token": "token"})

    def get(self, url: str, headers: dict, params: dict, timeout: int) -> FakeResponse:
        self.calls.append({"method": "GET", "url": url, "headers": headers, "params": params, "timeout": timeout})
        return FakeResponse({"rt_cd": "0", "output": {"ok": True}})


def test_kis_price_request_is_read_only() -> None:
    session = FakeSession()
    broker = KisBroker(
        base_url="https://example.test",
        app_key="app",
        app_secret="secret",
        account_no="12345678",
        session=session,
    )

    result = broker.get_domestic_price("005930")

    assert result["output"]["ok"]
    assert session.calls[0]["method"] == "POST"
    assert session.calls[0]["url"].endswith("/oauth2/tokenP")
    assert session.calls[1]["method"] == "GET"
    assert session.calls[1]["url"].endswith("/uapi/domestic-stock/v1/quotations/inquire-price")
    assert session.calls[1]["headers"]["tr_id"] == "FHKST01010100"
    assert session.calls[1]["params"]["FID_INPUT_ISCD"] == "005930"


def test_kis_submit_order_remains_disabled() -> None:
    broker = KisBroker(
        base_url="https://example.test",
        app_key="app",
        app_secret="secret",
        account_no="12345678",
    )

    try:
        broker.submit_order({"symbol": "005930"})
    except RuntimeError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("submit_order must remain disabled")


def test_kis_overseas_price_request_is_read_only() -> None:
    session = FakeSession()
    broker = KisBroker(
        base_url="https://example.test",
        app_key="app",
        app_secret="secret",
        account_no="12345678",
        session=session,
    )

    result = broker.get_overseas_price("AAPL", "NAS")

    assert result["output"]["ok"]
    assert session.calls[0]["method"] == "POST"
    assert session.calls[1]["method"] == "GET"
    assert session.calls[1]["url"].endswith("/uapi/overseas-price/v1/quotations/price")
    assert session.calls[1]["headers"]["tr_id"] == "HHDFS00000300"
    assert session.calls[1]["params"]["EXCD"] == "NAS"
    assert session.calls[1]["params"]["SYMB"] == "AAPL"


def test_kis_overseas_balance_request_uses_demo_tr_id_for_virtual() -> None:
    session = FakeSession()
    broker = KisBroker(
        base_url="https://example.test",
        app_key="app",
        app_secret="secret",
        account_no="12345678",
        use_virtual=True,
        session=session,
    )

    broker.get_overseas_balance()

    assert session.calls[1]["url"].endswith("/uapi/overseas-stock/v1/trading/inquire-balance")
    assert session.calls[1]["headers"]["tr_id"] == "VTTS3012R"
    assert session.calls[1]["params"]["OVRS_EXCG_CD"] == "NASD"
    assert session.calls[1]["params"]["TR_CRCY_CD"] == "USD"

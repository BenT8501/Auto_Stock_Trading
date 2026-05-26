from __future__ import annotations

import os
import time
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from src.broker.base import BrokerInterface


@dataclass(frozen=True)
class KisCredentials:
    app_key: str
    app_secret: str
    account_no: str
    account_product_code: str


class KisBroker(BrokerInterface):
    def __init__(
        self,
        *,
        base_url: str,
        app_key: str,
        app_secret: str,
        account_no: str,
        account_product_code: str = "01",
        use_virtual: bool = True,
        session: requests.Session | None = None,
        token_cache_enabled: bool | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.credentials = KisCredentials(app_key, app_secret, account_no, account_product_code)
        self.use_virtual = use_virtual
        self.session = session or requests.Session()
        self.session.trust_env = False
        self.token_cache_enabled = (session is None) if token_cache_enabled is None else token_cache_enabled
        self._access_token: str | None = None
        self._access_token_expires_at = 0.0
        self._last_request_at = 0.0
        self.min_request_interval_seconds = 1.05

    @classmethod
    def from_config(cls, config: dict, env_path: str | Path = ".env") -> "KisBroker":
        load_env_file(env_path)
        broker_config = config["broker"]["kis"]
        use_virtual = bool(broker_config.get("use_virtual", True))
        base_url = broker_config["virtual_base_url"] if use_virtual else broker_config["base_url"]
        return cls(
            base_url=base_url,
            app_key=_required_env("KIS_APP_KEY"),
            app_secret=_required_env("KIS_APP_SECRET"),
            account_no=_required_env("KIS_ACCOUNT_NO"),
            account_product_code=os.getenv("KIS_ACCOUNT_PRODUCT_CODE", "01"),
            use_virtual=use_virtual,
        )

    def submit_order(self, order: dict) -> dict:
        raise RuntimeError("KIS order submission is disabled. Use manual approval with paper mode first.")

    def issue_access_token(self) -> str:
        if self._access_token and time.time() < self._access_token_expires_at:
            return self._access_token
        if self.token_cache_enabled:
            cached = self._load_cached_token()
            if cached is not None:
                self._access_token = cached["access_token"]
                self._access_token_expires_at = float(cached["expires_at"])
                return self._access_token
        self._throttle()
        response = self.session.post(
            f"{self.base_url}/oauth2/tokenP",
            json={
                "grant_type": "client_credentials",
                "appkey": self.credentials.app_key,
                "appsecret": self.credentials.app_secret,
            },
            timeout=10,
        )
        payload = _parse_response(response)
        token = payload.get("access_token")
        if not token:
            raise RuntimeError(f"KIS token response did not include access_token: {payload}")
        self._access_token = str(token)
        self._access_token_expires_at = time.time() + _token_ttl_seconds(payload)
        if self.token_cache_enabled:
            self._save_cached_token(self._access_token, self._access_token_expires_at)
        return self._access_token

    def get_domestic_price(self, symbol: str) -> dict[str, Any]:
        self._throttle()
        response = self.session.get(
            f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price",
            headers=self._headers("FHKST01010100"),
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
            },
            timeout=10,
        )
        return _parse_response(response)

    def get_domestic_balance(self) -> dict[str, Any]:
        tr_id = "VTTC8434R" if self.use_virtual else "TTTC8434R"
        self._throttle()
        response = self.session.get(
            f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance",
            headers=self._headers(tr_id),
            params={
                "CANO": self.credentials.account_no,
                "ACNT_PRDT_CD": self.credentials.account_product_code,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            },
            timeout=10,
        )
        return _parse_response(response)

    def get_domestic_daily_ohlcv(self, symbol: str, start_date: str, end_date: str) -> dict[str, Any]:
        self._throttle()
        response = self.session.get(
            f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
            headers=self._headers("FHKST03010100"),
            params={
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_INPUT_DATE_1": start_date,
                "FID_INPUT_DATE_2": end_date,
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            },
            timeout=10,
        )
        return _parse_response(response)

    def get_overseas_price(self, symbol: str, exchange: str = "NAS") -> dict[str, Any]:
        self._throttle()
        response = self.session.get(
            f"{self.base_url}/uapi/overseas-price/v1/quotations/price",
            headers=self._headers("HHDFS00000300"),
            params={
                "AUTH": "",
                "EXCD": exchange,
                "SYMB": symbol.upper(),
            },
            timeout=10,
        )
        return _parse_response(response)

    def get_overseas_price_detail(self, symbol: str, exchange: str = "NAS") -> dict[str, Any]:
        self._throttle()
        response = self.session.get(
            f"{self.base_url}/uapi/overseas-price/v1/quotations/price-detail",
            headers=self._headers("HHDFS76200200"),
            params={
                "AUTH": "",
                "EXCD": exchange,
                "SYMB": symbol.upper(),
            },
            timeout=10,
        )
        return _parse_response(response)

    def get_overseas_daily_ohlcv(self, symbol: str, exchange: str = "NAS", end_date: str = "") -> dict[str, Any]:
        self._throttle()
        response = self.session.get(
            f"{self.base_url}/uapi/overseas-price/v1/quotations/dailyprice",
            headers=self._headers("HHDFS76240000"),
            params={
                "AUTH": "",
                "EXCD": exchange,
                "SYMB": symbol.upper(),
                "GUBN": "0",
                "BYMD": end_date,
                "MODP": "0",
            },
            timeout=10,
        )
        return _parse_response(response)

    def get_overseas_balance(self, exchange: str = "NASD", currency: str = "USD") -> dict[str, Any]:
        tr_id = "VTTS3012R" if self.use_virtual else "TTTS3012R"
        self._throttle()
        response = self.session.get(
            f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance",
            headers=self._headers(tr_id),
            params={
                "CANO": self.credentials.account_no,
                "ACNT_PRDT_CD": self.credentials.account_product_code,
                "OVRS_EXCG_CD": exchange,
                "TR_CRCY_CD": currency,
                "CTX_AREA_FK200": "",
                "CTX_AREA_NK200": "",
            },
            timeout=10,
        )
        return _parse_response(response)

    def _headers(self, tr_id: str) -> dict[str, str]:
        token = self._access_token or self.issue_access_token()
        return {
            "authorization": f"Bearer {token}",
            "appkey": self.credentials.app_key,
            "appsecret": self.credentials.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_at
        wait = self.min_request_interval_seconds - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.time()

    def _token_cache_path(self) -> Path:
        key = hashlib.sha256(f"{self.base_url}:{self.credentials.app_key}".encode("utf-8")).hexdigest()[:16]
        path = Path("outputs") / f"kis_token_{key}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _load_cached_token(self) -> dict[str, Any] | None:
        path = self._token_cache_path()
        if not path.exists():
            return None
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if not cached.get("access_token") or float(cached.get("expires_at", 0)) <= time.time() + 60:
            return None
        return cached

    def _save_cached_token(self, token: str, expires_at: float) -> None:
        self._token_cache_path().write_text(
            json.dumps({"access_token": token, "expires_at": expires_at}, ensure_ascii=False),
            encoding="utf-8",
        )


def load_env_file(path: str | Path) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _parse_response(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"KIS response was not JSON: HTTP {response.status_code}") from exc
    if payload.get("msg_cd") == "EGW00201":
        raise RuntimeError("KIS API 호출 제한: 초당 거래건수를 초과했습니다. 잠시 후 다시 시도하세요.")
    if response.status_code >= 400:
        raise RuntimeError(f"KIS HTTP error {response.status_code}: {payload}")
    if payload.get("rt_cd") not in {None, "0"}:
        raise RuntimeError(f"KIS API error: {payload}")
    return payload


def _token_ttl_seconds(payload: dict[str, Any]) -> float:
    raw = payload.get("expires_in")
    try:
        ttl = float(raw)
    except (TypeError, ValueError):
        ttl = 60 * 60 * 12
    return max(60.0, ttl - 60.0)

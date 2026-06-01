"""
Thin wrapper around the Binance Futures Testnet REST API.

Keeps all the request-signing boilerplate in one place so the rest of
the code doesn't have to think about it.
"""

import hashlib
import hmac
import time
from urllib.parse import urlencode

import requests

from .logging_config import setup_logging

BASE_URL = "https://demo-fapi.binance.com"

logger = setup_logging()


class BinanceAPIError(Exception):
    """Raised when Binance returns an error code in the response body."""
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg
        super().__init__(f"Binance error {code}: {msg}")


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded",
        })

    # ------------------------------------------------------------------ #
    # internals                                                            #
    # ------------------------------------------------------------------ #

    def _sign(self, params: dict) -> dict:
        params["recvWindow"] = 60000
        params["timestamp"] = int(time.time() * 1000)
        query = urlencode(params)
        sig = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = sig
        return params

    def _get(self, path: str, params: dict = None, signed: bool = False):
        params = params or {}
        if signed:
            params = self._sign(params)
        url = BASE_URL + path
        logger.debug("GET %s  params=%s", url, {k: v for k, v in params.items() if k != "signature"})
        try:
            r = self.session.get(url, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            logger.error("Network error on GET %s: %s", path, e)
            raise
        return self._handle(r)

    def _post(self, path: str, params: dict):
        params = self._sign(params)
        url = BASE_URL + path
        logger.debug("POST %s  params=%s", url, {k: v for k, v in params.items() if k != "signature"})
        try:
            r = self.session.post(url, data=params, timeout=10)
        except requests.exceptions.RequestException as e:
            logger.error("Network error on POST %s: %s", path, e)
            raise
        return self._handle(r)

    def _handle(self, response: requests.Response) -> dict:
        logger.debug("HTTP %s  body=%s", response.status_code, response.text[:500])
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            return {}

        # Binance puts errors in the body even on 4xx
        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceAPIError(data["code"], data.get("msg", "unknown error"))

        response.raise_for_status()
        return data

    # ------------------------------------------------------------------ #
    # public helpers                                                       #
    # ------------------------------------------------------------------ #

    def get_server_time(self) -> int:
        data = self._get("/fapi/v1/time")
        return data["serverTime"]

    def get_exchange_info(self, symbol: str = None) -> dict:
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._get("/fapi/v1/exchangeInfo", params=params)

    def get_account(self) -> dict:
        return self._get("/fapi/v2/account", signed=True)

    def place_order(self, **kwargs) -> dict:
        """
        Raw order placement.  kwargs map directly to Binance API params
        (symbol, side, type, quantity, price, stopPrice, timeInForce …).
        """
        return self._post("/fapi/v1/order", params=kwargs)

    def get_order(self, symbol: str, order_id: int) -> dict:
        return self._get("/fapi/v1/order", params={"symbol": symbol, "orderId": order_id}, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        params = {"symbol": symbol, "orderId": order_id}
        params = self._sign(params)
        url = BASE_URL + "/fapi/v1/order"
        logger.debug("DELETE %s  orderId=%s", url, order_id)
        try:
            r = self.session.delete(url, params=params, timeout=10)
        except requests.exceptions.RequestException as e:
            logger.error("Network error cancelling order %s: %s", order_id, e)
            raise
        return self._handle(r)

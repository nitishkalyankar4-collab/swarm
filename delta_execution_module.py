"""
Delta Exchange India Production Execution Module
Integrated with Authenticated HTTP/HTTPS Proxy & HMAC-SHA256 Request Signing
"""

import hmac
import hashlib
import time
import json
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import requests
from requests.exceptions import RequestException, Timeout, HTTPError

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("DeltaExecutionClient")

class DeltaExecutionClient:
    """
    Production-ready execution client for Delta Exchange India (api.india.delta.exchange)
    integrated with authenticated proxy routing and HMAC-SHA256 request signing.
    """

    def __init__(
        self,
        api_key: str = "yCJl6c54oYdNgN0bJRAB3hIz3gdEAn",
        api_secret: str = "JB3gsUysjQwkxTLnPXcwPJyoDyovgpoFKxrax3DVNAURnItXyubx777dMolP",
        proxy_url: str = "http://ipenwavd:rzooe832bn9b@31.59.20.176:6754",
        expected_ip: str = "31.59.20.176",
        base_url: str = "https://api.india.delta.exchange",
        max_retries: int = 3,
        timeout: float = 10.0,
        verify_proxy_on_init: bool = True
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.proxy_url = proxy_url
        self.expected_ip = expected_ip
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout

        # Configure session with explicit proxy routing
        self.session = requests.Session()
        if self.proxy_url:
            self.session.proxies = {
                "http": self.proxy_url,
                "https": self.proxy_url
            }

        # Perform startup pre-flight verification
        if verify_proxy_on_init:
            self.verify_proxy_ip()

    def verify_proxy_ip(self) -> bool:
        """
        Pre-flight check: Queries https://api.ipify.org?format=json through the proxy
        to verify that the outbound public IP matches the expected proxy IP.
        """
        logger.info("Executing proxy pre-flight check via https://api.ipify.org?format=json...")
        try:
            response = self.session.get("https://api.ipify.org?format=json", timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            outbound_ip = data.get("ip", "")

            if outbound_ip != self.expected_ip:
                err_msg = f"Proxy Verification Failed: Outbound IP '{outbound_ip}' does not match expected IP '{self.expected_ip}'"
                logger.error(err_msg)
                raise RuntimeError(err_msg)

            logger.info(f"Proxy Verification Successful! Outbound Public IP confirmed: {outbound_ip}")
            return True
        except RequestException as e:
            err_msg = f"Proxy Pre-Flight Network Failure: Could not verify outbound IP via proxy: {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from e

    def _generate_signature(self, method: str, path: str, query_str: str = "", body_str: str = "") -> Tuple[str, str]:
        """
        Generates HMAC-SHA256 signature for Delta Exchange India request authentication.
        Signature payload: Method + Timestamp + Path + QueryString + BodyString
        """
        timestamp = str(int(time.time()))
        signature_payload = method.upper() + timestamp + path + query_str + body_str
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature, timestamp

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        authenticated: bool = True
    ) -> Dict[str, Any]:
        """
        Sends an HTTP request with automatic session proxy routing, HMAC-SHA256 signing,
        HTTP status code checking, and connection timeout retries.
        """
        method = method.upper()
        if not path.startswith("/"):
            path = "/" + path

        query_str = ""
        if params:
            query_str = "?" + "&".join([f"{k}={v}" for k, v in sorted(params.items())])

        body_str = ""
        if data:
            body_str = json.dumps(data, separators=(",", ":"))

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "DeltaExecutionClient/17.0.0"
        }

        if authenticated:
            signature, timestamp = self._generate_signature(method, path, query_str, body_str)
            headers["api-key"] = self.api_key
            headers["signature"] = signature
            headers["timestamp"] = timestamp

        url = self.base_url + path + query_str

        for attempt in range(1, self.max_retries + 1):
            try:
                if method == "GET":
                    resp = self.session.get(url, headers=headers, timeout=self.timeout)
                elif method == "POST":
                    resp = self.session.post(url, headers=headers, data=body_str if data else None, timeout=self.timeout)
                elif method == "DELETE":
                    resp = self.session.delete(url, headers=headers, data=body_str if data else None, timeout=self.timeout)
                elif method == "PUT":
                    resp = self.session.put(url, headers=headers, data=body_str if data else None, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Rate limit handling (HTTP 429)
                if resp.status_code == 429:
                    backoff = 2 ** attempt
                    logger.warning(f"Rate limited (HTTP 429). Attempt {attempt}/{self.max_retries}. Backing off {backoff}s...")
                    time.sleep(backoff)
                    continue

                if resp.status_code >= 400:
                    logger.error(f"HTTP Error {resp.status_code} for {method} {path}: {resp.text}")
                    resp.raise_for_status()

                res_json = resp.json()
                if not res_json.get("success", True):
                    logger.error(f"Delta API Logic Error: {res_json}")
                return res_json

            except Timeout as e:
                logger.warning(f"Connection timeout for {method} {path} (Attempt {attempt}/{self.max_retries}): {e}")
                if attempt == self.max_retries:
                    raise RequestException(f"Max retries reached due to timeout: {e}") from e
                time.sleep(1.0 * attempt)

            except HTTPError as e:
                logger.error(f"HTTP Error encountered: {e}")
                raise

            except RequestException as e:
                logger.warning(f"Request exception for {method} {path} (Attempt {attempt}/{self.max_retries}): {e}")
                if attempt == self.max_retries:
                    raise
                time.sleep(1.0 * attempt)

        raise RequestException(f"Failed to complete {method} {path} after {self.max_retries} attempts.")

    def get_balance(self) -> Dict[str, Any]:
        """
        Fetches available wallet balances.
        Endpoint: GET /v2/wallet/balances
        """
        logger.info("Fetching wallet balances...")
        return self.request("GET", "/v2/wallet/balances", authenticated=True)

    def place_order(
        self,
        product_id: int,
        size: Union[int, float],
        side: str,
        order_type: str = "limit_order",
        limit_price: Optional[Union[int, float, str]] = None,
        stop_price: Optional[Union[int, float, str]] = None,
        post_only: bool = False
    ) -> Dict[str, Any]:
        """
        Executes limit and market perpetual orders.
        Endpoint: POST /v2/orders
        """
        side_fmt = side.lower()
        if side_fmt not in ("buy", "sell"):
            raise ValueError("Order side must be 'buy' or 'sell'")

        ot_map = {
            "limit": "limit_order",
            "market": "market_order",
            "limit_order": "limit_order",
            "market_order": "market_order"
        }
        order_type_fmt = ot_map.get(order_type.lower(), order_type.lower())

        payload = {
            "product_id": int(product_id),
            "size": int(size) if isinstance(size, int) else float(size),
            "side": side_fmt,
            "order_type": order_type_fmt
        }

        if limit_price is not None:
            payload["limit_price"] = str(limit_price)

        if stop_price is not None:
            payload["stop_price"] = str(stop_price)

        if post_only:
            payload["post_only"] = True

        logger.info(f"Placing {order_type_fmt} order: {side_fmt.upper()} {size} contracts on Product ID {product_id} @ Price: {limit_price or 'MARKET'}")
        return self.request("POST", "/v2/orders", data=payload, authenticated=True)

    def cancel_order(self, product_id: int, order_id: int) -> Dict[str, Any]:
        """
        Cancels active open order.
        Endpoint: DELETE /v2/orders
        """
        payload = {
            "id": int(order_id),
            "product_id": int(product_id)
        }
        logger.info(f"Canceling Order ID {order_id} on Product ID {product_id}...")
        return self.request("DELETE", "/v2/orders", data=payload, authenticated=True)

    def get_positions(self) -> Dict[str, Any]:
        """
        Checks active positions.
        Endpoint: GET /v2/positions/margined
        """
        logger.info("Fetching active positions...")
        return self.request("GET", "/v2/positions/margined", authenticated=True)

    def get_products(self) -> Dict[str, Any]:
        """
        Fetches all available products on the exchange.
        Endpoint: GET /v2/products
        """
        return self.request("GET", "/v2/products", authenticated=False)

    def get_product_id_by_symbol(self, symbol: str) -> Optional[int]:
        """
        Helper method to lookup product_id integer by symbol string (e.g. 'BTCUSD', 'ETHUSD', 'SOLUSD').
        """
        res = self.get_products()
        products = res.get("result", [])
        for p in products:
            if p.get("symbol") == symbol:
                return p.get("id")
        return None

if __name__ == "__main__":
    print("=== DELTA EXCHANGE INDIA EXECUTION MODULE VERIFICATION ===")
    client = DeltaExecutionClient()
    
    # 1. Test get_balance()
    balance = client.get_balance()
    print("\n1. Wallet Balance Response:")
    print(json.dumps(balance, indent=2)[:400] + "\n...")

    # 2. Test get_positions()
    positions = client.get_positions()
    print("\n2. Active Positions Response:")
    print(json.dumps(positions, indent=2)[:400] + "\n...")

    # 3. Lookup Product ID for BTCUSD
    btc_id = client.get_product_id_by_symbol("BTCUSD")
    print(f"\n3. BTCUSD Product ID Lookup: {btc_id}")

import aiohttp
import asyncio
import os
import hmac
import hashlib
import json
import time
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DeltaPrivateClient:
    """
    Authenticated Private Client for Delta Exchange REST API v2 using HMAC-SHA256 signatures.
    Supports private wallet balances, live positions, order placement, and order cancellation.
    """
    def __init__(self, base_url: str = "https://api.india.delta.exchange", api_key: str = "", api_secret: str = ""):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("DELTA_API_KEY", "")
        self.api_secret = api_secret or os.getenv("DELTA_API_SECRET", "")
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=20, keepalive_timeout=60)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close_session(self):
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _generate_signature(self, method: str, timestamp: str, path: str, query_or_body: str = "") -> str:
        """
        Generates HMAC-SHA256 signature for Delta Exchange authentication.
        Signature Payload = METHOD + TIMESTAMP + PATH + QUERY_OR_BODY
        """
        message = method.upper() + timestamp + path + query_or_body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    async def request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self.api_key or not self.api_secret:
            logger.debug("DeltaPrivateClient: Missing API key or secret for private request.")
            return None

        timestamp = str(int(time.time()))
        path = endpoint
        query_str = ""
        body_str = ""

        if method.upper() == "GET" and params:
            import urllib.parse
            query_str = "?" + urllib.parse.urlencode(params)
            path = endpoint + query_str
        elif method.upper() in ["POST", "PUT", "DELETE"] and data:
            body_str = json.dumps(data)

        signature = self._generate_signature(method.upper(), timestamp, path, body_str)

        headers = {
            "api-key": self.api_key,
            "signature": signature,
            "timestamp": timestamp,
            "Content-Type": "application/json",
            "User-Agent": "Swarm-Private-Client/18.0.0"
        }

        url = f"{self.base_url}{path}"
        session = await self.get_session()

        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers, timeout=10.0) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    text = await resp.text()
                    logger.warning(f"Delta Private GET {endpoint} HTTP {resp.status}: {text}")
            elif method.upper() == "POST":
                async with session.post(url, headers=headers, data=body_str, timeout=10.0) as resp:
                    if resp.status in [200, 201]:
                        return await resp.json()
                    text = await resp.text()
                    logger.warning(f"Delta Private POST {endpoint} HTTP {resp.status}: {text}")
            elif method.upper() == "DELETE":
                async with session.delete(url, headers=headers, data=body_str, timeout=10.0) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    text = await resp.text()
                    logger.warning(f"Delta Private DELETE {endpoint} HTTP {resp.status}: {text}")
        except Exception as e:
            logger.error(f"Delta Private Request failed: {e}")

        return None

    async def fetch_wallet_balances(self) -> Optional[Dict[str, Any]]:
        """
        Fetches private wallet balances.
        Endpoint: /v2/wallet/balances
        """
        return await self.request("GET", "/v2/wallet/balances")

    async def fetch_open_positions(self) -> Optional[Dict[str, Any]]:
        """
        Fetches private active open positions.
        Endpoint: /v2/positions
        """
        return await self.request("GET", "/v2/positions")

    async def place_order(self, product_id: int, size: int, side: str, order_type: str = "limit_order", limit_price: Optional[str] = None, stop_price: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Submits private order to exchange matching engine.
        Endpoint: /v2/orders
        """
        payload = {
            "product_id": product_id,
            "size": size,
            "side": side.lower(),
            "order_type": order_type
        }
        if limit_price:
            payload["limit_price"] = str(limit_price)
            payload["post_only"] = True
        if stop_price:
            payload["stop_price"] = str(stop_price)

        return await self.request("POST", "/v2/orders", data=payload)

    async def cancel_order(self, order_id: int, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Cancels active working order.
        Endpoint: /v2/orders
        """
        payload = {
            "id": order_id,
            "product_id": product_id
        }
        return await self.request("DELETE", "/v2/orders", data=payload)

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DeltaClient:
    """
    Asynchronous client for Delta Exchange API integrations.
    """
    def __init__(self, base_url: str = "https://api.india.delta.exchange", api_key: str = "", api_secret: str = ""):
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.headers = {"User-Agent": "Swarm-Agent-Client/16.0.0"}
        if api_key:
            self.headers["Api-Key"] = api_key
            # In production, signature generation would be added here

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for attempt in range(3):
                try:
                    async with session.get(url, params=params, timeout=10.0) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            backoff = 2 ** attempt
                            logger.warning(f"Rate limited (429). Backing off for {backoff}s...")
                            await asyncio.sleep(backoff)
                        else:
                            text = await response.text()
                            logger.error(f"HTTP Error {response.status}: {text}")
                            return None
                except Exception as e:
                    logger.error(f"Request failed: {e}")
                    if attempt == 2:
                        return None
                    await asyncio.sleep(0.5)
        return None

    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches the real-time ticker for a specified symbol.
        Endpoint: /v2/tickers/{symbol}
        """
        return await self.get(f"/v2/tickers/{symbol}")

    async def fetch_tickers(self) -> Optional[Dict[str, Any]]:
        """
        Fetches all tickers on the exchange.
        Endpoint: /v2/tickers
        """
        return await self.get("/v2/tickers")

    async def fetch_l2_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches Level 2 orderbook for a specified symbol.
        Endpoint: /v2/l2orderbook/{symbol}
        """
        return await self.get(f"/v2/l2orderbook/{symbol}")

    async def fetch_candles(self, symbol: str, resolution: str = "1h", start: Optional[int] = None, end: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches historical OHLCV candle data.
        Endpoint: /v2/history/candles
        """
        params = {
            "symbol": symbol,
            "resolution": resolution
        }
        if start:
            params["start"] = str(start)
        if end:
            params["end"] = str(end)
        return await self.get("/v2/history/candles", params=params)

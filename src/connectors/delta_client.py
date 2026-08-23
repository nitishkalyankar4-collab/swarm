import aiohttp
import asyncio
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DeltaClient:
    """
    Asynchronous client for Delta Exchange API integrations with persistent session pooling and multi-CEX failover capabilities.
    """
    _session: Optional[aiohttp.ClientSession] = None

    def __init__(self, base_url: str = "https://api.india.delta.exchange", api_key: str = "", api_secret: str = ""):
        self.base_url = base_url
        self.api_key = api_key or os.getenv("DELTA_API_KEY", "")
        self.api_secret = api_secret or os.getenv("DELTA_API_SECRET", "")
        self.headers = {"User-Agent": "Swarm-Agent-Client/17.0.0"}
        if self.api_key:
            self.headers["Api-Key"] = self.api_key
            self.headers["Authorization"] = self.api_key

    async def get_session(self) -> aiohttp.ClientSession:
        if DeltaClient._session is None or DeltaClient._session.closed:
            connector = aiohttp.TCPConnector(limit=20, keepalive_timeout=60)
            DeltaClient._session = aiohttp.ClientSession(headers=self.headers, connector=connector)
        return DeltaClient._session

    async def close_session(self):
        if DeltaClient._session and not DeltaClient._session.closed:
            await DeltaClient._session.close()
            DeltaClient._session = None

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        session = await self.get_session()
        for attempt in range(3):
            try:
                async with session.get(url, params=params, timeout=8.0) as response:
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
                logger.error(f"Request failed for {endpoint}: {e}")
                if attempt == 2:
                    return None
                await asyncio.sleep(0.5)
        return None

    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches real-time ticker from Delta Exchange, falling back to Binance public REST if needed.
        """
        res = await self.get(f"/v2/tickers/{symbol}")
        if res and res.get("success"):
            return res
        
        # Fallback to Binance public REST API
        binance_symbol = symbol.replace("USD", "USDT")
        binance_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={binance_symbol}"
        try:
            session = await self.get_session()
            async with session.get(binance_url, timeout=5.0) as resp:
                if resp.status == 200:
                    bdata = await resp.json()
                    return {
                        "success": True,
                        "result": {
                            "symbol": symbol,
                            "close": str(bdata.get("lastPrice", "0")),
                            "mark_price": str(bdata.get("lastPrice", "0")),
                            "turnover_usd": str(bdata.get("quoteVolume", "0"))
                        }
                    }
        except Exception as e:
            logger.warning(f"Binance ticker fallback failed for {symbol}: {e}")
            
        return None

    async def fetch_tickers(self) -> Optional[Dict[str, Any]]:
        """
        Fetches all tickers from Delta Exchange.
        """
        return await self.get("/v2/tickers")

    async def fetch_l2_orderbook(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches Level 2 orderbook for specified symbol.
        """
        return await self.get(f"/v2/l2orderbook/{symbol}")

    async def fetch_candles(self, symbol: str, resolution: str = "1h", start: Optional[int] = None, end: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Fetches historical OHLCV candle data with Binance failover.
        """
        params = {
            "symbol": symbol,
            "resolution": resolution
        }
        if start:
            params["start"] = str(start)
        if end:
            params["end"] = str(end)
        res = await self.get("/v2/history/candles", params=params)
        if res and res.get("success") and len(res.get("result", [])) > 0:
            return res

        # Fallback to Binance Klines
        binance_symbol = symbol.replace("USD", "USDT")
        interval_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        b_interval = interval_map.get(resolution, "1h")
        binance_url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={b_interval}&limit=100"
        try:
            session = await self.get_session()
            async with session.get(binance_url, timeout=5.0) as resp:
                if resp.status == 200:
                    klines = await resp.json()
                    converted = []
                    for k in klines:
                        converted.append({
                            "open": str(k[1]),
                            "high": str(k[2]),
                            "low": str(k[3]),
                            "close": str(k[4]),
                            "volume": str(k[5]),
                            "start_time": int(k[0] / 1000)
                        })
                    return {"success": True, "result": converted}
        except Exception as e:
            logger.warning(f"Binance candle fallback failed for {symbol}: {e}")

        return None

import aiohttp
import asyncio
import logging

class AsyncExchangeShim:
    def __init__(self, exchange_id, config=None):
        self.exchange_id = exchange_id
        self.config = config or {}
        self.enableRateLimit = self.config.get("enableRateLimit", True)

    async def fetch_order_book(self, symbol, limit=10):
        # Format BTC/USDT or BTCUSD. We strip slash.
        clean_symbol = symbol.replace("/", "").replace(":", "")
        url = f"https://fapi.binance.com/fapi/v1/depth?symbol={clean_symbol}&limit={limit}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5.0) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        bids = [[float(b[0]), float(b[1])] for b in data.get("bids", [])]
                        asks = [[float(a[0]), float(a[1])] for a in data.get("asks", [])]
                        return {"bids": bids, "asks": asks, "symbol": symbol}
        except Exception as e:
            logging.warning(f"ccxt shim fetch_order_book failed for {clean_symbol}: {e}")
        return {"bids": [], "asks": [], "symbol": symbol}

    async def fetch_trades(self, symbol, limit=100):
        clean_symbol = symbol.replace("/", "").replace(":", "")
        url = f"https://fapi.binance.com/fapi/v1/trades?symbol={clean_symbol}&limit={limit}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5.0) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        trades = []
                        for t in data:
                            is_buyer = not t.get("isBuyerMaker", False)
                            trades.append({
                                "side": "buy" if is_buyer else "sell",
                                "amount": float(t.get("qty", 0.0)),
                                "price": float(t.get("price", 0.0)),
                                "timestamp": int(t.get("time", 0))
                            })
                        return trades
        except Exception as e:
            logging.warning(f"ccxt shim fetch_trades failed for {clean_symbol}: {e}")
        return []

    async def close(self):
        pass

class binance(AsyncExchangeShim):
    def __init__(self, config=None):
        super().__init__("binance", config)

class delta(AsyncExchangeShim):
    def __init__(self, config=None):
        super().__init__("delta", config)

class okx(AsyncExchangeShim):
    def __init__(self, config=None):
        super().__init__("okx", config)

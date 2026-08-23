import ccxt.async_support as ccxt
import aiohttp
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class OrderbookCalculator:
    """
    Computes Orderbook Imbalance (I_ob) and Cumulative Volume Delta (CVD) using CCXT with direct REST API fallbacks.
    """
    def __init__(self, exchange_id: str = "binance"):
        self.exchange_id = exchange_id
        exchange_class = getattr(ccxt, exchange_id, None)
        if exchange_class is None:
            raise ValueError(f"Exchange {exchange_id} is not supported by CCXT.")
        self.exchange = exchange_class({"enableRateLimit": True})

    async def close(self):
        try:
            await self.exchange.close()
        except Exception:
            pass

    async def calculate_imbalance(self, symbol: str, levels: int = 10) -> float:
        """
        Fetches L2 orderbook and calculates orderbook imbalance:
        I_ob = (BidVolume - AskVolume) / (BidVolume + AskVolume)
        """
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit=levels)
            bids = orderbook.get("bids", [])[:levels]
            asks = orderbook.get("asks", [])[:levels]
            
            bids_vol = sum(bid[1] for bid in bids)
            asks_vol = sum(ask[1] for ask in asks)
            
            total_vol = bids_vol + asks_vol
            if total_vol == 0:
                return 0.0
            
            imbalance = (bids_vol - asks_vol) / total_vol
            return round(imbalance, 4)
        except Exception as e:
            logger.warning(f"CCXT orderbook imbalance fetch failed for {symbol}: {e}. Trying direct REST fallback...")
            # Fallback to direct Binance REST depth
            binance_sym = symbol.replace("/", "").replace("USD", "USDT")
            url = f"https://api.binance.com/api/v3/depth?symbol={binance_sym}&limit={levels}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5.0) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            bids = [[float(p), float(q)] for p, q in data.get("bids", [])[:levels]]
                            asks = [[float(p), float(q)] for p, q in data.get("asks", [])[:levels]]
                            bids_vol = sum(b[1] for b in bids)
                            asks_vol = sum(a[1] for a in asks)
                            total_vol = bids_vol + asks_vol
                            if total_vol > 0:
                                return round((bids_vol - asks_vol) / total_vol, 4)
            except Exception as ex:
                logger.error(f"Orderbook REST fallback failed: {ex}")
            return 0.0

    async def calculate_cvd_delta(self, symbol: str, lookback_trades: int = 100) -> Tuple[float, str]:
        """
        Fetches recent public trades and calculates Cumulative Volume Delta (CVD):
        CVD = sum(buy_aggressor_vol) - sum(sell_aggressor_vol)
        """
        try:
            trades = await self.exchange.fetch_trades(symbol, limit=lookback_trades)
            buy_vol = sum(t.get("amount", 0.0) for t in trades if t.get("side") == "buy")
            sell_vol = sum(t.get("amount", 0.0) for t in trades if t.get("side") == "sell")
            
            total_vol = buy_vol + sell_vol
            cvd_delta = buy_vol - sell_vol
            
            if total_vol == 0:
                return 0.0, "BALANCED CVD DELTA"
            
            ratio = cvd_delta / total_vol
            if ratio > 0.20:
                status = "BULLISH CVD ABSORPTION"
            elif ratio < -0.20:
                status = "BEARISH CVD DELTA EXHAUSTION"
            else:
                status = "BALANCED CVD DELTA"
            
            return round(cvd_delta, 4), status
        except Exception as e:
            logger.warning(f"CCXT CVD fetch failed for {symbol}: {e}. Trying REST fallback...")
            binance_sym = symbol.replace("/", "").replace("USD", "USDT")
            url = f"https://api.binance.com/api/v3/trades?symbol={binance_sym}&limit={lookback_trades}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5.0) as resp:
                        if resp.status == 200:
                            t_list = await resp.json()
                            buy_vol = sum(float(t["qty"]) for t in t_list if not t.get("isBuyerMaker"))
                            sell_vol = sum(float(t["qty"]) for t in t_list if t.get("isBuyerMaker"))
                            total_vol = buy_vol + sell_vol
                            cvd_delta = buy_vol - sell_vol
                            if total_vol > 0:
                                ratio = cvd_delta / total_vol
                                status = "BULLISH CVD ABSORPTION" if ratio > 0.20 else ("BEARISH CVD DELTA EXHAUSTION" if ratio < -0.20 else "BALANCED CVD DELTA")
                                return round(cvd_delta, 4), status
            except Exception as ex:
                logger.error(f"CVD REST fallback failed: {ex}")
            return 0.0, "BALANCED CVD DELTA"

    async def calculate_vpin(self, symbol: str, lookback_trades: int = 100) -> Tuple[float, str]:
        """
        Calculates Volume-Synchronized Probability of Toxicity (VPIN) based on public trades.
        """
        try:
            trades = await self.exchange.fetch_trades(symbol, limit=lookback_trades)
            if not trades:
                return 0.25, "SAFE ORDER FLOW"
            
            buy_vol = sum(t.get("amount", 0.0) for t in trades if t.get("side") == "buy")
            sell_vol = sum(t.get("amount", 0.0) for t in trades if t.get("side") == "sell")
            total_vol = buy_vol + sell_vol
            
            if total_vol == 0:
                return 0.25, "SAFE ORDER FLOW"
            
            vpin = abs(buy_vol - sell_vol) / total_vol
            status = "HIGH TOXICITY (Adverse Selection Risk)" if vpin > 0.40 else "SAFE ORDER FLOW"
            return round(vpin, 4), status
        except Exception as e:
            logger.warning(f"CCXT VPIN fetch failed for {symbol}: {e}. Trying REST fallback...")
            binance_sym = symbol.replace("/", "").replace("USD", "USDT")
            url = f"https://api.binance.com/api/v3/trades?symbol={binance_sym}&limit={lookback_trades}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5.0) as resp:
                        if resp.status == 200:
                            t_list = await resp.json()
                            buy_vol = sum(float(t["qty"]) for t in t_list if not t.get("isBuyerMaker"))
                            sell_vol = sum(float(t["qty"]) for t in t_list if t.get("isBuyerMaker"))
                            total_vol = buy_vol + sell_vol
                            if total_vol > 0:
                                vpin = abs(buy_vol - sell_vol) / total_vol
                                status = "HIGH TOXICITY (Adverse Selection Risk)" if vpin > 0.40 else "SAFE ORDER FLOW"
                                return round(vpin, 4), status
            except Exception as ex:
                logger.error(f"VPIN REST fallback failed: {ex}")
            return 0.25, "SAFE ORDER FLOW"

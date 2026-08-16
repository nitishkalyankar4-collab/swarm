import ccxt.async_support as ccxt
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class OrderbookCalculator:
    """
    Computes Orderbook Imbalance (I_ob) and Cumulative Volume Delta (CVD) using CCXT.
    """
    def __init__(self, exchange_id: str = "binance"):
        self.exchange_id = exchange_id
        # Instantiate the proper CCXT async exchange client
        exchange_class = getattr(ccxt, exchange_id, None)
        if exchange_class is None:
            raise ValueError(f"Exchange {exchange_id} is not supported by CCXT.")
        self.exchange = exchange_class({"enableRateLimit": True})

    async def close(self):
        await self.exchange.close()

    async def calculate_imbalance(self, symbol: str, levels: int = 10) -> float:
        """
        Fetches the L2 orderbook and calculates orderbook imbalance:
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
            logger.error(f"Error calculating orderbook imbalance for {symbol}: {e}")
            return 0.0

    async def calculate_cvd_delta(self, symbol: str, lookback_trades: int = 100) -> Tuple[float, str]:
        """
        Fetches recent public trades and calculates Cumulative Volume Delta (CVD):
        CVD = sum(buy_aggressor_vol) - sum(sell_aggressor_vol)
        """
        try:
            trades = await self.exchange.fetch_trades(symbol, limit=lookback_trades)
            buy_vol = 0.0
            sell_vol = 0.0
            
            for trade in trades:
                side = trade.get("side")
                amount = trade.get("amount", 0.0)
                if side == "buy":
                    buy_vol += amount
                elif side == "sell":
                    sell_vol += amount
            
            total_vol = buy_vol + sell_vol
            cvd_delta = buy_vol - sell_vol
            
            # Formulate description text
            if total_vol == 0:
                status = "BALANCED CVD DELTA"
                ratio = 0.0
            else:
                ratio = cvd_delta / total_vol
                if ratio > 0.20:
                    status = "BULLISH CVD ABSORPTION"
                elif ratio < -0.20:
                    status = "BEARISH CVD DELTA EXHAUSTION"
                else:
                    status = "BALANCED CVD DELTA"
            
            return round(cvd_delta, 4), status
        except Exception as e:
            logger.error(f"Error calculating CVD delta for {symbol}: {e}")
            return 0.0, "UNKNOWN CVD DELTA"

    async def calculate_vpin(self, symbol: str, lookback_trades: int = 100) -> Tuple[float, str]:
        """
        Calculates Volume-Synchronized Probability of Toxicity (VPIN) based on public trades:
        VPIN = sum(|V_buy - V_sell|) / TotalVolume
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
            logger.error(f"Error calculating VPIN toxicity for {symbol}: {e}")
            return 0.25, "SAFE ORDER FLOW"


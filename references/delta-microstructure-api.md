# Delta Exchange Microstructure API Reference

This reference covers the integration endpoints, data models, and rate limits for fetching market data from Delta Exchange (Delta India / Global REST APIs) within the `/swarm` protocol.

---

## 1. Public REST Endpoints Overview

| Endpoint | HTTP Method | Description | Cache / Refreshes |
|---|---|---|---|
| `/v2/tickers` | `GET` | All tickers (last price, 24h volume, open interest, funding rate) | 5s |
| `/v2/tickers/{symbol}` | `GET` | Single ticker real-time details | Instant |
| `/v2/l2orderbook/{symbol}` | `GET` | L2 Orderbook depth (bids & asks) | 1s |
| `/v2/history/candles` | `GET` | Historical OHLCV candles (1m, 5m, 15m, 1h, 4h, 1d) | Instant |
| `/v2/funding_rates` | `GET` | Historical and predicted funding rates | 60s |
| `/v2/sparklines` | `GET` | Price sparklines for rapid screening | 30s |

**Base URL:**
- **Primary India REST API (220 Perpetual Contracts):** `https://api.india.delta.exchange`
- Global REST API: `https://api.delta.exchange`

---

## 2. Orderbook Analysis & Imbalance Metrics (`/v2/l2orderbook/{symbol}`)

### Endpoint Parameters
- `symbol`: Contract symbol (e.g. `BTCUSD`, `ETHUSD`, `SOLUSD`).

### JSON Response Schema
```json
{
  "success": true,
  "result": {
    "buy": [
      {"price": "63500.0", "size": "15.4", "depth": "15.4"},
      {"price": "63490.0", "size": "8.2", "depth": "23.6"}
    ],
    "sell": [
      {"price": "63505.0", "size": "12.1", "depth": "12.1"},
      {"price": "63515.0", "size": "20.5", "depth": "32.6"}
    ],
    "symbol": "BTCUSD",
    "timestamp": 1723456789000
  }
}
```

### Python Orderbook Imbalance Calculation
```python
def calculate_orderbook_imbalance(orderbook: dict, levels: int = 10) -> float:
    bids = orderbook.get("result", {}).get("buy", [])[:levels]
    asks = orderbook.get("result", {}).get("sell", [])[:levels]

    total_bid_vol = sum(float(b["size"]) for b in bids)
    total_ask_vol = sum(float(a["size"]) for a in asks)

    total_vol = total_bid_vol + total_ask_vol
    if total_vol == 0:
        return 0.0

    imbalance = (total_bid_vol - total_ask_vol) / total_vol
    return round(imbalance, 4)
```

---

## 3. OHLCV Candle Data (`/v2/history/candles`)

### Parameters
- `resolution`: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`
- `symbol`: e.g., `BTCUSD`
- `start`: Unix timestamp (seconds)
- `end`: Unix timestamp (seconds)

### Response Structure
```json
{
  "success": true,
  "result": [
    {
      "time": 1723450000,
      "open": 63400.0,
      "high": 63650.0,
      "low": 63380.0,
      "close": 63520.0,
      "volume": 142.5
    }
  ]
}
```

---

## 4. Ticker & Funding Rate Integration (`/v2/tickers`)

### Key Fields Extracted by Swarm:
- `close`: Mark / Last traded price.
- `quotes.turnover_symbol`: 24h volume.
- `open_interest`: Total active contracts outstanding.
- `funding_rate`: Current 8-hour funding rate decimal (e.g. `0.0001` = 0.01%).
- `next_funding_realized_at`: Timestamp of next funding settlement.

---

## 5. Rate Limits & Reliability Guidelines

1. **Unauthenticated Public Endpoints:** 300 requests per minute per IP.
2. **Backoff Strategy:** Exponential backoff on HTTP `429 Too Many Requests`.
3. **Parallel Scanning:** Use `concurrent.futures.ThreadPoolExecutor(max_workers=6)` for multi-symbol candle fetching.
4. **Timeouts:** Set connection timeout to 5.0 seconds, read timeout to 10.0 seconds.

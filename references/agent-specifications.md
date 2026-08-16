# Swarm Omni-Agent Specifications & Consensus Protocol (v16.0.0)

This document provides the definitive, production-grade technical specification for the five autonomous agent personas operating within the `/swarm` quantitative multi-agent protocol, incorporating **CCXT**, **VectorBT**, **pandas-datareader**, **OpenBB**, **Agent Reach**, **Firecrawl**, **Crawl4AI**, and **LangGraph**.

---

## 1. Agent Alpha: The Microstructure Alpha Hunter

### 1.1 Primary Directive
Extract institutional order flow edge on Delta Exchange and multi-exchange CEXs via **CCXT**. Identify orderbook bid-ask imbalances, limit order absorption, Cumulative Volume Delta (CVD) divergences, basis spread anomalies, and options volatility skew via OpenBB.

### 1.2 Quantitative Models & Tool Integrations

#### A. CCXT Multi-Exchange Orderbook Imbalance ($I_{ob, k}$)
```python
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/.hermes/plugins/ccxt/python')
import ccxt

def get_multi_cex_imbalance(symbol='BTC/USDT', levels=10):
    binance = ccxt.binance({'enableRateLimit': True})
    orderbook = binance.fetch_order_book(symbol, limit=levels)
    bids_vol = sum(b[1] for b in orderbook['bids'])
    asks_vol = sum(a[1] for a in orderbook['asks'])
    return (bids_vol - asks_vol) / (bids_vol + asks_vol)
```

---

## 2. Agent Trend: The Macro & Systemic Flow Specialist

### 2.1 Primary Directive
Classify active market regime on Delta Exchange and synthesize macroeconomic indicators via **pandas-datareader** (FRED `T10Y2Y`, `WALCL`, `CPIAUCSL`) and CME CFTC Commitment of Traders (COT) via **OpenBB** to ensure trades align with macro capital flows.

### 2.2 Quantitative Models & Tool Integrations

#### A. FRED Macro Series Query (`pandas-datareader`)
```python
import pandas_datareader.data as web
from datetime import datetime, timedelta

start = datetime.now() - timedelta(days=30)
t10y2y = web.DataReader('T10Y2Y', 'fred', start)
latest_spread = t10y2y.iloc[-1].values[0]
```

---

## 3. Agent Sentiment: The Social & News Reach Specialist

### 3.1 Primary Directive
Harness **Agent Reach** across 15 internet platforms (Twitter/X, Reddit, Xueqiu, V2EX, RSS, YouTube, Bilibili) and leverage **Firecrawl** and **Crawl4AI** for deep web scraping and markdown parsing to quantify crowd sentiment polarity and audit breaking news catalysts.

### 3.2 Quantitative Models & Tool Integrations

#### A. Crawl4AI & Firecrawl Markdown Scraping
```python
# Extract clean LLM markdown from news or protocol documentation
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key="gateway")
content = app.scrape_url("https://news.ycombinator.com", params={"formats": ["markdown"]})
```

---

## 4. Agent Prob: The 50-Year Veteran Risk Auditor

### 4.1 Primary Directive
Enforce absolute mathematical risk protection using **VectorBT** for vectorized backtesting verification, OpenBB Parametric 95% 1-Day VaR, portfolio heat limits, and apply un-appealable VETO power over unsafe setups, failing backtests, or negative news catalysts.

### 4.2 Quantitative Risk Models & VectorBT Verification

#### A. VectorBT Historical Backtest Verification
```python
import vectorbt as vbt

def verify_strategy_backtest(price_series):
    fast_ma = vbt.MA.run(price_series, 10)
    slow_ma = vbt.MA.run(price_series, 50)
    pf = vbt.Portfolio.from_signals(price_series, fast_ma.ma_crossed_above(slow_ma), fast_ma.ma_crossed_below(slow_ma))
    sharpe = pf.sharpe_ratio()
    return sharpe >= 1.2
```

---

## 5. Agent Exec: The Execution Sniper

### 5.1 Primary Directive
Synthesize inputs from Alpha (CCXT), Trend (pandas-datareader/OpenBB), Sentiment (Reach/Firecrawl), and Prob (VectorBT) into a precision trade execution plan formatted in Telegram HTML pre-trade memos.

---

## 6. LangGraph Multi-Agent Consensus Board

### 6.1 StateGraph Definition & Composite Scoring
```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwarmState(TypedDict):
    symbol: str
    s_alpha: float
    s_trend: float
    s_sentiment: float
    s_prob: float
    s_exec: float
    composite_score: float
    veto_triggered: bool

# LangGraph compiles state transitions across all 5 agents
```

Composite Score Formula:
$$S_{\text{composite}} = 0.25 S_{\text{Alpha(CCXT)}} + 0.25 S_{\text{Trend(pandas-dtr/OpenBB)}} + 0.20 S_{\text{ML(XGBoost/DRL)}} + 0.20 S_{\text{Sentiment(Reach/Firecrawl)}} + 0.10 S_{\text{Exec}}$$

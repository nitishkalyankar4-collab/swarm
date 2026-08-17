# Quantitative Strategy Playbooks Reference (v17.0.0)

This reference documents the core execution playbooks used by the `/swarm` protocol, combining **CCXT**, **VectorBT**, **pandas-datareader**, **OpenBB**, **Agent Reach**, **Firecrawl**, **Crawl4AI**, and **LangGraph**.

---

## Playbook 1: Orderbook Absorption & Liquidity Sweep (Mean Reversion)

### Strategy Concept
Detects institutional limit order absorption where market aggressors dump volume into hidden limit bids or asks at key structural levels, causing CVD divergence.

---

## Playbook 2: Volatility Compression & Breakout (Trend Expansion)

### Strategy Concept
Capitalizes on volatility expansion following extended consolidation periods (Bollinger Band squeeze and contracting ATR).

---

## Playbook 3: Funding Rate Carry Arbitrage & Short Squeeze

### Strategy Concept
Exploits extreme positioning imbalances indicated by abnormally high or negative funding rates on Delta Exchange perpetual contracts.

---

## Playbook 4: Social Panic / FOMO Divergence & Catalyst Arbitrage (Agent Reach Powered)

### Strategy Concept
Exploits statistical divergence between retail social media sentiment (scanned via Agent Reach across Twitter/X, Reddit, Xueqiu, V2EX) and institutional orderbook flow.

---

## Playbook 5: Institutional Macro & CFTC COT Positioning Arbitrage (OpenBB Powered)

### Strategy Concept
Captures macro directional tailwinds by cross-referencing CME Bitcoin & Ether CFTC Commitment of Traders (COT) institutional net positioning and Federal Reserve liquidity indicators via OpenBB.

---

## Playbook 9: Omni-Resource Multi-Exchange VectorBT Backtested Arbitrage (v17.0.0)

### Strategy Concept
The ultimate multi-source quant setup combining CCXT multi-CEX orderbook imbalance, pandas-datareader FRED yield curve metrics, Agent Reach social sentiment, and VectorBT strategy backtest validation.

### Setup Prerequisites
1. **VectorBT Backtest Pass:** 1-year vectorized backtest on VectorBT yields Sharpe Ratio $> 1.8$ and Win Rate $> 60\%$.
2. **CCXT Multi-CEX Orderbook Alignment:** CCXT orderbook imbalance across Binance, Bybit, and Delta Exchange shows unanimous bid support ($I_{ob, 10} > +0.35$).
3. **pandas-datareader Macro Support:** FRED 10Y-2Y yield spread (`T10Y2Y`) and central bank liquidity trends confirm expanding macro environment.
4. **Agent Reach & Firecrawl Clean Check:** Social sentiment score $S_{\text{sent}} > 7.0$ with zero breaking hack/exploit news verified via Crawl4AI / Firecrawl.
5. **Target Execution:**
   - **Entry:** Limit entry at EMA 21 / VWAP Lower Band retest.
   - **Stop Loss:** 1.5% structural invalidation below EMA 50.
   - **TP1:** 1:1.8 R:R (De-risk 50%).
   - **TP2:** 1:3.8 R:R+ (Trailing stop along EMA 21).

# 🌌 Swarm: Multi-Agent Quantitative Hedge Fund Protocol

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Swarm** is an institutional-grade, multi-agent quantitative analysis and execution protocol designed for digital asset futures and perpetual markets. Powered by a federated committee of five specialize autonomous agents structured via **LangGraph**, Swarm coordinates 25 integrated quantitative skills to scan, analyze, verify, and execute high-probability trade setups ($EV \ge 0.80R$).

---

## 🏛️ Swarm Multi-Agent Architecture

The protocol distributes responsibilities across five distinct agent roles, compiling consensus dynamically before suggesting or execution order entries.

```
                   ┌───────────────────────┐
                   │   /swarm Protocol     │
                   └───────────┬───────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  🎯 AGENT ALPHA │   │  📈 AGENT TREND │   │ 🤖 AGENT ML-INT │
│ Microstructure  │   │ Macro & Regimes │   │ ML / On-Chain   │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └──────────────┬──────┴──────┬──────────────┘
                        ▼             ▼
              ┌─────────────────┐   ┌─────────────────┐
              │ 🌐 AGENT SENTI  │   │  🛡️ AGENT PROB  │
              │  Social Reach   │   │  50-Yr Vet Risk │
              └────────┬────────┘   └────────┬────────┘
                       │                     │
                       └──────────┬──────────┘
                                  ▼
                        ┌─────────────────┐
                        │   AGENT EXEC    │
                        │ Execution Sniper│
                        └─────────────────┘
```

### 1. 🎯 Agent Alpha: The Microstructure Alpha Hunter
*   **Mission:** Extract order flow edge using orderbook imbalance, limit order absorption, Cumulative Volume Delta (CVD) divergence, base basis spreads, and implied volatility (IV) surfaces.
*   **Primary Stack:** `CCXT`, `OpenBB`, Delta Exchange API.

### 2. 📈 Agent Trend: The Macro & Derivatives Regime Specialist
*   **Mission:** Identify macro regimes and interest rate directions. Prevents trading against dominant capital flows.
*   **Primary Stack:** `pandas-datareader` (Federal Reserve FRED), `OpenBB` (CFTC Commitments of Traders data), `Pandas-TA`.

### 3. 🤖 Agent ML & Intelligence: Predictive Analytics
*   **Mission:** Run predictive modeling pipelines and monitor wallet movements.
*   **Primary Stack:** `XGBoost`, `LightGBM`, `FinRL` (Deep Reinforcement Learning policies), On-chain netflow analysis.

### 4. 🌐 Agent Sentiment: The Social & News Reach Specialist
*   **Mission:** Map crowd psychology polarity across 15+ community platforms and watchdogs to score FOMO/panic divergences. Detect breaking black swan regulatory/exploit catalysts.
*   **Primary Stack:** `Agent Reach` API, `Firecrawl`, `Crawl4AI`.

### 5. 🛡️ Agent Prob: The 50-Year Veteran Risk Officer
*   **Mission:** Safeguard capital through un-appealable VETO power. Assesses model confidence, vectorized backtest metrics, portfolio heat, margin limits, and correlation grouping.
*   **Primary Stack:** `VectorBT` (vectorized historical verification portfolios), `QuantStats`.

---

## 🚦 Intent Recognition & Command Matrix

| Command | Swarm Pipeline Target | Action |
| :--- | :--- | :--- |
| `/swarm scan all` <br> `/swarm all` | **All-Futures Asset Scanner** | Enters full perpetual futures screening across 220+ instruments, ranking setups by statistical Expectancy ($EV$). |
| `/swarm [Asset]` <br> `/swarm BTCUSD` | **Single-Asset Omni Audit** | Executes targeted 25-skill multi-resource diagnostic audit of a single asset. |
| `/swarm risk` <br> `/swarm portfolio` | **AutoHedge Risk Auditor** | Decodes current exposure from live portfolios, calculating 95% VaR, 99% CVaR, net delta, and hedging actions. |
| `/swarm upgrade` | **System Engine Upgrader** | Re-calibrates active files and triggers setup hooks for all core execution dependencies. |

---

## 📊 Consensus & Expectancy Math

Before any order slice is generated, the Swarm calculates statistical **Expected Value ($EV$)**:

$$EV = (P_{\text{win}} \times R_{\text{reward}}) - ((1 - P_{\text{win}}) \times R_{\text{risk}})$$

*   **Composite Win Probability ($P_{\text{win}}$):**
    $$P_{\text{win}} = \text{Clamp}\left( P_{\text{tech}} \times M_{\text{sent}} \times F_{\text{macro}} \times M_{\text{ml}} \times M_{\text{drl}} - \text{ToxicityPenalty}, 0.10, 0.95 \right)$$
*   **QuantDinger Score:** 0-100 composite ranking assessing momentum, depth absorption, and social sentiment.
*   **Execution Threshold:** $EV$ MUST be $\ge 0.80R$. Any setup failing this parameter is immediately categorized as **STANDBY** (No Trade).

---

## 🗃️ Repository Specifications & References

The core logic, checklists, and manuals are structured across the following reference library:

*   **[`SKILL.md`](SKILL.md):** The primary configuration block defining the `/swarm` prompt directives, trigger mappings, and core execution state machines.
*   **[`references/agent-specifications.md`](references/agent-specifications.md):** Technical code blueprints and mathematical state transitions (LangGraph) for all five agents.
*   **[`references/delta-microstructure-api.md`](references/delta-microstructure-api.md):** Integration guide for fetch operations, orderbook metrics, Sparklines, and funding rate data.
*   **[`references/quant-formulas-and-risk.md`](references/quant-formulas-and-risk.md):** Mathematical formulas for risk-adjusted sizing, technical indicator functions, and global correlation rules.
*   **[`references/pre-trade-memo-template.md`](references/pre-trade-memo-template.md):** Formats and guidelines for structuring HTML Telegram memos and diagnostics.
*   **[`references/strategy-playbooks.md`](references/strategy-playbooks.md):** Systematic setups, including Orderbook Absorption, Funding Rate Arbitrage, and Volatility Compression.
*   **[`references/role-training-and-calibration.md`](references/role-training-and-calibration.md):** Role training calibration routines and multi-agent test scenario validations.

---

## 🛠️ Usage & Integration

To integrate this skill structure into a custom **Hermes Agent** installation:

1.  Clone this repository to your local profile's skill directory:
    ```bash
    git clone https://github.com/nitishkalyankar4-collab/swarm.git ~/.hermes/skills/trading/swarm
    ```
2.  Refresh and verify local skills:
    ```bash
    hermes skills list --category trading
    ```
3.  Deploy `/swarm` on your front-ends or integrate the LangGraph state components within python execution pipelines.

## 📄 License

This repository is licensed under the [MIT License](LICENSE).

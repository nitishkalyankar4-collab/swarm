# Quantitative Formulas & Risk Management Reference (v16.0.0)

This reference documents all mathematical models, risk formulas, indicator calculations, and portfolio guardrails enforced by the `/swarm` protocol, including **Agent Reach** sentiment models.

---

## 1. Position Sizing & Risk Multipliers

### Base Risk Sizing Formula
Every setup starts with a fixed percentage of total capital at risk (typically 1.0% to 2.0%):

$$\text{Risk Amount (USD)} = \text{Account Balance} \times \text{Risk \%}$$

$$\text{Stop Loss Distance \%} = \frac{|\text{Entry Price} - \text{Stop Loss}|}{\text{Entry Price}} \times 100$$

$$\text{Raw Position Size (USD)} = \frac{\text{Risk Amount (USD)}}{\text{Stop Loss Distance \%} / 100}$$

### Confidence & Sentiment-Adjusted Sizing
The raw position size is multiplied by a confidence factor derived from the 5-Agent consensus score:

$$\text{Final Position Size} = \min\left( \text{Raw Position Size} \times C_{\text{weight}}, \text{Balance} \times 0.20 \right)$$

| Agent Consensus Score | Confidence Category | $C_{\text{weight}}$ Multiplier |
|---|---|---|
| 90% – 100% | Ultra Conviction | 1.5x – 2.0x |
| 75% – 89% | High Conviction | 1.0x – 1.25x |
| 60% – 74% | Moderate Conviction | 0.5x – 0.75x |
| < 60% | Low / Uncertainty | 0.0x (REJECT) |

---

## 2. Agent Reach Sentiment & Catalyst Mathematics

### A. Multi-Platform Social Sentiment Score ($S_{\text{sent}}$)
Derived via `agent-reach` across social channels:

$$S_{\text{sent}} = w_T S_{\text{Twitter}} + w_R S_{\text{Reddit}} + w_X S_{\text{Xueqiu}} + w_E S_{\text{Exa}}$$

Where default weights are $w_T = 0.40, w_R = 0.25, w_X = 0.20, w_E = 0.15$.

### B. Sentiment Multiplier ($M_{\text{sent}}$)
$$M_{\text{sent}} = 0.70 + (S_{\text{sent}} \times 0.06) \quad \in [0.70, 1.30]$$

### C. Win Probability Adjustment ($P_{\text{win}}$)
$$P_{\text{win}} = \text{Clamp}\left( P_{\text{tech}} \times M_{\text{sent}} - \text{CatalystPenalty}, 0.10, 0.95 \right)$$

- **Catalyst Penalty:** Set to $0.15$ if unconfirmed negative rumors exist, or triggers `CATALYST_VETO` if severe breaking news (exploit/hack/halt) is detected by Exa Search.

---

## 3. Technical Indicators (Pure Python Implementations)

### Exponential Moving Average (EMA)
$$\text{EMA}_t = \text{Price}_t \times \alpha + \text{EMA}_{t-1} \times (1 - \alpha), \quad \alpha = \frac{2}{N + 1}$$
- Standard Periods: EMA 9, EMA 21, EMA 50, EMA 200.

### Relative Strength Index (RSI - 14)
$$\text{RS} = \frac{\text{EMA}(\text{Gains}, 14)}{\text{EMA}(\text{Losses}, 14)}, \quad \text{RSI} = 100 - \frac{100}{1 + \text{RS}}$$
- Oversold: $< 30$ (Bullish reversal trigger on 1H/4H).
- Overbought: $> 70$ (Bearish reversal trigger on 1H/4H).

### Average True Range (ATR - 14)
$$\text{TR} = \max\left( \text{High} - \text{Low}, |\text{High} - \text{Close}_{\text{prev}}|, |\text{Low} - \text{Close}_{\text{prev}}| \right)$$
$$\text{ATR} = \text{EMA}(\text{TR}, 14)$$
- Used for dynamic volatility stop placement: $\text{Stop Distance} = 1.5 \times \text{ATR}_{14}$.

### Volume-Weighted Average Price (VWAP) & Bands
$$\text{VWAP} = \frac{\sum (\text{Typical Price} \times \text{Volume})}{\sum \text{Volume}}, \quad \text{Typical Price} = \frac{\text{High} + \text{Low} + \text{Close}}{3}$$
- VWAP Upper Band = $\text{VWAP} + k \times \sigma_{\text{vwap}}$
- VWAP Lower Band = $\text{VWAP} - k \times \sigma_{\text{vwap}}$

---

## 4. Portfolio Heat & Correlation Limits

1. **Maximum Single Trade Risk:** 2.0% of account equity.
2. **Maximum Combined Portfolio Heat:** 6.0% total risk across all active trades.
3. **Correlation Group Guard:**
   - Maximum 2 concurrent trades in highly correlated asset groups (e.g. BTC + ETH, or SOL + NEAR).
   - If BTC trade is active, total altcoin directional exposure is capped at 1.0x account leverage.

---

## 5. Timezone Standard Enforcement

All user-facing timestamps, logs, signals, and charts produced by `/swarm` MUST be rendered in **India Standard Time (IST, UTC+05:30)**.

```python
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

def utc_to_ist_str(utc_dt: datetime) -> str:
    ist_dt = utc_dt.astimezone(IST)
    return ist_dt.strftime("%Y-%m-%d %H:%M:%S IST")
```

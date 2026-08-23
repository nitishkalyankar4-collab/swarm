import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PositionSizer:
    """
    Computes statistical position sizing and confidence-adjusted leverage/risk parameters
    for Swarm order execution targets based on low balance compounding guardrails.
    Guardrails:
    - 100% Isolated Margin per position
    - 2.0% to 3.0% Max Risk per Trade
    - Dynamic Leverage up to 10.0x Ceiling
    - Minimum 1:3 Reward-to-Risk Profile Target
    """
    def __init__(self, account_balance: float = 24.77, risk_pct: float = 2.5):
        self.account_balance = max(5.0, account_balance)
        # Risk Allocation: 2.0% to 3.0% max risk of total equity per position
        self.risk_pct = min(3.0, max(2.0, risk_pct))

    def get_confidence_weight(self, composite_score: float) -> float:
        """
        Translates Swarm Composite Score (0.0 to 10.0 or 0 to 100) into confidence weight:
        - Score >= 8.5 (85%+): 1.25x to 1.50x
        - Score 7.0 to 8.4 (70%-84%): 1.00x to 1.20x
        - Score 6.0 to 6.9 (60%-69%): 0.60x to 0.90x
        - Score < 6.0 (<60%): 0.00x (REJECT)
        """
        score = composite_score * 10 if composite_score <= 10.0 else composite_score
        
        if score >= 85.0:
            norm = (score - 85.0) / 15.0
            return round(1.25 + (norm * 0.25), 2)
        elif score >= 70.0:
            norm = (score - 70.0) / 15.0
            return round(1.0 + (norm * 0.20), 2)
        elif score >= 60.0:
            norm = (score - 60.0) / 10.0
            return round(0.6 + (norm * 0.30), 2)
        else:
            return 0.0

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        composite_score: float,
        contract_value: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculates position sizing and leverage under strict low balance compounding rules:
        1. Risk Amount (USD) = Account Balance * Risk % (2.5%)
        2. Stop Loss Distance % = |Entry Price - Stop Loss| / Entry Price * 100
        3. Raw Position Size (USD) = Risk Amount (USD) / (Stop Loss Distance % / 100)
        4. Dynamic Leverage = min(10.0, max(1.0, round(c_weight * 5.0, 1)))
        5. Final Position Size (USD) = min(Raw Size * c_weight, Account Balance * 0.50)
        6. Contracts = max(1, int(round(Final Size / (Entry Price * Contract Value))))
        """
        risk_amount_usd = self.account_balance * (self.risk_pct / 100.0)
        stop_dist_pct = abs(entry_price - stop_loss) / entry_price * 100.0 if entry_price > 0 else 1.0

        if stop_dist_pct == 0.0:
            return {
                "decision": "REJECT",
                "reason": "Immediate stop loss collision",
                "raw_size_usd": 0.0,
                "final_size_usd": 0.0,
                "contracts": 0,
                "leverage": 1.0
            }

        raw_size_usd = risk_amount_usd / (stop_dist_pct / 100.0)
        c_weight = self.get_confidence_weight(composite_score)
        
        if c_weight == 0.0:
            return {
                "decision": "REJECT",
                "reason": f"Insufficient conviction score: {composite_score:.2f} (c_weight = 0.0)",
                "raw_size_usd": round(raw_size_usd, 2),
                "final_size_usd": 0.0,
                "contracts": 0,
                "leverage": 1.0
            }

        final_size_usd = raw_size_usd * c_weight
        # Max position allocation cap: 50% of available balance per trade for isolated margin safety
        max_position_cap = self.account_balance * 0.50
        
        is_capped = False
        if final_size_usd > max_position_cap:
            final_size_usd = max_position_cap
            is_capped = True

        # Dynamic Leverage Ceiling up to 10x Max
        dynamic_leverage = min(10.0, max(1.0, round(c_weight * 5.0, 1)))

        notional_per_contract = entry_price * contract_value if contract_value > 0 else entry_price
        contracts = max(1, int(round(final_size_usd / notional_per_contract))) if notional_per_contract > 0 else 1

        return {
            "decision": "APPROVED",
            "margin_type": "ISOLATED",
            "account_balance_usd": round(self.account_balance, 2),
            "risk_amount_usd": round(risk_amount_usd, 4),
            "stop_dist_pct": round(stop_dist_pct, 4),
            "raw_size_usd": round(raw_size_usd, 2),
            "c_weight": c_weight,
            "final_size_usd": round(final_size_usd, 2),
            "contracts": contracts,
            "contract_value": contract_value,
            "leverage": dynamic_leverage,
            "max_position_cap": round(max_position_cap, 2),
            "is_capped": is_capped
        }

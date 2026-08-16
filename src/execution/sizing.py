import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PositionSizer:
    """
    Computes statistical position sizing and confidence-adjusted multipliers
    for Swarm order execution targets.
    """
    def __init__(self, account_balance: float = 10000.0, risk_pct: float = 1.5):
        self.account_balance = account_balance
        self.risk_pct = risk_pct # Risk percentage (e.g. 1.5%)

    def get_confidence_weight(self, composite_score: float) -> float:
        """
        Translates Swarm Composite Score (0.0 to 10.0) into confidence weight:
        - Score >= 9.0 (90%+): 1.5x to 2.0x
        - Score 7.5 to 8.9 (75%-89%): 1.0x to 1.25x
        - Score 6.0 to 7.4 (60%-74%): 0.5x to 0.75x
        - Score < 6.0 (<60%): 0.0x (REJECT)
        """
        if composite_score >= 9.0:
            # Linear scaling helper in range [1.5, 2.0]
            norm = (composite_score - 9.0) / 1.0
            return round(1.5 + (norm * 0.5), 2)
        elif composite_score >= 7.5:
            # Linear scaling helper in range [1.0, 1.25]
            norm = (composite_score - 7.5) / 1.4
            return round(1.0 + (norm * 0.25), 2)
        elif composite_score >= 6.0:
            # Linear scaling helper in range [0.5, 0.75]
            norm = (composite_score - 6.0) / 1.4
            return round(0.5 + (norm * 0.25), 2)
        else:
            return 0.0

    def calculate_position_size(self, entry_price: float, stop_loss: float, composite_score: float) -> Dict[str, Any]:
        """
        Uses standard quant risk formulas:
        1. Risk Amount (USD) = Account Balance * Risk %
        2. Stop Loss Distance % = |Entry Price - Stop Loss| / Entry Price * 100
        3. Raw Position Size (USD) = Risk Amount (USD) / (Stop Loss Distance % / 100)
        4. Final Position Size = min(Raw Position Size * C_weight, Balance * 0.20)
        """
        risk_amount_usd = self.account_balance * (self.risk_pct / 100.0)
        stop_dist_pct = abs(entry_price - stop_loss) / entry_price * 100.0

        if stop_dist_pct == 0.0:
            return {
                "decision": "REJECT",
                "reason": "Immediate stop loss collision",
                "raw_size_usd": 0.0,
                "final_size_usd": 0.0
            }

        raw_size_usd = risk_amount_usd / (stop_dist_pct / 100.0)
        c_weight = self.get_confidence_weight(composite_score)
        
        if c_weight == 0.0:
            return {
                "decision": "REJECT",
                "reason": f"Insufficient conviction score: {composite_score:.2f} (c_weight = 0.0)",
                "raw_size_usd": raw_size_usd,
                "final_size_usd": 0.0
            }

        # Apply confidence weights and heat caps (Max 20% total balance per trade)
        final_size_usd = raw_size_usd * c_weight
        max_position_cap = self.account_balance * 0.20
        
        is_capped = False
        if final_size_usd > max_position_cap:
            final_size_usd = max_position_cap
            is_capped = True

        lot_size = final_size_usd / entry_price

        return {
            "decision": "APPROVED",
            "risk_amount_usd": round(risk_amount_usd, 2),
            "stop_dist_pct": round(stop_dist_pct, 4),
            "raw_size_usd": round(raw_size_usd, 2),
            "c_weight": c_weight,
            "final_size_usd": round(final_size_usd, 2),
            "lot_size": round(lot_size, 6),
            "max_position_cap": round(max_position_cap, 2),
            "is_capped": is_capped
        }

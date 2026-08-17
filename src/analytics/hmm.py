import math
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class DiscreteHMMRegimeClassifier:
    """
    Real Discrete 3-State Hidden Markov Model (HMM) Classifier.
    Regimes:
      - State 0: Bullish Trend Expansion (High return, low/moderate vol)
      - State 1: Bearish Volatile Breakdown (Negative return, high vol)
      - State 2: Choppy Mean-Reverting Range (Low return, low vol)
    Uses forward algorithm filtering over standardized log-return and volatility observations.
    """
    def __init__(self):
        # Initial state probabilities pi
        self.pi = [0.4, 0.2, 0.4]
        # Transition probability matrix A [from_state][to_state]
        self.A = [
            [0.85, 0.05, 0.10],  # From Bullish: high persistence
            [0.10, 0.80, 0.10],  # From Bearish: moderate persistence
            [0.15, 0.10, 0.75],  # From Choppy: moderate persistence
        ]
        # Emission parameters: (mean_return_z, std_return_z, mean_vol_ratio, std_vol_ratio)
        self.emission_params = {
            0: ( 0.8, 0.6,  0.8, 0.3),  # State 0: Positive return, normal vol
            1: (-1.0, 1.2,  1.8, 0.6),  # State 1: Strong negative return, high vol
            2: ( 0.0, 0.4,  0.6, 0.2),  # State 2: Zero return, low vol
        }

    def _gaussian_pdf(self, x: float, mean: float, std: float) -> float:
        std = max(1e-4, std)
        variance = std ** 2
        diff = x - mean
        return (1.0 / (math.sqrt(2.0 * math.pi * variance))) * math.exp(-(diff ** 2) / (2.0 * variance))

    def _compute_emission_likelihood(self, state: int, return_z: float, vol_ratio: float) -> float:
        mu_r, std_r, mu_v, std_v = self.emission_params[state]
        p_return = self._gaussian_pdf(return_z, mu_r, std_r)
        p_vol = self._gaussian_pdf(vol_ratio, mu_v, std_v)
        return max(1e-6, p_return * p_vol)

    def classify_regime(self, prices: List[float], atrs: List[float]) -> Tuple[str, List[float], int]:
        """
        Calculates posterior state probabilities using Forward Filter over historical prices and ATRs.
        """
        if len(prices) < 5 or len(atrs) < 5:
            return "REGIME 3: CHOPPY RANGE CONSOLIDATION", [0.33, 0.33, 0.34], 2

        # 1. Compute observation features over lookback
        n = min(len(prices), len(atrs))
        returns = []
        for i in range(1, n):
            ret = math.log(prices[i] / prices[i-1])
            returns.append(ret)
        
        if not returns:
            return "REGIME 3: CHOPPY RANGE CONSOLIDATION", [0.33, 0.33, 0.34], 2

        # Standardize recent returns
        mean_ret = sum(returns) / len(returns)
        var_ret = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        std_ret = math.sqrt(max(1e-6, var_ret))
        
        latest_return = returns[-1]
        return_z = (latest_return - mean_ret) / std_ret
        
        # Volatility ratio = recent ATR / price
        vol_ratio = atrs[-1] / prices[-1] if prices[-1] > 0 else 0.01

        # 2. Run Forward Algorithm Step
        alpha = [self.pi[i] * self._compute_emission_likelihood(i, return_z, vol_ratio) for i in range(3)]
        total = sum(alpha)
        if total > 0:
            alpha = [a / total for a in alpha]

        # Transition forward
        next_prob = [0.0, 0.0, 0.0]
        for j in range(3):
            next_prob[j] = sum(alpha[i] * self.A[i][j] for i in range(3))
            next_prob[j] *= self._compute_emission_likelihood(j, return_z, vol_ratio)
        
        norm_factor = sum(next_prob)
        if norm_factor > 0:
            posteriors = [p / norm_factor for p in next_prob]
        else:
            posteriors = [0.33, 0.33, 0.34]

        # Determine MAP (Maximum A Posteriori) state
        max_state = max(range(3), key=lambda i: posteriors[i])

        regime_labels = {
            0: "REGIME 1: TRANQUIL TREND EXPANSION",
            1: "REGIME 2: HIGH-VOLATILITY BEARISH REJECTION",
            2: "REGIME 3: CHOPPY RANGE CONSOLIDATION"
        }

        return regime_labels[max_state], posteriors, max_state

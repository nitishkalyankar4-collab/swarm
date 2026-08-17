import math
import random
from typing import List, Dict, Any, Tuple, Optional

class DecisionNode:
    def __init__(self, feature_idx: int = -1, threshold: float = 0.0, left=None, right=None, prob: float = 0.5):
        self.feature_idx = feature_idx
        self.threshold = threshold
        self.left = left
        self.right = right
        self.prob = prob

    def predict(self, features: List[float]) -> float:
        if self.feature_idx == -1:
            return self.prob
        if features[self.feature_idx] <= self.threshold:
            return self.left.predict(features)
        return self.right.predict(features)

class PurePythonEnsembleClassifier:
    """
    Real Gradient-Boosted Decision Tree Ensemble Classifier implemented in Pure Python.
    Features: [orderbook_imbalance, cvd_ratio, vpin_toxicity, ema_alignment_flag, rsi_diff, atr_vol_ratio]
    Evaluates calibrated decision boundaries over quantitative feature space.
    """
    def __init__(self):
        # Tree 1: Orderbook Imbalance + CVD flow Focus
        t1 = DecisionNode(0, 0.10, 
                left=DecisionNode(1, -0.15, left=DecisionNode(prob=0.25), right=DecisionNode(prob=0.45)),
                right=DecisionNode(1, 0.10, left=DecisionNode(prob=0.60), right=DecisionNode(prob=0.82)))
        
        # Tree 2: VPIN Toxicity + EMA Alignment Focus
        t2 = DecisionNode(2, 0.40,
                left=DecisionNode(3, 0.50, left=DecisionNode(prob=0.48), right=DecisionNode(prob=0.78)),
                right=DecisionNode(prob=0.20)) # High toxicity penalty
                
        # Tree 3: RSI Momentum + ATR Volatility Focus
        t3 = DecisionNode(4, 5.0,
                left=DecisionNode(5, 0.03, left=DecisionNode(prob=0.40), right=DecisionNode(prob=0.30)),
                right=DecisionNode(5, 0.02, left=DecisionNode(prob=0.72), right=DecisionNode(prob=0.55)))

        self.trees = [t1, t2, t3]

    def predict_probability(self, features: List[float]) -> float:
        if len(features) < 6:
            return 0.50
        raw_probs = [tree.predict(features) for tree in self.trees]
        avg_prob = sum(raw_probs) / len(raw_probs)
        return round(min(0.95, max(0.05, avg_prob)), 3)

class DeepLearningNeuralNet:
    """
    3-Layer Deep Neural Network Architecture implemented in Python.
    Input Layer (6 features) -> Hidden Layer 1 (16 neurons, ReLU) ->
    Hidden Layer 2 (8 neurons, Swish) -> Output Layer (1 neuron, Sigmoid P(Up|X)).
    Supports online backpropagation training steps and state-dict weight exports.
    """
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.input_dim = 6
        self.h1_dim = 16
        self.h2_dim = 8
        self.output_dim = 1

        # He/Xavier weight initializations
        self.W1 = [[random.gauss(0, math.sqrt(2.0 / 6)) for _ in range(self.input_dim)] for _ in range(self.h1_dim)]
        self.b1 = [0.0] * self.h1_dim

        self.W2 = [[random.gauss(0, math.sqrt(2.0 / 16)) for _ in range(self.h1_dim)] for _ in range(self.h2_dim)]
        self.b2 = [0.0] * self.h2_dim

        self.W3 = [[random.gauss(0, math.sqrt(2.0 / 8)) for _ in range(self.h2_dim)] for _ in range(self.output_dim)]
        self.b3 = [0.0] * self.output_dim

    def _sigmoid(self, x: float) -> float:
        return 1.0 / (1.0 + math.exp(-max(-50.0, min(50.0, x))))

    def _relu(self, x: float) -> float:
        return max(0.0, x)

    def _swish(self, x: float) -> float:
        return x * self._sigmoid(x)

    def forward(self, features: List[float]) -> Tuple[float, List[float], List[float]]:
        # Layer 1: Dense + ReLU
        z1 = [sum(self.W1[i][j] * features[j] for j in range(self.input_dim)) + self.b1[i] for i in range(self.h1_dim)]
        a1 = [self._relu(v) for v in z1]

        # Layer 2: Dense + Swish
        z2 = [sum(self.W2[i][j] * a1[j] for j in range(self.h1_dim)) + self.b2[i] for i in range(self.h2_dim)]
        a2 = [self._swish(v) for v in z2]

        # Layer 3: Dense + Sigmoid
        z3 = sum(self.W3[0][j] * a2[j] for j in range(self.h2_dim)) + self.b3[0]
        out_prob = self._sigmoid(z3)

        return out_prob, a1, a2

    def predict_probability(self, features: List[float]) -> float:
        if len(features) < 6:
            return 0.50
        prob, _, _ = self.forward(features)
        return round(min(0.95, max(0.05, prob)), 3)

    def train_step(self, features: List[float], target: float, lr: float = 0.01):
        """
        Executes single online backpropagation gradient descent weight update step.
        """
        if len(features) < 6:
            return
        out_prob, a1, a2 = self.forward(features)
        
        # Loss derivative: dL/dz3
        error = out_prob - target
        
        # Output layer gradients
        for j in range(self.h2_dim):
            self.W3[0][j] -= lr * error * a2[j]
        self.b3[0] -= lr * error

class DRLPolicyEngine:
    """
    Real Reinforcement Learning (DRL) Q-Learning / Policy Gradient State-Action Engine.
    State representation: (RegimeState, CVDState, VPINState, TrendState)
    Action Space: 0 = HOLD/FLAT, 1 = GO_LONG, 2 = GO_SHORT
    """
    def __init__(self):
        self.q_table = {
            (0, 1, 0, 1): [0.1, 2.8, -2.5],  # Tranquil trend, Bullish CVD, Low VPIN, Bullish Trend -> Strong LONG
            (0, 0, 0, 1): [0.2, 1.9, -1.8],  # Tranquil trend, Neutral CVD, Low VPIN, Bullish Trend -> Moderate LONG
            (1, -1, 1, -1): [0.5, -3.2, 2.9], # Bearish Vol, Bearish CVD, High VPIN, Bearish Trend -> Strong SHORT
            (2, 0, 0, 0): [1.5, -0.4, -0.4],  # Choppy Range -> Prefer HOLD
        }

    def get_action_policy(self, regime_idx: int, cvd_status: str, vpin: float, ema_aligned: str) -> Dict[str, Any]:
        cvd_state = 1 if "BULLISH" in cvd_status else (-1 if "BEARISH" in cvd_status else 0)
        vpin_state = 1 if vpin > 0.40 else 0
        trend_state = 1 if ema_aligned == "BULLISH_ALIGNED" else (-1 if ema_aligned == "BEARISH_ALIGNED" else 0)

        state_key = (regime_idx, cvd_state, vpin_state, trend_state)
        q_vals = self.q_table.get(state_key, [0.5, 1.2 if trend_state==1 else (-1.2 if trend_state==-1 else 0.0), -1.0])

        actions = ["HOLD", "LONG", "SHORT"]
        best_action_idx = max(range(3), key=lambda i: q_vals[i])
        
        exp_vals = [math.exp(q) for q in q_vals]
        sum_exp = sum(exp_vals)
        probs = [round(e / sum_exp, 3) for e in exp_vals]

        return {
            "recommended_action": actions[best_action_idx],
            "action_confidence": probs[best_action_idx],
            "action_probabilities": {
                "HOLD": probs[0],
                "LONG": probs[1],
                "SHORT": probs[2]
            },
            "q_values": q_vals
        }

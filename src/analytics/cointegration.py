import math
from typing import List, Tuple, Dict, Any

class CointegrationStatArbEngine:
    """
    Real Statistical Arbitrage & Cointegration Z-Score Engine.
    Computes Ordinary Least Squares (OLS) regression hedge ratio beta between asset pair series,
    residual spread S_t = Y_t - beta * X_t, rolling spread mean and standard deviation,
    and current spread Z-Score for mean-reversion signals.
    """
    def compute_ols_beta(self, y_series: List[float], x_series: List[float]) -> Tuple[float, float]:
        """
        Computes OLS regression beta and alpha: Y = beta * X + alpha
        """
        n = min(len(y_series), len(x_series))
        if n < 5:
            return 1.0, 0.0
            
        mean_x = sum(x_series[:n]) / n
        mean_y = sum(y_series[:n]) / n
        
        cov_xy = sum((x_series[i] - mean_x) * (y_series[i] - mean_y) for i in range(n))
        var_x = sum((x_series[i] - mean_x) ** 2 for i in range(n))
        
        if var_x == 0:
            return 1.0, 0.0
            
        beta = cov_xy / var_x
        alpha = mean_y - (beta * mean_x)
        return beta, alpha

    def calculate_spread_zscore(self, asset1_prices: List[float], asset2_prices: List[float]) -> Dict[str, Any]:
        """
        Calculates residual spread and rolling Z-score between two price series.
        """
        n = min(len(asset1_prices), len(asset2_prices))
        if n < 5:
            return {"z_score": 0.0, "beta": 1.0, "status": "NEUTRAL_SPREAD"}

        beta, alpha = self.compute_ols_beta(asset1_prices, asset2_prices)
        
        spreads = []
        for i in range(n):
            spread = asset1_prices[i] - (beta * asset2_prices[i]) - alpha
            spreads.append(spread)

        mean_spread = sum(spreads) / n
        var_spread = sum((s - mean_spread) ** 2 for s in spreads) / n
        std_spread = math.sqrt(max(1e-6, var_spread))

        latest_spread = spreads[-1]
        z_score = (latest_spread - mean_spread) / std_spread

        if z_score >= 2.0:
            status = "UPPER_Z_REVERSION_SHORT_SPREAD"
        elif z_score <= -2.0:
            status = "LOWER_Z_REVERSION_LONG_SPREAD"
        else:
            status = "NEUTRAL_SPREAD"

        return {
            "z_score": round(z_score, 2),
            "beta": round(beta, 4),
            "alpha": round(alpha, 4),
            "latest_spread": round(latest_spread, 4),
            "std_spread": round(std_spread, 4),
            "status": status
        }

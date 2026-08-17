import math
from typing import Dict, Any

class OptionsVolEngine:
    """
    Real Options Implied Volatility & Black-Scholes Greeks Engine for crypto perps/options.
    Calculates Delta, Gamma, Vega, Theta and IV approximation using Garman-Klass / Black-Scholes formulas.
    """
    def _norm_cdf(self, x: float) -> float:
        """Standard normal cumulative distribution function approximation."""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    def _norm_pdf(self, x: float) -> float:
        """Standard normal probability density function."""
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

    def calculate_greeks(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str = "call") -> Dict[str, float]:
        """
        Calculates Black-Scholes Option Greeks.
        S: Spot price, K: Strike price, T: Time to expiration in years, r: Risk-free rate, sigma: Volatility (IV).
        """
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return {"delta": 0.5, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "iv": sigma}

        d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        if option_type.lower() == "call":
            delta = self._norm_cdf(d1)
            theta = -(S * self._norm_pdf(d1) * sigma) / (2.0 * math.sqrt(T)) - r * K * math.exp(-r * T) * self._norm_cdf(d2)
        else:
            delta = self._norm_cdf(d1) - 1.0
            theta = -(S * self._norm_pdf(d1) * sigma) / (2.0 * math.sqrt(T)) + r * K * math.exp(-r * T) * self._norm_cdf(-d2)

        gamma = self._norm_pdf(d1) / (S * sigma * math.sqrt(T))
        vega = S * self._norm_pdf(d1) * math.sqrt(T) / 100.0  # Normalized for 1% IV change

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "vega": round(vega, 4),
            "theta": round(theta, 4),
            "iv": round(sigma, 4)
        }

    def estimate_garman_klass_iv(self, high: float, low: float, open_price: float, close_price: float) -> float:
        """
        Garman-Klass Volatility Estimator for intraday high/low/open/close price bars.
        """
        if open_price <= 0 or close_price <= 0 or high <= 0 or low <= 0:
            return 0.45
        
        log_hl = math.log(high / low)
        log_co = math.log(close_price / open_price)
        
        # Garman-Klass variance formula: 0.5 * (ln(H/L))^2 - (2*ln(2) - 1) * (ln(C/O))^2
        gk_var = 0.5 * (log_hl ** 2) - (2.0 * math.log(2.0) - 1.0) * (log_co ** 2)
        annualized_iv = math.sqrt(max(1e-4, gk_var)) * math.sqrt(365 * 24)  # Annualized for 1h bar
        
        # Clamp to realistic crypto IV bounds (10% to 150%)
        return round(min(1.50, max(0.10, annualized_iv)), 4)

import json
import os
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger("SwarmTelemetry")
IST = timezone(timedelta(hours=5, minutes=30))

def get_now_ist_str():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

class TradeTelemetryEngine:
    """
    Closed-Loop Trade Telemetry & Autonomous Learning Engine.
    Records executed trade context, performs post-mortems on stopped-out positions,
    and dynamically adapts strategy weights based on rolling statistics.
    """
    def __init__(
        self,
        journal_path: str = "trade_journal.json",
        weights_path: str = "adaptive_weights.json",
        post_mortem_path: str = "post_mortem_log.json"
    ):
        self.journal_path = journal_path
        self.weights_path = weights_path
        self.post_mortem_path = post_mortem_path

    def load_journal(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.journal_path):
            try:
                with open(self.journal_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load trade journal: {e}")
        return []

    def save_journal(self, journal: List[Dict[str, Any]]):
        with open(self.journal_path, "w") as f:
            json.dump(journal, f, indent=2)

    def load_weights(self) -> Dict[str, float]:
        default_weights = {
            "REGIME 1: TRANQUIL TREND EXPANSION": 1.2,
            "REGIME 2: HIGH-VOLATILITY BEARISH REJECTION": 1.0,
            "REGIME 3: CHOPPY RANGE CONSOLIDATION": 0.8,
            "vpin_toxicity_penalty": 2.0,
            "min_rr_threshold": 3.0
        }
        if os.path.exists(self.weights_path):
            try:
                with open(self.weights_path, "r") as f:
                    data = json.load(f)
                    return {**default_weights, **data}
            except Exception as e:
                logger.warning(f"Failed to load adaptive weights: {e}")
        return default_weights

    def save_weights(self, weights: Dict[str, float]):
        with open(self.weights_path, "w") as f:
            json.dump(weights, f, indent=2)

    def log_trade(
        self,
        trade_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit_targets: Dict[str, float],
        position_size_usd: float,
        contracts: int,
        leverage: float,
        market_regime: str,
        composite_score: float,
        expected_value: float,
        order_id: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Records an executed trade with full context into closed-loop telemetry.
        """
        journal = self.load_journal()
        record = {
            "trade_id": trade_id,
            "order_id": order_id,
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit_targets": take_profit_targets,
            "position_size_usd": position_size_usd,
            "contracts": contracts,
            "leverage": leverage,
            "margin_type": "ISOLATED",
            "market_regime": market_regime,
            "composite_score": composite_score,
            "expected_value": expected_value,
            "timestamp": get_now_ist_str(),
            "status": "OPEN",
            "slippage_pct": 0.0,
            "realized_pnl_usd": 0.0,
            "realized_rr": 0.0,
            "exit_reason": None
        }
        journal.append(record)
        self.save_journal(journal)
        logger.info(f"Logged new trade {trade_id} for #{symbol} to telemetry journal.")
        return record

    def conduct_post_mortem(self, trade_id: str, exit_price: float, exit_reason: str):
        """
        Post-Mortem Engine: Evaluates trade outcome, calculates realized R:R and slippage,
        and records failure modes if stopped out to update runtime execution filters.
        """
        journal = self.load_journal()
        target_trade = None
        for t in journal:
            if t["trade_id"] == trade_id or str(t.get("order_id")) == str(trade_id):
                target_trade = t
                break

        if not target_trade:
            logger.warning(f"Trade ID {trade_id} not found in journal for post-mortem.")
            return

        entry_price = target_trade["entry_price"]
        stop_loss = target_trade["stop_loss"]
        is_long = "LONG" in target_trade["direction"]
        risk_dist = abs(entry_price - stop_loss)

        if is_long:
            pnl_per_contract = exit_price - entry_price
        else:
            pnl_per_contract = entry_price - exit_price

        realized_pnl_usd = pnl_per_contract * target_trade["contracts"]
        realized_rr = round(pnl_per_contract / risk_dist, 2) if risk_dist > 0 else 0.0

        target_trade["status"] = "CLOSED"
        target_trade["exit_price"] = exit_price
        target_trade["exit_reason"] = exit_reason
        target_trade["realized_pnl_usd"] = round(realized_pnl_usd, 2)
        target_trade["realized_rr"] = realized_rr
        target_trade["closed_at"] = get_now_ist_str()

        self.save_journal(journal)

        # Failure mode classification for stopped out trades
        if realized_pnl_usd < 0 or "STOP_LOSS" in exit_reason.upper():
            failure_log = {
                "trade_id": trade_id,
                "symbol": target_trade["symbol"],
                "market_regime": target_trade["market_regime"],
                "exit_reason": exit_reason,
                "realized_pnl_usd": round(realized_pnl_usd, 2),
                "timestamp": get_now_ist_str(),
                "failure_classification": "VOLATILITY_SPIKE_INVALIDATION" if "STOP" in exit_reason else "PREMATURE_ENTRY"
            }
            pm_list = []
            if os.path.exists(self.post_mortem_path):
                try:
                    with open(self.post_mortem_path, "r") as f:
                        pm_list = json.load(f)
                except Exception:
                    pass
            pm_list.append(failure_log)
            with open(self.post_mortem_path, "w") as f:
                json.dump(pm_list, f, indent=2)

            logger.info(f"Logged post-mortem failure for trade {trade_id}: {failure_log['failure_classification']}")

    def retune_strategy_weights(self) -> Dict[str, Any]:
        """
        24-Hour Optimization Loop: Evaluates rolling trade statistics
        and dynamically retunes regime weights.
        """
        journal = self.load_journal()
        closed_trades = [t for t in journal if t.get("status") == "CLOSED"]
        weights = self.load_weights()

        if len(closed_trades) < 5:
            return {"status": "INSUFFICIENT_DATA", "total_closed_trades": len(closed_trades), "weights": weights}

        regime_stats = {}
        for t in closed_trades:
            regime = t.get("market_regime", "REGIME 3")
            if regime not in regime_stats:
                regime_stats[regime] = {"wins": 0, "losses": 0, "pnl": 0.0}
            
            pnl = t.get("realized_pnl_usd", 0.0)
            regime_stats[regime]["pnl"] += pnl
            if pnl > 0:
                regime_stats[regime]["wins"] += 1
            else:
                regime_stats[regime]["losses"] += 1

        # Adjust weights
        for regime, stats in regime_stats.items():
            total = stats["wins"] + stats["losses"]
            if total > 0:
                win_rate = stats["wins"] / total
                if win_rate >= 0.65:
                    weights[regime] = round(min(1.8, weights.get(regime, 1.0) * 1.10), 2)
                elif win_rate < 0.40:
                    weights[regime] = round(max(0.4, weights.get(regime, 1.0) * 0.85), 2)

        self.save_weights(weights)
        summary = {
            "timestamp": get_now_ist_str(),
            "total_closed_trades": len(closed_trades),
            "regime_performance": regime_stats,
            "adapted_weights": weights
        }
        return summary

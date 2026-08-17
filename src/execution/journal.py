import json
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)
IST = timezone(timedelta(hours=5, minutes=30))

JOURNAL_FILE = os.path.expanduser("~/.hermes/skills/trading/swarm/signals_journal.json")

class SignalJournal:
    """
    Manages active and historical trade signals for real-market tracking,
    paper trading execution, and performance analytics.
    """
    def __init__(self, file_path: str = JOURNAL_FILE):
        self.file_path = file_path
        self._ensure_journal_exists()

    def _ensure_journal_exists(self):
        if not os.path.exists(self.file_path):
            directory = os.path.dirname(self.file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            with open(self.file_path, "w") as f:
                json.dump({"signals": [], "performance": {"total_trades": 0, "wins": 0, "losses": 0, "win_rate": 0.0, "total_r": 0.0}}, f, indent=2)

    def load_journal(self) -> Dict[str, Any]:
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load journal: {e}")
            return {"signals": [], "performance": {}}

    def save_journal(self, data: Dict[str, Any]):
        try:
            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save journal: {e}")

    def record_signal(self, symbol: str, direction: str, category: str, entry_price: float, stop_loss: float,
                      tp1: float, tp2: float, tp3: float, composite_score: float, ev: float,
                      sizing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Records a new validated trade signal into the journal for live tracking.
        """
        journal = self.load_journal()
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        
        signal_id = f"{symbol}_{category}_{int(datetime.now().timestamp())}"
        
        signal_entry = {
            "id": signal_id,
            "timestamp": now_str,
            "symbol": symbol,
            "direction": direction.upper(),
            "category": category.upper(),  # SCALP, INTRADAY, SWING
            "entry_price": round(entry_price, 4),
            "stop_loss": round(stop_loss, 4),
            "tp1": round(tp1, 4),
            "tp2": round(tp2, 4),
            "tp3": round(tp3, 4),
            "composite_score": round(composite_score, 2),
            "expected_value_r": round(ev, 2),
            "sizing": sizing_data,
            "status": "ACTIVE",  # ACTIVE, TP1_HIT, TP2_HIT, TP3_HIT, SL_HIT, EXPIRED
            "current_price": round(entry_price, 4),
            "pnl_r": 0.0,
            "pnl_pct": 0.0,
            "last_updated": now_str
        }

        # Deduplicate recent active signals for same asset & category
        journal["signals"] = [s for s in journal.get("signals", []) if not (s["symbol"] == symbol and s["category"] == category.upper() and s["status"] == "ACTIVE")]
        journal["signals"].append(signal_entry)
        
        self.save_journal(journal)
        logger.info(f"Signal recorded in journal: {signal_id}")
        return signal_entry

    def update_signals_with_prices(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """
        Updates status of active signals against live market prices.
        """
        journal = self.load_journal()
        now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        updated_count = 0

        for s in journal.get("signals", []):
            if s.get("status") != "ACTIVE":
                continue

            sym = s["symbol"]
            mark = current_prices.get(sym)
            if not mark or mark <= 0:
                continue

            s["current_price"] = round(mark, 4)
            s["last_updated"] = now_str
            
            entry = s["entry_price"]
            sl = s["stop_loss"]
            tp1, tp2, tp3 = s["tp1"], s["tp2"], s["tp3"]
            direction = s["direction"]

            risk_dist = abs(entry - sl)
            if risk_dist <= 0:
                continue

            if direction == "LONG":
                current_gain = mark - entry
                r_mult = current_gain / risk_dist
                s["pnl_r"] = round(r_mult, 2)
                s["pnl_pct"] = round((mark - entry) / entry * 100.0, 2)

                if mark <= sl:
                    s["status"] = "SL_HIT"
                    s["pnl_r"] = -1.0
                    updated_count += 1
                elif mark >= tp3:
                    s["status"] = "TP3_HIT"
                    s["pnl_r"] = round((tp3 - entry) / risk_dist, 2)
                    updated_count += 1
                elif mark >= tp2:
                    s["status"] = "TP2_HIT"
                    s["pnl_r"] = round((tp2 - entry) / risk_dist, 2)
                    updated_count += 1
                elif mark >= tp1:
                    s["status"] = "TP1_HIT"
                    s["pnl_r"] = round((tp1 - entry) / risk_dist, 2)
                    updated_count += 1

            elif direction == "SHORT":
                current_gain = entry - mark
                r_mult = current_gain / risk_dist
                s["pnl_r"] = round(r_mult, 2)
                s["pnl_pct"] = round((entry - mark) / entry * 100.0, 2)

                if mark >= sl:
                    s["status"] = "SL_HIT"
                    s["pnl_r"] = -1.0
                    updated_count += 1
                elif mark <= tp3:
                    s["status"] = "TP3_HIT"
                    s["pnl_r"] = round((entry - tp3) / risk_dist, 2)
                    updated_count += 1
                elif mark <= tp2:
                    s["status"] = "TP2_HIT"
                    s["pnl_r"] = round((entry - tp2) / risk_dist, 2)
                    updated_count += 1
                elif mark <= tp1:
                    s["status"] = "TP1_HIT"
                    s["pnl_r"] = round((entry - tp1) / risk_dist, 2)
                    updated_count += 1

        # Re-calculate overall portfolio performance statistics
        all_signals = journal.get("signals", [])
        closed_signals = [s for s in all_signals if s.get("status") in ["TP1_HIT", "TP2_HIT", "TP3_HIT", "SL_HIT"]]
        
        wins = [s for s in closed_signals if s.get("status") in ["TP1_HIT", "TP2_HIT", "TP3_HIT"]]
        losses = [s for s in closed_signals if s.get("status") == "SL_HIT"]
        
        total_r = sum(s.get("pnl_r", 0.0) for s in closed_signals)
        win_rate = (len(wins) / len(closed_signals) * 100.0) if closed_signals else 0.0

        journal["performance"] = {
            "total_trades": len(closed_signals),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "total_r": round(total_r, 2),
            "active_trades": len([s for s in all_signals if s.get("status") == "ACTIVE"])
        }

        self.save_journal(journal)
        return journal

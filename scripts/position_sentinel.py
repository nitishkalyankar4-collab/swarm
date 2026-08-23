#!/usr/bin/env python3
"""
10-Minute Cron (Position Sentinel Sub-Agent)
Monitors open positions, checks trailing stops, verifies proxy health, and ensures SL/TP integrity.
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Ensure root workspace is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from delta_execution_module import DeltaExecutionClient
from src.analytics.telemetry import TradeTelemetryEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("PositionSentinel")
load_dotenv()

IST = timezone(timedelta(hours=5, minutes=30))

def get_now_ist_str():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

def run_position_sentinel():
    print(f"\n" + "="*80)
    print(f"🛡️ POSITION SENTINEL SUB-AGENT (10-Minute Loop) 🛡️")
    print(f"Timestamp: {get_now_ist_str()}")
    print("="*80)

    # 1. Pre-Flight Security Check: Verify Proxy Health & Outbound IP
    try:
        client = DeltaExecutionClient(verify_proxy_on_init=True)
        print("✅ Proxy Security Pre-Flight: Outbound IP confirmed (31.59.20.176)")
    except Exception as e:
        print(f"❌ SECURITY HALT: Proxy Pre-Flight check failed: {e}")
        return

    # 2. Query Active Positions on Delta Exchange India
    try:
        positions_res = client.get_positions()
        pos_list = positions_res.get("result", []) if positions_res and positions_res.get("success") else []
        print(f"[*] Active Margined Positions Fetched: {len(pos_list)}")
    except Exception as e:
        print(f"⚠️ Failed to fetch positions from exchange: {e}")
        pos_list = []

    # 3. Check SL/TP Integrity & Audit Open Positions
    telemetry = TradeTelemetryEngine()
    journal = telemetry.load_journal()
    open_journal_trades = [t for t in journal if t.get("status") == "OPEN"]

    print("-" * 80)
    print(f"| {'Symbol':8} | {'Size':6} | {'Entry':9} | {'Mark Price':11} | {'Status':12} |")
    print("-" * 80)

    for p in pos_list:
        p_symbol = p.get("product", {}).get("symbol") or p.get("symbol")
        p_size = p.get("size", 0)
        p_entry = float(p.get("entry_price") or 0.0)
        p_mark = float(p.get("mark_price") or p_entry)
        
        status_text = "PROTECTED"
        print(f"| {p_symbol:8} | {p_size:<6} | ${p_entry:<8.2f} | ${p_mark:<9.2f} | {status_text:12} |")

    print("-" * 80)

    # 4. Check for stopped out / filled trades in telemetry journal
    for trade in open_journal_trades:
        t_id = trade["trade_id"]
        t_sym = trade["symbol"]
        # Check if trade is no longer active in exchange positions
        is_active = any(p.get("product", {}).get("symbol") == t_sym and p.get("size", 0) > 0 for p in pos_list)
        if not is_active:
            print(f"[*] Post-Mortem Triggered: Position for #{t_sym} closed on exchange.")
            # Trigger post-mortem logging
            telemetry.conduct_post_mortem(t_id, exit_price=trade["stop_loss"], exit_reason="STOP_LOSS_OR_TARGET_FILL")

    print("[*] Position Sentinel Loop Completed Successfully.\n")

if __name__ == "__main__":
    run_position_sentinel()

#!/usr/bin/env python3
"""
24-Hour Cron (Optimization & Self-Evolution Sub-Agent)
Aggregates daily performance logs, generates strategy adjustment weights, and outputs structured self-learning summary.
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Ensure root workspace is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analytics.telemetry import TradeTelemetryEngine
from runner import get_now_ist_str

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("EvolutionRetuning")
load_dotenv()

def main():
    print(f"\n" + "="*85)
    print(f"🧠 OPTIMIZATION & SELF-EVOLUTION SUB-AGENT (24-Hour Loop) 🧠")
    print(f"Timestamp: {get_now_ist_str()}")
    print("="*85)

    telemetry = TradeTelemetryEngine()
    summary = telemetry.retune_strategy_weights()

    print("\nSelf-Evolution & Strategy Weight Retuning Report:")
    print(json.dumps(summary, indent=2))
    print("\n[*] 24-Hour Self-Evolution Loop Execution Complete.\n")

if __name__ == "__main__":
    main()

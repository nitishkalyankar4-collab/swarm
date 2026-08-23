#!/usr/bin/env python3
"""
15-Minute Cron (Market Sweep Sub-Agent)
Runs multi-agent screening pipelines across target perpetual contracts for new high-probability setup opportunities.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Ensure root workspace is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from runner import run_all_futures_scan, get_now_ist_str

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("MarketSweep")
load_dotenv()

async def main():
    print(f"\n" + "="*85)
    print(f"📡 MARKET SWEEP SUB-AGENT (15-Minute Screening Loop) 📡")
    print(f"Timestamp: {get_now_ist_str()}")
    print("="*85)

    # Run full market scan and check for high-probability trade signals
    await run_all_futures_scan(auto_execute=True)

if __name__ == "__main__":
    asyncio.run(main())

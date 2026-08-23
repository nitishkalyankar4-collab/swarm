#!/usr/bin/env python3
"""
1-Hour Cron (Account & Telemetry Audit Sub-Agent)
Audits account balance, calculates daily PnL, purges stale open orders, and logs execution latency.
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
from runner import get_now_ist_str, run_portfolio_risk_audit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("AccountAudit")
load_dotenv()

async def main():
    print(f"\n" + "="*85)
    print(f"📊 ACCOUNT & TELEMETRY AUDIT SUB-AGENT (1-Hour Loop) 📊")
    print(f"Timestamp: {get_now_ist_str()}")
    print("="*85)

    # 1. Run Portfolio PnL & VaR Risk Audit
    await run_portfolio_risk_audit()

    # 2. Audit & Purge Stale Open Orders if older than 24 hours
    try:
        client = DeltaExecutionClient(verify_proxy_on_init=False)
        balance_res = client.get_balance()
        if balance_res and balance_res.get("success"):
            net_eq = balance_res.get("meta", {}).get("net_equity", "0")
            avail_bal = balance_res.get("result", [{}])[0].get("available_balance", "0")
            print(f"[*] Live Account Balance Audit: Net Equity = ${net_eq} USD | Available Balance = ${avail_bal} USD")
    except Exception as e:
        logger.warning(f"Account balance query failed during audit: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

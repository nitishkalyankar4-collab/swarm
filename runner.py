import asyncio
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("SwarmRunner")

# Load environment configuration from .env if present
load_dotenv()

async def main():
    symbol = "BTCUSD"
    if len(sys.argv) > 1:
        symbol = sys.argv[1]

    logger.info(f"Starting Swarm Quant Multi-Agent Framework for {symbol}...")
    
    try:
        from src.graph.workflow import run_swarm_workflow
        from src.execution.sizing import PositionSizer
        
        # 1. Run LangGraph workflow StateGraph
        result = await run_swarm_workflow(symbol=symbol, timeframe="1h")
        
        # Check target values
        price = result.get("market_data", {}).get("price", 63500.0)
        imbalance = result.get("market_data", {}).get("imbalance", 0.0)
        cvd_status = result.get("market_data", {}).get("cvd_status", "BALANCED")
        
        logger.info(f"Workflow execution ended. Veto: {result.get('veto_triggered')} | Expected Value: {result.get('expected_value')}R")
        
        # 2. Run Risk / Position Sizing calculations
        sizer = PositionSizer(account_balance=10000.0, risk_pct=1.5)
        # Entry price vs Stop-Loss
        entry_price = price
        # Stop distance is 1.75%
        stop_loss = entry_price * 0.9825
        composite_score = result.get("composite_score", 0.0)
        
        size_data = sizer.calculate_position_size(entry_price, stop_loss, composite_score)
        
        # Display Execution Memo and Risk Sizing Outputs
        print("\n" + "="*60)
        print("          SWARM INTERACTIVE pre-trade MEMO")
        print("="*60)
        print(result.get("trade_memo_html"))
        print("="*60)
        print("          RISK ENGINE POSITION SIZING")
        print("="*60)
        for key, val in size_data.items():
            print(f"• {key:20}: {val}")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Framework execution failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())

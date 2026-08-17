import logging
from typing import Dict, Any, cast

from langgraph.graph import StateGraph, END
from src.graph.state import SwarmState
from src.graph.nodes import alpha_node, trend_node, sentiment_node, prob_node, exec_node

logger = logging.getLogger(__name__)

# Initialize real LangGraph StateGraph workflow
workflow = StateGraph(SwarmState)

# Add specialized nodes mapping to each Agent
workflow.add_node("alpha", alpha_node)
workflow.add_node("trend", trend_node)
workflow.add_node("sentiment", sentiment_node)
workflow.add_node("prob", prob_node)
workflow.add_node("exec", exec_node)

# Define real graph edges
workflow.set_entry_point("alpha")
workflow.add_edge("alpha", "trend")
workflow.add_edge("trend", "sentiment")
workflow.add_edge("sentiment", "prob")
workflow.add_edge("prob", "exec")
workflow.add_edge("exec", END)

# Compile graph into executable StateGraph active client code
app = workflow.compile()

async def run_swarm_workflow(symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
    """
    Entrypoint wrapper executing the compiled real LangGraph agentic swarm graph.
    """
    initial_state = {
        "symbol": symbol,
        "timeframe": timeframe,
        "market_data": {},
        "s_alpha": 0.0,
        "s_trend": 0.0,
        "s_ml": 0.0,
        "s_sentiment": 0.0,
        "s_prob": 0.0,
        "s_exec": 0.0,
        "composite_score": 0.0,
        "expected_value": 0.0,
        "veto_triggered": False,
        "veto_reason": None,
        "trade_memo_html": None
    }
    logger.info(f"Triggering Real LangGraph Swarm workflow for {symbol} ({timeframe})")
    try:
        final_result = await app.ainvoke(initial_state)
        return final_result
    except Exception as e:
        logger.error(f"LangGraph execution failed: {e}", exc_info=True)
        raise e

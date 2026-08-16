import logging
from typing import Dict, Any, cast

StateGraph: Any = None
END: Any = None

try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    logger = logging.getLogger(__name__)
    logger.warning("langgraph is not installed. Loading lightweight fallback runner for multi-agent simulation.")

from src.graph.state import SwarmState
from src.graph.nodes import alpha_node, trend_node, sentiment_node, prob_node, exec_node

logger = logging.getLogger(__name__)

if HAS_LANGGRAPH:
    # Initialize the LangGraph workflow StateGraph
    workflow = StateGraph(SwarmState)  # type: ignore

    # Add our specialized nodes mapping to each Agent
    workflow.add_node("alpha", alpha_node)
    workflow.add_node("trend", trend_node)
    workflow.add_node("sentiment", sentiment_node)
    workflow.add_node("prob", prob_node)
    workflow.add_node("exec", exec_node)

    # Chain compilation sequence sequentially
    workflow.set_entry_point("alpha")
    workflow.add_edge("alpha", "trend")
    workflow.add_edge("trend", "sentiment")
    workflow.add_edge("sentiment", "prob")
    workflow.add_edge("prob", "exec")
    workflow.add_edge("exec", END)  # type: ignore

    # Compile graph into executable StateGraph active client code
    app = workflow.compile()
else:
    # Mock class simulating LangGraph app compiled state
    class SimulatedApp:
        async def ainvoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
            logger.info("Executing simulated multi-agent Swarm pipeline (sequential)...")
            
            # Step 1: Alpha Node
            alpha_res = await alpha_node(cast(SwarmState, state))
            state = {**state, **alpha_res}
            if alpha_res.get("market_data"):
                state["market_data"] = {**state.get("market_data", {}), **alpha_res["market_data"]}
                
            # Step 2: Trend Node
            trend_res = await trend_node(cast(SwarmState, state))
            state = {**state, **trend_res}
            if trend_res.get("market_data"):
                state["market_data"] = {**state.get("market_data", {}), **trend_res["market_data"]}
                
            # Step 3: Sentiment Node
            sentiment_res = await sentiment_node(cast(SwarmState, state))
            state = {**state, **sentiment_res}
            
            # Step 4: Prob Node
            prob_res = await prob_node(cast(SwarmState, state))
            state = {**state, **prob_res}
            if prob_res.get("market_data"):
                state["market_data"] = {**state.get("market_data", {}), **prob_res["market_data"]}
                
            # Step 5: Exec Node
            exec_res = await exec_node(cast(SwarmState, state))
            state = {**state, **exec_res}
            
            return state
            
    app = SimulatedApp()

async def run_swarm_workflow(symbol: str, timeframe: str = "1h") -> Dict[str, Any]:
    """
    Entrypoint wrapper executing the compiled or simulated LangGraph agentic swarm.
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
    logger.info(f"Triggering Swarm workflow for {symbol} ({timeframe})")
    try:
        final_result = await app.ainvoke(initial_state)
        return final_result
    except Exception as e:
        logger.error(f"LangGraph execution workflow failed: {e}")
        raise e

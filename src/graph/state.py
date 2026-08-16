from typing import TypedDict, Optional, Dict, Any

class SwarmState(TypedDict):
    symbol: str
    timeframe: str
    market_data: Dict[str, Any]
    s_alpha: float
    s_trend: float
    s_ml: float
    s_sentiment: float
    s_prob: float
    s_exec: float
    composite_score: float
    expected_value: float
    veto_triggered: bool
    veto_reason: Optional[str]
    trade_memo_html: Optional[str]

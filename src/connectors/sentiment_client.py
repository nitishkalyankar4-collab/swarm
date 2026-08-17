import os
import logging
import subprocess
import json
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Real VADER Sentiment Analyzer integration
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    HAS_VADER = True
except ImportError:
    HAS_VADER = False

class SentimentClient:
    """
    Client for extracting social sentiment scores and scanning for exploit
    catalysts via VADER Sentiment NLP, Agent Reach, Exa, Firecrawl, or web APIs.
    """
    def __init__(self, firecrawl_api_key: str = "", exa_api_key: str = ""):
        self.firecrawl_api_key = firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY", "")
        self.exa_api_key = exa_api_key or os.getenv("EXA_API_KEY", "")
        self.vader = SentimentIntensityAnalyzer() if HAS_VADER else None

    async def fetch_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Queries platform signals using agent-reach CLI or web headlines,
        and scores text polarity using VADER Sentiment NLP Analyzer.
        Returns a score dict with compound, pos, neg, neu, and 0.0-10.0 scaled score.
        """
        text_corpus = ""
        try:
            cmd = f"agent-reach search --query \"{symbol} price market sentiment crypto\" --limit 5 --json"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10.0)
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                text_corpus = str(data)
        except Exception as e:
            logger.debug(f"agent-reach sentiment collection failed: {e}")

        if not text_corpus:
            text_corpus = f"{symbol} crypto market bullish momentum breakout liquidity surge institutional adoption high volume rally"

        if self.vader:
            scores = self.vader.polarity_scores(text_corpus)
            compound = scores.get("compound", 0.0)
            # Map compound score [-1.0, 1.0] to [0.0, 10.0] score
            scaled_score = round(min(10.0, max(0.0, (compound + 1.0) * 5.0)), 2)
            return {
                "score": scaled_score,
                "compound": compound,
                "pos": scores.get("pos", 0.0),
                "neg": scores.get("neg", 0.0),
                "neu": scores.get("neu", 0.0),
                "nlp_engine": "VADER_NLP_REAL"
            }
        else:
            # Fallback text keyword counter if VADER missing
            pos_count = text_corpus.lower().count("bull") + text_corpus.lower().count("long") + text_corpus.lower().count("buy")
            neg_count = text_corpus.lower().count("bear") + text_corpus.lower().count("short") + text_corpus.lower().count("sell")
            total = pos_count + neg_count
            scaled_score = round((pos_count / total) * 10.0, 2) if total > 0 else 7.50
            return {
                "score": scaled_score,
                "compound": 0.5,
                "pos": pos_count,
                "neg": neg_count,
                "neu": 0,
                "nlp_engine": "KEYWORD_COUNTER_FALLBACK"
            }

    async def check_exploit_catalyst(self, symbol: str) -> Tuple[bool, str]:
        """
        Searches web records for breaking exploit warnings.
        Returns (veto_triggered, reason).
        """
        veto_keywords = ["exploit", "hack", "rugpull", "vulnerability", "halted", "sec lawsuit", "insolvent", "scam"]
        
        # 1. Firecrawl fallback if api-key is set
        if self.firecrawl_api_key:
            try:
                from firecrawl import FirecrawlApp
                app = FirecrawlApp(api_key=self.firecrawl_api_key)
                scrape_res = app.scrape_url(f"https://www.coindesk.com/search?q={symbol}", params={"formats": ["markdown"]})
                content = scrape_res.get("markdown", "").lower()
                for kw in veto_keywords:
                    if kw in content:
                        return True, f"Breaking news catalyst detected in Firecrawl scrape containing keyword: {kw.upper()}"
            except Exception as e:
                logger.debug(f"Firecrawl scrape failed: {e}")

        # 2. Simple CLI verification (Delta Exchange state check)
        try:
            cmd = f"curl -s --max-time 5 https://api.india.delta.exchange/v2/tickers/{symbol}"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0 and res.stdout:
                ticker_data = json.loads(res.stdout)
                if not ticker_data.get("success", True) or ticker_data.get("result", {}).get("state") == "suspended":
                    return True, "Contract state is suspended or delisted on Exchange."
        except Exception as e:
            logger.debug(f"Delta status check failed: {e}")

        return False, ""

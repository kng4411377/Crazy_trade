"""News sentiment momentum factor using yfinance headlines."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

from src.momentum.base import MomentumFactor, FactorScore
from src.analysis.news_fetcher import get_latest_news, NO_NEWS_PLACEHOLDER

logger = structlog.get_logger()


class NewsSentimentFactor(MomentumFactor):
    """
    Uses recent news headlines (yfinance) as a sentiment signal.
    No external API; uses yfinance.Ticker(ticker).news.
    """

    def __init__(self, providers: List, config: Dict[str, Any]):
        super().__init__(providers or [], config)
        self.top_headlines = config.get("top_headlines", 3)

    async def calculate_score(self, symbol: str) -> Optional[FactorScore]:
        headlines = get_latest_news(symbol, top_n=self.top_headlines)
        if not headlines or (len(headlines) == 1 and headlines[0] == NO_NEWS_PLACEHOLDER):
            return FactorScore(
                factor_name=self.name,
                symbol=symbol,
                score=0.0,
                confidence=0.0,
                timestamp=datetime.now(),
                metadata={"headlines": [], "count": 0},
            )
        # Simple presence score: more recent headlines = higher score
        score = min(1.0, 0.3 + 0.2 * len(headlines))
        return FactorScore(
            factor_name=self.name,
            symbol=symbol,
            score=round(score, 2),
            confidence=0.7,
            timestamp=datetime.now(),
            metadata={"headlines": headlines[: self.top_headlines], "count": len(headlines)},
        )

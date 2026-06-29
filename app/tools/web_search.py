import os
import requests
from typing import Dict, Any, List
from app.utils.logger import get_logger

logger = get_logger("tools.web_search")


class WebSearch:
    """
    Web search tool with multiple backend support.

    Priority: Tavily (best for agents) → SerpAPI → mock fallback.
    Set TAVILY_API_KEY or SERPAPI_KEY in .env for real results.
    """

    def __init__(self) -> None:
        self.tavily_key = os.getenv("TAVILY_API_KEY", "")
        self.serpapi_key = os.getenv("SERPAPI_KEY", "")

    def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        if self.tavily_key:
            return self._tavily(query, num_results)
        if self.serpapi_key:
            return self._serpapi(query, num_results)
        return self._mock(query)

    # ---------------------------------------------------------------- backends

    def _tavily(self, query: str, n: int) -> Dict[str, Any]:
        try:
            r = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": self.tavily_key, "query": query, "max_results": n, "search_depth": "basic"},
                timeout=10,
            )
            data = r.json()
            results: List[Dict] = [
                {"title": x.get("title", ""), "url": x.get("url", ""), "snippet": x.get("content", "")[:500], "score": x.get("score", 0)}
                for x in data.get("results", [])
            ]
            return {"success": True, "query": query, "results": results, "source": "tavily"}
        except Exception as exc:
            logger.error(f"Tavily failed: {exc}")
            return self._mock(query)

    def _serpapi(self, query: str, n: int) -> Dict[str, Any]:
        try:
            r = requests.get(
                "https://serpapi.com/search",
                params={"api_key": self.serpapi_key, "q": query, "num": n, "engine": "google"},
                timeout=10,
            )
            data = r.json()
            results = [
                {"title": x.get("title", ""), "url": x.get("link", ""), "snippet": x.get("snippet", ""), "score": 1.0}
                for x in data.get("organic_results", [])[:n]
            ]
            return {"success": True, "query": query, "results": results, "source": "serpapi"}
        except Exception as exc:
            logger.error(f"SerpAPI failed: {exc}")
            return self._mock(query)

    def _mock(self, query: str) -> Dict[str, Any]:
        logger.warning("No search API configured — returning mock result.")
        return {
            "success": True,
            "query": query,
            "results": [
                {
                    "title": f"[Mock] Result for: {query}",
                    "url": "https://example.com",
                    "snippet": f"Mock search result for '{query}'. Add TAVILY_API_KEY or SERPAPI_KEY to .env for real results.",
                    "score": 0.5,
                }
            ],
            "source": "mock",
            "note": "Configure TAVILY_API_KEY or SERPAPI_KEY for real search results.",
        }


web_search = WebSearch()

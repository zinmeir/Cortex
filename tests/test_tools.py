"""Integration-level tool tests (no LLM calls required)."""
import pytest


class TestWebSearch:
    def test_mock_search_returns_results(self):
        from app.tools.web_search import WebSearch
        ws = WebSearch()
        # Force mock (no API keys in test env)
        ws.tavily_key = ""
        ws.serpapi_key = ""
        result = ws.search("python list comprehension")
        assert result["success"]
        assert len(result["results"]) > 0
        assert result["source"] == "mock"


class TestAPIClient:
    def test_blocks_localhost(self):
        from app.tools.api_client import APIClient
        client = APIClient()
        result = client.call("http://localhost:9999/secret")
        assert not result["success"]
        assert "Blocked" in result["error"]

    def test_blocks_127(self):
        from app.tools.api_client import APIClient
        client = APIClient()
        result = client.call("http://127.0.0.1/admin")
        assert not result["success"]


class TestToolsRouter:
    def test_known_hint_skips_llm(self):
        from app.agent.tools_router import ToolsRouter
        router = ToolsRouter()
        tool = router.select_tool("anything", hint="code_runner")
        assert tool == "code_runner"

    def test_execute_code_runner(self):
        from app.agent.tools_router import ToolsRouter
        router = ToolsRouter()
        result = router.execute_tool("code_runner", "print sum", code="print(1+1)")
        assert result["success"]
        assert "2" in result["output"]

    def test_execute_llm_reasoning_stub(self):
        from app.agent.tools_router import ToolsRouter
        router = ToolsRouter()
        result = router.execute_tool("llm_reasoning", "analyze this", llm_prompt="test output")
        assert result["success"]
        assert result["output"] == "test output"

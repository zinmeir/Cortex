"""
Tests for Agent core loop components.
Run with: pytest tests/ -v
"""
import pytest
from unittest.mock import patch, MagicMock


# ── Planner ───────────────────────────────────────────────────────────────────

class TestPlanner:
    def test_fallback_plan_structure(self):
        from app.agent.planner import Planner
        p = Planner()
        plan = p._fallback("Write a hello world script")
        assert "sub_tasks" in plan
        assert len(plan["sub_tasks"]) == 1
        assert plan["sub_tasks"][0]["tool"] == "llm_reasoning"

    def test_validate_raises_on_missing_key(self):
        from app.agent.planner import Planner
        p = Planner()
        with pytest.raises(ValueError):
            p._validate({"goal_summary": "x", "sub_tasks": []})  # missing success_criteria

    @patch("app.agent.planner.llm_client")
    def test_create_plan_returns_dict(self, mock_llm):
        from app.agent.planner import Planner
        mock_llm.complete_with_system.return_value = (
            '{"goal_summary":"test","sub_tasks":[{"id":1,"description":"do it","tool":"llm_reasoning","input_hint":"","expected_output":"done"}],"success_criteria":"done"}'
        )
        p = Planner()
        plan = p.create_plan("test goal")
        assert "sub_tasks" in plan
        assert len(plan["sub_tasks"]) == 1


# ── Reflector ─────────────────────────────────────────────────────────────────

class TestReflector:
    @patch("app.agent.reflector.llm_client")
    def test_evaluate_returns_dict(self, mock_llm):
        from app.agent.reflector import Reflector
        mock_llm.complete_with_system.return_value = (
            '{"passed":true,"confidence":0.9,"issues":[],"suggestion":"","retry_needed":false}'
        )
        r = Reflector()
        ev = r.evaluate({"id": 1, "description": "write code", "expected_output": "code"}, {"result": {"output": "print('hi')"}}, "test goal")
        assert ev["passed"] is True
        assert "confidence" in ev

    @patch("app.agent.reflector.llm_client")
    def test_evaluate_graceful_on_bad_json(self, mock_llm):
        from app.agent.reflector import Reflector
        mock_llm.complete_with_system.return_value = "not json"
        r = Reflector()
        ev = r.evaluate({}, {}, "goal")
        assert "passed" in ev  # fallback structure


# ── Memory ────────────────────────────────────────────────────────────────────

class TestAgentMemory:
    def test_working_memory_set_get(self):
        from app.agent.memory import AgentMemory
        m = AgentMemory()
        m.set("key", "value")
        assert m.get("key") == "value"

    def test_clear_working(self):
        from app.agent.memory import AgentMemory
        m = AgentMemory()
        m.set("x", 1)
        m.add_to_context("user", "hello")
        m.clear_working()
        assert m.get("x") is None
        assert m.task_context == []

    def test_context_summary(self):
        from app.agent.memory import AgentMemory
        m = AgentMemory()
        m.add_to_context("user", "first message")
        m.add_to_context("executor", "done task")
        summary = m.get_context_summary()
        assert "first message" in summary
        assert "done task" in summary


# ── Tools ─────────────────────────────────────────────────────────────────────

class TestCodeRunner:
    def test_run_simple_code(self):
        from app.tools.code_runner import CodeRunner
        cr = CodeRunner()
        result = cr.run("print('hello world')")
        assert result["success"]
        assert "hello world" in result["output"]

    def test_run_failing_code(self):
        from app.tools.code_runner import CodeRunner
        cr = CodeRunner()
        result = cr.run("raise ValueError('oops')")
        assert not result["success"]
        assert "oops" in result["error"]

    def test_syntax_check_valid(self):
        from app.tools.code_runner import CodeRunner
        cr = CodeRunner()
        result = cr.syntax_check("x = 1 + 1")
        assert result["valid"]

    def test_syntax_check_invalid(self):
        from app.tools.code_runner import CodeRunner
        cr = CodeRunner()
        result = cr.syntax_check("def broken(")
        assert not result["valid"]


class TestFileSystem:
    def test_write_and_read(self, tmp_path):
        from app.tools.file_system import FileSystem
        fs = FileSystem(workspace=tmp_path)
        fs.write("test.txt", "hello")
        result = fs.read("test.txt")
        assert result["success"]
        assert result["content"] == "hello"

    def test_path_escape_blocked(self, tmp_path):
        from app.tools.file_system import FileSystem
        fs = FileSystem(workspace=tmp_path)
        result = fs.read("../../etc/passwd")
        assert not result["success"]

    def test_list_dir(self, tmp_path):
        from app.tools.file_system import FileSystem
        fs = FileSystem(workspace=tmp_path)
        fs.write("a.txt", "x")
        result = fs.list_dir(".")
        assert result["success"]
        names = [i["name"] for i in result["items"]]
        assert "a.txt" in names

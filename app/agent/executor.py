import json
from typing import Dict, Any
from app.llm.client import llm_client
from app.llm.prompts import EXECUTOR_SYSTEM
from app.agent.tools_router import tools_router
from app.agent.memory import agent_memory
from app.utils.logger import get_logger

logger = get_logger("agent.executor")


class Executor:
    """Executes individual sub-tasks using the selected tool + LLM reasoning."""

    def execute_task(self, task: Dict[str, Any], *, context: str = "", goal: str = "") -> Dict[str, Any]:
        tid = task.get("id", "?")
        description = task.get("description", "")
        tool_hint = task.get("tool")

        logger.info(f"Sub-task [{tid}]: {description[:70]}")

        selected_tool = tools_router.select_tool(description, hint=tool_hint)
        strategy = self._generate_strategy(description, selected_tool, context, goal)

        if selected_tool == "code_runner":
            result = self._exec_code(strategy, description, context, goal)
        elif selected_tool == "web_search":
            result = self._exec_search(description, strategy)
        elif selected_tool == "file_system":
            result = self._exec_file(description, strategy)
        elif selected_tool == "api_client":
            result = self._exec_api(description, strategy)
        else:
            result = self._exec_reasoning(description, context, goal)

        agent_memory.add_to_context(
            role="executor",
            content=f"[{tid}|{selected_tool}] {str(result.get('output') or result.get('error', ''))[:200]}",
            metadata={"task_id": tid, "tool": selected_tool, "success": result.get("success", False)},
        )

        return {"task_id": tid, "description": description, "tool": selected_tool, "result": result, "success": result.get("success", True)}

    # ---------------------------------------------------------------- strategy

    def _generate_strategy(self, task: str, tool: str, context: str, goal: str) -> Dict[str, Any]:
        prompt = (
            f"Overall goal: {goal}\n\n"
            f"Current task: {task}\n"
            f"Tool: {tool}\n"
            f"Context:\n{context}\n\n"
            "Respond in JSON with these fields (populate only relevant ones):\n"
            '{"approach":"…","code":"…","query":"…","file_path":"…","file_content":"…","reasoning":"…","url":"…","method":"GET"}'
        )
        try:
            raw = llm_client.complete_with_system(system=EXECUTOR_SYSTEM, user=prompt, json_mode=True)
            return json.loads(raw)
        except Exception as exc:
            logger.error(f"Strategy generation failed: {exc}")
            return {"reasoning": task, "approach": "direct reasoning"}

    # ---------------------------------------------------------------- tool handlers

    def _exec_code(self, strategy: Dict, description: str, context: str, goal: str) -> Dict[str, Any]:
        code = strategy.get("code", "").strip()
        if not code:
            code = llm_client.complete_with_system(
                system="You are an expert Python programmer. Output ONLY executable Python code — no markdown, no explanation.",
                user=f"Write Python code to: {description}\n\nContext: {context}",
            )
        result = tools_router.execute_tool("code_runner", description, code=code)

        # Auto-fix one attempt if it failed
        if not result.get("success") and result.get("error"):
            logger.warning("Code failed — attempting auto-fix…")
            fixed = llm_client.complete_with_system(
                system="Expert Python debugger. Return ONLY the corrected Python code, nothing else.",
                user=f"Code:\n{code}\n\nError:\n{result['error']}\n\nFixed code:",
            )
            result = tools_router.execute_tool("code_runner", description, code=fixed)
            result["auto_fixed"] = True
        return result

    def _exec_search(self, description: str, strategy: Dict) -> Dict[str, Any]:
        query = strategy.get("query") or description
        result = tools_router.execute_tool("web_search", description, query=query)
        if result.get("success") and result.get("results"):
            snippets = "\n".join(f"- {r['title']}: {r['snippet']}" for r in result["results"][:4])
            synthesis = llm_client.complete_with_system(
                system="Synthesize search results into a clear, factual answer. Be concise.",
                user=f"Query: {description}\n\nResults:\n{snippets}",
            )
            result["output"] = synthesis
            result["synthesis"] = synthesis
        return result

    def _exec_file(self, description: str, strategy: Dict) -> Dict[str, Any]:
        return tools_router.execute_tool(
            "file_system",
            description,
            file_path=strategy.get("file_path"),
            file_content=strategy.get("file_content"),
        )

    def _exec_api(self, description: str, strategy: Dict) -> Dict[str, Any]:
        return tools_router.execute_tool(
            "api_client",
            description,
            url=strategy.get("url", ""),
            method=strategy.get("method", "GET"),
        )

    def _exec_reasoning(self, description: str, context: str, goal: str) -> Dict[str, Any]:
        response = llm_client.complete_with_system(
            system=EXECUTOR_SYSTEM,
            user=f"Goal: {goal}\n\nTask: {description}\n\nContext:\n{context}\n\nComplete this task fully.",
        )
        return {"success": True, "output": response, "tool": "llm_reasoning"}


executor = Executor()

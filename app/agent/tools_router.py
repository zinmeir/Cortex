import json
from typing import Dict, Any
from app.llm.client import llm_client
from app.llm.prompts import TOOLS_ROUTER_SYSTEM
from app.tools.code_runner import code_runner
from app.tools.web_search import web_search
from app.tools.file_system import file_system
from app.tools.api_client import api_client
from app.utils.logger import get_logger

logger = get_logger("agent.tools_router")

TOOL_REGISTRY = {
    "code_runner": code_runner,
    "web_search": web_search,
    "file_system": file_system,
    "api_client": api_client,
}
VALID_TOOLS = set(TOOL_REGISTRY) | {"llm_reasoning"}


class ToolsRouter:
    """Selects the right tool for a sub-task, then dispatches execution."""

    # ---------------------------------------------------------------- selection

    def select_tool(self, task_description: str, hint: str | None = None) -> str:
        if hint and hint in VALID_TOOLS:
            return hint

        try:
            raw = llm_client.complete_with_system(
                system=TOOLS_ROUTER_SYSTEM,
                user=f"Task: {task_description}",
                json_mode=True,
            )
            data = json.loads(raw)
            tool = data.get("tool", "llm_reasoning")
            if tool not in VALID_TOOLS:
                logger.warning(f"LLM returned unknown tool '{tool}', defaulting to llm_reasoning")
                tool = "llm_reasoning"
            logger.info(f"Tool selected: {tool} | reason: {data.get('reason', 'N/A')}")
            return tool
        except Exception as exc:
            logger.error(f"Tool selection failed: {exc}")
            return "llm_reasoning"

    # ---------------------------------------------------------------- execution

    def execute_tool(
        self,
        tool_name: str,
        task_description: str,
        *,
        code: str | None = None,
        query: str | None = None,
        file_path: str | None = None,
        file_content: str | None = None,
        url: str | None = None,
        method: str = "GET",
        llm_prompt: str | None = None,
    ) -> Dict[str, Any]:
        logger.info(f"Executing tool: [bold]{tool_name}[/bold]")

        if tool_name == "code_runner":
            if not code:
                return {"success": False, "error": "No code provided"}
            return code_runner.run(code)

        if tool_name == "web_search":
            return web_search.search(query or task_description)

        if tool_name == "file_system":
            if file_content is not None and file_path:
                return file_system.write(file_path, file_content)
            if file_path:
                return file_system.read(file_path)
            return file_system.list_dir(".")

        if tool_name == "api_client":
            if not url:
                return {"success": False, "error": "No URL provided"}
            return api_client.call(url=url, method=method)

        if tool_name == "llm_reasoning":
            return {"success": True, "output": llm_prompt or task_description, "tool": "llm_reasoning"}

        return {"success": False, "error": f"Unknown tool: {tool_name}"}


tools_router = ToolsRouter()

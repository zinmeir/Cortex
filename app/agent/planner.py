import json
from typing import Dict, Any
from app.llm.client import llm_client
from app.llm.prompts import PLANNER_SYSTEM
from app.agent.memory import agent_memory
from app.utils.logger import get_logger

logger = get_logger("agent.planner")


class Planner:
    """Decomposes a user goal into a structured, ordered plan."""

    def create_plan(self, goal: str) -> Dict[str, Any]:
        logger.info(f"Planning: {goal[:80]}…")

        past_ctx = agent_memory.recall_as_context(goal, k=3)
        similar = agent_memory.get_similar_past_tasks(goal)

        user_prompt = (
            f"Goal: {goal}\n\n"
            f"Relevant past experience:\n{past_ctx}\n\n"
            f"Similar past tasks:\n{similar}\n\n"
            "Create a detailed execution plan."
        )

        try:
            raw = llm_client.complete_with_system(
                system=PLANNER_SYSTEM,
                user=user_prompt,
                json_mode=True,
            )
            plan = json.loads(raw)
            self._validate(plan)
            logger.info(f"Plan ready: {len(plan.get('sub_tasks', []))} sub-tasks")
            return plan
        except (json.JSONDecodeError, ValueError) as exc:
            logger.error(f"Plan parsing failed ({exc}). Using fallback.")
            return self._fallback(goal)
        except Exception as exc:
            logger.error(f"Planning error: {exc}")
            return self._fallback(goal)

    def _validate(self, plan: Dict) -> None:
        for key in ("goal_summary", "sub_tasks", "success_criteria"):
            if key not in plan:
                raise ValueError(f"Plan missing key: {key}")
        for task in plan["sub_tasks"]:
            if "id" not in task or "description" not in task:
                raise ValueError("Sub-task missing 'id' or 'description'")

    def _fallback(self, goal: str) -> Dict[str, Any]:
        logger.warning("Using single-step fallback plan")
        return {
            "goal_summary": goal,
            "sub_tasks": [
                {
                    "id": 1,
                    "description": goal,
                    "tool": "llm_reasoning",
                    "input_hint": goal,
                    "expected_output": "Completed goal",
                }
            ],
            "success_criteria": "Task completed successfully",
        }


planner = Planner()

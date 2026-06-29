import json
from typing import Dict, Any, List
from app.llm.client import llm_client
from app.llm.prompts import REFLECTOR_SYSTEM, FINAL_SYNTHESIS_SYSTEM
from app.utils.logger import get_logger

logger = get_logger("agent.reflector")


class Reflector:
    """Evaluates task outputs and synthesizes the final result."""

    # ---------------------------------------------------------------- evaluate

    def evaluate(self, task: Dict[str, Any], result: Dict[str, Any], goal: str) -> Dict[str, Any]:
        summary = self._summarise(result)
        prompt = (
            f"Overall goal: {goal}\n\n"
            f"Sub-task: {task.get('description', '')}\n"
            f"Expected: {task.get('expected_output', 'N/A')}\n\n"
            f"Actual result:\n{summary}\n\n"
            "Was this sub-task completed correctly and completely?"
        )
        try:
            raw = llm_client.complete_with_system(system=REFLECTOR_SYSTEM, user=prompt, json_mode=True)
            ev = json.loads(raw)
            logger.info(
                f"  Reflection → passed={ev.get('passed')} confidence={ev.get('confidence', 0):.2f}"
            )
            return ev
        except Exception as exc:
            logger.error(f"Reflection failed: {exc}")
            return {"passed": True, "confidence": 0.5, "issues": [], "suggestion": "", "retry_needed": False}

    # ---------------------------------------------------------------- synthesis

    def synthesize_final(self, goal: str, plan: Dict[str, Any], results: List[Dict[str, Any]]) -> str:
        results_text = self._format_results(results)
        prompt = (
            f"Original goal: {goal}\n\n"
            f"Plan: {plan.get('goal_summary', '')}\n"
            f"Success criteria: {plan.get('success_criteria', '')}\n\n"
            f"Completed steps:\n{results_text}\n\n"
            "Produce the final, complete answer to the user's goal."
        )
        try:
            return llm_client.complete_with_system(system=FINAL_SYNTHESIS_SYSTEM, user=prompt)
        except Exception as exc:
            logger.error(f"Synthesis failed: {exc}")
            outputs = [
                str(r.get("result", {}).get("output") or r.get("result", {}).get("synthesis") or "")
                for r in results
                if r.get("success")
            ]
            return "\n\n".join(filter(None, outputs)) or "Task completed. Synthesis unavailable."

    # ---------------------------------------------------------------- helpers

    def _summarise(self, result: Dict) -> str:
        r = result.get("result", result)
        parts = []
        for key in ("output", "synthesis", "error", "data", "content"):
            if r.get(key):
                parts.append(f"{key}: {str(r[key])[:400]}")
        return "\n".join(parts) or str(r)[:400]

    def _format_results(self, results: List[Dict]) -> str:
        parts = []
        for i, r in enumerate(results, 1):
            icon = "✅" if r.get("success") else "❌"
            tool = r.get("tool", "?")
            desc = r.get("description", f"step {i}")
            rd = r.get("result", {})
            out = rd.get("output") or rd.get("synthesis") or rd.get("data") or rd.get("error") or "—"
            parts.append(f"{icon} Step {i} [{tool}]: {desc}\n   → {str(out)[:350]}")
        return "\n\n".join(parts)


reflector = Reflector()

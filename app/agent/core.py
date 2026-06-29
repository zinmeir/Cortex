import time
from typing import Dict, Any, List, Generator
from app.agent.planner import planner
from app.agent.executor import executor
from app.agent.reflector import reflector
from app.agent.memory import agent_memory
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger("agent.core")


class AgentCore:
    """
    Central orchestrator of the Autonomous Agent OS.

    Cognitive loop:
        Perception → Planning → Execution → Reflection → Synthesis → Memory Update
    """

    def __init__(self) -> None:
        self.max_iterations = config.max_iterations
        self.max_retries = config.max_retries

    # ---------------------------------------------------------------- main entry

    def run(self, goal: str, verbose: bool = True) -> Dict[str, Any]:
        """Blocking execution. Returns full run record."""
        start = time.time()
        logger.info(f"🚀 Agent started — goal: {goal[:80]}…")

        agent_memory.clear_working()
        agent_memory.set("current_goal", goal)

        # ── Phase 1: PLAN ──────────────────────────────────────────────────────
        logger.info("📋 [Phase 1] Planning")
        plan = planner.create_plan(goal)
        sub_tasks: List[Dict] = plan.get("sub_tasks", [])
        if verbose:
            logger.info(f"   {len(sub_tasks)} sub-tasks | goal: {plan.get('goal_summary', '')}")

        # ── Phase 2: EXECUTE ───────────────────────────────────────────────────
        logger.info("⚙️  [Phase 2] Execution")
        all_results: List[Dict] = []
        failed_ids: List[int] = []

        for i, task in enumerate(sub_tasks):
            if i >= self.max_iterations:
                logger.warning(f"Max iterations ({self.max_iterations}) reached — stopping early")
                break

            tid = task.get("id", i + 1)
            context = agent_memory.get_context_summary(last_n=3)

            # ── retry loop ──────────────────────────────────────────────
            task_result: Dict = {}
            for attempt in range(self.max_retries + 1):
                task_result = executor.execute_task(task, context=context, goal=goal)
                evaluation = reflector.evaluate(task, task_result, goal)
                task_result["evaluation"] = evaluation

                if evaluation.get("passed") or not evaluation.get("retry_needed"):
                    break

                if attempt < self.max_retries:
                    logger.warning(
                        f"   Task [{tid}] retry {attempt + 1}/{self.max_retries} — "
                        f"{evaluation.get('issues', [])}"
                    )
                    agent_memory.add_to_context(
                        role="reflector",
                        content=f"Task [{tid}] retry hint: {evaluation.get('suggestion', '')}",
                    )

            if not task_result.get("success") or not task_result.get("evaluation", {}).get("passed"):
                failed_ids.append(tid)

            all_results.append(task_result)

        # ── Phase 3: SYNTHESISE ────────────────────────────────────────────────
        logger.info("🔮 [Phase 3] Synthesis")
        final_output = reflector.synthesize_final(goal, plan, all_results)

        # ── Phase 4: MEMORY UPDATE ─────────────────────────────────────────────
        duration = time.time() - start
        success = len(failed_ids) < max(1, len(sub_tasks) / 2)

        agent_memory.remember(
            text=f"Goal: {goal}\nOutcome: {'success' if success else 'partial failure'}\nSummary: {final_output[:200]}",
            metadata={"success": success, "duration": duration},
        )
        ep_id = agent_memory.record_episode(goal, plan, all_results, final_output, success, duration)

        logger.info(f"✅ Done | {duration:.1f}s | episode={ep_id}")

        return {
            "goal": goal,
            "episode_id": ep_id,
            "plan": plan,
            "results": all_results,
            "final_output": final_output,
            "success": success,
            "failed_tasks": failed_ids,
            "duration_seconds": round(duration, 2),
            "stats": {
                "total_sub_tasks": len(sub_tasks),
                "completed": len(all_results),
                "failed": len(failed_ids),
            },
        }

    # ---------------------------------------------------------------- streaming

    def stream(self, goal: str) -> Generator[Dict[str, Any], None, None]:
        """Generator that yields progress events for SSE / WebSocket consumption."""
        yield {"event": "start", "goal": goal}

        agent_memory.clear_working()
        plan = planner.create_plan(goal)
        yield {"event": "plan_ready", "plan": plan}

        all_results: List[Dict] = []
        for task in plan.get("sub_tasks", []):
            yield {"event": "task_start", "task": task}
            context = agent_memory.get_context_summary()
            result = executor.execute_task(task, context=context, goal=goal)
            evaluation = reflector.evaluate(task, result, goal)
            result["evaluation"] = evaluation
            all_results.append(result)
            yield {"event": "task_complete", "task_id": task["id"], "result": result}

        final = reflector.synthesize_final(goal, plan, all_results)
        yield {"event": "final", "output": final}


agent = AgentCore()

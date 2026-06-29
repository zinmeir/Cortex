import os
import json
from datetime import datetime
from typing import List, Dict, Any
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger("memory.episodic_store")


class EpisodicStore:
    """
    JSON-backed task history (episodic memory).
    Records every agent run with goal, plan, results, and outcome.
    """

    def __init__(self):
        self.store_path = config.episodic_store_path
        os.makedirs(os.path.dirname(self.store_path) or ".", exist_ok=True)
        self.episodes: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path) as f:
                    self.episodes = json.load(f)
                logger.info(f"Loaded {len(self.episodes)} episodes")
            except Exception as exc:
                logger.warning(f"Could not load episodic store: {exc}")

    def _save(self) -> None:
        try:
            with open(self.store_path, "w") as f:
                json.dump(self.episodes, f, indent=2, default=str)
        except Exception as exc:
            logger.error(f"Failed to save episodic store: {exc}")

    def record_task(
        self,
        goal: str,
        plan: Dict[str, Any],
        results: List[Dict[str, Any]],
        final_output: str,
        success: bool,
        duration_seconds: float,
    ) -> str:
        ep_id = f"ep_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.episodes):04d}"
        episode = {
            "id": ep_id,
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "plan": plan,
            "results": results,
            "final_output": final_output,
            "success": success,
            "duration_seconds": duration_seconds,
            "sub_task_count": len(plan.get("sub_tasks", [])),
        }
        self.episodes.append(episode)
        self._save()
        logger.info(f"Recorded episode {ep_id} (success={success})")
        return ep_id

    def get_recent(self, n: int = 5) -> List[Dict[str, Any]]:
        return self.episodes[-n:]

    def get_successful(self, n: int = 10) -> List[Dict[str, Any]]:
        return [e for e in self.episodes if e.get("success")][-n:]

    def search_by_goal(self, query: str, n: int = 3) -> List[Dict[str, Any]]:
        q = query.lower()
        return [e for e in self.episodes if q in e.get("goal", "").lower()][-n:]

    def get_stats(self) -> Dict[str, Any]:
        if not self.episodes:
            return {"total": 0, "success_rate": 0.0, "avg_duration_seconds": 0.0}
        successes = sum(1 for e in self.episodes if e.get("success"))
        avg_dur = sum(e.get("duration_seconds", 0) for e in self.episodes) / len(self.episodes)
        return {
            "total": len(self.episodes),
            "successes": successes,
            "failures": len(self.episodes) - successes,
            "success_rate": round(successes / len(self.episodes), 3),
            "avg_duration_seconds": round(avg_dur, 2),
        }


episodic_store = EpisodicStore()

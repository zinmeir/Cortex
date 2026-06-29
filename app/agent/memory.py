from typing import Any, Dict, List
from app.memory.vector_store import vector_store
from app.memory.episodic_store import episodic_store
from app.utils.logger import get_logger

logger = get_logger("agent.memory")


class AgentMemory:
    """
    Unified memory interface.

    Short-term  → working_memory dict + task_context list (cleared per task)
    Long-term   → FAISS vector store (semantic recall across sessions)
    Episodic    → JSON task history (structured run records)
    """

    def __init__(self) -> None:
        self.working_memory: Dict[str, Any] = {}
        self.task_context: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------- Short-term

    def set(self, key: str, value: Any) -> None:
        self.working_memory[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.working_memory.get(key, default)

    def clear_working(self) -> None:
        self.working_memory = {}
        self.task_context = []

    def add_to_context(self, role: str, content: str, metadata: Dict | None = None) -> None:
        self.task_context.append({"role": role, "content": content, "metadata": metadata or {}})

    def get_context_summary(self, last_n: int = 5) -> str:
        recent = self.task_context[-last_n:]
        if not recent:
            return "No context yet."
        return "\n".join(f"[{item['role']}]: {item['content']}" for item in recent)

    # ---------------------------------------------------------------- Long-term

    def remember(self, text: str, metadata: Dict | None = None) -> int:
        doc_id = vector_store.add(text, metadata)
        logger.debug(f"Stored in long-term memory: {text[:60]}…")
        return doc_id

    def recall(self, query: str, k: int = 3) -> List[Dict]:
        return vector_store.search(query, k=k)

    def recall_as_context(self, query: str, k: int = 3) -> str:
        results = self.recall(query, k=k)
        if not results:
            return "No relevant past experience found."
        parts = [
            f"- [relevance {r['score']:.2f}] {r['text'][:200]}"
            for r in results
            if r.get("score", 0) > 0.25
        ]
        return "\n".join(parts) if parts else "No highly relevant past experience."

    # ---------------------------------------------------------------- Episodic

    def record_episode(
        self,
        goal: str,
        plan: Dict,
        results: List[Dict],
        final_output: str,
        success: bool,
        duration: float,
    ) -> str:
        return episodic_store.record_task(goal, plan, results, final_output, success, duration)

    def get_similar_past_tasks(self, goal: str) -> str:
        episodes = episodic_store.search_by_goal(goal)
        if not episodes:
            return "No similar past tasks found."
        lines = []
        for ep in episodes:
            icon = "✅" if ep.get("success") else "❌"
            lines.append(f"{icon} [{ep['timestamp'][:10]}] {ep['goal'][:80]}")
        return "\n".join(lines)

    def get_stats(self) -> Dict:
        return episodic_store.get_stats()


agent_memory = AgentMemory()

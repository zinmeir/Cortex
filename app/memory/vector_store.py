import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger("memory.vector_store")

EMBEDDING_DIM = 384  # default for all-MiniLM-L6-v2


class VectorStore:
    """
    Persistent FAISS-backed semantic memory.

    Fully lazy: imports sentence-transformers and faiss only on first use.
    Gracefully degrades to a no-op store when dependencies are unavailable
    or the embedding model cannot be downloaded (e.g., CI without network).
    """

    def __init__(self):
        self._model = None
        self._index = None
        self.documents: List[Dict[str, Any]] = []
        self.store_path = config.vector_store_path
        os.makedirs(self.store_path, exist_ok=True)
        self._ready = False          # True once model + index are loaded
        self._failed = False         # True if init already failed (skip retries)

    # ------------------------------------------------------------------ lazy setup

    def _ensure_ready(self) -> bool:
        """Return True if the store is operational; False to signal graceful skip."""
        if self._ready:
            return True
        if self._failed:
            return False

        try:
            from sentence_transformers import SentenceTransformer
            import faiss as _faiss

            logger.info(f"Loading embedding model '{config.embedding_model}'…")
            self._model = SentenceTransformer(config.embedding_model)
            dim = self._model.get_sentence_embedding_dimension()

            self._index = _faiss.IndexFlatL2(dim)
            self._load()
            self._ready = True
            logger.info(f"Vector store ready — {len(self.documents)} docs, dim={dim}")
            return True

        except Exception as exc:
            logger.warning(
                f"Vector store unavailable ({exc}). "
                "Semantic memory is disabled for this session."
            )
            self._failed = True
            return False

    # ------------------------------------------------------------------ persistence

    def _load(self) -> None:
        import faiss as _faiss
        index_path = os.path.join(self.store_path, "index.faiss")
        docs_path = os.path.join(self.store_path, "documents.json")
        if os.path.exists(index_path) and os.path.exists(docs_path):
            try:
                self._index = _faiss.read_index(index_path)
                with open(docs_path) as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded {len(self.documents)} vectors from store")
            except Exception as exc:
                logger.warning(f"Could not load vector store ({exc}). Starting fresh.")

    def _save(self) -> None:
        if not self._ready or not self._index:
            return
        import faiss as _faiss
        try:
            _faiss.write_index(self._index, os.path.join(self.store_path, "index.faiss"))
            with open(os.path.join(self.store_path, "documents.json"), "w") as f:
                json.dump(self.documents, f, indent=2)
        except Exception as exc:
            logger.error(f"Failed to save vector store: {exc}")

    # ------------------------------------------------------------------ public API

    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
        if not self._ensure_ready():
            return -1
        embedding = self._model.encode(
            [text], normalize_embeddings=True
        ).astype(np.float32)
        self._index.add(embedding)
        doc = {"id": len(self.documents), "text": text, "metadata": metadata or {}}
        self.documents.append(doc)
        self._save()
        return doc["id"]

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self._ensure_ready() or not self.documents:
            return []
        k = min(k, len(self.documents))
        q_emb = self._model.encode(
            [query], normalize_embeddings=True
        ).astype(np.float32)
        distances, indices = self._index.search(q_emb, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if 0 <= idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["score"] = float(max(0.0, 1.0 - dist / 2))
                results.append(doc)
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def clear(self) -> None:
        if not self._ensure_ready():
            return
        import faiss as _faiss
        dim = self._model.get_sentence_embedding_dimension()
        self._index = _faiss.IndexFlatL2(dim)
        self.documents = []
        self._save()

    def __len__(self) -> int:
        return len(self.documents)


vector_store = VectorStore()

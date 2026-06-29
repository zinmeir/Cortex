"""
Pytest configuration and shared fixtures.
Sets a dummy OPENAI_API_KEY so modules can be imported in test
environments without a real key (actual LLM calls are always mocked).
"""
import os
import pytest

# ── Set dummy credentials before any module is imported ──────────────────────
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder")


@pytest.fixture(autouse=True)
def _patch_vector_store(monkeypatch):
    """
    Prevent VectorStore from trying to download the embedding model
    during unit tests.  Tests that need real vectors should override this.
    """
    from app.memory import vector_store as vs_module

    monkeypatch.setattr(vs_module.vector_store, "_failed", True)
    monkeypatch.setattr(vs_module.vector_store, "_ready", False)
    yield


@pytest.fixture
def tmp_workspace(tmp_path):
    """Return a temporary path usable as an isolated workspace."""
    return tmp_path

import os
from dotenv import load_dotenv
from dataclasses import dataclass, field

load_dotenv()


@dataclass
class Config:
    # LLM
    llm_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    llm_base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    llm_temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    llm_max_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "4096")))

    # Memory
    vector_store_path: str = field(default_factory=lambda: os.getenv("VECTOR_STORE_PATH", "./data/vector_store"))
    episodic_store_path: str = field(default_factory=lambda: os.getenv("EPISODIC_STORE_PATH", "./data/episodic_store.json"))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

    # Agent
    max_iterations: int = field(default_factory=lambda: int(os.getenv("MAX_ITERATIONS", "10")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))

    # API Server
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))


config = Config()

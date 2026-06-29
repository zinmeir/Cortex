from typing import Optional, List, Dict, Any
from app.utils.config import config
from app.utils.logger import get_logger

logger = get_logger("llm.client")


class LLMClient:
    """
    Thin wrapper around OpenAI-compatible APIs.
    Swap LLM_BASE_URL in .env to use any compatible provider
    (OpenAI, Together, Groq, Ollama, Anthropic proxy, etc.)

    The underlying openai.OpenAI client is created lazily so that
    importing this module never raises even when OPENAI_API_KEY is unset.
    """

    def __init__(self):
        self._client = None  # lazy
        self.model = config.llm_model
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens

    @property
    def client(self):
        """Lazy-initialise the openai.OpenAI client on first use."""
        if self._client is None:
            from openai import OpenAI
            api_key = config.llm_api_key or "sk-not-configured"
            self._client = OpenAI(
                api_key=api_key,
                base_url=config.llm_base_url,
            )
        return self._client

    def complete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error(f"LLM call failed: {exc}")
            raise

    def complete_with_system(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        json_mode: bool = False,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self.complete(messages, temperature=temperature, json_mode=json_mode)


llm_client = LLMClient()

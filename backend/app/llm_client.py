"""Single AsyncOpenAI client shared across all agents."""
from openai import AsyncOpenAI
from .config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.mimo_api_key,
            base_url=settings.mimo_base_url,
            timeout=settings.request_timeout_seconds,
        )
    return _client

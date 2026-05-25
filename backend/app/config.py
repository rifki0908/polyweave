"""Configuration via env vars."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mimo_base_url: str = "https://token-plan-sgp.xiaomimimo.com/v1"
    mimo_api_key: str = ""
    mimo_model: str = "mimo-v2.5-pro"
    per_lang_max_tokens: int = 8192
    synthesis_max_tokens: int = 4096
    request_timeout_seconds: int = 240

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

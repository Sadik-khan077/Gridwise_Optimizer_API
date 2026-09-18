from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    LLM_API_KEY: str
    LLM_MODEL: str = "openai/gpt-oss-120b"
    LLM_PROVIDER: Literal["gemini", "openai"] = "openai"
    LLM_TIMEOUT_SECONDS: int = 30
    PORT: int = 8000
    LLM_CACHE_ENABLED: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

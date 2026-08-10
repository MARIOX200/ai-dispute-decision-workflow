from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    ai_provider: str = os.getenv("AI_PROVIDER", "local")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    database_path: str = os.getenv("DATABASE_PATH", "artifacts/workflow.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    min_retrieval_score: float = float(os.getenv("MIN_RETRIEVAL_SCORE", "0.12"))

settings = Settings()

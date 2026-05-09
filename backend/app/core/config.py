"""
Madhyastha — Application Configuration
Loads environment variables via pydantic-settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # ── App ─────────────────────────────────────────────────────────────────
    APP_NAME: str = "Madhyastha"
    APP_DESCRIPTION: str = "AI-Powered Dispute Resolution Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./nyayaai.db"

    # ── LLM ─────────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-70b-8192"

    # ── Auth ────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "madhyastha-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 72

    # ── Email — SMTP (Gmail) ────────────────────────────────────────────────
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "Madhyastha AI"

    # ── AI APIs ─────────────────────────────────────────────────────────────
    BHASHINI_USER_ID: str = ""
    BHASHINI_API_KEY: str = ""

    # ── ML Paths ────────────────────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "data/kanoon_faiss.index"
    FAISS_CHUNKS_PATH: str = "data/kanoon_chunks.json"
    RISK_MODEL_PATH: str = "ml/models/risk_scorer.pkl"
    NUDGE_THRESHOLD: int = 72

    # ── App URLs ────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

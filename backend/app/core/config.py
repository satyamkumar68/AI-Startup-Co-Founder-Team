from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_NAME: str = "AI Startup Co-Founder Team"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # LLM Settings
    LLM_PROVIDER: Literal["openrouter", "openai", "gemini", "anthropic", "ollama"] = "openrouter"
    OPENROUTER_API_KEY: str = ""
    LLM_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # Default model identifiers
    MODEL_DEFAULT: str = "openai/gpt-4o"
    MODEL_CRITIC: str = "google/gemini-2.0-flash"

    # Search Configuration
    SEARCH_PROVIDER: Literal["duckduckgo", "tavily", "serpapi"] = "duckduckgo"
    SEARCH_API_KEY: str = ""

    # Database & Redis
    DATABASE_URL: str = "sqlite+aiosqlite:///./cofounder.db"
    DATABASE_SYNC_URL: str = "sqlite:///./cofounder.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Auth
    JWT_SECRET: str = "dev-secret-change-in-production-12345"
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ])

    # Pipeline Thresholds & Constraints
    SCORE_THRESHOLD: float = 7.0
    DEBATE_MAX_ROUNDS: int = 2
    MAX_RETRIES_PER_AGENT: int = 2
    MAX_TOKENS_PER_RUN: int = 80000
    RATE_LIMIT_RUNS_PER_HOUR: int = 10

    # Exports & Storage
    EXPORTS_DIR: str = "./exports_storage"


settings = Settings()

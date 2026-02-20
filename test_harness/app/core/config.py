"""Mock config module for local testing"""


class Settings:
    """Mock settings object"""
    LLM_TIMEOUT = 120  # seconds
    DEFAULT_MODEL = "gpt-4o-mini"
    MARKETPLACE_URL = "http://localhost:8000"
    REDIS_URL = "redis://localhost:6379/0"
    SESSION_TTL = 3600
    LOG_LEVEL = "INFO"


settings = Settings()

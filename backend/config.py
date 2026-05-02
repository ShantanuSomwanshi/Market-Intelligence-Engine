from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseModel):
    firecrawl_api_key: str = os.getenv("FIRECRAWL_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    apollo_api_key: str = os.getenv("APOLLO_API_KEY", "")
    newsapi_key: str = os.getenv("NEWSAPI_KEY", "")
    use_mock_data: bool = os.getenv("USE_MOCK_DATA", "true").lower() == "true"
    max_validator_retries: int = int(os.getenv("MAX_VALIDATOR_RETRIES", "3"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "25"))

    @property
    def live_mode_available(self) -> bool:
        return bool(self.firecrawl_api_key or self.newsapi_key or self.groq_api_key or self.apollo_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

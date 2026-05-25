from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    NVIDIA_API_KEY: str
    REDIS_URL: str = 'redis://localhost:6379'
    GOOGLE_CSE_API_KEY: str = ''
    GOOGLE_CSE_ID: str = ''
    APP_ENV: str = 'development'
    DEMO_MODE: bool = True

    # Reddit — optional, raises rate limit from 10req/min to 60req/min
    REDDIT_CLIENT_ID: str = ''
    REDDIT_CLIENT_SECRET: str = ''

    # HuggingFace — optional, needed only if hitting download rate limits
    HUGGINGFACE_HUB_TOKEN: str = ''

    # Competitor panel — pre-configured brand UUIDs for demo (comma-separated)
    COMPETITOR_BRAND_IDS: str = ''

    class Config:
        env_file = '.env'

@lru_cache
def get_settings() -> Settings:
    return Settings()

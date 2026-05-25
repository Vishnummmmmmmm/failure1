from supabase import create_client, Client
from app.core.config import get_settings
from functools import lru_cache

@lru_cache
def get_db() -> Client:
    s = get_settings()
    return create_client(s.SUPABASE_URL, s.SUPABASE_SERVICE_KEY)

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

def supabase_config() -> tuple[str, str]:
    from fastapi import HTTPException
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVER_KEY") or os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise HTTPException(503, "Configuração do Supabase indisponível no backend.")
    return url, key

def cookie_secure() -> bool:
    return os.getenv("COOKIE_SECURE", "false").lower() == "true"

def trusted_origins() -> set[str]:
    return {origin.strip() for origin in os.getenv("TRUSTED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000").split(",")}

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    APP_NAME: str = "AI Outreach Automation System"
    VERSION: str = "1.0.0"
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Storage
    DB_PATH: str = str(BASE_DIR / "data" / "outreach.db")
    EXPORTS_DIR: str = str(BASE_DIR / "exports")
    
    # Email Sequence Days
    SEQUENCE_DAYS: dict = {
        "cold_email": 1,
        "followup_1": 3,
        "followup_2": 7,
    }
    
    # Limits
    MAX_LEADS_PER_UPLOAD: int = 500
    MAX_TOKENS_PER_EMAIL: int = 400

settings = Settings()

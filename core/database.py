import sqlite3
import json
from pathlib import Path
from core.config import settings

def get_connection():
    Path(settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            meta TEXT DEFAULT '{}'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT NOT NULL,
            industry TEXT NOT NULL,
            website TEXT,
            lead_score INTEGER DEFAULT 50,
            status TEXT DEFAULT 'pending',
            created_at TEXT NOT NULL,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_sequences (
            id TEXT PRIMARY KEY,
            lead_id TEXT NOT NULL,
            campaign_id TEXT NOT NULL,
            email_type TEXT NOT NULL,
            send_day INTEGER NOT NULL,
            subject TEXT,
            body TEXT,
            personalization_data TEXT DEFAULT '{}',
            status TEXT DEFAULT 'draft',
            created_at TEXT NOT NULL,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)

    conn.commit()
    conn.close()

"""
Lead Service
Handles lead import (CSV/JSON), storage, and retrieval.
"""

import csv
import json
import uuid
from datetime import datetime, timezone
from io import StringIO
from typing import List, Optional

from core.database import get_connection
from models.schemas import LeadInput


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    return str(uuid.uuid4())


def create_campaign(name: str) -> dict:
    """Create a new campaign and return it."""
    conn = get_connection()
    cursor = conn.cursor()
    
    campaign_id = _generate_id()
    now = _now()
    
    cursor.execute(
        "INSERT INTO campaigns (id, name, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (campaign_id, name, "pending", now, now)
    )
    conn.commit()
    conn.close()
    
    return {"id": campaign_id, "name": name, "status": "pending", "created_at": now, "updated_at": now}


def insert_lead(campaign_id: str, lead: LeadInput) -> dict:
    """Insert a single lead into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    lead_id = _generate_id()
    now = _now()
    
    cursor.execute(
        """INSERT INTO leads 
           (id, campaign_id, name, email, company, industry, website, lead_score, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (lead_id, campaign_id, lead.name, lead.email, lead.company,
         lead.industry, lead.website, lead.lead_score, "pending", now)
    )
    conn.commit()
    conn.close()
    
    return {
        "id": lead_id, "campaign_id": campaign_id,
        "name": lead.name, "email": lead.email,
        "company": lead.company, "industry": lead.industry,
        "website": lead.website, "lead_score": lead.lead_score,
        "status": "pending", "created_at": now
    }


def parse_csv(content: str) -> List[LeadInput]:
    """Parse CSV content into LeadInput objects."""
    reader = csv.DictReader(StringIO(content))
    leads = []
    
    required = {"name", "email", "company", "industry"}
    headers = {h.strip().lower() for h in (reader.fieldnames or [])}
    
    missing = required - headers
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")
    
    for row in reader:
        row = {k.strip().lower(): v.strip() for k, v in row.items()}
        leads.append(LeadInput(
            name=row["name"],
            email=row["email"],
            company=row["company"],
            industry=row["industry"],
            website=row.get("website") or None,
            lead_score=int(row.get("lead_score", 50))
        ))
    
    return leads


def parse_json_leads(data: list) -> List[LeadInput]:
    """Parse a list of dicts into LeadInput objects."""
    return [LeadInput(**item) for item in data]


def get_campaign(campaign_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_campaigns() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaigns ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_leads_by_campaign(campaign_id: str) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE campaign_id = ? ORDER BY created_at", (campaign_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_lead(lead_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_lead_status(lead_id: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id))
    conn.commit()
    conn.close()


def update_campaign_status(campaign_id: str, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    now = _now()
    cursor.execute(
        "UPDATE campaigns SET status = ?, updated_at = ? WHERE id = ?",
        (status, now, campaign_id)
    )
    conn.commit()
    conn.close()

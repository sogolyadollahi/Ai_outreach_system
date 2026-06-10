"""
Campaign Service
Orchestrates AI generation across all leads in a campaign.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from core.database import get_connection
from services.lead_service import (
    get_leads_by_campaign, update_lead_status, update_campaign_status
)
from ai.email_generator import generate_full_outreach


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_id() -> str:
    return str(uuid.uuid4())


def save_email_sequence(lead_id: str, campaign_id: str, email: dict, personalization: dict):
    """Save a single generated email to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    email_id = _generate_id()
    now = _now()
    
    cursor.execute(
        """INSERT INTO email_sequences
           (id, lead_id, campaign_id, email_type, send_day, subject, body, personalization_data, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            email_id, lead_id, campaign_id,
            email["email_type"], email["send_day"],
            email["subject"], email["body"],
            json.dumps(personalization),
            "draft", now
        )
    )
    conn.commit()
    conn.close()
    return email_id


def generate_campaign_emails(campaign_id: str) -> dict:
    """
    Main orchestration: iterate over all pending leads and generate email sequences.
    Returns a summary report.
    """
    update_campaign_status(campaign_id, "generating")
    
    leads = get_leads_by_campaign(campaign_id)
    pending_leads = [l for l in leads if l["status"] in ("pending", "failed")]
    
    results = {
        "campaign_id": campaign_id,
        "total": len(pending_leads),
        "success": 0,
        "failed": 0,
        "errors": []
    }
    
    for lead in pending_leads:
        try:
            update_lead_status(lead["id"], "processing")
            
            lead_dict = {
                "name": lead["name"],
                "email": lead["email"],
                "company": lead["company"],
                "industry": lead["industry"],
                "website": lead.get("website"),
                "lead_score": lead.get("lead_score", 50),
            }
            
            output = generate_full_outreach(lead_dict)
            personalization = output["personalization"]
            
            for email in output["emails"]:
                save_email_sequence(lead["id"], campaign_id, email, personalization)
            
            update_lead_status(lead["id"], "completed")
            results["success"] += 1
            
        except Exception as e:
            update_lead_status(lead["id"], "failed")
            results["failed"] += 1
            results["errors"].append({"lead_id": lead["id"], "name": lead["name"], "error": str(e)})
    
    final_status = "completed" if results["failed"] == 0 else "completed"
    update_campaign_status(campaign_id, final_status)
    
    return results


def get_emails_for_lead(lead_id: str) -> List[dict]:
    """Return all generated emails for a specific lead."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM email_sequences WHERE lead_id = ? ORDER BY send_day",
        (lead_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        item = dict(row)
        item["personalization_data"] = json.loads(item.get("personalization_data", "{}"))
        result.append(item)
    return result


def get_all_emails_for_campaign(campaign_id: str) -> List[dict]:
    """Return all emails across all leads in a campaign."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT es.*, l.name as lead_name, l.email as lead_email, 
                  l.company as lead_company, l.industry as lead_industry
           FROM email_sequences es
           JOIN leads l ON es.lead_id = l.id
           WHERE es.campaign_id = ?
           ORDER BY l.name, es.send_day""",
        (campaign_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        item = dict(row)
        item["personalization_data"] = json.loads(item.get("personalization_data", "{}"))
        result.append(item)
    return result


def get_campaign_stats(campaign_id: str) -> dict:
    """Return campaign statistics."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    campaign = cursor.fetchone()
    
    if not campaign:
        conn.close()
        return {}
    
    cursor.execute(
        "SELECT status, COUNT(*) as cnt FROM leads WHERE campaign_id = ? GROUP BY status",
        (campaign_id,)
    )
    lead_counts = {row["status"]: row["cnt"] for row in cursor.fetchall()}
    
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM email_sequences WHERE campaign_id = ?",
        (campaign_id,)
    )
    email_count = cursor.fetchone()["cnt"]
    
    conn.close()
    
    total = sum(lead_counts.values())
    return {
        **dict(campaign),
        "total_leads": total,
        "completed_leads": lead_counts.get("completed", 0),
        "failed_leads": lead_counts.get("failed", 0),
        "pending_leads": lead_counts.get("pending", 0),
        "emails_generated": email_count,
    }

"""
Export Utilities
Handles CSV, JSON, and plain text exports of campaign data.
"""

import csv
import json
import os
from io import StringIO
from datetime import datetime, timezone
from pathlib import Path

from core.config import settings


def export_to_csv(emails: list, campaign_name: str = "campaign") -> str:
    """Export email sequences to CSV string."""
    output = StringIO()
    
    fieldnames = [
        "lead_name", "lead_email", "lead_company", "lead_industry",
        "email_type", "send_day", "subject", "body",
        "pain_point_guess", "improvement_area", "hook"
    ]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    
    for email in emails:
        pd = email.get("personalization_data", {})
        writer.writerow({
            "lead_name": email.get("lead_name", ""),
            "lead_email": email.get("lead_email", ""),
            "lead_company": email.get("lead_company", ""),
            "lead_industry": email.get("lead_industry", ""),
            "email_type": email.get("email_type", ""),
            "send_day": email.get("send_day", ""),
            "subject": email.get("subject", ""),
            "body": email.get("body", ""),
            "pain_point_guess": pd.get("pain_point_guess", ""),
            "improvement_area": pd.get("improvement_area", ""),
            "hook": pd.get("hook", ""),
        })
    
    return output.getvalue()


def export_to_json(emails: list) -> str:
    """Export email sequences to JSON string."""
    return json.dumps(emails, indent=2, ensure_ascii=False)


def export_to_text(emails: list) -> str:
    """Export email sequences to plain text (Gmail copy-paste friendly)."""
    lines = []
    
    # Group by lead
    by_lead = {}
    for email in emails:
        key = email.get("lead_email", "unknown")
        if key not in by_lead:
            by_lead[key] = {
                "name": email.get("lead_name", ""),
                "email": key,
                "company": email.get("lead_company", ""),
                "emails": []
            }
        by_lead[key]["emails"].append(email)
    
    for lead_email, data in by_lead.items():
        lines.append("=" * 60)
        lines.append(f"LEAD: {data['name']} | {data['email']} | {data['company']}")
        lines.append("=" * 60)
        
        for email in sorted(data["emails"], key=lambda x: x.get("send_day", 0)):
            etype = email.get("email_type", "").replace("_", " ").upper()
            day = email.get("send_day", "?")
            lines.append(f"\n[{etype} — Send Day {day}]")
            lines.append(f"Subject: {email.get('subject', '')}")
            lines.append("-" * 40)
            lines.append(email.get("body", ""))
            lines.append("")
        
        lines.append("")
    
    return "\n".join(lines)


def save_export_file(content: str, filename: str) -> str:
    """Save export content to disk and return path."""
    Path(settings.EXPORTS_DIR).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(settings.EXPORTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath

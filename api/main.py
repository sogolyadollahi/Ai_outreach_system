"""
AI Outreach Automation System — FastAPI Backend
"""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from core.config import settings
from core.database import init_db
from models.schemas import LeadInput, CampaignCreateInput
from services.lead_service import (
    create_campaign, insert_lead, parse_csv, parse_json_leads,
    get_campaign, get_all_campaigns, get_leads_by_campaign, get_lead
)
from services.campaign_service import (
    generate_campaign_emails, get_emails_for_lead,
    get_all_emails_for_campaign, get_campaign_stats
)
from utils.export import export_to_csv, export_to_json, export_to_text

# Initialize DB on startup
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Automated personalized cold outreach system for agencies and freelancers."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}


# ─── Lead Upload ──────────────────────────────────────────

@app.post("/upload-leads")
async def upload_leads(
    campaign_name: str = Form(...),
    file: Optional[UploadFile] = File(None),
    leads_json: Optional[str] = Form(None)
):
    """
    Upload leads via CSV file or JSON payload.
    Creates a new campaign and stores all leads.
    """
    if not file and not leads_json:
        raise HTTPException(400, "Provide either a CSV file or leads_json")
    
    try:
        if file:
            content = await file.read()
            leads = parse_csv(content.decode("utf-8"))
        else:
            data = json.loads(leads_json)
            leads = parse_json_leads(data)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(400, f"Failed to parse leads: {e}")
    
    if len(leads) > settings.MAX_LEADS_PER_UPLOAD:
        raise HTTPException(413, f"Max {settings.MAX_LEADS_PER_UPLOAD} leads per upload")
    
    campaign = create_campaign(campaign_name)
    inserted = []
    
    for lead in leads:
        record = insert_lead(campaign["id"], lead)
        inserted.append(record)
    
    return {
        "campaign_id": campaign["id"],
        "campaign_name": campaign_name,
        "leads_imported": len(inserted),
        "message": f"Successfully imported {len(inserted)} leads. Run POST /generate-campaign to start."
    }


# ─── Campaign Management ──────────────────────────────────

@app.post("/campaigns")
def create_campaign_with_leads(payload: CampaignCreateInput):
    """Create campaign with inline JSON leads."""
    campaign = create_campaign(payload.name)
    inserted = []
    for lead in payload.leads:
        record = insert_lead(campaign["id"], lead)
        inserted.append(record)
    
    return {
        "campaign_id": campaign["id"],
        "campaign_name": campaign["name"],
        "leads_imported": len(inserted),
    }


@app.post("/generate-campaign")
def generate_campaign(campaign_id: str, background_tasks: BackgroundTasks):
    """
    Trigger AI email generation for all pending leads in a campaign.
    Runs synchronously and returns results.
    """
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(404, f"Campaign {campaign_id} not found")
    
    results = generate_campaign_emails(campaign_id)
    return results


@app.get("/campaigns")
def list_campaigns():
    """List all campaigns."""
    campaigns = get_all_campaigns()
    enriched = []
    for c in campaigns:
        stats = get_campaign_stats(c["id"])
        enriched.append(stats)
    return {"campaigns": enriched, "total": len(enriched)}


@app.get("/campaign/{campaign_id}")
def get_campaign_detail(campaign_id: str):
    """Return full campaign details with stats."""
    stats = get_campaign_stats(campaign_id)
    if not stats:
        raise HTTPException(404, "Campaign not found")
    return stats


@app.get("/campaign/{campaign_id}/leads")
def get_campaign_leads(campaign_id: str):
    """List all leads in a campaign."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    leads = get_leads_by_campaign(campaign_id)
    return {"campaign_id": campaign_id, "leads": leads, "total": len(leads)}


@app.get("/campaign/{campaign_id}/emails")
def get_campaign_emails(campaign_id: str):
    """Return all generated emails for a campaign."""
    emails = get_all_emails_for_campaign(campaign_id)
    return {"campaign_id": campaign_id, "emails": emails, "total": len(emails)}


# ─── Lead Endpoints ───────────────────────────────────────

@app.get("/lead/{lead_id}")
def get_lead_detail(lead_id: str):
    """Get a single lead by ID."""
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


@app.get("/lead/{lead_id}/emails")
def get_lead_emails(lead_id: str):
    """Return generated email sequence for a specific lead."""
    lead = get_lead(lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    emails = get_emails_for_lead(lead_id)
    return {
        "lead_id": lead_id,
        "lead": lead,
        "emails": emails,
        "total": len(emails)
    }


# ─── Export Endpoints ─────────────────────────────────────

@app.get("/campaign/{campaign_id}/export/csv")
def export_campaign_csv(campaign_id: str):
    """Export full email sequences as CSV."""
    emails = get_all_emails_for_campaign(campaign_id)
    if not emails:
        raise HTTPException(404, "No emails found for this campaign")
    
    csv_content = export_to_csv(emails)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=campaign_{campaign_id[:8]}.csv"}
    )


@app.get("/campaign/{campaign_id}/export/json")
def export_campaign_json(campaign_id: str):
    """Export full email sequences as JSON."""
    emails = get_all_emails_for_campaign(campaign_id)
    if not emails:
        raise HTTPException(404, "No emails found for this campaign")
    return {"campaign_id": campaign_id, "data": emails}


@app.get("/campaign/{campaign_id}/export/text")
def export_campaign_text(campaign_id: str):
    """Export emails as plain text for Gmail copy-paste."""
    emails = get_all_emails_for_campaign(campaign_id)
    if not emails:
        raise HTTPException(404, "No emails found for this campaign")
    
    text_content = export_to_text(emails)
    return StreamingResponse(
        iter([text_content]),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=campaign_{campaign_id[:8]}.txt"}
    )

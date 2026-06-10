from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from enum import Enum

class LeadStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class EmailType(str, Enum):
    cold_email = "cold_email"
    followup_1 = "followup_1"
    followup_2 = "followup_2"

class CampaignStatus(str, Enum):
    pending = "pending"
    generating = "generating"
    completed = "completed"
    failed = "failed"


# --- Input Models ---

class LeadInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    company: str = Field(..., min_length=1, max_length=200)
    industry: str = Field(..., min_length=1, max_length=100)
    website: Optional[str] = None
    lead_score: int = Field(default=50, ge=0, le=100)

class CampaignCreateInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    leads: List[LeadInput]

class GenerateCampaignInput(BaseModel):
    campaign_id: str


# --- Response Models ---

class LeadResponse(BaseModel):
    id: str
    campaign_id: str
    name: str
    email: str
    company: str
    industry: str
    website: Optional[str]
    lead_score: int
    status: str
    created_at: str

class EmailSequenceResponse(BaseModel):
    id: str
    lead_id: str
    campaign_id: str
    email_type: str
    send_day: int
    subject: Optional[str]
    body: Optional[str]
    personalization_data: dict
    status: str
    created_at: str

class CampaignResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
    updated_at: str
    total_leads: int = 0
    completed_leads: int = 0
    emails_generated: int = 0

class PersonalizationData(BaseModel):
    first_name: str
    company_name: str
    industry: str
    pain_point_guess: str
    improvement_area: str
    hook: str

class GeneratedEmail(BaseModel):
    email_type: str
    send_day: int
    subject: str
    body: str
    personalization: PersonalizationData

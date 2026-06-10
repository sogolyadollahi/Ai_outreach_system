"""
AI Email Generator Module
Handles all OpenAI interactions for generating personalized outreach sequences.
"""

import json
import re
from typing import Optional
from openai import OpenAI
from core.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


SYSTEM_PROMPT = """You are an expert B2B sales copywriter specializing in cold outreach for agencies and freelancers.

Your emails are:
- Conversational, not corporate
- Short (under 100 words for cold, under 80 for follow-ups)
- Specific to the prospect's industry and likely pain points
- Never pushy or spammy
- Always end with a low-friction CTA (a question or soft ask)

You will return ONLY valid JSON. No markdown, no explanation. No code fences."""


def _build_personalization_prompt(lead: dict) -> str:
    website_info = f"Website: {lead.get('website', 'not provided')}" if lead.get("website") else "No website provided"
    return f"""
Analyze this lead and infer personalization details:

Lead:
- Name: {lead['name']}
- Company: {lead['company']}
- Industry: {lead['industry']}
- {website_info}
- Lead Score: {lead.get('lead_score', 50)}/100

Return ONLY this JSON structure (no extra text):
{{
  "first_name": "<first name only>",
  "company_name": "<company name>",
  "industry": "<industry>",
  "pain_point_guess": "<1 specific pain point companies in this industry typically face>",
  "improvement_area": "<one of: automation, lead generation, time saving, cost reduction, scaling>",
  "hook": "<a 1-sentence industry-specific hook that will resonate>"
}}
"""


def _build_sequence_prompt(lead: dict, personalization: dict) -> str:
    return f"""
Generate a 3-email cold outreach sequence for this lead.

Lead Details:
- Name: {lead['name']} (First name: {personalization['first_name']})
- Company: {lead['company']}
- Industry: {lead['industry']}
- Pain Point: {personalization['pain_point_guess']}
- Improvement Area: {personalization['improvement_area']}
- Hook: {personalization['hook']}

Rules:
- Cold email (Day 1): Under 100 words. Introduce yourself briefly, reference their industry pain point, soft CTA.
- Follow-up 1 (Day 3): Under 80 words. Reference the previous email, add a relevant insight or question.
- Follow-up 2 (Day 7): Under 70 words. Final nudge. Acknowledge they're busy, leave the door open.
- Never use "I hope this email finds you well" or generic openers.
- Be direct, warm, and professional.

Return ONLY this JSON (no extra text, no markdown):
{{
  "cold_email": {{
    "subject": "<compelling subject line, no clickbait>",
    "body": "<email body with line breaks as \\n>"
  }},
  "followup_1": {{
    "subject": "<Re: or new subject>",
    "body": "<email body>"
  }},
  "followup_2": {{
    "subject": "<subject>",
    "body": "<email body>"
  }}
}}
"""


def generate_personalization(lead: dict) -> dict:
    """Infer personalization variables from lead data."""
    prompt = _build_personalization_prompt(lead)
    
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0.7,
    )
    
    raw = response.choices[0].message.content.strip()
    # Strip any accidental markdown fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    return json.loads(raw)


def generate_email_sequence(lead: dict, personalization: dict) -> dict:
    """Generate the full 3-email sequence for a lead."""
    prompt = _build_sequence_prompt(lead, personalization)
    
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.75,
    )
    
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    return json.loads(raw)


def generate_full_outreach(lead: dict) -> dict:
    """
    Main entry point: Generate personalization + email sequence for a single lead.
    Returns structured dict with personalization and all 3 emails.
    """
    personalization = generate_personalization(lead)
    sequence = generate_email_sequence(lead, personalization)
    
    send_days = settings.SEQUENCE_DAYS
    
    return {
        "personalization": personalization,
        "emails": [
            {
                "email_type": "cold_email",
                "send_day": send_days["cold_email"],
                "subject": sequence["cold_email"]["subject"],
                "body": sequence["cold_email"]["body"],
            },
            {
                "email_type": "followup_1",
                "send_day": send_days["followup_1"],
                "subject": sequence["followup_1"]["subject"],
                "body": sequence["followup_1"]["body"],
            },
            {
                "email_type": "followup_2",
                "send_day": send_days["followup_2"],
                "subject": sequence["followup_2"]["subject"],
                "body": sequence["followup_2"]["body"],
            },
        ],
    }

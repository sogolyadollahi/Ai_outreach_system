"""
AI Outreach Automation System — Streamlit UI
"""

import streamlit as st
import json
import sys
import os
import io
import csv
from pathlib import Path

# ── Path setup ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.config import settings
from core.database import init_db
from models.schemas import LeadInput
from services.lead_service import (
    create_campaign, insert_lead, parse_csv, parse_json_leads,
    get_all_campaigns, get_leads_by_campaign, get_lead,
    get_campaign,
)
from services.campaign_service import (
    generate_campaign_emails, get_emails_for_lead,
    get_all_emails_for_campaign, get_campaign_stats,
)
from utils.export import export_to_csv, export_to_json, export_to_text

init_db()

# ── Page config ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Outreach System",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Fonts & base */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* Dark sidebar */
  [data-testid="stSidebar"] {
    background: #0f1117;
    border-right: 1px solid #1e2230;
  }
  [data-testid="stSidebar"] * { color: #c9d1e0 !important; }
  [data-testid="stSidebar"] .stRadio label { 
    padding: 8px 12px; 
    border-radius: 6px; 
    display: block;
    transition: background 0.15s;
  }
  [data-testid="stSidebar"] .stRadio label:hover { background: #1a1f2e; }

  /* Main area */
  .main .block-container { padding-top: 2rem; max-width: 1100px; }

  /* Metric cards */
  .metric-card {
    background: #1a1f2e;
    border: 1px solid #2a3048;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
  }
  .metric-card .value { font-size: 2rem; font-weight: 700; color: #6c8fff; }
  .metric-card .label { font-size: 0.8rem; color: #8892a4; text-transform: uppercase; letter-spacing: 0.06em; margin-top: 4px; }

  /* Status badges */
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.03em;
  }
  .badge-completed { background: #0d2e1a; color: #3fcf8e; border: 1px solid #1a5c3a; }
  .badge-pending   { background: #2a2510; color: #f5c842; border: 1px solid #5a4e1a; }
  .badge-generating{ background: #0d1f3a; color: #6c8fff; border: 1px solid #2a4080; }
  .badge-failed    { background: #2e0d0d; color: #ff6b6b; border: 1px solid #5c1a1a; }

  /* Email card */
  .email-card {
    background: #12161f;
    border: 1px solid #2a3048;
    border-left: 3px solid #6c8fff;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 16px;
  }
  .email-card.followup { border-left-color: #a78bfa; }
  .email-card.followup2 { border-left-color: #34d399; }
  .email-type-tag {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6c8fff;
    margin-bottom: 8px;
  }
  .email-subject {
    font-size: 1rem;
    font-weight: 600;
    color: #e2e8f0;
    margin-bottom: 12px;
  }
  .email-body {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #94a3b8;
    line-height: 1.7;
    white-space: pre-wrap;
    background: #0d1117;
    border-radius: 6px;
    padding: 12px 16px;
  }
  .send-day-badge {
    float: right;
    background: #1e2230;
    color: #64748b;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 500;
  }

  /* Section headers */
  .section-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 0.25rem;
  }
  .section-sub {
    font-size: 0.88rem;
    color: #64748b;
    margin-bottom: 1.5rem;
  }

  /* Lead row */
  .lead-row {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #12161f;
    border: 1px solid #2a3048;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
  }

  /* Buttons */
  .stButton > button {
    background: #6c8fff;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    font-size: 0.9rem;
    transition: background 0.15s;
  }
  .stButton > button:hover { background: #5a75e8; }

  /* Page header */
  .page-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #1e2230;
  }

  /* Pill tag */
  .pill {
    background: #1a1f2e;
    border: 1px solid #2a3048;
    color: #94a3b8;
    padding: 3px 10px;
    border-radius: 16px;
    font-size: 0.78rem;
    display: inline-block;
    margin: 2px;
  }
  .pill.score-high { border-color: #1a5c3a; color: #3fcf8e; background: #0d2e1a; }
  .pill.score-mid  { border-color: #5a4e1a; color: #f5c842; background: #2a2510; }
  .pill.score-low  { border-color: #5c1a1a; color: #ff6b6b; background: #2e0d0d; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ─────────────────────────────────────────────────────────────

def badge(status: str) -> str:
    cls = f"badge-{status.lower()}"
    return f'<span class="badge {cls}">{status.upper()}</span>'


def score_pill(score: int) -> str:
    cls = "score-high" if score >= 70 else ("score-mid" if score >= 40 else "score-low")
    return f'<span class="pill {cls}">Score: {score}</span>'


def check_api_key() -> bool:
    key = settings.OPENAI_API_KEY or st.session_state.get("api_key", "")
    return bool(key and key.startswith("sk-"))


# ── Sidebar ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ✉️ AI Outreach")
    st.markdown('<p style="font-size:0.8rem; color:#64748b; margin-top:-10px;">Automation System</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.radio(
        "Navigate",
        ["🏠  Dashboard", "📥  Import Leads", "⚡  Generate Campaign", "📋  View Campaigns", "🔍  Lead Inspector", "📤  Export"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("**⚙️ Settings**")
    
    api_key_input = st.text_input(
        "OpenAI API Key",
        value=st.session_state.get("api_key", settings.OPENAI_API_KEY),
        type="password",
        placeholder="sk-...",
    )
    if api_key_input:
        st.session_state["api_key"] = api_key_input
        os.environ["OPENAI_API_KEY"] = api_key_input
        settings.OPENAI_API_KEY = api_key_input
    
    model = st.selectbox(
        "Model",
        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
        index=0
    )
    settings.OPENAI_MODEL = model
    
    if check_api_key():
        st.success("✓ API key set", icon="🔑")
    else:
        st.warning("Add your OpenAI key to generate emails", icon="⚠️")
    
    st.markdown("---")
    st.markdown('<p style="font-size:0.72rem; color:#3a4055;">v1.0.0 · Production MVP</p>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ═══════════════════════════════════════════════════════════════════════

if page == "🏠  Dashboard":
    st.markdown('<div class="section-title">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Your outreach automation at a glance</div>', unsafe_allow_html=True)
    
    campaigns = get_all_campaigns()
    
    total_campaigns = len(campaigns)
    total_leads = sum(get_campaign_stats(c["id"]).get("total_leads", 0) for c in campaigns)
    total_emails = sum(get_campaign_stats(c["id"]).get("emails_generated", 0) for c in campaigns)
    completed = sum(1 for c in campaigns if c["status"] == "completed")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="value">{total_campaigns}</div><div class="label">Campaigns</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="value">{total_leads}</div><div class="label">Total Leads</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="value">{total_emails}</div><div class="label">Emails Generated</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="value">{completed}</div><div class="label">Completed</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if campaigns:
        st.markdown("**Recent Campaigns**")
        for c in campaigns[:5]:
            stats = get_campaign_stats(c["id"])
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"**{c['name']}**")
            with col2:
                st.markdown(badge(c["status"]), unsafe_allow_html=True)
            with col3:
                st.markdown(f"👥 {stats.get('total_leads', 0)} leads")
            with col4:
                st.markdown(f"✉️ {stats.get('emails_generated', 0)} emails")
            st.markdown("---")
    else:
        st.info("No campaigns yet. Go to **Import Leads** to get started.", icon="📌")


# ═══════════════════════════════════════════════════════════════════════
# PAGE: IMPORT LEADS
# ═══════════════════════════════════════════════════════════════════════

elif page == "📥  Import Leads":
    st.markdown('<div class="section-title">Import Leads</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Upload a CSV or paste JSON to create a new campaign</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📂 CSV Upload", "📋 JSON Paste", "✏️ Manual Entry"])
    
    with tab1:
        campaign_name_csv = st.text_input("Campaign Name", placeholder="e.g. Q3 SaaS Outreach", key="csv_camp")
        
        st.markdown("""
        **Required CSV columns:** `name`, `email`, `company`, `industry`  
        **Optional:** `website`, `lead_score` (0–100)
        """)
        
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        
        # Sample CSV download
        sample_csv = """name,email,company,industry,website,lead_score
Alice Johnson,alice@acmecorp.com,Acme Corp,SaaS,https://acmecorp.com,82
Bob Smith,bob@retailco.com,RetailCo,E-commerce,https://retailco.com,65
Carlos Mendez,carlos@lawfirm.io,LawFirm LLC,Legal Services,,45
Diana Lee,diana@healthplus.com,HealthPlus,Healthcare,https://healthplus.com,91
"""
        st.download_button("⬇️ Download Sample CSV", sample_csv, "sample_leads.csv", "text/csv")
        
        if uploaded and campaign_name_csv:
            if st.button("Import CSV Leads", key="btn_csv"):
                with st.spinner("Parsing CSV..."):
                    try:
                        content = uploaded.read().decode("utf-8")
                        leads = parse_csv(content)
                        campaign = create_campaign(campaign_name_csv)
                        for lead in leads:
                            insert_lead(campaign["id"], lead)
                        st.success(f"✅ Campaign **{campaign_name_csv}** created with {len(leads)} leads!")
                        st.markdown(f"Campaign ID: `{campaign['id']}`")
                        st.session_state["last_campaign_id"] = campaign["id"]
                    except Exception as e:
                        st.error(f"Import failed: {e}")
    
    with tab2:
        campaign_name_json = st.text_input("Campaign Name", placeholder="e.g. Agency Outreach Wave 1", key="json_camp")
        
        sample_json = json.dumps([
            {"name": "Alice Johnson", "email": "alice@acmecorp.com", "company": "Acme Corp", "industry": "SaaS", "website": "https://acmecorp.com", "lead_score": 82},
            {"name": "Bob Smith", "email": "bob@retailco.com", "company": "RetailCo", "industry": "E-commerce", "lead_score": 65}
        ], indent=2)
        
        json_input = st.text_area("Paste JSON array of leads", value=sample_json, height=250)
        
        if campaign_name_json and json_input:
            if st.button("Import JSON Leads", key="btn_json"):
                with st.spinner("Parsing JSON..."):
                    try:
                        data = json.loads(json_input)
                        leads = parse_json_leads(data)
                        campaign = create_campaign(campaign_name_json)
                        for lead in leads:
                            insert_lead(campaign["id"], lead)
                        st.success(f"✅ Campaign **{campaign_name_json}** created with {len(leads)} leads!")
                        st.session_state["last_campaign_id"] = campaign["id"]
                    except Exception as e:
                        st.error(f"Import failed: {e}")
    
    with tab3:
        campaign_name_manual = st.text_input("Campaign Name", placeholder="e.g. Manual Outreach Test", key="manual_camp")
        
        if "manual_leads" not in st.session_state:
            st.session_state["manual_leads"] = []
        
        st.markdown("**Add Lead**")
        mc1, mc2 = st.columns(2)
        with mc1:
            m_name = st.text_input("Full Name", key="m_name")
            m_email = st.text_input("Email", key="m_email")
            m_company = st.text_input("Company", key="m_company")
        with mc2:
            m_industry = st.text_input("Industry", key="m_industry")
            m_website = st.text_input("Website (optional)", key="m_website")
            m_score = st.slider("Lead Score", 0, 100, 60, key="m_score")
        
        if st.button("➕ Add to List"):
            if m_name and m_email and m_company and m_industry:
                st.session_state["manual_leads"].append({
                    "name": m_name, "email": m_email,
                    "company": m_company, "industry": m_industry,
                    "website": m_website or None, "lead_score": m_score
                })
                st.success(f"Added {m_name}")
            else:
                st.warning("Fill all required fields")
        
        if st.session_state["manual_leads"]:
            st.markdown(f"**{len(st.session_state['manual_leads'])} leads queued:**")
            for l in st.session_state["manual_leads"]:
                st.markdown(f"- {l['name']} · {l['company']} · {l['industry']}")
            
            if campaign_name_manual and st.button("💾 Save Campaign"):
                try:
                    leads = parse_json_leads(st.session_state["manual_leads"])
                    campaign = create_campaign(campaign_name_manual)
                    for lead in leads:
                        insert_lead(campaign["id"], lead)
                    st.success(f"✅ Campaign created with {len(leads)} leads!")
                    st.session_state["manual_leads"] = []
                    st.session_state["last_campaign_id"] = campaign["id"]
                except Exception as e:
                    st.error(str(e))


# ═══════════════════════════════════════════════════════════════════════
# PAGE: GENERATE CAMPAIGN
# ═══════════════════════════════════════════════════════════════════════

elif page == "⚡  Generate Campaign":
    st.markdown('<div class="section-title">Generate Campaign</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Run AI to generate personalized email sequences for all leads</div>', unsafe_allow_html=True)
    
    if not check_api_key():
        st.error("⚠️ Add your OpenAI API key in the sidebar first.", icon="🔑")
        st.stop()
    
    campaigns = get_all_campaigns()
    pending = [c for c in campaigns if c["status"] in ("pending", "failed")]
    
    if not pending:
        if campaigns:
            st.info("All campaigns have been processed. Import new leads to generate more.")
        else:
            st.info("No campaigns found. Import leads first.")
        st.stop()
    
    options = {f"{c['name']} ({c['id'][:8]}...)": c["id"] for c in pending}
    selected_label = st.selectbox("Select Campaign to Generate", list(options.keys()))
    selected_id = options[selected_label]
    
    stats = get_campaign_stats(selected_id)
    leads = get_leads_by_campaign(selected_id)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Leads", stats.get("total_leads", 0))
    col2.metric("Pending", stats.get("pending_leads", 0))
    col3.metric("Already Generated", stats.get("completed_leads", 0))
    
    st.markdown("**Leads preview:**")
    for lead in leads[:5]:
        st.markdown(f"""
        <div class="lead-row">
          <span style="color:#e2e8f0; font-weight:600;">{lead['name']}</span>
          <span class="pill">{lead['company']}</span>
          <span class="pill">{lead['industry']}</span>
          {score_pill(lead.get('lead_score', 50))}
          {badge(lead['status'])}
        </div>
        """, unsafe_allow_html=True)
    if len(leads) > 5:
        st.caption(f"... and {len(leads) - 5} more leads")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.info("""
    **What happens next:**
    1. For each lead, AI infers pain points and a personalized hook
    2. AI writes a cold email, follow-up 1 (Day 3), and follow-up 2 (Day 7)
    3. Results are saved and ready to export
    
    ⏱️ Estimated time: ~15-30 seconds per lead (API dependent)
    """)
    
    if st.button("⚡ Generate All Email Sequences", type="primary"):
        pending_leads = [l for l in leads if l["status"] in ("pending", "failed")]
        
        progress = st.progress(0)
        status_text = st.empty()
        results_placeholder = st.empty()
        
        # We call the service which iterates internally, but show progress with a spinner
        with st.spinner(f"Generating emails for {len(pending_leads)} leads..."):
            results = generate_campaign_emails(selected_id)
        
        progress.progress(100)
        
        if results["success"] > 0:
            st.success(f"✅ Generated emails for {results['success']} leads! ({results['failed']} failed)")
        if results["failed"] > 0:
            st.warning(f"⚠️ {results['failed']} leads failed. Check errors below.")
            for err in results.get("errors", []):
                st.error(f"Lead **{err['name']}**: {err['error']}")
        
        st.session_state["last_campaign_id"] = selected_id
        st.markdown("➡️ Go to **View Campaigns** or **Export** to review results.")


# ═══════════════════════════════════════════════════════════════════════
# PAGE: VIEW CAMPAIGNS
# ═══════════════════════════════════════════════════════════════════════

elif page == "📋  View Campaigns":
    st.markdown('<div class="section-title">Campaigns</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Browse all campaigns and their generated email sequences</div>', unsafe_allow_html=True)
    
    campaigns = get_all_campaigns()
    
    if not campaigns:
        st.info("No campaigns yet. Import leads to get started.", icon="📌")
        st.stop()
    
    options = {f"{c['name']} — {c['status'].upper()} ({c['id'][:8]}...)": c["id"] for c in campaigns}
    selected_label = st.selectbox("Select Campaign", list(options.keys()))
    selected_id = options[selected_label]
    
    stats = get_campaign_stats(selected_id)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Status", stats.get("status", "—").upper())
    col2.metric("Leads", stats.get("total_leads", 0))
    col3.metric("Completed", stats.get("completed_leads", 0))
    col4.metric("Emails Generated", stats.get("emails_generated", 0))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    leads = get_leads_by_campaign(selected_id)
    completed_leads = [l for l in leads if l["status"] == "completed"]
    
    if not completed_leads:
        st.warning("No emails generated yet. Run the Generate Campaign step first.")
        st.stop()
    
    lead_names = {f"{l['name']} ({l['email']})": l["id"] for l in completed_leads}
    selected_lead_label = st.selectbox("Select Lead to Preview", list(lead_names.keys()))
    selected_lead_id = lead_names[selected_lead_label]
    lead = get_lead(selected_lead_id)
    
    # Lead info row
    st.markdown(f"""
    <div class="lead-row" style="margin-bottom:24px;">
      <span style="color:#e2e8f0; font-weight:700; font-size:1.05rem;">{lead['name']}</span>
      <span class="pill">{lead['email']}</span>
      <span class="pill">{lead['company']}</span>
      <span class="pill">{lead['industry']}</span>
      {score_pill(lead.get('lead_score', 50))}
    </div>
    """, unsafe_allow_html=True)
    
    emails = get_emails_for_lead(selected_lead_id)
    
    if emails:
        pd = emails[0].get("personalization_data", {})
        if pd:
            with st.expander("🎯 AI Personalization Data", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Pain Point:** {pd.get('pain_point_guess', '—')}")
                    st.markdown(f"**Improvement Area:** {pd.get('improvement_area', '—')}")
                with col2:
                    st.markdown(f"**Hook:** {pd.get('hook', '—')}")
        
        type_labels = {
            "cold_email": ("Cold Email", "email-card", "Day 1"),
            "followup_1": ("Follow-Up 1", "email-card followup", "Day 3"),
            "followup_2": ("Follow-Up 2", "email-card followup2", "Day 7"),
        }
        
        for email in emails:
            etype = email.get("email_type", "cold_email")
            label, card_class, day_label = type_labels.get(etype, (etype, "email-card", ""))
            
            st.markdown(f"""
            <div class="{card_class}">
              <span class="send-day-badge">{day_label}</span>
              <div class="email-type-tag">{label}</div>
              <div class="email-subject">✉️ {email.get('subject', '')}</div>
              <div class="email-body">{email.get('body', '').replace(chr(10), '<br>')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No emails found for this lead.")


# ═══════════════════════════════════════════════════════════════════════
# PAGE: LEAD INSPECTOR
# ═══════════════════════════════════════════════════════════════════════

elif page == "🔍  Lead Inspector":
    st.markdown('<div class="section-title">Lead Inspector</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Inspect individual lead details and their full email sequence</div>', unsafe_allow_html=True)
    
    campaigns = get_all_campaigns()
    if not campaigns:
        st.info("No campaigns found.")
        st.stop()
    
    camp_options = {f"{c['name']} ({c['id'][:8]})": c["id"] for c in campaigns}
    selected_camp = st.selectbox("Campaign", list(camp_options.keys()))
    selected_camp_id = camp_options[selected_camp]
    
    leads = get_leads_by_campaign(selected_camp_id)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("🔍 Search leads", placeholder="Name, email, or company...")
    with col2:
        status_filter = st.selectbox("Status", ["All", "completed", "pending", "failed"])
    
    filtered = leads
    if search:
        search = search.lower()
        filtered = [l for l in filtered if search in l["name"].lower() or search in l["email"].lower() or search in l["company"].lower()]
    if status_filter != "All":
        filtered = [l for l in filtered if l["status"] == status_filter]
    
    st.markdown(f"**{len(filtered)} leads**")
    
    for lead in filtered:
        with st.expander(f"{'✅' if lead['status'] == 'completed' else '⏳'} {lead['name']} — {lead['company']} ({lead['industry']})"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Email:** {lead['email']}")
                st.markdown(f"**Company:** {lead['company']}")
                st.markdown(f"**Industry:** {lead['industry']}")
            with c2:
                st.markdown(f"**Lead Score:** {lead.get('lead_score', 50)}/100")
                st.markdown(f"**Status:** {lead['status'].upper()}")
                if lead.get("website"):
                    st.markdown(f"**Website:** {lead['website']}")
            
            if lead["status"] == "completed":
                emails = get_emails_for_lead(lead["id"])
                for email in emails:
                    etype = email.get("email_type", "").replace("_", " ").title()
                    st.markdown(f"**[{etype} — Day {email['send_day']}]** {email.get('subject', '')}")
                    st.text_area(
                        "Body", email.get("body", ""),
                        height=120, key=f"body_{email['id']}",
                        disabled=True
                    )


# ═══════════════════════════════════════════════════════════════════════
# PAGE: EXPORT
# ═══════════════════════════════════════════════════════════════════════

elif page == "📤  Export":
    st.markdown('<div class="section-title">Export</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Download your campaign data in multiple formats</div>', unsafe_allow_html=True)
    
    campaigns = [c for c in get_all_campaigns() if c["status"] == "completed"]
    
    if not campaigns:
        st.info("No completed campaigns to export yet.", icon="📌")
        st.stop()
    
    options = {f"{c['name']} ({c['id'][:8]})": c["id"] for c in campaigns}
    selected_label = st.selectbox("Select Campaign", list(options.keys()))
    selected_id = options[selected_label]
    
    stats = get_campaign_stats(selected_id)
    st.info(f"📊 This campaign has **{stats.get('total_leads',0)} leads** and **{stats.get('emails_generated',0)} generated emails**.")
    
    emails = get_all_emails_for_campaign(selected_id)
    
    if not emails:
        st.warning("No emails to export.")
        st.stop()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    e1, e2, e3 = st.columns(3)
    
    with e1:
        st.markdown("#### 📊 CSV Export")
        st.markdown("Full sequences in spreadsheet format. Works with Excel, Google Sheets, and any CRM.")
        csv_content = export_to_csv(emails)
        st.download_button(
            "⬇️ Download CSV",
            csv_content,
            f"campaign_{selected_id[:8]}_emails.csv",
            "text/csv",
            use_container_width=True
        )
    
    with e2:
        st.markdown("#### 🔧 JSON Export")
        st.markdown("Structured JSON for developers and API integrations.")
        json_content = export_to_json(emails)
        st.download_button(
            "⬇️ Download JSON",
            json_content,
            f"campaign_{selected_id[:8]}_emails.json",
            "application/json",
            use_container_width=True
        )
    
    with e3:
        st.markdown("#### 📝 Text Export")
        st.markdown("Copy-paste format for Gmail, Outlook, or manual sending.")
        text_content = export_to_text(emails)
        st.download_button(
            "⬇️ Download TXT",
            text_content,
            f"campaign_{selected_id[:8]}_emails.txt",
            "text/plain",
            use_container_width=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 👀 Preview (first 2 leads)")
    preview_emails = emails[:6]
    for email in preview_emails:
        etype = email.get("email_type", "").replace("_", " ").title()
        st.markdown(f"**{email.get('lead_name')}** — {etype} (Day {email.get('send_day')})")
        st.markdown(f"*{email.get('subject')}*")
        st.text(email.get("body", "")[:200] + "...")
        st.markdown("---")

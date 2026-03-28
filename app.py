import streamlit as st
from utils.styles import inject_global_css, render_sidebar

st.set_page_config(
    page_title="TriageFlow",
    page_icon=":material/local_hospital:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar()

# --- Hero Section ---
st.markdown(
    """
    <div style="text-align: center; padding: 52px 20px 40px 20px;
        background: #F8FAFC;
        border-radius: 16px; margin-bottom: 32px;
        border: 1px solid #E2E8F0;">
        <h1 style="font-size: 3em; margin: 0; font-weight: 800;
            background: linear-gradient(135deg, #0066CC, #059669);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing: -0.03em;">TriageFlow</h1>
        <p style="font-size: 1.15em; color: #64748B; margin-top: 12px; font-weight: 400;
            max-width: 560px; margin-left: auto; margin-right: auto; line-height: 1.6;">
            AI-Powered Emergency Department Triage &amp; Care Navigation
        </p>
        <div style="display: flex; justify-content: center; gap: 10px; margin-top: 20px; flex-wrap: wrap;">
            <span style="background: rgba(0,102,204,0.08); color: #0066CC; padding: 5px 14px;
                border-radius: 6px; font-size: 0.82em; font-weight: 600;">ML Triage Model</span>
            <span style="background: rgba(5,150,105,0.08); color: #059669; padding: 5px 14px;
                border-radius: 6px; font-size: 0.82em; font-weight: 600;">Claude AI Engine</span>
            <span style="background: rgba(139,92,246,0.08); color: #8B5CF6; padding: 5px 14px;
                border-radius: 6px; font-size: 0.82em; font-weight: 600;">Synthetic EHR Data</span>
        </div>
        <div style="margin-top: 28px;">
            <a href="/Self_Triage" target="_self"
                style="display:inline-block;background:linear-gradient(135deg,#059669,#047857);
                color:white;padding:12px 32px;border-radius:10px;font-weight:700;font-size:1em;
                text-decoration:none;box-shadow:0 4px 14px rgba(5,150,105,0.3);
                letter-spacing:0.01em;">
                Enter the Live ED Waiting Room
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

stats = [
    ("10K", "Training Encounters", "#0066CC"),
    ("2K", "Synthetic Patients", "#059669"),
    ("5", "CTAS Triage Levels", "#F97316"),
    ("25+", "More Patients/Day", "#8B5CF6"),
]
stats_html = "".join(
    f'<div style="text-align:center;padding:20px 12px;background:white;border-radius:10px;'
    f'border:1px solid #E2E8F0;">'
    f'<div style="font-size:2em;font-weight:800;color:{color};letter-spacing:-0.02em;">{val}</div>'
    f'<div style="color:#64748B;font-size:0.82em;font-weight:500;margin-top:4px;">{label}</div>'
    f'</div>' for val, label, color in stats
)
st.markdown(
    f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:36px;">{stats_html}</div>',
    unsafe_allow_html=True,
)

# --- Problem ---
st.markdown("## The Problem")
problems = [
    ("6.5M Canadians", "don't have a family doctor. They rely on ERs for routine care, overwhelming the system.",
     "#DC2626", "#FEF2F2", "#7F1D1D"),
    ("4+ Hour Waits", "Canadian ER wait times are among the worst in the OECD. Patients leave without being seen.",
     "#CA8A04", "#FFFBEB", "#713F12"),
    ("Physician Burnout", "Doctors spend ~2 hours/day on admin tasks. Cognitive overload leads to errors and burnout.",
     "#2563EB", "#EFF6FF", "#1E3A5F"),
]
prob_cols = st.columns(3)
for col, (title, desc, border, bg, text_color) in zip(prob_cols, problems):
    with col:
        st.markdown(
            f'<div style="background:{bg};padding:24px;border-radius:10px;border-left:4px solid {border};height:100%;">'
            f'<h3 style="color:{border};margin-top:0;font-size:1.15em;">{title}</h3>'
            f'<p style="color:{text_color};margin:0;line-height:1.6;font-size:0.93em;">{desc}</p></div>',
            unsafe_allow_html=True,
        )

st.markdown("")

# --- Solution ---
st.markdown("## Our Solution")
st.markdown(
    """
    <div style="background: #F8FAFC; border-radius: 10px;
        padding: 28px 32px; border: 1px solid #E2E8F0;">
        <p style="color: #334155; font-size: 1em; line-height: 1.8; margin: 0;">
            <strong style="color: #0F172A;">TriageFlow</strong> is an AI-powered clinical decision support system that:<br><br>
            <strong style="color: #0066CC;">1. Routes patients to the right care</strong> — AI triage assesses symptoms and vital signs
            to recommend ER, urgent care, walk-in clinic, telehealth, or self-care.<br><br>
            <strong style="color: #059669;">2. Optimizes ED patient flow</strong> — Discrete event simulation proves AI triage serves
            25–40 more patients per 24h shift and reduces queue backlogs by 30–60 patients.<br><br>
            <strong style="color: #8B5CF6;">3. Gives clinicians instant patient context</strong> — Complete patient view with medication
            interaction checking, lab trends, and AI-generated SBAR clinical briefs.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# --- Feature Cards ---
st.markdown("## Features")

features = [
    {
        "label": "01", "title": "Care Navigator",
        "desc": "AI triage prediction (CTAS 1–5), care routing, and clinical assessment in seconds.",
        "stat": "10K encounters trained",
        "accent": "#059669",
    },
    {
        "label": "02", "title": "ED Dashboard",
        "desc": "Real-time ED patient flow, triage distribution, and facility capacity analytics.",
        "stat": "5 hospitals tracked",
        "accent": "#2563EB",
    },
    {
        "label": "03", "title": "Patient Lookup",
        "desc": "Full history, medications, lab trends, drug interactions, and AI clinical briefs.",
        "stat": "2,000 patient records",
        "accent": "#7C3AED",
    },
    {
        "label": "04", "title": "ED Simulation",
        "desc": "Discrete event simulation comparing Traditional vs AI-Optimized triage side-by-side.",
        "stat": "24h shift modeled",
        "accent": "#EA580C",
    },
    {
        "label": "05", "title": "Clinical Docs",
        "desc": "Auto-generate SOAP notes, suggest ICD-10 codes, and reduce charting time by up to 70%.",
        "stat": "2–6 hrs/day saved",
        "accent": "#DC2626",
    },
    {
        "label": "06", "title": "SMS Triage",
        "desc": "Receive triage assessment via SMS. Enter HSP number and symptoms, get care routing by text.",
        "stat": "HIPAA-aware design",
        "accent": "#DB2777",
    },
    {
        "label": "07", "title": "Email Triage",
        "desc": "Receive triage assessment via email. Full HTML report with care routing delivered to your inbox.",
        "stat": "Gmail integration",
        "accent": "#0369A1",
    },
]

feat_rows = [features[:4], features[4:]]
for row in feat_rows:
    row_cols = st.columns(len(row))
    for col_idx, feat in enumerate(row):
        with row_cols[col_idx]:
            st.markdown(
                f"""
                <div style="background: white; padding: 24px; border-radius: 10px;
                    border: 1px solid #E2E8F0; height: 100%;
                    border-top: 3px solid {feat['accent']};">
                    <div style="font-size: 0.72em; font-weight: 700; color: {feat['accent']};
                        letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 10px;">{feat['label']}</div>
                    <h3 style="margin: 0 0 8px 0; font-size: 1em; color: #0F172A;">{feat['title']}</h3>
                    <p style="color: #64748B; font-size: 0.88em; line-height: 1.6; margin-bottom: 14px;">{feat['desc']}</p>
                    <div style="font-size: 0.78em; color: {feat['accent']}; font-weight: 600;">
                        {feat['stat']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

# --- Technical Architecture ---
st.markdown("## Technical Architecture")
tech_items = [
    ("Frontend", "Streamlit + Plotly"),
    ("ML Model", "Gradient Boosting / scikit-learn"),
    ("AI Engine", "Claude API / Anthropic"),
    ("Data", "Synthea EHR — 2K patients, 10K encounters"),
    ("Email", "Gmail SMTP (TLS) / Mock mode"),
    ("SMS", "Twilio API / Mock mode"),
]
tech_html = "".join(
    f'<div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:20px;">'
    f'<div style="font-weight:700;color:#0F172A;margin-bottom:4px;font-size:0.95em;">{title}</div>'
    f'<div style="color:#64748B;font-size:0.83em;line-height:1.5;">{desc}</div></div>'
    for title, desc in tech_items
)
st.markdown(
    f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">{tech_html}</div>',
    unsafe_allow_html=True,
)

st.divider()

# --- Footer ---
st.markdown(
    """
    <div style="text-align: center; padding: 20px; background: #F8FAFC; border-radius: 10px;
        border: 1px solid #E2E8F0;">
        <p style="color: #64748B; margin: 0; font-weight: 500; font-size: 0.9em;">
            TriageFlow &middot; UVic Healthcare AI Hackathon 2026 &middot; Track 1: Clinical AI
        </p>
        <p style="color: #94A3B8; font-size: 0.78em; margin: 6px 0 0 0;">
            All patient data is synthetic. This is a decision support tool &mdash; all clinical decisions must be made by qualified healthcare professionals.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

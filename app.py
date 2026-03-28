import streamlit as st
from utils.styles import inject_global_css, render_sidebar

st.set_page_config(
    page_title="TriageFlow",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar()

# --- Hero Section ---
st.markdown(
    """
    <div style="text-align: center; padding: 48px 20px 32px 20px;
        background: linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 50%, #FDF4FF 100%);
        border-radius: 20px; margin-bottom: 32px;">
        <div style="font-size: 3.2em; margin-bottom: 8px;">🏥</div>
        <h1 style="font-size: 3.2em; margin: 0; font-weight: 800;
            background: linear-gradient(135deg, #0066CC, #059669);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            letter-spacing: -0.03em;">TriageFlow</h1>
        <p style="font-size: 1.25em; color: #64748B; margin-top: 10px; font-weight: 400; max-width: 600px; margin-left: auto; margin-right: auto;">
            AI-Powered Emergency Department Triage & Care Navigation
        </p>
        <div style="display: flex; justify-content: center; gap: 12px; margin-top: 24px; flex-wrap: wrap;">
            <span style="background: rgba(0,102,204,0.1); color: #0066CC; padding: 6px 16px;
                border-radius: 20px; font-size: 0.85em; font-weight: 600;">ML Triage Model</span>
            <span style="background: rgba(5,150,105,0.1); color: #059669; padding: 6px 16px;
                border-radius: 20px; font-size: 0.85em; font-weight: 600;">Claude AI Engine</span>
            <span style="background: rgba(139,92,246,0.1); color: #8B5CF6; padding: 6px 16px;
                border-radius: 20px; font-size: 0.85em; font-weight: 600;">Synthetic EHR Data</span>
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
    f'<div style="text-align:center;padding:20px 12px;background:white;border-radius:14px;'
    f'border:1px solid #E2E8F0;box-shadow:0 2px 8px rgba(0,0,0,0.04);">'
    f'<div style="font-size:2em;font-weight:800;color:{color};letter-spacing:-0.02em;">{val}</div>'
    f'<div style="color:#64748B;font-size:0.82em;font-weight:500;margin-top:2px;">{label}</div>'
    f'</div>' for val, label, color in stats
)
st.markdown(
    f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:36px;">{stats_html}</div>',
    unsafe_allow_html=True,
)

st.markdown("## The Problem")
problems = [
    ("🚨", "6.5M Canadians", "don't have a family doctor. They rely on ERs for routine care, overwhelming the system.",
     "linear-gradient(135deg, #FEF2F2, #FFF1F2)", "#DC2626", "#991B1B", "#7F1D1D"),
    ("⏱️", "4+ Hour Waits", "Canadian ER wait times are among the worst in the OECD. Patients leave without being seen.",
     "linear-gradient(135deg, #FFFBEB, #FEF3C7)", "#CA8A04", "#854D0E", "#713F12"),
    ("😓", "Physician Burnout", "Doctors spend ~2 hours/day on admin tasks. Cognitive overload leads to errors and burnout.",
     "linear-gradient(135deg, #EFF6FF, #DBEAFE)", "#2563EB", "#1E40AF", "#1E3A5F"),
]
prob_cols = st.columns(3)
for col, (icon, title, desc, bg, border, title_color, text_color) in zip(prob_cols, problems):
    with col:
        st.markdown(
            f'<div style="background:{bg};padding:24px;border-radius:14px;border-left:4px solid {border};'
            f'height:100%;transition:transform 0.2s ease;"'
            f' onmouseover="this.style.transform=\'translateY(-3px)\'" onmouseout="this.style.transform=\'none\'">'
            f'<div style="font-size:1.6em;margin-bottom:8px;">{icon}</div>'
            f'<h3 style="color:{title_color};margin-top:0;font-size:1.3em;">{title}</h3>'
            f'<p style="color:{text_color};margin:0;line-height:1.5;">{desc}</p></div>',
            unsafe_allow_html=True,
        )

st.markdown("")

# --- Solution ---
st.markdown("## Our Solution")
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #F0F9FF, #F0FDF4); border-radius: 14px;
        padding: 28px; border: 1px solid #E2E8F0;">
        <p style="color: #334155; font-size: 1.05em; line-height: 1.7; margin: 0;">
            <strong style="color: #0F172A;">TriageFlow</strong> is an AI-powered clinical decision support system that:<br><br>
            <strong style="color: #0066CC;">1. Routes patients to the right care</strong> — AI triage assesses symptoms and vital signs
            to recommend ER, urgent care, walk-in clinic, telehealth, or self-care.<br><br>
            <strong style="color: #059669;">2. Optimizes ED patient flow</strong> — Discrete event simulation proves AI triage serves
            25-40 more patients per 24h shift and reduces queue backlogs by 30-60 patients.<br><br>
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
        "icon": "🧭", "title": "Care Navigator",
        "desc": "AI triage prediction (CTAS 1-5), care routing, and clinical assessment in seconds.",
        "stat": "10K encounters trained",
        "gradient": "linear-gradient(135deg, #ECFDF5, #D1FAE5)",
        "accent": "#059669",
    },
    {
        "icon": "📊", "title": "ED Dashboard",
        "desc": "Real-time ED patient flow, triage distribution, and facility capacity analytics.",
        "stat": "5 hospitals tracked",
        "gradient": "linear-gradient(135deg, #EFF6FF, #DBEAFE)",
        "accent": "#2563EB",
    },
    {
        "icon": "🔍", "title": "Patient Lookup",
        "desc": "Full history, medications, lab trends, drug interactions, and AI clinical briefs.",
        "stat": "2,000 patient records",
        "gradient": "linear-gradient(135deg, #FDF4FF, #F3E8FF)",
        "accent": "#7C3AED",
    },
    {
        "icon": "⚡", "title": "ED Simulation",
        "desc": "Discrete event simulation comparing Traditional vs AI-Optimized triage side-by-side.",
        "stat": "24h shift modeled",
        "gradient": "linear-gradient(135deg, #FFF7ED, #FFEDD5)",
        "accent": "#EA580C",
    },
    {
        "icon": "📝", "title": "Clinical Docs",
        "desc": "Auto-generate SOAP notes, suggest ICD-10 codes. Reduce charting time by up to 70%.",
        "stat": "2-6 hrs/day saved",
        "gradient": "linear-gradient(135deg, #FEF2F2, #FECACA)",
        "accent": "#DC2626",
    },
    {
        "icon": "📱", "title": "SMS Triage",
        "desc": "Get triage assessment via SMS. Enter HSP number and symptoms, receive care routing by text.",
        "stat": "HIPAA-aware design",
        "gradient": "linear-gradient(135deg, #FDF2F8, #FCE7F3)",
        "accent": "#DB2777",
    },
]

# 2 rows of 3 for better card sizing
feat_rows = [features[:3], features[3:]]
for row in feat_rows:
    row_cols = st.columns(3)
    for col_idx, feat in enumerate(row):
        with row_cols[col_idx]:
            st.markdown(
                f"""
                <div style="background: {feat['gradient']}; padding: 24px 18px; border-radius: 14px;
                    text-align: center; height: 100%; transition: transform 0.2s ease;
                    border: 1px solid rgba(0,0,0,0.04);"
                    onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='none'">
                    <div style="font-size: 2em; margin-bottom: 10px;">{feat['icon']}</div>
                    <h3 style="margin: 0 0 8px 0; font-size: 1.05em; color: #0F172A;">{feat['title']}</h3>
                    <p style="color: #475569; font-size: 0.85em; line-height: 1.5; margin-bottom: 12px;">{feat['desc']}</p>
                    <div style="background: rgba(0,0,0,0.06); padding: 4px 12px; border-radius: 20px;
                        font-size: 0.75em; color: {feat['accent']}; font-weight: 600; display: inline-block;">
                        {feat['stat']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.divider()

st.markdown("## Technical Architecture")
tech_items = [
    ("🖥️", "Frontend", "Streamlit + Plotly"),
    ("🤖", "ML Model", "Gradient Boosting<br>scikit-learn"),
    ("🧠", "AI Engine", "Claude API<br>Anthropic"),
    ("🗄️", "Data", "Synthea EHR<br>2K patients, 10K encounters"),
    ("📱", "SMS", "Twilio API<br>Mock + Live modes"),
]
tech_html = "".join(
    f'<div style="background:white;border:1px solid #E2E8F0;border-radius:14px;padding:20px;'
    f'text-align:center;box-shadow:0 1px 4px rgba(0,0,0,0.04);">'
    f'<div style="font-size:1.5em;margin-bottom:6px;">{icon}</div>'
    f'<div style="font-weight:700;color:#0F172A;margin-bottom:4px;">{title}</div>'
    f'<div style="color:#64748B;font-size:0.85em;">{desc}</div></div>'
    for icon, title, desc in tech_items
)
st.markdown(
    f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;">{tech_html}</div>',
    unsafe_allow_html=True,
)

st.divider()

# --- Footer ---
st.markdown(
    """
    <div style="text-align: center; padding: 24px 20px; background: #F8FAFC; border-radius: 14px;
        border: 1px solid #E2E8F0;">
        <p style="color: #64748B; margin: 0; font-weight: 500;">
            TriageFlow &middot; UVic Healthcare AI Hackathon 2026 &middot; Track 1: Clinical AI
        </p>
        <p style="color: #94A3B8; font-size: 0.78em; margin: 8px 0 0 0;">
            All patient data is synthetic. This is a decision support tool &mdash; all clinical decisions must be made by qualified healthcare professionals.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

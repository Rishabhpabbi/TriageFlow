"""Shared CSS styles for consistent theming across TriageFlow pages."""

import streamlit as st

GLOBAL_CSS = """
<style>
/* ===== METRIC CARDS ===== */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
div[data-testid="stMetric"] label {
    color: #64748B;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-weight: 700;
    color: #0F172A;
}

/* ===== BUTTONS ===== */
button[kind="primary"] {
    background: linear-gradient(135deg, #0066CC 0%, #0052A3 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    padding: 0.6rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 8px rgba(0, 102, 204, 0.25) !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(0, 102, 204, 0.35) !important;
}
button[kind="secondary"], .stButton > button:not([kind="primary"]) {
    border-radius: 8px !important;
    border: 1px solid #E2E8F0 !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
button[kind="secondary"]:hover, .stButton > button:not([kind="primary"]):hover {
    background: #F1F5F9 !important;
    border-color: #CBD5E1 !important;
}

/* ===== SIDEBAR ===== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label {
    color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] .stMarkdown strong {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.1) !important;
}
section[data-testid="stSidebar"] a {
    color: #93C5FD !important;
    text-decoration: none !important;
}
section[data-testid="stSidebar"] a:hover {
    color: #BFDBFE !important;
}
section[data-testid="stSidebarNav"] li {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    margin-bottom: 2px;
}
section[data-testid="stSidebarNav"] li:hover {
    background: rgba(255, 255, 255, 0.1);
}
section[data-testid="stSidebarNav"] a span {
    color: #CBD5E1 !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebarNav"] li[aria-selected="true"] {
    background: rgba(59, 130, 246, 0.2);
}
section[data-testid="stSidebarNav"] li[aria-selected="true"] a span {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* ===== TABS ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #F1F5F9;
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 500;
    color: #64748B;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    font-weight: 600 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

/* ===== DATAFRAMES ===== */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #E2E8F0;
}

/* ===== INPUTS ===== */
.stTextInput input, .stNumberInput input, .stSelectbox > div > div {
    border-radius: 8px !important;
    border: 1px solid #E2E8F0 !important;
    transition: border-color 0.15s ease !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #0066CC !important;
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1) !important;
}

/* ===== DIVIDERS ===== */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(to right, transparent, #E2E8F0, transparent);
    margin: 1.5rem 0;
}

/* ===== ALERTS ===== */
.stAlert {
    border-radius: 10px !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94A3B8;
}

/* ===== TYPOGRAPHY ===== */
h1 {
    font-weight: 800 !important;
    color: #0F172A !important;
    letter-spacing: -0.02em !important;
}
h2 {
    font-weight: 700 !important;
    color: #1E293B !important;
    letter-spacing: -0.01em !important;
}
h3 {
    font-weight: 600 !important;
    color: #334155 !important;
}
</style>
"""

_SIDEBAR_HTML = """
<div style="text-align: center; padding: 8px 0 4px 0;">
    <div style="font-size: 2.2em; margin-bottom: 2px;">🏥</div>
    <h2 style="margin: 0; font-size: 1.5em; font-weight: 800;
        background: linear-gradient(135deg, #60A5FA, #34D399);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;">TriageFlow</h2>
    <p style="color: #94A3B8; font-size: 0.82em; margin-top: 4px; font-weight: 400;">
        AI-Powered ED Triage & Care Navigation
    </p>
</div>
<hr style="border: none; height: 1px; background: rgba(255,255,255,0.1); margin: 12px 0;">
<div style="padding: 0 4px;">
    <p style="color: #94A3B8; font-size: 0.7em; text-transform: uppercase;
        letter-spacing: 0.08em; font-weight: 600; margin-bottom: 8px;">Navigation</p>
    <div style="font-size: 0.88em; line-height: 2.2;">
        <div>🧭 <strong>Care Navigator</strong> <span style="color:#64748B;">— Triage & routing</span></div>
        <div>📊 <strong>ED Dashboard</strong> <span style="color:#64748B;">— Live ED analytics</span></div>
        <div>🔍 <strong>Patient Lookup</strong> <span style="color:#64748B;">— Full patient view</span></div>
        <div>⚡ <strong>ED Simulation</strong> <span style="color:#64748B;">— AI vs Traditional</span></div>
        <div>📝 <strong>Clinical Docs</strong> <span style="color:#64748B;">— SOAP & ICD-10</span></div>
        <div>📱 <strong>SMS Triage</strong> <span style="color:#64748B;">— Triage via text</span></div>
    </div>
</div>
<hr style="border: none; height: 1px; background: rgba(255,255,255,0.1); margin: 12px 0;">
<div style="text-align: center; padding: 4px 0;">
    <p style="color: #64748B; font-size: 0.75em; margin: 0;">
        UVic Healthcare AI Hackathon<br>
        <span style="color: #94A3B8;">March 27-28, 2026 | Track 1</span>
    </p>
</div>
"""


def inject_global_css():
    """Inject global CSS into the current Streamlit page (once per session)."""
    if "_tf_css_injected" not in st.session_state:
        st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
        st.session_state["_tf_css_injected"] = True


def render_sidebar():
    """Render a polished sidebar consistent across all pages."""
    with st.sidebar:
        st.markdown(_SIDEBAR_HTML, unsafe_allow_html=True)


def render_page_header(title: str, subtitle: str):
    """Render a consistent page header with title and subtitle, followed by a divider."""
    st.markdown(
        f'<div style="margin-bottom: 8px;">'
        f'<h1 style="margin: 0;">{title}</h1>'
        f'<p style="color: #64748B; font-size: 1.05em; margin-top: 4px;">{subtitle}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.divider()

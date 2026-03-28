import streamlit as st

st.set_page_config(
    page_title="TriageFlow",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/hospital-3.png", width=60)
    st.title("TriageFlow")
    st.caption("AI-Powered ED Triage & Care Navigation")
    st.divider()
    st.markdown("""
    **Pages:**
    - **Care Navigator** — Symptom assessment & care routing
    - **ED Dashboard** — Real-time ED flow & analytics
    - **Patient Lookup** — Full patient history & AI brief
    """)
    st.divider()
    st.markdown("Built for **UVic Healthcare AI Hackathon**")
    st.markdown("March 27-28, 2026 | Track 1: Clinical AI")

# --- Home Page ---
st.markdown(
    """
    <div style="text-align: center; padding: 40px 20px;">
        <h1 style="font-size: 3em; margin-bottom: 0;">TriageFlow</h1>
        <p style="font-size: 1.3em; color: #6B7280; margin-top: 8px;">
            AI-Powered Emergency Department Triage & Care Navigation
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

# --- Problem Statement ---
st.markdown("## The Problem")
prob_cols = st.columns(3)
with prob_cols[0]:
    st.markdown(
        """
        <div style="background: #FEF2F2; padding: 20px; border-radius: 12px; border-left: 4px solid #DC2626; height: 100%;">
            <h3 style="color: #991B1B;">6.5M Canadians</h3>
            <p>don't have a family doctor. They rely on ERs for routine care, overwhelming the system.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with prob_cols[1]:
    st.markdown(
        """
        <div style="background: #FFFBEB; padding: 20px; border-radius: 12px; border-left: 4px solid #CA8A04; height: 100%;">
            <h3 style="color: #854D0E;">4+ Hour Waits</h3>
            <p>Canadian ER wait times are among the worst in the OECD. Patients leave without being seen.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with prob_cols[2]:
    st.markdown(
        """
        <div style="background: #EFF6FF; padding: 20px; border-radius: 12px; border-left: 4px solid #2563EB; height: 100%;">
            <h3 style="color: #1E40AF;">Physician Burnout</h3>
            <p>Doctors spend ~2 hours/day on admin tasks. Cognitive overload leads to errors and burnout.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

# --- Solution ---
st.markdown("## Our Solution")
st.markdown(
    """
    **TriageFlow** is an AI-powered clinical decision support system that:

    1. **Routes patients to the right care** — Not everyone needs the ER. Our AI triage system
       assesses symptoms and vital signs to recommend the appropriate level of care (ER, urgent care,
       walk-in clinic, telehealth, or self-care).

    2. **Optimizes ED patient flow** — Real-time dashboard showing patient acuity, wait times,
       and capacity across Victoria-area hospitals. Helps ED staff prioritize and manage flow.

    3. **Gives clinicians instant patient context** — Complete patient view with history, medications,
       lab trends, drug interaction checks, and AI-generated clinical briefs. No more chart-digging.
    """
)

st.divider()

# --- Feature Cards ---
st.markdown("## Features")
feat_cols = st.columns(3)

with feat_cols[0]:
    st.markdown(
        """
        <div style="background: #F0FDF4; padding: 24px; border-radius: 12px; text-align: center;">
            <h3>Care Navigator</h3>
            <p>Enter symptoms + vitals. Get AI triage prediction (CTAS Level 1-5), care routing,
            and clinical assessment in seconds.</p>
            <p><strong>ML model trained on 10,000 clinical encounters</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feat_cols[1]:
    st.markdown(
        """
        <div style="background: #EFF6FF; padding: 24px; border-radius: 12px; text-align: center;">
            <h3>ED Dashboard</h3>
            <p>Real-time view of ED patient flow, triage distribution, facility capacity,
            and encounter analytics across 5 hospitals.</p>
            <p><strong>Simulated live ED board with patient status</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feat_cols[2]:
    st.markdown(
        """
        <div style="background: #FDF4FF; padding: 24px; border-radius: 12px; text-align: center;">
            <h3>Patient Lookup</h3>
            <p>Full patient history: encounters, medications, lab trends, vitals.
            Drug interaction checking. AI-generated SBAR clinical briefs.</p>
            <p><strong>2,000 patients with medically coherent data</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# --- Tech Stack ---
st.markdown("## Technical Architecture")
tech_cols = st.columns(4)
with tech_cols[0]:
    st.markdown("**Frontend**\n\nStreamlit")
with tech_cols[1]:
    st.markdown("**ML Model**\n\nGradient Boosting (scikit-learn)\n\nTrained on 10K encounters")
with tech_cols[2]:
    st.markdown("**AI Engine**\n\nClaude API (Anthropic)\n\nClinical assessment & briefs")
with tech_cols[3]:
    st.markdown("**Data**\n\nSynthea synthetic EHR\n\n2K patients, 10K encounters, 5K meds, 3K labs")

st.divider()

# --- Footer ---
st.markdown(
    """
    <div style="text-align: center; color: #9CA3AF; padding: 20px;">
        <p>TriageFlow | UVic Healthcare AI Hackathon 2026 | Track 1: Clinical AI</p>
        <p style="font-size: 0.8em;">All patient data is synthetic. This is a decision support tool — all clinical decisions must be made by qualified healthcare professionals.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

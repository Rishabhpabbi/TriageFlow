import streamlit as st
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import load_encounters, load_vitals
from utils.triage_model import train_model, load_model, predict_triage, get_care_routing
from utils.ai_engine import get_clinical_assessment
from utils.styles import inject_global_css, render_sidebar, render_page_header

st.set_page_config(page_title="Care Navigator | TriageFlow", page_icon="🧭", layout="wide")
inject_global_css()
render_sidebar()
render_page_header("🧭 Care Navigator", "Enter symptoms and vitals to get AI-powered triage assessment and care routing.")


@st.cache_resource
def get_triage_model():
    model = load_model()
    if model is None:
        with st.spinner("Training triage model on 10,000 clinical encounters..."):
            encounters = load_encounters()
            vitals = load_vitals()
            model = train_model(encounters, vitals)
    return model


model = get_triage_model()

# --- Input Form ---
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("Presenting Complaint")

    if "selected_complaints" not in st.session_state:
        st.session_state["selected_complaints"] = []

    common_complaints = [
        "chest pain", "shortness of breath", "abdominal pain", "headache",
        "fever and cough", "dizziness", "nausea and vomiting", "back pain",
        "laceration", "allergic reaction", "mental health crisis", "seizure",
    ]
    st.markdown(
        '<p style="color: #64748B; font-size: 0.82em; font-weight: 600; text-transform: uppercase; '
        'letter-spacing: 0.05em; margin-bottom: 6px;">Select Complaints (click to toggle)</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for i, complaint in enumerate(common_complaints):
        with cols[i % 4]:
            is_selected = complaint in st.session_state["selected_complaints"]
            if st.button(
                f"{'✓ ' if is_selected else ''}{complaint}",
                key=f"qc_{i}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                if is_selected:
                    st.session_state["selected_complaints"].remove(complaint)
                else:
                    st.session_state["selected_complaints"].append(complaint)
                st.rerun()

    extra_complaint = st.text_input(
        "Additional complaints (optional)",
        placeholder="Type any other symptoms not listed above...",
        help="Add free-text symptoms in addition to the quick-select buttons",
    )

    # Build combined chief complaint string
    all_complaints = list(st.session_state["selected_complaints"])
    if extra_complaint:
        all_complaints.append(extra_complaint)
    chief_complaint = ", ".join(all_complaints)

    if all_complaints:
        selected_tags = " ".join(
            f'<span style="background:#0066CC;color:white;padding:4px 12px;border-radius:16px;'
            f'font-size:0.82em;font-weight:500;display:inline-block;margin:2px;">{c}</span>'
            for c in all_complaints
        )
        st.markdown(
            f'<div style="margin-top:8px;">'
            f'<span style="color:#64748B;font-size:0.78em;font-weight:600;">Chief Complaint: </span>'
            f'{selected_tags}</div>',
            unsafe_allow_html=True,
        )

with col_right:
    st.subheader("Vital Signs")
    v_col1, v_col2 = st.columns(2)
    with v_col1:
        heart_rate = st.number_input("Heart Rate (bpm)", 30, 220, 80)
        systolic_bp = st.number_input("Systolic BP (mmHg)", 50, 250, 120)
        diastolic_bp = st.number_input("Diastolic BP (mmHg)", 20, 150, 80)
        temperature = st.number_input("Temperature (C)", 33.0, 42.0, 37.0, step=0.1)
    with v_col2:
        respiratory_rate = st.number_input("Respiratory Rate (/min)", 5, 50, 16)
        o2_saturation = st.number_input("O2 Saturation (%)", 50.0, 100.0, 98.0, step=0.5)
        pain_scale = st.slider("Pain Scale (0-10)", 0, 10, 0)

st.divider()

# --- Triage Prediction ---
if st.button("Assess Patient", type="primary", use_container_width=True, disabled=not chief_complaint):
    with st.spinner("Running AI triage assessment..."):
        result = predict_triage(
            model, chief_complaint, heart_rate, systolic_bp, diastolic_bp,
            temperature, respiratory_rate, o2_saturation, pain_scale,
        )
        routing = get_care_routing(result["predicted_level"])

    st.divider()

    ctas_styles = {
        1: ("#DC2626", "linear-gradient(135deg, #DC2626 0%, #B91C1C 100%)"),
        2: ("#EA580C", "linear-gradient(135deg, #EA580C 0%, #C2410C 100%)"),
        3: ("#CA8A04", "linear-gradient(135deg, #CA8A04 0%, #A16207 100%)"),
        4: ("#2563EB", "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)"),
        5: ("#16A34A", "linear-gradient(135deg, #16A34A 0%, #15803D 100%)"),
    }
    level = result["predicted_level"]
    level_color, bg_gradient = ctas_styles.get(level, ("#6B7280", "linear-gradient(135deg, #6B7280, #4B5563)"))

    st.markdown(
        f"""
        <div style="background: {bg_gradient}; padding: 28px; border-radius: 16px; text-align: center;
            margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
            <div style="font-size: 0.85em; color: rgba(255,255,255,0.7); text-transform: uppercase;
                letter-spacing: 0.1em; font-weight: 600; margin-bottom: 6px;">Triage Assessment Result</div>
            <h1 style="color: white; margin: 0; font-size: 2.2em; letter-spacing: -0.02em;">
                CTAS Level {level} &mdash; {result['level_name']}</h1>
            <div style="display: flex; justify-content: center; gap: 24px; margin-top: 14px;">
                <div style="background: rgba(255,255,255,0.15); padding: 6px 18px; border-radius: 20px;">
                    <span style="color: rgba(255,255,255,0.8); font-size: 0.85em;">Target Wait:</span>
                    <strong style="color: white; margin-left: 4px;">{result['target_wait']}</strong>
                </div>
                <div style="background: rgba(255,255,255,0.15); padding: 6px 18px; border-radius: 20px;">
                    <span style="color: rgba(255,255,255,0.8); font-size: 0.85em;">Confidence:</span>
                    <strong style="color: white; margin-left: 4px;">{result['confidence']:.0%}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    r_col1, r_col2, r_col3 = st.columns(3)

    with r_col1:
        st.markdown("### Care Routing")
        st.info(f"**Destination:** {routing['destination']}")
        st.markdown(f"**Action:** {routing['action']}")

    with r_col2:
        st.markdown("### Clinical Flags")
        if result["clinical_flags"]:
            for flag in result["clinical_flags"]:
                st.warning(f"  {flag}")
        else:
            st.success("No critical flags detected")

    with r_col3:
        st.markdown("### CTAS Probability Distribution")
        probs = result["probabilities"]
        fig = go.Figure(data=[
            go.Bar(
                x=[f"Level {k}" for k in sorted(probs.keys())],
                y=[probs[k] for k in sorted(probs.keys())],
                marker_color=[ctas_styles.get(k, ("#6B7280",))[0] for k in sorted(probs.keys())],
            )
        ])
        fig.update_layout(
            yaxis_title="Probability",
            yaxis_range=[0, 1],
            height=250,
            margin=dict(t=10, b=30, l=40, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### AI Clinical Assessment")
    vitals_dict = {
        "heart_rate": heart_rate,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "temperature": temperature,
        "respiratory_rate": respiratory_rate,
        "o2_saturation": o2_saturation,
        "pain_scale": pain_scale,
    }
    assessment = get_clinical_assessment(chief_complaint, vitals_dict, result)
    st.markdown(assessment)

elif not chief_complaint:
    st.info("Enter a chief complaint and vital signs above, then click **Assess Patient** to get AI-powered triage and care routing.")

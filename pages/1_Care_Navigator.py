import streamlit as st
import plotly.graph_objects as go
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import load_encounters, load_vitals
from utils.triage_model import train_model, load_model, predict_triage, get_care_routing
from utils.ai_engine import get_clinical_assessment

st.set_page_config(page_title="Care Navigator | TriageFlow", page_icon="🏥", layout="wide")

st.title("Care Navigator")
st.markdown("*Enter symptoms and vitals to get AI-powered triage assessment and care routing.*")
st.divider()


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

    # Initialize session state for complaint
    if "chief_complaint_value" not in st.session_state:
        st.session_state["chief_complaint_value"] = ""

    chief_complaint = st.text_input(
        "Chief Complaint",
        value=st.session_state["chief_complaint_value"],
        placeholder="e.g., chest pain, shortness of breath, headache...",
        help="Enter the patient's primary reason for seeking care",
        key="chief_complaint_input",
    )
    st.session_state["chief_complaint_value"] = chief_complaint

    common_complaints = [
        "chest pain", "shortness of breath", "abdominal pain", "headache",
        "fever and cough", "dizziness", "nausea and vomiting", "back pain",
        "laceration", "allergic reaction", "mental health crisis", "seizure",
    ]
    st.caption("Quick select:")
    cols = st.columns(4)
    for i, complaint in enumerate(common_complaints):
        with cols[i % 4]:
            if st.button(complaint, key=f"qc_{i}", use_container_width=True):
                st.session_state["chief_complaint_value"] = complaint
                st.rerun()

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
    if not chief_complaint:
        st.warning("Please enter a chief complaint.")
    else:
        with st.spinner("Running AI triage assessment..."):
            result = predict_triage(
                model, chief_complaint, heart_rate, systolic_bp, diastolic_bp,
                temperature, respiratory_rate, o2_saturation, pain_scale,
            )
            routing = get_care_routing(result["predicted_level"])

        # Results
        st.divider()

        # Triage Level Banner
        level = result["predicted_level"]
        color_map = {1: "#DC2626", 2: "#EA580C", 3: "#CA8A04", 4: "#2563EB", 5: "#16A34A"}
        bg_color = color_map.get(level, "#6B7280")

        st.markdown(
            f"""
            <div style="background-color: {bg_color}; padding: 24px; border-radius: 12px; text-align: center; margin-bottom: 20px;">
                <h1 style="color: white; margin: 0;">CTAS Level {level} — {result['level_name']}</h1>
                <p style="color: rgba(255,255,255,0.9); font-size: 1.2em; margin: 8px 0 0 0;">
                    Target wait time: {result['target_wait']} | Confidence: {result['confidence']:.0%}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Three columns: Routing, Flags, Probabilities
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
                    marker_color=[color_map.get(k, "#6B7280") for k in sorted(probs.keys())],
                )
            ])
            fig.update_layout(
                yaxis_title="Probability",
                yaxis_range=[0, 1],
                height=250,
                margin=dict(t=10, b=30, l=40, r=10),
            )
            st.plotly_chart(fig, use_container_width=True)

        # AI Clinical Assessment
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

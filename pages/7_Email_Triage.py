import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import load_encounters, load_vitals
from utils.triage_model import train_model, load_model, predict_triage, get_care_routing
from utils.ai_engine import get_clinical_assessment
from utils.email_service import (
    validate_bc_hsp, validate_email, format_triage_email_html,
    send_triage_email, generate_audit_entry, USE_GMAIL,
)
from utils.styles import inject_global_css, render_sidebar, render_page_header

st.set_page_config(
    page_title="Email Triage | TriageFlow",
    page_icon=":material/local_hospital:",
    layout="wide",
)
inject_global_css()
render_sidebar()
render_page_header(
    "Email Triage",
    "Enter your BC HSP number and symptoms to receive a triage assessment via email.",
)

# Compliance banner
st.markdown(
    '<div style="background:#F0F9FF;border:1px solid #BAE6FD;border-left:4px solid #0066CC;'
    'border-radius:8px;padding:14px 18px;margin-bottom:24px;">'
    '<strong style="color:#0066CC;">HIPAA-Compliant Design</strong> &mdash; '
    'All data is synthetic. Email content is minimized to reduce PHI exposure. '
    'Symptoms and vitals are not transmitted in the email. '
    'An audit trail is generated for every notification.'
    '</div>',
    unsafe_allow_html=True,
)


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

# Email mode indicator
mode_label = "Gmail (Live)" if USE_GMAIL else "Mock (Demo)"
mode_color = "#16A34A" if USE_GMAIL else "#0066CC"
st.markdown(
    f'<div style="text-align:right;margin-bottom:8px;">'
    f'<span style="background:{mode_color};color:white;padding:4px 12px;border-radius:6px;'
    f'font-size:0.78em;font-weight:600;">Email Mode: {mode_label}</span></div>',
    unsafe_allow_html=True,
)

# --- Input Form ---
id_col, symptom_col = st.columns([1, 1.3])

with id_col:
    st.subheader("Patient Identification")
    hsp_number = st.text_input(
        "BC HSP Number",
        placeholder="e.g., 912345678",
        help="9-digit BC Health Services Plan number (mock validation for demo)",
    )
    recipient_email = st.text_input(
        "Email Address",
        placeholder="e.g., patient@example.com",
        help="Email address to receive the triage assessment",
    )

with symptom_col:
    st.subheader("Presenting Symptoms")

    if "email_selected_complaints" not in st.session_state:
        st.session_state["email_selected_complaints"] = []

    common_complaints = [
        "chest pain", "shortness of breath", "abdominal pain", "headache",
        "fever and cough", "dizziness", "nausea and vomiting", "back pain",
        "laceration", "allergic reaction", "mental health crisis", "seizure",
    ]
    st.markdown(
        '<p style="color:#64748B;font-size:0.82em;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.05em;margin-bottom:6px;">Select Symptoms (click to toggle)</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for i, complaint in enumerate(common_complaints):
        with cols[i % 4]:
            is_selected = complaint in st.session_state["email_selected_complaints"]
            if st.button(
                f"{'+ ' if not is_selected else '- '}{complaint}",
                key=f"email_qc_{i}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                if is_selected:
                    st.session_state["email_selected_complaints"].remove(complaint)
                else:
                    st.session_state["email_selected_complaints"].append(complaint)
                st.rerun()

    extra = st.text_input(
        "Additional symptoms (optional)",
        placeholder="Type any other symptoms...",
        key="email_extra",
    )

    all_complaints = list(st.session_state["email_selected_complaints"])
    if extra:
        all_complaints.append(extra)
    chief_complaint = ", ".join(all_complaints)

    if all_complaints:
        tags = " ".join(
            f'<span style="background:#0066CC;color:white;padding:4px 12px;border-radius:6px;'
            f'font-size:0.82em;font-weight:500;display:inline-block;margin:2px;">{c}</span>'
            for c in all_complaints
        )
        st.markdown(f'<div style="margin-top:8px;">{tags}</div>', unsafe_allow_html=True)

# Vital signs (optional)
with st.expander("Vital Signs (optional — sensible defaults used if not provided)"):
    v_cols = st.columns(4)
    with v_cols[0]:
        heart_rate = st.number_input("Heart Rate (bpm)", 30, 220, 80, key="email_hr")
        systolic_bp = st.number_input("Systolic BP (mmHg)", 50, 250, 120, key="email_sbp")
    with v_cols[1]:
        diastolic_bp = st.number_input("Diastolic BP (mmHg)", 20, 150, 80, key="email_dbp")
        temperature = st.number_input("Temperature (C)", 33.0, 42.0, 37.0, step=0.1, key="email_temp")
    with v_cols[2]:
        respiratory_rate = st.number_input("Respiratory Rate (/min)", 5, 50, 16, key="email_rr")
        o2_saturation = st.number_input("O2 Saturation (%)", 50.0, 100.0, 98.0, step=0.5, key="email_o2")
    with v_cols[3]:
        pain_scale = st.slider("Pain Scale (0–10)", 0, 10, 0, key="email_pain")

st.divider()

# --- Assess & Preview ---
can_assess = bool(chief_complaint and hsp_number and recipient_email)
if st.button("Assess & Preview Email", type="primary", use_container_width=True, disabled=not can_assess):
    hsp_valid, hsp_err = validate_bc_hsp(hsp_number)
    email_valid, email_err = validate_email(recipient_email)

    if not hsp_valid:
        st.error(f"HSP Number: {hsp_err}")
    if not email_valid:
        st.error(f"Email: {email_err}")

    if hsp_valid and email_valid:
        with st.spinner("Running AI triage assessment..."):
            result = predict_triage(
                model, chief_complaint, heart_rate, systolic_bp, diastolic_bp,
                temperature, respiratory_rate, o2_saturation, pain_scale,
            )
            routing = get_care_routing(result["predicted_level"])

        st.session_state["email_triage_result"] = result
        st.session_state["email_routing"] = routing
        st.session_state["email_complaint"] = chief_complaint
        st.session_state["email_hsp"] = hsp_number
        st.session_state["email_recipient"] = recipient_email

# --- Display Results ---
if "email_triage_result" in st.session_state:
    result = st.session_state["email_triage_result"]
    routing = st.session_state["email_routing"]
    complaint = st.session_state["email_complaint"]
    level = result["predicted_level"]

    st.divider()

    ctas_gradients = {
        1: "linear-gradient(135deg, #DC2626, #B91C1C)",
        2: "linear-gradient(135deg, #EA580C, #C2410C)",
        3: "linear-gradient(135deg, #CA8A04, #A16207)",
        4: "linear-gradient(135deg, #2563EB, #1D4ED8)",
        5: "linear-gradient(135deg, #16A34A, #15803D)",
    }
    bg = ctas_gradients.get(level, "linear-gradient(135deg, #6B7280, #4B5563)")

    st.markdown(
        f'<div style="background:{bg};padding:24px;border-radius:12px;text-align:center;'
        f'margin-bottom:20px;box-shadow:0 4px 20px rgba(0,0,0,0.12);">'
        f'<div style="font-size:0.78em;color:rgba(255,255,255,0.7);text-transform:uppercase;'
        f'letter-spacing:0.1em;font-weight:600;">Triage Result</div>'
        f'<h2 style="color:white;margin:6px 0;font-size:1.8em;">CTAS Level {level} &mdash; {result["level_name"]}</h2>'
        f'<span style="background:rgba(255,255,255,0.15);padding:4px 14px;border-radius:20px;'
        f'color:white;font-size:0.85em;">{result["target_wait"]} &nbsp;&middot;&nbsp; {result["confidence"]:.0%} confidence</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    res_col, email_col = st.columns([1, 1])

    with res_col:
        st.markdown("### Care Routing")
        st.info(f"**Destination:** {routing['destination']}")
        st.markdown(f"**Action:** {routing['action']}")

        if result["clinical_flags"]:
            st.markdown("### Clinical Flags")
            for flag in result["clinical_flags"]:
                st.warning(f"  {flag}")
        else:
            st.success("No critical flags detected")

    with email_col:
        st.markdown("### Email Preview")
        html_preview = format_triage_email_html(result, routing, complaint)
        # Render a scaled-down iframe preview
        st.markdown(
            f'<div style="border:1px solid #E2E8F0;border-radius:10px;overflow:hidden;'
            f'background:white;max-height:420px;overflow-y:auto;">'
            f'{html_preview}'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")

        if st.button("Send Email", type="primary", use_container_width=True, key="send_email"):
            with st.spinner("Sending email..."):
                email_result = send_triage_email(
                    st.session_state["email_recipient"],
                    result,
                    routing,
                    complaint,
                )

            if email_result["success"]:
                st.success(
                    f"Email sent successfully ({email_result['mode']} mode) — "
                    f"ID: {email_result['message_id']}"
                )
            else:
                st.error(f"Email failed: {email_result['error']}")

            audit = generate_audit_entry(
                st.session_state["email_hsp"],
                st.session_state["email_recipient"],
                level,
                email_result,
            )
            with st.expander("HIPAA Audit Log Entry"):
                st.code(json.dumps(audit, indent=2), language="json")

    # AI Clinical Assessment (on-screen only, not emailed)
    st.divider()
    st.markdown("### AI Clinical Assessment")
    st.caption("This assessment is displayed on-screen only and is NOT included in the email (HIPAA — minimum necessary standard).")
    vitals_dict = {
        "heart_rate": heart_rate, "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp, "temperature": temperature,
        "respiratory_rate": respiratory_rate, "o2_saturation": o2_saturation,
        "pain_scale": pain_scale,
    }
    assessment = get_clinical_assessment(chief_complaint, vitals_dict, result)
    st.markdown(assessment)

elif not can_assess:
    st.info("Enter your **BC HSP number**, **email address**, and **select symptoms** above, then click **Assess & Preview Email**.")

st.divider()

# HIPAA compliance details
with st.expander("HIPAA Compliance & Security Details"):
    compliance_items = [
        ("Data Classification", "All data in this system is synthetic (Synthea-generated). No real patient data is used."),
        ("Minimum Necessary Standard", "Emails contain only triage level and care routing. Symptoms, vitals, and clinical details are NOT transmitted via email."),
        ("Audit Controls", "Each email event generates an audit trail entry with SHA-256 hashed patient identifiers and masked email addresses."),
        ("Transmission Security", "When using Gmail (live mode), messages are transmitted over TLS 1.3 via SMTP SSL. Mock mode simulates delivery without network activity."),
        ("Data Retention", "No data is persisted beyond the current session. In production, audit logs would be retained per organizational policy (typically 6 years)."),
        ("Access Controls", "In production, this system would require role-based access control (RBAC) and user authentication before sending clinical notifications."),
    ]
    for title, desc in compliance_items:
        st.markdown(f"**{title}:** {desc}")

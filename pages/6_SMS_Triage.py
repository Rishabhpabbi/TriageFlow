import streamlit as st
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import load_encounters, load_vitals
from utils.triage_model import train_model, load_model, predict_triage, get_care_routing
from utils.ai_engine import get_clinical_assessment
from utils.sms_service import (
    validate_bc_hsp, validate_phone, format_triage_sms,
    send_triage_sms, generate_audit_entry, USE_TWILIO,
)
from utils.styles import inject_global_css, render_sidebar, render_page_header

st.set_page_config(page_title="SMS Triage | TriageFlow", page_icon="📱", layout="wide")
inject_global_css()
render_sidebar()
render_page_header(
    "📱 SMS Triage",
    "Enter your BC HSP number and symptoms to receive a triage assessment via SMS.",
)

# HIPAA compliance banner
st.markdown(
    '<div style="background:#F0F9FF;border:1px solid #BAE6FD;border-left:4px solid #0066CC;'
    'border-radius:8px;padding:14px 18px;margin-bottom:24px;">'
    '<strong style="color:#0066CC;">HIPAA-Compliant Design</strong> &mdash; '
    'All data is synthetic. SMS content minimized to reduce PHI exposure. '
    'No diagnosis or symptoms transmitted via SMS. Audit trail generated for every notification.'
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

# SMS mode indicator
mode_label = "Twilio (Live)" if USE_TWILIO else "Mock (Demo)"
mode_color = "#16A34A" if USE_TWILIO else "#0066CC"
st.markdown(
    f'<div style="text-align:right;margin-bottom:8px;">'
    f'<span style="background:{mode_color};color:white;padding:4px 12px;border-radius:16px;'
    f'font-size:0.78em;font-weight:600;">SMS Mode: {mode_label}</span></div>',
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
    phone_number = st.text_input(
        "Phone Number",
        placeholder="e.g., (250) 555-0123",
        help="North American phone number to receive SMS triage result",
    )

with symptom_col:
    st.subheader("Presenting Symptoms")

    if "sms_selected_complaints" not in st.session_state:
        st.session_state["sms_selected_complaints"] = []

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
            is_selected = complaint in st.session_state["sms_selected_complaints"]
            if st.button(
                f"{'✓ ' if is_selected else ''}{complaint}",
                key=f"sms_qc_{i}",
                use_container_width=True,
                type="primary" if is_selected else "secondary",
            ):
                if is_selected:
                    st.session_state["sms_selected_complaints"].remove(complaint)
                else:
                    st.session_state["sms_selected_complaints"].append(complaint)
                st.rerun()

    extra = st.text_input(
        "Additional symptoms (optional)",
        placeholder="Type any other symptoms...",
        key="sms_extra",
    )

    all_complaints = list(st.session_state["sms_selected_complaints"])
    if extra:
        all_complaints.append(extra)
    chief_complaint = ", ".join(all_complaints)

    if all_complaints:
        tags = " ".join(
            f'<span style="background:#0066CC;color:white;padding:4px 12px;border-radius:16px;'
            f'font-size:0.82em;font-weight:500;display:inline-block;margin:2px;">{c}</span>'
            for c in all_complaints
        )
        st.markdown(f'<div style="margin-top:8px;">{tags}</div>', unsafe_allow_html=True)

# Vital signs (optional, in expander)
with st.expander("Vital Signs (Optional - sensible defaults used if not provided)"):
    v_cols = st.columns(4)
    with v_cols[0]:
        heart_rate = st.number_input("Heart Rate (bpm)", 30, 220, 80, key="sms_hr")
        systolic_bp = st.number_input("Systolic BP (mmHg)", 50, 250, 120, key="sms_sbp")
    with v_cols[1]:
        diastolic_bp = st.number_input("Diastolic BP (mmHg)", 20, 150, 80, key="sms_dbp")
        temperature = st.number_input("Temperature (C)", 33.0, 42.0, 37.0, step=0.1, key="sms_temp")
    with v_cols[2]:
        respiratory_rate = st.number_input("Respiratory Rate (/min)", 5, 50, 16, key="sms_rr")
        o2_saturation = st.number_input("O2 Saturation (%)", 50.0, 100.0, 98.0, step=0.5, key="sms_o2")
    with v_cols[3]:
        pain_scale = st.slider("Pain Scale (0-10)", 0, 10, 0, key="sms_pain")

st.divider()

# --- Assess & Preview ---
can_assess = bool(chief_complaint and hsp_number and phone_number)
if st.button("Assess & Preview SMS", type="primary", use_container_width=True, disabled=not can_assess):
    # Validate inputs
    hsp_valid, hsp_err = validate_bc_hsp(hsp_number)
    phone_valid, phone_err = validate_phone(phone_number)

    if not hsp_valid:
        st.error(f"HSP Number: {hsp_err}")
    if not phone_valid:
        st.error(f"Phone: {phone_err}")

    if hsp_valid and phone_valid:
        with st.spinner("Running AI triage assessment..."):
            result = predict_triage(
                model, chief_complaint, heart_rate, systolic_bp, diastolic_bp,
                temperature, respiratory_rate, o2_saturation, pain_scale,
            )
            routing = get_care_routing(result["predicted_level"])

        st.session_state["sms_triage_result"] = result
        st.session_state["sms_routing"] = routing
        st.session_state["sms_complaint"] = chief_complaint
        st.session_state["sms_hsp"] = hsp_number
        st.session_state["sms_phone"] = phone_number

# --- Display Results ---
if "sms_triage_result" in st.session_state:
    result = st.session_state["sms_triage_result"]
    routing = st.session_state["sms_routing"]
    complaint = st.session_state["sms_complaint"]
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
        f'<div style="background:{bg};padding:24px;border-radius:16px;text-align:center;'
        f'margin-bottom:20px;box-shadow:0 4px 20px rgba(0,0,0,0.15);">'
        f'<div style="font-size:0.8em;color:rgba(255,255,255,0.7);text-transform:uppercase;'
        f'letter-spacing:0.1em;font-weight:600;">Triage Result</div>'
        f'<h2 style="color:white;margin:6px 0;font-size:1.8em;">CTAS Level {level} &mdash; {result["level_name"]}</h2>'
        f'<span style="background:rgba(255,255,255,0.15);padding:4px 14px;border-radius:16px;'
        f'color:white;font-size:0.85em;">{result["target_wait"]} | {result["confidence"]:.0%} confidence</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    res_col, sms_col = st.columns([1, 1])

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

    with sms_col:
        st.markdown("### SMS Preview")
        sms_body = format_triage_sms(result, routing, complaint)
        char_count = len(sms_body)

        # Phone mockup UI
        st.markdown(
            f'<div style="max-width:340px;margin:0 auto;background:#111;border-radius:28px;'
            f'padding:36px 20px 28px 20px;box-shadow:0 8px 32px rgba(0,0,0,0.35);">'
            f'<div style="text-align:center;color:#666;font-size:0.72em;margin-bottom:14px;">Messages</div>'
            f'<div style="background:#1c1c1e;border-radius:18px;padding:14px 16px;">'
            f'<div style="color:#4ade80;font-size:0.72em;margin-bottom:6px;font-weight:600;">'
            f'TriageFlow +1 (800) 555-0199</div>'
            f'<div style="color:#f0f0f0;font-family:-apple-system,sans-serif;'
            f'font-size:0.88em;line-height:1.6;white-space:pre-line;">{sms_body}</div>'
            f'</div>'
            f'<div style="text-align:center;color:#555;font-size:0.7em;margin-top:10px;">'
            f'{char_count}/160 characters</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")

        if st.button("Send SMS", type="primary", use_container_width=True, key="send_sms"):
            with st.spinner("Sending SMS..."):
                sms_result = send_triage_sms(
                    st.session_state["sms_phone"], result, routing, complaint,
                )

            if sms_result["success"]:
                st.success(f"SMS sent successfully ({sms_result['mode']} mode) | SID: {sms_result['message_sid']}")
            else:
                st.error(f"SMS failed: {sms_result['error']}")

            # Audit log
            audit = generate_audit_entry(
                st.session_state["sms_hsp"],
                st.session_state["sms_phone"],
                level,
                sms_result,
            )
            with st.expander("HIPAA Audit Log Entry"):
                st.code(json.dumps(audit, indent=2), language="json")

    # AI Clinical Assessment (shown on page only, NOT in SMS)
    st.divider()
    st.markdown("### AI Clinical Assessment")
    st.caption("This assessment is displayed on-screen only and is NOT included in the SMS (HIPAA - minimum necessary).")
    vitals_dict = {
        "heart_rate": heart_rate, "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp, "temperature": temperature,
        "respiratory_rate": respiratory_rate, "o2_saturation": o2_saturation,
        "pain_scale": pain_scale,
    }
    assessment = get_clinical_assessment(chief_complaint, vitals_dict, result)
    st.markdown(assessment)

elif not can_assess:
    st.info("Enter your **BC HSP number**, **phone number**, and **select symptoms** above, then click **Assess & Preview SMS**.")

st.divider()

# --- HIPAA Compliance Details ---
with st.expander("HIPAA Compliance & Security Details"):
    compliance_items = [
        ("Data Classification", "All data in this system is synthetic (Synthea-generated). No real patient data is used."),
        ("Minimum Necessary Standard", "SMS messages contain only triage level and care routing. Symptoms, vitals, and clinical details are NOT transmitted via SMS."),
        ("Audit Controls", "Each SMS event generates an audit trail entry with SHA-256 hashed patient identifiers and masked phone numbers."),
        ("Transmission Security", "When using Twilio (live mode), messages are transmitted over TLS 1.2+. Mock mode simulates transmission without network activity."),
        ("Data Retention", "No data is persisted beyond the current session. In production, audit logs would be retained per organizational policy (typically 6 years)."),
        ("Access Controls", "In production, this system would require role-based access control (RBAC) and user authentication before sending clinical notifications."),
    ]
    for title, desc in compliance_items:
        st.markdown(f"**{title}:** {desc}")

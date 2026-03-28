"""
Live ED Waiting Room
====================
A demo-ready page that simulates a real emergency department waiting room.
Synthetic patients are already queued. The audience member joins the queue,
gets triaged by the AI model, and watches their position on the live board.
Hitting "Simulate Queue" progresses the queue in real-time until it's your turn,
then auto-sends a "doctor is ready" email.
"""

import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import load_encounters, load_vitals
from utils.triage_model import train_model, load_model, predict_triage, get_care_routing
from utils.ai_engine import get_clinical_assessment
from utils.email_service import validate_email, send_triage_email, send_ready_email, USE_GMAIL
from utils.styles import inject_global_css, render_sidebar

st.set_page_config(
    page_title="Live ED | TriageFlow",
    page_icon=":material/local_hospital:",
    layout="wide",
)
inject_global_css()
render_sidebar()


# ── Model ────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_triage_model():
    model = load_model()
    if model is None:
        with st.spinner("Preparing triage engine..."):
            model = train_model(load_encounters(), load_vitals())
    return model


model = get_triage_model()


# ── Synthetic patients ───────────────────────────────────────────────────────

_SYNTHETIC_PATIENTS = [
    {"name": "Margaret Chen",    "age": 72, "complaint": "chest pain, dizziness",             "channel": "Walk-in",  "ctas": 2, "vitals": (105, 155, 92, 37.2, 22, 94.0, 7)},
    {"name": "James Wilson",     "age": 45, "complaint": "laceration on forearm",             "channel": "Walk-in",  "ctas": 4, "vitals": (78, 128, 82, 36.8, 16, 98.5, 4)},
    {"name": "Priya Sharma",     "age": 34, "complaint": "fever and cough, body aches",       "channel": "Email",    "ctas": 4, "vitals": (92, 118, 76, 38.6, 20, 97.0, 3)},
    {"name": "Robert Tremblay",  "age": 58, "complaint": "severe abdominal pain, vomiting",   "channel": "Walk-in",  "ctas": 2, "vitals": (110, 142, 88, 37.8, 24, 96.0, 8)},
    {"name": "Sarah Okafor",     "age": 28, "complaint": "allergic reaction, facial swelling", "channel": "Email",    "ctas": 2, "vitals": (118, 100, 65, 37.1, 26, 93.0, 5)},
    {"name": "David Nguyen",     "age": 67, "complaint": "shortness of breath",               "channel": "Walk-in",  "ctas": 2, "vitals": (98, 160, 95, 37.0, 28, 89.0, 6)},
    {"name": "Emily Larsson",    "age": 19, "complaint": "headache, nausea",                  "channel": "Walk-in",  "ctas": 4, "vitals": (72, 115, 74, 36.9, 15, 99.0, 5)},
    {"name": "Michael Brown",    "age": 52, "complaint": "back pain",                         "channel": "Email",    "ctas": 5, "vitals": (76, 132, 84, 36.7, 16, 98.0, 3)},
    {"name": "Anika Patel",      "age": 41, "complaint": "fever and cough",                   "channel": "Email",    "ctas": 4, "vitals": (88, 122, 78, 38.2, 18, 97.5, 2)},
    {"name": "Thomas Martin",    "age": 80, "complaint": "dizziness, weakness",               "channel": "Walk-in",  "ctas": 3, "vitals": (62, 108, 62, 36.4, 14, 95.0, 2)},
    {"name": "Lisa Campbell",    "age": 37, "complaint": "nausea and vomiting",               "channel": "Walk-in",  "ctas": 4, "vitals": (82, 110, 72, 37.4, 17, 98.0, 4)},
    {"name": "Hassan Ali",       "age": 55, "complaint": "chest pain, shortness of breath",   "channel": "Email",    "ctas": 1, "vitals": (130, 88, 55, 37.5, 30, 86.0, 9)},
]

_CTAS_COLORS = {1: "#DC2626", 2: "#EA580C", 3: "#CA8A04", 4: "#2563EB", 5: "#16A34A"}
_CTAS_NAMES  = {1: "Resuscitation", 2: "Emergent", 3: "Urgent", 4: "Less Urgent", 5: "Non-Urgent"}
_CTAS_WAIT   = {1: "Immediate", 2: "15 min", 3: "30 min", 4: "60 min", 5: "120 min"}
_STATUS_OPTIONS = ["Waiting", "In Treatment", "Waiting", "Waiting", "Waiting"]


def _init_queue():
    """Build the initial synthetic waiting room. Called once per session."""
    now = datetime.now()
    queue = []
    for i, p in enumerate(_SYNTHETIC_PATIENTS):
        mins_ago = random.randint(5, 90)
        status = "In Treatment" if p["ctas"] <= 1 else random.choice(_STATUS_OPTIONS)
        queue.append({
            "id": f"synth_{i}",
            "name": p["name"],
            "age": p["age"],
            "complaint": p["complaint"],
            "ctas": p["ctas"],
            "channel": p["channel"],
            "arrival": now - timedelta(minutes=mins_ago),
            "status": status,
            "is_you": False,
            "vitals": p["vitals"],
        })
    return queue


if "ed_queue" not in st.session_state:
    st.session_state["ed_queue"] = _init_queue()
    st.session_state["you_in_queue"] = False


def _sorted_queue(queue):
    """Sort by CTAS level (ascending = most urgent first), then arrival time."""
    return sorted(queue, key=lambda p: (p["ctas"], p["arrival"]))


# ── Rendering helpers ────────────────────────────────────────────────────────

def _render_status_bar(sorted_q):
    total = len(sorted_q)
    in_tx = sum(1 for p in sorted_q if p["status"] == "In Treatment")
    waiting = total - in_tx
    high = sum(1 for p in sorted_q if p["ctas"] <= 2)
    items = [
        ("Patients in ED", str(total), "#0F172A"),
        ("Waiting", str(waiting), "#EA580C"),
        ("In Treatment", str(in_tx), "#16A34A"),
        ("High Acuity (CTAS 1-2)", str(high), "#DC2626"),
        ("Treatment Rooms", f"{in_tx}/5", "#2563EB"),
    ]
    cells = "".join(
        f'<div style="text-align:center;padding:14px 8px;">'
        f'<div style="font-size:1.6em;font-weight:800;color:{c};">{v}</div>'
        f'<div style="font-size:0.75em;color:#64748B;font-weight:600;margin-top:2px;">{l}</div>'
        f'</div>'
        for l, v, c in items
    )
    return (
        f'<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;'
        f'background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:8px 12px;'
        f'margin-bottom:24px;">{cells}</div>'
    )


def _render_queue_table(sorted_q, now=None):
    if now is None:
        now = datetime.now()

    rows = ""
    for p in sorted_q:
        ctas = p["ctas"]
        color = _CTAS_COLORS[ctas]
        is_you = p["is_you"]
        wait_mins = int((now - p["arrival"]).total_seconds() / 60)
        arrival_str = p["arrival"].strftime("%H:%M")

        row_bg = f"background:rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.06);" if is_you else ""
        highlight = "border-left:4px solid #059669;" if is_you else "border-left:4px solid transparent;"
        you_tag = (' <span style="background:#059669;color:white;padding:2px 8px;border-radius:4px;'
                   'font-size:0.72em;font-weight:700;margin-left:8px;">YOU</span>') if is_you else ""

        ch_color = "#0066CC" if p["channel"] == "Email" else ("#059669" if p["channel"] == "Self-Triage" else "#64748B")

        status = p["status"]
        if status == "In Treatment":
            st_cell = f'<span style="color:#16A34A;font-weight:600;">{status}</span>'
        elif status == "Discharged":
            st_cell = f'<span style="color:#94A3B8;font-weight:500;font-style:italic;">{status}</span>'
        else:
            st_cell = f'<span style="color:#64748B;">{status}</span>'

        row_opacity = "opacity:0.45;" if status == "Discharged" else ""

        rows += (
            f'<tr style="{row_bg}{highlight}{row_opacity}">'
            f'<td style="padding:10px 12px;font-weight:{"700" if is_you else "500"};color:#0F172A;">'
            f'{p["name"]}{you_tag}</td>'
            f'<td style="padding:10px 8px;text-align:center;">'
            f'<span style="background:{color};color:white;padding:3px 10px;border-radius:4px;'
            f'font-size:0.82em;font-weight:700;">CTAS {ctas}</span></td>'
            f'<td style="padding:10px 8px;color:#475569;font-size:0.9em;">{p["complaint"]}</td>'
            f'<td style="padding:10px 8px;text-align:center;">'
            f'<span style="color:{ch_color};font-size:0.82em;font-weight:600;">{p["channel"]}</span></td>'
            f'<td style="padding:10px 8px;text-align:center;color:#64748B;font-size:0.88em;">{arrival_str}</td>'
            f'<td style="padding:10px 8px;text-align:center;color:#64748B;font-size:0.88em;">{wait_mins} min</td>'
            f'<td style="padding:10px 8px;text-align:center;">{st_cell}</td>'
            f'</tr>'
        )

    th_style = ('padding:10px 8px;color:#475569;font-weight:700;font-size:0.8em;'
                'text-transform:uppercase;letter-spacing:0.05em;')
    return (
        f'<div style="border:1px solid #E2E8F0;border-radius:10px;overflow:hidden;margin-bottom:24px;">'
        f'<table style="width:100%;border-collapse:collapse;font-size:0.92em;">'
        f'<thead><tr style="background:#F1F5F9;border-bottom:2px solid #E2E8F0;">'
        f'<th style="{th_style}text-align:left;padding-left:12px;">Patient</th>'
        f'<th style="{th_style}text-align:center;">Triage</th>'
        f'<th style="{th_style}text-align:left;">Complaint</th>'
        f'<th style="{th_style}text-align:center;">Intake</th>'
        f'<th style="{th_style}text-align:center;">Arrived</th>'
        f'<th style="{th_style}text-align:center;">Waiting</th>'
        f'<th style="{th_style}text-align:center;">Status</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )


# ── Hero ─────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div style="text-align:center;padding:32px 20px 24px;">
        <h1 style="font-size:2.4em;margin:0;font-weight:800;color:#0F172A;
            letter-spacing:-0.03em;">Live ED Waiting Room</h1>
        <p style="color:#64748B;font-size:1.05em;margin-top:8px;max-width:580px;
            margin-left:auto;margin-right:auto;line-height:1.6;">
            Join the queue below. Our AI will triage your symptoms and show exactly
            where you fall relative to other patients — just like a real emergency department.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Live Board (placeholders so simulation can update them) ──────────────────

status_bar_ph = st.empty()
st.markdown("### Patient Queue")
st.caption("Sorted by triage priority. Higher acuity patients are seen first.")
queue_table_ph = st.empty()
position_ph = st.empty()
sim_controls_ph = st.container()

# Initial render
queue = st.session_state["ed_queue"]
sorted_q = _sorted_queue(queue)
status_bar_ph.markdown(_render_status_bar(sorted_q), unsafe_allow_html=True)
queue_table_ph.markdown(_render_queue_table(sorted_q), unsafe_allow_html=True)


# ── Position callout helper ──────────────────────────────────────────────────

def _render_position_callout(sorted_q):
    your_entry = next((p for p in sorted_q if p["is_you"]), None)
    if not your_entry:
        return ""
    total = len(sorted_q)
    your_pos = next(i for i, p in enumerate(sorted_q) if p["is_you"]) + 1
    ctas = your_entry["ctas"]
    color = _CTAS_COLORS[ctas]
    name = _CTAS_NAMES[ctas]
    wait = _CTAS_WAIT[ctas]

    advice = {
        1: "You are the highest priority. A treatment room is being prepared for you now.",
        2: "You are high priority and will be seen very shortly.",
        3: "You are in the urgent queue. A care team will see you soon.",
        4: "You are in the standard queue. You may have a wait.",
        5: "Your symptoms appear minor. A walk-in clinic or telehealth may be faster.",
    }

    return (
        f'<div style="background:linear-gradient(135deg,{color},{color}dd);padding:28px 32px;'
        f'border-radius:14px;margin-bottom:24px;box-shadow:0 4px 20px rgba(0,0,0,0.12);">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">'
        f'<div>'
        f'<div style="font-size:0.78em;color:rgba(255,255,255,0.7);text-transform:uppercase;'
        f'letter-spacing:1.2px;font-weight:600;">Your Position</div>'
        f'<div style="font-size:2.4em;font-weight:800;color:white;line-height:1.1;margin-top:4px;">'
        f'#{your_pos} of {total}</div>'
        f'<div style="color:rgba(255,255,255,0.85);margin-top:6px;font-size:0.95em;">'
        f'CTAS {ctas} — {name} &nbsp;|&nbsp; Target wait: {wait}</div>'
        f'</div>'
        f'<div style="background:rgba(255,255,255,0.15);border-radius:10px;padding:16px 24px;max-width:420px;">'
        f'<div style="color:white;font-size:0.95em;line-height:1.6;">{advice[ctas]}</div>'
        f'</div></div></div>'
    )


if st.session_state["you_in_queue"] and not st.session_state.get("patient_called"):
    position_ph.markdown(_render_position_callout(sorted_q), unsafe_allow_html=True)


# ── Simulation logic ─────────────────────────────────────────────────────────

def _run_queue_simulation():
    """Advance the queue one patient at a time until it's your turn."""
    queue = st.session_state["ed_queue"]

    # Figure out which waiting patients are ahead of "you" in priority order
    sorted_q = _sorted_queue(queue)
    your_idx = next((i for i, p in enumerate(sorted_q) if p["is_you"]), None)
    if your_idx is None:
        return

    # Patients ahead of you who are still Waiting
    ahead_waiting = [
        p for p in sorted_q[:your_idx]
        if p["status"] == "Waiting"
    ]

    # Process each one with a visible delay
    for p in ahead_waiting:
        time.sleep(3)

        # Move to In Treatment
        p["status"] = "In Treatment"
        sq = _sorted_queue(queue)
        status_bar_ph.markdown(_render_status_bar(sq), unsafe_allow_html=True)
        queue_table_ph.markdown(_render_queue_table(sq), unsafe_allow_html=True)
        position_ph.markdown(_render_position_callout(sq), unsafe_allow_html=True)

        time.sleep(2)

        # Discharge them to free the room
        p["status"] = "Discharged"
        sq = _sorted_queue(queue)
        status_bar_ph.markdown(_render_status_bar(sq), unsafe_allow_html=True)
        queue_table_ph.markdown(_render_queue_table(sq), unsafe_allow_html=True)
        position_ph.markdown(_render_position_callout(sq), unsafe_allow_html=True)

    # Now it's your turn
    time.sleep(2)
    your_entry = next(p for p in queue if p["is_you"])
    your_entry["status"] = "In Treatment"
    st.session_state["patient_called"] = True

    # Send the ready email
    your_email = st.session_state.get("q_email", "")
    your_name = st.session_state.get("q_name", "")
    your_result = st.session_state.get("portal_triage_result")
    your_routing = st.session_state.get("portal_routing")
    if your_email and your_result:
        ready_out = send_ready_email(your_email, your_name, your_result, your_routing)
        st.session_state["ready_email_result"] = ready_out

    # Final render
    sq = _sorted_queue(queue)
    status_bar_ph.markdown(_render_status_bar(sq), unsafe_allow_html=True)
    queue_table_ph.markdown(_render_queue_table(sq), unsafe_allow_html=True)

    # Replace position callout with "you're up" banner
    ready_out = st.session_state.get("ready_email_result", {})
    email_note = ""
    if ready_out.get("success"):
        email_note = (
            f'<div style="margin-top:12px;font-size:0.9em;color:rgba(255,255,255,0.8);">'
            f'"The doctor is ready for you" email sent to {your_email}</div>'
        )
    position_ph.markdown(
        f'<div style="background:linear-gradient(135deg,#059669,#047857);padding:32px;'
        f'border-radius:14px;text-align:center;margin-bottom:24px;'
        f'box-shadow:0 4px 20px rgba(5,150,105,0.25);">'
        f'<div style="font-size:2em;font-weight:800;color:white;">The doctor is ready for you</div>'
        f'<div style="color:rgba(255,255,255,0.85);font-size:1.05em;margin-top:8px;">'
        f'{your_name}, please proceed to {your_routing["destination"]}</div>'
        f'{email_note}'
        f'</div>',
        unsafe_allow_html=True,
    )


with sim_controls_ph:
    if st.session_state.get("you_in_queue") and not st.session_state.get("patient_called"):
        if st.button("Simulate Queue", type="primary", use_container_width=True, key="sim_queue"):
            _run_queue_simulation()

    if st.session_state.get("patient_called"):
        ready_out = st.session_state.get("ready_email_result", {})
        if ready_out.get("success"):
            st.markdown(
                f'<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-left:4px solid #16A34A;'
                f'border-radius:8px;padding:14px 18px;">'
                f'<strong style="color:#15803D;">Patient called.</strong> '
                f'<span style="color:#166534;">"The doctor is ready for you" notification sent to '
                f'{st.session_state.get("q_email", "")}.</span></div>',
                unsafe_allow_html=True,
            )
        elif ready_out:
            st.error(f"Notification failed: {ready_out.get('error', 'Unknown error')}")

st.divider()

# ── Join the Queue ───────────────────────────────────────────────────────────

st.markdown("### Join the Queue")
st.markdown("Enter your details and symptoms below. The AI will triage you and place you in the queue.")

_SYMPTOM_MAP = [
    ("Chest pain or tightness",       "chest pain"),
    ("Difficulty breathing",           "shortness of breath"),
    ("Stomach / abdominal pain",      "abdominal pain"),
    ("Headache",                       "headache"),
    ("Fever, cough, or cold symptoms", "fever and cough"),
    ("Dizziness or lightheadedness",   "dizziness"),
    ("Nausea or vomiting",            "nausea and vomiting"),
    ("Back pain",                      "back pain"),
    ("Cut or wound",                   "laceration"),
    ("Allergic reaction",              "allergic reaction"),
    ("Anxiety, panic, or crisis",      "mental health crisis"),
    ("Seizure",                        "seizure"),
]

name_col, email_col = st.columns(2)
with name_col:
    patient_name = st.text_input("Your name", placeholder="e.g., Jane Smith", key="q_name")
with email_col:
    patient_email = st.text_input("Email (to receive results)", placeholder="e.g., jane@example.com", key="q_email")

st.markdown(
    '<p style="font-size:0.78em;font-weight:700;color:#64748B;text-transform:uppercase;'
    'letter-spacing:0.08em;margin:12px 0 4px;">What are you experiencing?</p>',
    unsafe_allow_html=True,
)

if "portal_symptoms" not in st.session_state:
    st.session_state["portal_symptoms"] = []

cols = st.columns(4)
for i, (label, clinical) in enumerate(_SYMPTOM_MAP):
    with cols[i % 4]:
        selected = clinical in st.session_state["portal_symptoms"]
        if st.button(label, key=f"ps_{i}", use_container_width=True,
                     type="primary" if selected else "secondary"):
            if selected:
                st.session_state["portal_symptoms"].remove(clinical)
            else:
                st.session_state["portal_symptoms"].append(clinical)
            st.rerun()

extra_symptom = st.text_input("Anything else?", placeholder="Describe other symptoms...", key="portal_extra")

all_symptoms = list(st.session_state["portal_symptoms"])
if extra_symptom:
    all_symptoms.append(extra_symptom)
chief_complaint = ", ".join(all_symptoms)

if all_symptoms:
    tags = " ".join(
        f'<span style="background:#0066CC;color:white;padding:4px 12px;border-radius:6px;'
        f'font-size:0.85em;font-weight:500;display:inline-block;margin:2px;">{s}</span>'
        for s in all_symptoms
    )
    st.markdown(f'<div style="margin-top:6px;margin-bottom:12px;">{tags}</div>', unsafe_allow_html=True)

# Optional vitals
with st.expander("I know my vitals (optional)"):
    vc = st.columns(4)
    with vc[0]:
        heart_rate = st.number_input("Pulse (bpm)", 30, 220, 80, key="p_hr")
        systolic_bp = st.number_input("BP — top number", 50, 250, 120, key="p_sbp")
    with vc[1]:
        diastolic_bp = st.number_input("BP — bottom number", 20, 150, 80, key="p_dbp")
        temperature = st.number_input("Temperature (C)", 33.0, 42.0, 37.0, step=0.1, key="p_temp")
    with vc[2]:
        respiratory_rate = st.number_input("Breaths / min", 5, 50, 16, key="p_rr")
        o2_saturation = st.number_input("Oxygen sat (%)", 50.0, 100.0, 98.0, step=0.5, key="p_o2")
    with vc[3]:
        pain_scale = st.select_slider(
            "How bad is your pain?",
            options=["None", "Mild", "Moderate", "Severe", "Very Severe", "Worst Possible"],
            value="None", key="p_pain",
        )
        _PAIN_MAP = {"None": 0, "Mild": 2, "Moderate": 4, "Severe": 6, "Very Severe": 8, "Worst Possible": 10}
        pain_value = _PAIN_MAP.get(pain_scale, 0)

st.markdown("")

can_go = bool(chief_complaint and patient_name and patient_email)

if st.button("Triage Me", type="primary", use_container_width=True, disabled=not can_go):
    email_ok, email_err = validate_email(patient_email)
    if not email_ok:
        st.error(email_err)
    else:
        with st.spinner("AI is triaging your symptoms..."):
            result = predict_triage(
                model, chief_complaint,
                heart_rate, systolic_bp, diastolic_bp,
                temperature, respiratory_rate, o2_saturation, pain_value,
            )
            routing = get_care_routing(result["predicted_level"])

        # Remove previous "you" entry if re-triaging
        st.session_state["ed_queue"] = [p for p in st.session_state["ed_queue"] if not p["is_you"]]
        st.session_state["patient_called"] = False
        st.session_state.pop("ready_email_result", None)

        # Add to queue
        st.session_state["ed_queue"].append({
            "id": "you",
            "name": patient_name,
            "age": "",
            "complaint": chief_complaint,
            "ctas": result["predicted_level"],
            "channel": "Self-Triage",
            "arrival": datetime.now(),
            "status": "Waiting",
            "is_you": True,
            "vitals": (heart_rate, systolic_bp, diastolic_bp, temperature,
                       respiratory_rate, o2_saturation, pain_value),
        })
        st.session_state["you_in_queue"] = True
        st.session_state["portal_triage_result"] = result
        st.session_state["portal_routing"] = routing
        st.session_state["portal_complaint"] = chief_complaint

        # Send triage email
        email_out = send_triage_email(patient_email, result, routing, chief_complaint)
        st.session_state["portal_email_sent"] = email_out

        st.rerun()

# ── AI Assessment (shown after triage) ───────────────────────────────────────

if "portal_triage_result" in st.session_state and st.session_state["you_in_queue"]:
    result = st.session_state["portal_triage_result"]
    routing = st.session_state["portal_routing"]
    complaint = st.session_state["portal_complaint"]

    email_out = st.session_state.get("portal_email_sent", {})
    if email_out.get("success"):
        st.success(f"Triage results emailed to **{st.session_state.get('q_email', '')}** ({email_out['mode']} mode)")

    st.divider()
    st.markdown("### AI Clinical Assessment")
    st.caption("Detailed assessment shown on-screen only. Not included in the email.")
    vitals_dict = {
        "heart_rate": heart_rate, "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp, "temperature": temperature,
        "respiratory_rate": respiratory_rate, "o2_saturation": o2_saturation,
        "pain_scale": pain_value,
    }
    assessment = get_clinical_assessment(chief_complaint, vitals_dict, result)
    st.markdown(assessment)

# ── Disclaimer ───────────────────────────────────────────────────────────────

st.markdown("")
st.markdown(
    '<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;'
    'padding:14px 18px;font-size:0.85em;color:#64748B;line-height:1.6;">'
    '<strong>Disclaimer:</strong> All patients shown are synthetic. This is a decision support '
    'tool — not a medical diagnosis. If you are experiencing a medical emergency, call 911. '
    'All clinical decisions must be made by qualified healthcare professionals.'
    '</div>',
    unsafe_allow_html=True,
)

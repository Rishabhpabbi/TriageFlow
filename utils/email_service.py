"""Email triage notification service using Gmail SMTP."""

import hashlib
import re
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    import streamlit as st
    _GMAIL_SENDER = st.secrets.get("gmail", {}).get("sender", "")
    _GMAIL_APP_PASSWORD = st.secrets.get("gmail", {}).get("app_password", "")
except Exception:
    import os
    _GMAIL_SENDER = os.environ.get("GMAIL_SENDER", "")
    _GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

USE_GMAIL = bool(_GMAIL_SENDER and _GMAIL_APP_PASSWORD)

_CTAS_NAMES = {
    1: "Resuscitation",
    2: "Emergent",
    3: "Urgent",
    4: "Less Urgent",
    5: "Non-Urgent",
}

_CTAS_COLORS = {
    1: "#DC2626",
    2: "#EA580C",
    3: "#CA8A04",
    4: "#2563EB",
    5: "#16A34A",
}


def validate_email(address: str) -> tuple:
    """Basic email format validation."""
    address = address.strip()
    if not address:
        return False, "Please enter an email address."
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, address):
        return False, "Invalid email address format."
    return True, ""


def validate_bc_hsp(number: str) -> tuple:
    """Validate BC Health Services Plan number (9-digit format for demo)."""
    cleaned = re.sub(r"[\s\-]", "", number.strip())
    if not cleaned:
        return False, "Please enter a BC HSP number."
    if not cleaned.isdigit():
        return False, "HSP number must contain only digits."
    if len(cleaned) != 9:
        return False, f"HSP number must be 9 digits (got {len(cleaned)})."
    return True, ""


def format_triage_email_html(triage_result: dict, routing: dict, complaint: str) -> str:
    """Build an HTML email body with triage assessment. No symptoms in body (HIPAA)."""
    level = triage_result["predicted_level"]
    level_name = triage_result["level_name"]
    target = triage_result["target_wait"]
    confidence = triage_result["confidence"]
    destination = routing["destination"]
    action = routing["action"]
    ref = datetime.now().strftime("TF-%Y%m%d-%H%M%S")
    color = _CTAS_COLORS.get(level, "#6B7280")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:560px;margin:32px auto;background:white;border-radius:12px;
      border:1px solid #E2E8F0;overflow:hidden;">

    <!-- Header -->
    <div style="background:{color};padding:28px 32px;text-align:center;">
      <div style="font-size:11px;color:rgba(255,255,255,0.75);text-transform:uppercase;
          letter-spacing:1.5px;margin-bottom:6px;">Triage Assessment Result</div>
      <div style="font-size:26px;font-weight:800;color:white;letter-spacing:-0.5px;">
        CTAS Level {level} &mdash; {level_name}
      </div>
      <div style="margin-top:12px;display:inline-block;background:rgba(255,255,255,0.18);
          padding:6px 18px;border-radius:20px;font-size:13px;color:white;">
        Target Wait: {target} &nbsp;&middot;&nbsp; Confidence: {confidence:.0%}
      </div>
    </div>

    <!-- Body -->
    <div style="padding:28px 32px;">

      <table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
        <tr>
          <td style="width:50%;padding:16px;background:#F8FAFC;border-radius:8px;
              border:1px solid #E2E8F0;vertical-align:top;">
            <div style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;
                letter-spacing:1px;margin-bottom:6px;">Recommended Destination</div>
            <div style="font-size:15px;font-weight:600;color:#0F172A;">{destination}</div>
          </td>
          <td style="width:4px;"></td>
          <td style="width:50%;padding:16px;background:#F8FAFC;border-radius:8px;
              border:1px solid #E2E8F0;vertical-align:top;">
            <div style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;
                letter-spacing:1px;margin-bottom:6px;">Recommended Action</div>
            <div style="font-size:15px;font-weight:600;color:#0F172A;">{action}</div>
          </td>
        </tr>
      </table>

      <div style="background:#FFF7ED;border:1px solid #FED7AA;border-left:4px solid #EA580C;
          border-radius:8px;padding:14px 16px;margin-bottom:24px;font-size:13px;color:#7C2D12;">
        <strong>Note:</strong> This is a decision support tool only. All clinical decisions must
        be made by a qualified healthcare professional. If you are experiencing a medical emergency,
        call 911 immediately.
      </div>

      <div style="border-top:1px solid #E2E8F0;padding-top:16px;font-size:12px;color:#94A3B8;">
        Reference: {ref}<br>
        All patient data is synthetic (Synthea-generated). No real PHI transmitted.
      </div>
    </div>

    <!-- Footer -->
    <div style="background:#F1F5F9;padding:16px 32px;text-align:center;
        border-top:1px solid #E2E8F0;">
      <div style="font-size:12px;font-weight:700;color:#334155;">TriageFlow</div>
      <div style="font-size:11px;color:#94A3B8;margin-top:2px;">
        UVic Healthcare AI Hackathon 2026 &middot; AI-Powered ED Triage
      </div>
    </div>
  </div>
</body>
</html>"""


def format_ready_email_html(patient_name: str, triage_result: dict, routing: dict) -> str:
    """Build an HTML email notifying the patient they are ready to be seen."""
    level = triage_result["predicted_level"]
    level_name = triage_result["level_name"]
    destination = routing["destination"]
    color = _CTAS_COLORS.get(level, "#6B7280")
    ref = datetime.now().strftime("TF-%Y%m%d-%H%M%S")
    time_str = datetime.now().strftime("%I:%M %p")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:560px;margin:32px auto;background:white;border-radius:12px;
      border:1px solid #E2E8F0;overflow:hidden;">

    <!-- Header -->
    <div style="background:#059669;padding:32px;text-align:center;">
      <div style="font-size:32px;font-weight:800;color:white;letter-spacing:-0.5px;">
        The doctor is ready for you
      </div>
      <div style="margin-top:10px;color:rgba(255,255,255,0.85);font-size:15px;">
        {patient_name}, please proceed to the care team now.
      </div>
    </div>

    <!-- Body -->
    <div style="padding:28px 32px;">

      <table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
        <tr>
          <td style="padding:16px;background:#F0FDF4;border-radius:8px;
              border:1px solid #BBF7D0;text-align:center;">
            <div style="font-size:11px;font-weight:700;color:#15803D;text-transform:uppercase;
                letter-spacing:1px;margin-bottom:6px;">Proceed To</div>
            <div style="font-size:18px;font-weight:700;color:#0F172A;">{destination}</div>
          </td>
        </tr>
      </table>

      <table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
        <tr>
          <td style="width:50%;padding:14px;background:#F8FAFC;border-radius:8px;
              border:1px solid #E2E8F0;text-align:center;">
            <div style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;
                letter-spacing:1px;margin-bottom:4px;">Your Triage Level</div>
            <div style="display:inline-block;background:{color};color:white;padding:4px 14px;
                border-radius:6px;font-weight:700;font-size:14px;">CTAS {level} — {level_name}</div>
          </td>
          <td style="width:4px;"></td>
          <td style="width:50%;padding:14px;background:#F8FAFC;border-radius:8px;
              border:1px solid #E2E8F0;text-align:center;">
            <div style="font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;
                letter-spacing:1px;margin-bottom:4px;">Called At</div>
            <div style="font-size:18px;font-weight:700;color:#0F172A;">{time_str}</div>
          </td>
        </tr>
      </table>

      <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-left:4px solid #2563EB;
          border-radius:8px;padding:14px 16px;margin-bottom:24px;font-size:13px;color:#1E40AF;">
        <strong>What to bring:</strong> Your health card and a list of any medications you
        are currently taking. A member of the care team will meet you shortly.
      </div>

      <div style="border-top:1px solid #E2E8F0;padding-top:16px;font-size:12px;color:#94A3B8;">
        Reference: {ref}<br>
        All patient data is synthetic. This is a demo notification.
      </div>
    </div>

    <!-- Footer -->
    <div style="background:#F1F5F9;padding:16px 32px;text-align:center;
        border-top:1px solid #E2E8F0;">
      <div style="font-size:12px;font-weight:700;color:#334155;">TriageFlow</div>
      <div style="font-size:11px;color:#94A3B8;margin-top:2px;">
        UVic Healthcare AI Hackathon 2026 &middot; AI-Powered ED Triage
      </div>
    </div>
  </div>
</body>
</html>"""


def format_ready_email_text(patient_name: str, triage_result: dict, routing: dict) -> str:
    """Plain-text fallback for the ready notification."""
    level = triage_result["predicted_level"]
    level_name = triage_result["level_name"]
    time_str = datetime.now().strftime("%I:%M %p")
    ref = datetime.now().strftime("TF-%Y%m%d-%H%M%S")

    return (
        f"TriageFlow — The Doctor Is Ready For You\n"
        f"{'=' * 42}\n\n"
        f"{patient_name}, please proceed to the care team now.\n\n"
        f"Proceed to: {routing['destination']}\n"
        f"Triage level: CTAS {level} — {level_name}\n"
        f"Called at: {time_str}\n\n"
        f"Please bring your health card and a list of current medications.\n\n"
        f"Reference: {ref}\n"
        f"All data is synthetic. This is a demo notification."
    )


def send_ready_email(
    recipient: str,
    patient_name: str,
    triage_result: dict,
    routing: dict,
) -> dict:
    """Send a 'ready to be seen' notification email."""
    if USE_GMAIL:
        return _gmail_send_ready(recipient, patient_name, triage_result, routing)
    return _mock_send_ready(recipient, patient_name, triage_result, routing)


def _gmail_send_ready(recipient, patient_name, triage_result, routing):
    subject = f"TriageFlow: {patient_name}, the doctor is ready for you"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _GMAIL_SENDER
    msg["To"] = recipient

    msg.attach(MIMEText(format_ready_email_text(patient_name, triage_result, routing), "plain"))
    msg.attach(MIMEText(format_ready_email_html(patient_name, triage_result, routing), "html"))

    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(_GMAIL_SENDER, _GMAIL_APP_PASSWORD)
            server.sendmail(_GMAIL_SENDER, recipient, msg.as_string())

        return {
            "success": True,
            "message_id": f"gmail-ready-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "mode": "gmail",
            "to": recipient,
            "subject": subject,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "message_id": None,
            "timestamp": datetime.now().isoformat(),
            "mode": "gmail",
            "to": recipient,
            "subject": subject,
            "error": str(e),
        }


def _mock_send_ready(recipient, patient_name, triage_result, routing):
    ts = datetime.now().isoformat()
    mock_id = f"MOCK-RDY-{hashlib.md5(ts.encode()).hexdigest()[:12]}"
    return {
        "success": True,
        "message_id": mock_id,
        "timestamp": ts,
        "mode": "mock",
        "to": recipient,
        "subject": f"TriageFlow: {patient_name}, the doctor is ready for you",
        "error": None,
    }


def format_triage_email_text(triage_result: dict, routing: dict) -> str:
    """Plain-text fallback for the triage email."""
    level = triage_result["predicted_level"]
    level_name = triage_result["level_name"]
    target = triage_result["target_wait"]
    confidence = triage_result["confidence"]
    ref = datetime.now().strftime("TF-%Y%m%d-%H%M%S")

    return (
        f"TriageFlow — Triage Assessment Result\n"
        f"{'=' * 40}\n\n"
        f"CTAS Level {level} — {level_name}\n"
        f"Target Wait: {target} | Confidence: {confidence:.0%}\n\n"
        f"Destination: {routing['destination']}\n"
        f"Action: {routing['action']}\n\n"
        f"IMPORTANT: This is a decision support tool only. All clinical decisions must\n"
        f"be made by a qualified healthcare professional. Call 911 for emergencies.\n\n"
        f"Reference: {ref}\n"
        f"All data is synthetic. No real PHI transmitted."
    )


def send_triage_email(
    recipient: str,
    triage_result: dict,
    routing: dict,
    complaint: str,
) -> dict:
    """Send triage result via Gmail SMTP. Falls back to mock if credentials absent."""
    if USE_GMAIL:
        return _gmail_send(recipient, triage_result, routing, complaint)
    return _mock_send_email(recipient, triage_result, routing, complaint)


def _gmail_send(
    recipient: str,
    triage_result: dict,
    routing: dict,
    complaint: str,
) -> dict:
    level = triage_result["predicted_level"]
    level_name = triage_result["level_name"]
    subject = f"TriageFlow: CTAS Level {level} — {level_name} | Triage Assessment"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _GMAIL_SENDER
    msg["To"] = recipient

    text_body = format_triage_email_text(triage_result, routing)
    html_body = format_triage_email_html(triage_result, routing, complaint)

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(_GMAIL_SENDER, _GMAIL_APP_PASSWORD)
            server.sendmail(_GMAIL_SENDER, recipient, msg.as_string())

        return {
            "success": True,
            "message_id": f"gmail-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "mode": "gmail",
            "to": recipient,
            "subject": subject,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "message_id": None,
            "timestamp": datetime.now().isoformat(),
            "mode": "gmail",
            "to": recipient,
            "subject": subject,
            "error": str(e),
        }


def _mock_send_email(
    recipient: str,
    triage_result: dict,
    routing: dict,
    complaint: str,
) -> dict:
    ts = datetime.now().isoformat()
    mock_id = f"MOCK-EM-{hashlib.md5(ts.encode()).hexdigest()[:12]}"
    level = triage_result["predicted_level"]
    level_name = triage_result["level_name"]
    return {
        "success": True,
        "message_id": mock_id,
        "timestamp": ts,
        "mode": "mock",
        "to": recipient,
        "subject": f"TriageFlow: CTAS Level {level} — {level_name} | Triage Assessment",
        "error": None,
    }


def generate_audit_entry(
    hsp_number: str,
    recipient_email: str,
    triage_level: int,
    email_result: dict,
) -> dict:
    """Generate HIPAA-compliant audit log entry."""
    hsp_hash = hashlib.sha256(hsp_number.encode()).hexdigest()[:16]
    parts = recipient_email.split("@")
    email_masked = f"{'*' * max(2, len(parts[0]) - 2)}{parts[0][-2:]}@{parts[1]}" if len(parts) == 2 else "***"

    return {
        "timestamp": datetime.now().isoformat() + "Z",
        "event_type": "EMAIL_TRIAGE_NOTIFICATION",
        "action": "SEND",
        "patient_id_hash": f"{hsp_hash}... (SHA-256 of HSP)",
        "recipient_email": email_masked,
        "triage_level": triage_level,
        "email_status": "delivered" if email_result["success"] else "failed",
        "email_mode": email_result["mode"],
        "message_id": email_result["message_id"],
        "data_classification": "SYNTHETIC - No real PHI",
        "retention_policy": "Session only (no persistence)",
        "encryption": "TLS 1.3 (Gmail SMTP SSL)" if email_result["mode"] == "gmail" else "N/A (mock)",
    }

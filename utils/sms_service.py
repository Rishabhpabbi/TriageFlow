"""SMS triage notification service with mock/real Twilio support."""

import os
import re
import hashlib
import json
from datetime import datetime

USE_TWILIO = bool(os.environ.get("TWILIO_ACCOUNT_SID"))

# Shortened routing actions for SMS (under 160 char total)
_SMS_ACTIONS = {
    1: "CALL 911 NOW",
    2: "Go to nearest ER immediately",
    3: "Visit ER or urgent care within 30 min",
    4: "Visit a walk-in clinic today",
    5: "Call 811 or self-care appropriate",
}


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


def validate_phone(number: str) -> tuple:
    """Validate North American phone number."""
    cleaned = re.sub(r"[\s\-\(\)\+]", "", number.strip())
    if not cleaned:
        return False, "Please enter a phone number."
    if not cleaned.isdigit():
        return False, "Phone number must contain only digits."
    if cleaned.startswith("1"):
        cleaned = cleaned[1:]
    if len(cleaned) != 10:
        return False, "Phone number must be 10 digits."
    return True, ""


def normalize_phone(number: str) -> str:
    """Normalize phone to +1XXXXXXXXXX format."""
    cleaned = re.sub(r"[\s\-\(\)\+]", "", number.strip())
    if cleaned.startswith("1") and len(cleaned) == 11:
        cleaned = cleaned[1:]
    return f"+1{cleaned}"


def format_triage_sms(triage_result: dict, routing: dict, complaint: str) -> str:
    """Build SMS message under 160 characters. No symptoms included (HIPAA)."""
    level = triage_result["predicted_level"]
    level_name = triage_result["level_name"]
    target = triage_result["target_wait"]
    confidence = triage_result["confidence"]
    action = _SMS_ACTIONS.get(level, routing["action"][:40])
    ref = datetime.now().strftime("TF-%Y%m%d-%H%M%S")

    msg = (
        f"TriageFlow: CTAS {level} ({level_name})\n"
        f"Wait: {target} | Conf: {confidence:.0%}\n"
        f"{action}\n"
        f"Ref: {ref}"
    )
    return msg[:160]


def send_triage_sms(phone: str, triage_result: dict, routing: dict, complaint: str) -> dict:
    """Send triage SMS via mock or real Twilio."""
    normalized = normalize_phone(phone)
    body = format_triage_sms(triage_result, routing, complaint)

    if USE_TWILIO:
        return _twilio_send_sms(normalized, body)
    return _mock_send_sms(normalized, body)


def _mock_send_sms(phone: str, body: str) -> dict:
    """Mock SMS - simulates successful delivery."""
    ts = datetime.now().isoformat()
    mock_sid = f"MOCK-SM-{hashlib.md5(ts.encode()).hexdigest()[:12]}"
    return {
        "success": True,
        "message_sid": mock_sid,
        "timestamp": ts,
        "mode": "mock",
        "sms_body": body,
        "to": phone,
        "error": None,
    }


def _twilio_send_sms(phone: str, body: str) -> dict:
    """Real Twilio SMS send."""
    try:
        from twilio.rest import Client
        client = Client(
            os.environ["TWILIO_ACCOUNT_SID"],
            os.environ["TWILIO_AUTH_TOKEN"],
        )
        message = client.messages.create(
            body=body,
            from_=os.environ["TWILIO_FROM_NUMBER"],
            to=phone,
        )
        return {
            "success": True,
            "message_sid": message.sid,
            "timestamp": datetime.now().isoformat(),
            "mode": "twilio",
            "sms_body": body,
            "to": phone,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "message_sid": None,
            "timestamp": datetime.now().isoformat(),
            "mode": "twilio",
            "sms_body": body,
            "to": phone,
            "error": str(e),
        }


def generate_audit_entry(hsp_number: str, phone: str, triage_level: int, sms_result: dict) -> dict:
    """Generate HIPAA-compliant audit log entry with hashed/masked identifiers."""
    hsp_hash = hashlib.sha256(hsp_number.encode()).hexdigest()[:16]
    phone_masked = f"***-***-{phone[-4:]}" if len(phone) >= 4 else "***"

    return {
        "timestamp": datetime.now().isoformat() + "Z",
        "event_type": "SMS_TRIAGE_NOTIFICATION",
        "action": "SEND",
        "patient_id_hash": f"{hsp_hash}... (SHA-256 of HSP)",
        "recipient_phone": phone_masked,
        "triage_level": triage_level,
        "sms_status": "delivered" if sms_result["success"] else "failed",
        "sms_mode": sms_result["mode"],
        "message_sid": sms_result["message_sid"],
        "data_classification": "SYNTHETIC - No real PHI",
        "retention_policy": "Session only (no persistence)",
        "encryption": "TLS 1.2+ (Twilio)" if sms_result["mode"] == "twilio" else "N/A (mock)",
    }

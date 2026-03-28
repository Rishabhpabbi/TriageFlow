import os

# Set to True when you have an API key
USE_CLAUDE_API = bool(os.environ.get("ANTHROPIC_API_KEY"))


def get_clinical_assessment(chief_complaint: str, vitals: dict, triage_result: dict,
                            patient_history: dict | None = None) -> str:
    """Generate clinical assessment using Claude API or mock response."""
    if USE_CLAUDE_API:
        return _claude_assessment(chief_complaint, vitals, triage_result, patient_history)
    return _mock_assessment(chief_complaint, vitals, triage_result, patient_history)


def get_interaction_explanation(interactions: list[dict]) -> str:
    """Generate plain-language explanation of drug interactions."""
    if USE_CLAUDE_API:
        return _claude_interaction_explanation(interactions)
    return _mock_interaction_explanation(interactions)


def get_patient_brief(summary: dict) -> str:
    """Generate an SBAR-style patient brief."""
    if USE_CLAUDE_API:
        return _claude_patient_brief(summary)
    return _mock_patient_brief(summary)


# --- Claude API implementations ---

def _claude_assessment(complaint, vitals, triage, history):
    from anthropic import Anthropic
    client = Anthropic()

    history_ctx = ""
    if history:
        meds = ", ".join([m["drug_name"] for m in history.get("active_medications", [])])
        dx = ", ".join(history.get("diagnoses", [])[:5])
        history_ctx = f"\nPatient history: {history['demographics']['age']}yo {history['demographics']['sex']}, known conditions: {dx}, active medications: {meds}"

    prompt = f"""You are an emergency medicine clinical decision support system. Provide a concise clinical assessment.

Patient presents with: {complaint}
Vitals: HR {vitals.get('heart_rate', 'N/A')}, BP {vitals.get('systolic_bp', 'N/A')}/{vitals.get('diastolic_bp', 'N/A')}, Temp {vitals.get('temperature', 'N/A')}C, RR {vitals.get('respiratory_rate', 'N/A')}, O2 Sat {vitals.get('o2_saturation', 'N/A')}%, Pain {vitals.get('pain_scale', 'N/A')}/10
AI Triage Level: CTAS {triage['predicted_level']} ({triage['level_name']})
Clinical Flags: {', '.join(triage.get('clinical_flags', []))}
{history_ctx}

Provide:
1. Assessment: 2-3 sentence clinical impression
2. Differential diagnoses: Top 3 most likely
3. Recommended workup: Initial tests/imaging to order
4. Red flags to watch for

Keep it concise and actionable. This is a decision SUPPORT tool - all decisions are made by the physician."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _claude_interaction_explanation(interactions):
    from anthropic import Anthropic
    client = Anthropic()

    interaction_text = "\n".join([
        f"- {i['drug_1']} + {i['drug_2']} ({i['severity']}): {i['risk']}"
        for i in interactions
    ])

    prompt = f"""You are a clinical pharmacist. Explain these drug interactions in clear, actionable language for a physician.

{interaction_text}

For each interaction:
1. What could happen to the patient
2. What to do about it (monitor, adjust dose, substitute)
Keep it concise - 2-3 sentences per interaction."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _claude_patient_brief(summary):
    from anthropic import Anthropic
    client = Anthropic()

    demo = summary.get("demographics", {})
    meds = ", ".join([m["drug_name"] for m in summary.get("active_medications", [])])
    dx = ", ".join(summary.get("diagnoses", [])[:5])
    last_enc = summary.get("last_encounter", {})

    prompt = f"""Generate a concise SBAR clinical handoff brief for this patient.

Patient: {demo.get('name', 'Unknown')}, {demo.get('age', 'N/A')}yo {demo.get('sex', 'N/A')}
Conditions: {dx}
Active medications: {meds}
Encounter count: {summary.get('encounter_count', 0)}
Last visit: {last_enc.get('encounter_date', 'N/A')} - {last_enc.get('chief_complaint', 'N/A')} ({last_enc.get('diagnosis_description', 'N/A')})
Abnormal labs: {summary.get('abnormal_lab_count', 0)}
Risk flags: Polypharmacy={summary['risk_factors']['polypharmacy']}, Multiple conditions={summary['risk_factors']['multiple_conditions']}, Frequent ED={summary['risk_factors']['frequent_ed_visits']}

Format as SBAR (Situation, Background, Assessment, Recommendation). Keep it to 4-6 sentences total."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


# --- Mock implementations ---

def _mock_assessment(complaint, vitals, triage, history):
    flags = triage.get("clinical_flags", [])
    flag_text = ", ".join(flags) if flags else "No critical flags"

    level = triage["predicted_level"]
    level_name = triage["level_name"]

    history_note = ""
    if history:
        dx = history.get("diagnoses", [])
        if dx:
            history_note = f"\n\n**Relevant History:** Known conditions include {', '.join(dx[:3])}. "
            if history["risk_factors"]["polypharmacy"]:
                history_note += "Patient is on 5+ medications (polypharmacy risk). "
            if history["risk_factors"]["frequent_ed_visits"]:
                history_note += "Frequent ED utilizer - consider care coordination."

    assessment = f"""**Clinical Assessment (AI-Generated)**

**Impression:** Patient presents with {complaint}. Vital signs {'show concerning findings' if level <= 2 else 'are within acceptable parameters'} for CTAS Level {level} ({level_name}). {flag_text}.

**Differential Diagnoses:**
1. Most likely based on presenting complaint and vital signs
2. Consider secondary causes related to patient demographics
3. Rule out emergent conditions if red flags present

**Recommended Workup:**
- {'Immediate ECG, troponin, CBC, BMP' if 'Cardiac' in flag_text else 'CBC, BMP, urinalysis as indicated'}
- {'Chest X-ray' if any(f in complaint.lower() for f in ['chest', 'breath', 'cough']) else 'Imaging as clinically indicated'}
- Reassess in {'15 minutes' if level <= 2 else '30-60 minutes'}

**Red Flags:** {'Hemodynamic instability requiring immediate intervention' if level == 1 else 'Monitor for clinical deterioration. Reassess if symptoms worsen.'}
{history_note}

*This is a decision support tool. All clinical decisions must be made by the treating physician.*"""
    return assessment


def _mock_interaction_explanation(interactions):
    if not interactions:
        return "No significant drug interactions detected."

    explanations = []
    for i in interactions:
        severity_icon = {"HIGH": "!!!", "MODERATE": "!!", "LOW": "!"}[i["severity"]]
        explanations.append(
            f"**{severity_icon} {i['drug_1'].title()} + {i['drug_2'].title()} [{i['severity']}]**\n{i['risk']}"
        )
    return "\n\n".join(explanations)


def _mock_patient_brief(summary):
    demo = summary.get("demographics", {})
    meds = [m["drug_name"] for m in summary.get("active_medications", [])]
    dx = summary.get("diagnoses", [])
    last_enc = summary.get("last_encounter", {})
    risks = summary.get("risk_factors", {})

    risk_items = []
    if risks.get("polypharmacy"):
        risk_items.append("polypharmacy")
    if risks.get("multiple_conditions"):
        risk_items.append("multiple comorbidities")
    if risks.get("frequent_ed_visits"):
        risk_items.append("frequent ED utilizer")
    if risks.get("abnormal_labs"):
        risk_items.append("abnormal lab values")

    last_date = "N/A"
    if last_enc and last_enc.get("encounter_date"):
        last_date = str(last_enc["encounter_date"])[:10]

    return f"""**SBAR Patient Brief**

**Situation:** {demo.get('name', 'Unknown')}, {demo.get('age', 'N/A')}yo {demo.get('sex', 'N/A')}, presenting with {last_enc.get('chief_complaint', 'N/A') if last_enc else 'N/A'}. Last seen {last_date} at {last_enc.get('facility', 'N/A') if last_enc else 'N/A'}.

**Background:** {len(dx)} known conditions ({', '.join(dx[:3]) if dx else 'none documented'}). Currently on {len(meds)} active medication{'s' if len(meds) != 1 else ''} ({', '.join(meds[:4]) if meds else 'none'}). Total {summary.get('encounter_count', 0)} encounters on record.

**Assessment:** {f"Risk factors identified: {', '.join(risk_items)}." if risk_items else "No significant risk factors identified."} {summary.get('abnormal_lab_count', 0)} abnormal lab result(s) on file.

**Recommendation:** {'High-risk patient — review medication list for interactions, consider care plan coordination.' if len(risk_items) >= 2 else 'Standard care pathway. Follow up on any outstanding lab results.'}"""

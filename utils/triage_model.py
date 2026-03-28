import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
from pathlib import Path

MODEL_PATH = Path(__file__).parent / "triage_model.pkl"

# Chief complaint keywords mapped to clinical urgency signals
COMPLAINT_FEATURES = {
    "chest pain": {"cardiac_flag": 1, "urgency_weight": 5},
    "shortness of breath": {"cardiac_flag": 1, "urgency_weight": 4},
    "difficulty breathing": {"cardiac_flag": 1, "urgency_weight": 4},
    "seizure": {"neuro_flag": 1, "urgency_weight": 5},
    "unconscious": {"neuro_flag": 1, "urgency_weight": 5},
    "altered mental status": {"neuro_flag": 1, "urgency_weight": 4},
    "stroke symptoms": {"neuro_flag": 1, "urgency_weight": 5},
    "severe bleeding": {"trauma_flag": 1, "urgency_weight": 5},
    "abdominal pain": {"gi_flag": 1, "urgency_weight": 3},
    "headache": {"neuro_flag": 1, "urgency_weight": 2},
    "fever": {"infection_flag": 1, "urgency_weight": 2},
    "cough": {"respiratory_flag": 1, "urgency_weight": 1},
    "cold symptoms": {"respiratory_flag": 1, "urgency_weight": 1},
    "nausea": {"gi_flag": 1, "urgency_weight": 2},
    "vomiting": {"gi_flag": 1, "urgency_weight": 2},
    "dizziness": {"neuro_flag": 1, "urgency_weight": 2},
    "back pain": {"msk_flag": 1, "urgency_weight": 1},
    "laceration": {"trauma_flag": 1, "urgency_weight": 2},
    "fracture": {"trauma_flag": 1, "urgency_weight": 3},
    "allergic reaction": {"allergy_flag": 1, "urgency_weight": 3},
    "anaphylaxis": {"allergy_flag": 1, "urgency_weight": 5},
    "suicidal": {"psych_flag": 1, "urgency_weight": 5},
    "overdose": {"psych_flag": 1, "urgency_weight": 5},
    "mental health": {"psych_flag": 1, "urgency_weight": 3},
}


def extract_complaint_features(complaint: str) -> dict:
    """Extract clinical features from chief complaint text."""
    complaint_lower = complaint.lower()
    features = {
        "cardiac_flag": 0, "neuro_flag": 0, "trauma_flag": 0, "gi_flag": 0,
        "respiratory_flag": 0, "infection_flag": 0, "msk_flag": 0,
        "allergy_flag": 0, "psych_flag": 0, "urgency_weight": 0,
    }
    for keyword, kw_features in COMPLAINT_FEATURES.items():
        if keyword in complaint_lower:
            for k, v in kw_features.items():
                features[k] = max(features[k], v)
    return features


def build_feature_matrix(encounters: pd.DataFrame, vitals: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Build features for triage prediction from encounters + vitals."""
    merged = encounters.merge(vitals, on=["patient_id", "encounter_id"], how="inner")

    feature_rows = []
    for _, row in merged.iterrows():
        complaint_feats = extract_complaint_features(str(row.get("chief_complaint", "")))
        feature_rows.append({
            **complaint_feats,
            "heart_rate": row.get("heart_rate", 80),
            "systolic_bp": row.get("systolic_bp", 120),
            "diastolic_bp": row.get("diastolic_bp", 80),
            "temperature": row.get("temperature_celsius", 37.0),
            "respiratory_rate": row.get("respiratory_rate", 16),
            "o2_saturation": row.get("o2_saturation", 98),
            "pain_scale": row.get("pain_scale", 0),
            # Vital sign abnormality flags
            "tachycardic": 1 if row.get("heart_rate", 80) > 100 else 0,
            "bradycardic": 1 if row.get("heart_rate", 80) < 50 else 0,
            "hypotensive": 1 if row.get("systolic_bp", 120) < 90 else 0,
            "hypertensive": 1 if row.get("systolic_bp", 120) > 180 else 0,
            "febrile": 1 if row.get("temperature_celsius", 37.0) > 38.0 else 0,
            "hypothermic": 1 if row.get("temperature_celsius", 37.0) < 35.5 else 0,
            "hypoxic": 1 if row.get("o2_saturation", 98) < 92 else 0,
            "tachypneic": 1 if row.get("respiratory_rate", 16) > 22 else 0,
        })

    X = pd.DataFrame(feature_rows)
    y = merged["triage_level"]
    return X, y


def train_model(encounters: pd.DataFrame, vitals: pd.DataFrame) -> GradientBoostingClassifier:
    """Train triage prediction model."""
    X, y = build_feature_matrix(encounters, vitals)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Handle class imbalance with sample weights
    from collections import Counter
    class_counts = Counter(y_train)
    total = len(y_train)
    class_weight = {c: total / (len(class_counts) * count) for c, count in class_counts.items()}
    sample_weights = np.array([class_weight[label] for label in y_train])

    model = GradientBoostingClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        min_samples_leaf=5,
        subsample=0.8,
        random_state=42,
    )
    model.fit(X_train, y_train, sample_weight=sample_weights)

    y_pred = model.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    accuracy = report["accuracy"]
    print(f"Triage model accuracy: {accuracy:.2%}")

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    return model


def load_model() -> GradientBoostingClassifier | None:
    """Load saved model if it exists."""
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return None


def _apply_clinical_overrides(complaint_feats: dict, features: dict,
                              ml_level: int, chief_complaint: str) -> int:
    """Apply evidence-based clinical rules that override ML prediction when safety-critical.
    These reflect CTAS guidelines for presentations that MUST be triaged at certain levels."""
    complaint_lower = chief_complaint.lower()
    level = ml_level

    # CTAS 1 (Resuscitation) overrides — life-threatening presentations
    if features["hypotensive"] and features["tachycardic"]:
        level = min(level, 1)  # Hemodynamic instability
    if features["hypoxic"] and features.get("o2_saturation", 98) < 85:
        level = min(level, 1)  # Severe hypoxia
    if any(kw in complaint_lower for kw in ["cardiac arrest", "not breathing", "unconscious", "unresponsive", "anaphylaxis"]):
        level = min(level, 1)

    # CTAS 2 (Emergent) overrides
    if complaint_feats["cardiac_flag"] and (features["tachycardic"] or features["hypotensive"] or features["hypoxic"]):
        level = min(level, 2)  # Cardiac + abnormal vitals
    if complaint_feats["neuro_flag"] and complaint_feats["urgency_weight"] >= 4:
        level = min(level, 2)  # Stroke/seizure
    if complaint_feats["psych_flag"] and complaint_feats["urgency_weight"] >= 5:
        level = min(level, 2)  # Active suicidal/overdose
    if features["hypoxic"]:
        level = min(level, 2)  # Any hypoxia is emergent
    if features["hypotensive"]:
        level = min(level, 2)  # Hypotension is emergent
    if features["febrile"] and features["tachycardic"]:
        level = min(level, 2)  # Sepsis concern

    # CTAS 3 (Urgent) minimum for moderate presentations
    if complaint_feats["cardiac_flag"] and level > 3:
        level = min(level, 3)  # Chest pain always at least urgent
    if features["febrile"] and level > 3:
        level = min(level, 3)  # Fever at least urgent
    if features.get("pain_scale", 0) >= 8 and level > 3:
        level = min(level, 3)  # Severe pain at least urgent

    return level


def predict_triage(model: GradientBoostingClassifier, chief_complaint: str,
                   heart_rate: float, systolic_bp: float, diastolic_bp: float,
                   temperature: float, respiratory_rate: float,
                   o2_saturation: float, pain_scale: int) -> dict:
    """Predict CTAS triage level for a patient using ML + clinical override rules."""
    complaint_feats = extract_complaint_features(chief_complaint)

    features = {
        **complaint_feats,
        "heart_rate": heart_rate,
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "temperature": temperature,
        "respiratory_rate": respiratory_rate,
        "o2_saturation": o2_saturation,
        "pain_scale": pain_scale,
        "tachycardic": 1 if heart_rate > 100 else 0,
        "bradycardic": 1 if heart_rate < 50 else 0,
        "hypotensive": 1 if systolic_bp < 90 else 0,
        "hypertensive": 1 if systolic_bp > 180 else 0,
        "febrile": 1 if temperature > 38.0 else 0,
        "hypothermic": 1 if temperature < 35.5 else 0,
        "hypoxic": 1 if o2_saturation < 92 else 0,
        "tachypneic": 1 if respiratory_rate > 22 else 0,
    }

    X = pd.DataFrame([features])
    ml_predicted = int(model.predict(X)[0])
    probabilities = model.predict_proba(X)[0]
    class_labels = model.classes_

    # Apply clinical safety overrides
    predicted_level = _apply_clinical_overrides(complaint_feats, features, ml_predicted, chief_complaint)
    was_overridden = predicted_level != ml_predicted

    CTAS_LABELS = {
        1: "Resuscitation",
        2: "Emergent",
        3: "Urgent",
        4: "Less Urgent",
        5: "Non-Urgent",
    }
    CTAS_WAIT = {
        1: "Immediate",
        2: "< 15 minutes",
        3: "< 30 minutes",
        4: "< 60 minutes",
        5: "< 120 minutes",
    }

    # Build reasoning based on flagged features
    reasons = []
    if complaint_feats["cardiac_flag"]:
        reasons.append("Cardiac symptoms detected")
    if complaint_feats["neuro_flag"]:
        reasons.append("Neurological symptoms detected")
    if complaint_feats["trauma_flag"]:
        reasons.append("Trauma indicators present")
    if complaint_feats["psych_flag"]:
        reasons.append("Mental health/psychiatric concern")
    if features["hypotensive"]:
        reasons.append(f"Hypotension (BP {systolic_bp}/{diastolic_bp})")
    if features["tachycardic"]:
        reasons.append(f"Tachycardia (HR {heart_rate})")
    if features["hypoxic"]:
        reasons.append(f"Hypoxia (O2 sat {o2_saturation}%)")
    if features["febrile"]:
        reasons.append(f"Fever ({temperature}C)")
    if features["tachypneic"]:
        reasons.append(f"Tachypnea (RR {respiratory_rate})")
    if pain_scale >= 8:
        reasons.append(f"Severe pain ({pain_scale}/10)")
    if was_overridden:
        reasons.append(f"Clinical override: upgraded from CTAS {ml_predicted} to {predicted_level}")

    return {
        "predicted_level": predicted_level,
        "ml_predicted": ml_predicted,
        "was_overridden": was_overridden,
        "level_name": CTAS_LABELS.get(predicted_level, "Unknown"),
        "target_wait": CTAS_WAIT.get(predicted_level, "Unknown"),
        "confidence": float(max(probabilities)),
        "probabilities": {int(c): float(p) for c, p in zip(class_labels, probabilities)},
        "clinical_flags": reasons,
    }


CARE_ROUTING = {
    1: {"destination": "Emergency Department - Resuscitation Bay", "action": "CALL 911 / Immediate medical attention", "color": "red"},
    2: {"destination": "Emergency Department - Urgent", "action": "Go to nearest ER immediately", "color": "orange"},
    3: {"destination": "Emergency Department or Urgent Care", "action": "Visit ER or urgent care clinic within 30 minutes", "color": "yellow"},
    4: {"destination": "Walk-in Clinic or Urgent Care", "action": "Visit a walk-in clinic today. ER not required.", "color": "blue"},
    5: {"destination": "Family Doctor / Telehealth / Pharmacist", "action": "Book an appointment or call 811 (HealthLink BC). Self-care may be appropriate.", "color": "green"},
}


def get_care_routing(triage_level: int) -> dict:
    """Get care routing recommendation based on triage level."""
    return CARE_ROUTING.get(triage_level, CARE_ROUTING[3])

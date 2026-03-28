import pandas as pd
from pathlib import Path

# Resolve data directory relative to this file
_BASE = Path(__file__).resolve().parent.parent.parent
_TRACK1 = _BASE / "Data Sources for Hackathon" / "hackathon-data" / "track-1-clinical-ai" / "synthea-patients"
_SHARED = _BASE / "Data Sources for Hackathon" / "hackathon-data" / "shared"
_DRUG_DB = _SHARED / "drug-database" / "canadian_drug_reference.csv"


def load_patients() -> pd.DataFrame:
    df = pd.read_csv(_TRACK1 / "patients.csv")
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"])
    return df


def load_encounters() -> pd.DataFrame:
    df = pd.read_csv(_TRACK1 / "encounters.csv")
    df["encounter_date"] = pd.to_datetime(df["encounter_date"])
    return df


def load_medications() -> pd.DataFrame:
    df = pd.read_csv(_TRACK1 / "medications.csv")
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
    return df


def load_lab_results() -> pd.DataFrame:
    df = pd.read_csv(_TRACK1 / "lab_results.csv")
    df["collected_date"] = pd.to_datetime(df["collected_date"])
    return df


def load_vitals() -> pd.DataFrame:
    df = pd.read_csv(_TRACK1 / "vitals.csv")
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    return df


def load_drug_reference() -> pd.DataFrame:
    return pd.read_csv(_DRUG_DB)


def get_patient_summary(patient_id: str, patients: pd.DataFrame, encounters: pd.DataFrame,
                        medications: pd.DataFrame, lab_results: pd.DataFrame,
                        vitals: pd.DataFrame) -> dict:
    """Build a complete patient summary from all datasets."""
    patient = patients[patients["patient_id"] == patient_id]
    if patient.empty:
        return {}

    p = patient.iloc[0]
    p_enc = encounters[encounters["patient_id"] == patient_id].sort_values("encounter_date", ascending=False)
    p_meds = medications[medications["patient_id"] == patient_id]
    p_labs = lab_results[lab_results["patient_id"] == patient_id].sort_values("collected_date", ascending=False)
    p_vitals = vitals[vitals["patient_id"] == patient_id].sort_values("recorded_at", ascending=False)

    active_meds = p_meds[p_meds["active"] == True]
    abnormal_labs = p_labs[p_labs["abnormal_flag"] != "N"]
    unique_diagnoses = p_enc["diagnosis_description"].dropna().unique().tolist()

    return {
        "demographics": {
            "name": f"{p['first_name']} {p['last_name']}",
            "age": int(p["age"]),
            "sex": p["sex"],
            "blood_type": p["blood_type"],
            "postal_code": p["postal_code"],
        },
        "encounter_count": len(p_enc),
        "last_encounter": p_enc.iloc[0].to_dict() if not p_enc.empty else None,
        "diagnoses": unique_diagnoses,
        "active_medications": active_meds[["drug_name", "dosage", "frequency"]].to_dict("records"),
        "recent_labs": p_labs.head(10)[["test_name", "value", "unit", "abnormal_flag", "collected_date"]].to_dict("records"),
        "abnormal_lab_count": len(abnormal_labs),
        "latest_vitals": p_vitals.iloc[0].to_dict() if not p_vitals.empty else None,
        "risk_factors": {
            "polypharmacy": len(active_meds) >= 5,
            "multiple_conditions": len(unique_diagnoses) >= 3,
            "frequent_ed_visits": len(p_enc[p_enc["encounter_type"] == "emergency"]) >= 3,
            "abnormal_labs": len(abnormal_labs) > 0,
        }
    }


# Known drug interaction pairs (simplified for hackathon)
DRUG_INTERACTIONS = {
    frozenset(["warfarin", "ibuprofen"]): {"severity": "HIGH", "risk": "Increased bleeding risk — NSAIDs inhibit platelet function and can cause GI bleeding when combined with anticoagulants."},
    frozenset(["warfarin", "acetaminophen"]): {"severity": "MODERATE", "risk": "High-dose acetaminophen may enhance anticoagulant effect of warfarin. Monitor INR closely."},
    frozenset(["metformin", "furosemide"]): {"severity": "MODERATE", "risk": "Furosemide may increase blood glucose, reducing metformin effectiveness. Monitor glucose."},
    frozenset(["lisinopril", "potassium chloride"]): {"severity": "HIGH", "risk": "ACE inhibitors increase potassium retention. Adding potassium supplements risks hyperkalemia."},
    frozenset(["lisinopril", "spironolactone"]): {"severity": "HIGH", "risk": "Both drugs increase potassium. Combination significantly increases hyperkalemia risk."},
    frozenset(["metoprolol", "verapamil"]): {"severity": "HIGH", "risk": "Both slow heart rate and AV conduction. Combination risks severe bradycardia or heart block."},
    frozenset(["simvastatin", "amlodipine"]): {"severity": "MODERATE", "risk": "Amlodipine increases simvastatin levels. Limit simvastatin to 20mg/day with amlodipine."},
    frozenset(["clopidogrel", "omeprazole"]): {"severity": "MODERATE", "risk": "Omeprazole reduces clopidogrel activation via CYP2C19 inhibition. Consider pantoprazole instead."},
    frozenset(["metformin", "contrast dye"]): {"severity": "HIGH", "risk": "IV contrast can cause acute kidney injury. Hold metformin 48h before/after contrast procedures."},
    frozenset(["ssri", "opioid"]): {"severity": "HIGH", "risk": "Serotonin syndrome risk with tramadol/fentanyl. CNS depression risk with all opioids. Monitor closely."},
    frozenset(["gabapentin", "opioid"]): {"severity": "HIGH", "risk": "CNS depression risk. Combined respiratory depression can be fatal."},
    frozenset(["ciprofloxacin", "tizanidine"]): {"severity": "HIGH", "risk": "Ciprofloxacin dramatically increases tizanidine levels — risk of severe hypotension and sedation."},
    frozenset(["atorvastatin", "clarithromycin"]): {"severity": "HIGH", "risk": "Clarithromycin inhibits statin metabolism, increasing rhabdomyolysis risk."},
    frozenset(["atorvastatin", "gemfibrozil"]): {"severity": "HIGH", "risk": "Fibrates increase statin levels, significantly increasing rhabdomyolysis risk."},
    frozenset(["hydrochlorothiazide", "lithium"]): {"severity": "HIGH", "risk": "Thiazides reduce lithium clearance, risking lithium toxicity."},
    frozenset(["methotrexate", "ibuprofen"]): {"severity": "HIGH", "risk": "NSAIDs reduce methotrexate clearance, increasing toxicity risk."},
    frozenset(["warfarin", "aspirin"]): {"severity": "HIGH", "risk": "Dual antiplatelet/anticoagulant therapy significantly increases bleeding risk."},
    frozenset(["insulin", "metformin"]): {"severity": "LOW", "risk": "Common combination for diabetes. Monitor for hypoglycemia, especially with dose changes."},
}

# Drug class mapping for interaction checking
DRUG_CLASS_MAP = {
    "sertraline": "ssri", "fluoxetine": "ssri", "paroxetine": "ssri", "citalopram": "ssri", "escitalopram": "ssri",
    "morphine": "opioid", "oxycodone": "opioid", "hydromorphone": "opioid", "codeine": "opioid", "fentanyl": "opioid",
    "tramadol": "opioid",
}


def check_drug_interactions(medication_list: list[str]) -> list[dict]:
    """Check a list of drug names for known interactions."""
    meds_lower = [m.lower().strip() for m in medication_list]
    # Expand to include class names
    expanded = set(meds_lower)
    for med in meds_lower:
        if med in DRUG_CLASS_MAP:
            expanded.add(DRUG_CLASS_MAP[med])

    interactions = []
    expanded_list = list(expanded)
    for i in range(len(expanded_list)):
        for j in range(i + 1, len(expanded_list)):
            pair = frozenset([expanded_list[i], expanded_list[j]])
            if pair in DRUG_INTERACTIONS:
                info = DRUG_INTERACTIONS[pair]
                interactions.append({
                    "drug_1": expanded_list[i],
                    "drug_2": expanded_list[j],
                    "severity": info["severity"],
                    "risk": info["risk"],
                })
    return sorted(interactions, key=lambda x: {"HIGH": 0, "MODERATE": 1, "LOW": 2}[x["severity"]])

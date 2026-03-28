import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import (
    load_patients, load_encounters, load_medications,
    load_lab_results, load_vitals, load_drug_reference,
    get_patient_summary, check_drug_interactions,
)
from utils.ai_engine import get_patient_brief, get_interaction_explanation
from utils.styles import inject_global_css, render_sidebar, render_page_header

st.set_page_config(page_title="Patient Lookup | TriageFlow", page_icon="🔍", layout="wide")
inject_global_css()
render_sidebar()
render_page_header("🔍 Patient Lookup", "Complete patient view with history, medications, labs, vitals, and AI-generated clinical brief.")


@st.cache_data
def load_all():
    return (load_patients(), load_encounters(), load_medications(),
            load_lab_results(), load_vitals(), load_drug_reference())


patients, encounters, medications, lab_results, vitals, drug_ref = load_all()

# --- Patient Search ---
search_col1, search_col2 = st.columns([2, 1])

with search_col1:
    search_term = st.text_input("Search by Patient ID or Name", placeholder="e.g., PAT-000042 or Margaret")

with search_col2:
    st.markdown("<br>", unsafe_allow_html=True)

# Filter patients
if search_term:
    mask = (
        patients["patient_id"].str.contains(search_term, case=False, na=False) |
        patients["first_name"].str.contains(search_term, case=False, na=False) |
        patients["last_name"].str.contains(search_term, case=False, na=False)
    )
    filtered = patients[mask].head(20)
else:
    filtered = patients.head(20)

# Patient selector
if not filtered.empty:
    options = filtered.apply(lambda r: f"{r['patient_id']} — {r['first_name']} {r['last_name']} ({r['age']}yo {r['sex']})", axis=1).tolist()
    selected = st.selectbox("Select Patient", options)
    selected_id = selected.split(" — ")[0]

    # Get full summary
    summary = get_patient_summary(selected_id, patients, encounters, medications, lab_results, vitals)

    if summary:
        demo = summary["demographics"]

        # --- Demographics Banner ---
        st.divider()
        risk_count = sum(1 for v in summary["risk_factors"].values() if v)
        risk_label = "High" if risk_count >= 3 else "Medium" if risk_count >= 1 else "Low"
        risk_color = "#DC2626" if risk_label == "High" else "#CA8A04" if risk_label == "Medium" else "#16A34A"

        demo_items = [
            ("Patient", demo["name"], "#0066CC"),
            ("Age / Sex", f"{demo['age']}yo {demo['sex']}", "#334155"),
            ("Blood Type", demo["blood_type"], "#334155"),
            ("Encounters", str(summary["encounter_count"]), "#2563EB"),
            ("Risk Level", risk_label, risk_color),
            ("Risk Factors", str(risk_count), risk_color),
        ]
        demo_html = "".join(
            f'<div style="text-align:center;padding:16px 12px;background:white;border-radius:12px;'
            f'border:1px solid #E2E8F0;box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
            f'<div style="color:#64748B;font-size:0.72rem;font-weight:600;text-transform:uppercase;'
            f'letter-spacing:0.05em;margin-bottom:6px;">{label}</div>'
            f'<div style="font-size:1.2rem;font-weight:700;color:{color};">{value}</div>'
            f'</div>' for label, value, color in demo_items
        )
        st.markdown(
            f'<div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr 1fr 1fr;gap:10px;margin-bottom:8px;">'
            f'{demo_html}</div>',
            unsafe_allow_html=True,
        )

        st.divider()

        # --- Tabs ---
        tab_overview, tab_meds, tab_labs, tab_vitals, tab_ai = st.tabs([
            "Overview", "Medications", "Lab Results", "Vitals", "AI Brief"
        ])

        # --- Overview Tab ---
        with tab_overview:
            ov_col1, ov_col2 = st.columns(2)

            with ov_col1:
                st.subheader("Known Conditions")
                if summary["diagnoses"]:
                    for dx in summary["diagnoses"][:10]:
                        st.markdown(f"- {dx}")
                else:
                    st.info("No conditions on record")

                st.subheader("Risk Factors")
                rf = summary["risk_factors"]
                if rf["polypharmacy"]:
                    st.warning("Polypharmacy: 5+ active medications")
                if rf["multiple_conditions"]:
                    st.warning("Multiple comorbidities: 3+ conditions")
                if rf["frequent_ed_visits"]:
                    st.warning("Frequent ED utilizer: 3+ emergency visits")
                if rf["abnormal_labs"]:
                    st.warning(f"Abnormal labs: {summary['abnormal_lab_count']} result(s)")
                if not any(rf.values()):
                    st.success("No significant risk factors")

            with ov_col2:
                st.subheader("Recent Encounters")
                p_enc = encounters[encounters["patient_id"] == selected_id].sort_values("encounter_date", ascending=False).head(10)
                if not p_enc.empty:
                    enc_display = p_enc[["encounter_date", "encounter_type", "facility", "chief_complaint", "diagnosis_description", "triage_level"]].copy()
                    enc_display["encounter_date"] = enc_display["encounter_date"].dt.strftime("%Y-%m-%d")
                    enc_display.columns = ["Date", "Type", "Facility", "Complaint", "Diagnosis", "CTAS"]
                    st.dataframe(enc_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No encounters on record")

        # --- Medications Tab ---
        with tab_meds:
            p_meds = medications[medications["patient_id"] == selected_id]

            med_col1, med_col2 = st.columns([1.5, 1])

            with med_col1:
                st.subheader("Active Medications")
                active = p_meds[p_meds["active"] == True]
                if not active.empty:
                    med_display = active[["drug_name", "dosage", "frequency", "route", "start_date"]].copy()
                    med_display["start_date"] = med_display["start_date"].dt.strftime("%Y-%m-%d")
                    med_display.columns = ["Drug", "Dosage", "Frequency", "Route", "Started"]
                    st.dataframe(med_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No active medications")

                st.subheader("Past Medications")
                past = p_meds[p_meds["active"] == False]
                if not past.empty:
                    past_display = past[["drug_name", "dosage", "frequency", "start_date", "end_date"]].copy()
                    past_display["start_date"] = past_display["start_date"].dt.strftime("%Y-%m-%d")
                    past_display["end_date"] = past_display["end_date"].dt.strftime("%Y-%m-%d")
                    past_display.columns = ["Drug", "Dosage", "Frequency", "Started", "Ended"]
                    st.dataframe(past_display, use_container_width=True, hide_index=True)

            with med_col2:
                st.subheader("Drug Interaction Check")
                active_drug_names = active["drug_name"].tolist() if not active.empty else []
                if active_drug_names:
                    interactions = check_drug_interactions(active_drug_names)
                    if interactions:
                        for ix in interactions:
                            severity_color = {"HIGH": "error", "MODERATE": "warning", "LOW": "info"}
                            getattr(st, severity_color.get(ix["severity"], "info"))(
                                f"**{ix['severity']}**: {ix['drug_1'].title()} + {ix['drug_2'].title()}\n\n{ix['risk']}"
                            )
                        with st.expander("AI Explanation"):
                            st.markdown(get_interaction_explanation(interactions))
                    else:
                        st.success("No known interactions detected among active medications.")
                else:
                    st.info("No active medications to check.")

        # --- Labs Tab ---
        with tab_labs:
            p_labs = lab_results[lab_results["patient_id"] == selected_id].sort_values("collected_date", ascending=False)

            if not p_labs.empty:
                lab_col1, lab_col2 = st.columns([1.5, 1])

                with lab_col1:
                    st.subheader("Lab Results")
                    abnormal_only = st.toggle("Show abnormal only", value=False)
                    display_labs = p_labs[p_labs["abnormal_flag"] != "N"] if abnormal_only else p_labs

                    lab_display = display_labs[["collected_date", "test_name", "value", "unit", "reference_range_low", "reference_range_high", "abnormal_flag"]].copy()
                    lab_display["collected_date"] = lab_display["collected_date"].dt.strftime("%Y-%m-%d")
                    lab_display["reference"] = lab_display["reference_range_low"].astype(str) + " - " + lab_display["reference_range_high"].astype(str)
                    lab_display = lab_display[["collected_date", "test_name", "value", "unit", "reference", "abnormal_flag"]]
                    lab_display.columns = ["Date", "Test", "Value", "Unit", "Reference Range", "Flag"]

                    def highlight_abnormal(val):
                        return "background-color: #FEE2E2; color: #991B1B; font-weight: bold;" if val != "N" else ""

                    styled = lab_display.style.map(highlight_abnormal, subset=["Flag"])
                    st.dataframe(styled, use_container_width=True, hide_index=True)

                with lab_col2:
                    st.subheader("Lab Trends")
                    test_types = p_labs["test_name"].unique()
                    selected_test = st.selectbox("Select test to plot", test_types)
                    test_data = p_labs[p_labs["test_name"] == selected_test].sort_values("collected_date")

                    if len(test_data) > 0:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=test_data["collected_date"], y=test_data["value"],
                            mode="lines+markers", name="Value",
                            line=dict(color="#2563EB"),
                        ))
                        # Reference range band
                        if test_data["reference_range_low"].notna().any():
                            fig.add_hrect(
                                y0=test_data["reference_range_low"].iloc[0],
                                y1=test_data["reference_range_high"].iloc[0],
                                fillcolor="#DCFCE7", opacity=0.3,
                                line_width=0, annotation_text="Normal Range",
                            )
                        fig.update_layout(
                            yaxis_title=f"{selected_test} ({test_data['unit'].iloc[0]})",
                            height=300, margin=dict(t=10),
                        )
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No lab results on record")

        # --- Vitals Tab ---
        with tab_vitals:
            p_vitals = vitals[vitals["patient_id"] == selected_id].sort_values("recorded_at")

            if not p_vitals.empty:
                st.subheader("Vital Sign Trends")

                vital_options = {
                    "Heart Rate": ("heart_rate", "bpm", (60, 100)),
                    "Systolic BP": ("systolic_bp", "mmHg", (90, 140)),
                    "Diastolic BP": ("diastolic_bp", "mmHg", (60, 90)),
                    "Temperature": ("temperature_celsius", "C", (36.1, 37.8)),
                    "O2 Saturation": ("o2_saturation", "%", (95, 100)),
                    "Respiratory Rate": ("respiratory_rate", "/min", (12, 20)),
                    "Pain Scale": ("pain_scale", "/10", (0, 3)),
                }

                v_cols = st.columns(2)
                for i, (label, (col, unit, (lo, hi))) in enumerate(vital_options.items()):
                    with v_cols[i % 2]:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=p_vitals["recorded_at"], y=p_vitals[col],
                            mode="lines+markers", name=label,
                            line=dict(color="#2563EB"),
                        ))
                        fig.add_hrect(y0=lo, y1=hi, fillcolor="#DCFCE7", opacity=0.2, line_width=0)
                        fig.update_layout(title=label, yaxis_title=unit, height=250,
                                          margin=dict(t=30, b=20))
                        st.plotly_chart(fig, use_container_width=True)

                # Latest vitals table
                st.subheader("Latest Vitals")
                latest = p_vitals.iloc[-1]
                vt_cols = st.columns(7)
                with vt_cols[0]:
                    st.metric("HR", f"{latest['heart_rate']} bpm")
                with vt_cols[1]:
                    st.metric("BP", f"{latest['systolic_bp']}/{latest['diastolic_bp']}")
                with vt_cols[2]:
                    st.metric("Temp", f"{latest['temperature_celsius']}C")
                with vt_cols[3]:
                    st.metric("RR", f"{latest['respiratory_rate']}/min")
                with vt_cols[4]:
                    st.metric("O2 Sat", f"{latest['o2_saturation']}%")
                with vt_cols[5]:
                    st.metric("Pain", f"{latest['pain_scale']}/10")
                with vt_cols[6]:
                    st.metric("Recorded", str(latest["recorded_at"])[:16])
            else:
                st.info("No vital signs on record")

        # --- AI Brief Tab ---
        with tab_ai:
            st.subheader("AI-Generated Patient Brief")
            if st.button("Generate SBAR Brief", type="primary"):
                with st.spinner("Generating clinical brief..."):
                    brief = get_patient_brief(summary)
                st.markdown(brief)
                st.divider()
                st.caption("This brief is AI-generated for decision support. Verify all information against the patient record.")
            else:
                st.info("Click **Generate SBAR Brief** to create an AI-powered clinical handoff summary for this patient.")

else:
    st.warning("No patients found matching your search.")

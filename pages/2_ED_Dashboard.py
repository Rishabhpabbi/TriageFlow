import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_loader import load_patients, load_encounters, load_vitals
from utils.styles import inject_global_css, render_sidebar, render_page_header

st.set_page_config(page_title="ED Dashboard | TriageFlow", page_icon="📊", layout="wide")
inject_global_css()
render_sidebar()
render_page_header("📊 Emergency Department Dashboard", "Real-time view of ED patient flow, wait times, and capacity across Victoria-area hospitals.")


@st.cache_data
def load_all_data():
    patients = load_patients()
    encounters = load_encounters()
    vitals = load_vitals()
    return patients, encounters, vitals


patients, encounters, vitals = load_all_data()

# --- Simulated "Live" ED Board ---
# Use recent encounters to simulate current ED state
facilities = encounters["facility"].unique()
selected_facility = st.selectbox("Select Facility", ["All Facilities"] + sorted(facilities.tolist()))

if selected_facility != "All Facilities":
    facility_enc = encounters[encounters["facility"] == selected_facility]
else:
    facility_enc = encounters

# --- KPI Cards ---
st.subheader("Key Metrics")
kpi_cols = st.columns(5)

total_encounters = len(facility_enc)
emergency_enc = facility_enc[facility_enc["encounter_type"] == "emergency"]
avg_los = facility_enc["length_of_stay_hours"].mean()
triage_dist = facility_enc["triage_level"].value_counts().sort_index()
high_acuity = len(facility_enc[facility_enc["triage_level"].isin([1, 2])])

with kpi_cols[0]:
    st.metric("Total Encounters", f"{total_encounters:,}")
with kpi_cols[1]:
    st.metric("Emergency Visits", f"{len(emergency_enc):,}")
with kpi_cols[2]:
    st.metric("Avg Length of Stay", f"{avg_los:.1f} hrs")
with kpi_cols[3]:
    pct_high = (high_acuity / total_encounters * 100) if total_encounters > 0 else 0
    st.metric("High Acuity (CTAS 1-2)", f"{high_acuity:,}", delta=f"{pct_high:.1f}%")
with kpi_cols[4]:
    admitted = len(facility_enc[facility_enc["disposition"] == "admitted"])
    admit_rate = (admitted / total_encounters * 100) if total_encounters > 0 else 0
    st.metric("Admission Rate", f"{admit_rate:.1f}%")

st.divider()

# --- Simulated Live ED Board ---
st.subheader("Simulated ED Board (Current Patients)")

# Take the most recent 20 emergency encounters as "current" patients
recent_emergency = facility_enc[facility_enc["encounter_type"] == "emergency"].sort_values("encounter_date", ascending=False).head(20)

if not recent_emergency.empty:
    board_data = recent_emergency.merge(patients[["patient_id", "first_name", "last_name", "age", "sex"]], on="patient_id", how="left")
    board_data = board_data.merge(vitals[["patient_id", "encounter_id", "heart_rate", "systolic_bp", "diastolic_bp", "o2_saturation", "pain_scale"]], on=["patient_id", "encounter_id"], how="left")

    # Simulate wait times and status
    rng = np.random.default_rng(42)
    statuses = rng.choice(["Waiting", "In Treatment", "Awaiting Results", "Ready for Discharge"], size=len(board_data), p=[0.3, 0.35, 0.2, 0.15])
    wait_minutes = rng.exponential(scale=45, size=len(board_data)).astype(int)

    # Handle NaN vitals from left join
    bp_sys = board_data["systolic_bp"].fillna(0).astype(int).astype(str).replace("0", "--")
    bp_dia = board_data["diastolic_bp"].fillna(0).astype(int).astype(str).replace("0", "--")

    board_display = pd.DataFrame({
        "Patient": board_data["first_name"] + " " + board_data["last_name"].str[0] + ".",
        "Age": board_data["age"],
        "Sex": board_data["sex"],
        "CTAS": board_data["triage_level"],
        "Chief Complaint": board_data["chief_complaint"],
        "Status": statuses,
        "Wait (min)": wait_minutes,
        "HR": board_data["heart_rate"].fillna(0).astype(int).replace(0, "--"),
        "BP": bp_sys + "/" + bp_dia,
        "O2": board_data["o2_saturation"].fillna(0).replace(0, "--"),
        "Pain": board_data["pain_scale"].fillna(0).astype(int).replace(0, "--"),
        "Facility": board_data["facility"],
    })

    def color_triage(val):
        colors = {1: "background-color: #FEE2E2; color: #991B1B;",
                  2: "background-color: #FFEDD5; color: #9A3412;",
                  3: "background-color: #FEF9C3; color: #854D0E;",
                  4: "background-color: #DBEAFE; color: #1E40AF;",
                  5: "background-color: #DCFCE7; color: #166534;"}
        return colors.get(val, "")

    def color_status(val):
        colors = {"Waiting": "color: #DC2626; font-weight: bold;",
                  "In Treatment": "color: #2563EB;",
                  "Awaiting Results": "color: #CA8A04;",
                  "Ready for Discharge": "color: #16A34A;"}
        return colors.get(val, "")

    styled = board_display.style.map(color_triage, subset=["CTAS"]).map(color_status, subset=["Status"])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=500)

st.divider()

# --- Analytics ---
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("Triage Level Distribution")
    triage_counts = facility_enc["triage_level"].value_counts().sort_index()
    ctas_labels = {1: "1-Resuscitation", 2: "2-Emergent", 3: "3-Urgent", 4: "4-Less Urgent", 5: "5-Non-Urgent"}
    colors = ["#DC2626", "#EA580C", "#CA8A04", "#2563EB", "#16A34A"]

    fig = go.Figure(data=[go.Bar(
        x=[ctas_labels.get(k, str(k)) for k in triage_counts.index],
        y=triage_counts.values,
        marker_color=[colors[k-1] for k in triage_counts.index],
    )])
    fig.update_layout(yaxis_title="Count", height=350, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("Encounters by Facility")
    fac_counts = facility_enc["facility"].value_counts()
    fig = px.pie(values=fac_counts.values, names=fac_counts.index, hole=0.4,
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=350, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

# --- Time series ---
st.subheader("Encounter Volume Over Time")
facility_enc_copy = facility_enc.copy()
facility_enc_copy["month"] = facility_enc_copy["encounter_date"].dt.to_period("M").astype(str)
monthly = facility_enc_copy.groupby(["month", "encounter_type"]).size().reset_index(name="count")

fig = px.bar(monthly, x="month", y="count", color="encounter_type",
             barmode="stack", color_discrete_sequence=["#DC2626", "#2563EB", "#16A34A"])
fig.update_layout(xaxis_title="Month", yaxis_title="Encounters", height=350,
                  margin=dict(t=10), xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# --- Top Diagnoses ---
diag_col1, diag_col2 = st.columns(2)

with diag_col1:
    st.subheader("Top 10 Diagnoses (All)")
    top_dx = facility_enc["diagnosis_description"].value_counts().head(10)
    fig = px.bar(x=top_dx.values, y=top_dx.index, orientation="h",
                 color_discrete_sequence=["#2563EB"])
    fig.update_layout(yaxis_title="", xaxis_title="Count", height=350,
                      margin=dict(t=10, l=200), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

with diag_col2:
    st.subheader("Top 10 Diagnoses (Emergency)")
    top_dx_emerg = emergency_enc["diagnosis_description"].value_counts().head(10)
    fig = px.bar(x=top_dx_emerg.values, y=top_dx_emerg.index, orientation="h",
                 color_discrete_sequence=["#DC2626"])
    fig.update_layout(yaxis_title="", xaxis_title="Count", height=350,
                      margin=dict(t=10, l=200), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

# --- Disposition Analysis ---
st.subheader("Patient Disposition by Triage Level")
disp_data = facility_enc.groupby(["triage_level", "disposition"]).size().reset_index(name="count")
fig = px.bar(disp_data, x="triage_level", y="count", color="disposition",
             barmode="group", color_discrete_sequence=px.colors.qualitative.Set2,
             labels={"triage_level": "CTAS Level", "count": "Count"})
fig.update_layout(height=350, margin=dict(t=10))
st.plotly_chart(fig, use_container_width=True)

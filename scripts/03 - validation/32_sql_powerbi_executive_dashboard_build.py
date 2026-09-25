# ================================================================================
# STAGE 2G.19 — POWER BI EXECUTIVE DASHBOARD BUILD PACKAGE
# ================================================================================
#
# Purpose:
#   Build the complete Power BI executive dashboard implementation package
#   from the validated Stage 2G.18 semantic model.
#
# Important:
#   No new economic assumptions are introduced.
#   Stage 2G.10.1 remains the authoritative economic baseline.
#
# ================================================================================

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np


# ================================================================================
# CONFIGURATION
# ================================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.19_PowerBI_Executive_Dashboard"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.19_PowerBI_Executive_Dashboard.xlsx"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ================================================================================
# VALIDATED BASELINE — STAGE 2G.10.1
# ================================================================================

VALIDATED_NPT_EVENTS = 677
VALIDATED_NPT_HOURS = 4008.0

VALIDATED_DIRECT_NPT_COST = 79204408.0
VALIDATED_DEFERRED_COST = 118945770.0
VALIDATED_TOTAL_IMPACT = 198150178.0

VALIDATED_CONSERVATIVE_SAVINGS = 15412920.0
VALIDATED_TARGET_SAVINGS = 30825850.0
VALIDATED_STRETCH_SAVINGS = 46238770.0

TARGET_SAVINGS_RATE = (
    VALIDATED_TARGET_SAVINGS / VALIDATED_TOTAL_IMPACT
)


# ================================================================================
# INITIATIVE MAP
# ================================================================================

INITIATIVE_MAP = {
    "INIT-001": "Drilling Dysfunction Reduction Program",
    "INIT-002": "Mechanical Reliability Program",
    "INIT-003": "Weather & Marine Operations Resilience",
    "INIT-004": "Supply Chain & Logistics Optimization",
    "INIT-005": "People, Competency & Operational Readiness",
    "INIT-006": "Drilling Performance Optimization",
}


# ================================================================================
# LOAD DATABASE
# ================================================================================

print("=" * 95)
print("STAGE 2G.19 — POWER BI EXECUTIVE DASHBOARD BUILD PACKAGE")
print("=" * 95)

print()
print("Project root :", PROJECT_ROOT)
print("Database     :", DB_PATH)
print("Output       :", OUTPUT_FILE)

conn = sqlite3.connect(DB_PATH)

fact_npt = pd.read_sql_query(
    "SELECT * FROM Fact_NPT",
    conn
)

fact_drilling = pd.read_sql_query(
    "SELECT * FROM Fact_Drilling_Daily_Report",
    conn
)

dim_well = pd.read_sql_query(
    "SELECT * FROM Dim_Well",
    conn
)

dim_rig = pd.read_sql_query(
    "SELECT * FROM Dim_Rig",
    conn
)

dim_date = pd.read_sql_query(
    "SELECT * FROM Dim_Date",
    conn
)

conn.close()


print()
print("DATABASE LOADED")
print("-" * 95)
print(f"NPT rows      : {len(fact_npt):,}")
print(f"Drilling rows : {len(fact_drilling):,}")
print(f"Wells         : {len(dim_well):,}")
print(f"Rigs          : {len(dim_rig):,}")
print(f"Dates         : {len(dim_date):,}")


# ================================================================================
# NORMALIZATION
# ================================================================================

fact_npt["Action_Status"] = (
    fact_npt["Action_Status"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
)

fact_npt["Risk_Factor"] = np.select(
    [
        fact_npt["Action_Status"].eq("Open"),
        fact_npt["Action_Status"].eq("In Progress"),
        fact_npt["Action_Status"].eq("Closed"),
    ],
    [
        1.00,
        0.50,
        0.00,
    ],
    default=0.75,
)


# ================================================================================
# TARGET SAVINGS ALLOCATION
# ================================================================================

fact_npt["Target_Savings_USD"] = (
    fact_npt["Total_Impact_USD"]
    * TARGET_SAVINGS_RATE
)

fact_npt["Savings_At_Risk_USD"] = (
    fact_npt["Target_Savings_USD"]
    * fact_npt["Risk_Factor"]
)


# ================================================================================
# INITIATIVE CLASSIFICATION
# ================================================================================

drilling_performance_root_causes = ["Bit Wear"]

conditions = [
    fact_npt["NPT_Category"].eq("Drilling")
    & ~fact_npt["Root_Cause"].isin(
        drilling_performance_root_causes
    ),

    fact_npt["NPT_Category"].eq("Mechanical"),

    fact_npt["NPT_Category"].eq("Weather"),

    fact_npt["NPT_Category"].eq("Logistics"),

    fact_npt["NPT_Category"].eq("Personnel"),

    fact_npt["Root_Cause"].isin(
        drilling_performance_root_causes
    ),
]

choices = [
    "INIT-001",
    "INIT-002",
    "INIT-003",
    "INIT-004",
    "INIT-005",
    "INIT-006",
]

fact_npt["Initiative_ID"] = np.select(
    conditions,
    choices,
    default="INIT-001"
)

fact_npt["Initiative_Name"] = (
    fact_npt["Initiative_ID"].map(INITIATIVE_MAP)
)


# ================================================================================
# CORE CALCULATIONS
# ================================================================================

drilling_days = fact_drilling["Date"].nunique()

total_footage = fact_drilling["Daily_Footage_ft"].sum()

average_rop = fact_drilling["ROP_ft_hr"].mean()

cost_per_foot = (
    fact_drilling["Daily_Cost_USD"].sum()
    / total_footage
)

npt_hours_per_day = (
    VALIDATED_NPT_HOURS / drilling_days
)

savings_at_risk = (
    fact_npt["Savings_At_Risk_USD"].sum()
)

savings_protection_rate = (
    1 - savings_at_risk / VALIDATED_TARGET_SAVINGS
)


# ================================================================================
# POWER BI DAX MEASURE LIBRARY
# ================================================================================

dax_measures = [
    {
        "ID": "M001",
        "Name": "NPT Events",
        "DAX": "COUNTROWS(Fact_NPT)",
        "Format": "#,##0",
    },
    {
        "ID": "M002",
        "Name": "NPT Hours",
        "DAX": "SUM(Fact_NPT[Duration_hr])",
        "Format": "#,##0.0",
    },
    {
        "ID": "M003",
        "Name": "Direct NPT Cost",
        "DAX": "SUM(Fact_NPT[Cost_USD])",
        "Format": "$#,##0",
    },
    {
        "ID": "M004",
        "Name": "Deferred Cost",
        "DAX": "SUM(Fact_NPT[Deferred_Cost_USD])",
        "Format": "$#,##0",
    },
    {
        "ID": "M005",
        "Name": "Total Economic Impact",
        "DAX": "SUM(Fact_NPT[Total_Impact_USD])",
        "Format": "$#,##0",
    },
    {
        "ID": "M006",
        "Name": "Target Savings",
        "DAX": "SUM(Fact_NPT[Target_Savings_USD])",
        "Format": "$#,##0",
    },
    {
        "ID": "M007",
        "Name": "Savings At Risk",
        "DAX": "SUM(Fact_NPT[Savings_At_Risk_USD])",
        "Format": "$#,##0",
    },
    {
        "ID": "M008",
        "Name": "Average ROP",
        "DAX": "AVERAGE(Fact_Drilling_Daily_Report[ROP_ft_hr])",
        "Format": "0.00",
    },
    {
        "ID": "M009",
        "Name": "Total Footage",
        "DAX": "SUM(Fact_Drilling_Daily_Report[Daily_Footage_ft])",
        "Format": "#,##0.0",
    },
    {
        "ID": "M010",
        "Name": "Cost per Foot",
        "DAX": "DIVIDE(SUM(Fact_Drilling_Daily_Report[Daily_Cost_USD]), [Total Footage])",
        "Format": "$#,##0.00",
    },
    {
        "ID": "M011",
        "Name": "NPT Hours per Drilling Day",
        "DAX": "DIVIDE([NPT Hours], DISTINCTCOUNT(Fact_Drilling_Daily_Report[Date]))",
        "Format": "0.00",
    },
    {
        "ID": "M012",
        "Name": "Target Savings Rate",
        "DAX": "DIVIDE([Target Savings], [Total Economic Impact])",
        "Format": "0.00%",
    },
    {
        "ID": "M013",
        "Name": "Savings Protection Rate",
        "DAX": "1 - DIVIDE([Savings At Risk], [Target Savings])",
        "Format": "0.00%",
    },
    {
        "ID": "M014",
        "Name": "Drilling Days",
        "DAX": "DISTINCTCOUNT(Fact_Drilling_Daily_Report[Date])",
        "Format": "#,##0",
    },
    {
        "ID": "M015",
        "Name": "Well Count",
        "DAX": "DISTINCTCOUNT(Dim_Well[Well_ID])",
        "Format": "#,##0",
    },
    {
        "ID": "M016",
        "Name": "Rig Count",
        "DAX": "DISTINCTCOUNT(Dim_Rig[Rig_ID])",
        "Format": "#,##0",
    },
    {
        "ID": "M017",
        "Name": "Target Variance",
        "DAX": "[Target Savings] - [Savings At Risk]",
        "Format": "$#,##0",
    },
    {
        "ID": "M018",
        "Name": "NPT Cost per Hour",
        "DAX": "DIVIDE([Direct NPT Cost], [NPT Hours])",
        "Format": "$#,##0",
    },
    {
        "ID": "M019",
        "Name": "Economic Impact per NPT Hour",
        "DAX": "DIVIDE([Total Economic Impact], [NPT Hours])",
        "Format": "$#,##0",
    },
    {
        "ID": "M020",
        "Name": "Savings Risk %",
        "DAX": "DIVIDE([Savings At Risk], [Target Savings])",
        "Format": "0.00%",
    },
]


# ================================================================================
# KPI STATUS MEASURES
# ================================================================================

kpi_dax = [
    {
        "ID": "KPI-DAX-001",
        "Name": "NPT Hours Status",
        "DAX": """
VAR Actual = [NPT Hours]
VAR Target = 3000
RETURN
SWITCH(
    TRUE(),
    Actual <= Target, "GREEN",
    Actual <= Target * 1.10, "AMBER",
    "RED"
)
""".strip(),
    },
    {
        "ID": "KPI-DAX-002",
        "Name": "Direct Cost Status",
        "DAX": """
VAR Actual = [Direct NPT Cost]
VAR Target = 60000000
RETURN
SWITCH(
    TRUE(),
    Actual <= Target, "GREEN",
    Actual <= Target * 1.10, "AMBER",
    "RED"
)
""".strip(),
    },
    {
        "ID": "KPI-DAX-003",
        "Name": "Economic Impact Status",
        "DAX": """
VAR Actual = [Total Economic Impact]
VAR Target = 150000000
RETURN
SWITCH(
    TRUE(),
    Actual <= Target, "GREEN",
    Actual <= Target * 1.10, "AMBER",
    "RED"
)
""".strip(),
    },
    {
        "ID": "KPI-DAX-004",
        "Name": "ROP Status",
        "DAX": """
VAR Actual = [Average ROP]
VAR Target = 35
RETURN
SWITCH(
    TRUE(),
    Actual >= Target, "GREEN",
    Actual >= Target * 0.90, "AMBER",
    "RED"
)
""".strip(),
    },
    {
        "ID": "KPI-DAX-005",
        "Name": "Cost per Foot Status",
        "DAX": """
VAR Actual = [Cost per Foot]
VAR Target = 600
RETURN
SWITCH(
    TRUE(),
    Actual <= Target, "GREEN",
    Actual <= Target * 1.10, "AMBER",
    "RED"
)
""".strip(),
    },
    {
        "ID": "KPI-DAX-006",
        "Name": "Savings Protection Status",
        "DAX": """
VAR Actual = [Savings At Risk]
VAR Target = 6165170
RETURN
SWITCH(
    TRUE(),
    Actual <= Target, "GREEN",
    Actual <= Target * 1.10, "AMBER",
    "RED"
)
""".strip(),
    },
]


# ================================================================================
# DASHBOARD PAGE DESIGN
# ================================================================================

dashboard_pages = [
    {
        "Page": 1,
        "Name": "Executive Command Center",
        "Navigation": "Home",
        "Audience": "Executive Management",
        "Purpose": "Portfolio-level operational and economic decision support",
        "Slicers": "Date; Rig; Well; Operator; Block",
    },
    {
        "Page": 2,
        "Name": "KPI Performance",
        "Navigation": "KPI",
        "Audience": "Management",
        "Purpose": "Executive KPI monitoring and target variance",
        "Slicers": "Date; Rig; Well",
    },
    {
        "Page": 3,
        "Name": "Rig Performance",
        "Navigation": "Rigs",
        "Audience": "Drilling Management",
        "Purpose": "Rig-level operational and economic comparison",
        "Slicers": "Date; Rig",
    },
    {
        "Page": 4,
        "Name": "Well Risk",
        "Navigation": "Wells",
        "Audience": "Well Engineering",
        "Purpose": "Well-level risk and economic exposure",
        "Slicers": "Date; Well; Rig",
    },
    {
        "Page": 5,
        "Name": "Root Cause Pareto",
        "Navigation": "Root Causes",
        "Audience": "Operations / Engineering",
        "Purpose": "Identify dominant sources of NPT and economic impact",
        "Slicers": "Date; Category; Root Cause",
    },
    {
        "Page": 6,
        "Name": "Initiative Portfolio",
        "Navigation": "Initiatives",
        "Audience": "Management",
        "Purpose": "Track improvement initiatives and savings",
        "Slicers": "Date; Initiative; Action Status",
    },
    {
        "Page": 7,
        "Name": "Savings Protection",
        "Navigation": "Savings",
        "Audience": "Executive Management",
        "Purpose": "Protect the validated savings opportunity",
        "Slicers": "Initiative; Action Status",
    },
    {
        "Page": 8,
        "Name": "Scenario Simulator",
        "Navigation": "Scenarios",
        "Audience": "Management",
        "Purpose": "Evaluate conservative, target and stretch outcomes",
        "Slicers": "Scenario; Rig; Initiative",
    },
    {
        "Page": 9,
        "Name": "Data Quality",
        "Navigation": "DQ",
        "Audience": "Analytics / Management",
        "Purpose": "Validate analytical integrity",
        "Slicers": "None",
    },
]


# ================================================================================
# VISUAL BUILD SPECIFICATION
# ================================================================================

visuals = [
    {
        "Visual_ID": "V001",
        "Page": "Executive Command Center",
        "Position": "Top-left",
        "Type": "Card",
        "Title": "Total Economic Impact",
        "Measure": "Total Economic Impact",
    },
    {
        "Visual_ID": "V002",
        "Page": "Executive Command Center",
        "Position": "Top-center-left",
        "Type": "Card",
        "Title": "Target Savings",
        "Measure": "Target Savings",
    },
    {
        "Visual_ID": "V003",
        "Page": "Executive Command Center",
        "Position": "Top-center-right",
        "Type": "Card",
        "Title": "Savings At Risk",
        "Measure": "Savings At Risk",
    },
    {
        "Visual_ID": "V004",
        "Page": "Executive Command Center",
        "Position": "Top-right",
        "Type": "Card",
        "Title": "Average ROP",
        "Measure": "Average ROP",
    },
    {
        "Visual_ID": "V005",
        "Page": "Executive Command Center",
        "Position": "Middle-left",
        "Type": "Bar Chart",
        "Title": "Economic Impact by Rig",
        "Axis": "Rig_ID",
        "Measure": "Total Economic Impact",
    },
    {
        "Visual_ID": "V006",
        "Page": "Executive Command Center",
        "Position": "Middle-right",
        "Type": "Bar Chart",
        "Title": "Economic Impact by Root Cause",
        "Axis": "Root_Cause",
        "Measure": "Total Economic Impact",
    },
    {
        "Visual_ID": "V007",
        "Page": "KPI Performance",
        "Position": "Main",
        "Type": "Matrix",
        "Title": "KPI Status Matrix",
        "Rows": "KPI",
        "Measures": "Actual; Target; Variance; Status",
    },
    {
        "Visual_ID": "V008",
        "Page": "Rig Performance",
        "Position": "Main",
        "Type": "Matrix",
        "Title": "Rig Performance Scorecard",
        "Rows": "Rig_ID",
        "Measures": "NPT Events; NPT Hours; Economic Impact; ROP; Cost per Foot",
    },
    {
        "Visual_ID": "V009",
        "Page": "Well Risk",
        "Position": "Main",
        "Type": "Bar Chart",
        "Title": "Top Wells by Economic Impact",
        "Axis": "Well_ID",
        "Measure": "Total Economic Impact",
    },
    {
        "Visual_ID": "V010",
        "Page": "Root Cause Pareto",
        "Position": "Main",
        "Type": "Pareto",
        "Title": "NPT Root Cause Pareto",
        "Axis": "Root_Cause",
        "Measure": "Total Economic Impact",
    },
    {
        "Visual_ID": "V011",
        "Page": "Initiative Portfolio",
        "Position": "Main",
        "Type": "Matrix",
        "Title": "Initiative Performance",
        "Rows": "Initiative_Name",
        "Measures": "NPT Events; NPT Hours; Target Savings; Savings At Risk",
    },
    {
        "Visual_ID": "V012",
        "Page": "Savings Protection",
        "Position": "Main",
        "Type": "Waterfall",
        "Title": "Savings Protection",
        "Axis": "Initiative_Name",
        "Measure": "Target Savings; Savings At Risk",
    },
    {
        "Visual_ID": "V013",
        "Page": "Scenario Simulator",
        "Position": "Main",
        "Type": "Line Chart",
        "Title": "Scenario Savings Curve",
        "Axis": "Scenario",
        "Measure": "Scenario Savings",
    },
    {
        "Visual_ID": "V014",
        "Page": "Data Quality",
        "Position": "Main",
        "Type": "Table",
        "Title": "Data Quality Validation",
        "Rows": "Check; Actual; Expected; Status",
    },
]


# ================================================================================
# NAVIGATION
# ================================================================================

navigation = pd.DataFrame([
    {"Order": 1, "Page": "Executive Command Center", "Button": "HOME"},
    {"Order": 2, "Page": "KPI Performance", "Button": "KPI"},
    {"Order": 3, "Page": "Rig Performance", "Button": "RIGS"},
    {"Order": 4, "Page": "Well Risk", "Button": "WELLS"},
    {"Order": 5, "Page": "Root Cause Pareto", "Button": "ROOT CAUSES"},
    {"Order": 6, "Page": "Initiative Portfolio", "Button": "INITIATIVES"},
    {"Order": 7, "Page": "Savings Protection", "Button": "SAVINGS"},
    {"Order": 8, "Page": "Scenario Simulator", "Button": "SCENARIOS"},
    {"Order": 9, "Page": "Data Quality", "Button": "DATA QUALITY"},
])


# ================================================================================
# DRILL-THROUGH
# ================================================================================

drillthrough = pd.DataFrame([
    {
        "ID": "DT001",
        "Source": "Executive Command Center",
        "Target": "Rig Performance",
        "Field": "Rig_ID",
    },
    {
        "ID": "DT002",
        "Source": "Executive Command Center",
        "Target": "Well Risk",
        "Field": "Well_ID",
    },
    {
        "ID": "DT003",
        "Source": "Root Cause Pareto",
        "Target": "Initiative Portfolio",
        "Field": "Initiative_ID",
    },
    {
        "ID": "DT004",
        "Source": "Initiative Portfolio",
        "Target": "Savings Protection",
        "Field": "Initiative_ID",
    },
    {
        "ID": "DT005",
        "Source": "KPI Performance",
        "Target": "Root Cause Pareto",
        "Field": "Root_Cause",
    },
    {
        "ID": "DT006",
        "Source": "Rig Performance",
        "Target": "Well Risk",
        "Field": "Rig_ID + Well_ID",
    },
])


# ================================================================================
# CONDITIONAL FORMATTING
# ================================================================================

conditional_formatting = pd.DataFrame([
    {
        "Object": "KPI Status",
        "Green": "Status = GREEN",
        "Amber": "Status = AMBER",
        "Red": "Status = RED",
    },
    {
        "Object": "Savings At Risk",
        "Green": "<= $6.165M",
        "Amber": "$6.165M–$6.782M",
        "Red": "> $6.782M",
    },
    {
        "Object": "ROP",
        "Green": ">= 35 ft/hr",
        "Amber": "31.5–34.99 ft/hr",
        "Red": "< 31.5 ft/hr",
    },
    {
        "Object": "Cost per Foot",
        "Green": "<= $600",
        "Amber": "$600–$660",
        "Red": "> $660",
    },
])


# ================================================================================
# SCENARIO MODEL
# ================================================================================

scenario_model = pd.DataFrame([
    {
        "Scenario": "BASELINE",
        "NPT_Reduction": 0.00,
        "NPT_Hours_Reduced": 0.0,
        "NPT_Hours_Remaining": VALIDATED_NPT_HOURS,
        "Savings": 0.0,
    },
    {
        "Scenario": "CONSERVATIVE",
        "NPT_Reduction": 0.20,
        "NPT_Hours_Reduced": VALIDATED_NPT_HOURS * 0.20,
        "NPT_Hours_Remaining": VALIDATED_NPT_HOURS * 0.80,
        "Savings": VALIDATED_CONSERVATIVE_SAVINGS,
    },
    {
        "Scenario": "TARGET",
        "NPT_Reduction": 0.40,
        "NPT_Hours_Reduced": VALIDATED_NPT_HOURS * 0.40,
        "NPT_Hours_Remaining": VALIDATED_NPT_HOURS * 0.60,
        "Savings": VALIDATED_TARGET_SAVINGS,
    },
    {
        "Scenario": "STRETCH",
        "NPT_Reduction": 0.60,
        "NPT_Hours_Reduced": VALIDATED_NPT_HOURS * 0.60,
        "NPT_Hours_Remaining": VALIDATED_NPT_HOURS * 0.40,
        "Savings": VALIDATED_STRETCH_SAVINGS,
    },
])


# ================================================================================
# DATA QUALITY
# ================================================================================

dq = []

dq.append({
    "Check": "NPT row count",
    "Actual": len(fact_npt),
    "Expected": 677,
    "Status": "PASS" if len(fact_npt) == 677 else "FAIL",
})

dq.append({
    "Check": "Drilling row count",
    "Actual": len(fact_drilling),
    "Expected": 1474,
    "Status": "PASS" if len(fact_drilling) == 1474 else "FAIL",
})

dq.append({
    "Check": "Unique NPT IDs",
    "Actual": fact_npt["NPT_ID"].nunique(),
    "Expected": 677,
    "Status": (
        "PASS"
        if fact_npt["NPT_ID"].nunique() == 677
        else "FAIL"
    ),
})

dq.append({
    "Check": "Duplicate NPT IDs",
    "Actual": int(fact_npt["NPT_ID"].duplicated().sum()),
    "Expected": 0,
    "Status": (
        "PASS"
        if fact_npt["NPT_ID"].duplicated().sum() == 0
        else "FAIL"
    ),
})

actual_direct = fact_npt["Cost_USD"].sum()
actual_deferred = fact_npt["Deferred_Cost_USD"].sum()
actual_total = fact_npt["Total_Impact_USD"].sum()

economic_reconciliation = (
    abs(actual_direct - VALIDATED_DIRECT_NPT_COST)
    + abs(actual_deferred - VALIDATED_DEFERRED_COST)
    + abs(actual_total - VALIDATED_TOTAL_IMPACT)
)

dq.append({
    "Check": "Economic reconciliation",
    "Actual": economic_reconciliation,
    "Expected": 0,
    "Status": (
        "PASS"
        if economic_reconciliation < 0.01
        else "FAIL"
    ),
})

target_reconciliation = (
    fact_npt["Target_Savings_USD"].sum()
    - VALIDATED_TARGET_SAVINGS
)

dq.append({
    "Check": "Target savings reconciliation",
    "Actual": target_reconciliation,
    "Expected": 0,
    "Status": (
        "PASS"
        if abs(target_reconciliation) < 0.01
        else "FAIL"
    ),
})

dq.append({
    "Check": "Rig count",
    "Actual": dim_rig["Rig_ID"].nunique(),
    "Expected": 4,
    "Status": (
        "PASS"
        if dim_rig["Rig_ID"].nunique() == 4
        else "FAIL"
    ),
})

dq.append({
    "Check": "Well count",
    "Actual": dim_well["Well_ID"].nunique(),
    "Expected": 50,
    "Status": (
        "PASS"
        if dim_well["Well_ID"].nunique() == 50
        else "FAIL"
    ),
})

dq.append({
    "Check": "Initiative count",
    "Actual": fact_npt["Initiative_ID"].nunique(),
    "Expected": 6,
    "Status": (
        "PASS"
        if fact_npt["Initiative_ID"].nunique() == 6
        else "FAIL"
    ),
})

dq.append({
    "Check": "DAX measure count",
    "Actual": len(dax_measures),
    "Expected": 20,
    "Status": "PASS" if len(dax_measures) == 20 else "FAIL",
})

dq.append({
    "Check": "Dashboard page count",
    "Actual": len(dashboard_pages),
    "Expected": 9,
    "Status": "PASS" if len(dashboard_pages) == 9 else "FAIL",
})

dq.append({
    "Check": "Visual specification count",
    "Actual": len(visuals),
    "Expected": 14,
    "Status": "PASS" if len(visuals) == 14 else "FAIL",
})

dq.append({
    "Check": "Drill-through count",
    "Actual": len(drillthrough),
    "Expected": 6,
    "Status": "PASS" if len(drillthrough) == 6 else "FAIL",
})

dq.append({
    "Check": "Navigation count",
    "Actual": len(navigation),
    "Expected": 9,
    "Status": "PASS" if len(navigation) == 9 else "FAIL",
})

dq.append({
    "Check": "Scenario count",
    "Actual": len(scenario_model),
    "Expected": 4,
    "Status": "PASS" if len(scenario_model) == 4 else "FAIL",
})


# ================================================================================
# SEMANTIC CONSISTENCY
# ================================================================================

m010 = dax_measures[9]["DAX"]

dq.append({
    "Check": "Cost per Foot semantic consistency",
    "Actual": m010,
    "Expected": "Daily_Cost_USD / Total Footage",
    "Status": (
        "PASS"
        if (
            "Daily_Cost_USD" in m010
            and "[Total Footage]" in m010
        )
        else "FAIL"
    ),
})


overall_status = (
    "PASS"
    if all(row["Status"] == "PASS" for row in dq)
    else "FAIL"
)

dq.append({
    "Check": "Overall Data Quality",
    "Actual": overall_status,
    "Expected": "PASS",
    "Status": overall_status,
})

data_quality = pd.DataFrame(dq)


# ================================================================================
# EXECUTIVE SUMMARY
# ================================================================================

executive_summary = pd.DataFrame([
    {
        "Metric": "NPT Events",
        "Value": VALIDATED_NPT_EVENTS,
    },
    {
        "Metric": "NPT Hours",
        "Value": VALIDATED_NPT_HOURS,
    },
    {
        "Metric": "Direct NPT Cost",
        "Value": VALIDATED_DIRECT_NPT_COST,
    },
    {
        "Metric": "Deferred Cost",
        "Value": VALIDATED_DEFERRED_COST,
    },
    {
        "Metric": "Total Economic Impact",
        "Value": VALIDATED_TOTAL_IMPACT,
    },
    {
        "Metric": "Target Savings",
        "Value": VALIDATED_TARGET_SAVINGS,
    },
    {
        "Metric": "Savings At Risk",
        "Value": savings_at_risk,
    },
    {
        "Metric": "Savings Protection Rate",
        "Value": savings_protection_rate,
    },
    {
        "Metric": "Drilling Days",
        "Value": drilling_days,
    },
    {
        "Metric": "Total Footage",
        "Value": total_footage,
    },
    {
        "Metric": "Average ROP",
        "Value": average_rop,
    },
    {
        "Metric": "Cost per Foot",
        "Value": cost_per_foot,
    },
    {
        "Metric": "NPT Hours per Drilling Day",
        "Value": npt_hours_per_day,
    },
])


# ================================================================================
# BUILD INSTRUCTIONS
# ================================================================================

build_instructions = pd.DataFrame([
    {
        "Step": 1,
        "Action": "Import Dim_Date, Dim_Well, Dim_Rig, Fact_Drilling_Daily_Report and Fact_NPT",
        "Validation": "All five tables loaded",
    },
    {
        "Step": 2,
        "Action": "Create six active 1:* single-direction relationships",
        "Validation": "No many-to-many relationships",
    },
    {
        "Step": 3,
        "Action": "Mark Dim_Date as the official Date table",
        "Validation": "Date column recognized as Date",
    },
    {
        "Step": 4,
        "Action": "Create the 20 core DAX measures",
        "Validation": "All measures calculate without errors",
    },
    {
        "Step": 5,
        "Action": "Create KPI status measures",
        "Validation": "GREEN / AMBER / RED returned",
    },
    {
        "Step": 6,
        "Action": "Build nine dashboard pages",
        "Validation": "Navigation works",
    },
    {
        "Step": 7,
        "Action": "Add slicers and synchronization",
        "Validation": "Filters propagate correctly",
    },
    {
        "Step": 8,
        "Action": "Configure drill-through",
        "Validation": "Context is retained",
    },
    {
        "Step": 9,
        "Action": "Configure conditional formatting",
        "Validation": "RAG status visible",
    },
    {
        "Step": 10,
        "Action": "Validate executive baseline",
        "Validation": "Matches Stage 2G.10.1",
    },
])


# ================================================================================
# EXPORT
# ================================================================================

print()
print("EXPORTING POWER BI EXECUTIVE DASHBOARD BUILD PACKAGE...")
print("-" * 95)

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    executive_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    pd.DataFrame(dax_measures).to_excel(
        writer,
        sheet_name="DAX_Measures",
        index=False
    )

    pd.DataFrame(kpi_dax).to_excel(
        writer,
        sheet_name="KPI_DAX",
        index=False
    )

    pd.DataFrame(dashboard_pages).to_excel(
        writer,
        sheet_name="Dashboard_Pages",
        index=False
    )

    pd.DataFrame(visuals).to_excel(
        writer,
        sheet_name="Visual_Specification",
        index=False
    )

    navigation.to_excel(
        writer,
        sheet_name="Navigation",
        index=False
    )

    drillthrough.to_excel(
        writer,
        sheet_name="Drillthrough",
        index=False
    )

    conditional_formatting.to_excel(
        writer,
        sheet_name="Conditional_Formatting",
        index=False
    )

    scenario_model.to_excel(
        writer,
        sheet_name="Scenario_Model",
        index=False
    )

    build_instructions.to_excel(
        writer,
        sheet_name="Build_Instructions",
        index=False
    )

    data_quality.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# ================================================================================
# FINAL OUTPUT
# ================================================================================

print()
print("=" * 95)
print("STAGE 2G.19 — POWER BI EXECUTIVE DASHBOARD RESULTS")
print("=" * 95)

print()
print(f"Data Quality Status           : {overall_status}")

print()
print("--- EXECUTIVE BASELINE ---")
print(f"NPT Events                    : {VALIDATED_NPT_EVENTS:,}")
print(f"NPT Hours                     : {VALIDATED_NPT_HOURS:,.0f}")
print(f"Direct NPT Cost               : ${VALIDATED_DIRECT_NPT_COST:,.0f}")
print(f"Deferred Cost                 : ${VALIDATED_DEFERRED_COST:,.0f}")
print(f"Total Economic Impact         : ${VALIDATED_TOTAL_IMPACT:,.0f}")
print(f"Target Savings                : ${VALIDATED_TARGET_SAVINGS:,.0f}")
print(f"Savings At Risk               : ${savings_at_risk:,.0f}")
print(f"Savings Protection Rate       : {savings_protection_rate:.2%}")

print()
print("--- POWER BI BUILD ARCHITECTURE ---")
print(f"DAX Measures                  : {len(dax_measures)}")
print(f"KPI Status Measures           : {len(kpi_dax)}")
print(f"Dashboard Pages               : {len(dashboard_pages)}")
print(f"Visual Specifications         : {len(visuals)}")
print(f"Navigation Items              : {len(navigation)}")
print(f"Drill-through Paths           : {len(drillthrough)}")
print(f"Scenario Cases                : {len(scenario_model)}")

print()
print("--- OPERATIONAL BASELINE ---")
print(f"Drilling Days                 : {drilling_days:,}")
print(f"Total Footage                : {total_footage:,.1f} ft")
print(f"Average ROP                  : {average_rop:.2f} ft/hr")
print(f"Cost per Foot                : ${cost_per_foot:,.2f}")
print(f"NPT Hours / Drilling Day     : {npt_hours_per_day:.2f}")

print()
print("--- DATA QUALITY ---")
print(
    data_quality[
        ["Check", "Actual", "Expected", "Status"]
    ].to_string(index=False)
)

print()
print("=" * 95)

if overall_status == "PASS":
    print("OUTPUT GENERATED SUCCESSFULLY")
else:
    print("OUTPUT GENERATED WITH DATA QUALITY FAILURE")

print("=" * 95)

print()
print("Excel file:")
print(OUTPUT_FILE)
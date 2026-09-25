import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from openpyxl import load_workbook

# =============================================================================
# STAGE 2G.20.1
# POWER BI DATA & SEMANTIC REMEDIATION
# =============================================================================

PROJECT_ROOT = r"C:\Users\aniba\Documents\Guyana_Offshore_Drilling_Analytics"

DB_PATH = os.path.join(
    PROJECT_ROOT,
    "database",
    "guyana_drilling.db"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "outputs",
    "sql_stage_2G.20.1_PowerBI_Data_Semantic_Remediation"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "sql_stage_2G.20.1_PowerBI_Data_Semantic_Remediation.xlsx"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =============================================================================
# VALIDATED ECONOMIC BASELINE
# =============================================================================

EXPECTED = {
    "npt_rows": 677,
    "npt_hours": 4008.0,
    "direct_cost": 79204408.0,
    "deferred_cost": 118945770.0,
    "total_impact": 198150178.0,
    "target_savings": 30825850.0,
    "savings_at_risk": 6390129.0,
    "wells": 50,
    "rigs": 4,
}

TARGET_SAVINGS_RATE = (
    EXPECTED["target_savings"]
    / EXPECTED["total_impact"]
)

# =============================================================================
# RESULTS
# =============================================================================

qa_results = []
findings = []


def add_qa(test_id, area, test, expected, actual, status, severity="INFO"):
    qa_results.append({
        "Test_ID": test_id,
        "Area": area,
        "Test": test,
        "Expected": expected,
        "Actual": actual,
        "Status": status,
        "Severity": severity
    })


def add_finding(fid, area, severity, finding, action):
    findings.append({
        "Finding_ID": fid,
        "Area": area,
        "Severity": severity,
        "Finding": finding,
        "Required_Action": action
    })


# =============================================================================
# LOAD SOURCE DATABASE
# =============================================================================

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(
        f"SQLite database not found:\n{DB_PATH}"
    )

con = sqlite3.connect(DB_PATH)

dim_date = pd.read_sql_query(
    "SELECT * FROM Dim_Date",
    con
)

dim_rig = pd.read_sql_query(
    "SELECT * FROM Dim_Rig",
    con
)

dim_well = pd.read_sql_query(
    "SELECT * FROM Dim_Well",
    con
)

fact_drilling = pd.read_sql_query(
    "SELECT * FROM Fact_Drilling_Daily_Report",
    con
)

fact_npt = pd.read_sql_query(
    "SELECT * FROM Fact_NPT",
    con
)

con.close()

# =============================================================================
# 1. SOURCE VALIDATION
# =============================================================================

add_qa(
    "REM-001",
    "Source",
    "Fact_NPT row count",
    EXPECTED["npt_rows"],
    len(fact_npt),
    "PASS" if len(fact_npt) == EXPECTED["npt_rows"] else "FAIL",
    "CRITICAL" if len(fact_npt) != EXPECTED["npt_rows"] else "INFO"
)

add_qa(
    "REM-002",
    "Source",
    "Fact_NPT unique NPT_ID",
    EXPECTED["npt_rows"],
    fact_npt["NPT_ID"].nunique(),
    "PASS"
    if fact_npt["NPT_ID"].nunique() == EXPECTED["npt_rows"]
    else "FAIL",
    "CRITICAL"
)

add_qa(
    "REM-003",
    "Source",
    "Dim_Well count",
    EXPECTED["wells"],
    len(dim_well),
    "PASS" if len(dim_well) == EXPECTED["wells"] else "FAIL",
    "CRITICAL"
)

add_qa(
    "REM-004",
    "Source",
    "Dim_Rig count",
    EXPECTED["rigs"],
    len(dim_rig),
    "PASS" if len(dim_rig) == EXPECTED["rigs"] else "FAIL",
    "CRITICAL"
)

# =============================================================================
# 2. ECONOMIC BASELINE RECONCILIATION
# =============================================================================

source_npt_hours = fact_npt["Duration_hr"].sum()
source_direct_cost = fact_npt["Cost_USD"].sum()
source_deferred_cost = fact_npt["Deferred_Cost_USD"].sum()
source_total_impact = fact_npt["Total_Impact_USD"].sum()

economic_checks = [
    (
        "REM-010",
        "NPT Hours",
        EXPECTED["npt_hours"],
        source_npt_hours
    ),
    (
        "REM-011",
        "Direct NPT Cost",
        EXPECTED["direct_cost"],
        source_direct_cost
    ),
    (
        "REM-012",
        "Deferred Cost",
        EXPECTED["deferred_cost"],
        source_deferred_cost
    ),
    (
        "REM-013",
        "Total Economic Impact",
        EXPECTED["total_impact"],
        source_total_impact
    )
]

for tid, label, expected, actual in economic_checks:

    difference = abs(float(expected) - float(actual))

    status = "PASS" if difference < 0.01 else "FAIL"

    add_qa(
        tid,
        "Economic Baseline",
        label,
        expected,
        round(float(actual), 2),
        status,
        "CRITICAL" if status == "FAIL" else "INFO"
    )

# =============================================================================
# 3. CREATE POWER BI READY FACT
# =============================================================================

fact_npt_pbi = fact_npt.copy()

# -------------------------------------------------------------------------
# Target Savings
# -------------------------------------------------------------------------

fact_npt_pbi["Target_Savings_USD"] = (
    fact_npt_pbi["Total_Impact_USD"]
    * TARGET_SAVINGS_RATE
)

# -------------------------------------------------------------------------
# Initiative classification
# -------------------------------------------------------------------------

def classify_initiative(row):

    category = str(
        row.get("NPT_Category", "")
    ).strip().casefold()

    root_cause = str(
        row.get("Root_Cause", "")
    ).strip().casefold()

    if category == "mechanical":
        return (
            "INIT-002",
            "Mechanical Reliability Program"
        )

    if category == "weather":
        return (
            "INIT-003",
            "Weather & Marine Operations Resilience"
        )

    if category == "logistics":
        return (
            "INIT-004",
            "Supply Chain & Logistics Optimization"
        )

    if category == "personnel":
        return (
            "INIT-005",
            "People, Competency & Operational Readiness"
        )

    if category == "drilling":

        # Bit Wear is classified through Root_Cause,
        # not NPT_Subcategory, in the source Fact_NPT.
        if "bit wear" in root_cause:
            return (
                "INIT-006",
                "Drilling Performance Optimization"
            )

        return (
            "INIT-001",
            "Drilling Dysfunction Reduction Program"
        )

    return (
        "UNASSIGNED",
        "Unassigned"
    )

# =============================================================================
# 4. ACTION STATUS NORMALIZATION
# =============================================================================

if "Action_Status" in fact_npt_pbi.columns:

    fact_npt_pbi["Action_Status_Normalized"] = (
        fact_npt_pbi["Action_Status"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .str.title()
    )

else:

    fact_npt_pbi["Action_Status_Normalized"] = "Unknown"

# =============================================================================
# 5. RISK FACTOR
# =============================================================================

RISK_MAP = {
    "Open": 1.00,
    "In Progress": 0.50,
    "Closed": 0.00,
    "Completed": 0.00
}

fact_npt_pbi["Risk_Factor"] = (
    fact_npt_pbi["Action_Status_Normalized"]
    .map(RISK_MAP)
    .fillna(0.25)
)

# =============================================================================
# 6. SAVINGS AT RISK
# =============================================================================

fact_npt_pbi["Savings_At_Risk_USD"] = (
    fact_npt_pbi["Target_Savings_USD"]
    * fact_npt_pbi["Risk_Factor"]
)

# =============================================================================
# 7. VALIDATE ENRICHED FACT
# =============================================================================

# =============================================================================
# 8. TARGET SAVINGS RECONCILIATION
# =============================================================================

derived_target_savings = (
    fact_npt_pbi["Target_Savings_USD"].sum()
)

target_difference = abs(
    derived_target_savings
    - EXPECTED["target_savings"]
)

add_qa(
    "REM-030",
    "Savings Reconciliation",
    "Target Savings",
    EXPECTED["target_savings"],
    round(derived_target_savings, 2),
    "PASS" if target_difference < 0.01 else "FAIL",
    "CRITICAL" if target_difference >= 0.01 else "INFO"
)

# =============================================================================
# 9. SAVINGS AT RISK RECONCILIATION
# =============================================================================

derived_savings_risk = (
    fact_npt_pbi["Savings_At_Risk_USD"].sum()
)

risk_difference = abs(
    derived_savings_risk
    - EXPECTED["savings_at_risk"]
)

add_qa(
    "REM-031",
    "Savings Reconciliation",
    "Savings At Risk",
    EXPECTED["savings_at_risk"],
    round(derived_savings_risk, 2),
    "PASS" if risk_difference < 1.0 else "WARN",
    "HIGH" if risk_difference >= 1.0 else "INFO"
)

# =============================================================================
# 10. INITIATIVE VALIDATION
# =============================================================================
# ============================================================
# INITIATIVE CLASSIFICATION
# ============================================================

initiative_results = fact_npt_pbi.apply(
    classify_initiative,
    axis=1
)

fact_npt_pbi["Initiative_ID"] = initiative_results.apply(
    lambda x: x[0]
)

fact_npt_pbi["Initiative_Name"] = initiative_results.apply(
    lambda x: x[1]
)

# =============================================================================
# 10A. VALIDATE ENRICHED FACT AFTER INITIATIVE CLASSIFICATION
# =============================================================================

required_pbi_columns = [
    "Target_Savings_USD",
    "Savings_At_Risk_USD",
    "Initiative_ID",
    "Initiative_Name",
    "Risk_Factor",
    "Action_Status_Normalized"
]

for column in required_pbi_columns:

    status = (
        "PASS"
        if column in fact_npt_pbi.columns
        else "FAIL"
    )

    add_qa(
        "REM-020",
        "Power BI Fact",
        f"Required enriched column: {column}",
        "PRESENT",
        "PRESENT" if status == "PASS" else "MISSING",
        status,
        "CRITICAL" if status == "FAIL" else "INFO"
    )



initiative_summary = (
    fact_npt_pbi
    .groupby(
        ["Initiative_ID", "Initiative_Name"],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Savings_At_Risk_USD=("Savings_At_Risk_USD", "sum")
    )
)

initiative_count = len(initiative_summary)

add_qa(
    "REM-040",
    "Initiative Model",
    "Initiative count",
    6,
    initiative_count,
    "PASS" if initiative_count == 6 else "FAIL",
    "CRITICAL" if initiative_count != 6 else "INFO"
)

unassigned_events = int(
    fact_npt_pbi["Initiative_ID"]
    .eq("UNASSIGNED")
    .sum()
)

add_qa(
    "REM-041",
    "Initiative Model",
    "Unassigned NPT events",
    0,
    unassigned_events,
    "PASS" if unassigned_events == 0 else "FAIL",
    "CRITICAL" if unassigned_events else "INFO"
)

# =============================================================================
# 11. CREATE DIM_SCENARIO
# =============================================================================

dim_scenario = pd.DataFrame([
    {
        "Scenario_ID": "SCN-001",
        "Scenario_Name": "Baseline",
        "NPT_Reduction_pct": 0.00,
        "Savings_Level": "Baseline"
    },
    {
        "Scenario_ID": "SCN-002",
        "Scenario_Name": "Conservative",
        "NPT_Reduction_pct": 0.20,
        "Savings_Level": "Conservative"
    },
    {
        "Scenario_ID": "SCN-003",
        "Scenario_Name": "Target",
        "NPT_Reduction_pct": 0.40,
        "Savings_Level": "Target"
    },
    {
        "Scenario_ID": "SCN-004",
        "Scenario_Name": "Stretch",
        "NPT_Reduction_pct": 0.60,
        "Savings_Level": "Stretch"
    }
])

add_qa(
    "REM-050",
    "Scenario Model",
    "Scenario count",
    4,
    len(dim_scenario),
    "PASS" if len(dim_scenario) == 4 else "FAIL",
    "CRITICAL"
)

# =============================================================================
# 12. CREATE DIM_KPI
# =============================================================================

dim_kpi = pd.DataFrame([
    {
        "KPI_ID": "KPI-001",
        "KPI_Name": "NPT Events",
        "Measure_Name": "NPT Events",
        "Direction": "Lower is Better",
        "Unit": "Events"
    },
    {
        "KPI_ID": "KPI-002",
        "KPI_Name": "NPT Hours",
        "Measure_Name": "NPT Hours",
        "Direction": "Lower is Better",
        "Unit": "Hours"
    },
    {
        "KPI_ID": "KPI-003",
        "KPI_Name": "Total Economic Impact",
        "Measure_Name": "Total Economic Impact",
        "Direction": "Lower is Better",
        "Unit": "USD"
    },
    {
        "KPI_ID": "KPI-004",
        "KPI_Name": "Target Savings",
        "Measure_Name": "Target Savings",
        "Direction": "Higher is Better",
        "Unit": "USD"
    },
    {
        "KPI_ID": "KPI-005",
        "KPI_Name": "Savings At Risk",
        "Measure_Name": "Savings At Risk",
        "Direction": "Lower is Better",
        "Unit": "USD"
    },
    {
        "KPI_ID": "KPI-006",
        "KPI_Name": "Savings Protection Rate",
        "Measure_Name": "Savings Protection Rate",
        "Direction": "Higher is Better",
        "Unit": "%"
    },
    {
        "KPI_ID": "KPI-007",
        "KPI_Name": "Average ROP",
        "Measure_Name": "Average ROP",
        "Direction": "Higher is Better",
        "Unit": "ft/hr"
    },
    {
        "KPI_ID": "KPI-008",
        "KPI_Name": "Cost per Foot",
        "Measure_Name": "Cost per Foot",
        "Direction": "Lower is Better",
        "Unit": "USD/ft"
    },
    {
        "KPI_ID": "KPI-009",
        "KPI_Name": "NPT Hours per Portfolio Drilling Day",
        "Measure_Name": "NPT Hours per Drilling Day",
        "Direction": "Lower is Better",
        "Unit": "Hours/Day"
    }
])

add_qa(
    "REM-060",
    "KPI Model",
    "KPI definition count",
    9,
    len(dim_kpi),
    "PASS" if len(dim_kpi) == 9 else "FAIL",
    "CRITICAL"
)

add_qa(
    "REM-061",
    "KPI Model",
    "KPI IDs unique",
    9,
    dim_kpi["KPI_ID"].nunique(),
    "PASS"
    if dim_kpi["KPI_ID"].nunique() == 9
    else "FAIL",
    "CRITICAL"
)

# =============================================================================
# 13. DAX-READY MEASURE DEFINITIONS
# =============================================================================

dax_measures = pd.DataFrame([
    ["M001", "NPT Events", "COUNTROWS(Fact_NPT_PBI)"],
    ["M002", "NPT Hours", "SUM(Fact_NPT_PBI[Duration_hr])"],
    ["M003", "Direct NPT Cost", "SUM(Fact_NPT_PBI[Cost_USD])"],
    ["M004", "Deferred Cost", "SUM(Fact_NPT_PBI[Deferred_Cost_USD])"],
    ["M005", "Total Economic Impact", "[Direct NPT Cost] + [Deferred Cost]"],
    ["M006", "Target Savings", "SUM(Fact_NPT_PBI[Target_Savings_USD])"],
    ["M007", "Savings At Risk", "SUM(Fact_NPT_PBI[Savings_At_Risk_USD])"],
    ["M008", "Average ROP", "AVERAGE(Fact_Drilling_Daily_Report[ROP_ft_hr])"],
    ["M009", "Total Footage", "SUM(Fact_Drilling_Daily_Report[Daily_Footage_ft])"],
    ["M010", "Cost per Foot", "DIVIDE(SUM(Fact_Drilling_Daily_Report[Daily_Cost_USD]), [Total Footage])"],
    ["M011", "NPT Hours per Drilling Day", "DIVIDE([NPT Hours], DISTINCTCOUNT(Fact_Drilling_Daily_Report[Date]))"],
    ["M012", "Target Savings Rate", "DIVIDE([Target Savings], [Total Economic Impact])"],
    ["M013", "Savings Protection Rate", "1 - DIVIDE([Savings At Risk], [Target Savings])"],
    ["M014", "Drilling Days", "DISTINCTCOUNT(Fact_Drilling_Daily_Report[Date])"],
    ["M015", "Well Count", "DISTINCTCOUNT(Dim_Well[Well_ID])"],
    ["M016", "Rig Count", "DISTINCTCOUNT(Dim_Rig[Rig_ID])"],
    ["M017", "Protected Savings", "[Target Savings] - [Savings At Risk]"],
    ["M018", "NPT Cost per Hour", "DIVIDE([Direct NPT Cost], [NPT Hours])"],
    ["M019", "Economic Impact per NPT Hour", "DIVIDE([Total Economic Impact], [NPT Hours])"],
    ["M020", "Savings Risk %", "DIVIDE([Savings At Risk], [Target Savings])"]
], columns=[
    "Measure_ID",
    "Measure_Name",
    "DAX"
])

add_qa(
    "REM-070",
    "DAX Model",
    "DAX measure count",
    20,
    len(dax_measures),
    "PASS" if len(dax_measures) == 20 else "FAIL",
    "CRITICAL"
)

# =============================================================================
# 14. RAG RULES
# =============================================================================

rag_rules = pd.DataFrame([
    ["RAG-001", "NPT Hours per Portfolio Drilling Day",
     "<= 4.0", "GREEN",
     "> 4.0 and <= 6.0", "AMBER",
     "> 6.0", "RED"],

    ["RAG-002", "Savings Protection Rate",
     ">= 90%", "GREEN",
     ">= 75% and < 90%", "AMBER",
     "< 75%", "RED"],

    ["RAG-003", "Cost per Foot",
     "<= 600", "GREEN",
     "> 600 and <= 750", "AMBER",
     "> 750", "RED"]
], columns=[
    "Rule_ID",
    "KPI",
    "Green_Threshold",
    "Green_Status",
    "Amber_Threshold",
    "Amber_Status",
    "Red_Threshold",
    "Red_Status"
])

# =============================================================================
# 15. SEMANTIC MODEL TABLE CATALOG
# =============================================================================

table_catalog = pd.DataFrame([
    ["Dim_Date", "Dimension", "Date", "Active relationship to both facts"],
    ["Dim_Well", "Dimension", "Well_ID", "Active relationship to both facts"],
    ["Dim_Rig", "Dimension", "Rig_ID", "Active relationship to both facts"],
    ["Fact_Drilling_Daily_Report", "Fact", "Date + Well_ID + Rig_ID", "Operational drilling fact"],
    ["Fact_NPT_PBI", "Fact", "NPT_ID", "Power BI-ready NPT fact"],
    ["Dim_Scenario", "Disconnected", "Scenario_ID", "Scenario selector"],
    ["Dim_KPI", "Disconnected", "KPI_ID", "KPI framework / selector"],
], columns=[
    "Table_Name",
    "Table_Type",
    "Key",
    "Purpose"
])

# =============================================================================
# 16. RELATIONSHIPS
# =============================================================================

relationships = pd.DataFrame([
    ["Dim_Date", "Date", "Fact_Drilling_Daily_Report", "Date", "1:*", "Active", "Single"],
    ["Dim_Date", "Date", "Fact_NPT_PBI", "Date", "1:*", "Active", "Single"],
    ["Dim_Well", "Well_ID", "Fact_Drilling_Daily_Report", "Well_ID", "1:*", "Active", "Single"],
    ["Dim_Well", "Well_ID", "Fact_NPT_PBI", "Well_ID", "1:*", "Active", "Single"],
    ["Dim_Rig", "Rig_ID", "Fact_Drilling_Daily_Report", "Rig_ID", "1:*", "Active", "Single"],
    ["Dim_Rig", "Rig_ID", "Fact_NPT_PBI", "Rig_ID", "1:*", "Active", "Single"],
], columns=[
    "From_Table",
    "From_Column",
    "To_Table",
    "To_Column",
    "Cardinality",
    "Status",
    "Cross_Filter"
])

# =============================================================================
# 17. SCENARIO LOGIC
# =============================================================================

scenario_logic = dim_scenario.copy()

scenario_logic["Baseline_NPT_Hours"] = EXPECTED["npt_hours"]

scenario_logic["NPT_Hours_Reduced"] = (
    scenario_logic["Baseline_NPT_Hours"]
    * scenario_logic["NPT_Reduction_pct"]
)

scenario_logic["NPT_Hours_Remaining"] = (
    scenario_logic["Baseline_NPT_Hours"]
    - scenario_logic["NPT_Hours_Reduced"]
)

scenario_logic["Validated_Economic_Savings_USD"] = [
    0.0,
    EXPECTED["target_savings"] * 0.50,
    EXPECTED["target_savings"],
    EXPECTED["target_savings"] * 1.50
]

# =============================================================================
# 18. POWER BI IMPLEMENTATION CHECKLIST
# =============================================================================

implementation_checklist = pd.DataFrame([
    ["PBI-001", "Import Fact_NPT_PBI", "Required", "OPEN"],
    ["PBI-002", "Import Dim_Scenario", "Required", "OPEN"],
    ["PBI-003", "Import Dim_KPI", "Required", "OPEN"],
    ["PBI-004", "Create six star-schema relationships for Fact_NPT_PBI", "Required", "OPEN"],
    ["PBI-005", "Mark Dim_Date as Date Table", "Required", "OPEN"],
    ["PBI-006", "Create 20 DAX measures", "Required", "OPEN"],
    ["PBI-007", "Create nine KPI definitions", "Required", "OPEN"],
    ["PBI-008", "Create scenario slicer using Dim_Scenario", "Required", "OPEN"],
    ["PBI-009", "Hide technical keys where appropriate", "Recommended", "OPEN"],
    ["PBI-010", "Validate cross-filter direction", "Required", "OPEN"],
    ["PBI-011", "Validate drill-through fields", "Required", "OPEN"],
    ["PBI-012", "Validate Pareto visual", "Required", "OPEN"],
    ["PBI-013", "Validate Savings Protection visual", "Required", "OPEN"],
    ["PBI-014", "Run executive baseline reconciliation", "Required", "OPEN"],
])

# =============================================================================
# 19. DATA LINEAGE
# =============================================================================

lineage = pd.DataFrame([
    ["L001", "SQLite", "Fact_NPT", "Source NPT events and economics"],
    ["L002", "SQLite", "Fact_Drilling_Daily_Report", "Source drilling performance"],
    ["L003", "SQLite", "Dim_Well", "Well dimension"],
    ["L004", "SQLite", "Dim_Rig", "Rig dimension"],
    ["L005", "SQLite", "Dim_Date", "Date dimension"],
    ["L006", "Python", "Fact_NPT_PBI", "Power BI enriched fact"],
    ["L007", "Python", "Dim_Scenario", "Scenario selector"],
    ["L008", "Python", "Dim_KPI", "KPI framework"],
    ["L009", "Power BI", "DAX Measures", "Executive calculations"],
    ["L010", "Power BI", "Dashboard", "Executive decision layer"],
], columns=[
    "Lineage_ID",
    "Layer",
    "Object",
    "Purpose"
])

# =============================================================================
# 20. FINAL REMEDIATION STATUS
# =============================================================================

critical_failures = sum(
    1
    for row in qa_results
    if row["Status"] == "FAIL"
    and row["Severity"] == "CRITICAL"
)

if critical_failures == 0:
    remediation_status = "PASS"
else:
    remediation_status = "FAIL"

# =============================================================================
# 21. SUMMARY
# =============================================================================

summary = pd.DataFrame([
    ["Stage", "2G.20.1"],
    ["Process", "Power BI Data & Semantic Remediation"],
    ["Execution Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    ["Remediation Status", remediation_status],
    ["Critical QA Failures", critical_failures],
    ["NPT Events", len(fact_npt_pbi)],
    ["NPT Hours", round(source_npt_hours, 2)],
    ["Direct NPT Cost", round(source_direct_cost, 2)],
    ["Deferred Cost", round(source_deferred_cost, 2)],
    ["Total Economic Impact", round(source_total_impact, 2)],
    ["Target Savings", round(derived_target_savings, 2)],
    ["Savings At Risk", round(derived_savings_risk, 2)],
    ["Target Savings Rate", round(TARGET_SAVINGS_RATE * 100, 4)],
    ["Initiatives", initiative_count],
    ["Scenario Cases", len(dim_scenario)],
    ["KPI Definitions", len(dim_kpi)],
    ["DAX Measures", len(dax_measures)],
    ["Semantic Tables", len(table_catalog)],
    ["Relationships", len(relationships)],
], columns=["Metric", "Value"])

# =============================================================================
# 22. WRITE EXCEL
# =============================================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    summary.to_excel(
        writer,
        sheet_name="Remediation_Summary",
        index=False
    )

    pd.DataFrame(qa_results).to_excel(
        writer,
        sheet_name="QA_Results",
        index=False
    )

    pd.DataFrame(findings).to_excel(
        writer,
        sheet_name="Findings",
        index=False
    )

    fact_npt_pbi.to_excel(
        writer,
        sheet_name="Fact_NPT_PBI",
        index=False
    )

    initiative_summary.to_excel(
        writer,
        sheet_name="Initiative_Summary",
        index=False
    )

    dim_scenario.to_excel(
        writer,
        sheet_name="Dim_Scenario",
        index=False
    )

    scenario_logic.to_excel(
        writer,
        sheet_name="Scenario_Logic",
        index=False
    )

    dim_kpi.to_excel(
        writer,
        sheet_name="Dim_KPI",
        index=False
    )

    dax_measures.to_excel(
        writer,
        sheet_name="DAX_Measures",
        index=False
    )

    rag_rules.to_excel(
        writer,
        sheet_name="RAG_Rules",
        index=False
    )

    table_catalog.to_excel(
        writer,
        sheet_name="Table_Catalog",
        index=False
    )

    relationships.to_excel(
        writer,
        sheet_name="Relationships",
        index=False
    )

    implementation_checklist.to_excel(
        writer,
        sheet_name="PBI_Checklist",
        index=False
    )

    lineage.to_excel(
        writer,
        sheet_name="Data_Lineage",
        index=False
    )

# =============================================================================
# 23. BASIC EXCEL FORMATTING
# =============================================================================

wb = load_workbook(OUTPUT_FILE)

for ws in wb.worksheets:

    ws.freeze_panes = "A2"

    for column_cells in ws.columns:

        max_length = 0
        column_letter = column_cells[0].column_letter

        for cell in column_cells:

            try:
                value_length = len(str(cell.value))
                max_length = max(
                    max_length,
                    value_length
                )
            except Exception:
                pass

        ws.column_dimensions[column_letter].width = min(
            max_length + 2,
            55
        )

wb.save(OUTPUT_FILE)

# =============================================================================
# 24. CONSOLE OUTPUT
# =============================================================================

print("=" * 88)
print("STAGE 2G.20.1 — POWER BI DATA & SEMANTIC REMEDIATION")
print("=" * 88)

print()
print("--- REMEDIATION STATUS ---")
print(f"Status                        : {remediation_status}")
print(f"Critical QA Failures          : {critical_failures}")

print()
print("--- ECONOMIC BASELINE ---")
print(f"NPT Events                    : {len(fact_npt_pbi):,}")
print(f"NPT Hours                     : {source_npt_hours:,.0f}")
print(f"Direct NPT Cost               : ${source_direct_cost:,.0f}")
print(f"Deferred Cost                 : ${source_deferred_cost:,.0f}")
print(f"Total Economic Impact         : ${source_total_impact:,.0f}")
print(f"Target Savings                : ${derived_target_savings:,.0f}")
print(f"Savings At Risk               : ${derived_savings_risk:,.0f}")

print()
print("--- SEMANTIC REMEDIATION ---")
print(f"Power BI Fact Columns         : {len(required_pbi_columns)}")
print(f"Initiatives                   : {initiative_count}")
print(f"Scenario Cases                : {len(dim_scenario)}")
print(f"KPI Definitions               : {len(dim_kpi)}")
print(f"DAX Measures                  : {len(dax_measures)}")
print(f"Semantic Tables               : {len(table_catalog)}")
print(f"Relationships                 : {len(relationships)}")

print()
print("--- INITIATIVE SUMMARY ---")

for _, row in initiative_summary.iterrows():

    print(
        f"{row['Initiative_ID']} | "
        f"{row['NPT_Events']} events | "
        f"{row['NPT_Hours']:.1f} hr | "
        f"${row['Target_Savings_USD']:,.0f}"
    )

print()
print("--- OUTPUT ---")
print(f"{OUTPUT_FILE}")

print("=" * 88)
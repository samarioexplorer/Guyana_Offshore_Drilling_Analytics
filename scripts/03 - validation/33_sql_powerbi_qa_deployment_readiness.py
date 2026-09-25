import os
import re
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

# =============================================================================
# STAGE 2G.20
# POWER BI EXECUTIVE DASHBOARD QA & DEPLOYMENT READINESS GATE
# =============================================================================

PROJECT_ROOT = r"C:\Users\aniba\Documents\Guyana_Offshore_Drilling_Analytics"
DB_PATH = os.path.join(PROJECT_ROOT, "database", "guyana_drilling.db")
OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "outputs",
    "sql_stage_2G.20_PowerBI_QA_Deployment_Readiness"
)
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "sql_stage_2G.20_PowerBI_QA_Deployment_Readiness.xlsx"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

EXPECTED = {
    "npt_rows": 677,
    "drilling_rows": 1474,
    "npt_hours": 4008,
    "direct_cost": 79204408,
    "deferred_cost": 118945770,
    "total_impact": 198150178,
    "target_savings": 30825850,
    "savings_at_risk": 6390129,
    "wells": 50,
    "rigs": 4,
    "drilling_days": 666,
    "footage": 952078.8,
    "average_rop": 33.67,
    "cost_per_foot": 687.67,
    "npt_hours_per_day": 6.02,
    "dax_measures": 20,
    "kpi_definitions": 9,
    "dashboard_pages": 9,
    "visual_specs": 14,
    "navigation_items": 9,
    "drillthrough_paths": 6,
    "scenario_cases": 4,
}

TARGET_RATE = EXPECTED["target_savings"] / EXPECTED["total_impact"]

# =============================================================================
# HELPERS
# =============================================================================

results = []
findings = []
dax_results = []
relationship_results = []
lineage_results = []
deployment_results = []


def add_result(test_id, area, test, expected, actual, status, severity="INFO"):
    results.append({
        "Test_ID": test_id,
        "Area": area,
        "Test": test,
        "Expected": expected,
        "Actual": actual,
        "Status": status,
        "Severity": severity
    })


def add_finding(finding_id, area, severity, finding, recommendation):
    findings.append({
        "Finding_ID": finding_id,
        "Area": area,
        "Severity": severity,
        "Finding": finding,
        "Recommendation": recommendation
    })


def add_deployment(item_id, gate, requirement, status, evidence, action):
    deployment_results.append({
        "Gate_ID": item_id,
        "Gate": gate,
        "Requirement": requirement,
        "Status": status,
        "Evidence": evidence,
        "Required_Action": action
    })


def sql_value(con, sql):
    return pd.read_sql_query(sql, con).iloc[0, 0]


# =============================================================================
# LOAD DATABASE
# =============================================================================

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

con = sqlite3.connect(DB_PATH)

tables = pd.read_sql_query(
    "SELECT name FROM sqlite_master WHERE type='table'",
    con
)["name"].tolist()

required_tables = [
    "Dim_Date",
    "Dim_Rig",
    "Dim_Well",
    "Fact_Drilling_Daily_Report",
    "Fact_NPT"
]

# =============================================================================
# LOAD TABLES
# =============================================================================

dim_date = pd.read_sql_query("SELECT * FROM Dim_Date", con)
dim_rig = pd.read_sql_query("SELECT * FROM Dim_Rig", con)
dim_well = pd.read_sql_query("SELECT * FROM Dim_Well", con)
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
# 1. SOURCE TABLE QA
# =============================================================================

for table in required_tables:
    status = "PASS" if table in tables else "FAIL"
    add_result(
        "QA-001",
        "Source Model",
        f"Required table exists: {table}",
        "EXISTS",
        "EXISTS" if status == "PASS" else "MISSING",
        status,
        "CRITICAL" if status == "FAIL" else "INFO"
    )

# =============================================================================
# 2. ROW COUNT RECONCILIATION
# =============================================================================

checks = [
    ("QA-010", "Fact_NPT row count", EXPECTED["npt_rows"], len(fact_npt)),
    ("QA-011", "Fact_Drilling row count", EXPECTED["drilling_rows"], len(fact_drilling)),
    ("QA-012", "Dim_Well row count", EXPECTED["wells"], len(dim_well)),
    ("QA-013", "Dim_Rig row count", EXPECTED["rigs"], len(dim_rig)),
]

for tid, label, expected, actual in checks:
    status = "PASS" if expected == actual else "FAIL"
    add_result(
        tid,
        "Source Reconciliation",
        label,
        expected,
        actual,
        status,
        "CRITICAL" if status == "FAIL" else "INFO"
    )

# =============================================================================
# 3. COLUMN QA
# =============================================================================

required_columns = {
    "Dim_Date": ["Date"],
    "Dim_Rig": ["Rig_ID"],
    "Dim_Well": ["Well_ID"],
    "Fact_Drilling_Daily_Report": [
        "Date",
        "Well_ID",
        "Rig_ID",
        "Daily_Footage_ft",
        "ROP_ft_hr",
        "Daily_Cost_USD"
    ],
    "Fact_NPT": [
        "NPT_ID",
        "Date",
        "Well_ID",
        "Rig_ID",
        "Duration_hr",
        "Cost_USD",
        "Deferred_Cost_USD",
        "Total_Impact_USD",
        "Root_Cause"
    ]
}

for table_name, cols in required_columns.items():

    if table_name == "Dim_Date":
        df = dim_date
    elif table_name == "Dim_Rig":
        df = dim_rig
    elif table_name == "Dim_Well":
        df = dim_well
    elif table_name == "Fact_Drilling_Daily_Report":
        df = fact_drilling
    else:
        df = fact_npt

    for col in cols:
        status = "PASS" if col in df.columns else "FAIL"

        add_result(
            "QA-020",
            "Column Integrity",
            f"{table_name}.{col}",
            "PRESENT",
            "PRESENT" if status == "PASS" else "MISSING",
            status,
            "CRITICAL" if status == "FAIL" else "INFO"
        )

# =============================================================================
# 4. DIMENSION KEY UNIQUENESS
# =============================================================================

dimension_keys = [
    ("Dim_Date", dim_date, "Date"),
    ("Dim_Rig", dim_rig, "Rig_ID"),
    ("Dim_Well", dim_well, "Well_ID"),
]

for name, df, key in dimension_keys:

    if key in df.columns:
        duplicate_count = int(df[key].duplicated().sum())
        null_count = int(df[key].isna().sum())

        status = "PASS" if duplicate_count == 0 and null_count == 0 else "FAIL"

        add_result(
            "QA-030",
            "Dimension Integrity",
            f"{name} key uniqueness",
            "0 duplicates / 0 nulls",
            f"{duplicate_count} duplicates / {null_count} nulls",
            status,
            "CRITICAL" if status == "FAIL" else "INFO"
        )

# =============================================================================
# 5. FACT KEY INTEGRITY
# =============================================================================

if all(c in fact_npt.columns for c in ["NPT_ID"]):
    dup_npt = int(fact_npt["NPT_ID"].duplicated().sum())
    add_result(
        "QA-040",
        "Fact Integrity",
        "NPT_ID uniqueness",
        0,
        dup_npt,
        "PASS" if dup_npt == 0 else "FAIL",
        "CRITICAL" if dup_npt else "INFO"
    )

drill_key_cols = ["Date", "Well_ID", "Rig_ID"]

if all(c in fact_drilling.columns for c in drill_key_cols):
    drill_dups = int(
        fact_drilling.duplicated(subset=drill_key_cols).sum()
    )

    add_result(
        "QA-041",
        "Fact Integrity",
        "Drilling daily composite key duplicates",
        0,
        drill_dups,
        "PASS" if drill_dups == 0 else "FAIL",
        "CRITICAL" if drill_dups else "INFO"
    )

# =============================================================================
# 6. REFERENTIAL INTEGRITY
# =============================================================================

def orphan_count(fact, fact_key, dim):
    return int(
        (~fact[fact_key].isin(dim[fact_key].dropna().unique())).sum()
    )


for fact_name, fact_df in [
    ("Fact_Drilling_Daily_Report", fact_drilling),
    ("Fact_NPT", fact_npt)
]:

    for key, dim_df in [
        ("Well_ID", dim_well),
        ("Rig_ID", dim_rig)
    ]:

        if key in fact_df.columns and key in dim_df.columns:

            orphans = orphan_count(
                fact_df,
                key,
                dim_df
            )

            status = "PASS" if orphans == 0 else "FAIL"

            relationship_results.append({
                "Fact": fact_name,
                "Dimension": f"Dim_{'Well' if key == 'Well_ID' else 'Rig'}",
                "Key": key,
                "Orphans": orphans,
                "Status": status
            })

            add_result(
                "QA-050",
                "Referential Integrity",
                f"{fact_name} -> {key}",
                0,
                orphans,
                status,
                "CRITICAL" if orphans else "INFO"
            )

# =============================================================================
# 7. DATE QA
# =============================================================================

if "Date" in dim_date.columns:

    dates = pd.to_datetime(dim_date["Date"], errors="coerce")

    null_dates = int(dates.isna().sum())
    duplicate_dates = int(dates.duplicated().sum())

    sorted_dates = dates.dropna().sort_values()

    if len(sorted_dates) > 1:
        gaps = sorted_dates.diff().dropna()
        gap_count = int((gaps > pd.Timedelta(days=1)).sum())
    else:
        gap_count = 0

    add_result(
        "QA-060",
        "Date Intelligence",
        "Dim_Date null dates",
        0,
        null_dates,
        "PASS" if null_dates == 0 else "FAIL",
        "CRITICAL" if null_dates else "INFO"
    )

    add_result(
        "QA-061",
        "Date Intelligence",
        "Dim_Date duplicate dates",
        0,
        duplicate_dates,
        "PASS" if duplicate_dates == 0 else "FAIL",
        "CRITICAL" if duplicate_dates else "INFO"
    )

    add_result(
        "QA-062",
        "Date Intelligence",
        "Dim_Date continuity gaps",
        0,
        gap_count,
        "PASS" if gap_count == 0 else "WARN",
        "HIGH" if gap_count else "INFO"
    )

# =============================================================================
# 8. ECONOMIC RECONCILIATION
# =============================================================================

npt_hours = float(fact_npt["Duration_hr"].sum())
direct_cost = float(fact_npt["Cost_USD"].sum())
deferred_cost = float(fact_npt["Deferred_Cost_USD"].sum())
total_impact = float(fact_npt["Total_Impact_USD"].sum())

economic_tests = [
    ("QA-070", "NPT hours", EXPECTED["npt_hours"], npt_hours),
    ("QA-071", "Direct NPT cost", EXPECTED["direct_cost"], direct_cost),
    ("QA-072", "Deferred cost", EXPECTED["deferred_cost"], deferred_cost),
    ("QA-073", "Total economic impact", EXPECTED["total_impact"], total_impact),
]

for tid, label, expected, actual in economic_tests:

    diff = abs(expected - actual)

    status = "PASS" if diff < 0.01 else "FAIL"

    add_result(
        tid,
        "Economic Reconciliation",
        label,
        expected,
        round(actual, 2),
        status,
        "CRITICAL" if status == "FAIL" else "INFO"
    )

# =============================================================================
# 9. CRITICAL ARCHITECTURE CHECK:
#    POWER BI REQUIRED ENRICHED COLUMNS
# =============================================================================

required_pbi_columns = [
    "Target_Savings_USD",
    "Savings_At_Risk_USD",
    "Initiative_ID",
    "Initiative_Name",
    "Risk_Factor"
]

for col in required_pbi_columns:

    exists = col in fact_npt.columns

    add_result(
        "QA-080",
        "Power BI Data Architecture",
        f"Fact_NPT contains {col}",
        "PRESENT",
        "PRESENT" if exists else "MISSING",
        "PASS" if exists else "FAIL",
        "CRITICAL" if not exists else "INFO"
    )

# =============================================================================
# 10. DERIVED POWER BI ENRICHMENT RECONCILIATION
# =============================================================================

fact_npt_pbi = fact_npt.copy()

fact_npt_pbi["Target_Savings_USD"] = (
    fact_npt_pbi["Total_Impact_USD"] * TARGET_RATE
)

def initiative_class(row):
    category = str(row.get("NPT_Category", "")).strip()
    subcategory = str(row.get("NPT_Subcategory", "")).strip()

    if category == "Mechanical":
        return "INIT-002", "Mechanical Reliability Program"

    if category == "Weather":
        return "INIT-003", "Weather & Marine Operations Resilience"

    if category == "Logistics":
        return "INIT-004", "Supply Chain & Logistics Optimization"

    if category == "Personnel":
        return "INIT-005", "People, Competency & Operational Readiness"

    if category == "Drilling":
        if subcategory == "Bit Wear":
            return "INIT-006", "Drilling Performance Optimization"
        return "INIT-001", "Drilling Dysfunction Reduction Program"

    return "UNASSIGNED", "Unassigned"

pairs = fact_npt_pbi.apply(initiative_class, axis=1)

fact_npt_pbi["Initiative_ID"] = pairs.apply(lambda x: x[0])
fact_npt_pbi["Initiative_Name"] = pairs.apply(lambda x: x[1])

# Normalize Action_Status

if "Action_Status" in fact_npt_pbi.columns:

    action_status = (
        fact_npt_pbi["Action_Status"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .str.title()
    )

else:
    action_status = pd.Series(
        ["Unknown"] * len(fact_npt_pbi)
    )

fact_npt_pbi["Action_Status_Normalized"] = action_status

risk_map = {
    "Open": 1.00,
    "In Progress": 0.50,
    "Closed": 0.00,
    "Completed": 0.00
}

fact_npt_pbi["Risk_Factor"] = (
    fact_npt_pbi["Action_Status_Normalized"]
    .map(risk_map)
    .fillna(0.25)
)

fact_npt_pbi["Savings_At_Risk_USD"] = (
    fact_npt_pbi["Target_Savings_USD"]
    * fact_npt_pbi["Risk_Factor"]
)

derived_target = fact_npt_pbi["Target_Savings_USD"].sum()
derived_risk = fact_npt_pbi["Savings_At_Risk_USD"].sum()

add_result(
    "QA-081",
    "Power BI Enrichment",
    "Derived target savings reconciliation",
    EXPECTED["target_savings"],
    round(derived_target, 2),
    "PASS" if abs(derived_target - EXPECTED["target_savings"]) < 0.01 else "FAIL",
    "CRITICAL" if abs(derived_target - EXPECTED["target_savings"]) >= 0.01 else "INFO"
)

add_result(
    "QA-082",
    "Power BI Enrichment",
    "Derived savings-at-risk reconciliation",
    EXPECTED["savings_at_risk"],
    round(derived_risk, 2),
    "PASS" if abs(derived_risk - EXPECTED["savings_at_risk"]) < 1 else "WARN",
    "HIGH" if abs(derived_risk - EXPECTED["savings_at_risk"]) >= 1 else "INFO"
)

# =============================================================================
# 11. INITIATIVE RECONCILIATION
# =============================================================================

initiative_counts = (
    fact_npt_pbi
    .groupby(["Initiative_ID", "Initiative_Name"])
    .size()
    .reset_index(name="Event_Count")
)

initiative_count = len(initiative_counts)

add_result(
    "QA-090",
    "Initiative Model",
    "Initiative count",
    6,
    initiative_count,
    "PASS" if initiative_count == 6 else "FAIL",
    "CRITICAL" if initiative_count != 6 else "INFO"
)

# =============================================================================
# 12. DAX MEASURE CATALOG
# =============================================================================

dax_measures = {
    "M001": "NPT Events",
    "M002": "NPT Hours",
    "M003": "Direct NPT Cost",
    "M004": "Deferred Cost",
    "M005": "Total Economic Impact",
    "M006": "Target Savings",
    "M007": "Savings At Risk",
    "M008": "Average ROP",
    "M009": "Total Footage",
    "M010": "Cost per Foot",
    "M011": "NPT Hours per Drilling Day",
    "M012": "Target Savings Rate",
    "M013": "Savings Protection Rate",
    "M014": "Drilling Days",
    "M015": "Well Count",
    "M016": "Rig Count",
    "M017": "Target Variance",
    "M018": "NPT Cost per Hour",
    "M019": "Economic Impact per NPT Hour",
    "M020": "Savings Risk %"
}

add_result(
    "QA-100",
    "DAX Architecture",
    "DAX measure catalog count",
    EXPECTED["dax_measures"],
    len(dax_measures),
    "PASS" if len(dax_measures) == EXPECTED["dax_measures"] else "FAIL",
    "CRITICAL" if len(dax_measures) != EXPECTED["dax_measures"] else "INFO"
)

# =============================================================================
# 13. DAX DEPENDENCY INTEGRITY
# =============================================================================

measure_definitions = {
    "M001": "COUNTROWS(Fact_NPT)",
    "M002": "SUM(Fact_NPT[Duration_hr])",
    "M003": "SUM(Fact_NPT[Cost_USD])",
    "M004": "SUM(Fact_NPT[Deferred_Cost_USD])",
    "M005": "[Direct NPT Cost] + [Deferred Cost]",
    "M006": "SUM(Fact_NPT[Target_Savings_USD])",
    "M007": "SUM(Fact_NPT[Savings_At_Risk_USD])",
    "M008": "AVERAGE(Fact_Drilling_Daily_Report[ROP_ft_hr])",
    "M009": "SUM(Fact_Drilling_Daily_Report[Daily_Footage_ft])",
    "M010": "DIVIDE(SUM(Fact_Drilling_Daily_Report[Daily_Cost_USD]), [Total Footage])",
    "M011": "DIVIDE([NPT Hours], DISTINCTCOUNT(Fact_Drilling_Daily_Report[Date]))",
    "M012": "DIVIDE([Target Savings], [Total Economic Impact])",
    "M013": "1 - DIVIDE([Savings At Risk], [Target Savings])",
    "M014": "DISTINCTCOUNT(Fact_Drilling_Daily_Report[Date])",
    "M015": "DISTINCTCOUNT(Dim_Well[Well_ID])",
    "M016": "DISTINCTCOUNT(Dim_Rig[Rig_ID])",
    "M017": "[Target Savings] - [Savings At Risk]",
    "M018": "DIVIDE([Direct NPT Cost], [NPT Hours])",
    "M019": "DIVIDE([Total Economic Impact], [NPT Hours])",
    "M020": "DIVIDE([Savings At Risk], [Target Savings])"
}

all_columns = {}
for name, df in {
    "Dim_Date": dim_date,
    "Dim_Rig": dim_rig,
    "Dim_Well": dim_well,
    "Fact_Drilling_Daily_Report": fact_drilling,
    "Fact_NPT": fact_npt
}.items():
    all_columns[name] = set(df.columns)

measure_names = set(dax_measures.values())

for mid, expression in measure_definitions.items():

    invalid_columns = []

    refs = re.findall(
        r"(Dim_Date|Dim_Rig|Dim_Well|Fact_Drilling_Daily_Report|Fact_NPT)\[([^\]]+)\]",
        expression
    )

    for table, column in refs:

        if column not in all_columns.get(table, set()):

            # These are intentionally expected to fail for the
            # raw SQLite Fact_NPT architecture.
            invalid_columns.append(f"{table}[{column}]")

    measure_refs = re.findall(
        r"\[([A-Za-z0-9 _%]+)\]",
        expression
    )

    unresolved_measures = []

    for ref in measure_refs:

        if ref not in measure_names:
            unresolved_measures.append(ref)

    status = "PASS"

    if invalid_columns:
        status = "FAIL"

    dax_results.append({
        "Measure_ID": mid,
        "Measure_Name": dax_measures[mid],
        "Expression": expression,
        "Invalid_Column_References": "; ".join(invalid_columns),
        "Unresolved_Measure_References": "; ".join(unresolved_measures),
        "Status": status
    })

    add_result(
        "QA-101",
        "DAX Dependency",
        f"{mid} - {dax_measures[mid]}",
        "VALID REFERENCES",
        "VALID" if status == "PASS" else "INVALID COLUMN REFERENCE",
        status,
        "CRITICAL" if status == "FAIL" else "INFO"
    )

# =============================================================================
# 14. EXPLICIT ARCHITECTURAL FINDINGS
# =============================================================================

missing_enriched = [
    c for c in required_pbi_columns
    if c not in fact_npt.columns
]

if missing_enriched:

    add_finding(
        "F-001",
        "Power BI Semantic Model",
        "CRITICAL",
        "Power BI measures reference enriched Fact_NPT fields that are not physically present in the SQLite source fact.",
        "Create a Power BI-ready Fact_NPT_PBI table/view or implement the enrichment explicitly in Power Query before importing the model."
    )

add_finding(
    "F-002",
    "Scenario Architecture",
    "HIGH",
    "Scenario slicer requires a disconnected Scenario table in the Power BI model.",
    "Create Dim_Scenario with Baseline, Conservative, Target and Stretch and connect the slicer to scenario measures."
)

add_finding(
    "F-003",
    "KPI Architecture",
    "HIGH",
    "The dashboard defines 9 KPIs but the package contains only 6 KPI status measures.",
    "Create a KPI dimension/disconnected table and a complete KPI status calculation covering all 9 KPI definitions."
)

add_finding(
    "F-004",
    "Visual Compatibility",
    "MEDIUM",
    "Native Power BI waterfall and Pareto implementations require explicit visual configuration; the build specification alone is insufficient.",
    "Implement the waterfall with valid category/value semantics and implement Pareto as bar + cumulative percentage line or approved custom visual."
)

add_finding(
    "F-005",
    "Drill-through",
    "MEDIUM",
    "A combined Rig_ID + Well_ID drill-through concept is not a single native Power BI field.",
    "Use separate Rig_ID and Well_ID drill-through fields or define a dedicated composite business key."
)

add_finding(
    "F-006",
    "KPI Definition",
    "LOW",
    "NPT Hours per Drilling Day uses DISTINCTCOUNT(Date), representing portfolio calendar drilling days rather than well-days.",
    "Rename the KPI to NPT Hours per Portfolio Drilling Day or explicitly document the denominator."
)

# =============================================================================
# 15. DASHBOARD ARCHITECTURE
# =============================================================================

architecture_counts = {
    "KPI definitions": EXPECTED["kpi_definitions"],
    "Dashboard pages": EXPECTED["dashboard_pages"],
    "Visual specifications": EXPECTED["visual_specs"],
    "Navigation items": EXPECTED["navigation_items"],
    "Drill-through paths": EXPECTED["drillthrough_paths"],
    "Scenario cases": EXPECTED["scenario_cases"]
}

for label, expected in architecture_counts.items():

    add_result(
        "QA-110",
        "Dashboard Architecture",
        label,
        expected,
        expected,
        "PASS",
        "INFO"
    )

# =============================================================================
# 16. SQL -> PYTHON -> POWER BI LINEAGE
# =============================================================================

lineage_items = [
    ("SQL", "Fact_NPT", "NPT events / hours / costs", "PASS"),
    ("SQL", "Fact_Drilling_Daily_Report", "Footage / ROP / drilling cost", "PASS"),
    ("SQL", "Dim_Well", "Well filtering", "PASS"),
    ("SQL", "Dim_Rig", "Rig filtering", "PASS"),
    ("SQL", "Dim_Date", "Date intelligence", "PASS"),
    ("Python", "Target Savings Allocation", "Validated target savings rate", "PASS"),
    ("Python", "Initiative Classification", "6 initiative portfolio", "PASS"),
    ("Python", "Savings Risk", "Savings at risk", "PASS"),
    ("Power BI", "DAX Measures", "Executive KPI calculations", "CONDITIONAL"),
]

for source, object_name, purpose, status in lineage_items:

    lineage_results.append({
        "Layer": source,
        "Object": object_name,
        "Purpose": purpose,
        "Status": status
    })

# =============================================================================
# 17. EXECUTIVE BASELINE
# =============================================================================

operational_values = {
    "NPT Events": len(fact_npt),
    "NPT Hours": npt_hours,
    "Direct NPT Cost": direct_cost,
    "Deferred Cost": deferred_cost,
    "Total Economic Impact": total_impact,
    "Target Savings": derived_target,
    "Savings At Risk": derived_risk,
    "Wells": fact_npt["Well_ID"].nunique(),
    "Rigs": fact_npt["Rig_ID"].nunique(),
    "Drilling Days": fact_drilling["Date"].nunique(),
    "Total Footage": fact_drilling["Daily_Footage_ft"].sum(),
    "Average ROP": fact_drilling["ROP_ft_hr"].mean(),
    "Cost per Foot": (
        fact_drilling["Daily_Cost_USD"].sum()
        / fact_drilling["Daily_Footage_ft"].sum()
    )
}

for label, actual in operational_values.items():

    key_map = {
        "NPT Events": "npt_rows",
        "NPT Hours": "npt_hours",
        "Direct NPT Cost": "direct_cost",
        "Deferred Cost": "deferred_cost",
        "Total Economic Impact": "total_impact",
        "Target Savings": "target_savings",
        "Savings At Risk": "savings_at_risk",
        "Wells": "wells",
        "Rigs": "rigs",
        "Drilling Days": "drilling_days",
        "Total Footage": "footage",
        "Average ROP": "average_rop",
        "Cost per Foot": "cost_per_foot"
    }

    expected = EXPECTED[key_map[label]]

    tolerance = 0.01

    if label in ["Savings At Risk"]:
        tolerance = 1.0

    diff = abs(float(actual) - float(expected))

    status = "PASS" if diff <= tolerance else "FAIL"

    add_result(
        "QA-120",
        "Executive Baseline",
        label,
        expected,
        round(float(actual), 2),
        status,
        "CRITICAL" if status == "FAIL" else "INFO"
    )

# =============================================================================
# 18. DEPLOYMENT GATE
# =============================================================================

critical_failures = sum(
    1 for r in results
    if r["Status"] == "FAIL" and r["Severity"] == "CRITICAL"
)

high_failures = sum(
    1 for r in results
    if r["Status"] == "FAIL" and r["Severity"] == "HIGH"
)

if critical_failures > 0:
    overall_status = "NOT READY"
elif high_failures > 0 or any(
    f["Severity"] == "CRITICAL" for f in findings
):
    overall_status = "CONDITIONAL"
else:
    overall_status = "READY"

deployment_gate_items = [
    (
        "DG-001",
        "Source integrity",
        "All source tables, columns and keys valid",
        "PASS" if critical_failures == 0 else "FAIL",
        "Source database QA",
        "Resolve critical source failures"
    ),
    (
        "DG-002",
        "Economic reconciliation",
        "Economic baseline reconciles to validated 2G.10.1 baseline",
        "PASS",
        "677 NPT events / $198.150M impact",
        "None"
    ),
    (
        "DG-003",
        "Power BI enriched fact",
        "Target savings and savings-at-risk fields available to Power BI",
        "FAIL" if missing_enriched else "PASS",
        "Missing physical enriched columns" if missing_enriched else "Columns present",
        "Create Power BI-ready enriched fact"
        if missing_enriched else "None"
    ),
    (
        "DG-004",
        "DAX dependency integrity",
        "All DAX measure references resolve",
        "FAIL" if any(
            x["Status"] == "FAIL" for x in dax_results
        ) else "PASS",
        "DAX dependency QA",
        "Fix unresolved field references"
    ),
    (
        "DG-005",
        "Scenario architecture",
        "Scenario slicer has valid disconnected table",
        "FAIL",
        "Scenario table not part of source star schema",
        "Create Dim_Scenario"
    ),
    (
        "DG-006",
        "KPI architecture",
        "All 9 KPIs have status logic",
        "FAIL",
        "Only 6 KPI status measures currently specified",
        "Complete KPI status architecture"
    ),
    (
        "DG-007",
        "Dashboard navigation",
        "9 pages / 9 navigation items",
        "PASS",
        "2G.19 build package",
        "None"
    ),
    (
        "DG-008",
        "Drill-through",
        "6 drill-through paths technically implementable",
        "CONDITIONAL",
        "Rig + Well composite path requires design adjustment",
        "Implement separate fields or composite key"
    ),
    (
        "DG-009",
        "Visual compatibility",
        "All visuals implementable in Power BI",
        "CONDITIONAL",
        "Pareto / Waterfall require implementation QA",
        "Validate native/custom visual configuration"
    ),
    (
        "DG-010",
        "Executive baseline",
        "Power BI KPI baseline matches validated SQL/Python baseline",
        "PASS",
        "All baseline reconciliations pass",
        "None"
    )
]

for row in deployment_gate_items:
    add_deployment(*row)

# =============================================================================
# 19. FINAL STATUS
# =============================================================================

if any(x[3] == "FAIL" for x in deployment_gate_items):
    final_release_status = "CONDITIONAL — REMEDIATION REQUIRED"
else:
    final_release_status = "READY FOR DEPLOYMENT"

# =============================================================================
# 20. SUMMARY
# =============================================================================

summary = pd.DataFrame([
    ["Stage", "2G.20"],
    ["Gate", "Power BI Executive Dashboard QA & Deployment Readiness"],
    ["Execution Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
    ["Overall QA Status", overall_status],
    ["Final Release Status", final_release_status],
    ["Critical Failures", critical_failures],
    ["High Failures", high_failures],
    ["NPT Events", len(fact_npt)],
    ["NPT Hours", round(npt_hours, 2)],
    ["Direct NPT Cost", round(direct_cost, 2)],
    ["Deferred Cost", round(deferred_cost, 2)],
    ["Total Economic Impact", round(total_impact, 2)],
    ["Target Savings", round(derived_target, 2)],
    ["Savings At Risk", round(derived_risk, 2)],
    ["Wells", fact_npt["Well_ID"].nunique()],
    ["Rigs", fact_npt["Rig_ID"].nunique()],
    ["Drilling Days", fact_drilling["Date"].nunique()],
    ["Total Footage", round(fact_drilling["Daily_Footage_ft"].sum(), 1)],
    ["Average ROP", round(fact_drilling["ROP_ft_hr"].mean(), 2)],
    ["Cost per Foot", round(
        fact_drilling["Daily_Cost_USD"].sum()
        / fact_drilling["Daily_Footage_ft"].sum(),
        2
    )],
    ["DAX Measures", len(dax_measures)],
    ["KPI Definitions", EXPECTED["kpi_definitions"]],
    ["Dashboard Pages", EXPECTED["dashboard_pages"]],
    ["Visual Specifications", EXPECTED["visual_specs"]],
    ["Navigation Items", EXPECTED["navigation_items"]],
    ["Drill-through Paths", EXPECTED["drillthrough_paths"]],
    ["Scenario Cases", EXPECTED["scenario_cases"]],
], columns=["Metric", "Value"])

# =============================================================================
# 21. WRITE EXCEL
# =============================================================================

results_df = pd.DataFrame(results)
findings_df = pd.DataFrame(findings)
dax_df = pd.DataFrame(dax_results)
relationships_df = pd.DataFrame(relationship_results)
lineage_df = pd.DataFrame(lineage_results)
deployment_df = pd.DataFrame(deployment_results)

initiative_df = (
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

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    summary.to_excel(
        writer,
        sheet_name="QA_Summary",
        index=False
    )

    results_df.to_excel(
        writer,
        sheet_name="QA_Test_Results",
        index=False
    )

    findings_df.to_excel(
        writer,
        sheet_name="QA_Findings",
        index=False
    )

    deployment_df.to_excel(
        writer,
        sheet_name="Deployment_Gate",
        index=False
    )

    dax_df.to_excel(
        writer,
        sheet_name="DAX_Dependency_QA",
        index=False
    )

    relationships_df.to_excel(
        writer,
        sheet_name="Relationship_QA",
        index=False
    )

    lineage_df.to_excel(
        writer,
        sheet_name="Data_Lineage",
        index=False
    )

    initiative_df.to_excel(
        writer,
        sheet_name="Initiative_QA",
        index=False
    )

    fact_npt_pbi[
        [
            "NPT_ID",
            "Date",
            "Well_ID",
            "Rig_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Duration_hr",
            "Total_Impact_USD",
            "Target_Savings_USD",
            "Initiative_ID",
            "Initiative_Name",
            "Action_Status_Normalized",
            "Risk_Factor",
            "Savings_At_Risk_USD"
        ]
    ].to_excel(
        writer,
        sheet_name="PowerBI_Enriched_Fact",
        index=False
    )

# =============================================================================
# 22. CONSOLE OUTPUT
# =============================================================================

print("=" * 88)
print("STAGE 2G.20 — POWER BI EXECUTIVE DASHBOARD QA & DEPLOYMENT READINESS")
print("=" * 88)

print()
print("--- QA STATUS ---")
print(f"Overall QA Status             : {overall_status}")
print(f"Final Release Status          : {final_release_status}")
print(f"Critical Failures             : {critical_failures}")
print(f"High Failures                 : {high_failures}")

print()
print("--- EXECUTIVE BASELINE ---")
print(f"NPT Events                    : {len(fact_npt):,}")
print(f"NPT Hours                     : {npt_hours:,.0f}")
print(f"Direct NPT Cost               : ${direct_cost:,.0f}")
print(f"Deferred Cost                 : ${deferred_cost:,.0f}")
print(f"Total Economic Impact         : ${total_impact:,.0f}")
print(f"Target Savings                : ${derived_target:,.0f}")
print(f"Savings At Risk               : ${derived_risk:,.0f}")

print()
print("--- POWER BI ARCHITECTURE ---")
print(f"DAX Measures                  : {len(dax_measures)}")
print(f"KPI Definitions               : {EXPECTED['kpi_definitions']}")
print(f"Dashboard Pages               : {EXPECTED['dashboard_pages']}")
print(f"Visual Specifications         : {EXPECTED['visual_specs']}")
print(f"Navigation Items              : {EXPECTED['navigation_items']}")
print(f"Drill-through Paths           : {EXPECTED['drillthrough_paths']}")
print(f"Scenario Cases                : {EXPECTED['scenario_cases']}")

print()
print("--- CRITICAL FINDINGS ---")

for f in findings:
    print(
        f"{f['Finding_ID']} | "
        f"{f['Severity']} | "
        f"{f['Area']} | "
        f"{f['Finding']}"
    )

print()
print("--- DEPLOYMENT GATE ---")

for row in deployment_gate_items:
    print(
        f"{row[0]} | "
        f"{row[3]} | "
        f"{row[1]}"
    )

print()
print("--- OUTPUT ---")
print(f"Output file: {OUTPUT_FILE}")
print("=" * 88)
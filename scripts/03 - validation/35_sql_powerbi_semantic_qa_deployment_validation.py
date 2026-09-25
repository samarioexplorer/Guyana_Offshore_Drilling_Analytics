# STAGE 2G.20.2 — POWER BI SEMANTIC QA & DEPLOYMENT VALIDATION

from pathlib import Path
import sqlite3
import pandas as pd
import re

# =============================================================================
# PATHS
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

INPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.20.1_PowerBI_Data_Semantic_Remediation"
)

INPUT_XLSX = (
    INPUT_DIR
    / "sql_stage_2G.20.1_PowerBI_Data_Semantic_Remediation.xlsx"
)

DASHBOARD_INPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.19_PowerBI_Executive_Dashboard"
)

DASHBOARD_INPUT_XLSX = (
    DASHBOARD_INPUT_DIR
    / "sql_stage_2G.19_PowerBI_Executive_Dashboard.xlsx"
)

INTELLIGENCE_INPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.17_Executive_Operational_Intelligence"
)

INTELLIGENCE_INPUT_XLSX = (
    INTELLIGENCE_INPUT_DIR
    / "sql_stage_2G.17_Executive_Operational_Intelligence.xlsx"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.20.2_PowerBI_Semantic_QA_Deployment_Validation"
)

OUTPUT_XLSX = (
    OUTPUT_DIR
    / "sql_stage_2G.20.2_PowerBI_Semantic_QA_Deployment_Validation.xlsx"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# VALIDATED BASELINE
# =============================================================================

EXPECTED = {
    "npt_events": 677,
    "npt_hours": 4008.0,
    "direct_cost": 79204408.0,
    "deferred_cost": 118945770.0,
    "total_impact": 198150178.0,
    "target_savings": 30825850.0,
    "savings_at_risk": 6390129.0,
    "wells": 50,
    "rigs": 4,
    "drilling_days": 666,
    "footage": 952078.8,
    "avg_rop": 33.67,
    "cost_per_foot": 687.67,
}

EXPECTED_INITIATIVES = {
    "INIT-001": (168, 962.0, 7164099.0),
    "INIT-002": (171, 1052.0, 8125652.0),
    "INIT-003": (161, 942.0, 7293656.0),
    "INIT-004": (104, 606.0, 4827110.0),
    "INIT-005": (28, 156.0, 1080154.0),
    "INIT-006": (45, 290.0, 2335179.0),
}

EXPECTED_SCENARIOS = {
    "SCN-001": ("Baseline", 0.00),
    "SCN-002": ("Conservative", 0.20),
    "SCN-003": ("Target", 0.40),
    "SCN-004": ("Stretch", 0.60),
}

EXPECTED_TABLES = {
    "Dim_Date",
    "Dim_Well",
    "Dim_Rig",
    "Fact_Drilling_Daily_Report",
    "Fact_NPT_PBI",
    "Dim_Scenario",
    "Dim_KPI",
}

EXPECTED_RELATIONSHIPS = {
    ("Dim_Date", "Fact_Drilling_Daily_Report"),
    ("Dim_Date", "Fact_NPT_PBI"),
    ("Dim_Well", "Fact_Drilling_Daily_Report"),
    ("Dim_Well", "Fact_NPT_PBI"),
    ("Dim_Rig", "Fact_Drilling_Daily_Report"),
    ("Dim_Rig", "Fact_NPT_PBI"),
}

EXPECTED_KPIS = 9
EXPECTED_DAX = 20
EXPECTED_SCENARIOS_COUNT = 4
EXPECTED_DRILLTHROUGHS = 6
EXPECTED_DECISIONS = 7


# =============================================================================
# QA ENGINE
# =============================================================================

qa = []
findings = []


def add_qa(
    test_id,
    area,
    test,
    expected,
    actual,
    status,
    severity="INFO",
):
    record = {
        "Test_ID": test_id,
        "Area": area,
        "Test": test,
        "Expected": expected,
        "Actual": actual,
        "Status": status,
        "Severity": severity,
    }

    qa.append(record)

    if status == "FAIL":
        findings.append(record)


def check(actual, expected, tolerance=0.01):
    try:
        return abs(float(actual) - float(expected)) <= tolerance
    except Exception:
        return actual == expected


def norm(value):
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).strip().casefold(),
    )


def find_sheet(required_columns):
    required = {norm(c) for c in required_columns}

    for name, df in workbook.items():
        actual = {norm(c) for c in df.columns}

        if required.issubset(actual):
            return name, df

    return None, pd.DataFrame()


# =============================================================================
# 1. FILE INTEGRITY
# =============================================================================

add_qa(
    "DEP-001",
    "Deployment",
    "SQLite database exists",
    "PRESENT",
    "PRESENT" if DB_PATH.exists() else "MISSING",
    "PASS" if DB_PATH.exists() else "FAIL",
    "CRITICAL",
)

add_qa(
    "DEP-002",
    "Deployment",
    "Stage 2G.20.1 workbook exists",
    "PRESENT",
    "PRESENT" if INPUT_XLSX.exists() else "MISSING",
    "PASS" if INPUT_XLSX.exists() else "FAIL",
    "CRITICAL",
)

if not DB_PATH.exists():
    raise FileNotFoundError(DB_PATH)

if not INPUT_XLSX.exists():
    raise FileNotFoundError(INPUT_XLSX)


# =============================================================================
# 2. SQLITE SOURCE VALIDATION
# =============================================================================

conn = sqlite3.connect(DB_PATH)

db_tables_df = pd.read_sql_query(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name
    """,
    conn,
)

db_tables = set(db_tables_df["name"])

required_source_tables = {
    "Dim_Date",
    "Dim_Well",
    "Dim_Rig",
    "Fact_Drilling_Daily_Report",
    "Fact_NPT",
}

for table in sorted(required_source_tables):

    status = (
        "PASS"
        if table in db_tables
        else "FAIL"
    )

    add_qa(
        "SRC-001",
        "Source Integrity",
        f"Source table: {table}",
        "PRESENT",
        "PRESENT" if status == "PASS" else "MISSING",
        status,
        "CRITICAL" if status == "FAIL" else "INFO",
    )


npt = pd.read_sql_query(
    "SELECT * FROM Fact_NPT",
    conn,
)

drilling = pd.read_sql_query(
    "SELECT * FROM Fact_Drilling_Daily_Report",
    conn,
)

wells = pd.read_sql_query(
    "SELECT * FROM Dim_Well",
    conn,
)

rigs = pd.read_sql_query(
    "SELECT * FROM Dim_Rig",
    conn,
)

conn.close()


# =============================================================================
# 3. EXECUTIVE BASELINE
# =============================================================================

source_values = {
    "NPT Events": len(npt),
    "NPT Hours": npt["Duration_hr"].sum(),
    "Direct NPT Cost": npt["Cost_USD"].sum(),
    "Deferred Cost": npt["Deferred_Cost_USD"].sum(),
    "Total Economic Impact": npt["Total_Impact_USD"].sum(),
    "Well Count": wells["Well_ID"].nunique(),
    "Rig Count": rigs["Rig_ID"].nunique(),
    "Drilling Days": drilling["Date"].nunique(),
    "Total Footage": drilling["Daily_Footage_ft"].sum(),
    "Average ROP": drilling["ROP_ft_hr"].mean(),
}

expected_values = {
    "NPT Events": EXPECTED["npt_events"],
    "NPT Hours": EXPECTED["npt_hours"],
    "Direct NPT Cost": EXPECTED["direct_cost"],
    "Deferred Cost": EXPECTED["deferred_cost"],
    "Total Economic Impact": EXPECTED["total_impact"],
    "Well Count": EXPECTED["wells"],
    "Rig Count": EXPECTED["rigs"],
    "Drilling Days": EXPECTED["drilling_days"],
    "Total Footage": EXPECTED["footage"],
    "Average ROP": EXPECTED["avg_rop"],
}

for index, label in enumerate(source_values, start=1):

    tolerance = 0 if label in {
        "NPT Events",
        "Well Count",
        "Rig Count",
        "Drilling Days",
    } else 0.01

    actual = source_values[label]
    expected = expected_values[label]

    status = (
        "PASS"
        if check(actual, expected, tolerance)
        else "FAIL"
    )

    add_qa(
        f"BASE-{index:03d}",
        "Executive Baseline",
        label,
        expected,
        round(float(actual), 4),
        status,
        "CRITICAL" if status == "FAIL" else "INFO",
    )


total_footage = float(
    drilling["Daily_Footage_ft"].sum()
)

cost_per_foot = (
    float(drilling["Daily_Cost_USD"].sum())
    / total_footage
)

add_qa(
    "BASE-011",
    "Executive Baseline",
    "Cost per Foot",
    EXPECTED["cost_per_foot"],
    round(cost_per_foot, 4),
    "PASS"
    if check(
        cost_per_foot,
        EXPECTED["cost_per_foot"],
        0.01,
    )
    else "FAIL",
    "CRITICAL",
)


# =============================================================================
# 4. LOAD 2G.20.1 REMEDIATION WORKBOOK
# =============================================================================

xls = pd.ExcelFile(INPUT_XLSX)

workbook = {}

for sheet in xls.sheet_names:
    workbook[sheet] = pd.read_excel(
        INPUT_XLSX,
        sheet_name=sheet,
    )

dashboard_xls = pd.ExcelFile(DASHBOARD_INPUT_XLSX)

dashboard_workbook = {}

for sheet in dashboard_xls.sheet_names:
    dashboard_workbook[sheet] = pd.read_excel(
        DASHBOARD_INPUT_XLSX,
        sheet_name=sheet
    )


intelligence_xls = pd.ExcelFile(
    INTELLIGENCE_INPUT_XLSX
)

intelligence_workbook = {}

for sheet in intelligence_xls.sheet_names:
    intelligence_workbook[sheet] = pd.read_excel(
        INTELLIGENCE_INPUT_XLSX,
        sheet_name=sheet
    )

add_qa(
    "REM-001",
    "Remediation Package",
    "Workbook readable",
    "YES",
    "YES",
    "PASS",
    "INFO",
)


# =============================================================================
# 5. DISCOVER SEMANTIC ARTIFACTS
# =============================================================================

fact_sheet, fact_pbi = find_sheet(
    [
        "Target_Savings_USD",
        "Savings_At_Risk_USD",
        "Initiative_ID",
        "Initiative_Name",
        "Risk_Factor",
        "Action_Status_Normalized",
    ]
)

scenario_sheet, scenario_df = find_sheet(
    [
        "Scenario_ID",
        "Scenario_Name",
    ]
)

kpi_sheet, kpi_df = find_sheet(
    [
        "KPI_ID",
        "KPI_Name",
    ]
)

dax_sheet, dax_df = find_sheet(
    [
        "Measure_ID",
        "Measure_Name",
    ]
)

table_sheet, table_df = find_sheet(
    [
        "Table_Name",
    ]
)

relationship_sheet, relationship_df = find_sheet(
    [
        "From_Table",
        "To_Table",
    ]
)

# Dashboard architecture comes from Stage 2G.19
visual_sheet = "Visual_Specification"

if visual_sheet in dashboard_workbook:
    visual_df = dashboard_workbook[visual_sheet].copy()
else:
    visual_df = pd.DataFrame()


drill_sheet = "Drillthrough"

if drill_sheet in dashboard_workbook:
    drill_df = dashboard_workbook[drill_sheet].copy()
else:
    drill_df = pd.DataFrame()


# Decision architecture comes from Stage 2G.17
decision_sheet = "Decision_Matrix"

if decision_sheet in intelligence_workbook:
    decision_df = intelligence_workbook[
        decision_sheet
    ].copy()
else:
    decision_df = pd.DataFrame()


# =============================================================================
# 6. POWER BI FACT VALIDATION
# =============================================================================

required_fact_columns = [
    "Target_Savings_USD",
    "Savings_At_Risk_USD",
    "Initiative_ID",
    "Initiative_Name",
    "Risk_Factor",
    "Action_Status_Normalized",
]

if fact_pbi.empty:

    add_qa(
        "FACT-001",
        "Power BI Fact",
        "Fact_NPT_PBI discovered",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "CRITICAL",
    )

else:

    for column in required_fact_columns:

        status = (
            "PASS"
            if column in fact_pbi.columns
            else "FAIL"
        )

        add_qa(
            "FACT-002",
            "Power BI Fact",
            f"Required column: {column}",
            "PRESENT",
            "PRESENT" if status == "PASS" else "MISSING",
            status,
            "CRITICAL" if status == "FAIL" else "INFO",
        )


    add_qa(
        "FACT-003",
        "Power BI Fact",
        "Fact_NPT_PBI row count",
        EXPECTED["npt_events"],
        len(fact_pbi),
        "PASS"
        if len(fact_pbi) == EXPECTED["npt_events"]
        else "FAIL",
        "CRITICAL",
    )


    if "NPT_ID" in fact_pbi.columns:

        duplicates = int(
            fact_pbi["NPT_ID"].duplicated().sum()
        )

    else:

        duplicates = -1


    add_qa(
        "FACT-004",
        "Power BI Fact",
        "Duplicate NPT_ID",
        0,
        duplicates,
        "PASS"
        if duplicates == 0
        else "FAIL",
        "CRITICAL",
    )


    for column in required_fact_columns:

        if column in fact_pbi.columns:

            nulls = int(
                fact_pbi[column].isna().sum()
            )

            add_qa(
                "FACT-005",
                "Power BI Fact",
                f"Null check: {column}",
                0,
                nulls,
                "PASS"
                if nulls == 0
                else "FAIL",
                "CRITICAL"
                if nulls > 0
                else "INFO",
            )


# =============================================================================
# 7. ECONOMIC RECONCILIATION
# =============================================================================

if not fact_pbi.empty:

    target_savings = float(
        fact_pbi["Target_Savings_USD"].sum()
    )

    savings_risk = float(
        fact_pbi["Savings_At_Risk_USD"].sum()
    )

    add_qa(
        "ECO-001",
        "Economic Reconciliation",
        "Target savings",
        EXPECTED["target_savings"],
        round(target_savings, 2),
        "PASS"
        if check(
            target_savings,
            EXPECTED["target_savings"],
            0.01,
        )
        else "FAIL",
        "CRITICAL",
    )

    add_qa(
        "ECO-002",
        "Economic Reconciliation",
        "Savings at risk",
        EXPECTED["savings_at_risk"],
        round(savings_risk, 2),
        "PASS"
        if check(
            savings_risk,
            EXPECTED["savings_at_risk"],
            1.00,
        )
        else "FAIL",
        "CRITICAL",
    )


# =============================================================================
# 8. INITIATIVE RECONCILIATION
# =============================================================================

initiative_reconciliation = pd.DataFrame()

if not fact_pbi.empty:

    initiative_reconciliation = (
        fact_pbi
        .groupby(
            ["Initiative_ID", "Initiative_Name"],
            as_index=False,
        )
        .agg(
            Events=("NPT_ID", "count"),
            NPT_Hours=("Duration_hr", "sum"),
            Target_Savings_USD=(
                "Target_Savings_USD",
                "sum",
            ),
        )
    )

    for initiative_id, expected in EXPECTED_INITIATIVES.items():

        rows = initiative_reconciliation[
            initiative_reconciliation["Initiative_ID"]
            == initiative_id
        ]

        if rows.empty:

            status = "FAIL"
            actual = "MISSING"

        else:

            row = rows.iloc[0]

            actual = (
                int(row["Events"]),
                round(float(row["NPT_Hours"]), 1),
                round(float(row["Target_Savings_USD"]), 2),
            )

            status = (
                "PASS"
                if actual[0] == expected[0]
                and check(actual[1], expected[1])
                and check(actual[2], expected[2], 1.00)
                else "FAIL"
            )

        add_qa(
            f"INIT-{initiative_id.split('-')[1]}",
            "Initiative Architecture",
            f"Initiative reconciliation: {initiative_id}",
            expected,
            actual,
            status,
            "CRITICAL" if status == "FAIL" else "INFO",
        )


    initiative_count = int(
        fact_pbi["Initiative_ID"].nunique()
    )

    add_qa(
        "INIT-002",
        "Initiative Architecture",
        "Initiative count",
        6,
        initiative_count,
        "PASS"
        if initiative_count == 6
        else "FAIL",
        "CRITICAL",
    )


# =============================================================================
# 9. SCENARIO ARCHITECTURE
# =============================================================================

if scenario_df.empty:

    add_qa(
        "SCN-001",
        "Scenario Architecture",
        "Scenario table",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "CRITICAL",
    )

else:

    add_qa(
        "SCN-002",
        "Scenario Architecture",
        "Scenario count",
        EXPECTED_SCENARIOS_COUNT,
        len(scenario_df),
        "PASS"
        if len(scenario_df) == EXPECTED_SCENARIOS_COUNT
        else "FAIL",
        "CRITICAL",
    )

    scenario_id_col = next(
        (
            c
            for c in scenario_df.columns
            if norm(c) == "scenarioid"
        ),
        None,
    )

    scenario_name_col = next(
        (
            c
            for c in scenario_df.columns
            if norm(c) == "scenarioname"
        ),
        None,
    )

    if scenario_id_col and scenario_name_col:

        for scenario_id, expected in EXPECTED_SCENARIOS.items():

            rows = scenario_df[
                scenario_df[scenario_id_col].astype(str)
                == scenario_id
            ]

            if rows.empty:

                actual = "MISSING"
                status = "FAIL"

            else:

                actual = str(
                    rows.iloc[0][scenario_name_col]
                )

                status = (
                    "PASS"
                    if actual == expected[0]
                    else "FAIL"
                )

            add_qa(
                "SCN-003",
                "Scenario Architecture",
                f"Scenario definition: {scenario_id}",
                expected[0],
                actual,
                status,
                "CRITICAL" if status == "FAIL" else "INFO",
            )


# =============================================================================
# 10. KPI ARCHITECTURE
# =============================================================================

if kpi_df.empty:

    add_qa(
        "KPI-001",
        "KPI Architecture",
        "KPI catalog",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "CRITICAL",
    )

else:

    add_qa(
        "KPI-002",
        "KPI Architecture",
        "KPI count",
        EXPECTED_KPIS,
        len(kpi_df),
        "PASS"
        if len(kpi_df) == EXPECTED_KPIS
        else "FAIL",
        "CRITICAL",
    )


# =============================================================================
# 11. DAX ARCHITECTURE
# =============================================================================

if dax_df.empty:

    add_qa(
        "DAX-001",
        "DAX Architecture",
        "DAX catalog",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "CRITICAL",
    )

else:

    add_qa(
        "DAX-002",
        "DAX Architecture",
        "DAX measure count",
        EXPECTED_DAX,
        len(dax_df),
        "PASS"
        if len(dax_df) == EXPECTED_DAX
        else "FAIL",
        "CRITICAL",
    )

    dax_text = "\n".join(
        dax_df.astype(str)
        .fillna("")
        .agg(" | ".join, axis=1)
        .tolist()
    )

    for field in required_fact_columns:

        referenced = field in dax_text

        physically_present = (
            not fact_pbi.empty
            and field in fact_pbi.columns
        )

        status = (
            "PASS"
            if not referenced or physically_present
            else "FAIL"
        )

        add_qa(
            "DAX-003",
            "DAX Dependency Integrity",
            f"DAX dependency: {field}",
            "VALID",
            "VALID" if status == "PASS" else "BROKEN",
            status,
            "CRITICAL" if status == "FAIL" else "INFO",
        )


# =============================================================================
# 12. SEMANTIC TABLES
# =============================================================================

if table_df.empty:

    add_qa(
        "SEM-001",
        "Semantic Model",
        "Semantic table catalog",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "CRITICAL",
    )

else:

    table_col = next(
        (
            c
            for c in table_df.columns
            if norm(c) == "tablename"
        ),
        None,
    )

    actual_tables = set()

    if table_col:

        actual_tables = set(
            table_df[table_col]
            .dropna()
            .astype(str)
            .str.strip()
        )

    missing = EXPECTED_TABLES - actual_tables

    add_qa(
        "SEM-002",
        "Semantic Model",
        "Semantic table set",
        sorted(EXPECTED_TABLES),
        sorted(actual_tables),
        "PASS"
        if actual_tables == EXPECTED_TABLES
        else "FAIL",
        "CRITICAL",
    )


# =============================================================================
# 13. RELATIONSHIPS
# =============================================================================

if relationship_df.empty:

    add_qa(
        "REL-001",
        "Relationship Architecture",
        "Relationship catalog",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "CRITICAL",
    )

else:

    from_col = next(
        (
            c
            for c in relationship_df.columns
            if norm(c) == "fromtable"
        ),
        None,
    )

    to_col = next(
        (
            c
            for c in relationship_df.columns
            if norm(c) == "totable"
        ),
        None,
    )

    actual_relationships = set()

    if from_col and to_col:

        for _, row in relationship_df.iterrows():

            actual_relationships.add(
                (
                    str(row[from_col]).strip(),
                    str(row[to_col]).strip(),
                )
            )

    add_qa(
        "REL-002",
        "Relationship Architecture",
        "Relationship count",
        len(EXPECTED_RELATIONSHIPS),
        len(actual_relationships),
        "PASS"
        if actual_relationships == EXPECTED_RELATIONSHIPS
        else "FAIL",
        "CRITICAL",
    )

    missing_relationships = (
        EXPECTED_RELATIONSHIPS
        - actual_relationships
    )

    add_qa(
        "REL-003",
        "Relationship Architecture",
        "Required relationships",
        "ALL PRESENT",
        "ALL PRESENT"
        if not missing_relationships
        else sorted(missing_relationships),
        "PASS"
        if not missing_relationships
        else "FAIL",
        "CRITICAL",
    )


# =============================================================================
# 14. DASHBOARD / DRILL-THROUGH / DECISION ARCHITECTURE
# =============================================================================

if visual_df.empty:

    add_qa(
        "UI-001",
        "Dashboard Architecture",
        "Visual specification catalog",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "HIGH",
    )

else:

    add_qa(
        "UI-002",
        "Dashboard Architecture",
        "Visual specifications",
        "PRESENT",
        len(visual_df),
        "PASS",
        "INFO",
    )


if drill_df.empty:

    add_qa(
        "UI-003",
        "Drill-through Architecture",
        "Drill-through catalog",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "HIGH",
    )

else:

    add_qa(
        "UI-004",
        "Drill-through Architecture",
        "Drill-through count",
        EXPECTED_DRILLTHROUGHS,
        len(drill_df),
        "PASS"
        if len(drill_df) == EXPECTED_DRILLTHROUGHS
        else "FAIL",
        "HIGH",
    )


if decision_df.empty:

    add_qa(
        "UI-005",
        "Decision Architecture",
        "Decision rule catalog",
        "PRESENT",
        "NOT FOUND",
        "FAIL",
        "HIGH",
    )

else:

    add_qa(
        "UI-006",
        "Decision Architecture",
        "Decision rule count",
        EXPECTED_DECISIONS,
        len(decision_df),
        "PASS"
        if len(decision_df) == EXPECTED_DECISIONS
        else "FAIL",
        "HIGH",
    )


# =============================================================================
# 15. FINAL DEPLOYMENT GATES
# =============================================================================

qa_df = pd.DataFrame(qa)

critical_failures = int(
    (
        (qa_df["Status"] == "FAIL")
        & (qa_df["Severity"] == "CRITICAL")
    ).sum()
)

high_failures = int(
    (
        (qa_df["Status"] == "FAIL")
        & (qa_df["Severity"] == "HIGH")
    ).sum()
)

medium_failures = int(
    (
        (qa_df["Status"] == "FAIL")
        & (qa_df["Severity"] == "MEDIUM")
    ).sum()
)

low_failures = int(
    (
        (qa_df["Status"] == "FAIL")
        & (qa_df["Severity"] == "LOW")
    ).sum()
)


overall_status = (
    "PASS"
    if (
        critical_failures == 0
        and high_failures == 0
        and medium_failures == 0
        and low_failures == 0
    )
    else "FAIL"
)

final_release = (
    "READY"
    if overall_status == "PASS"
    else "NOT READY"
)


# =============================================================================
# 16. DEPLOYMENT GATE SUMMARY
# =============================================================================

def area_status(areas):

    rows = qa_df[
        qa_df["Area"].isin(areas)
    ]

    if rows.empty:
        return "FAIL"

    return (
        "PASS"
        if (rows["Status"] == "PASS").all()
        else "FAIL"
    )


deployment_gates = pd.DataFrame(
    [
        [
            "DG-001",
            "Source integrity",
            area_status(["Source Integrity"]),
        ],
        [
            "DG-002",
            "Economic reconciliation",
            area_status(["Economic Reconciliation"]),
        ],
        [
            "DG-003",
            "Power BI enriched fact",
            area_status(["Power BI Fact"]),
        ],
        [
            "DG-004",
            "DAX dependency integrity",
            area_status(["DAX Dependency Integrity"]),
        ],
        [
            "DG-005",
            "Scenario architecture",
            area_status(["Scenario Architecture"]),
        ],
        [
            "DG-006",
            "KPI architecture",
            area_status(["KPI Architecture"]),
        ],
        [
            "DG-007",
            "Semantic table architecture",
            area_status(["Semantic Model"]),
        ],
        [
            "DG-008",
            "Relationship architecture",
            area_status(["Relationship Architecture"]),
        ],
        [
            "DG-009",
            "Dashboard / drill-through / decision architecture",
            area_status(
                [
                    "Dashboard Architecture",
                    "Drill-through Architecture",
                    "Decision Architecture",
                ]
            ),
        ],
        [
            "DG-010",
            "Executive baseline",
            area_status(["Executive Baseline"]),
        ],
    ],
    columns=[
        "Gate_ID",
        "Gate",
        "Status",
    ],
)


# =============================================================================
# 17. SUMMARY
# =============================================================================

summary = pd.DataFrame(
    [
        ["Overall QA Status", overall_status],
        ["Final Release", final_release],
        ["Critical Failures", critical_failures],
        ["High Failures", high_failures],
        ["Medium Failures", medium_failures],
        ["Low Failures", low_failures],
        ["NPT Events", EXPECTED["npt_events"]],
        ["NPT Hours", EXPECTED["npt_hours"]],
        ["Direct NPT Cost", EXPECTED["direct_cost"]],
        ["Deferred Cost", EXPECTED["deferred_cost"]],
        ["Total Economic Impact", EXPECTED["total_impact"]],
        ["Target Savings", EXPECTED["target_savings"]],
        ["Savings At Risk", EXPECTED["savings_at_risk"]],
        ["Power BI Fact Columns", len(required_fact_columns)],
        ["Initiatives", 6],
        ["Scenario Cases", EXPECTED_SCENARIOS_COUNT],
        ["KPI Definitions", EXPECTED_KPIS],
        ["DAX Measures", EXPECTED_DAX],
        ["Semantic Tables", len(EXPECTED_TABLES)],
        ["Relationships", len(EXPECTED_RELATIONSHIPS)],
    ],
    columns=["Metric", "Value"],
)


# =============================================================================
# 18. EXPORT
# =============================================================================

with pd.ExcelWriter(
    OUTPUT_XLSX,
    engine="openpyxl",
) as writer:

    summary.to_excel(
        writer,
        sheet_name="Deployment_Summary",
        index=False,
    )

    qa_df.to_excel(
        writer,
        sheet_name="QA_Results",
        index=False,
    )

    deployment_gates.to_excel(
        writer,
        sheet_name="Deployment_Gates",
        index=False,
    )

    pd.DataFrame(findings).to_excel(
        writer,
        sheet_name="Findings",
        index=False,
    )

    if not initiative_reconciliation.empty:

        initiative_reconciliation.to_excel(
            writer,
            sheet_name="Initiative_Reconciliation",
            index=False,
        )

    db_tables_df.to_excel(
        writer,
        sheet_name="Source_Tables",
        index=False,
    )


# =============================================================================
# 19. CONSOLE OUTPUT
# =============================================================================

print("=" * 88)
print(
    "STAGE 2G.20.2 — "
    "POWER BI SEMANTIC QA & DEPLOYMENT VALIDATION"
)
print("=" * 88)

print()
print("--- DEPLOYMENT STATUS ---")
print(
    f"Overall QA Status            : {overall_status}"
)
print(
    f"Final Release                : {final_release}"
)
print(
    f"Critical Failures            : {critical_failures}"
)
print(
    f"High Failures                : {high_failures}"
)
print(
    f"Medium Failures              : {medium_failures}"
)
print(
    f"Low Failures                 : {low_failures}"
)

print()
print("--- EXECUTIVE BASELINE ---")
print(
    f"NPT Events                   : "
    f"{EXPECTED['npt_events']:,}"
)
print(
    f"NPT Hours                    : "
    f"{EXPECTED['npt_hours']:,.0f}"
)
print(
    f"Direct NPT Cost              : "
    f"${EXPECTED['direct_cost']:,.0f}"
)
print(
    f"Deferred Cost                : "
    f"${EXPECTED['deferred_cost']:,.0f}"
)
print(
    f"Total Economic Impact        : "
    f"${EXPECTED['total_impact']:,.0f}"
)
print(
    f"Target Savings               : "
    f"${EXPECTED['target_savings']:,.0f}"
)
print(
    f"Savings At Risk              : "
    f"${EXPECTED['savings_at_risk']:,.0f}"
)

print()
print("--- SEMANTIC VALIDATION ---")
print(
    f"Power BI Fact Columns        : "
    f"{len(required_fact_columns)}"
)
print(
    f"Initiatives                  : 6"
)
print(
    f"Scenario Cases               : "
    f"{EXPECTED_SCENARIOS}"
)
print(
    f"KPI Definitions              : "
    f"{EXPECTED_KPIS}"
)
print(
    f"DAX Measures                 : "
    f"{EXPECTED_DAX}"
)
print(
    f"Semantic Tables              : "
    f"{len(EXPECTED_TABLES)}"
)
print(
    f"Relationships                : "
    f"{len(EXPECTED_RELATIONSHIPS)}"
)

print()
print("--- DEPLOYMENT GATES ---")

for _, row in deployment_gates.iterrows():

    print(
        f"{row['Gate_ID']} | "
        f"{row['Gate']} | "
        f"{row['Status']}"
    )

if findings:

    print()
    print("--- FINDINGS ---")

    for finding in findings:

        print(
            f"{finding['Test_ID']} | "
            f"{finding['Severity']} | "
            f"{finding['Area']} | "
            f"{finding['Test']}"
        )

print()
print("--- OUTPUT ---")
print(OUTPUT_XLSX)

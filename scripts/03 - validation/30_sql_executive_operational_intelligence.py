import os
import sqlite3
import pandas as pd
import numpy as np


# =============================================================================
# STAGE 2G.17
# EXECUTIVE OPERATIONAL INTELLIGENCE
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
    "sql_stage_2G.17_Executive_Operational_Intelligence"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "sql_stage_2G.17_Executive_Operational_Intelligence.xlsx"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


print("=" * 90)
print("STAGE 2G.17 — EXECUTIVE OPERATIONAL INTELLIGENCE")
print("=" * 90)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")


# =============================================================================
# 1. VALIDATED BASELINE
# =============================================================================

VALIDATED_NPT_EVENTS = 677
VALIDATED_NPT_HOURS = 4008
VALIDATED_DIRECT_COST = 79204408.0
VALIDATED_DEFERRED_COST = 118945770.0
VALIDATED_TOTAL_IMPACT = 198150178.0

VALIDATED_CONSERVATIVE_SAVINGS = 15412920.0
VALIDATED_TARGET_SAVINGS = 30825850.0
VALIDATED_STRETCH_SAVINGS = 46238770.0

TARGET_SAVINGS_RATE = (
    VALIDATED_TARGET_SAVINGS /
    VALIDATED_TOTAL_IMPACT
)


# =============================================================================
# 2. LOAD DATABASE
# =============================================================================

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(
        f"Database not found: {DB_PATH}"
    )

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


print("\nDATABASE LOADED")
print("-" * 90)
print(f"NPT rows      : {len(fact_npt):,}")
print(f"Drilling rows : {len(fact_drilling):,}")
print(f"Wells         : {len(dim_well):,}")
print(f"Rigs          : {len(dim_rig):,}")
print(f"Dates         : {len(dim_date):,}")


# =============================================================================
# 3. NUMERIC STANDARDIZATION
# =============================================================================

for col in [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Lost_Drilling_Days",
    "Productivity_Loss_pct"
]:

    if col in fact_npt.columns:

        fact_npt[col] = pd.to_numeric(
            fact_npt[col],
            errors="coerce"
        ).fillna(0)


for col in [
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Daily_Cost_USD",
    "Weather_Delay_hr"
]:

    if col in fact_drilling.columns:

        fact_drilling[col] = pd.to_numeric(
            fact_drilling[col],
            errors="coerce"
        ).fillna(0)


# =============================================================================
# 4. EVENT-LEVEL ECONOMIC METRICS
# =============================================================================

fact_npt["Target_Savings_USD"] = (
    fact_npt["Total_Impact_USD"] *
    TARGET_SAVINGS_RATE
)


# =============================================================================
# 5. INITIATIVE CLASSIFICATION
# =============================================================================

conditions = [

    (
        fact_npt["NPT_Category"].eq("Drilling")
        &
        ~fact_npt["Root_Cause"].eq("Bit Wear")
    ),

    fact_npt["NPT_Category"].eq("Mechanical"),

    fact_npt["NPT_Category"].eq("Weather"),

    fact_npt["NPT_Category"].eq("Logistics"),

    fact_npt["NPT_Category"].eq("Personnel"),

    fact_npt["Root_Cause"].eq("Bit Wear")
]

choices = [
    "INIT-001",
    "INIT-002",
    "INIT-003",
    "INIT-004",
    "INIT-005",
    "INIT-006"
]

fact_npt["Initiative_ID"] = np.select(
    conditions,
    choices,
    default="INIT-001"
)


initiative_names = {

    "INIT-001":
        "Drilling Dysfunction Reduction Program",

    "INIT-002":
        "Mechanical Reliability Program",

    "INIT-003":
        "Weather & Marine Operations Resilience",

    "INIT-004":
        "Supply Chain & Logistics Optimization",

    "INIT-005":
        "People, Competency & Operational Readiness",

    "INIT-006":
        "Drilling Performance Optimization"
}

fact_npt["Initiative_Name"] = (
    fact_npt["Initiative_ID"].map(
        initiative_names
    )
)


# =============================================================================
# 6. ACTION / SAVINGS RISK
# =============================================================================

fact_npt["Action_Status_Normalized"] = (
    fact_npt["Action_Status"]
    .fillna("Unknown")
    .astype(str)
    .str.strip()
    .str.title()
)

risk_factor_map = {

    "Open": 1.00,

    "In Progress": 0.50,

    "Closed": 0.00,

    "Unknown": 0.75
}

fact_npt["Savings_Risk_Factor"] = (
    fact_npt["Action_Status_Normalized"]
    .map(risk_factor_map)
    .fillna(0.75)
)

fact_npt["Savings_At_Risk_USD"] = (
    fact_npt["Target_Savings_USD"] *
    fact_npt["Savings_Risk_Factor"]
)


# =============================================================================
# 7. EXECUTIVE KPI DICTIONARY
# =============================================================================

kpi_dictionary = pd.DataFrame(
    [

        [
            "KPI-001",
            "NPT Hours",
            "SUM(Fact_NPT[Duration_hr])",
            "Hours",
            "MINIMIZE",
            3000,
            "RED if > target × 1.10",
            "Lagging",
            "Executive"
        ],

        [
            "KPI-002",
            "Direct NPT Cost",
            "SUM(Fact_NPT[Cost_USD])",
            "USD",
            "MINIMIZE",
            60000000,
            "RED if > target × 1.10",
            "Lagging",
            "Executive"
        ],

        [
            "KPI-003",
            "Total Economic Impact",
            "SUM(Fact_NPT[Total_Impact_USD])",
            "USD",
            "MINIMIZE",
            150000000,
            "RED if > target × 1.10",
            "Lagging",
            "Executive"
        ],

        [
            "KPI-004",
            "Average ROP",
            "AVERAGE(Fact_Drilling_Daily_Report[ROP_ft_hr])",
            "ft/hr",
            "MAXIMIZE",
            35,
            "RED if < target × 0.95",
            "Leading",
            "Executive"
        ],

        [
            "KPI-005",
            "Cost per Foot",
            "SUM(Daily_Cost_USD) / SUM(Daily_Footage_ft)",
            "USD/ft",
            "MINIMIZE",
            600,
            "RED if > target × 1.10",
            "Lagging",
            "Executive"
        ],

        [
            "KPI-006",
            "Target Savings",
            "SUM(Target_Savings_USD)",
            "USD",
            "MAXIMIZE",
            VALIDATED_TARGET_SAVINGS,
            "RED if < target × 0.95",
            "Leading",
            "Executive"
        ],

        [
            "KPI-007",
            "Savings At Risk",
            "SUM(Savings_At_Risk_USD)",
            "USD",
            "MINIMIZE",
            VALIDATED_TARGET_SAVINGS * 0.20,
            "RED if > target",
            "Leading",
            "Executive"
        ],

        [
            "KPI-008",
            "NPT Event Count",
            "COUNT(Fact_NPT[NPT_ID])",
            "Events",
            "MINIMIZE",
            500,
            "Management threshold",
            "Lagging",
            "Management"
        ],

        [
            "KPI-009",
            "NPT Hours per Drilling Day",
            "NPT Hours / Drilling Days",
            "hr/day",
            "MINIMIZE",
            5,
            "Management threshold",
            "Leading",
            "Management"
        ]

    ],
    columns=[
        "KPI_ID",
        "KPI_Name",
        "Definition",
        "Unit",
        "Direction",
        "Target",
        "Status_Rule",
        "Indicator_Type",
        "Audience"
    ]
)


# =============================================================================
# 8. KPI CURRENT VALUES
# =============================================================================

npt_events = len(fact_npt)

npt_hours = fact_npt["Duration_hr"].sum()

direct_cost = fact_npt["Cost_USD"].sum()

deferred_cost = fact_npt["Deferred_Cost_USD"].sum()

total_impact = fact_npt["Total_Impact_USD"].sum()

target_savings = fact_npt["Target_Savings_USD"].sum()

savings_at_risk = fact_npt["Savings_At_Risk_USD"].sum()

drilling_days = fact_drilling["Date"].nunique()

total_footage = fact_drilling["Daily_Footage_ft"].sum()

avg_rop = fact_drilling["ROP_ft_hr"].mean()

cost_per_ft = (
    fact_drilling["Daily_Cost_USD"].sum() /
    total_footage
)

npt_hours_per_day = (
    npt_hours /
    drilling_days
)


def minimize_status(actual, target):

    if actual <= target:
        return "GREEN"

    if actual <= target * 1.10:
        return "AMBER"

    return "RED"


def maximize_status(actual, target):

    if actual >= target:
        return "GREEN"

    if actual >= target * 0.95:
        return "AMBER"

    return "RED"


kpi_values = pd.DataFrame(
    [

        [
            "KPI-001",
            "NPT Hours",
            npt_hours,
            3000,
            minimize_status(
                npt_hours,
                3000
            )
        ],

        [
            "KPI-002",
            "Direct NPT Cost",
            direct_cost,
            60000000,
            minimize_status(
                direct_cost,
                60000000
            )
        ],

        [
            "KPI-003",
            "Total Economic Impact",
            total_impact,
            150000000,
            minimize_status(
                total_impact,
                150000000
            )
        ],

        [
            "KPI-004",
            "Average ROP",
            avg_rop,
            35,
            maximize_status(
                avg_rop,
                35
            )
        ],

        [
            "KPI-005",
            "Cost per Foot",
            cost_per_ft,
            600,
            minimize_status(
                cost_per_ft,
                600
            )
        ],

        [
            "KPI-006",
            "Target Savings",
            target_savings,
            VALIDATED_TARGET_SAVINGS,
            maximize_status(
                target_savings,
                VALIDATED_TARGET_SAVINGS
            )
        ],

        [
            "KPI-007",
            "Savings At Risk",
            savings_at_risk,
            VALIDATED_TARGET_SAVINGS * 0.20,
            minimize_status(
                savings_at_risk,
                VALIDATED_TARGET_SAVINGS * 0.20
            )
        ],

        [
            "KPI-008",
            "NPT Event Count",
            npt_events,
            500,
            minimize_status(
                npt_events,
                500
            )
        ],

        [
            "KPI-009",
            "NPT Hours per Drilling Day",
            npt_hours_per_day,
            5,
            minimize_status(
                npt_hours_per_day,
                5
            )
        ]

    ],
    columns=[
        "KPI_ID",
        "KPI_Name",
        "Actual",
        "Target",
        "Status"
    ]
)


# =============================================================================
# 9. POWER BI DATA MODEL
# =============================================================================

semantic_model = pd.DataFrame(
    [

        [
            "Dim_Date",
            "Dimension",
            "Date",
            "Date_Key",
            "1:*",
            "Fact_Drilling_Daily_Report / Fact_NPT"
        ],

        [
            "Dim_Well",
            "Dimension",
            "Well_ID",
            "Well_ID",
            "1:*",
            "Fact_Drilling_Daily_Report / Fact_NPT"
        ],

        [
            "Dim_Rig",
            "Dimension",
            "Rig_ID",
            "Rig_ID",
            "1:*",
            "Fact_Drilling_Daily_Report / Fact_NPT"
        ],

        [
            "Fact_Drilling_Daily_Report",
            "Fact",
            "Daily drilling performance",
            "Date / Well_ID / Rig_ID",
            "*:1",
            "Dim_Date / Dim_Well / Dim_Rig"
        ],

        [
            "Fact_NPT",
            "Fact",
            "NPT events and economic impact",
            "Date / Well_ID / Rig_ID",
            "*:1",
            "Dim_Date / Dim_Well / Dim_Rig"
        ]

    ],
    columns=[
        "Table_Name",
        "Table_Type",
        "Business_Role",
        "Key",
        "Relationship",
        "Related_Tables"
    ]
)


# =============================================================================
# 10. POWER BI MEASURE CATALOG
# =============================================================================

measure_catalog = pd.DataFrame(
    [

        [
            "M001",
            "NPT Hours",
            "SUM(Fact_NPT[Duration_hr])",
            "Hours",
            "Operational"
        ],

        [
            "M002",
            "NPT Events",
            "COUNTROWS(Fact_NPT)",
            "Events",
            "Operational"
        ],

        [
            "M003",
            "Direct NPT Cost",
            "SUM(Fact_NPT[Cost_USD])",
            "USD",
            "Economic"
        ],

        [
            "M004",
            "Deferred Cost",
            "SUM(Fact_NPT[Deferred_Cost_USD])",
            "USD",
            "Economic"
        ],

        [
            "M005",
            "Total Economic Impact",
            "SUM(Fact_NPT[Total_Impact_USD])",
            "USD",
            "Economic"
        ],

        [
            "M006",
            "Target Savings",
            "SUM(Fact_NPT[Target_Savings_USD])",
            "USD",
            "Economic"
        ],

        [
            "M007",
            "Savings At Risk",
            "SUM(Fact_NPT[Savings_At_Risk_USD])",
            "USD",
            "Economic"
        ],

        [
            "M008",
            "Average ROP",
            "AVERAGE(Fact_Drilling_Daily_Report[ROP_ft_hr])",
            "ft/hr",
            "Performance"
        ],

        [
            "M009",
            "Total Footage",
            "SUM(Fact_Drilling_Daily_Report[Daily_Footage_ft])",
            "ft",
            "Performance"
        ],

        [
            "M010",
            "Cost per Foot",
            "DIVIDE([Daily Cost],[Total Footage])",
            "USD/ft",
            "Performance"
        ],

        [
            "M011",
            "NPT Hours per Drilling Day",
            "DIVIDE([NPT Hours],[Drilling Days])",
            "hr/day",
            "Performance"
        ],

        [
            "M012",
            "Target Savings Rate",
            "DIVIDE([Target Savings],[Total Economic Impact])",
            "%",
            "Economic"
        ],

        [
            "M013",
            "Savings Protection Rate",
            "DIVIDE([Target Savings]-[Savings At Risk],[Target Savings])",
            "%",
            "Economic"
        ],

        [
            "M014",
            "Drilling Days",
            "DISTINCTCOUNT(Fact_Drilling_Daily_Report[Date])",
            "Days",
            "Operational"
        ],

        [
            "M015",
            "Well Count",
            "DISTINCTCOUNT(Fact_NPT[Well_ID])",
            "Wells",
            "Portfolio"
        ],

        [
            "M016",
            "Rig Count",
            "DISTINCTCOUNT(Fact_NPT[Rig_ID])",
            "Rigs",
            "Portfolio"
        ]

    ],
    columns=[
        "Measure_ID",
        "Measure_Name",
        "DAX_Definition",
        "Unit",
        "Domain"
    ]
)


# =============================================================================
# 11. EXECUTIVE DASHBOARD PAGE ARCHITECTURE
# =============================================================================

dashboard_pages = pd.DataFrame(
    [

        [
            1,
            "Executive Command Center",
            "Enterprise",
            "Overall operational status, economic exposure and savings",
            "CEO / VP Operations / Drilling Manager",
            "RED → Immediate action"
        ],

        [
            2,
            "KPI Performance",
            "Performance",
            "Leading and lagging KPI monitoring",
            "Operations Management",
            "KPI status"
        ],

        [
            3,
            "Rig Performance",
            "Asset",
            "Rig exposure, NPT and economic impact",
            "Drilling Management",
            "Rig prioritization"
        ],

        [
            4,
            "Well Risk",
            "Well",
            "Well-level operational and economic risk",
            "Well Engineering",
            "Well prioritization"
        ],

        [
            5,
            "Root Cause Pareto",
            "Root Cause",
            "Economic concentration by root cause",
            "Engineering / Operations",
            "Root-cause elimination"
        ],

        [
            6,
            "Initiative Portfolio",
            "Transformation",
            "Savings opportunity and risk by initiative",
            "Management",
            "Investment priority"
        ],

        [
            7,
            "Savings Protection",
            "Economic",
            "Target savings versus savings at risk",
            "Finance / Operations",
            "Savings realization"
        ],

        [
            8,
            "Scenario Simulator",
            "Scenario",
            "NPT reduction and illustrative impact avoidance",
            "Leadership",
            "Scenario planning"
        ],

        [
            9,
            "Data Quality",
            "Governance",
            "Data completeness and reconciliation",
            "Analytics Governance",
            "Model confidence"
        ]

    ],
    columns=[
        "Page_No",
        "Page_Name",
        "Domain",
        "Purpose",
        "Primary_Audience",
        "Decision_Output"
    ]
)


# =============================================================================
# 12. DRILL-THROUGH ARCHITECTURE
# =============================================================================

drillthrough = pd.DataFrame(
    [

        [
            "Executive Command Center",
            "Rig_ID",
            "Rig Performance",
            "Rig-level exposure and root causes"
        ],

        [
            "Executive Command Center",
            "Well_ID",
            "Well Risk",
            "Well-level NPT and economic exposure"
        ],

        [
            "Executive Command Center",
            "Root_Cause",
            "Root Cause Pareto",
            "Root-cause event detail"
        ],

        [
            "Executive Command Center",
            "Initiative_ID",
            "Initiative Portfolio",
            "Initiative savings and risk"
        ],

        [
            "Rig Performance",
            "Rig_ID",
            "Rig Detail",
            "Detailed rig diagnosis"
        ],

        [
            "Well Risk",
            "Well_ID",
            "Well Detail",
            "Detailed well diagnosis"
        ]

    ],
    columns=[
        "Source_Page",
        "Drillthrough_Field",
        "Target_Page",
        "Purpose"
    ]
)


# =============================================================================
# 13. MANAGEMENT DECISION MATRIX
# =============================================================================

decision_matrix = pd.DataFrame(
    [

        [
            "DEC-001",
            "Economic Exposure",
            "Total Economic Impact",
            "> $150M",
            "RED",
            "Immediate executive intervention"
        ],

        [
            "DEC-002",
            "Rig Exposure",
            "Impact Share",
            ">=25%",
            "RED",
            "Rig recovery plan"
        ],

        [
            "DEC-003",
            "Well Risk",
            "Impact Share",
            ">=2%",
            "CRITICAL",
            "Well-level performance review"
        ],

        [
            "DEC-004",
            "Root Cause",
            "Impact Share",
            ">=5%",
            "CRITICAL",
            "Root-cause elimination"
        ],

        [
            "DEC-005",
            "Savings Risk",
            "Savings At Risk",
            ">=20% target",
            "RED",
            "Action closure escalation"
        ],

        [
            "DEC-006",
            "ROP",
            "Average ROP",
            "<35 ft/hr",
            "RED",
            "Drilling performance review"
        ],

        [
            "DEC-007",
            "Cost Efficiency",
            "Cost per Foot",
            ">600 USD/ft",
            "RED",
            "Cost reduction intervention"
        ]

    ],
    columns=[
        "Decision_ID",
        "Decision_Domain",
        "Metric",
        "Threshold",
        "Severity",
        "Management_Response"
    ]
)


# =============================================================================
# 14. EXECUTIVE NARRATIVE
# =============================================================================

executive_narrative = pd.DataFrame(
    [

        [
            1,
            "Situation",
            "The drilling portfolio contains significant operational and economic exposure.",
            "677 NPT events and $198.15M total economic impact."
        ],

        [
            2,
            "Primary Exposure",
            "Rig R002 represents the largest concentration of economic exposure.",
            "$76.56M impact."
        ],

        [
            3,
            "Technical Driver",
            "Differential Sticking is the largest identified root-cause exposure.",
            "$16.61M impact."
        ],

        [
            4,
            "Largest Initiative",
            "Mechanical reliability provides the largest individual initiative savings opportunity.",
            "$8.13M target savings."
        ],

        [
            5,
            "Savings Risk",
            "A portion of target savings remains exposed because corrective actions are not fully closed.",
            "$6.39M savings at risk."
        ],

        [
            6,
            "Management Priority",
            "Immediate action should focus on the highest-impact rig, root cause and initiative.",
            "R002 / Differential Sticking / INIT-002."
        ]

    ],
    columns=[
        "Sequence",
        "Narrative_Element",
        "Executive_Message",
        "Evidence"
    ]
)


# =============================================================================
# 15. DATA LINEAGE
# =============================================================================

data_lineage = pd.DataFrame(
    [

        [
            "NPT Hours",
            "Fact_NPT",
            "Duration_hr",
            "SUM",
            "Executive KPI"
        ],

        [
            "Direct NPT Cost",
            "Fact_NPT",
            "Cost_USD",
            "SUM",
            "Economic KPI"
        ],

        [
            "Deferred Cost",
            "Fact_NPT",
            "Deferred_Cost_USD",
            "SUM",
            "Economic KPI"
        ],

        [
            "Total Economic Impact",
            "Fact_NPT",
            "Total_Impact_USD",
            "SUM",
            "Executive KPI"
        ],

        [
            "Target Savings",
            "Fact_NPT",
            "Total_Impact_USD",
            "× validated savings rate",
            "Savings KPI"
        ],

        [
            "Average ROP",
            "Fact_Drilling_Daily_Report",
            "ROP_ft_hr",
            "AVERAGE",
            "Performance KPI"
        ],

        [
            "Cost per Foot",
            "Fact_Drilling_Daily_Report",
            "Daily_Cost_USD / Daily_Footage_ft",
            "DIVIDE",
            "Efficiency KPI"
        ],

        [
            "Rig Exposure",
            "Fact_NPT",
            "Rig_ID / Total_Impact_USD",
            "GROUPBY",
            "Asset Intelligence"
        ],

        [
            "Well Risk",
            "Fact_NPT",
            "Well_ID / Total_Impact_USD",
            "GROUPBY",
            "Risk Intelligence"
        ],

        [
            "Root Cause Pareto",
            "Fact_NPT",
            "Root_Cause / Total_Impact_USD",
            "GROUPBY + CUMULATIVE",
            "Root Cause Intelligence"
        ]

    ],
    columns=[
        "Metric",
        "Source_Table",
        "Source_Field",
        "Transformation",
        "Destination"
    ]
)


# =============================================================================
# 16. POWER BI VISUAL SPECIFICATION
# =============================================================================

visual_specification = pd.DataFrame(
    [

        [
            "Executive Command Center",
            "KPI Cards",
            "Total Economic Impact / Target Savings / Savings At Risk / NPT Hours",
            "Top-level exposure"
        ],

        [
            "Executive Command Center",
            "Status Indicator",
            "Overall Status",
            "RED / AMBER / GREEN"
        ],

        [
            "Executive Command Center",
            "Bar Chart",
            "Economic Impact by Rig",
            "Identify dominant rig exposure"
        ],

        [
            "Executive Command Center",
            "Pareto Chart",
            "Economic Impact by Root Cause",
            "Identify dominant technical drivers"
        ],

        [
            "Executive Command Center",
            "Portfolio Chart",
            "Target Savings by Initiative",
            "Investment prioritization"
        ],

        [
            "KPI Performance",
            "KPI Matrix",
            "Actual / Target / Variance / Status",
            "Performance management"
        ],

        [
            "Rig Performance",
            "Heatmap",
            "Rig × Economic Impact / NPT Hours",
            "Asset comparison"
        ],

        [
            "Well Risk",
            "Scatter",
            "Impact vs NPT Hours",
            "Risk segmentation"
        ],

        [
            "Root Cause Pareto",
            "Pareto",
            "Root Cause × Impact × Cumulative %",
            "Root-cause prioritization"
        ],

        [
            "Initiative Portfolio",
            "Bubble Chart",
            "Savings vs Risk",
            "Portfolio prioritization"
        ],

        [
            "Savings Protection",
            "Waterfall",
            "Target Savings → At Risk → Protected",
            "Savings realization"
        ],

        [
            "Scenario Simulator",
            "Scenario Chart",
            "NPT Reduction vs Illustrative Impact Avoided",
            "Decision support"
        ]

    ],
    columns=[
        "Page",
        "Visual_Type",
        "Metric",
        "Purpose"
    ]
)


# =============================================================================
# 17. VALIDATION
# =============================================================================

economic_reconciliation = (
    total_impact -
    VALIDATED_TOTAL_IMPACT
)

target_reconciliation = (
    target_savings -
    VALIDATED_TARGET_SAVINGS
)

dq_rows = [

    [
        "NPT row count",
        npt_events,
        VALIDATED_NPT_EVENTS,
        "PASS"
        if npt_events == VALIDATED_NPT_EVENTS
        else "FAIL"
    ],

    [
        "Drilling row count",
        len(fact_drilling),
        1474,
        "PASS"
        if len(fact_drilling) == 1474
        else "FAIL"
    ],

    [
        "Unique NPT IDs",
        fact_npt["NPT_ID"].nunique(),
        VALIDATED_NPT_EVENTS,
        "PASS"
        if fact_npt["NPT_ID"].nunique()
        == VALIDATED_NPT_EVENTS
        else "FAIL"
    ],

    [
        "Duplicate NPT IDs",
        fact_npt["NPT_ID"].duplicated().sum(),
        0,
        "PASS"
        if fact_npt["NPT_ID"].duplicated().sum() == 0
        else "FAIL"
    ],

    [
        "Economic reconciliation",
        economic_reconciliation,
        0,
        "PASS"
        if abs(economic_reconciliation) < 0.01
        else "FAIL"
    ],

    [
        "Target savings reconciliation",
        target_reconciliation,
        0,
        "PASS"
        if abs(target_reconciliation) < 0.01
        else "FAIL"
    ],

    [
        "Target savings positive",
        target_savings,
        ">0",
        "PASS"
        if target_savings > 0
        else "FAIL"
    ],

    [
        "Rig count",
        fact_npt["Rig_ID"].nunique(),
        4,
        "PASS"
        if fact_npt["Rig_ID"].nunique() == 4
        else "FAIL"
    ],

    [
        "Well count",
        fact_npt["Well_ID"].nunique(),
        50,
        "PASS"
        if fact_npt["Well_ID"].nunique() == 50
        else "FAIL"
    ],

    [
        "Initiative count",
        fact_npt["Initiative_ID"].nunique(),
        6,
        "PASS"
        if fact_npt["Initiative_ID"].nunique() == 6
        else "FAIL"
    ],

    [
        "KPI dictionary",
        len(kpi_dictionary),
        9,
        "PASS"
        if len(kpi_dictionary) == 9
        else "FAIL"
    ],

    [
        "Measure catalog",
        len(measure_catalog),
        16,
        "PASS"
        if len(measure_catalog) == 16
        else "FAIL"
    ],

    [
        "Dashboard pages",
        len(dashboard_pages),
        9,
        "PASS"
        if len(dashboard_pages) == 9
        else "FAIL"
    ]

]

data_quality = pd.DataFrame(
    dq_rows,
    columns=[
        "Check",
        "Actual",
        "Expected",
        "Status"
    ]
)

overall_dq_status = (
    "PASS"
    if (data_quality["Status"] == "PASS").all()
    else "FAIL"
)


# =============================================================================
# 18. EXPORT
# =============================================================================

print("\nEXPORTING EXECUTIVE INTELLIGENCE PACKAGE...")
print("-" * 90)

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    kpi_dictionary.to_excel(
        writer,
        sheet_name="KPI_Dictionary",
        index=False
    )

    kpi_values.to_excel(
        writer,
        sheet_name="KPI_Current_Values",
        index=False
    )

    semantic_model.to_excel(
        writer,
        sheet_name="Semantic_Model",
        index=False
    )

    measure_catalog.to_excel(
        writer,
        sheet_name="Measure_Catalog",
        index=False
    )

    dashboard_pages.to_excel(
        writer,
        sheet_name="Dashboard_Pages",
        index=False
    )

    drillthrough.to_excel(
        writer,
        sheet_name="Drillthrough",
        index=False
    )

    decision_matrix.to_excel(
        writer,
        sheet_name="Decision_Matrix",
        index=False
    )

    executive_narrative.to_excel(
        writer,
        sheet_name="Executive_Narrative",
        index=False
    )

    data_lineage.to_excel(
        writer,
        sheet_name="Data_Lineage",
        index=False
    )

    visual_specification.to_excel(
        writer,
        sheet_name="Visual_Specification",
        index=False
    )

    data_quality.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# =============================================================================
# 19. FINAL REPORT
# =============================================================================

print("\n" + "=" * 90)
print("STAGE 2G.17 — EXECUTIVE OPERATIONAL INTELLIGENCE RESULTS")
print("=" * 90)

print(f"\nData Quality Status           : {overall_dq_status}")

print("\n--- EXECUTIVE BASELINE ---")

print(
    f"NPT Events                    : {npt_events:,}"
)

print(
    f"NPT Hours                     : {npt_hours:,.0f}"
)

print(
    f"Direct NPT Cost               : ${direct_cost:,.0f}"
)

print(
    f"Deferred Cost                 : ${deferred_cost:,.0f}"
)

print(
    f"Total Economic Impact         : ${total_impact:,.0f}"
)

print(
    f"Target Savings                : ${target_savings:,.0f}"
)

print(
    f"Savings At Risk               : ${savings_at_risk:,.0f}"
)

print("\n--- OPERATIONAL PERFORMANCE ---")

print(
    f"Drilling Days                 : {drilling_days:,}"
)

print(
    f"Total Footage                 : {total_footage:,.1f} ft"
)

print(
    f"Average ROP                   : {avg_rop:,.2f} ft/hr"
)

print(
    f"Cost per Foot                 : ${cost_per_ft:,.2f}"
)

print(
    f"NPT Hours / Drilling Day      : {npt_hours_per_day:,.2f}"
)

print("\n--- INTELLIGENCE ARCHITECTURE ---")

print(
    f"KPI Definitions               : {len(kpi_dictionary)}"
)

print(
    f"Power BI Measures             : {len(measure_catalog)}"
)

print(
    f"Dashboard Pages               : {len(dashboard_pages)}"
)

print(
    f"Drill-through Paths           : {len(drillthrough)}"
)

print(
    f"Decision Rules                : {len(decision_matrix)}"
)

print(
    f"Visual Specifications         : {len(visual_specification)}"
)

print("\n--- DATA QUALITY ---")

print(
    data_quality.to_string(index=False)
)

print("\n" + "=" * 90)
print("OUTPUT GENERATED SUCCESSFULLY")
print("=" * 90)

print("\nExcel file:")
print(OUTPUT_FILE)
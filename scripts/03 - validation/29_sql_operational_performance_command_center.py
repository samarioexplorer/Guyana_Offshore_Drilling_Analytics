import os
import sqlite3
import pandas as pd
import numpy as np


# =============================================================================
# STAGE 2G.16
# OPERATIONAL PERFORMANCE COMMAND CENTER
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
    "sql_stage_2G.16_Operational_Performance_Command_Center"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "sql_stage_2G.16_Operational_Performance_Command_Center.xlsx"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


print("=" * 90)
print("STAGE 2G.16 — OPERATIONAL PERFORMANCE COMMAND CENTER")
print("=" * 90)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")


# =============================================================================
# 1. VALIDATED ECONOMIC BASELINE — STAGE 2G.10.1
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
# 2. LOAD SQL DATA
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

conn.close()

print("\nSQL DATA LOADED")
print("-" * 90)
print(f"NPT rows      : {len(fact_npt):,}")
print(f"Drilling rows : {len(fact_drilling):,}")
print(f"Wells         : {len(dim_well):,}")
print(f"Rigs          : {len(dim_rig):,}")


# =============================================================================
# 3. STANDARDIZE NUMERIC FIELDS
# =============================================================================

npt_numeric = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Lost_Drilling_Days",
    "Productivity_Loss_pct"
]

for col in npt_numeric:
    if col in fact_npt.columns:
        fact_npt[col] = pd.to_numeric(
            fact_npt[col],
            errors="coerce"
        ).fillna(0)

drilling_numeric = [
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Daily_Cost_USD",
    "Weather_Delay_hr"
]

for col in drilling_numeric:
    if col in fact_drilling.columns:
        fact_drilling[col] = pd.to_numeric(
            fact_drilling[col],
            errors="coerce"
        ).fillna(0)


# =============================================================================
# 4. EVENT-LEVEL TARGET SAVINGS
# =============================================================================

fact_npt["Target_Savings_USD"] = (
    fact_npt["Total_Impact_USD"] *
    TARGET_SAVINGS_RATE
)


# =============================================================================
# 5. SIX-INITIATIVE ARCHITECTURE
# =============================================================================

# Validated Stage 2G.15 classification:
#
# INIT-001 = Drilling Dysfunction except Bit Wear
# INIT-002 = Mechanical Reliability
# INIT-003 = Weather & Marine
# INIT-004 = Logistics
# INIT-005 = Personnel
# INIT-006 = Bit Wear / Drilling Performance

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
    "INIT-001": "Drilling Dysfunction Reduction Program",
    "INIT-002": "Mechanical Reliability Program",
    "INIT-003": "Weather & Marine Operations Resilience",
    "INIT-004": "Supply Chain & Logistics Optimization",
    "INIT-005": "People, Competency & Operational Readiness",
    "INIT-006": "Drilling Performance Optimization"
}

initiative_priority = {
    "INIT-001": "CRITICAL",
    "INIT-002": "CRITICAL",
    "INIT-003": "CRITICAL",
    "INIT-004": "HIGH",
    "INIT-005": "LOW",
    "INIT-006": "LOW"
}

fact_npt["Initiative_Name"] = (
    fact_npt["Initiative_ID"].map(initiative_names)
)

fact_npt["Initiative_Priority"] = (
    fact_npt["Initiative_ID"].map(initiative_priority)
)


# =============================================================================
# 6. ACTION STATUS / SAVINGS RISK
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
# 7. OPERATIONAL BASELINE
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
    if total_footage > 0
    else 0
)


# =============================================================================
# 8. KPI STATUS FUNCTIONS
# =============================================================================

def minimize_status(actual, target):
    if actual <= target:
        return "GREEN"
    elif actual <= target * 1.10:
        return "AMBER"
    return "RED"


def maximize_status(actual, target):
    if actual >= target:
        return "GREEN"
    elif actual >= target * 0.95:
        return "AMBER"
    return "RED"


# =============================================================================
# 9. KPI COCKPIT
# =============================================================================

kpi_rows = [
    [
        "NPT Hours",
        npt_hours,
        3000,
        "MINIMIZE",
        minimize_status(npt_hours, 3000),
        "Lagging"
    ],
    [
        "Direct NPT Cost",
        direct_cost,
        60000000,
        "MINIMIZE",
        minimize_status(direct_cost, 60000000),
        "Lagging"
    ],
    [
        "Total Economic Impact",
        total_impact,
        150000000,
        "MINIMIZE",
        minimize_status(total_impact, 150000000),
        "Lagging"
    ],
    [
        "Average ROP",
        avg_rop,
        35,
        "MAXIMIZE",
        maximize_status(avg_rop, 35),
        "Leading"
    ],
    [
        "Cost per Foot",
        cost_per_ft,
        600,
        "MINIMIZE",
        minimize_status(cost_per_ft, 600),
        "Lagging"
    ],
    [
        "Target Savings",
        target_savings,
        VALIDATED_TARGET_SAVINGS,
        "MAXIMIZE",
        maximize_status(
            target_savings,
            VALIDATED_TARGET_SAVINGS
        ),
        "Leading"
    ]
]

kpi_cockpit = pd.DataFrame(
    kpi_rows,
    columns=[
        "KPI",
        "Actual",
        "Target",
        "Direction",
        "Status",
        "Indicator_Type"
    ]
)


# =============================================================================
# 10. RIG PERFORMANCE
# =============================================================================

rig_performance = (
    fact_npt
    .groupby("Rig_ID", as_index=False)
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Savings_At_Risk_USD=("Savings_At_Risk_USD", "sum"),
        Wells_Exposed=("Well_ID", "nunique")
    )
)

rig_performance["Impact_Share_pct"] = (
    rig_performance["Total_Impact_USD"] /
    total_impact * 100
)

rig_performance["Exposure_Status"] = np.select(
    [
        rig_performance["Impact_Share_pct"] >= 25,
        rig_performance["Impact_Share_pct"] >= 15,
        rig_performance["Impact_Share_pct"] >= 10
    ],
    [
        "RED",
        "AMBER",
        "YELLOW"
    ],
    default="GREEN"
)

rig_performance["Decision_Priority"] = np.select(
    [
        rig_performance["Impact_Share_pct"] >= 25,
        rig_performance["Impact_Share_pct"] >= 15,
        rig_performance["Impact_Share_pct"] >= 10
    ],
    [
        1,
        2,
        3
    ],
    default=4
)

rig_performance = rig_performance.sort_values(
    ["Decision_Priority", "Total_Impact_USD"],
    ascending=[True, False]
)


# =============================================================================
# 11. WELL RISK MATRIX
# =============================================================================

well_risk = (
    fact_npt
    .groupby("Well_ID", as_index=False)
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Savings_At_Risk_USD=("Savings_At_Risk_USD", "sum"),
        Rigs_Exposed=("Rig_ID", "nunique")
    )
)

well_risk["Impact_Share_pct"] = (
    well_risk["Total_Impact_USD"] /
    total_impact * 100
)

well_risk["Risk_Level"] = np.select(
    [
        well_risk["Impact_Share_pct"] >= 2,
        well_risk["Impact_Share_pct"] >= 1,
        well_risk["Impact_Share_pct"] >= 0.5
    ],
    [
        "CRITICAL",
        "HIGH",
        "MEDIUM"
    ],
    default="LOW"
)

well_risk["Decision_Priority"] = np.select(
    [
        well_risk["Impact_Share_pct"] >= 2,
        well_risk["Impact_Share_pct"] >= 1,
        well_risk["Impact_Share_pct"] >= 0.5
    ],
    [
        1,
        2,
        3
    ],
    default=4
)

well_risk = well_risk.sort_values(
    ["Decision_Priority", "Total_Impact_USD"],
    ascending=[True, False]
)


# =============================================================================
# 12. ROOT-CAUSE PARETO
# =============================================================================

root_cause_pareto = (
    fact_npt
    .groupby("Root_Cause", as_index=False)
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Savings_At_Risk_USD=("Savings_At_Risk_USD", "sum"),
        Wells_Exposed=("Well_ID", "nunique"),
        Rigs_Exposed=("Rig_ID", "nunique")
    )
)

root_cause_pareto = root_cause_pareto.sort_values(
    "Total_Impact_USD",
    ascending=False
).reset_index(drop=True)

root_cause_pareto["Cumulative_Impact_USD"] = (
    root_cause_pareto["Total_Impact_USD"].cumsum()
)

root_cause_pareto["Cumulative_Impact_pct"] = (
    root_cause_pareto["Cumulative_Impact_USD"] /
    total_impact * 100
)

root_cause_pareto["Pareto_Priority"] = np.select(
    [
        root_cause_pareto["Cumulative_Impact_pct"] <= 50,
        root_cause_pareto["Cumulative_Impact_pct"] <= 80
    ],
    [
        1,
        2
    ],
    default=3
)

# True economic criticality:
# individual root cause >= 5% of total economic impact

root_cause_pareto["Impact_Share_pct"] = (
    root_cause_pareto["Total_Impact_USD"] /
    total_impact * 100
)

root_cause_pareto["Criticality"] = np.select(
    [
        root_cause_pareto["Impact_Share_pct"] >= 5,
        root_cause_pareto["Impact_Share_pct"] >= 2,
        root_cause_pareto["Impact_Share_pct"] >= 1
    ],
    [
        "CRITICAL",
        "HIGH",
        "MEDIUM"
    ],
    default="LOW"
)


# =============================================================================
# 13. INITIATIVE PORTFOLIO
# =============================================================================

initiative_portfolio = (
    fact_npt
    .groupby(
        [
            "Initiative_ID",
            "Initiative_Name",
            "Initiative_Priority"
        ],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Savings_At_Risk_USD=("Savings_At_Risk_USD", "sum"),
        Wells_Exposed=("Well_ID", "nunique"),
        Rigs_Exposed=("Rig_ID", "nunique")
    )
)

initiative_portfolio["Impact_Share_pct"] = (
    initiative_portfolio["Total_Impact_USD"] /
    total_impact * 100
)

initiative_portfolio["Savings_At_Risk_pct"] = np.where(
    initiative_portfolio["Target_Savings_USD"] > 0,
    initiative_portfolio["Savings_At_Risk_USD"] /
    initiative_portfolio["Target_Savings_USD"] * 100,
    0
)

initiative_portfolio["Decision_Priority"] = np.select(
    [
        initiative_portfolio["Target_Savings_USD"] >= 8000000,
        initiative_portfolio["Target_Savings_USD"] >= 4000000,
        initiative_portfolio["Target_Savings_USD"] >= 1000000
    ],
    [
        1,
        2,
        3
    ],
    default=4
)

initiative_portfolio = initiative_portfolio.sort_values(
    ["Decision_Priority", "Target_Savings_USD"],
    ascending=[True, False]
).reset_index(drop=True)


# =============================================================================
# 14. SAVINGS WATERFALL
# =============================================================================

protected_savings = target_savings - savings_at_risk

savings_waterfall = pd.DataFrame(
    [
        [
            "Validated Target Savings",
            VALIDATED_TARGET_SAVINGS,
            0
        ],
        [
            "Savings At Risk",
            -savings_at_risk,
            1
        ],
        [
            "Protected Savings",
            protected_savings,
            2
        ]
    ],
    columns=[
        "Waterfall_Component",
        "Value_USD",
        "Sequence"
    ]
)


# =============================================================================
# 15. ACTION AGING
# =============================================================================

action_aging = (
    fact_npt
    .groupby("Action_Status_Normalized", as_index=False)
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Savings_At_Risk_USD=("Savings_At_Risk_USD", "sum")
    )
)

action_aging["Risk_pct"] = np.where(
    action_aging["Target_Savings_USD"] > 0,
    action_aging["Savings_At_Risk_USD"] /
    action_aging["Target_Savings_USD"] * 100,
    0
)


# =============================================================================
# 16. MANAGEMENT DECISION QUEUE
# =============================================================================

decision_rows = []

top_rig = rig_performance.iloc[0]
top_root = root_cause_pareto.iloc[0]
top_initiative = initiative_portfolio.iloc[0]
top_well = well_risk.iloc[0]

decision_rows.append([
    1,
    "RIG",
    top_rig["Rig_ID"],
    "Reduce rig-level operational exposure",
    top_rig["Total_Impact_USD"],
    top_rig["Savings_At_Risk_USD"],
    "CRITICAL",
    "Immediate"
])

decision_rows.append([
    2,
    "ROOT CAUSE",
    top_root["Root_Cause"],
    "Launch focused root-cause elimination",
    top_root["Total_Impact_USD"],
    top_root["Savings_At_Risk_USD"],
    top_root["Criticality"],
    "Immediate"
])

decision_rows.append([
    3,
    "INITIATIVE",
    top_initiative["Initiative_ID"],
    "Protect largest savings opportunity",
    top_initiative["Target_Savings_USD"],
    top_initiative["Savings_At_Risk_USD"],
    top_initiative["Initiative_Priority"],
    "Immediate"
])

decision_rows.append([
    4,
    "WELL",
    top_well["Well_ID"],
    "Perform well-level performance review",
    top_well["Total_Impact_USD"],
    top_well["Savings_At_Risk_USD"],
    top_well["Risk_Level"],
    "Priority"
])

decision_rows.append([
    5,
    "SAVINGS",
    top_initiative["Initiative_ID"],
    "Close actions threatening savings realization",
    top_initiative["Target_Savings_USD"],
    top_initiative["Savings_At_Risk_USD"],
    "HIGH",
    "Priority"
])

management_decision_queue = pd.DataFrame(
    decision_rows,
    columns=[
        "Decision_Rank",
        "Decision_Type",
        "Object",
        "Decision",
        "Exposure_USD",
        "Savings_At_Risk_USD",
        "Severity",
        "Timing"
    ]
)


# =============================================================================
# 17. EXECUTIVE COMMAND CENTER
# =============================================================================

critical_kpis = int(
    (kpi_cockpit["Status"] == "RED").sum()
)

red_rigs = int(
    (rig_performance["Exposure_Status"] == "RED").sum()
)

critical_wells = int(
    (well_risk["Risk_Level"] == "CRITICAL").sum()
)

critical_root_causes = int(
    (root_cause_pareto["Criticality"] == "CRITICAL").sum()
)

overall_status = "GREEN"

if (
    critical_kpis >= 1
    or red_rigs >= 1
    or critical_root_causes >= 1
    or savings_at_risk >= VALIDATED_TARGET_SAVINGS * 0.50
):
    overall_status = "RED"

elif (
    (kpi_cockpit["Status"] == "AMBER").sum() > 0
    or (rig_performance["Exposure_Status"] == "AMBER").sum() > 0
):
    overall_status = "AMBER"


executive_command_center = pd.DataFrame(
    [[
        "STAGE 2G.16",
        "Operational Performance Command Center",
        overall_status,
        npt_events,
        npt_hours,
        direct_cost,
        deferred_cost,
        total_impact,
        target_savings,
        savings_at_risk,
        len(dim_well),
        len(dim_rig),
        drilling_days,
        total_footage,
        avg_rop,
        cost_per_ft,
        critical_kpis,
        red_rigs,
        critical_wells,
        critical_root_causes,
        top_rig["Rig_ID"],
        top_root["Root_Cause"],
        top_initiative["Initiative_ID"],
        top_well["Well_ID"],
        "Execute immediate action on top rig, root cause and savings exposure."
    ]],
    columns=[
        "Stage",
        "Command_Center",
        "Overall_Status",
        "NPT_Events",
        "NPT_Hours",
        "Direct_NPT_Cost_USD",
        "Deferred_Cost_USD",
        "Total_Economic_Impact_USD",
        "Target_Savings_USD",
        "Savings_At_Risk_USD",
        "Wells",
        "Rigs",
        "Drilling_Days",
        "Total_Footage_ft",
        "Average_ROP_ft_hr",
        "Cost_per_Foot_USD",
        "Critical_KPIs",
        "Red_Rigs",
        "Critical_Wells",
        "Critical_Root_Causes",
        "Top_Rig",
        "Top_Root_Cause",
        "Top_Initiative",
        "Top_Well",
        "Executive_Decision"
    ]
)


# =============================================================================
# 18. SCENARIO IMPACT
# =============================================================================

scenario_rows = []

for scenario, reduction in [
    ("BASELINE", 0.00),
    ("CONSERVATIVE", 0.20),
    ("TARGET", 0.40),
    ("STRETCH", 0.60)
]:

    reduced_hours = npt_hours * reduction
    remaining_hours = npt_hours - reduced_hours

    scenario_rows.append([
        scenario,
        reduction * 100,
        reduced_hours,
        remaining_hours,
        VALIDATED_TOTAL_IMPACT * (1 - reduction),
        VALIDATED_TOTAL_IMPACT * reduction
    ])

scenario_impact = pd.DataFrame(
    scenario_rows,
    columns=[
        "Scenario",
        "NPT_Reduction_pct",
        "NPT_Hours_Reduced",
        "NPT_Hours_Remaining",
        "Illustrative_Remaining_Impact_USD",
        "Illustrative_Impact_Avoided_USD"
    ]
)


# =============================================================================
# 19. POWER BI METADATA
# =============================================================================

powerbi_metadata = pd.DataFrame(
    [
        [
            "Executive Command Center",
            "Executive_Command_Center",
            "Overall management status"
        ],
        [
            "KPI Cockpit",
            "KPI_Cockpit",
            "Leading and lagging KPI status"
        ],
        [
            "Rig Performance",
            "Rig_Performance",
            "Rig exposure and decision priority"
        ],
        [
            "Well Risk Matrix",
            "Well_Risk",
            "Well-level economic exposure"
        ],
        [
            "Root Cause Pareto",
            "Root_Cause_Pareto",
            "Root-cause prioritization"
        ],
        [
            "Initiative Portfolio",
            "Initiative_Portfolio",
            "Savings and initiative exposure"
        ],
        [
            "Savings Waterfall",
            "Savings_Waterfall",
            "Target savings protection"
        ],
        [
            "Decision Queue",
            "Management_Decision_Queue",
            "Management actions"
        ],
        [
            "Action Aging",
            "Action_Aging",
            "Action status and risk"
        ]
    ],
    columns=[
        "Dashboard_Component",
        "Source_Sheet",
        "Purpose"
    ]
)


# =============================================================================
# 20. ASSUMPTIONS
# =============================================================================

assumptions = pd.DataFrame(
    [
        [
            "Economic baseline",
            VALIDATED_TOTAL_IMPACT,
            "Stage 2G.10.1 validated baseline"
        ],
        [
            "Target savings",
            VALIDATED_TARGET_SAVINGS,
            "Stage 2G.10.1 validated target"
        ],
        [
            "Conservative savings",
            VALIDATED_CONSERVATIVE_SAVINGS,
            "Stage 2G.10.1 validated scenario"
        ],
        [
            "Stretch savings",
            VALIDATED_STRETCH_SAVINGS,
            "Stage 2G.10.1 validated scenario"
        ],
        [
            "Target savings rate",
            TARGET_SAVINGS_RATE,
            "Target savings / total economic impact"
        ],
        [
            "Rig RED threshold",
            ">=25% of total impact",
            "Management assumption"
        ],
        [
            "Well CRITICAL threshold",
            ">=2% of total impact",
            "Management assumption"
        ],
        [
            "Root cause CRITICAL threshold",
            ">=5% of total impact",
            "Management assumption"
        ],
        [
            "Open action risk",
            "100%",
            "Management assumption"
        ],
        [
            "In Progress action risk",
            "50%",
            "Management assumption"
        ],
        [
            "Closed action risk",
            "0%",
            "Management assumption"
        ],
        [
            "Unknown action risk",
            "75%",
            "Management assumption"
        ],
        [
            "Scenario methodology",
            "NPT reduction and economic savings are separate concepts",
            "Stage 2G.14 methodology"
        ]
    ],
    columns=[
        "Assumption",
        "Value",
        "Basis"
    ]
)


# =============================================================================
# 21. DATA QUALITY
# =============================================================================

economic_reconciliation = (
    total_impact -
    VALIDATED_TOTAL_IMPACT
)

target_savings_reconciliation = (
    target_savings -
    VALIDATED_TARGET_SAVINGS
)

initiative_count = (
    fact_npt["Initiative_ID"].nunique()
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
        if fact_npt["NPT_ID"].nunique() == VALIDATED_NPT_EVENTS
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
        target_savings_reconciliation,
        0,
        "PASS"
        if abs(target_savings_reconciliation) < 0.01
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
        initiative_count,
        6,
        "PASS"
        if initiative_count == 6
        else "FAIL"
    ],
    [
        "Power BI metadata",
        len(powerbi_metadata),
        9,
        "PASS"
        if len(powerbi_metadata) == 9
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
# 22. EXPORT EXCEL
# =============================================================================

print("\nEXPORTING EXCEL...")
print("-" * 90)

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    executive_command_center.to_excel(
        writer,
        sheet_name="Executive_Command_Center",
        index=False
    )

    kpi_cockpit.to_excel(
        writer,
        sheet_name="KPI_Cockpit",
        index=False
    )

    rig_performance.to_excel(
        writer,
        sheet_name="Rig_Performance",
        index=False
    )

    well_risk.to_excel(
        writer,
        sheet_name="Well_Risk",
        index=False
    )

    root_cause_pareto.to_excel(
        writer,
        sheet_name="Root_Cause_Pareto",
        index=False
    )

    initiative_portfolio.to_excel(
        writer,
        sheet_name="Initiative_Portfolio",
        index=False
    )

    savings_waterfall.to_excel(
        writer,
        sheet_name="Savings_Waterfall",
        index=False
    )

    management_decision_queue.to_excel(
        writer,
        sheet_name="Management_Decision_Queue",
        index=False
    )

    action_aging.to_excel(
        writer,
        sheet_name="Action_Aging",
        index=False
    )

    scenario_impact.to_excel(
        writer,
        sheet_name="Scenario_Impact",
        index=False
    )

    powerbi_metadata.to_excel(
        writer,
        sheet_name="PowerBI_Metadata",
        index=False
    )

    assumptions.to_excel(
        writer,
        sheet_name="Assumptions",
        index=False
    )

    data_quality.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# =============================================================================
# 23. FINAL REPORT
# =============================================================================

print("\n" + "=" * 90)
print("STAGE 2G.16 — COMMAND CENTER RESULTS")
print("=" * 90)

print(f"\nOverall Command Center Status : {overall_status}")
print(f"Data Quality Status           : {overall_dq_status}")

print("\n--- VALIDATED ECONOMIC BASELINE ---")
print(f"NPT Events                    : {npt_events:,}")
print(f"NPT Hours                     : {npt_hours:,.0f}")
print(f"Direct NPT Cost               : ${direct_cost:,.0f}")
print(f"Deferred Cost                 : ${deferred_cost:,.0f}")
print(f"Total Economic Impact         : ${total_impact:,.0f}")
print(f"Target Savings                : ${target_savings:,.0f}")
print(f"Savings At Risk               : ${savings_at_risk:,.0f}")

print("\n--- OPERATIONAL PERFORMANCE ---")
print(f"Drilling Days                 : {drilling_days:,}")
print(f"Total Footage                 : {total_footage:,.1f} ft")
print(f"Average ROP                   : {avg_rop:,.2f} ft/hr")
print(f"Cost per Foot                 : ${cost_per_ft:,.2f}")

print("\n--- MANAGEMENT EXPOSURE ---")
print(f"Critical KPIs                 : {critical_kpis}")
print(f"Red Rigs                      : {red_rigs}")
print(f"Critical Wells                : {critical_wells}")
print(f"Critical Root Causes          : {critical_root_causes}")

print("\n--- TOP MANAGEMENT PRIORITIES ---")

print(
    f"Top Rig                       : "
    f"{top_rig['Rig_ID']} "
    f"(${top_rig['Total_Impact_USD']:,.0f})"
)

print(
    f"Top Root Cause                : "
    f"{top_root['Root_Cause']} "
    f"(${top_root['Total_Impact_USD']:,.0f})"
)

print(
    f"Top Initiative                : "
    f"{top_initiative['Initiative_ID']} "
    f"(${top_initiative['Target_Savings_USD']:,.0f})"
)

print(
    f"Top Well                      : "
    f"{top_well['Well_ID']} "
    f"(${top_well['Total_Impact_USD']:,.0f})"
)

print("\n--- INITIATIVE VALIDATION ---")

initiative_validation = (
    fact_npt
    .groupby(
        ["Initiative_ID", "Initiative_Name"],
        as_index=False
    )
    .agg(
        Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum")
    )
    .sort_values("Initiative_ID")
)

print(
    initiative_validation.to_string(index=False)
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
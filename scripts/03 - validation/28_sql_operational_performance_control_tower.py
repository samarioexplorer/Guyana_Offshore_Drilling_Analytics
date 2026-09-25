import os
import sqlite3
import pandas as pd
import numpy as np


# =============================================================================
# STAGE 2G.15
# OPERATIONAL PERFORMANCE CONTROL TOWER
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
    "sql_stage_2G.15_Operational_Performance_Control_Tower"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "sql_stage_2G.15_Operational_Performance_Control_Tower.xlsx"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


print("=" * 90)
print("STAGE 2G.15 — OPERATIONAL PERFORMANCE CONTROL TOWER")
print("=" * 90)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")


# =============================================================================
# 1. VALIDATED ECONOMIC BASELINE
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


print("\nSQL data loaded successfully.")
print(f"NPT rows      : {len(fact_npt):,}")
print(f"Drilling rows : {len(fact_drilling):,}")
print(f"Wells         : {len(dim_well):,}")
print(f"Rigs          : {len(dim_rig):,}")


# =============================================================================
# 3. STANDARDIZE NUMERIC FIELDS
# =============================================================================

numeric_npt = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Lost_Drilling_Days",
    "Productivity_Loss_pct"
]

for col in numeric_npt:
    if col in fact_npt.columns:
        fact_npt[col] = pd.to_numeric(
            fact_npt[col],
            errors="coerce"
        ).fillna(0)


numeric_drilling = [
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Daily_Cost_USD",
    "Weather_Delay_hr"
]

for col in numeric_drilling:
    if col in fact_drilling.columns:
        fact_drilling[col] = pd.to_numeric(
            fact_drilling[col],
            errors="coerce"
        ).fillna(0)


# =============================================================================
# 4. EVENT-LEVEL MANAGEMENT METRICS
# =============================================================================

fact_npt["Target_Savings_USD"] = (
    fact_npt["Total_Impact_USD"] *
    TARGET_SAVINGS_RATE
)


# =============================================================================
# 5. INITIATIVE CLASSIFICATION
# =============================================================================
#
# Six-family management architecture.
#
# INIT-001 = Drilling Dysfunction Reduction
# INIT-002 = Mechanical Reliability
# INIT-003 = Weather & Marine Resilience
# INIT-004 = Supply Chain & Logistics
# INIT-005 = People / Competency / Readiness
# INIT-006 = Drilling Performance Optimization
#
# The classification is based on the actual Root_Cause values present
# in Fact_NPT. No synthetic or non-existent root causes are introduced.
#


# Root causes explicitly assigned to drilling-performance optimization.
#
# Bit Wear is treated as a drilling-performance optimization opportunity.
# The remaining Drilling root causes remain within the drilling dysfunction
# program.

drilling_performance_root_causes = [
    "Bit Wear"
]


conditions = [
    # INIT-001
    fact_npt["NPT_Category"].eq("Drilling")
    & ~fact_npt["Root_Cause"].isin(
        drilling_performance_root_causes
    ),

    # INIT-002
    fact_npt["NPT_Category"].eq("Mechanical"),

    # INIT-003
    fact_npt["NPT_Category"].eq("Weather"),

    # INIT-004
    fact_npt["NPT_Category"].eq("Logistics"),

    # INIT-005
    fact_npt["NPT_Category"].eq("Personnel"),

    # INIT-006
    fact_npt["Root_Cause"].isin(
        drilling_performance_root_causes
    )
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
    fact_npt["Initiative_ID"].map(
        initiative_names
    )
)


fact_npt["Initiative_Priority"] = (
    fact_npt["Initiative_ID"].map(
        initiative_priority
    )
)

# =============================================================================
# 6. ACTION STATUS NORMALIZATION
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
# 7. KPI STATUS LOGIC
# =============================================================================

def status_minimize(actual, target):
    """
    Lower is better.
    Green  <= target
    Amber  <= 110% of target
    Red    > 110% of target
    """
    if actual <= target:
        return "GREEN"
    elif actual <= target * 1.10:
        return "AMBER"
    return "RED"


def status_maximize(actual, target):
    """
    Higher is better.
    Green  >= target
    Amber  >= 95% of target
    Red    < 95% of target
    """
    if actual >= target:
        return "GREEN"
    elif actual >= target * 0.95:
        return "AMBER"
    return "RED"


# =============================================================================
# 8. OPERATIONAL KPI CALCULATIONS
# =============================================================================

npt_events = len(fact_npt)

npt_hours = fact_npt["Duration_hr"].sum()

direct_cost = fact_npt["Cost_USD"].sum()

deferred_cost = fact_npt["Deferred_Cost_USD"].sum()

total_impact = fact_npt["Total_Impact_USD"].sum()

drilling_days = fact_drilling["Date"].nunique()

total_footage = fact_drilling["Daily_Footage_ft"].sum()

avg_rop = fact_drilling["ROP_ft_hr"].mean()

cost_per_ft = (
    fact_drilling["Daily_Cost_USD"].sum() /
    total_footage
    if total_footage > 0
    else 0
)

target_savings = fact_npt["Target_Savings_USD"].sum()

savings_at_risk = fact_npt["Savings_At_Risk_USD"].sum()


# =============================================================================
# 9. KPI STATUS TABLE
# =============================================================================

kpi_rows = [
    [
        "NPT Hours",
        npt_hours,
        3000,
        "MINIMIZE",
        status_minimize(npt_hours, 3000),
        "Lagging",
        "Reduce operational downtime"
    ],
    [
        "Direct NPT Cost",
        direct_cost,
        60000000,
        "MINIMIZE",
        status_minimize(direct_cost, 60000000),
        "Lagging",
        "Reduce direct NPT expenditure"
    ],
    [
        "Total Economic Impact",
        total_impact,
        150000000,
        "MINIMIZE",
        status_minimize(total_impact, 150000000),
        "Lagging",
        "Reduce total operational exposure"
    ],
    [
        "Average ROP",
        avg_rop,
        35,
        "MAXIMIZE",
        status_maximize(avg_rop, 35),
        "Leading",
        "Improve drilling performance"
    ],
    [
        "Cost per Foot",
        cost_per_ft,
        600,
        "MINIMIZE",
        status_minimize(cost_per_ft, 600),
        "Lagging",
        "Improve cost efficiency"
    ],
    [
        "Target Savings",
        target_savings,
        VALIDATED_TARGET_SAVINGS,
        "MAXIMIZE",
        status_maximize(
            target_savings,
            VALIDATED_TARGET_SAVINGS
        ),
        "Leading",
        "Protect validated savings opportunity"
    ]
]

kpi_status = pd.DataFrame(
    kpi_rows,
    columns=[
        "KPI",
        "Actual",
        "Target",
        "Direction",
        "Status",
        "Indicator_Type",
        "Management_Objective"
    ]
)


# =============================================================================
# 10. RIG ALERTS
# =============================================================================

rig_group = (
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

rig_group["Impact_Share_pct"] = (
    rig_group["Total_Impact_USD"] /
    total_impact *
    100
)

rig_group["Alert_Level"] = np.select(
    [
        rig_group["Impact_Share_pct"] >= 25,
        rig_group["Impact_Share_pct"] >= 15,
        rig_group["Impact_Share_pct"] >= 10
    ],
    [
        "RED",
        "AMBER",
        "YELLOW"
    ],
    default="GREEN"
)

rig_group["Management_Priority"] = np.select(
    [
        rig_group["Impact_Share_pct"] >= 25,
        rig_group["Impact_Share_pct"] >= 15,
        rig_group["Impact_Share_pct"] >= 10
    ],
    [
        "CRITICAL",
        "HIGH",
        "MEDIUM"
    ],
    default="LOW"
)

rig_alerts = rig_group.sort_values(
    "Total_Impact_USD",
    ascending=False
)


# =============================================================================
# 11. WELL ALERTS
# =============================================================================

well_group = (
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

well_group["Impact_Share_pct"] = (
    well_group["Total_Impact_USD"] /
    total_impact *
    100
)

well_group["Alert_Level"] = np.select(
    [
        well_group["Impact_Share_pct"] >= 2.0,
        well_group["Impact_Share_pct"] >= 1.0,
        well_group["Impact_Share_pct"] >= 0.5
    ],
    [
        "RED",
        "AMBER",
        "YELLOW"
    ],
    default="GREEN"
)

well_group["Management_Priority"] = np.select(
    [
        well_group["Impact_Share_pct"] >= 2.0,
        well_group["Impact_Share_pct"] >= 1.0,
        well_group["Impact_Share_pct"] >= 0.5
    ],
    [
        "CRITICAL",
        "HIGH",
        "MEDIUM"
    ],
    default="LOW"
)

well_alerts = well_group.sort_values(
    "Total_Impact_USD",
    ascending=False
)


# =============================================================================
# 12. ROOT CAUSE ALERTS
# =============================================================================

root_group = (
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

root_group["Impact_Share_pct"] = (
    root_group["Total_Impact_USD"] /
    total_impact *
    100
)

root_group["Alert_Level"] = np.select(
    [
        root_group["Impact_Share_pct"] >= 2.0,
        root_group["Impact_Share_pct"] >= 1.0,
        root_group["Impact_Share_pct"] >= 0.5
    ],
    [
        "RED",
        "AMBER",
        "YELLOW"
    ],
    default="GREEN"
)

root_group["Management_Priority"] = np.select(
    [
        root_group["Impact_Share_pct"] >= 2.0,
        root_group["Impact_Share_pct"] >= 1.0,
        root_group["Impact_Share_pct"] >= 0.5
    ],
    [
        "CRITICAL",
        "HIGH",
        "MEDIUM"
    ],
    default="LOW"
)

root_cause_alerts = root_group.sort_values(
    "Total_Impact_USD",
    ascending=False
)


# =============================================================================
# 13. INITIATIVE STATUS
# =============================================================================

initiative_group = (
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

initiative_group["Savings_Protection_pct"] = np.where(
    initiative_group["Target_Savings_USD"] > 0,
    (
        1 -
        initiative_group["Savings_At_Risk_USD"] /
        initiative_group["Target_Savings_USD"]
    ) * 100,
    0
)

initiative_group["Management_Status"] = np.select(
    [
        initiative_group["Savings_At_Risk_USD"] /
        initiative_group["Target_Savings_USD"] >= 0.75,

        initiative_group["Savings_At_Risk_USD"] /
        initiative_group["Target_Savings_USD"] >= 0.40
    ],
    [
        "RED",
        "AMBER"
    ],
    default="GREEN"
)

initiative_status = initiative_group.sort_values(
    "Target_Savings_USD",
    ascending=False
)


# =============================================================================
# 14. SAVINGS AT RISK
# =============================================================================

savings_risk = (
    fact_npt
    .groupby(
        [
            "Initiative_ID",
            "Initiative_Name",
            "Initiative_Priority",
            "Action_Status_Normalized"
        ],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Savings_At_Risk_USD=("Savings_At_Risk_USD", "sum")
    )
)

savings_risk["Risk_pct"] = np.where(
    savings_risk["Target_Savings_USD"] > 0,
    savings_risk["Savings_At_Risk_USD"] /
    savings_risk["Target_Savings_USD"] *
    100,
    0
)

savings_at_risk_table = savings_risk.sort_values(
    "Savings_At_Risk_USD",
    ascending=False
)


# =============================================================================
# 15. MANAGEMENT ESCALATION
# =============================================================================

top_rig = rig_alerts.iloc[0]

top_root = root_cause_alerts.iloc[0]

top_initiative = initiative_status.iloc[0]

top_risk = savings_at_risk_table.iloc[0]


critical_kpis = int(
    (kpi_status["Status"] == "RED").sum()
)

red_rigs = int(
    (rig_alerts["Alert_Level"] == "RED").sum()
)

critical_wells = int(
    (well_alerts["Management_Priority"] == "CRITICAL").sum()
)

critical_roots = int(
    (root_cause_alerts["Management_Priority"] == "CRITICAL").sum()
)

overall_status = "GREEN"

if (
    critical_kpis > 0
    or red_rigs > 0
    or critical_roots > 0
    or savings_at_risk > VALIDATED_TARGET_SAVINGS * 0.50
):
    overall_status = "RED"

elif (
    (kpi_status["Status"] == "AMBER").sum() > 0
    or (rig_alerts["Alert_Level"] == "AMBER").sum() > 0
):
    overall_status = "AMBER"


escalation_rows = [
    [
        1,
        "KPI",
        "NPT Hours",
        npt_hours,
        3000,
        status_minimize(npt_hours, 3000),
        "Reduce operational downtime through top NPT drivers."
    ],
    [
        2,
        "RIG",
        top_rig["Rig_ID"],
        top_rig["Total_Impact_USD"],
        None,
        top_rig["Alert_Level"],
        "Escalate rig-level reliability and execution review."
    ],
    [
        3,
        "ROOT CAUSE",
        top_root["Root_Cause"],
        top_root["Total_Impact_USD"],
        None,
        top_root["Alert_Level"],
        "Launch focused root-cause elimination action."
    ],
    [
        4,
        "INITIATIVE",
        top_initiative["Initiative_ID"],
        top_initiative["Target_Savings_USD"],
        None,
        top_initiative["Initiative_Priority"],
        "Protect the largest savings opportunity."
    ],
    [
        5,
        "SAVINGS AT RISK",
        top_risk["Initiative_ID"],
        top_risk["Savings_At_Risk_USD"],
        None,
        "RED" if top_risk["Risk_pct"] >= 75 else "AMBER",
        "Prioritize closure of open actions threatening savings."
    ]
]

management_escalation = pd.DataFrame(
    escalation_rows,
    columns=[
        "Priority",
        "Alert_Type",
        "Object",
        "Exposure_USD_or_Value",
        "Target",
        "Status",
        "Recommended_Action"
    ]
)


# =============================================================================
# 16. ACTION OWNERSHIP
# =============================================================================

action_ownership = (
    fact_npt
    .groupby("Responsible_Party", as_index=False)
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Savings_At_Risk_USD=("Savings_At_Risk_USD", "sum"),
        Open_Actions=(
            "Action_Status_Normalized",
            lambda x: (x == "Open").sum()
        ),
        In_Progress_Actions=(
            "Action_Status_Normalized",
            lambda x: (x == "In Progress").sum()
        ),
        Closed_Actions=(
            "Action_Status_Normalized",
            lambda x: (x == "Closed").sum()
        )
    )
)

action_ownership["Savings_Risk_pct"] = np.where(
    action_ownership["Target_Savings_USD"] > 0,
    action_ownership["Savings_At_Risk_USD"] /
    action_ownership["Target_Savings_USD"] *
    100,
    0
)

action_ownership = action_ownership.sort_values(
    "Savings_At_Risk_USD",
    ascending=False
)


# =============================================================================
# 17. EXECUTIVE CONTROL TOWER
# =============================================================================

control_tower = pd.DataFrame(
    [[
        "STAGE 2G.15",
        "Operational Performance Control Tower",
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
        critical_roots,
        top_rig["Rig_ID"],
        top_root["Root_Cause"],
        top_initiative["Initiative_ID"],
        "Protect target savings and eliminate top rig/root-cause exposure."
    ]],
    columns=[
        "Stage",
        "Control_Tower",
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
        "Executive_Priority"
    ]
)


# =============================================================================
# 18. ASSUMPTIONS
# =============================================================================

assumptions = pd.DataFrame(
    [
        [
            "Economic baseline",
            "Stage 2G.10.1 validated economic baseline",
            "Reference"
        ],
        [
            "Target savings",
            VALIDATED_TARGET_SAVINGS,
            "Validated Stage 2G.10.1"
        ],
        [
            "Target savings rate",
            TARGET_SAVINGS_RATE,
            "Validated target savings / total impact"
        ],
        [
            "KPI minimize threshold",
            "Green <= target; Amber <= 110%; Red > 110%",
            "Management assumption"
        ],
        [
            "KPI maximize threshold",
            "Green >= target; Amber >= 95%; Red < 95%",
            "Management assumption"
        ],
        [
            "Rig alert threshold",
            "Red >=25% impact share; Amber >=15%; Yellow >=10%",
            "Management assumption"
        ],
        [
            "Well/root cause alert threshold",
            "Red >=2%; Amber >=1%; Yellow >=0.5% impact share",
            "Management assumption"
        ],
        [
            "Open action risk",
            "100% of target savings at risk",
            "Management assumption"
        ],
        [
            "In-progress action risk",
            "50% of target savings at risk",
            "Management assumption"
        ],
        [
            "Closed action risk",
            "0% of target savings at risk",
            "Management assumption"
        ],
        [
            "Unknown action risk",
            "75% of target savings at risk",
            "Management assumption"
        ],
        [
            "Important economic caveat",
            "NPT reduction scenarios and economic savings are separate concepts",
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
# 19. DATA QUALITY VALIDATION
# =============================================================================

economic_reconciliation = (
    total_impact -
    VALIDATED_TOTAL_IMPACT
)

target_savings_reconciliation = (
    target_savings -
    VALIDATED_TARGET_SAVINGS
)

dq_rows = [
    [
        "NPT row count",
        npt_events,
        VALIDATED_NPT_EVENTS,
        "PASS" if npt_events == VALIDATED_NPT_EVENTS else "FAIL"
    ],
    [
        "Drilling row count",
        len(fact_drilling),
        1474,
        "PASS" if len(fact_drilling) == 1474 else "FAIL"
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
        "PASS" if target_savings > 0 else "FAIL"
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
# 20. EXPORT EXCEL
# =============================================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    control_tower.to_excel(
        writer,
        sheet_name="Control_Tower",
        index=False
    )

    kpi_status.to_excel(
        writer,
        sheet_name="KPI_Status",
        index=False
    )

    rig_alerts.to_excel(
        writer,
        sheet_name="Rig_Alerts",
        index=False
    )

    well_alerts.to_excel(
        writer,
        sheet_name="Well_Alerts",
        index=False
    )

    root_cause_alerts.to_excel(
        writer,
        sheet_name="Root_Cause_Alerts",
        index=False
    )

    initiative_status.to_excel(
        writer,
        sheet_name="Initiative_Status",
        index=False
    )

    savings_at_risk_table.to_excel(
        writer,
        sheet_name="Savings_At_Risk",
        index=False
    )

    management_escalation.to_excel(
        writer,
        sheet_name="Management_Escalation",
        index=False
    )

    action_ownership.to_excel(
        writer,
        sheet_name="Action_Ownership",
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
# 21. FINAL CONSOLE REPORT
# =============================================================================

print("\n" + "=" * 90)
print("STAGE 2G.15 — CONTROL TOWER RESULTS")
print("=" * 90)

print(f"\nOverall Control Tower Status : {overall_status}")
print(f"Data Quality Status          : {overall_dq_status}")

print("\n--- OPERATIONAL BASELINE ---")
print(f"NPT Events                   : {npt_events:,}")
print(f"NPT Hours                    : {npt_hours:,.0f}")
print(f"Direct NPT Cost              : ${direct_cost:,.0f}")
print(f"Deferred Cost                : ${deferred_cost:,.0f}")
print(f"Total Economic Impact        : ${total_impact:,.0f}")
print(f"Target Savings               : ${target_savings:,.0f}")
print(f"Savings At Risk              : ${savings_at_risk:,.0f}")

print("\n--- OPERATIONAL KPIs ---")
print(f"Drilling Days                : {drilling_days:,}")
print(f"Total Footage                : {total_footage:,.1f} ft")
print(f"Average ROP                  : {avg_rop:,.2f} ft/hr")
print(f"Cost per Foot                : ${cost_per_ft:,.2f}")

print("\n--- ALERT SUMMARY ---")
print(f"Critical KPIs                : {critical_kpis}")
print(f"Red Rigs                     : {red_rigs}")
print(f"Critical Wells               : {critical_wells}")
print(f"Critical Root Causes         : {critical_roots}")

print("\n--- TOP EXPOSURES ---")
print(
    f"Top Rig                      : "
    f"{top_rig['Rig_ID']} "
    f"(${top_rig['Total_Impact_USD']:,.0f})"
)

print(
    f"Top Root Cause               : "
    f"{top_root['Root_Cause']} "
    f"(${top_root['Total_Impact_USD']:,.0f})"
)

print(
    f"Top Initiative               : "
    f"{top_initiative['Initiative_ID']} "
    f"(${top_initiative['Target_Savings_USD']:,.0f})"
)

print(
    f"Largest Savings Risk         : "
    f"{top_risk['Initiative_ID']} "
    f"(${top_risk['Savings_At_Risk_USD']:,.0f})"
)

print("\n--- DATA QUALITY ---")
print(data_quality.to_string(index=False))

print("\n" + "=" * 90)
print("OUTPUT GENERATED SUCCESSFULLY")
print("=" * 90)

print(f"\nExcel file:")
print(OUTPUT_FILE)
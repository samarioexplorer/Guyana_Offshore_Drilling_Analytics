import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np


# =============================================================================
# STAGE 2G.12.1
# IMPROVEMENT INITIATIVE PORTFOLIO & MANAGEMENT PRIORITIZATION
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.12.1_Improvement_Initiative_Portfolio"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.12.1_Improvement_Initiative_Portfolio.xlsx"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# VALIDATED ECONOMIC BASELINE — STAGE 2G.10.1
# =============================================================================

VALIDATED_TOTAL_IMPACT = 198150178.00
VALIDATED_TARGET_SAVINGS = 30825850.00
VALIDATED_CONSERVATIVE_SAVINGS = 15412920.00
VALIDATED_STRETCH_SAVINGS = 46238770.00

TARGET_SAVINGS_RATE = (
    VALIDATED_TARGET_SAVINGS
    / VALIDATED_TOTAL_IMPACT
)

CONSERVATIVE_SAVINGS_RATE = (
    VALIDATED_CONSERVATIVE_SAVINGS
    / VALIDATED_TOTAL_IMPACT
)

STRETCH_SAVINGS_RATE = (
    VALIDATED_STRETCH_SAVINGS
    / VALIDATED_TOTAL_IMPACT
)


# =============================================================================
# HELPERS
# =============================================================================

def safe_div(a, b):
    if b == 0 or pd.isna(b):
        return 0.0
    return a / b


def priority(score):
    if score >= 75:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    return "LOW"


def initiative_family(row):
    category = str(row["NPT_Category"]).strip()
    subcategory = str(row["NPT_Subcategory"]).strip()
    root = str(row["Root_Cause"]).strip()
    corrective = str(row["Corrective_Action"]).strip()

    text = (
        category
        + " "
        + subcategory
        + " "
        + root
        + " "
        + corrective
    ).lower()

    # -------------------------------------------------------------------------
    # MECHANICAL RELIABILITY
    # -------------------------------------------------------------------------
    if category == "Mechanical":
        if any(x in text for x in [
            "top drive",
            "bop",
            "mud pump",
            "draw works",
            "generator",
            "power system",
            "equipment wear",
            "preventive maintenance",
            "hydraulic failure",
            "electrical failure",
            "equipment failure",
            "mechanical failure",
        ]):
            return "Mechanical Reliability Program"

        return "Mechanical Reliability Program"

    # -------------------------------------------------------------------------
    # DRILLING PERFORMANCE
    # -------------------------------------------------------------------------
    if category == "Drilling":
        if any(x in text for x in [
            "differential sticking",
            "stuck pipe",
            "hole cleaning",
            "fishing",
            "lost circulation",
            "formation instability",
            "bit failure",
            "bit wear",
            "drilling parameter",
        ]):
            return "Drilling Dysfunction Reduction Program"

        return "Drilling Performance Optimization"

    # -------------------------------------------------------------------------
    # LOGISTICS
    # -------------------------------------------------------------------------
    if category == "Logistics":
        if any(x in text for x in [
            "customs",
            "material",
            "helicopter",
            "fuel",
            "supply",
            "shipment",
            "port",
            "transport",
        ]):
            return "Supply Chain & Logistics Optimization"

        return "Supply Chain & Logistics Optimization"

    # -------------------------------------------------------------------------
    # WEATHER
    # -------------------------------------------------------------------------
    if category == "Weather":
        if any(x in text for x in [
            "heavy rain",
            "storm",
            "lightning",
            "high waves",
            "strong wind",
            "weather",
        ]):
            return "Weather & Marine Operations Resilience"

        return "Weather & Marine Operations Resilience"

    # -------------------------------------------------------------------------
    # PERSONNEL
    # -------------------------------------------------------------------------
    if category == "Personnel":
        return "People, Competency & Operational Readiness"

    return "Integrated Operational Performance"


def initiative_objective(family):
    mapping = {
        "Mechanical Reliability Program":
            "Reduce equipment-driven NPT through reliability, maintenance and failure-prevention actions.",

        "Drilling Dysfunction Reduction Program":
            "Reduce drilling-related NPT through improved drilling practices, parameter optimization and dysfunction prevention.",

        "Drilling Performance Optimization":
            "Improve drilling execution, efficiency and operational consistency.",

        "Supply Chain & Logistics Optimization":
            "Reduce logistics-driven downtime through improved materials, customs, transportation and supply reliability.",

        "Weather & Marine Operations Resilience":
            "Reduce controllable weather and marine downtime through planning, forecasting and operational readiness.",

        "People, Competency & Operational Readiness":
            "Reduce personnel-related downtime through competency, readiness and execution discipline.",

        "Integrated Operational Performance":
            "Coordinate cross-functional actions to improve overall operational performance.",
    }

    return mapping.get(
        family,
        "Improve operational performance."
    )


def initiative_owner(family):
    mapping = {
        "Mechanical Reliability Program":
            "Maintenance Manager",

        "Drilling Dysfunction Reduction Program":
            "Drilling Manager",

        "Drilling Performance Optimization":
            "Drilling Manager",

        "Supply Chain & Logistics Optimization":
            "Supply Chain Manager",

        "Weather & Marine Operations Resilience":
            "Marine Operations Manager",

        "People, Competency & Operational Readiness":
            "Operations Manager",

        "Integrated Operational Performance":
            "Operations Manager",
    }

    return mapping.get(
        family,
        "Operations Manager"
    )


def initiative_kpi(family):
    mapping = {
        "Mechanical Reliability Program":
            "Mechanical NPT Hours",

        "Drilling Dysfunction Reduction Program":
            "Drilling NPT Hours",

        "Drilling Performance Optimization":
            "ROP / NPT Hours",

        "Supply Chain & Logistics Optimization":
            "Logistics NPT Hours",

        "Weather & Marine Operations Resilience":
            "Weather NPT Hours",

        "People, Competency & Operational Readiness":
            "Personnel NPT Hours",

        "Integrated Operational Performance":
            "Total NPT Hours",
    }

    return mapping.get(
        family,
        "Total NPT Hours"
    )


# =============================================================================
# HEADER
# =============================================================================

print("=" * 80)
print("STAGE 2G.12.1 — IMPROVEMENT INITIATIVE PORTFOLIO")
print("MANAGEMENT PRIORITIZATION")
print("=" * 80)

print()
print(f"Project root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")
print()


# =============================================================================
# LOAD DATA
# =============================================================================

conn = sqlite3.connect(DB_PATH)

npt = pd.read_sql_query(
    """
    SELECT *
    FROM Fact_NPT
    """,
    conn
)

drilling = pd.read_sql_query(
    """
    SELECT *
    FROM Fact_Drilling_Daily_Report
    """,
    conn
)

conn.close()

print(f"NPT rows loaded      : {len(npt):,}")
print(f"Drilling rows loaded : {len(drilling):,}")
print()


# =============================================================================
# NUMERIC CLEANUP
# =============================================================================

numeric_cols = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
]

for col in numeric_cols:
    npt[col] = pd.to_numeric(
        npt[col],
        errors="coerce"
    ).fillna(0)


# =============================================================================
# CREATE INITIATIVE FAMILY
# =============================================================================

npt["Initiative_Family"] = npt.apply(
    initiative_family,
    axis=1
)


# =============================================================================
# STRATEGIC ACTION RECONSTRUCTION
#
# Same logical grouping used in Stage 2G.11.1
# =============================================================================

strategic_keys = [
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Corrective_Action",
]

strategic_actions = (
    npt.groupby(
        strategic_keys,
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost=("Cost_USD", "sum"),
        Deferred_Cost=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Wells=("Well_ID", "nunique"),
        Rigs=("Rig_ID", "nunique"),
    )
    .reset_index()
)

strategic_actions["Target_Savings_USD"] = (
    strategic_actions["Total_Impact_USD"]
    * TARGET_SAVINGS_RATE
)

strategic_actions["Conservative_Savings_USD"] = (
    strategic_actions["Total_Impact_USD"]
    * CONSERVATIVE_SAVINGS_RATE
)

strategic_actions["Stretch_Savings_USD"] = (
    strategic_actions["Total_Impact_USD"]
    * STRETCH_SAVINGS_RATE
)


strategic_actions = strategic_actions.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

strategic_actions["Strategic_Action_ID"] = [
    f"SA-{i:04d}"
    for i in range(1, len(strategic_actions) + 1)
]


# =============================================================================
# MAP STRATEGIC ACTIONS TO INITIATIVES
# =============================================================================

strategic_actions["Initiative_Family"] = (
    strategic_actions.apply(
        initiative_family,
        axis=1
    )
)


# =============================================================================
# INITIATIVE PORTFOLIO
# =============================================================================

initiative_group = (
    strategic_actions.groupby(
        "Initiative_Family",
        dropna=False
    )
    .agg(
        Strategic_Actions=("Strategic_Action_ID", "count"),
        NPT_Events=("NPT_Events", "sum"),
        Baseline_NPT_Hours=("Baseline_NPT_Hours", "sum"),
        Direct_NPT_Cost=("Direct_NPT_Cost", "sum"),
        Deferred_Cost=("Deferred_Cost", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Conservative_Savings_USD=("Conservative_Savings_USD", "sum"),
        Stretch_Savings_USD=("Stretch_Savings_USD", "sum"),
        Wells=("Wells", "sum"),
        Rigs=("Rigs", "sum"),
    )
    .reset_index()
)


# =============================================================================
# REMOVE DUPLICATED WELL/RIG COUNTS
# =============================================================================

well_counts = (
    npt.groupby("Initiative_Family")["Well_ID"]
    .nunique()
    .reset_index(name="Unique_Wells")
)

rig_counts = (
    npt.groupby("Initiative_Family")["Rig_ID"]
    .nunique()
    .reset_index(name="Unique_Rigs")
)

initiative_group = initiative_group.drop(
    columns=["Wells", "Rigs"]
)

initiative_group = initiative_group.merge(
    well_counts,
    on="Initiative_Family",
    how="left"
)

initiative_group = initiative_group.merge(
    rig_counts,
    on="Initiative_Family",
    how="left"
)


# =============================================================================
# PRIORITIZATION
# =============================================================================

initiative_group["Impact_Share_pct"] = (
    initiative_group["Total_Impact_USD"]
    / VALIDATED_TOTAL_IMPACT
    * 100
)

initiative_group["Target_Savings_Share_pct"] = (
    initiative_group["Target_Savings_USD"]
    / VALIDATED_TARGET_SAVINGS
    * 100
)


# Savings-based score
initiative_group["Savings_Score"] = (
    initiative_group["Target_Savings_USD"]
    / initiative_group["Target_Savings_USD"].max()
    * 100
)

# Impact-based score
initiative_group["Impact_Score"] = (
    initiative_group["Total_Impact_USD"]
    / initiative_group["Total_Impact_USD"].max()
    * 100
)

# Event frequency score
initiative_group["Frequency_Score"] = (
    initiative_group["NPT_Events"]
    / initiative_group["NPT_Events"].max()
    * 100
)

initiative_group["Priority_Score"] = (
    0.50 * initiative_group["Savings_Score"]
    + 0.35 * initiative_group["Impact_Score"]
    + 0.15 * initiative_group["Frequency_Score"]
)

initiative_group["Priority"] = (
    initiative_group["Priority_Score"]
    .apply(priority)
)


initiative_group["Management_Owner"] = (
    initiative_group["Initiative_Family"]
    .apply(initiative_owner)
)

initiative_group["Primary_KPI"] = (
    initiative_group["Initiative_Family"]
    .apply(initiative_kpi)
)

initiative_group["Objective"] = (
    initiative_group["Initiative_Family"]
    .apply(initiative_objective)
)


initiative_group = initiative_group.sort_values(
    "Priority_Score",
    ascending=False
).reset_index(drop=True)

initiative_group["Initiative_Rank"] = (
    initiative_group.index + 1
)

initiative_group["Initiative_ID"] = [
    f"INIT-{i:03d}"
    for i in initiative_group["Initiative_Rank"]
]


# =============================================================================
# MANAGEMENT TIER
# =============================================================================

def management_tier(row):
    if row["Priority"] == "CRITICAL":
        return "Tier 1 — Executive Priority"
    elif row["Priority"] == "HIGH":
        return "Tier 2 — Management Priority"
    elif row["Priority"] == "MEDIUM":
        return "Tier 3 — Operational Priority"
    return "Tier 4 — Monitor"


initiative_group["Management_Tier"] = (
    initiative_group.apply(
        management_tier,
        axis=1
    )
)


# =============================================================================
# PORTFOLIO EXECUTIVE VIEW
# =============================================================================

portfolio_view = initiative_group[
    [
        "Initiative_Rank",
        "Initiative_ID",
        "Initiative_Family",
        "Management_Tier",
        "Priority",
        "Priority_Score",
        "Strategic_Actions",
        "NPT_Events",
        "Baseline_NPT_Hours",
        "Total_Impact_USD",
        "Target_Savings_USD",
        "Conservative_Savings_USD",
        "Stretch_Savings_USD",
        "Impact_Share_pct",
        "Target_Savings_Share_pct",
        "Unique_Wells",
        "Unique_Rigs",
        "Management_Owner",
        "Primary_KPI",
        "Objective",
    ]
].copy()


# =============================================================================
# STRATEGIC ACTION DETAIL
# =============================================================================

strategic_detail = strategic_actions.merge(
    initiative_group[
        [
            "Initiative_Family",
            "Initiative_ID",
            "Management_Tier",
            "Priority",
        ]
    ],
    on="Initiative_Family",
    how="left"
)

strategic_detail = strategic_detail.sort_values(
    "Target_Savings_USD",
    ascending=False
)


# =============================================================================
# INITIATIVE × RIG
# =============================================================================

npt_with_initiative = npt.merge(
    strategic_detail[
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party",
            "Corrective_Action",
            "Initiative_ID",
        ]
    ],
    on=[
        "NPT_Category",
        "NPT_Subcategory",
        "Root_Cause",
        "Responsible_Party",
        "Corrective_Action",
    ],
    how="left"
)

initiative_rig = (
    npt_with_initiative.groupby(
        [
            "Initiative_ID",
            "Initiative_Family",
            "Rig_ID",
        ],
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost=("Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
    )
    .reset_index()
)

initiative_rig["Target_Savings_USD"] = (
    initiative_rig["Total_Impact_USD"]
    * TARGET_SAVINGS_RATE
)

initiative_rig = initiative_rig.sort_values(
    "Target_Savings_USD",
    ascending=False
)


# =============================================================================
# INITIATIVE × WELL
# =============================================================================

initiative_well = (
    npt_with_initiative.groupby(
        [
            "Initiative_ID",
            "Initiative_Family",
            "Well_ID",
            "Rig_ID",
        ],
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost=("Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
    )
    .reset_index()
)

initiative_well["Target_Savings_USD"] = (
    initiative_well["Total_Impact_USD"]
    * TARGET_SAVINGS_RATE
)

initiative_well = initiative_well.sort_values(
    "Target_Savings_USD",
    ascending=False
)


# =============================================================================
# RESPONSIBLE PARTY PORTFOLIO
# =============================================================================

responsible_party = (
    npt_with_initiative.groupby(
        [
            "Responsible_Party",
            "Initiative_Family",
        ],
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
    )
    .reset_index()
)

responsible_party["Target_Savings_USD"] = (
    responsible_party["Total_Impact_USD"]
    * TARGET_SAVINGS_RATE
)

responsible_party = responsible_party.sort_values(
    "Target_Savings_USD",
    ascending=False
)


# =============================================================================
# TOP OPPORTUNITIES
# =============================================================================

top_opportunities = strategic_detail[
    [
        "Strategic_Action_ID",
        "Initiative_ID",
        "Initiative_Family",
        "NPT_Category",
        "NPT_Subcategory",
        "Root_Cause",
        "Responsible_Party",
        "Corrective_Action",
        "NPT_Events",
        "Baseline_NPT_Hours",
        "Total_Impact_USD",
        "Target_Savings_USD",
        "Management_Tier",
        "Priority",
    ]
].head(25)


# =============================================================================
# PORTFOLIO RECONCILIATION
# =============================================================================

portfolio_total_impact = (
    initiative_group["Total_Impact_USD"].sum()
)

portfolio_target_savings = (
    initiative_group["Target_Savings_USD"].sum()
)

portfolio_conservative = (
    initiative_group["Conservative_Savings_USD"].sum()
)

portfolio_stretch = (
    initiative_group["Stretch_Savings_USD"].sum()
)


economic_difference = (
    portfolio_total_impact
    - VALIDATED_TOTAL_IMPACT
)


target_difference = (
    portfolio_target_savings
    - VALIDATED_TARGET_SAVINGS
)


# =============================================================================
# DATA QUALITY
# =============================================================================

data_quality = pd.DataFrame([
    [
        "NPT rows",
        len(npt),
        677,
        "PASS" if len(npt) == 677 else "FAIL",
    ],
    [
        "Strategic Actions",
        len(strategic_actions),
        502,
        "PASS" if len(strategic_actions) == 502 else "FAIL",
    ],
    [
        "Management Initiatives",
        len(initiative_group),
        "> 0",
        "PASS" if len(initiative_group) > 0 else "FAIL",
    ],
    [
        "Unique NPT IDs",
        npt["NPT_ID"].nunique(),
        len(npt),
        "PASS"
        if npt["NPT_ID"].nunique() == len(npt)
        else "FAIL",
    ],
    [
        "Duplicate NPT IDs",
        npt["NPT_ID"].duplicated().sum(),
        0,
        "PASS"
        if npt["NPT_ID"].duplicated().sum() == 0
        else "FAIL",
    ],
    [
        "Missing Initiative IDs",
        strategic_detail["Initiative_ID"].isna().sum(),
        0,
        "PASS"
        if strategic_detail["Initiative_ID"].isna().sum() == 0
        else "FAIL",
    ],
    [
        "Negative Initiative Impact",
        (initiative_group["Total_Impact_USD"] < 0).sum(),
        0,
        "PASS"
        if (initiative_group["Total_Impact_USD"] < 0).sum() == 0
        else "FAIL",
    ],
    [
        "Negative Target Savings",
        (initiative_group["Target_Savings_USD"] < 0).sum(),
        0,
        "PASS"
        if (initiative_group["Target_Savings_USD"] < 0).sum() == 0
        else "FAIL",
    ],
    [
        "Economic Reconciliation",
        economic_difference,
        0,
        "PASS"
        if abs(economic_difference) < 0.01
        else "FAIL",
    ],
    [
        "Target Savings Reconciliation",
        target_difference,
        0,
        "PASS"
        if abs(target_difference) < 0.01
        else "FAIL",
    ],
], columns=[
    "Check",
    "Actual",
    "Expected",
    "Status",
])


overall_status = (
    "PASS"
    if (data_quality["Status"] == "PASS").all()
    else "FAIL"
)
# =============================================================================
# EXECUTIVE SUMMARY
# =============================================================================

executive_summary = pd.DataFrame([
    [
        "NPT Events",
        len(npt)
    ],
    [
        "Strategic Actions",
        len(strategic_actions)
    ],
    [
        "Management Initiatives",
        len(initiative_group)
    ],
    [
        "Action Reduction",
        len(strategic_actions) - len(initiative_group)
    ],
    [
        "Baseline NPT Hours",
        npt["Duration_hr"].sum()
    ],
    [
        "Total Economic Impact",
        portfolio_total_impact
    ],
    [
        "Validated Target Savings",
        VALIDATED_TARGET_SAVINGS
    ],
    [
        "Portfolio Target Savings",
        portfolio_target_savings
    ],
    [
        "Validated Conservative Savings",
        VALIDATED_CONSERVATIVE_SAVINGS
    ],
    [
        "Portfolio Conservative Savings",
        portfolio_conservative
    ],
    [
        "Validated Stretch Savings",
        VALIDATED_STRETCH_SAVINGS
    ],
    [
        "Portfolio Stretch Savings",
        portfolio_stretch
    ],
    [
        "Critical Initiatives",
        (initiative_group["Priority"] == "CRITICAL").sum()
    ],
    [
        "High Initiatives",
        (initiative_group["Priority"] == "HIGH").sum()
    ],
    [
        "Medium Initiatives",
        (initiative_group["Priority"] == "MEDIUM").sum()
    ],
    [
        "Low Initiatives",
        (initiative_group["Priority"] == "LOW").sum()
    ],
    [
        "Overall Data Quality",
        overall_status
    ],
], columns=[
    "Metric",
    "Value"
])


# =============================================================================
# SAVE EXCEL
# =============================================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    executive_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    portfolio_view.to_excel(
        writer,
        sheet_name="Initiative_Portfolio",
        index=False
    )

    strategic_detail.to_excel(
        writer,
        sheet_name="Strategic_Action_Detail",
        index=False
    )

    initiative_rig.to_excel(
        writer,
        sheet_name="Initiative_Rig",
        index=False
    )

    initiative_well.to_excel(
        writer,
        sheet_name="Initiative_Well",
        index=False
    )

    responsible_party.to_excel(
        writer,
        sheet_name="Responsible_Party",
        index=False
    )

    top_opportunities.to_excel(
        writer,
        sheet_name="Top_Opportunities",
        index=False
    )

    data_quality.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# =============================================================================
# CONSOLE RESULTS
# =============================================================================

print("=" * 80)
print("STAGE 2G.12.1 — RESULTS")
print("=" * 80)

print()

print(f"NPT events                : {len(npt):,}")
print(f"Strategic actions         : {len(strategic_actions):,}")
print(f"Management initiatives    : {len(initiative_group):,}")

print(
    f"Action reduction          : "
    f"{len(strategic_actions) - len(initiative_group):,}"
)

print(
    f"Baseline NPT hours        : "
    f"{npt['Duration_hr'].sum():,.2f}"
)

print(
    f"Total economic impact     : "
    f"${portfolio_total_impact:,.2f}"
)

print(
    f"Validated target savings  : "
    f"${VALIDATED_TARGET_SAVINGS:,.2f}"
)

print(
    f"Portfolio target savings  : "
    f"${portfolio_target_savings:,.2f}"
)

print(
    f"Target reconciliation     : "
    f"${target_difference:,.2f}"
)

print()
print(
    f"Critical initiatives      : "
    f"{(initiative_group['Priority'] == 'CRITICAL').sum()}"
)

print(
    f"High initiatives          : "
    f"{(initiative_group['Priority'] == 'HIGH').sum()}"
)

print(
    f"Medium initiatives        : "
    f"{(initiative_group['Priority'] == 'MEDIUM').sum()}"
)

print(
    f"Low initiatives           : "
    f"{(initiative_group['Priority'] == 'LOW').sum()}"
)

print()
print("Top Management Initiatives:")

print(
    initiative_group[
        [
            "Initiative_Rank",
            "Initiative_ID",
            "Initiative_Family",
            "NPT_Events",
            "Baseline_NPT_Hours",
            "Target_Savings_USD",
            "Priority",
        ]
    ].head(10).to_string(index=False)
)

print()
print("Data Quality:")
print(data_quality.to_string(index=False))

print()
print(
    f"Overall Data Quality Status : "
    f"{overall_status}"
)

print()
print("Output file:")
print(OUTPUT_FILE)

print()
print("=" * 80)
print("STAGE 2G.12.1 COMPLETED")
print("=" * 80)
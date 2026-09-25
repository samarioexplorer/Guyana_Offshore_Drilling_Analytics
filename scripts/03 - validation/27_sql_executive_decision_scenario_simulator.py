from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np


# =============================================================================
# STAGE 2G.14
# EXECUTIVE DECISION INTELLIGENCE & SCENARIO SIMULATOR
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.14_Executive_Decision_Scenario_Simulator"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.14_Executive_Decision_Scenario_Simulator.xlsx"
)


# =============================================================================
# VALIDATED ECONOMIC BASELINE
# =============================================================================

VALIDATED_TOTAL_IMPACT = 198_150_178.00
VALIDATED_TARGET_SAVINGS = 30_825_850.00
VALIDATED_CONSERVATIVE_SAVINGS = 15_412_920.00
VALIDATED_STRETCH_SAVINGS = 46_238_770.00

CONSERVATIVE_RATE = (
    VALIDATED_CONSERVATIVE_SAVINGS
    / VALIDATED_TOTAL_IMPACT
)

TARGET_RATE = (
    VALIDATED_TARGET_SAVINGS
    / VALIDATED_TOTAL_IMPACT
)

STRETCH_RATE = (
    VALIDATED_STRETCH_SAVINGS
    / VALIDATED_TOTAL_IMPACT
)


# =============================================================================
# HEADER
# =============================================================================

print("=" * 80)
print("STAGE 2G.14 — EXECUTIVE DECISION INTELLIGENCE")
print("SCENARIO SIMULATOR")
print("=" * 80)

print()
print(f"Project root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")
print()


# =============================================================================
# LOAD DATABASE
# =============================================================================

conn = sqlite3.connect(DB_PATH)

npt = pd.read_sql_query(
    "SELECT * FROM Fact_NPT",
    conn
)

drilling = pd.read_sql_query(
    "SELECT * FROM Fact_Drilling_Daily_Report",
    conn
)

wells = pd.read_sql_query(
    "SELECT * FROM Dim_Well",
    conn
)

rigs = pd.read_sql_query(
    "SELECT * FROM Dim_Rig",
    conn
)

conn.close()


print(f"NPT rows loaded      : {len(npt):,}")
print(f"Drilling rows loaded : {len(drilling):,}")
print(f"Well rows loaded     : {len(wells):,}")
print(f"Rig rows loaded      : {len(rigs):,}")
print()


# =============================================================================
# NUMERIC NORMALIZATION
# =============================================================================

numeric_npt = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
]

for col in numeric_npt:
    if col in npt.columns:
        npt[col] = pd.to_numeric(
            npt[col],
            errors="coerce"
        ).fillna(0)

for col in [
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Daily_Cost_USD",
]:
    if col in drilling.columns:
        drilling[col] = pd.to_numeric(
            drilling[col],
            errors="coerce"
        ).fillna(0)


# =============================================================================
# BASELINE
# =============================================================================

baseline_npt_events = len(npt)

baseline_npt_hours = npt["Duration_hr"].sum()

baseline_direct_cost = npt["Cost_USD"].sum()

baseline_deferred_cost = npt["Deferred_Cost_USD"].sum()

baseline_total_impact = npt["Total_Impact_USD"].sum()

baseline_footage = drilling["Daily_Footage_ft"].sum()

baseline_rop = drilling["ROP_ft_hr"].mean()

baseline_cost_per_foot = (
    drilling["Daily_Cost_USD"].sum()
    / baseline_footage
)

baseline_wells = npt["Well_ID"].nunique()

baseline_rigs = npt["Rig_ID"].nunique()


# =============================================================================
# 1. EXECUTIVE SCENARIOS
# =============================================================================

scenario_definitions = [
    [
        "BASELINE",
        "Current state",
        0.00,
        0.00,
        0.00,
        0.00,
    ],
    [
        "CONSERVATIVE",
        "20% improvement opportunity",
        0.20,
        CONSERVATIVE_RATE,
        VALIDATED_CONSERVATIVE_SAVINGS,
        0.20,
    ],
    [
        "TARGET",
        "Validated management target",
        0.40,
        TARGET_RATE,
        VALIDATED_TARGET_SAVINGS,
        0.40,
    ],
    [
        "STRETCH",
        "60% improvement opportunity",
        0.60,
        STRETCH_RATE,
        VALIDATED_STRETCH_SAVINGS,
        0.60,
    ],
]

executive_scenarios = pd.DataFrame(
    scenario_definitions,
    columns=[
        "Scenario",
        "Description",
        "Improvement_Rate",
        "Savings_Rate",
        "Validated_Savings_USD",
        "NPT_Reduction_Rate",
    ]
)

executive_scenarios["NPT_Hours_Reduced"] = (
    baseline_npt_hours
    * executive_scenarios["NPT_Reduction_Rate"]
)

executive_scenarios["Remaining_NPT_Hours"] = (
    baseline_npt_hours
    - executive_scenarios["NPT_Hours_Reduced"]
)

executive_scenarios["Economic_Impact_Reduced_USD"] = (
    executive_scenarios["Validated_Savings_USD"]
)

executive_scenarios["Remaining_Economic_Impact_USD"] = (
    VALIDATED_TOTAL_IMPACT
    - executive_scenarios["Economic_Impact_Reduced_USD"]
)

executive_scenarios["Impact_Reduction_pct"] = (
    executive_scenarios["Economic_Impact_Reduced_USD"]
    / VALIDATED_TOTAL_IMPACT
)


# =============================================================================
# 2. SCENARIO IMPACT
# =============================================================================

scenario_impact = executive_scenarios[
    [
        "Scenario",
        "Description",
        "NPT_Hours_Reduced",
        "Remaining_NPT_Hours",
        "Economic_Impact_Reduced_USD",
        "Remaining_Economic_Impact_USD",
        "Impact_Reduction_pct",
    ]
].copy()


# =============================================================================
# 3. RIG SCENARIOS
# =============================================================================

rig_scenarios = (
    npt.groupby("Rig_ID")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Wells=("Well_ID", "nunique"),
    )
    .reset_index()
)

rig_scenarios["Target_Savings_USD"] = (
    rig_scenarios["Total_Impact_USD"]
    * TARGET_RATE
)

rig_scenarios["Conservative_Savings_USD"] = (
    rig_scenarios["Total_Impact_USD"]
    * CONSERVATIVE_RATE
)

rig_scenarios["Stretch_Savings_USD"] = (
    rig_scenarios["Total_Impact_USD"]
    * STRETCH_RATE
)

rig_scenarios["Target_NPT_Hours_Reduced"] = (
    rig_scenarios["NPT_Hours"]
    * 0.40
)

rig_scenarios["Remaining_NPT_Hours_Target"] = (
    rig_scenarios["NPT_Hours"]
    - rig_scenarios["Target_NPT_Hours_Reduced"]
)

rig_scenarios["Impact_Share_pct"] = (
    rig_scenarios["Total_Impact_USD"]
    / baseline_total_impact
)

rig_scenarios["Priority"] = pd.cut(
    rig_scenarios["Impact_Share_pct"],
    bins=[
        -np.inf,
        0.10,
        0.20,
        0.35,
        np.inf
    ],
    labels=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]
)

rig_scenarios = rig_scenarios.sort_values(
    "Total_Impact_USD",
    ascending=False
).reset_index(drop=True)

rig_scenarios.insert(
    0,
    "Rank",
    range(1, len(rig_scenarios) + 1)
)


# =============================================================================
# 4. ROOT CAUSE SCENARIOS
# =============================================================================

root_cause_scenarios = (
    npt.groupby(
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
        ]
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Wells=("Well_ID", "nunique"),
        Rigs=("Rig_ID", "nunique"),
    )
    .reset_index()
)

root_cause_scenarios["Target_Savings_USD"] = (
    root_cause_scenarios["Total_Impact_USD"]
    * TARGET_RATE
)

root_cause_scenarios["Target_NPT_Hours_Reduced"] = (
    root_cause_scenarios["NPT_Hours"]
    * 0.40
)

root_cause_scenarios["Impact_Share_pct"] = (
    root_cause_scenarios["Total_Impact_USD"]
    / baseline_total_impact
)

root_cause_scenarios["Priority"] = pd.cut(
    root_cause_scenarios["Impact_Share_pct"],
    bins=[
        -np.inf,
        0.01,
        0.02,
        0.04,
        np.inf
    ],
    labels=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]
)

root_cause_scenarios = root_cause_scenarios.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

root_cause_scenarios.insert(
    0,
    "Rank",
    range(1, len(root_cause_scenarios) + 1)
)


# =============================================================================
# 5. INITIATIVE SCENARIOS
# =============================================================================

initiative_map = {
    "Drilling Dysfunction Reduction Program":
        "INIT-001",

    "Mechanical Reliability Program":
        "INIT-002",

    "Weather & Marine Operations Resilience":
        "INIT-003",

    "Supply Chain & Logistics Optimization":
        "INIT-004",

    "People, Competency & Operational Readiness":
        "INIT-005",

    "Drilling Performance Optimization":
        "INIT-006",
}


npt["Initiative_Family"] = np.select(
    [
        npt["NPT_Category"].eq("Mechanical"),

        npt["NPT_Category"].eq("Weather"),

        npt["NPT_Category"].eq("Logistics"),

        npt["NPT_Category"].eq("Personnel"),

        (
            npt["NPT_Category"].eq("Drilling")
            & npt["Root_Cause"].str.contains(
                "Sticking|Fishing|Hole Cleaning|Lost Circulation|Bit Failure",
                case=False,
                na=False,
            )
        ),
    ],
    [
        "Mechanical Reliability Program",

        "Weather & Marine Operations Resilience",

        "Supply Chain & Logistics Optimization",

        "People, Competency & Operational Readiness",

        "Drilling Dysfunction Reduction Program",
    ],
    default="Drilling Performance Optimization",
)

initiative_scenarios = (
    npt.groupby("Initiative_Family")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Wells=("Well_ID", "nunique"),
        Rigs=("Rig_ID", "nunique"),
    )
    .reset_index()
)

initiative_scenarios["Initiative_ID"] = (
    initiative_scenarios["Initiative_Family"]
    .map(initiative_map)
)

initiative_scenarios["Target_Savings_USD"] = (
    initiative_scenarios["Total_Impact_USD"]
    * TARGET_RATE
)

initiative_scenarios["Conservative_Savings_USD"] = (
    initiative_scenarios["Total_Impact_USD"]
    * CONSERVATIVE_RATE
)

initiative_scenarios["Stretch_Savings_USD"] = (
    initiative_scenarios["Total_Impact_USD"]
    * STRETCH_RATE
)

initiative_scenarios["Target_NPT_Hours_Reduced"] = (
    initiative_scenarios["NPT_Hours"]
    * 0.40
)

initiative_scenarios["Priority"] = pd.cut(
    initiative_scenarios["Target_Savings_USD"]
    / VALIDATED_TARGET_SAVINGS,
    bins=[
        -np.inf,
        0.05,
        0.15,
        0.25,
        np.inf
    ],
    labels=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]
)

initiative_scenarios = initiative_scenarios.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

initiative_scenarios.insert(
    0,
    "Rank",
    range(1, len(initiative_scenarios) + 1)
)


# =============================================================================
# 6. SAVINGS CURVE
# =============================================================================

savings_curve = pd.DataFrame([
    [
        "BASELINE",
        0.00,
        0,
        VALIDATED_TOTAL_IMPACT,
        baseline_npt_hours,
    ],
    [
        "10% IMPROVEMENT",
        0.10,
        VALIDATED_TOTAL_IMPACT * 0.10,
        VALIDATED_TOTAL_IMPACT * 0.90,
        baseline_npt_hours * 0.90,
    ],
    [
        "20% IMPROVEMENT",
        0.20,
        VALIDATED_CONSERVATIVE_SAVINGS,
        VALIDATED_TOTAL_IMPACT
        - VALIDATED_CONSERVATIVE_SAVINGS,
        baseline_npt_hours * 0.80,
    ],
    [
        "30% IMPROVEMENT",
        0.30,
        VALIDATED_TOTAL_IMPACT * 0.30,
        VALIDATED_TOTAL_IMPACT * 0.70,
        baseline_npt_hours * 0.70,
    ],
    [
        "40% TARGET",
        0.40,
        VALIDATED_TARGET_SAVINGS,
        VALIDATED_TOTAL_IMPACT
        - VALIDATED_TARGET_SAVINGS,
        baseline_npt_hours * 0.60,
    ],
    [
        "50% IMPROVEMENT",
        0.50,
        VALIDATED_TOTAL_IMPACT * 0.50,
        VALIDATED_TOTAL_IMPACT * 0.50,
        baseline_npt_hours * 0.50,
    ],
    [
        "60% STRETCH",
        0.60,
        VALIDATED_STRETCH_SAVINGS,
        VALIDATED_TOTAL_IMPACT
        - VALIDATED_STRETCH_SAVINGS,
        baseline_npt_hours * 0.40,
    ],
], columns=[
    "Scenario",
    "Improvement_Rate",
    "Savings_USD",
    "Remaining_Impact_USD",
    "Remaining_NPT_Hours",
])


# =============================================================================
# 7. KPI SCENARIO IMPACT
# =============================================================================

kpi_scenario_impact = pd.DataFrame([
    [
        "NPT Hours",
        baseline_npt_hours,
        baseline_npt_hours * 0.80,
        baseline_npt_hours * 0.60,
        baseline_npt_hours * 0.40,
        "Minimize",
    ],
    [
        "Economic Impact",
        VALIDATED_TOTAL_IMPACT,
        VALIDATED_TOTAL_IMPACT
        - VALIDATED_CONSERVATIVE_SAVINGS,
        VALIDATED_TOTAL_IMPACT
        - VALIDATED_TARGET_SAVINGS,
        VALIDATED_TOTAL_IMPACT
        - VALIDATED_STRETCH_SAVINGS,
        "Minimize",
    ],
    [
        "Target Savings",
        0,
        VALIDATED_CONSERVATIVE_SAVINGS,
        VALIDATED_TARGET_SAVINGS,
        VALIDATED_STRETCH_SAVINGS,
        "Maximize",
    ],
], columns=[
    "KPI",
    "Baseline",
    "Conservative",
    "Target",
    "Stretch",
    "Direction",
])


# =============================================================================
# 8. DECISION MATRIX
# =============================================================================

top_rig = rig_scenarios.iloc[0]

top_root = root_cause_scenarios.iloc[0]

top_initiative = initiative_scenarios.iloc[0]

decision_matrix = pd.DataFrame([
    [
        "DEC-001",
        "Rig",
        f"Prioritize {top_rig['Rig_ID']}",
        top_rig["Target_Savings_USD"],
        "CRITICAL",
        "Highest rig economic exposure",
        "Rig Management",
        "Immediate",
    ],
    [
        "DEC-002",
        "Root Cause",
        f"Address {top_root['Root_Cause']}",
        top_root["Target_Savings_USD"],
        "CRITICAL",
        "Highest target savings root cause",
        "Operations / Engineering",
        "Immediate",
    ],
    [
        "DEC-003",
        "Initiative",
        f"Accelerate {top_initiative['Initiative_ID']}",
        top_initiative["Target_Savings_USD"],
        "CRITICAL",
        "Highest-value management initiative",
        "Management",
        "30 Days",
    ],
    [
        "DEC-004",
        "Portfolio",
        "Execute TARGET scenario",
        VALIDATED_TARGET_SAVINGS,
        "CRITICAL",
        "Validated savings objective",
        "Executive Management",
        "90 Days",
    ],
    [
        "DEC-005",
        "Portfolio",
        "Prepare STRETCH scenario",
        VALIDATED_STRETCH_SAVINGS,
        "HIGH",
        "Upside opportunity after target execution",
        "Executive Management",
        "180 Days",
    ],
], columns=[
    "Decision_ID",
    "Decision_Area",
    "Decision",
    "Target_Value_USD",
    "Priority",
    "Rationale",
    "Owner",
    "Time_Horizon",
])


# =============================================================================
# 9. ASSUMPTIONS
# =============================================================================

assumptions = pd.DataFrame([
    [
        "Economic baseline",
        "Stage 2G.10.1 validated total economic impact",
        VALIDATED_TOTAL_IMPACT,
    ],
    [
        "Conservative savings",
        "Validated Stage 2G.10.1 savings",
        VALIDATED_CONSERVATIVE_SAVINGS,
    ],
    [
        "Target savings",
        "Validated Stage 2G.10.1 savings",
        VALIDATED_TARGET_SAVINGS,
    ],
    [
        "Stretch savings",
        "Validated Stage 2G.10.1 savings",
        VALIDATED_STRETCH_SAVINGS,
    ],
    [
        "Conservative improvement",
        "Scenario assumption",
        0.20,
    ],
    [
        "Target improvement",
        "Scenario assumption",
        0.40,
    ],
    [
        "Stretch improvement",
        "Scenario assumption",
        0.60,
    ],
    [
        "Savings allocation",
        "Proportional allocation by economic impact",
        "Impact-weighted",
    ],
    [
        "Economic principle",
        "No double counting across scenarios",
        "Validated baseline",
    ],
], columns=[
    "Assumption",
    "Definition",
    "Value",
])


# =============================================================================
# 10. DATA QUALITY
# =============================================================================

economic_difference = (
    baseline_total_impact
    - VALIDATED_TOTAL_IMPACT
)

target_difference = (
    executive_scenarios[
        "Validated_Savings_USD"
    ].sum()
    - (
        VALIDATED_CONSERVATIVE_SAVINGS
        + VALIDATED_TARGET_SAVINGS
        + VALIDATED_STRETCH_SAVINGS
    )
)


dq_rows = [
    [
        "NPT rows",
        len(npt),
        677,
        "PASS" if len(npt) == 677 else "FAIL",
    ],
    [
        "Drilling rows",
        len(drilling),
        1474,
        "PASS" if len(drilling) == 1474 else "FAIL",
    ],
    [
        "Unique NPT IDs",
        npt["NPT_ID"].nunique(),
        677,
        "PASS"
        if npt["NPT_ID"].nunique() == 677
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
        "Economic Reconciliation",
        economic_difference,
        0,
        "PASS"
        if abs(economic_difference) < 0.01
        else "FAIL",
    ],
    [
        "Target Savings Positive",
        VALIDATED_TARGET_SAVINGS,
        "> 0",
        "PASS"
        if VALIDATED_TARGET_SAVINGS > 0
        else "FAIL",
    ],
    [
        "Rig Scenarios",
        len(rig_scenarios),
        4,
        "PASS"
        if len(rig_scenarios) == 4
        else "FAIL",
    ],
    [
        "Initiative Scenarios",
        len(initiative_scenarios),
        6,
        "PASS"
        if len(initiative_scenarios) == 6
        else "FAIL",
    ],
]

data_quality = pd.DataFrame(
    dq_rows,
    columns=[
        "Check",
        "Actual",
        "Expected",
        "Status",
    ]
)

overall_status = (
    "PASS"
    if (data_quality["Status"] == "PASS").all()
    else "FAIL"
)


# =============================================================================
# 11. EXPORT
# =============================================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    executive_scenarios.to_excel(
        writer,
        sheet_name="Executive_Scenarios",
        index=False
    )

    scenario_impact.to_excel(
        writer,
        sheet_name="Scenario_Impact",
        index=False
    )

    rig_scenarios.to_excel(
        writer,
        sheet_name="Rig_Scenarios",
        index=False
    )

    root_cause_scenarios.to_excel(
        writer,
        sheet_name="Root_Cause_Scenarios",
        index=False
    )

    initiative_scenarios.to_excel(
        writer,
        sheet_name="Initiative_Scenarios",
        index=False
    )

    savings_curve.to_excel(
        writer,
        sheet_name="Savings_Curve",
        index=False
    )

    decision_matrix.to_excel(
        writer,
        sheet_name="Decision_Matrix",
        index=False
    )

    kpi_scenario_impact.to_excel(
        writer,
        sheet_name="KPI_Scenario_Impact",
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
# 12. BASIC FORMATTING
# =============================================================================

from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

wb = load_workbook(OUTPUT_FILE)

for ws in wb.worksheets:

    ws.freeze_panes = "A2"

    for cell in ws[1]:

        cell.font = Font(
            bold=True
        )

        cell.alignment = Alignment(
            horizontal="center"
        )

    for col in range(
        1,
        ws.max_column + 1
    ):

        max_length = 0

        for row in range(
            1,
            ws.max_row + 1
        ):

            value = ws.cell(
                row=row,
                column=col
            ).value

            if value is not None:

                max_length = max(
                    max_length,
                    len(str(value))
                )

        ws.column_dimensions[
            get_column_letter(col)
        ].width = min(
            max(max_length + 2, 12),
            45
        )

wb.save(OUTPUT_FILE)


# =============================================================================
# 13. FINAL REPORT
# =============================================================================

print()
print("=" * 80)
print("STAGE 2G.14 — RESULTS")
print("=" * 80)
print()

print(
    f"Baseline NPT events       : "
    f"{baseline_npt_events:,}"
)

print(
    f"Baseline NPT hours        : "
    f"{baseline_npt_hours:,.2f}"
)

print(
    f"Baseline economic impact  : "
    f"${baseline_total_impact:,.2f}"
)

print()

print(
    f"Conservative savings      : "
    f"${VALIDATED_CONSERVATIVE_SAVINGS:,.2f}"
)

print(
    f"Target savings            : "
    f"${VALIDATED_TARGET_SAVINGS:,.2f}"
)

print(
    f"Stretch savings           : "
    f"${VALIDATED_STRETCH_SAVINGS:,.2f}"
)

print()

print("Scenario NPT reduction:")

for _, row in executive_scenarios.iterrows():

    print(
        f"  {row['Scenario']:12s} | "
        f"{row['NPT_Hours_Reduced']:,.1f} h reduced | "
        f"{row['Remaining_NPT_Hours']:,.1f} h remaining"
    )

print()

print("Top Rig:")
print(
    f"  {top_rig['Rig_ID']} | "
    f"{top_rig['NPT_Hours']:,.0f} h | "
    f"${top_rig['Total_Impact_USD']:,.2f} impact | "
    f"${top_rig['Target_Savings_USD']:,.2f} target savings"
)

print()

print("Top Root Cause:")
print(
    f"  {top_root['Root_Cause']} | "
    f"${top_root['Total_Impact_USD']:,.2f} impact | "
    f"${top_root['Target_Savings_USD']:,.2f} target savings"
)

print()

print("Top Initiative:")
print(
    f"  {top_initiative['Initiative_ID']} | "
    f"{top_initiative['Initiative_Family']} | "
    f"${top_initiative['Target_Savings_USD']:,.2f} target savings"
)

print()

print("Data Quality:")
print(
    data_quality.to_string(
        index=False
    )
)

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
print("STAGE 2G.14 COMPLETED")
print("=" * 80)
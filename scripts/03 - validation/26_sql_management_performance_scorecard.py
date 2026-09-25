from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np


# =============================================================================
# STAGE 2G.13
# MANAGEMENT PERFORMANCE SCORECARD
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.13_Management_Performance_Scorecard"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.13_Management_Performance_Scorecard.xlsx"
)


# =============================================================================
# VALIDATED ECONOMIC BASELINE
# =============================================================================

VALIDATED_TOTAL_IMPACT = 198_150_178.00
VALIDATED_TARGET_SAVINGS = 30_825_850.00
VALIDATED_CONSERVATIVE_SAVINGS = 15_412_920.00
VALIDATED_STRETCH_SAVINGS = 46_238_770.00


# =============================================================================
# HEADER
# =============================================================================

print("=" * 80)
print("STAGE 2G.13 — MANAGEMENT PERFORMANCE SCORECARD")
print("EXECUTIVE DECISION DASHBOARD")
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

dates = pd.read_sql_query(
    "SELECT * FROM Dim_Date",
    conn
)

conn.close()


print(f"NPT rows loaded      : {len(npt):,}")
print(f"Drilling rows loaded : {len(drilling):,}")
print(f"Well rows loaded     : {len(wells):,}")
print(f"Rig rows loaded      : {len(rigs):,}")
print(f"Date rows loaded     : {len(dates):,}")
print()


# =============================================================================
# NUMERIC NORMALIZATION
# =============================================================================

for col in [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Lost_Drilling_Days",
    "Productivity_Loss_pct",
]:
    if col in npt.columns:
        npt[col] = pd.to_numeric(
            npt[col],
            errors="coerce"
        ).fillna(0)

for col in [
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Daily_Cost_USD",
    "Weather_Delay_hr",
]:
    if col in drilling.columns:
        drilling[col] = pd.to_numeric(
            drilling[col],
            errors="coerce"
        ).fillna(0)


# =============================================================================
# 1. EXECUTIVE SCORECARD
# =============================================================================

total_npt_events = len(npt)

total_npt_hours = npt["Duration_hr"].sum()

direct_npt_cost = npt["Cost_USD"].sum()

deferred_cost = npt["Deferred_Cost_USD"].sum()

calculated_total_impact = npt["Total_Impact_USD"].sum()

unique_wells = npt["Well_ID"].nunique()

unique_rigs = npt["Rig_ID"].nunique()

total_footage = drilling["Daily_Footage_ft"].sum()

average_rop = (
    drilling["ROP_ft_hr"].mean()
    if len(drilling) > 0
    else 0
)

cost_per_foot = (
    drilling["Daily_Cost_USD"].sum() / total_footage
    if total_footage > 0
    else 0
)

npt_hours_per_well = (
    total_npt_hours / unique_wells
    if unique_wells > 0
    else 0
)

npt_cost_per_event = (
    direct_npt_cost / total_npt_events
    if total_npt_events > 0
    else 0
)

target_savings_rate = (
    VALIDATED_TARGET_SAVINGS
    / VALIDATED_TOTAL_IMPACT
)

executive_scorecard = pd.DataFrame([
    ["NPT Events", total_npt_events, "events"],
    ["NPT Hours", total_npt_hours, "hours"],
    ["Direct NPT Cost", direct_npt_cost, "USD"],
    ["Deferred Cost", deferred_cost, "USD"],
    ["Total Economic Impact", calculated_total_impact, "USD"],
    ["Validated Target Savings", VALIDATED_TARGET_SAVINGS, "USD"],
    ["Validated Conservative Savings", VALIDATED_CONSERVATIVE_SAVINGS, "USD"],
    ["Validated Stretch Savings", VALIDATED_STRETCH_SAVINGS, "USD"],
    ["Target Savings Rate", target_savings_rate, "%"],
    ["Unique Wells", unique_wells, "wells"],
    ["Unique Rigs", unique_rigs, "rigs"],
    ["Total Footage", total_footage, "ft"],
    ["Average ROP", average_rop, "ft/hr"],
    ["Cost per Foot", cost_per_foot, "USD/ft"],
    ["NPT Hours per Well", npt_hours_per_well, "hr/well"],
    ["Direct NPT Cost per Event", npt_cost_per_event, "USD/event"],
], columns=[
    "KPI",
    "Value",
    "Unit",
])


# =============================================================================
# 2. MANAGEMENT DASHBOARD
# =============================================================================

impact_gap = (
    VALIDATED_TOTAL_IMPACT
    - calculated_total_impact
)

management_dashboard = pd.DataFrame([
    [
        "Operational Exposure",
        "Total NPT Hours",
        total_npt_hours,
        "4,008",
        "HIGH" if total_npt_hours > 3500 else "MEDIUM"
    ],
    [
        "Economic Exposure",
        "Total Economic Impact",
        calculated_total_impact,
        VALIDATED_TOTAL_IMPACT,
        "CRITICAL"
        if calculated_total_impact >= 150_000_000
        else "HIGH"
    ],
    [
        "Savings Opportunity",
        "Target Savings",
        VALIDATED_TARGET_SAVINGS,
        VALIDATED_TARGET_SAVINGS,
        "CRITICAL"
        if VALIDATED_TARGET_SAVINGS >= 25_000_000
        else "HIGH"
    ],
    [
        "Rig Exposure",
        "Highest NPT Rig",
        "",
        "",
        "REVIEW"
    ],
    [
        "Root Cause Exposure",
        "Highest Impact Root Cause",
        "",
        "",
        "REVIEW"
    ],
    [
        "Initiative Portfolio",
        "Critical Initiatives",
        3,
        3,
        "CRITICAL"
    ],
], columns=[
    "Management_Area",
    "Metric",
    "Actual",
    "Reference",
    "Priority",
])


# =============================================================================
# 3. RIG SCORECARD
# =============================================================================

rig_scorecard = (
    npt.groupby("Rig_ID")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost=("Cost_USD", "sum"),
        Deferred_Cost=("Deferred_Cost_USD", "sum"),
        Total_Impact=("Total_Impact_USD", "sum"),
        Wells=("Well_ID", "nunique"),
    )
    .reset_index()
)

rig_scorecard["Impact_per_NPT_Hour"] = (
    rig_scorecard["Total_Impact"]
    / rig_scorecard["NPT_Hours"].replace(0, np.nan)
)

rig_scorecard["Impact_per_Well"] = (
    rig_scorecard["Total_Impact"]
    / rig_scorecard["Wells"].replace(0, np.nan)
)

rig_scorecard["Impact_Share_pct"] = (
    rig_scorecard["Total_Impact"]
    / calculated_total_impact
)

rig_scorecard["Management_Priority"] = pd.cut(
    rig_scorecard["Impact_Share_pct"],
    bins=[-np.inf, 0.10, 0.20, 0.35, np.inf],
    labels=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]
)

rig_scorecard = rig_scorecard.sort_values(
    "Total_Impact",
    ascending=False
).reset_index(drop=True)

rig_scorecard.insert(
    0,
    "Rank",
    range(1, len(rig_scorecard) + 1)
)


# =============================================================================
# 4. WELL SCORECARD
# =============================================================================

well_scorecard = (
    npt.groupby("Well_ID")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost=("Cost_USD", "sum"),
        Deferred_Cost=("Deferred_Cost_USD", "sum"),
        Total_Impact=("Total_Impact_USD", "sum"),
        Rig_ID=("Rig_ID", "first"),
    )
    .reset_index()
)

well_scorecard["Impact_Share_pct"] = (
    well_scorecard["Total_Impact"]
    / calculated_total_impact
)

well_scorecard["Management_Priority"] = pd.cut(
    well_scorecard["Impact_Share_pct"],
    bins=[-np.inf, 0.01, 0.02, 0.04, np.inf],
    labels=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]
)

well_scorecard = well_scorecard.sort_values(
    "Total_Impact",
    ascending=False
).reset_index(drop=True)

well_scorecard.insert(
    0,
    "Rank",
    range(1, len(well_scorecard) + 1)
)


# =============================================================================
# 5. ROOT CAUSE SCORECARD
# =============================================================================

root_cause_scorecard = (
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
        Direct_NPT_Cost=("Cost_USD", "sum"),
        Deferred_Cost=("Deferred_Cost_USD", "sum"),
        Total_Impact=("Total_Impact_USD", "sum"),
        Wells=("Well_ID", "nunique"),
        Rigs=("Rig_ID", "nunique"),
    )
    .reset_index()
)

root_cause_scorecard["Impact_Share_pct"] = (
    root_cause_scorecard["Total_Impact"]
    / calculated_total_impact
)

root_cause_scorecard["Management_Priority"] = pd.cut(
    root_cause_scorecard["Impact_Share_pct"],
    bins=[-np.inf, 0.01, 0.02, 0.04, np.inf],
    labels=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]
)

root_cause_scorecard = root_cause_scorecard.sort_values(
    "Total_Impact",
    ascending=False
).reset_index(drop=True)

root_cause_scorecard.insert(
    0,
    "Rank",
    range(1, len(root_cause_scorecard) + 1)
)


# =============================================================================
# 6. INITIATIVE SCORECARD
# =============================================================================

initiative_output = (
    npt.groupby(
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party",
            "Corrective_Action",
        ]
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
    )
    .reset_index()
)

initiative_output["Target_Savings_USD"] = (
    initiative_output["Total_Impact_USD"]
    * target_savings_rate
)

initiative_output["Savings_Share_pct"] = (
    initiative_output["Target_Savings_USD"]
    / VALIDATED_TARGET_SAVINGS
)

initiative_output = initiative_output.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

initiative_output.insert(
    0,
    "Rank",
    range(1, len(initiative_output) + 1)
)

initiative_output["Management_Priority"] = pd.cut(
    initiative_output["Savings_Share_pct"],
    bins=[-np.inf, 0.01, 0.02, 0.04, np.inf],
    labels=[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]
)


# =============================================================================
# 7. ECONOMIC SCORECARD
# =============================================================================

economic_scorecard = pd.DataFrame([
    [
        "Direct NPT Cost",
        direct_npt_cost,
        calculated_total_impact,
        direct_npt_cost / calculated_total_impact
    ],
    [
        "Deferred Cost",
        deferred_cost,
        calculated_total_impact,
        deferred_cost / calculated_total_impact
    ],
    [
        "Total Economic Impact",
        calculated_total_impact,
        VALIDATED_TOTAL_IMPACT,
        calculated_total_impact / VALIDATED_TOTAL_IMPACT
    ],
    [
        "Conservative Savings",
        VALIDATED_CONSERVATIVE_SAVINGS,
        VALIDATED_TOTAL_IMPACT,
        VALIDATED_CONSERVATIVE_SAVINGS / VALIDATED_TOTAL_IMPACT
    ],
    [
        "Target Savings",
        VALIDATED_TARGET_SAVINGS,
        VALIDATED_TOTAL_IMPACT,
        VALIDATED_TARGET_SAVINGS / VALIDATED_TOTAL_IMPACT
    ],
    [
        "Stretch Savings",
        VALIDATED_STRETCH_SAVINGS,
        VALIDATED_TOTAL_IMPACT,
        VALIDATED_STRETCH_SAVINGS / VALIDATED_TOTAL_IMPACT
    ],
], columns=[
    "Metric",
    "Value_USD",
    "Reference_USD",
    "Share_of_Total_Impact",
])


# =============================================================================
# 8. KPI FRAMEWORK
# =============================================================================

kpi_framework = pd.DataFrame([
    [
        "NPT Hours",
        "Operational Efficiency",
        "Total non-productive time",
        "Minimize",
        total_npt_hours,
        "< 3,000 hr",
        "Monthly",
        "Wells / Operations",
    ],
    [
        "NPT Cost",
        "Economic Performance",
        "Direct NPT cost",
        "Minimize",
        direct_npt_cost,
        "< $60M",
        "Monthly",
        "Finance / Wells",
    ],
    [
        "Total Economic Impact",
        "Economic Exposure",
        "NPT + deferred impact",
        "Minimize",
        calculated_total_impact,
        "< $150M",
        "Monthly",
        "Management",
    ],
    [
        "Average ROP",
        "Drilling Performance",
        "Average drilling rate",
        "Maximize",
        average_rop,
        "> 35 ft/hr",
        "Weekly",
        "Drilling",
    ],
    [
        "Cost per Foot",
        "Cost Efficiency",
        "Daily drilling cost / footage",
        "Minimize",
        cost_per_foot,
        "< $600/ft",
        "Weekly",
        "Finance / Drilling",
    ],
    [
        "Target Savings",
        "Improvement",
        "Validated target savings",
        "Maximize",
        VALIDATED_TARGET_SAVINGS,
        "> $30M",
        "Monthly",
        "Management",
    ],
    [
        "NPT Hours per Well",
        "Well Performance",
        "NPT hours normalized by wells",
        "Minimize",
        npt_hours_per_well,
        "< 60 hr/well",
        "Per Well",
        "Well Engineering",
    ],
], columns=[
    "KPI",
    "Domain",
    "Definition",
    "Direction",
    "Baseline",
    "Target",
    "Frequency",
    "Owner",
])


# =============================================================================
# 9. DECISION REGISTER
# =============================================================================

top_rig = rig_scorecard.iloc[0]

top_root = root_cause_scorecard.iloc[0]

decision_register = pd.DataFrame([
    [
        "DEC-001",
        "Rig Performance",
        f"Intervene on Rig {top_rig['Rig_ID']}",
        top_rig["Total_Impact"],
        "CRITICAL",
        "Rig with highest economic exposure",
        "Rig Management",
        "Immediate",
    ],
    [
        "DEC-002",
        "Root Cause",
        f"Address {top_root['Root_Cause']}",
        top_root["Total_Impact"],
        "CRITICAL",
        "Highest-impact root cause",
        "Operations / Engineering",
        "Immediate",
    ],
    [
        "DEC-003",
        "Savings",
        "Execute validated target savings portfolio",
        VALIDATED_TARGET_SAVINGS,
        "CRITICAL",
        "Validated improvement opportunity",
        "Management",
        "90 Days",
    ],
    [
        "DEC-004",
        "NPT Reduction",
        "Reduce total NPT exposure",
        total_npt_hours,
        "HIGH",
        "4,008 baseline NPT hours",
        "Operations",
        "90 Days",
    ],
    [
        "DEC-005",
        "Drilling Performance",
        "Improve average ROP",
        average_rop,
        "HIGH",
        "Average ROP below strategic target",
        "Drilling Engineering",
        "90 Days",
    ],
], columns=[
    "Decision_ID",
    "Decision_Area",
    "Decision",
    "Economic_or_Operational_Value",
    "Priority",
    "Rationale",
    "Owner",
    "Time_Horizon",
])


# =============================================================================
# 10. DATA QUALITY
# =============================================================================

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
        impact_gap,
        0,
        "PASS"
        if abs(impact_gap) < 0.01
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
        "Rig Scorecard",
        len(rig_scorecard),
        4,
        "PASS"
        if len(rig_scorecard) == 4
        else "FAIL",
    ],
    [
        "Well Scorecard",
        len(well_scorecard),
        50,
        "PASS"
        if len(well_scorecard) == 50
        else "FAIL",
    ],
]

dq_rows = pd.DataFrame(
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
    if (dq_rows["Status"] == "PASS").all()
    else "FAIL"
)

# =============================================================================
# 11. UPDATE MANAGEMENT DASHBOARD
# =============================================================================

management_dashboard.loc[
    management_dashboard["Metric"] == "Highest NPT Rig",
    "Actual"
] = top_rig["Rig_ID"]

management_dashboard.loc[
    management_dashboard["Metric"] == "Highest NPT Rig",
    "Reference"
] = top_rig["Total_Impact"]

management_dashboard.loc[
    management_dashboard["Metric"] == "Highest Impact Root Cause",
    "Actual"
] = top_root["Root_Cause"]

management_dashboard.loc[
    management_dashboard["Metric"] == "Highest Impact Root Cause",
    "Reference"
] = top_root["Total_Impact"]


# =============================================================================
# 12. EXPORT
# =============================================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    executive_scorecard.to_excel(
        writer,
        sheet_name="Executive_Scorecard",
        index=False
    )

    management_dashboard.to_excel(
        writer,
        sheet_name="Management_Dashboard",
        index=False
    )

    rig_scorecard.to_excel(
        writer,
        sheet_name="Rig_Scorecard",
        index=False
    )

    well_scorecard.to_excel(
        writer,
        sheet_name="Well_Scorecard",
        index=False
    )

    root_cause_scorecard.to_excel(
        writer,
        sheet_name="Root_Cause_Scorecard",
        index=False
    )

    initiative_output.to_excel(
        writer,
        sheet_name="Initiative_Scorecard",
        index=False
    )

    economic_scorecard.to_excel(
        writer,
        sheet_name="Economic_Scorecard",
        index=False
    )

    kpi_framework.to_excel(
        writer,
        sheet_name="KPI_Framework",
        index=False
    )

    decision_register.to_excel(
        writer,
        sheet_name="Decision_Register",
        index=False
    )

    dq_rows.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# =============================================================================
# 13. OUTPUT FORMATTING
# =============================================================================

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
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
# FINAL REPORT
# =============================================================================

print()
print("=" * 80)
print("STAGE 2G.13 — RESULTS")
print("=" * 80)
print()

print(f"NPT events                : {total_npt_events:,}")
print(f"NPT hours                 : {total_npt_hours:,.2f}")
print(f"Direct NPT cost           : ${direct_npt_cost:,.2f}")
print(f"Deferred cost             : ${deferred_cost:,.2f}")
print(f"Total economic impact     : ${calculated_total_impact:,.2f}")
print()

print(
    f"Validated target savings  : "
    f"${VALIDATED_TARGET_SAVINGS:,.2f}"
)

print(
    f"Target savings rate       : "
    f"{target_savings_rate:.4%}"
)

print()

print(f"Unique wells              : {unique_wells}")
print(f"Unique rigs               : {unique_rigs}")
print(f"Total footage             : {total_footage:,.2f} ft")
print(f"Average ROP               : {average_rop:,.2f} ft/hr")
print(f"Cost per foot             : ${cost_per_foot:,.2f}")
print()

print("Top Rig:")
print(
    f"  {top_rig['Rig_ID']} | "
    f"{int(top_rig['NPT_Events'])} events | "
    f"{top_rig['NPT_Hours']:,.0f} h | "
    f"${top_rig['Total_Impact']:,.2f}"
)

print()

print("Top Root Cause:")
print(
    f"  {top_root['NPT_Category']} | "
    f"{top_root['NPT_Subcategory']} | "
    f"{top_root['Root_Cause']} | "
    f"${top_root['Total_Impact']:,.2f}"
)

print()

print("Data Quality:")
print(
    dq_rows.to_string(
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
print("STAGE 2G.13 COMPLETED")
print("=" * 80)
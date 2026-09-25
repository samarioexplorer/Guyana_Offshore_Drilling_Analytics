import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np


# =============================================================================
# STAGE 2G.12 — KPI MONITORING & OPERATIONAL PERFORMANCE DASHBOARD
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.12_KPI_Monitoring_Dashboard"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.12_KPI_Monitoring_Dashboard.xlsx"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# HELPERS
# =============================================================================

def money(x):
    return float(x) if pd.notna(x) else 0.0


def safe_div(a, b):
    if b == 0 or pd.isna(b):
        return 0.0
    return a / b


def priority_from_score(score):
    if score >= 75:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    return "LOW"


# =============================================================================
# HEADER
# =============================================================================

print("=" * 80)
print("STAGE 2G.12 — KPI MONITORING & OPERATIONAL PERFORMANCE DASHBOARD")
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

well = pd.read_sql_query(
    """
    SELECT *
    FROM Dim_Well
    """,
    conn
)

rig = pd.read_sql_query(
    """
    SELECT *
    FROM Dim_Rig
    """,
    conn
)

date_dim = pd.read_sql_query(
    """
    SELECT *
    FROM Dim_Date
    """,
    conn
)

conn.close()


print(f"NPT rows loaded      : {len(npt):,}")
print(f"Drilling rows loaded : {len(drilling):,}")
print(f"Well rows loaded     : {len(well):,}")
print(f"Rig rows loaded      : {len(rig):,}")
print(f"Date rows loaded     : {len(date_dim):,}")
print()


# =============================================================================
# DATE PREPARATION
# =============================================================================

npt["Date"] = pd.to_datetime(npt["Date"], errors="coerce")
drilling["Date"] = pd.to_datetime(drilling["Date"], errors="coerce")

npt["Month"] = npt["Date"].dt.to_period("M").astype(str)
npt["Quarter"] = (
    npt["Date"].dt.year.astype(str)
    + "-Q"
    + npt["Date"].dt.quarter.astype(str)
)

drilling["Month"] = drilling["Date"].dt.to_period("M").astype(str)
drilling["Quarter"] = (
    drilling["Date"].dt.year.astype(str)
    + "-Q"
    + drilling["Date"].dt.quarter.astype(str)
)


# =============================================================================
# NUMERIC CLEANUP
# =============================================================================

numeric_npt = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Lost_Drilling_Days",
    "Productivity_Loss_pct",
]

for col in numeric_npt:
    if col in npt.columns:
        npt[col] = pd.to_numeric(
            npt[col],
            errors="coerce"
        ).fillna(0)


numeric_drilling = [
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Daily_Cost_USD",
    "Weather_Delay_hr",
]

for col in numeric_drilling:
    if col in drilling.columns:
        drilling[col] = pd.to_numeric(
            drilling[col],
            errors="coerce"
        ).fillna(0)


# =============================================================================
# BASELINE KPI CALCULATIONS
# =============================================================================

npt_events = len(npt)

npt_hours = npt["Duration_hr"].sum()

direct_cost = npt["Cost_USD"].sum()

deferred_cost = npt["Deferred_Cost_USD"].sum()

economic_impact = npt["Total_Impact_USD"].sum()

unique_wells = npt["Well_ID"].nunique()

unique_rigs = npt["Rig_ID"].nunique()

drilling_days = drilling["Date"].nunique()

total_footage = drilling["Daily_Footage_ft"].sum()

average_rop = drilling["ROP_ft_hr"].mean()

total_drilling_cost = drilling["Daily_Cost_USD"].sum()

npt_rate = safe_div(npt_hours, drilling_days)

npt_cost_per_hour = safe_div(direct_cost, npt_hours)

cost_per_foot = safe_div(total_drilling_cost, total_footage)


# =============================================================================
# VALIDATED ECONOMIC BASELINE
#
# Stage 2G.10.1 validated:
# Total Impact = 198,150,178
# Target Savings = 30,825,850 approximately
#
# We preserve this validated Stage 2G.10.1 baseline here rather than
# recalculating savings from the Stage 2G.11.1 cluster structure.
# =============================================================================

VALIDATED_TOTAL_IMPACT = 198150178.00

VALIDATED_TARGET_SAVINGS = 30825850.00

VALIDATED_CONSERVATIVE_SAVINGS = 15412920.00

VALIDATED_STRETCH_SAVINGS = 46238770.00

target_savings_pct = safe_div(
    VALIDATED_TARGET_SAVINGS,
    VALIDATED_TOTAL_IMPACT
) * 100

conservative_savings_pct = safe_div(
    VALIDATED_CONSERVATIVE_SAVINGS,
    VALIDATED_TOTAL_IMPACT
) * 100

stretch_savings_pct = safe_div(
    VALIDATED_STRETCH_SAVINGS,
    VALIDATED_TOTAL_IMPACT
) * 100


# =============================================================================
# EXECUTIVE KPI TABLE
# =============================================================================

executive_kpi = pd.DataFrame([
    ["KPI001", "NPT Events", npt_events, "events"],
    ["KPI002", "NPT Hours", npt_hours, "hours"],
    ["KPI003", "Direct NPT Cost", direct_cost, "USD"],
    ["KPI004", "Deferred Cost", deferred_cost, "USD"],
    ["KPI005", "Total Economic Impact", economic_impact, "USD"],
    ["KPI006", "Validated Target Savings", VALIDATED_TARGET_SAVINGS, "USD"],
    ["KPI007", "Validated Conservative Savings",
     VALIDATED_CONSERVATIVE_SAVINGS, "USD"],
    ["KPI008", "Validated Stretch Savings",
     VALIDATED_STRETCH_SAVINGS, "USD"],
    ["KPI009", "Target Savings % of Impact",
     target_savings_pct, "%"],
    ["KPI010", "Unique Wells", unique_wells, "wells"],
    ["KPI011", "Unique Rigs", unique_rigs, "rigs"],
    ["KPI012", "Drilling Days", drilling_days, "days"],
    ["KPI013", "Total Footage", total_footage, "ft"],
    ["KPI014", "Average ROP", average_rop, "ft/hr"],
    ["KPI015", "Total Drilling Cost",
     total_drilling_cost, "USD"],
    ["KPI016", "Cost per Foot", cost_per_foot, "USD/ft"],
    ["KPI017", "NPT Hours per Drilling Day",
     npt_rate, "hr/day"],
    ["KPI018", "NPT Cost per NPT Hour",
     npt_cost_per_hour, "USD/hr"],
], columns=[
    "KPI_ID",
    "KPI_Name",
    "Value",
    "Unit"
])


# =============================================================================
# KPI FRAMEWORK
# =============================================================================

kpi_framework = pd.DataFrame([
    [
        "KPI001",
        "NPT Events",
        "COUNT(NPT_ID)",
        "Lower is better",
        "Daily",
        "Drilling Manager",
    ],
    [
        "KPI002",
        "NPT Hours",
        "SUM(Duration_hr)",
        "Lower is better",
        "Daily",
        "Drilling Manager",
    ],
    [
        "KPI003",
        "Direct NPT Cost",
        "SUM(Cost_USD)",
        "Lower is better",
        "Daily",
        "Operations Manager",
    ],
    [
        "KPI004",
        "Deferred Cost",
        "SUM(Deferred_Cost_USD)",
        "Lower is better",
        "Weekly",
        "Operations Manager",
    ],
    [
        "KPI005",
        "Total Economic Impact",
        "SUM(Total_Impact_USD)",
        "Lower is better",
        "Weekly",
        "Operations Manager",
    ],
    [
        "KPI006",
        "Target Savings",
        "Validated Stage 2G.10.1 baseline",
        "Higher is better",
        "Monthly",
        "Performance Manager",
    ],
    [
        "KPI007",
        "Average ROP",
        "AVG(ROP_ft_hr)",
        "Higher is better",
        "Daily",
        "Drilling Engineer",
    ],
    [
        "KPI008",
        "Cost per Foot",
        "SUM(Daily_Cost_USD)/SUM(Daily_Footage_ft)",
        "Lower is better",
        "Daily",
        "Drilling Engineer",
    ],
    [
        "KPI009",
        "NPT Hours per Drilling Day",
        "SUM(Duration_hr)/COUNT(DISTINCT Date)",
        "Lower is better",
        "Daily",
        "Drilling Manager",
    ],
    [
        "KPI010",
        "Savings Realization",
        "Realized Savings / Target Savings",
        "Higher is better",
        "Monthly",
        "Performance Manager",
    ],
], columns=[
    "KPI_ID",
    "KPI_Name",
    "Definition",
    "Direction",
    "Frequency",
    "Owner",
])


# =============================================================================
# RIG KPI
# =============================================================================

rig_kpi = (
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

rig_drilling = (
    drilling.groupby("Rig_ID")
    .agg(
        Drilling_Days=("Date", "nunique"),
        Footage_ft=("Daily_Footage_ft", "sum"),
        Avg_ROP_ft_hr=("ROP_ft_hr", "mean"),
        Drilling_Cost_USD=("Daily_Cost_USD", "sum"),
    )
    .reset_index()
)

rig_kpi = rig_kpi.merge(
    rig_drilling,
    on="Rig_ID",
    how="left"
)

rig_kpi["NPT_Hours_per_Drilling_Day"] = (
    rig_kpi["NPT_Hours"]
    / rig_kpi["Drilling_Days"].replace(0, np.nan)
)

rig_kpi["Cost_per_Foot_USD"] = (
    rig_kpi["Drilling_Cost_USD"]
    / rig_kpi["Footage_ft"].replace(0, np.nan)
)

rig_kpi["Target_Savings_USD"] = (
    rig_kpi["Total_Impact"]
    * target_savings_pct
    / 100
)

rig_kpi["Target_Savings_pct"] = (
    rig_kpi["Target_Savings_USD"]
    / rig_kpi["Total_Impact"].replace(0, np.nan)
    * 100
)

rig_kpi = rig_kpi.sort_values(
    "Total_Impact",
    ascending=False
).reset_index(drop=True)

rig_kpi["Performance_Rank"] = (
    rig_kpi.index + 1
)


# =============================================================================
# WELL KPI
# =============================================================================

well_kpi = (
    npt.groupby("Well_ID")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost=("Cost_USD", "sum"),
        Deferred_Cost=("Deferred_Cost_USD", "sum"),
        Total_Impact=("Total_Impact_USD", "sum"),
        Rigs=("Rig_ID", "nunique"),
    )
    .reset_index()
)

well_drilling = (
    drilling.groupby("Well_ID")
    .agg(
        Drilling_Days=("Date", "nunique"),
        Footage_ft=("Daily_Footage_ft", "sum"),
        Avg_ROP_ft_hr=("ROP_ft_hr", "mean"),
        Drilling_Cost_USD=("Daily_Cost_USD", "sum"),
    )
    .reset_index()
)

well_kpi = well_kpi.merge(
    well_drilling,
    on="Well_ID",
    how="left"
)

well_kpi["NPT_Hours_per_Drilling_Day"] = (
    well_kpi["NPT_Hours"]
    / well_kpi["Drilling_Days"].replace(0, np.nan)
)

well_kpi["Cost_per_Foot_USD"] = (
    well_kpi["Drilling_Cost_USD"]
    / well_kpi["Footage_ft"].replace(0, np.nan)
)

well_kpi["Target_Savings_USD"] = (
    well_kpi["Total_Impact"]
    * target_savings_pct
    / 100
)

well_kpi = well_kpi.sort_values(
    "Total_Impact",
    ascending=False
).reset_index(drop=True)

well_kpi["Performance_Rank"] = (
    well_kpi.index + 1
)


# =============================================================================
# ROOT CAUSE KPI
# =============================================================================

root_cause_kpi = (
    npt.groupby(
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party",
        ],
        dropna=False
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

root_cause_kpi["Impact_Share_pct"] = (
    root_cause_kpi["Total_Impact"]
    / economic_impact
    * 100
)

root_cause_kpi["Target_Savings_USD"] = (
    root_cause_kpi["Total_Impact"]
    * target_savings_pct
    / 100
)

root_cause_kpi["Priority"] = root_cause_kpi[
    "Total_Impact"
].rank(
    pct=True
) * 100

root_cause_kpi["Priority"] = root_cause_kpi[
    "Priority"
].apply(priority_from_score)

root_cause_kpi = root_cause_kpi.sort_values(
    "Total_Impact",
    ascending=False
).reset_index(drop=True)


# =============================================================================
# MONTHLY KPI
# =============================================================================

monthly_npt = (
    npt.groupby("Month")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost=("Cost_USD", "sum"),
        Deferred_Cost=("Deferred_Cost_USD", "sum"),
        Total_Impact=("Total_Impact_USD", "sum"),
    )
    .reset_index()
)

monthly_drilling = (
    drilling.groupby("Month")
    .agg(
        Drilling_Days=("Date", "nunique"),
        Footage_ft=("Daily_Footage_ft", "sum"),
        Avg_ROP_ft_hr=("ROP_ft_hr", "mean"),
        Drilling_Cost_USD=("Daily_Cost_USD", "sum"),
    )
    .reset_index()
)

monthly_kpi = monthly_npt.merge(
    monthly_drilling,
    on="Month",
    how="outer"
).fillna(0)

monthly_kpi["NPT_Hours_per_Drilling_Day"] = (
    monthly_kpi["NPT_Hours"]
    / monthly_kpi["Drilling_Days"].replace(0, np.nan)
)

monthly_kpi["Cost_per_Foot_USD"] = (
    monthly_kpi["Drilling_Cost_USD"]
    / monthly_kpi["Footage_ft"].replace(0, np.nan)
)

monthly_kpi["Target_Savings_USD"] = (
    monthly_kpi["Total_Impact"]
    * target_savings_pct
    / 100
)

monthly_kpi = monthly_kpi.sort_values(
    "Month"
).reset_index(drop=True)


# =============================================================================
# SAVINGS KPI
# =============================================================================

savings_kpi = pd.DataFrame([
    [
        "Conservative",
        VALIDATED_CONSERVATIVE_SAVINGS,
        conservative_savings_pct,
        "Validated Stage 2G.10.1",
    ],
    [
        "Target",
        VALIDATED_TARGET_SAVINGS,
        target_savings_pct,
        "Validated Stage 2G.10.1",
    ],
    [
        "Stretch",
        VALIDATED_STRETCH_SAVINGS,
        stretch_savings_pct,
        "Validated Stage 2G.10.1",
    ],
], columns=[
    "Scenario",
    "Savings_USD",
    "Savings_pct_of_Impact",
    "Baseline_Source",
])


# =============================================================================
# ACTION MONITORING
# =============================================================================

action_kpi = (
    npt.groupby(
        [
            "NPT_Category",
            "Root_Cause",
            "Responsible_Party",
            "Corrective_Action",
            "Action_Status",
        ],
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact=("Total_Impact_USD", "sum"),
    )
    .reset_index()
)

action_kpi["Target_Savings_USD"] = (
    action_kpi["Total_Impact"]
    * target_savings_pct
    / 100
)

action_kpi = action_kpi.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

action_kpi["Action_Rank"] = (
    action_kpi.index + 1
)


# =============================================================================
# DATA QUALITY
# =============================================================================

economic_difference = (
    economic_impact
    - VALIDATED_TOTAL_IMPACT
)

data_quality = pd.DataFrame([
    [
        "NPT rows",
        len(npt),
        677,
        "PASS" if len(npt) == 677 else "FAIL"
    ],
    [
        "Drilling rows",
        len(drilling),
        1474,
        "PASS" if len(drilling) == 1474 else "FAIL"
    ],
    [
        "Unique NPT IDs",
        npt["NPT_ID"].nunique(),
        len(npt),
        "PASS"
        if npt["NPT_ID"].nunique() == len(npt)
        else "FAIL"
    ],
    [
        "Duplicate NPT IDs",
        npt["NPT_ID"].duplicated().sum(),
        0,
        "PASS"
        if npt["NPT_ID"].duplicated().sum() == 0
        else "FAIL"
    ],
    [
        "Null NPT IDs",
        npt["NPT_ID"].isna().sum(),
        0,
        "PASS"
        if npt["NPT_ID"].isna().sum() == 0
        else "FAIL"
    ],
    [
        "Negative NPT Hours",
        (npt["Duration_hr"] < 0).sum(),
        0,
        "PASS"
        if (npt["Duration_hr"] < 0).sum() == 0
        else "FAIL"
    ],
    [
        "Negative Direct Cost",
        (npt["Cost_USD"] < 0).sum(),
        0,
        "PASS"
        if (npt["Cost_USD"] < 0).sum() == 0
        else "FAIL"
    ],
    [
        "Economic Difference vs Stage 2G.10.1",
        economic_difference,
        0,
        "PASS"
        if abs(economic_difference) < 0.01
        else "FAIL"
    ],
    [
        "Target Savings Positive",
        VALIDATED_TARGET_SAVINGS,
        "> 0",
        "PASS"
        if VALIDATED_TARGET_SAVINGS > 0
        else "FAIL"
    ],
], columns=[
    "Check",
    "Actual",
    "Expected",
    "Status"
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
    ["NPT Events", npt_events],
    ["NPT Hours", npt_hours],
    ["Direct NPT Cost USD", direct_cost],
    ["Deferred Cost USD", deferred_cost],
    ["Total Economic Impact USD", economic_impact],
    ["Validated Target Savings USD", VALIDATED_TARGET_SAVINGS],
    ["Validated Conservative Savings USD",
     VALIDATED_CONSERVATIVE_SAVINGS],
    ["Validated Stretch Savings USD",
     VALIDATED_STRETCH_SAVINGS],
    ["Target Savings %", target_savings_pct],
    ["Unique Wells", unique_wells],
    ["Unique Rigs", unique_rigs],
    ["Drilling Days", drilling_days],
    ["Total Footage ft", total_footage],
    ["Average ROP ft/hr", average_rop],
    ["Cost per Foot USD", cost_per_foot],
    ["NPT Hours per Drilling Day", npt_rate],
    ["Data Quality Status", overall_status],
], columns=[
    "Metric",
    "Value"
])


# =============================================================================
# WRITE EXCEL
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

    executive_kpi.to_excel(
        writer,
        sheet_name="KPI_Executive",
        index=False
    )

    kpi_framework.to_excel(
        writer,
        sheet_name="KPI_Framework",
        index=False
    )

    rig_kpi.to_excel(
        writer,
        sheet_name="KPI_Rig",
        index=False
    )

    well_kpi.to_excel(
        writer,
        sheet_name="KPI_Well",
        index=False
    )

    root_cause_kpi.to_excel(
        writer,
        sheet_name="KPI_Root_Cause",
        index=False
    )

    monthly_kpi.to_excel(
        writer,
        sheet_name="KPI_Monthly",
        index=False
    )

    savings_kpi.to_excel(
        writer,
        sheet_name="KPI_Savings",
        index=False
    )

    action_kpi.to_excel(
        writer,
        sheet_name="KPI_Action",
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
print("STAGE 2G.12 — RESULTS")
print("=" * 80)

print()

print(f"NPT events                  : {npt_events:,}")
print(f"NPT hours                   : {npt_hours:,.2f}")
print(f"Direct NPT cost             : ${direct_cost:,.2f}")
print(f"Deferred cost               : ${deferred_cost:,.2f}")
print(f"Total economic impact       : ${economic_impact:,.2f}")

print()
print(
    f"Validated target savings    : "
    f"${VALIDATED_TARGET_SAVINGS:,.2f}"
)

print(
    f"Validated conservative     : "
    f"${VALIDATED_CONSERVATIVE_SAVINGS:,.2f}"
)

print(
    f"Validated stretch          : "
    f"${VALIDATED_STRETCH_SAVINGS:,.2f}"
)

print()
print(f"Unique wells                : {unique_wells}")
print(f"Unique rigs                 : {unique_rigs}")
print(f"Drilling days               : {drilling_days:,}")
print(f"Total footage               : {total_footage:,.2f} ft")
print(f"Average ROP                 : {average_rop:,.2f} ft/hr")
print(f"Cost per foot               : ${cost_per_foot:,.2f}")
print()

print("Data Quality:")
print(data_quality.to_string(index=False))

print()
print(f"Overall Data Quality Status : {overall_status}")

print()
print("Output file:")
print(OUTPUT_FILE)

print()
print("=" * 80)
print("STAGE 2G.12 COMPLETED")
print("=" * 80)
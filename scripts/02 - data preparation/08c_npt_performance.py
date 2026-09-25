# ============================================================
# 08c_npt_performance.py
# Guyana Offshore Drilling Analytics
# Stage 2C - NPT Performance Analysis
# ============================================================

import sqlite3
from pathlib import Path
import pandas as pd


# ------------------------------------------------------------
# 1. PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DB_FILE = BASE_DIR / "database" / "guyana_drilling.db"

OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "NPT_Performance.csv"


# ------------------------------------------------------------
# 2. CONNECT TO DATABASE
# ------------------------------------------------------------

print("=" * 70)
print("STAGE 2C - NPT PERFORMANCE ANALYSIS")
print("=" * 70)

print("\nConnecting to database...")
print(f"Database: {DB_FILE}")

conn = sqlite3.connect(DB_FILE)


# ------------------------------------------------------------
# 3. LOAD NPT DATA
# ------------------------------------------------------------

query_npt = """
SELECT
    n.NPT_ID,
    n.Date,
    n.Well_ID,
    n.Rig_ID,

    n.Operator,
    n.Block,
    n.Well_Type,

    n.NPT_Category,
    n.NPT_Subcategory,
    n.Root_Cause,
    n.Responsible_Party,

    n.Duration_hr,
    n.Cost_USD,
    n.Deferred_Cost_USD,
    n.Total_Impact_USD,

    n.Duration_Bucket,
    n.Cost_Bucket,
    n.Severity,
    n.Downtime_Type,
    n.Shift,
    n.Corrective_Action,
    n.Action_Status,

    n.Month,
    n.Quarter,
    n.Season,

    r.Rig_Name,
    r.Contractor,
    r.Rig_Type,
    r.Day_Rate_USD,
    r.Year_Built

FROM Fact_NPT n

LEFT JOIN Dim_Rig r
    ON n.Rig_ID = r.Rig_ID

ORDER BY
    n.Date,
    n.Rig_ID,
    n.Well_ID
"""

df_npt = pd.read_sql_query(query_npt, conn)


# ------------------------------------------------------------
# 4. LOAD DRILLING DATA FOR BENCHMARKS
# ------------------------------------------------------------

query_drilling = """
SELECT
    Well_ID,
    Rig_ID,
    Date,
    Daily_Footage_ft,
    Drilling_Hours,
    Daily_Cost_USD
FROM Fact_Drilling_Daily_Report
"""

df_drilling = pd.read_sql_query(
    query_drilling,
    conn
)

conn.close()


# ------------------------------------------------------------
# 5. VALIDATION
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("DATA VALIDATION")
print("-" * 70)

print(f"NPT records:       {len(df_npt):,}")
print(f"Unique NPT wells:  {df_npt['Well_ID'].nunique()}")
print(f"Unique NPT rigs:   {df_npt['Rig_ID'].nunique()}")
print(
    f"NPT date range:    "
    f"{df_npt['Date'].min()} → {df_npt['Date'].max()}"
)

print("\nNPT records by category:")

print(
    df_npt["NPT_Category"]
    .value_counts()
    .to_string()
)


# ------------------------------------------------------------
# 6. GLOBAL NPT BENCHMARK
# ------------------------------------------------------------

total_events = len(df_npt)

total_npt_hours = df_npt["Duration_hr"].sum()

total_npt_cost = df_npt["Cost_USD"].sum()

total_deferred_cost = df_npt["Deferred_Cost_USD"].sum()

total_impact = df_npt["Total_Impact_USD"].sum()

total_drilling_hours = df_drilling["Drilling_Hours"].sum()

total_drilling_footage = df_drilling["Daily_Footage_ft"].sum()

total_drilling_cost = df_drilling["Daily_Cost_USD"].sum()

unique_wells = df_drilling["Well_ID"].nunique()


npt_days = total_npt_hours / 24

npt_hours_per_well = (
    total_npt_hours / unique_wells
)

npt_events_per_well = (
    total_events / unique_wells
)

npt_hours_pct = (
    total_npt_hours
    /
    (total_drilling_hours + total_npt_hours)
    * 100
)

npt_cost_per_foot = (
    total_npt_cost
    / total_drilling_footage
)

npt_cost_pct = (
    total_npt_cost
    / total_drilling_cost
    * 100
)

avg_npt_duration = (
    total_npt_hours
    / total_events
)

avg_npt_cost = (
    total_npt_cost
    / total_events
)

avg_total_impact = (
    total_impact
    / total_events
)


print("\n" + "=" * 70)
print("GLOBAL NPT BENCHMARK")
print("=" * 70)

print(f"\nNPT Events:              {total_events:,}")
print(f"NPT Hours:               {total_npt_hours:,.2f} hr")
print(f"NPT Days:                {npt_days:,.2f} days")
print(f"Drilling Hours:          {total_drilling_hours:,.2f} hr")
print(f"NPT Hours %:             {npt_hours_pct:.2f}%")
print(f"NPT Hours / Well:        {npt_hours_per_well:.2f} hr")
print(f"NPT Events / Well:       {npt_events_per_well:.2f}")

print(f"\nNPT Cost:                ${total_npt_cost:,.2f}")
print(f"Deferred Cost:           ${total_deferred_cost:,.2f}")
print(f"Total NPT Impact:        ${total_impact:,.2f}")

print(f"\nNPT Cost / Foot:          ${npt_cost_per_foot:,.2f}")
print(f"NPT Cost % of Drilling:  {npt_cost_pct:.2f}%")

print(f"\nAverage NPT Duration:     {avg_npt_duration:.2f} hr/event")
print(f"Average NPT Cost:         ${avg_npt_cost:,.2f}/event")
print(f"Average Total Impact:     ${avg_total_impact:,.2f}/event")


# ------------------------------------------------------------
# 7. NPT BY RIG
# ------------------------------------------------------------

npt_rig = (
    df_npt
    .groupby(
        [
            "Rig_ID",
            "Rig_Name",
            "Contractor",
            "Rig_Type"
        ],
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Average_NPT_Duration_hr=("Duration_hr", "mean")
    )
    .reset_index()
)


# Drilling benchmarks by rig

drilling_rig = (
    df_drilling
    .groupby("Rig_ID")
    .agg(
        Drilling_Hours=("Drilling_Hours", "sum"),
        Drilling_Footage_ft=("Daily_Footage_ft", "sum"),
        Drilling_Cost_USD=("Daily_Cost_USD", "sum"),
        Wells_Drilled=("Well_ID", "nunique")
    )
    .reset_index()
)


npt_rig = npt_rig.merge(
    drilling_rig,
    on="Rig_ID",
    how="left"
)


npt_rig["NPT_Days"] = (
    npt_rig["NPT_Hours"] / 24
)

npt_rig["NPT_Hours_per_Well"] = (
    npt_rig["NPT_Hours"]
    / npt_rig["Wells_Drilled"]
)

npt_rig["NPT_Events_per_Well"] = (
    npt_rig["NPT_Events"]
    / npt_rig["Wells_Drilled"]
)

npt_rig["NPT_Hours_pct"] = (
    npt_rig["NPT_Hours"]
    /
    (
        npt_rig["Drilling_Hours"]
        + npt_rig["NPT_Hours"]
    )
    * 100
)

npt_rig["NPT_Cost_per_Foot_USD"] = (
    npt_rig["NPT_Cost_USD"]
    / npt_rig["Drilling_Footage_ft"]
)

npt_rig["NPT_Cost_pct_Drilling_Cost"] = (
    npt_rig["NPT_Cost_USD"]
    / npt_rig["Drilling_Cost_USD"]
    * 100
)


# ------------------------------------------------------------
# 8. ROUND RIG RESULTS
# ------------------------------------------------------------

rig_numeric = [
    "NPT_Hours",
    "NPT_Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Average_NPT_Duration_hr",
    "Drilling_Hours",
    "Drilling_Footage_ft",
    "Drilling_Cost_USD",
    "NPT_Days",
    "NPT_Hours_per_Well",
    "NPT_Events_per_Well",
    "NPT_Hours_pct",
    "NPT_Cost_per_Foot_USD",
    "NPT_Cost_pct_Drilling_Cost"
]

for col in rig_numeric:
    npt_rig[col] = npt_rig[col].round(2)


# ------------------------------------------------------------
# 9. DISPLAY NPT BY RIG
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("NPT PERFORMANCE BY RIG")
print("=" * 70)

rig_display = [
    "Rig_ID",
    "Rig_Name",
    "NPT_Events",
    "NPT_Hours",
    "NPT_Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "NPT_Hours_per_Well",
    "NPT_Hours_pct",
    "NPT_Cost_per_Foot_USD"
]

print(
    npt_rig
    .sort_values("NPT_Hours", ascending=False)
    [rig_display]
    .to_string(index=False)
)


# ------------------------------------------------------------
# 10. NPT BY CATEGORY
# ------------------------------------------------------------

npt_category = (
    df_npt
    .groupby("NPT_Category")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Average_Duration_hr=("Duration_hr", "mean")
    )
    .reset_index()
)


npt_category["NPT_Hours_pct"] = (
    npt_category["NPT_Hours"]
    / total_npt_hours
    * 100
)

npt_category["NPT_Cost_pct"] = (
    npt_category["NPT_Cost_USD"]
    / total_npt_cost
    * 100
)


npt_category = npt_category.sort_values(
    "NPT_Hours",
    ascending=False
)


print("\n" + "=" * 70)
print("NPT PERFORMANCE BY CATEGORY")
print("=" * 70)

print(
    npt_category.to_string(index=False)
)


# ------------------------------------------------------------
# 11. NPT BY SEVERITY
# ------------------------------------------------------------

npt_severity = (
    df_npt
    .groupby("Severity")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Average_Duration_hr=("Duration_hr", "mean")
    )
    .reset_index()
)


npt_severity["NPT_Hours_pct"] = (
    npt_severity["NPT_Hours"]
    / total_npt_hours
    * 100
)


print("\n" + "=" * 70)
print("NPT BY SEVERITY")
print("=" * 70)

print(
    npt_severity.to_string(index=False)
)


# ------------------------------------------------------------
# 12. NPT BY ROOT CAUSE
# ------------------------------------------------------------

npt_root_cause = (
    df_npt
    .groupby("Root_Cause")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum")
    )
    .reset_index()
    .sort_values(
        "NPT_Hours",
        ascending=False
    )
)


print("\n" + "=" * 70)
print("TOP NPT ROOT CAUSES")
print("=" * 70)

print(
    npt_root_cause.head(15).to_string(index=False)
)


# ------------------------------------------------------------
# 13. NPT BY WELL
# ------------------------------------------------------------

npt_well = (
    df_npt
    .groupby(
        [
            "Well_ID",
            "Rig_ID"
        ]
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Average_NPT_Duration_hr=("Duration_hr", "mean")
    )
    .reset_index()
)


npt_well = npt_well.sort_values(
    "NPT_Hours",
    ascending=False
)


print("\n" + "=" * 70)
print("TOP 15 WELLS BY NPT HOURS")
print("=" * 70)

print(
    npt_well
    .head(15)
    .to_string(index=False)
)


# ------------------------------------------------------------
# 14. TOP NPT EVENTS
# ------------------------------------------------------------

top_events = (
    df_npt
    .sort_values(
        "Total_Impact_USD",
        ascending=False
    )
    .head(10)
)


print("\n" + "=" * 70)
print("TOP 10 NPT EVENTS BY TOTAL IMPACT")
print("=" * 70)

event_columns = [
    "NPT_ID",
    "Date",
    "Well_ID",
    "Rig_ID",
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Severity"
]

print(
    top_events[event_columns]
    .to_string(index=False)
)


# ------------------------------------------------------------
# 15. KEY FINDINGS
# ------------------------------------------------------------

highest_npt_rig = npt_rig.loc[
    npt_rig["NPT_Hours"].idxmax()
]

lowest_npt_rate_rig = npt_rig.loc[
    npt_rig["NPT_Hours_pct"].idxmin()
]

highest_npt_rate_rig = npt_rig.loc[
    npt_rig["NPT_Hours_pct"].idxmax()
]

highest_cost_rig = npt_rig.loc[
    npt_rig["NPT_Cost_USD"].idxmax()
]

top_category = npt_category.iloc[0]

top_cost_category = (
    npt_category
    .sort_values(
        "NPT_Cost_USD",
        ascending=False
    )
    .iloc[0]
)

top_root_cause = npt_root_cause.iloc[0]

top_npt_well = npt_well.iloc[0]


print("\n" + "=" * 70)
print("KEY FINDINGS")
print("=" * 70)

print(
    f"\nHighest NPT hours:"
    f" {highest_npt_rig['Rig_ID']} - "
    f"{highest_npt_rig['NPT_Hours']:,.2f} hr"
)

print(
    f"Highest NPT rate:"
    f" {highest_npt_rate_rig['Rig_ID']} - "
    f"{highest_npt_rate_rig['NPT_Hours_pct']:.2f}%"
)

print(
    f"Lowest NPT rate:"
    f" {lowest_npt_rate_rig['Rig_ID']} - "
    f"{lowest_npt_rate_rig['NPT_Hours_pct']:.2f}%"
)

print(
    f"Highest NPT cost:"
    f" {highest_cost_rig['Rig_ID']} - "
    f"${highest_cost_rig['NPT_Cost_USD']:,.2f}"
)

print(
    f"\nLargest NPT category by hours:"
    f" {top_category['NPT_Category']} - "
    f"{top_category['NPT_Hours']:,.2f} hr"
)

print(
    f"Largest NPT category by cost:"
    f" {top_cost_category['NPT_Category']} - "
    f"${top_cost_category['NPT_Cost_USD']:,.2f}"
)

print(
    f"Largest root cause:"
    f" {top_root_cause['Root_Cause']} - "
    f"{top_root_cause['NPT_Hours']:,.2f} hr"
)

print(
    f"\nWell with highest NPT:"
    f" {top_npt_well['Well_ID']} - "
    f"{top_npt_well['NPT_Hours']:,.2f} hr"
)


# ------------------------------------------------------------
# 16. VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

rig_npt_hours = npt_rig["NPT_Hours"].sum()
category_npt_hours = npt_category["NPT_Hours"].sum()
well_npt_hours = npt_well["NPT_Hours"].sum()

rig_npt_cost = npt_rig["NPT_Cost_USD"].sum()
category_npt_cost = npt_category["NPT_Cost_USD"].sum()

print(
    f"\nNPT hours source:     {total_npt_hours:,.2f}"
)

print(
    f"NPT hours by rig:     {rig_npt_hours:,.2f}"
)

print(
    f"NPT hours by category:{category_npt_hours:,.2f}"
)

print(
    f"NPT hours by well:    {well_npt_hours:,.2f}"
)

print(
    f"\nNPT cost source:       ${total_npt_cost:,.2f}"
)

print(
    f"NPT cost by rig:       ${rig_npt_cost:,.2f}"
)

print(
    f"NPT cost by category:  ${category_npt_cost:,.2f}"
)


if (
    abs(total_npt_hours - rig_npt_hours) < 0.01
    and abs(total_npt_hours - category_npt_hours) < 0.01
    and abs(total_npt_hours - well_npt_hours) < 0.01
    and abs(total_npt_cost - rig_npt_cost) < 0.01
    and abs(total_npt_cost - category_npt_cost) < 0.01
):
    print("\nSTATUS: PASS - NPT totals reconcile.")
else:
    print("\nSTATUS: WARNING - NPT reconciliation issue detected.")


# ------------------------------------------------------------
# 17. EXPORT MASTER NPT DATASET
# ------------------------------------------------------------

df_npt.to_csv(
    OUTPUT_FILE,
    index=False
)


# ------------------------------------------------------------
# 18. EXPORT SUPPORTING ANALYSIS TABLES
# ------------------------------------------------------------

npt_rig.to_csv(
    OUTPUT_DIR / "NPT_Performance_by_Rig.csv",
    index=False
)

npt_category.to_csv(
    OUTPUT_DIR / "NPT_Performance_by_Category.csv",
    index=False
)

npt_severity.to_csv(
    OUTPUT_DIR / "NPT_Performance_by_Severity.csv",
    index=False
)

npt_root_cause.to_csv(
    OUTPUT_DIR / "NPT_Performance_by_Root_Cause.csv",
    index=False
)

npt_well.to_csv(
    OUTPUT_DIR / "NPT_Performance_by_Well.csv",
    index=False
)


# ------------------------------------------------------------
# 19. COMPLETION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("EXPORT COMPLETE")
print("=" * 70)

print("\nFiles created:")

print(f"  {OUTPUT_FILE}")
print(
    f"  {OUTPUT_DIR / 'NPT_Performance_by_Rig.csv'}"
)
print(
    f"  {OUTPUT_DIR / 'NPT_Performance_by_Category.csv'}"
)
print(
    f"  {OUTPUT_DIR / 'NPT_Performance_by_Severity.csv'}"
)
print(
    f"  {OUTPUT_DIR / 'NPT_Performance_by_Root_Cause.csv'}"
)
print(
    f"  {OUTPUT_DIR / 'NPT_Performance_by_Well.csv'}"
)

print("\nStage 2C completed successfully.")
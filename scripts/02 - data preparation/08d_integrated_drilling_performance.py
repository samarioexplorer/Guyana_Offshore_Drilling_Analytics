import sqlite3
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_FILE = PROJECT_ROOT / "database" / "guyana_drilling.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "Integrated_Drilling_Performance.csv"


# ============================================================
# DATABASE CONNECTION
# ============================================================

print("=" * 80)
print("STAGE 2D — INTEGRATED DRILLING PERFORMANCE")
print("=" * 80)

print(f"\nDatabase:")
print(DB_FILE)

if not DB_FILE.exists():
    raise FileNotFoundError(f"Database not found: {DB_FILE}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_FILE)


# ============================================================
# 1. LOAD DRILLING DATA
# ============================================================

print("\n[1/7] Loading drilling data...")

drilling_query = """
SELECT
    d.Date,
    d.Well_ID,
    d.Rig_ID,
    d.Current_Depth_MD_ft,
    d.Daily_Footage_ft,
    d.ROP_ft_hr,
    d.Drilling_Hours,
    d.Weather_Delay_hr,
    d.Daily_Cost_USD
FROM Fact_Drilling_Daily_Report d
"""

df_drilling = pd.read_sql_query(drilling_query, conn)

print(f"     Drilling records: {len(df_drilling):,}")
print(f"     Wells: {df_drilling['Well_ID'].nunique():,}")
print(f"     Rigs: {df_drilling['Rig_ID'].nunique():,}")


# ============================================================
# 2. LOAD NPT DATA
# ============================================================

print("\n[2/7] Loading NPT data...")

npt_query = """
SELECT
    NPT_ID,
    Date,
    Well_ID,
    Rig_ID,
    NPT_Category,
    NPT_Subcategory,
    Root_Cause,
    Responsible_Party,
    Duration_hr,
    Cost_USD,
    Deferred_Cost_USD,
    Total_Impact_USD,
    Severity
FROM Fact_NPT
"""

df_npt = pd.read_sql_query(npt_query, conn)

print(f"     NPT records: {len(df_npt):,}")
print(f"     Wells: {df_npt['Well_ID'].nunique():,}")
print(f"     Rigs: {df_npt['Rig_ID'].nunique():,}")


# ============================================================
# 3. LOAD DIMENSIONS
# ============================================================

print("\n[3/7] Loading dimensions...")

well_query = """
SELECT
    Well_ID,
    Well_Name,
    Operator,
    Rig_ID,
    Block,
    Well_Type,
    Water_Depth_ft,
    Target_Depth_ft,
    Country,
    Status,
    Spud_Date,
    Water_Depth_Category
FROM Dim_Well
"""

rig_query = """
SELECT
    Rig_ID,
    Rig_Name,
    Contractor,
    Rig_Type,
    Max_Water_Depth_ft,
    Day_Rate_USD,
    Rig_Status,
    Year_Built
FROM Dim_Rig
"""

df_well = pd.read_sql_query(well_query, conn)
df_rig = pd.read_sql_query(rig_query, conn)

print(f"     Wells loaded: {len(df_well):,}")
print(f"     Rigs loaded: {len(df_rig):,}")


# ============================================================
# 4. AGGREGATE DRILLING AT WELL GRAIN
# ============================================================

print("\n[4/7] Aggregating drilling performance by well...")

drilling_by_well = (
    df_drilling
    .groupby(["Well_ID", "Rig_ID"], as_index=False)
    .agg(
        Drilling_Days=("Date", "nunique"),
        Drilling_Start_Date=("Date", "min"),
        Drilling_End_Date=("Date", "max"),
        Total_Footage_ft=("Daily_Footage_ft", "sum"),
        Total_Drilling_Hours=("Drilling_Hours", "sum"),
        Average_ROP_ft_hr=("ROP_ft_hr", "mean"),
        Maximum_ROP_ft_hr=("ROP_ft_hr", "max"),
        Total_Weather_Delay_hr=("Weather_Delay_hr", "sum"),
        Drilling_Cost_USD=("Daily_Cost_USD", "sum")
    )
)

print(f"     Aggregated wells: {len(drilling_by_well):,}")


# ============================================================
# 5. AGGREGATE NPT AT WELL GRAIN
# ============================================================

print("\n[5/7] Aggregating NPT performance by well...")

npt_by_well = (
    df_npt
    .groupby(["Well_ID", "Rig_ID"], as_index=False)
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_NPT_Impact_USD=("Total_Impact_USD", "sum")
    )
)

print(f"     Wells with NPT: {len(npt_by_well):,}")


# ============================================================
# 6. INTEGRATE WELL + DRILLING + NPT
# ============================================================

print("\n[6/7] Building integrated well performance...")

# Start from drilling because every analytical well should have
# actual drilling activity.

integrated = drilling_by_well.merge(
    npt_by_well,
    on=["Well_ID", "Rig_ID"],
    how="left"
)

# Fill NPT metrics for wells without NPT events.

npt_columns = [
    "NPT_Events",
    "NPT_Hours",
    "NPT_Cost_USD",
    "Deferred_Cost_USD",
    "Total_NPT_Impact_USD"
]

for col in npt_columns:
    integrated[col] = integrated[col].fillna(0)


# ------------------------------------------------------------
# Add well dimension
# ------------------------------------------------------------

integrated = integrated.merge(
    df_well,
    on=["Well_ID", "Rig_ID"],
    how="left",
    suffixes=("", "_Dim")
)


# ------------------------------------------------------------
# Add rig dimension
# ------------------------------------------------------------

integrated = integrated.merge(
    df_rig,
    on="Rig_ID",
    how="left"
)


# ============================================================
# 7. DERIVED INTEGRATED KPIs
# ============================================================

print("\n[7/7] Calculating integrated KPIs...")


# ------------------------------------------------------------
# Drilling efficiency
# ------------------------------------------------------------

integrated["Cost_per_Foot_USD"] = (
    integrated["Drilling_Cost_USD"]
    / integrated["Total_Footage_ft"]
)

integrated["Average_Daily_Footage_ft"] = (
    integrated["Total_Footage_ft"]
    / integrated["Drilling_Days"]
)

integrated["Average_Daily_Cost_USD"] = (
    integrated["Drilling_Cost_USD"]
    / integrated["Drilling_Days"]
)

integrated["Average_Hourly_Footage_ft"] = (
    integrated["Total_Footage_ft"]
    / integrated["Total_Drilling_Hours"]
)


# ------------------------------------------------------------
# NPT metrics
# ------------------------------------------------------------

integrated["NPT_Events_per_Day"] = (
    integrated["NPT_Events"]
    / integrated["Drilling_Days"]
)

integrated["NPT_Hours_per_Day"] = (
    integrated["NPT_Hours"]
    / integrated["Drilling_Days"]
)

integrated["NPT_Hours_per_Well"] = integrated["NPT_Hours"]

integrated["NPT_Hours_pct"] = (
    integrated["NPT_Hours"]
    /
    (
        integrated["Total_Drilling_Hours"]
        + integrated["NPT_Hours"]
    )
    * 100
)

integrated["NPT_Cost_per_Foot_USD"] = (
    integrated["NPT_Cost_USD"]
    / integrated["Total_Footage_ft"]
)


# ------------------------------------------------------------
# OPERATIONAL COST
#
# Actual operational expenditure:
#
# Drilling Cost + NPT Cost
# ------------------------------------------------------------

integrated["Operational_Cost_USD"] = (
    integrated["Drilling_Cost_USD"]
    + integrated["NPT_Cost_USD"]
)

integrated["Operational_Cost_per_Foot_USD"] = (
    integrated["Operational_Cost_USD"]
    / integrated["Total_Footage_ft"]
)


# ------------------------------------------------------------
# TOTAL ECONOMIC IMPACT
#
# Operational Cost + Deferred Cost
#
# Deferred Cost is kept separate conceptually because
# it represents economic impact/opportunity loss rather
# than direct operational expenditure.
# ------------------------------------------------------------

integrated["Total_Economic_Impact_USD"] = (
    integrated["Drilling_Cost_USD"]
    + integrated["NPT_Cost_USD"]
    + integrated["Deferred_Cost_USD"]
)

integrated["Total_Economic_Impact_per_Foot_USD"] = (
    integrated["Total_Economic_Impact_USD"]
    / integrated["Total_Footage_ft"]
)


# ------------------------------------------------------------
# NPT contribution to operational cost
# ------------------------------------------------------------

integrated["NPT_Cost_pct_of_Operational_Cost"] = (
    integrated["NPT_Cost_USD"]
    /
    integrated["Operational_Cost_USD"]
    * 100
)


# ------------------------------------------------------------
# Target attainment
# ------------------------------------------------------------

integrated["Target_Attainment_pct"] = (
    integrated["Total_Footage_ft"]
    / integrated["Target_Depth_ft"]
    * 100
)


# ------------------------------------------------------------
# Weather delay
# ------------------------------------------------------------

integrated["Weather_Delay_pct"] = (
    integrated["Total_Weather_Delay_hr"]
    /
    (
        integrated["Total_Drilling_Hours"]
        + integrated["Total_Weather_Delay_hr"]
    )
    * 100
)


# ============================================================
# PERFORMANCE FLAGS
# ============================================================

print("\nCreating performance indicators...")


# Use dataset medians as neutral benchmarks.
median_rop = integrated["Average_ROP_ft_hr"].median()
median_cost_ft = integrated["Operational_Cost_per_Foot_USD"].median()
median_npt_pct = integrated["NPT_Hours_pct"].median()


integrated["ROP_Performance"] = integrated[
    "Average_ROP_ft_hr"
].apply(
    lambda x: "Above Median" if x >= median_rop else "Below Median"
)


integrated["Cost_Performance"] = integrated[
    "Operational_Cost_per_Foot_USD"
].apply(
    lambda x: "Better than Median"
    if x <= median_cost_ft
    else "Worse than Median"
)


integrated["NPT_Performance"] = integrated[
    "NPT_Hours_pct"
].apply(
    lambda x: "Better than Median"
    if x <= median_npt_pct
    else "Worse than Median"
)


# ============================================================
# INTEGRATED PERFORMANCE CLASSIFICATION
# ============================================================

def classify_performance(row):

    good_metrics = 0
    bad_metrics = 0

    if row["Average_ROP_ft_hr"] >= median_rop:
        good_metrics += 1
    else:
        bad_metrics += 1

    if row["Operational_Cost_per_Foot_USD"] <= median_cost_ft:
        good_metrics += 1
    else:
        bad_metrics += 1

    if row["NPT_Hours_pct"] <= median_npt_pct:
        good_metrics += 1
    else:
        bad_metrics += 1

    if good_metrics == 3:
        return "High Performance"

    if good_metrics == 2:
        return "Good / Watch"

    if good_metrics == 1:
        return "Needs Improvement"

    return "High Risk"


integrated["Integrated_Performance"] = integrated.apply(
    classify_performance,
    axis=1
)


# ============================================================
# RISK INDICATOR
# ============================================================

integrated["NPT_Risk_Flag"] = integrated[
    "NPT_Hours_pct"
].apply(
    lambda x: "High NPT" if x > median_npt_pct else "Normal NPT"
)


integrated["Cost_Risk_Flag"] = integrated[
    "Operational_Cost_per_Foot_USD"
].apply(
    lambda x: "High Cost" if x > median_cost_ft else "Normal Cost"
)


# ============================================================
# COLUMN ORDER
# ============================================================

column_order = [
    "Well_ID",
    "Well_Name",
    "Operator",
    "Rig_ID",
    "Rig_Name",
    "Contractor",
    "Rig_Type",
    "Block",
    "Well_Type",
    "Country",
    "Water_Depth_ft",
    "Water_Depth_Category",
    "Target_Depth_ft",
    "Status",
    "Spud_Date",

    "Drilling_Days",
    "Drilling_Start_Date",
    "Drilling_End_Date",

    "Total_Footage_ft",
    "Total_Drilling_Hours",
    "Average_ROP_ft_hr",
    "Maximum_ROP_ft_hr",

    "Total_Weather_Delay_hr",
    "Weather_Delay_pct",

    "Drilling_Cost_USD",
    "Cost_per_Foot_USD",

    "NPT_Events",
    "NPT_Hours",
    "NPT_Hours_pct",
    "NPT_Events_per_Day",
    "NPT_Hours_per_Day",

    "NPT_Cost_USD",
    "NPT_Cost_per_Foot_USD",

    "Deferred_Cost_USD",
    "Total_NPT_Impact_USD",

    "Operational_Cost_USD",
    "Operational_Cost_per_Foot_USD",

    "Total_Economic_Impact_USD",
    "Total_Economic_Impact_per_Foot_USD",

    "NPT_Cost_pct_of_Operational_Cost",

    "Target_Attainment_pct",

    "ROP_Performance",
    "Cost_Performance",
    "NPT_Performance",

    "Integrated_Performance",

    "NPT_Risk_Flag",
    "Cost_Risk_Flag"
]


# Keep only columns that exist.

column_order = [
    col for col in column_order
    if col in integrated.columns
]

integrated = integrated[column_order]


# ============================================================
# ROUND NUMERIC VALUES
# ============================================================

numeric_columns = integrated.select_dtypes(
    include=["float64", "float32"]
).columns

integrated[numeric_columns] = integrated[numeric_columns].round(2)


# ============================================================
# EXPORT
# ============================================================

integrated.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

print(f"\nIntegrated wells: {len(integrated):,}")

print(
    f"Total footage: "
    f"{integrated['Total_Footage_ft'].sum():,.2f} ft"
)

print(
    f"Total drilling cost: "
    f"${integrated['Drilling_Cost_USD'].sum():,.2f}"
)

print(
    f"Total NPT hours: "
    f"{integrated['NPT_Hours'].sum():,.2f} hr"
)

print(
    f"Total NPT cost: "
    f"${integrated['NPT_Cost_USD'].sum():,.2f}"
)

print(
    f"Total deferred cost: "
    f"${integrated['Deferred_Cost_USD'].sum():,.2f}"
)

print(
    f"Total operational cost: "
    f"${integrated['Operational_Cost_USD'].sum():,.2f}"
)

print(
    f"Total economic impact: "
    f"${integrated['Total_Economic_Impact_USD'].sum():,.2f}"
)


# ============================================================
# PERFORMANCE DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("INTEGRATED PERFORMANCE DISTRIBUTION")
print("=" * 80)

print(
    integrated["Integrated_Performance"]
    .value_counts()
    .to_string()
)


# ============================================================
# TOP 10 — OPERATIONAL COST / FT
# ============================================================

print("\n" + "=" * 80)
print("TOP 10 WELLS — LOWEST OPERATIONAL COST / FT")
print("=" * 80)

top_cost = integrated.sort_values(
    "Operational_Cost_per_Foot_USD"
).head(10)

print(
    top_cost[
        [
            "Well_ID",
            "Well_Name",
            "Total_Footage_ft",
            "Average_ROP_ft_hr",
            "NPT_Hours_pct",
            "Operational_Cost_per_Foot_USD",
            "Integrated_Performance"
        ]
    ].to_string(index=False)
)


# ============================================================
# TOP 10 — ECONOMIC IMPACT
# ============================================================

print("\n" + "=" * 80)
print("TOP 10 WELLS — HIGHEST TOTAL ECONOMIC IMPACT")
print("=" * 80)

top_impact = integrated.sort_values(
    "Total_Economic_Impact_USD",
    ascending=False
).head(10)

print(
    top_impact[
        [
            "Well_ID",
            "Well_Name",
            "Total_Footage_ft",
            "Drilling_Cost_USD",
            "NPT_Cost_USD",
            "Deferred_Cost_USD",
            "Total_Economic_Impact_USD",
            "Integrated_Performance"
        ]
    ].to_string(index=False)
)


# ============================================================
# TOP 10 — NPT RISK
# ============================================================

print("\n" + "=" * 80)
print("TOP 10 WELLS — HIGHEST NPT %")
print("=" * 80)

top_npt = integrated.sort_values(
    "NPT_Hours_pct",
    ascending=False
).head(10)

print(
    top_npt[
        [
            "Well_ID",
            "Well_Name",
            "NPT_Events",
            "NPT_Hours",
            "NPT_Hours_pct",
            "NPT_Cost_USD",
            "Total_NPT_Impact_USD",
            "Integrated_Performance"
        ]
    ].to_string(index=False)
)


# ============================================================
# FINAL
# ============================================================

conn.close()

print("\n" + "=" * 80)
print("STAGE 2D COMPLETED")
print("=" * 80)

print(f"\nOutput file:")
print(OUTPUT_FILE)

print("\nDatabase connection closed.")
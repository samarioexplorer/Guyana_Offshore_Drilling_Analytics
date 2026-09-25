# ============================================================
# 08b_rig_drilling_performance.py
# Guyana Offshore Drilling Analytics
# Stage 2B - Rig Drilling Performance
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

OUTPUT_FILE = OUTPUT_DIR / "Rig_Drilling_Performance.csv"


# ------------------------------------------------------------
# 2. CONNECT TO DATABASE
# ------------------------------------------------------------

print("=" * 70)
print("STAGE 2B - RIG DRILLING PERFORMANCE")
print("=" * 70)

print("\nConnecting to database...")
print(f"Database: {DB_FILE}")

conn = sqlite3.connect(DB_FILE)


# ------------------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------------------

query = """
SELECT
    f.Date,
    f.Well_ID,
    f.Rig_ID,
    f.Daily_Footage_ft,
    f.ROP_ft_hr,
    f.Drilling_Hours,
    f.Weather_Delay_hr,
    f.Daily_Cost_USD,

    w.Well_Name,
    w.Operator,
    w.Block,
    w.Well_Type,
    w.Target_Depth_ft,

    r.Rig_Name,
    r.Contractor,
    r.Rig_Type,
    r.Max_Water_Depth_ft,
    r.Day_Rate_USD,
    r.Rig_Status,
    r.Year_Built

FROM Fact_Drilling_Daily_Report f

LEFT JOIN Dim_Well w
    ON f.Well_ID = w.Well_ID

LEFT JOIN Dim_Rig r
    ON f.Rig_ID = r.Rig_ID

ORDER BY
    f.Rig_ID,
    f.Date
"""

df = pd.read_sql_query(query, conn)

conn.close()

print(f"\nRecords loaded: {len(df):,}")


# ------------------------------------------------------------
# 4. DATA VALIDATION
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("DATA VALIDATION")
print("-" * 70)

print(f"Unique rigs:  {df['Rig_ID'].nunique()}")
print(f"Unique wells: {df['Well_ID'].nunique()}")

print("\nRecords by rig:")
print(
    df.groupby("Rig_ID")
      .size()
      .sort_values(ascending=False)
)


# ------------------------------------------------------------
# 5. RIG PERFORMANCE AGGREGATION
# ------------------------------------------------------------

rig_perf = (
    df.groupby(
        [
            "Rig_ID",
            "Rig_Name",
            "Contractor",
            "Rig_Type",
            "Rig_Status",
            "Year_Built",
            "Day_Rate_USD"
        ],
        dropna=False
    )
    .agg(
        Wells_Drilled=("Well_ID", "nunique"),

        Drilling_Days=("Date", "nunique"),

        Drilling_Start_Date=("Date", "min"),

        Drilling_End_Date=("Date", "max"),

        Total_Footage_ft=("Daily_Footage_ft", "sum"),

        Total_Drilling_Hours=("Drilling_Hours", "sum"),

        Average_ROP_ft_hr=("ROP_ft_hr", "mean"),

        Maximum_ROP_ft_hr=("ROP_ft_hr", "max"),

        Total_Weather_Delay_hr=("Weather_Delay_hr", "sum"),

        Total_Drilling_Cost_USD=("Daily_Cost_USD", "sum")
    )
    .reset_index()
)


# ------------------------------------------------------------
# 6. DERIVED PERFORMANCE METRICS
# ------------------------------------------------------------

rig_perf["Average_Daily_Footage_ft"] = (
    rig_perf["Total_Footage_ft"]
    / rig_perf["Drilling_Days"]
)

rig_perf["Average_Daily_Cost_USD"] = (
    rig_perf["Total_Drilling_Cost_USD"]
    / rig_perf["Drilling_Days"]
)

rig_perf["Cost_per_Foot_USD"] = (
    rig_perf["Total_Drilling_Cost_USD"]
    / rig_perf["Total_Footage_ft"]
)

rig_perf["Cost_per_Drilling_Hour_USD"] = (
    rig_perf["Total_Drilling_Cost_USD"]
    / rig_perf["Total_Drilling_Hours"]
)

rig_perf["Average_Hourly_Footage_ft"] = (
    rig_perf["Total_Footage_ft"]
    / rig_perf["Total_Drilling_Hours"]
)

rig_perf["Weather_Delay_pct"] = (
    rig_perf["Total_Weather_Delay_hr"]
    /
    (
        rig_perf["Total_Drilling_Hours"]
        + rig_perf["Total_Weather_Delay_hr"]
    )
    * 100
)


# ------------------------------------------------------------
# 7. RIG AGE
# ------------------------------------------------------------

REFERENCE_YEAR = 2025

rig_perf["Rig_Age_Years"] = (
    REFERENCE_YEAR - rig_perf["Year_Built"]
)


# ------------------------------------------------------------
# 8. ROUND VALUES
# ------------------------------------------------------------

numeric_columns = [
    "Total_Footage_ft",
    "Total_Drilling_Hours",
    "Average_ROP_ft_hr",
    "Maximum_ROP_ft_hr",
    "Total_Weather_Delay_hr",
    "Total_Drilling_Cost_USD",
    "Average_Daily_Footage_ft",
    "Average_Daily_Cost_USD",
    "Cost_per_Foot_USD",
    "Cost_per_Drilling_Hour_USD",
    "Average_Hourly_Footage_ft",
    "Weather_Delay_pct"
]

for col in numeric_columns:
    rig_perf[col] = rig_perf[col].round(2)


# ------------------------------------------------------------
# 9. SORT BY TOTAL FOOTAGE
# ------------------------------------------------------------

rig_perf = rig_perf.sort_values(
    "Total_Footage_ft",
    ascending=False
).reset_index(drop=True)


# ------------------------------------------------------------
# 10. DISPLAY RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("RIG PERFORMANCE - BY TOTAL FOOTAGE")
print("=" * 70)

display_columns = [
    "Rig_ID",
    "Rig_Name",
    "Wells_Drilled",
    "Drilling_Days",
    "Total_Footage_ft",
    "Average_ROP_ft_hr",
    "Total_Drilling_Hours",
    "Total_Weather_Delay_hr",
    "Total_Drilling_Cost_USD",
    "Cost_per_Foot_USD"
]

print(
    rig_perf[display_columns].to_string(index=False)
)


# ------------------------------------------------------------
# 11. RANKINGS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("RIG RANKINGS")
print("=" * 70)

print("\n1. TOTAL FOOTAGE")
print(
    rig_perf[
        ["Rig_ID", "Rig_Name", "Total_Footage_ft"]
    ].to_string(index=False)
)

print("\n2. AVERAGE ROP")
print(
    rig_perf
    .sort_values("Average_ROP_ft_hr", ascending=False)
    [
        ["Rig_ID", "Rig_Name", "Average_ROP_ft_hr"]
    ]
    .to_string(index=False)
)

print("\n3. COST PER FOOT")
print(
    rig_perf
    .sort_values("Cost_per_Foot_USD")
    [
        ["Rig_ID", "Rig_Name", "Cost_per_Foot_USD"]
    ]
    .to_string(index=False)
)

print("\n4. WEATHER DELAY")
print(
    rig_perf
    .sort_values("Total_Weather_Delay_hr", ascending=False)
    [
        ["Rig_ID", "Rig_Name", "Total_Weather_Delay_hr",
         "Weather_Delay_pct"]
    ]
    .to_string(index=False)
)


# ------------------------------------------------------------
# 12. BEST / WORST RIGS
# ------------------------------------------------------------

best_footage = rig_perf.loc[
    rig_perf["Total_Footage_ft"].idxmax()
]

best_rop = rig_perf.loc[
    rig_perf["Average_ROP_ft_hr"].idxmax()
]

best_cost = rig_perf.loc[
    rig_perf["Cost_per_Foot_USD"].idxmin()
]

worst_cost = rig_perf.loc[
    rig_perf["Cost_per_Foot_USD"].idxmax()
]

highest_weather = rig_perf.loc[
    rig_perf["Total_Weather_Delay_hr"].idxmax()
]


print("\n" + "=" * 70)
print("KEY FINDINGS")
print("=" * 70)

print(
    f"\nHighest total footage:"
    f" {best_footage['Rig_ID']} - "
    f"{best_footage['Total_Footage_ft']:,.1f} ft"
)

print(
    f"Highest average ROP:"
    f" {best_rop['Rig_ID']} - "
    f"{best_rop['Average_ROP_ft_hr']:.2f} ft/hr"
)

print(
    f"Lowest cost per foot:"
    f" {best_cost['Rig_ID']} - "
    f"${best_cost['Cost_per_Foot_USD']:,.2f}/ft"
)

print(
    f"Highest cost per foot:"
    f" {worst_cost['Rig_ID']} - "
    f"${worst_cost['Cost_per_Foot_USD']:,.2f}/ft"
)

print(
    f"Highest weather delay:"
    f" {highest_weather['Rig_ID']} - "
    f"{highest_weather['Total_Weather_Delay_hr']:,.1f} hr"
)


# ------------------------------------------------------------
# 13. OVERALL BENCHMARK
# ------------------------------------------------------------

total_footage = rig_perf["Total_Footage_ft"].sum()
total_hours = rig_perf["Total_Drilling_Hours"].sum()
total_cost = rig_perf["Total_Drilling_Cost_USD"].sum()
total_weather = rig_perf["Total_Weather_Delay_hr"].sum()

overall_cost_per_ft = total_cost / total_footage
overall_rop = total_footage / total_hours

print("\n" + "=" * 70)
print("OVERALL RIG BENCHMARK")
print("=" * 70)

print(f"\nTotal footage:        {total_footage:,.2f} ft")
print(f"Total drilling hours: {total_hours:,.2f} hr")
print(f"Average ROP:          {overall_rop:.2f} ft/hr")
print(f"Total drilling cost:  ${total_cost:,.2f}")
print(f"Cost per foot:        ${overall_cost_per_ft:,.2f}/ft")
print(f"Weather delay:        {total_weather:,.2f} hr")


# ------------------------------------------------------------
# 14. VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

source_footage = df["Daily_Footage_ft"].sum()
source_hours = df["Drilling_Hours"].sum()
source_cost = df["Daily_Cost_USD"].sum()

print(
    f"\nFootage reconciliation: "
    f"{total_footage:,.2f} vs {source_footage:,.2f}"
)

print(
    f"Hours reconciliation: "
    f"{total_hours:,.2f} vs {source_hours:,.2f}"
)

print(
    f"Cost reconciliation: "
    f"${total_cost:,.2f} vs ${source_cost:,.2f}"
)

if (
    abs(total_footage - source_footage) < 0.01
    and abs(total_hours - source_hours) < 0.01
    and abs(total_cost - source_cost) < 0.01
):
    print("\nSTATUS: PASS - All totals reconcile.")
else:
    print("\nSTATUS: WARNING - Reconciliation issue detected.")


# ------------------------------------------------------------
# 15. EXPORT
# ------------------------------------------------------------

rig_perf.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("EXPORT COMPLETE")
print("=" * 70)

print(f"\nFile created:")
print(OUTPUT_FILE)

print("\nStage 2B completed successfully.")
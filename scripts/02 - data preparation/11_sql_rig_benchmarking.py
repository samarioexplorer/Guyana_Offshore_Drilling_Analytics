import sqlite3
from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

# If this script is located in:
# ...\Guyana_Offshore_Drilling_Analytics\scripts
# then project root is one level above.

if SCRIPT_DIR.name.lower() == "scripts":
    BASE_DIR = SCRIPT_DIR.parent
else:
    BASE_DIR = SCRIPT_DIR.parents[1]

DB_FILE = BASE_DIR / "database" / "guyana_drilling.db"

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "Rig_Benchmark_SQL.csv"
)

# ============================================================
# SQL QUERY
# ============================================================
#
# IMPORTANT:
# Drilling and NPT are aggregated independently by Rig_ID.
# This prevents many-to-many row multiplication.
#
# ============================================================

query = """

WITH drilling_by_rig AS (

    SELECT
        f.Rig_ID,

        COUNT(DISTINCT f.Well_ID) AS Wells,

        COUNT(DISTINCT f.Date) AS Drilling_Days,

        SUM(f.Daily_Footage_ft) AS Total_Footage_ft,

        SUM(f.Drilling_Hours) AS Total_Drilling_Hours,

        AVG(f.ROP_ft_hr) AS Average_ROP_ft_hr,

        MAX(f.ROP_ft_hr) AS Maximum_ROP_ft_hr,

        SUM(f.Weather_Delay_hr) AS Total_Weather_Delay_hr,

        SUM(f.Daily_Cost_USD) AS Drilling_Cost_USD

    FROM Fact_Drilling_Daily_Report f

    GROUP BY
        f.Rig_ID
),


npt_by_rig AS (

    SELECT
        n.Rig_ID,

        COUNT(*) AS NPT_Events,

        SUM(n.Duration_hr) AS NPT_Hours,

        SUM(n.Cost_USD) AS NPT_Cost_USD,

        SUM(n.Deferred_Cost_USD) AS Deferred_Cost_USD,

        SUM(n.Total_Impact_USD) AS Total_NPT_Impact_USD

    FROM Fact_NPT n

    GROUP BY
        n.Rig_ID
),


rig_base AS (

    SELECT

        r.Rig_ID,
        r.Rig_Name,
        r.Contractor,
        r.Rig_Type,
        r.Max_Water_Depth_ft,
        r.Day_Rate_USD,
        r.Rig_Status,
        r.Year_Built,

        d.Wells,
        d.Drilling_Days,
        d.Total_Footage_ft,
        d.Total_Drilling_Hours,
        d.Average_ROP_ft_hr,
        d.Maximum_ROP_ft_hr,
        d.Total_Weather_Delay_hr,
        d.Drilling_Cost_USD,

        COALESCE(n.NPT_Events, 0) AS NPT_Events,
        COALESCE(n.NPT_Hours, 0) AS NPT_Hours,
        COALESCE(n.NPT_Cost_USD, 0) AS NPT_Cost_USD,
        COALESCE(n.Deferred_Cost_USD, 0) AS Deferred_Cost_USD,
        COALESCE(n.Total_NPT_Impact_USD, 0) AS Total_NPT_Impact_USD

    FROM Dim_Rig r

    LEFT JOIN drilling_by_rig d
        ON r.Rig_ID = d.Rig_ID

    LEFT JOIN npt_by_rig n
        ON r.Rig_ID = n.Rig_ID
),


metrics AS (

    SELECT

        *,

        CASE
            WHEN Drilling_Days > 0
            THEN Total_Footage_ft / Drilling_Days
            ELSE NULL
        END AS Average_Daily_Footage_ft,

        CASE
            WHEN Total_Footage_ft > 0
            THEN Drilling_Cost_USD / Total_Footage_ft
            ELSE NULL
        END AS Drilling_Cost_per_Foot_USD,

        CASE
            WHEN (Total_Drilling_Hours + NPT_Hours) > 0
            THEN
                NPT_Hours * 100.0 /
                (Total_Drilling_Hours + NPT_Hours)
            ELSE 0
        END AS NPT_Hours_pct,

        CASE
            WHEN Total_Footage_ft > 0
            THEN NPT_Cost_USD / Total_Footage_ft
            ELSE NULL
        END AS NPT_Cost_per_Foot_USD,

        (
            Drilling_Cost_USD +
            NPT_Cost_USD
        ) AS Operational_Cost_USD,

        (
            Drilling_Cost_USD +
            NPT_Cost_USD +
            Deferred_Cost_USD
        ) AS Total_Economic_Impact_USD

    FROM rig_base
),


metrics_2 AS (

    SELECT

        *,

        CASE
            WHEN Total_Footage_ft > 0
            THEN Operational_Cost_USD / Total_Footage_ft
            ELSE NULL
        END AS Operational_Cost_per_Foot_USD,

        CASE
            WHEN Total_Footage_ft > 0
            THEN Total_Economic_Impact_USD / Total_Footage_ft
            ELSE NULL
        END AS Total_Economic_Impact_per_Foot_USD,

        CASE
            WHEN Drilling_Cost_USD > 0
            THEN NPT_Cost_USD * 100.0 /
                 Drilling_Cost_USD
            ELSE 0
        END AS NPT_Cost_pct_of_Drilling_Cost

    FROM metrics
),


ranked AS (

    SELECT

        *,

        RANK() OVER (
            ORDER BY Average_ROP_ft_hr DESC
        ) AS Rank_ROP,

        RANK() OVER (
            ORDER BY Average_Daily_Footage_ft DESC
        ) AS Rank_Daily_Footage,

        RANK() OVER (
            ORDER BY Drilling_Cost_per_Foot_USD ASC
        ) AS Rank_Drilling_Cost_per_Foot,

        RANK() OVER (
            ORDER BY Operational_Cost_per_Foot_USD ASC
        ) AS Rank_Operational_Cost_per_Foot,

        RANK() OVER (
            ORDER BY NPT_Hours_pct ASC
        ) AS Rank_NPT,

        RANK() OVER (
            ORDER BY NPT_Cost_per_Foot_USD ASC
        ) AS Rank_NPT_Cost_per_Foot,

        RANK() OVER (
            ORDER BY Total_Economic_Impact_per_Foot_USD ASC
        ) AS Rank_Economic_Impact_per_Foot

    FROM metrics_2
)


SELECT

    Rig_ID,
    Rig_Name,
    Contractor,
    Rig_Type,
    Max_Water_Depth_ft,
    Day_Rate_USD,
    Rig_Status,
    Year_Built,

    Wells,
    Drilling_Days,

    Total_Footage_ft,
    Total_Drilling_Hours,

    Average_ROP_ft_hr,
    Maximum_ROP_ft_hr,

    Average_Daily_Footage_ft,

    Total_Weather_Delay_hr,

    Drilling_Cost_USD,
    Drilling_Cost_per_Foot_USD,

    NPT_Events,
    NPT_Hours,
    NPT_Hours_pct,

    NPT_Cost_USD,
    NPT_Cost_per_Foot_USD,

    Deferred_Cost_USD,
    Total_NPT_Impact_USD,

    Operational_Cost_USD,
    Operational_Cost_per_Foot_USD,

    Total_Economic_Impact_USD,
    Total_Economic_Impact_per_Foot_USD,

    NPT_Cost_pct_of_Drilling_Cost,

    Rank_ROP,
    Rank_Daily_Footage,
    Rank_Drilling_Cost_per_Foot,
    Rank_Operational_Cost_per_Foot,
    Rank_NPT,
    Rank_NPT_Cost_per_Foot,
    Rank_Economic_Impact_per_Foot,

    (
        Rank_ROP +
        Rank_Daily_Footage +
        Rank_Drilling_Cost_per_Foot +
        Rank_Operational_Cost_per_Foot +
        Rank_NPT +
        Rank_NPT_Cost_per_Foot +
        Rank_Economic_Impact_per_Foot
    ) AS Rank_Sum

FROM ranked

ORDER BY
    Rank_Sum ASC;

"""


# ============================================================
# EXECUTE QUERY
# ============================================================

conn = sqlite3.connect(DB_FILE)

try:

    df = pd.read_sql_query(query, conn)

finally:

    conn.close()


# ============================================================
# BASIC VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Number of rigs:       {len(df)}")
print(f"Unique Rig_ID:        {df['Rig_ID'].nunique()}")
print(f"Total wells:          {df['Wells'].sum():,.0f}")
print(f"Total footage:        {df['Total_Footage_ft'].sum():,.2f} ft")
print(f"Total drilling hours: {df['Total_Drilling_Hours'].sum():,.2f} hr")
print(f"Total drilling cost:  ${df['Drilling_Cost_USD'].sum():,.2f}")
print(f"Total NPT events:     {df['NPT_Events'].sum():,.0f}")
print(f"Total NPT hours:      {df['NPT_Hours'].sum():,.2f} hr")
print(f"Total NPT cost:       ${df['NPT_Cost_USD'].sum():,.2f}")
print(f"Total deferred cost:  ${df['Deferred_Cost_USD'].sum():,.2f}")
print(f"Total NPT impact:     ${df['Total_NPT_Impact_USD'].sum():,.2f}")


# ============================================================
# GLOBAL VALIDATION AGAINST DATABASE BASELINE
# ============================================================

checks = {

    "Rigs": (
        len(df),
        4
    ),

    "Wells": (
        int(df["Wells"].sum()),
        50
    ),

    "Footage": (
        round(df["Total_Footage_ft"].sum(), 2),
        952078.80
    ),

    "Drilling Hours": (
        round(df["Total_Drilling_Hours"].sum(), 2),
        28270.76
    ),

    "Drilling Cost": (
        round(df["Drilling_Cost_USD"].sum(), 2),
        654712456.04
    ),

    "NPT Events": (
        int(df["NPT_Events"].sum()),
        677
    ),

    "NPT Hours": (
        round(df["NPT_Hours"].sum(), 2),
        4008.00
    ),

    "NPT Cost": (
        round(df["NPT_Cost_USD"].sum(), 2),
        79204408.00
    ),

    "Deferred Cost": (
        round(df["Deferred_Cost_USD"].sum(), 2),
        118945770.00
    ),

    "NPT Impact": (
        round(df["Total_NPT_Impact_USD"].sum(), 2),
        198150178.00
    )
}


print("\nValidation checks:")

passed = 0

for name, (actual, expected) in checks.items():

    if actual == expected:

        print(f"PASS  {name}: {actual}")

        passed += 1

    else:

        print(
            f"FAIL  {name}: "
            f"actual={actual}, expected={expected}"
        )


print(f"\nValidation result: {passed}/{len(checks)} PASS")


# ============================================================
# DISPLAY RIG BENCHMARK
# ============================================================

print("\n" + "=" * 70)
print("RIG BENCHMARK")
print("=" * 70)

display_columns = [

    "Rig_ID",
    "Rig_Name",
    "Wells",
    "Total_Footage_ft",
    "Average_ROP_ft_hr",
    "Average_Daily_Footage_ft",
    "Drilling_Cost_per_Foot_USD",
    "NPT_Hours_pct",
    "NPT_Cost_per_Foot_USD",
    "Operational_Cost_per_Foot_USD",
    "Total_Economic_Impact_per_Foot_USD",
    "Rank_Sum"

]

print(
    df[display_columns].to_string(
        index=False,
        formatters={
            "Total_Footage_ft": "{:,.1f}".format,
            "Average_ROP_ft_hr": "{:.2f}".format,
            "Average_Daily_Footage_ft": "{:,.2f}".format,
            "Drilling_Cost_per_Foot_USD": "${:,.2f}".format,
            "NPT_Hours_pct": "{:.2f}%".format,
            "NPT_Cost_per_Foot_USD": "${:,.2f}".format,
            "Operational_Cost_per_Foot_USD": "${:,.2f}".format,
            "Total_Economic_Impact_per_Foot_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# TOP / BOTTOM RIGS
# ============================================================

print("\n" + "=" * 70)
print("RIG RANKINGS")
print("=" * 70)

print("\nBest rigs by Rank_Sum:")

print(
    df[
        [
            "Rig_ID",
            "Rig_Name",
            "Rank_Sum",
            "Rank_ROP",
            "Rank_Drilling_Cost_per_Foot",
            "Rank_NPT",
            "Rank_Economic_Impact_per_Foot"
        ]
    ]
    .sort_values("Rank_Sum")
    .to_string(index=False)
)


# ============================================================
# SAVE OUTPUT
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("OUTPUT")
print("=" * 70)

print(f"Saved successfully:")
print(OUTPUT_FILE)

print("\nSTAGE 2G.3 COMPLETED.")
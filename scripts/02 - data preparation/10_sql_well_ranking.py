import sqlite3
from pathlib import Path
import pandas as pd


# ============================================================
# STAGE 2G.2 - SQL WELL RANKING
# Guyana Offshore Drilling Analytics
# ============================================================

print("=" * 70)
print("STAGE 2G.2 - SQL WELL RANKING")
print("=" * 70)


# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

DB_FILE = BASE_DIR / "database" / "guyana_drilling.db"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "Well_Ranking_SQL.csv"


# ------------------------------------------------------------
# CONNECT
# ------------------------------------------------------------

print("\nConnecting to SQLite database...")

conn = sqlite3.connect(DB_FILE)

print(f"Database: {DB_FILE}")


# ------------------------------------------------------------
# SQL QUERY
#
# IMPORTANT:
# Drilling and NPT are aggregated independently before joining.
# This prevents many-to-many multiplication.
# ------------------------------------------------------------

sql_query = """

WITH drilling_by_well AS (

    SELECT

        Well_ID,

        COUNT(*) AS Drilling_Records,

        MIN(Date) AS Drilling_Start_Date,

        MAX(Date) AS Drilling_End_Date,

        COUNT(DISTINCT Date) AS Drilling_Days,

        SUM(Daily_Footage_ft) AS Total_Footage_ft,

        SUM(Drilling_Hours) AS Total_Drilling_Hours,

        AVG(ROP_ft_hr) AS Average_ROP_ft_hr,

        MAX(ROP_ft_hr) AS Maximum_ROP_ft_hr,

        SUM(Weather_Delay_hr) AS Total_Weather_Delay_hr,

        SUM(Daily_Cost_USD) AS Drilling_Cost_USD

    FROM Fact_Drilling_Daily_Report

    GROUP BY Well_ID

),

npt_by_well AS (

    SELECT

        Well_ID,

        COUNT(*) AS NPT_Events,

        SUM(Duration_hr) AS NPT_Hours,

        SUM(Cost_USD) AS NPT_Cost_USD,

        SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

        SUM(Total_Impact_USD) AS NPT_Impact_USD,

        AVG(Duration_hr) AS Average_NPT_Duration_hr,

        SUM(
            CASE
                WHEN Severity = 'High'
                THEN Duration_hr
                ELSE 0
            END
        ) AS High_Severity_NPT_Hours

    FROM Fact_NPT

    GROUP BY Well_ID

),

well_base AS (

    SELECT

        w.Well_ID,
        w.Well_Name,
        w.Operator,
        w.Rig_ID,
        w.Block,
        w.Well_Type,
        w.Water_Depth_ft,
        w.Water_Depth_Category,
        w.Target_Depth_ft,
        w.Country,
        w.Status,
        w.Spud_Date,

        d.Drilling_Records,
        d.Drilling_Start_Date,
        d.Drilling_End_Date,
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
        COALESCE(n.NPT_Impact_USD, 0) AS NPT_Impact_USD,

        COALESCE(
            n.Average_NPT_Duration_hr,
            0
        ) AS Average_NPT_Duration_hr,

        COALESCE(
            n.High_Severity_NPT_Hours,
            0
        ) AS High_Severity_NPT_Hours

    FROM Dim_Well w

    INNER JOIN drilling_by_well d
        ON w.Well_ID = d.Well_ID

    LEFT JOIN npt_by_well n
        ON w.Well_ID = n.Well_ID

),

metrics AS (

    SELECT

        *,

        Total_Footage_ft /
            NULLIF(Drilling_Days, 0)
            AS Average_Daily_Footage_ft,

        Drilling_Cost_USD /
            NULLIF(Total_Footage_ft, 0)
            AS Drilling_Cost_per_Foot_USD,

        NPT_Hours /
            NULLIF(
                Total_Drilling_Hours + NPT_Hours,
                0
            ) * 100
            AS NPT_Hours_pct,

        NPT_Cost_USD /
            NULLIF(Total_Footage_ft, 0)
            AS NPT_Cost_per_Foot_USD,

        Drilling_Cost_USD +
            NPT_Cost_USD
            AS Operational_Cost_USD,

        (
            Drilling_Cost_USD +
            NPT_Cost_USD
        ) /
            NULLIF(Total_Footage_ft, 0)
            AS Operational_Cost_per_Foot_USD,

        Drilling_Cost_USD +
            NPT_Cost_USD +
            Deferred_Cost_USD
            AS Total_Economic_Impact_USD,

        (
            Drilling_Cost_USD +
            NPT_Cost_USD +
            Deferred_Cost_USD
        ) /
            NULLIF(Total_Footage_ft, 0)
            AS Total_Economic_Impact_per_Foot_USD,

        NPT_Events /
            NULLIF(Drilling_Days, 0)
            AS NPT_Events_per_Day,

        NPT_Hours /
            NULLIF(Drilling_Days, 0)
            AS NPT_Hours_per_Day,

        Total_Weather_Delay_hr /
            NULLIF(Total_Drilling_Hours, 0) * 100
            AS Weather_Delay_pct,

        NPT_Cost_USD /
            NULLIF(Drilling_Cost_USD, 0) * 100
            AS NPT_Cost_pct_of_Drilling_Cost,

        Total_Footage_ft /
            NULLIF(Total_Drilling_Hours, 0)
            AS Average_Hourly_Footage_ft

    FROM well_base

),

ranked AS (

    SELECT

        *,

        RANK() OVER (
            ORDER BY Average_ROP_ft_hr DESC
        ) AS ROP_Rank,

        RANK() OVER (
            ORDER BY Average_Daily_Footage_ft DESC
        ) AS Daily_Footage_Rank,

        RANK() OVER (
            ORDER BY Drilling_Cost_per_Foot_USD ASC
        ) AS Drilling_Cost_per_Foot_Rank,

        RANK() OVER (
            ORDER BY Operational_Cost_per_Foot_USD ASC
        ) AS Operational_Cost_per_Foot_Rank,

        RANK() OVER (
            ORDER BY NPT_Hours_pct ASC
        ) AS NPT_Rank,

        RANK() OVER (
            ORDER BY NPT_Cost_per_Foot_USD ASC
        ) AS NPT_Cost_per_Foot_Rank,

        RANK() OVER (
            ORDER BY Total_Economic_Impact_per_Foot_USD ASC
        ) AS Economic_Impact_Rank,

        RANK() OVER (
            ORDER BY Total_Economic_Impact_USD ASC
        ) AS Absolute_Economic_Impact_Rank

    FROM metrics

),

final AS (

    SELECT

        *,

        (
            ROP_Rank
            + Daily_Footage_Rank
            + Drilling_Cost_per_Foot_Rank
            + Operational_Cost_per_Foot_Rank
            + NPT_Rank
            + NPT_Cost_per_Foot_Rank
            + Economic_Impact_Rank
        ) AS Rank_Sum

    FROM ranked

)

SELECT

    Well_ID,
    Well_Name,
    Operator,
    Rig_ID,
    Block,
    Well_Type,
    Water_Depth_ft,
    Water_Depth_Category,
    Target_Depth_ft,
    Country,
    Status,
    Spud_Date,

    Drilling_Records,
    Drilling_Start_Date,
    Drilling_End_Date,
    Drilling_Days,

    Total_Footage_ft,
    Total_Drilling_Hours,

    Average_ROP_ft_hr,
    Maximum_ROP_ft_hr,

    Average_Daily_Footage_ft,
    Average_Hourly_Footage_ft,

    Total_Weather_Delay_hr,
    Weather_Delay_pct,

    Drilling_Cost_USD,
    Drilling_Cost_per_Foot_USD,

    NPT_Events,
    NPT_Hours,
    NPT_Hours_pct,
    NPT_Events_per_Day,
    NPT_Hours_per_Day,

    NPT_Cost_USD,
    NPT_Cost_per_Foot_USD,

    Deferred_Cost_USD,
    NPT_Impact_USD,

    Operational_Cost_USD,
    Operational_Cost_per_Foot_USD,

    Total_Economic_Impact_USD,
    Total_Economic_Impact_per_Foot_USD,

    NPT_Cost_pct_of_Drilling_Cost,

    Average_NPT_Duration_hr,
    High_Severity_NPT_Hours,

    ROP_Rank,
    Daily_Footage_Rank,
    Drilling_Cost_per_Foot_Rank,
    Operational_Cost_per_Foot_Rank,
    NPT_Rank,
    NPT_Cost_per_Foot_Rank,
    Economic_Impact_Rank,
    Absolute_Economic_Impact_Rank,

    Rank_Sum

FROM final

ORDER BY Rank_Sum ASC;

"""


# ------------------------------------------------------------
# EXECUTE
# ------------------------------------------------------------

print("\nExecuting SQL Well Ranking query...")

df = pd.read_sql_query(sql_query, conn)

conn.close()


# ------------------------------------------------------------
# DISPLAY
# ------------------------------------------------------------

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 220)

print("\n" + "=" * 70)
print("SQL WELL RANKING RESULTS")
print("=" * 70)

print(f"\nWells returned: {len(df)}")

print("\nTOP 10 WELLS")
print("-" * 70)

top_columns = [
    "Well_ID",
    "Rig_ID",
    "Average_ROP_ft_hr",
    "Average_Daily_Footage_ft",
    "Operational_Cost_per_Foot_USD",
    "NPT_Hours_pct",
    "Total_Economic_Impact_per_Foot_USD",
    "Rank_Sum"
]

print(
    df[top_columns]
    .head(10)
    .to_string(index=False)
)


print("\nBOTTOM 10 WELLS")
print("-" * 70)

print(
    df[top_columns]
    .tail(10)
    .sort_values("Rank_Sum", ascending=False)
    .to_string(index=False)
)


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False,
    float_format="%.2f"
)

print("\n" + "-" * 70)
print("Output file:")
print(OUTPUT_FILE)


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

validation_passed = True


# 1. Number of wells

expected_wells = 50
actual_wells = len(df)

if actual_wells == expected_wells:
    print(
        f"PASS  | Wells returned | "
        f"Expected: {expected_wells} | "
        f"Actual: {actual_wells}"
    )
else:
    print(
        f"FAIL  | Wells returned | "
        f"Expected: {expected_wells} | "
        f"Actual: {actual_wells}"
    )
    validation_passed = False


# 2. Unique wells

unique_wells = df["Well_ID"].nunique()

if unique_wells == 50:
    print(
        f"PASS  | Unique Well_ID | "
        f"Expected: 50 | Actual: {unique_wells}"
    )
else:
    print(
        f"FAIL  | Unique Well_ID | "
        f"Expected: 50 | Actual: {unique_wells}"
    )
    validation_passed = False


# 3. No duplicate wells

duplicates = df["Well_ID"].duplicated().sum()

if duplicates == 0:
    print(
        "PASS  | Duplicate Well_ID records | "
        "Expected: 0 | Actual: 0"
    )
else:
    print(
        f"FAIL  | Duplicate Well_ID records | "
        f"Expected: 0 | Actual: {duplicates}"
    )
    validation_passed = False


# 4. Total footage

total_footage = df["Total_Footage_ft"].sum()

if abs(total_footage - 952078.80) < 0.10:
    print(
        f"PASS  | Total footage | "
        f"Expected: 952,078.80 | "
        f"Actual: {total_footage:,.2f}"
    )
else:
    print(
        f"FAIL  | Total footage | "
        f"Expected: 952,078.80 | "
        f"Actual: {total_footage:,.2f}"
    )
    validation_passed = False


# 5. Drilling hours

total_hours = df["Total_Drilling_Hours"].sum()

if abs(total_hours - 28270.76) < 0.10:
    print(
        f"PASS  | Drilling hours | "
        f"Expected: 28,270.76 | "
        f"Actual: {total_hours:,.2f}"
    )
else:
    print(
        f"FAIL  | Drilling hours | "
        f"Expected: 28,270.76 | "
        f"Actual: {total_hours:,.2f}"
    )
    validation_passed = False


# 6. Drilling cost

total_drilling_cost = df["Drilling_Cost_USD"].sum()

if abs(total_drilling_cost - 654712456.04) < 0.10:
    print(
        f"PASS  | Drilling cost | "
        f"Expected: 654,712,456.04 | "
        f"Actual: {total_drilling_cost:,.2f}"
    )
else:
    print(
        f"FAIL  | Drilling cost | "
        f"Expected: 654,712,456.04 | "
        f"Actual: {total_drilling_cost:,.2f}"
    )
    validation_passed = False


# 7. NPT hours

total_npt_hours = df["NPT_Hours"].sum()

if abs(total_npt_hours - 4008.00) < 0.10:
    print(
        f"PASS  | NPT hours | "
        f"Expected: 4,008.00 | "
        f"Actual: {total_npt_hours:,.2f}"
    )
else:
    print(
        f"FAIL  | NPT hours | "
        f"Expected: 4,008.00 | "
        f"Actual: {total_npt_hours:,.2f}"
    )
    validation_passed = False


# 8. NPT cost

total_npt_cost = df["NPT_Cost_USD"].sum()

if abs(total_npt_cost - 79204408.00) < 0.10:
    print(
        f"PASS  | NPT cost | "
        f"Expected: 79,204,408.00 | "
        f"Actual: {total_npt_cost:,.2f}"
    )
else:
    print(
        f"FAIL  | NPT cost | "
        f"Expected: 79,204,408.00 | "
        f"Actual: {total_npt_cost:,.2f}"
    )
    validation_passed = False


# 9. Deferred cost

total_deferred = df["Deferred_Cost_USD"].sum()

if abs(total_deferred - 118945770.00) < 0.10:
    print(
        f"PASS  | Deferred cost | "
        f"Expected: 118,945,770.00 | "
        f"Actual: {total_deferred:,.2f}"
    )
else:
    print(
        f"FAIL  | Deferred cost | "
        f"Expected: 118,945,770.00 | "
        f"Actual: {total_deferred:,.2f}"
    )
    validation_passed = False


# 10. NPT impact

total_impact = df["NPT_Impact_USD"].sum()

if abs(total_impact - 198150178.00) < 0.10:
    print(
        f"PASS  | NPT impact | "
        f"Expected: 198,150,178.00 | "
        f"Actual: {total_impact:,.2f}"
    )
else:
    print(
        f"FAIL  | NPT impact | "
        f"Expected: 198,150,178.00 | "
        f"Actual: {total_impact:,.2f}"
    )
    validation_passed = False


# ------------------------------------------------------------
# FINAL STATUS
# ------------------------------------------------------------

print("\n" + "=" * 70)

if validation_passed:

    print("STAGE 2G.2 VALIDATION: PASSED")

else:

    print("STAGE 2G.2 VALIDATION: FAILED")

print("=" * 70)


if not validation_passed:

    raise SystemExit(
        "Validation failed. Do not continue to Stage 2G.3."
    )


print("\nSTAGE 2G.2 COMPLETED SUCCESSFULLY")
print("=" * 70)
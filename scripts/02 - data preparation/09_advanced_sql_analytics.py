import sqlite3
from pathlib import Path
import pandas as pd


# ============================================================
# STAGE 2G.1 - EXECUTIVE KPIs
# Guyana Offshore Drilling Analytics
# ============================================================

print("=" * 70)
print("STAGE 2G.1 - EXECUTIVE KPIs")
print("=" * 70)

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

DB_FILE = BASE_DIR / "database" / "guyana_drilling.db"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "Executive_KPIs_SQL.csv"


# ------------------------------------------------------------
# CONNECT TO DATABASE
# ------------------------------------------------------------

print("\nConnecting to SQLite database...")

conn = sqlite3.connect(DB_FILE)

print(f"Database: {DB_FILE}")


# ------------------------------------------------------------
# SQL EXECUTIVE KPI QUERY
# ------------------------------------------------------------

sql_query = """
WITH drilling AS (

    SELECT
        COUNT(DISTINCT Well_ID) AS Wells,
        COUNT(DISTINCT Rig_ID) AS Rigs,
        COUNT(*) AS Drilling_Records,

        MIN(Date) AS Drilling_Start_Date,
        MAX(Date) AS Drilling_End_Date,

        SUM(Daily_Footage_ft) AS Total_Footage_ft,
        SUM(Drilling_Hours) AS Total_Drilling_Hours,

        AVG(ROP_ft_hr) AS Average_ROP_ft_hr,
        MAX(ROP_ft_hr) AS Maximum_ROP_ft_hr,

        SUM(Weather_Delay_hr) AS Total_Weather_Delay_hr,

        SUM(Daily_Cost_USD) AS Total_Drilling_Cost_USD

    FROM Fact_Drilling_Daily_Report

),

npt AS (

    SELECT

        COUNT(*) AS NPT_Events,

        SUM(Duration_hr) AS Total_NPT_Hours,

        SUM(Cost_USD) AS Total_NPT_Cost_USD,

        SUM(Deferred_Cost_USD) AS Total_Deferred_Cost_USD,

        SUM(Total_Impact_USD) AS Total_NPT_Impact_USD

    FROM Fact_NPT

),

combined AS (

    SELECT

        drilling.*,
        npt.*

    FROM drilling
    CROSS JOIN npt

)

SELECT

    Wells,
    Rigs,
    Drilling_Records,

    Drilling_Start_Date,
    Drilling_End_Date,

    Total_Footage_ft,
    Total_Drilling_Hours,

    Average_ROP_ft_hr,
    Maximum_ROP_ft_hr,

    Total_Weather_Delay_hr,

    Total_Drilling_Cost_USD,

    NPT_Events,
    Total_NPT_Hours,

    Total_NPT_Cost_USD,
    Total_Deferred_Cost_USD,
    Total_NPT_Impact_USD,

    ROUND(
        Total_Footage_ft / NULLIF(Total_Drilling_Hours, 0),
        2
    ) AS Average_Hourly_Footage_ft,

    ROUND(
        Total_Drilling_Cost_USD /
        NULLIF(Total_Footage_ft, 0),
        2
    ) AS Drilling_Cost_per_Foot_USD,

    ROUND(
        Total_NPT_Hours /
        NULLIF(Total_Drilling_Hours + Total_NPT_Hours, 0) * 100,
        2
    ) AS NPT_Hours_pct,

    ROUND(
        Total_NPT_Cost_USD /
        NULLIF(Total_Drilling_Cost_USD, 0) * 100,
        2
    ) AS NPT_Cost_pct_of_Drilling_Cost,

    ROUND(
        Total_NPT_Cost_USD /
        NULLIF(Total_Footage_ft, 0),
        2
    ) AS NPT_Cost_per_Foot_USD,

    ROUND(
        Total_Drilling_Cost_USD +
        Total_NPT_Cost_USD,
        2
    ) AS Operational_Cost_USD,

    ROUND(
        (
            Total_Drilling_Cost_USD +
            Total_NPT_Cost_USD
        ) /
        NULLIF(Total_Footage_ft, 0),
        2
    ) AS Operational_Cost_per_Foot_USD,

    ROUND(
        Total_Drilling_Cost_USD +
        Total_NPT_Cost_USD +
        Total_Deferred_Cost_USD,
        2
    ) AS Total_Economic_Impact_USD,

    ROUND(
        (
            Total_Drilling_Cost_USD +
            Total_NPT_Cost_USD +
            Total_Deferred_Cost_USD
        ) /
        NULLIF(Total_Footage_ft, 0),
        2
    ) AS Total_Economic_Impact_per_Foot_USD,

    ROUND(
        Total_NPT_Hours /
        NULLIF(Wells, 0),
        2
    ) AS NPT_Hours_per_Well,

    ROUND(
        NPT_Events /
        NULLIF(Wells, 0),
        2
    ) AS NPT_Events_per_Well

FROM combined;
"""


# ------------------------------------------------------------
# EXECUTE QUERY
# ------------------------------------------------------------

print("\nExecuting SQL Executive KPI query...")

df = pd.read_sql_query(sql_query, conn)


# ------------------------------------------------------------
# CLOSE CONNECTION
# ------------------------------------------------------------

conn.close()


# ------------------------------------------------------------
# DISPLAY RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("EXECUTIVE KPI RESULTS")
print("=" * 70)

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

print(df.to_string(index=False))


# ------------------------------------------------------------
# SAVE OUTPUT
# ------------------------------------------------------------

df.to_csv(
    OUTPUT_FILE,
    index=False,
    float_format="%.2f"
)

print("\n" + "-" * 70)

print(f"Output file:")
print(OUTPUT_FILE)


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

expected = {
    "Wells": 50,
    "Rigs": 4,
    "Drilling_Records": 1474,
    "Total_Footage_ft": 952078.80,
    "Total_Drilling_Hours": 28270.76,
    "Total_Drilling_Cost_USD": 654712456.04,
    "NPT_Events": 677,
    "Total_NPT_Hours": 4008.00,
    "Total_NPT_Cost_USD": 79204408.00,
    "Total_Deferred_Cost_USD": 118945770.00,
    "Total_NPT_Impact_USD": 198150178.00,
}

row = df.iloc[0]

validation_passed = True

for column, expected_value in expected.items():

    actual_value = row[column]

    if isinstance(expected_value, int):

        passed = int(round(actual_value)) == expected_value

    else:

        passed = abs(float(actual_value) - expected_value) < 0.10

    status = "PASS" if passed else "FAIL"

    print(
        f"{status:5} | "
        f"{column:35} | "
        f"Expected: {expected_value:,.2f} | "
        f"Actual: {actual_value:,.2f}"
    )

    if not passed:
        validation_passed = False


print("\n" + "=" * 70)

if validation_passed:

    print("STAGE 2G.1 VALIDATION: PASSED")

else:

    print("STAGE 2G.1 VALIDATION: FAILED")

print("=" * 70)


if not validation_passed:

    raise SystemExit(
        "Validation failed. Review SQL results before continuing."
    )


print("\nSTAGE 2G.1 COMPLETED SUCCESSFULLY")
print("=" * 70)
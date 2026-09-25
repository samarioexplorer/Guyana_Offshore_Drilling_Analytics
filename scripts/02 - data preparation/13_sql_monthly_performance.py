from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

if SCRIPT_DIR.name.lower() == "scripts":
    BASE_DIR = SCRIPT_DIR.parent
else:
    BASE_DIR = SCRIPT_DIR.parents[1]

DB_FILE = BASE_DIR / "database" / "guyana_drilling.db"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(DB_FILE)


# ============================================================
# 1. MONTHLY DRILLING + NPT PORTFOLIO PERFORMANCE
# ============================================================
#
# IMPORTANT:
# We aggregate drilling and NPT independently.
# We then build a complete monthly calendar using UNION.
#
# This prevents NPT-only months from being lost.
# ============================================================

monthly_drilling_sql = """
WITH drilling_monthly AS (

    SELECT

        strftime('%Y-%m', Date) AS Month,

        COUNT(*) AS Drilling_Records,

        COUNT(DISTINCT Well_ID) AS Wells,

        COUNT(DISTINCT Rig_ID) AS Rigs,

        MIN(Date) AS Month_Start_Date,

        MAX(Date) AS Month_End_Date,

        SUM(Daily_Footage_ft) AS Total_Footage_ft,

        SUM(Drilling_Hours) AS Total_Drilling_Hours,

        CASE
            WHEN SUM(Drilling_Hours) > 0
            THEN
                SUM(Daily_Footage_ft)
                / SUM(Drilling_Hours)
        END AS Average_ROP_ft_hr,

        MAX(ROP_ft_hr) AS Maximum_ROP_ft_hr,

        SUM(Weather_Delay_hr) AS Weather_Delay_hr,

        CASE
            WHEN SUM(Drilling_Hours) > 0
            THEN
                100.0 * SUM(Weather_Delay_hr)
                / SUM(Drilling_Hours)
        END AS Weather_Delay_pct,

        SUM(Daily_Cost_USD) AS Drilling_Cost_USD,

        CASE
            WHEN SUM(Daily_Footage_ft) > 0
            THEN
                SUM(Daily_Cost_USD)
                / SUM(Daily_Footage_ft)
        END AS Drilling_Cost_per_Foot_USD

    FROM Fact_Drilling_Daily_Report

    GROUP BY strftime('%Y-%m', Date)
),

npt_monthly AS (

    SELECT

        strftime('%Y-%m', Date) AS Month,

        COUNT(*) AS NPT_Events,

        SUM(Duration_hr) AS NPT_Hours,

        SUM(Cost_USD) AS NPT_Cost_USD,

        SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

        SUM(Total_Impact_USD) AS Total_NPT_Impact_USD

    FROM Fact_NPT

    GROUP BY strftime('%Y-%m', Date)
),

all_months AS (

    SELECT Month
    FROM drilling_monthly

    UNION

    SELECT Month
    FROM npt_monthly
)

SELECT

    m.Month,

    COALESCE(d.Drilling_Records, 0)
        AS Drilling_Records,

    COALESCE(d.Wells, 0)
        AS Wells,

    COALESCE(d.Rigs, 0)
        AS Rigs,

    d.Month_Start_Date,

    d.Month_End_Date,

    COALESCE(d.Total_Footage_ft, 0)
        AS Total_Footage_ft,

    COALESCE(d.Total_Drilling_Hours, 0)
        AS Total_Drilling_Hours,

    d.Average_ROP_ft_hr,

    d.Maximum_ROP_ft_hr,

    COALESCE(d.Weather_Delay_hr, 0)
        AS Weather_Delay_hr,

    d.Weather_Delay_pct,

    COALESCE(d.Drilling_Cost_USD, 0)
        AS Drilling_Cost_USD,

    d.Drilling_Cost_per_Foot_USD,

    COALESCE(n.NPT_Events, 0)
        AS NPT_Events,

    COALESCE(n.NPT_Hours, 0)
        AS NPT_Hours,

    CASE
        WHEN COALESCE(d.Total_Drilling_Hours, 0) > 0
        THEN
            100.0
            * COALESCE(n.NPT_Hours, 0)
            / d.Total_Drilling_Hours
    END AS NPT_Hours_pct,

    COALESCE(n.NPT_Cost_USD, 0)
        AS NPT_Cost_USD,

    COALESCE(n.Deferred_Cost_USD, 0)
        AS Deferred_Cost_USD,

    COALESCE(n.Total_NPT_Impact_USD, 0)
        AS Total_NPT_Impact_USD,

    COALESCE(d.Drilling_Cost_USD, 0)
        + COALESCE(n.NPT_Cost_USD, 0)
        AS Operational_Cost_USD,

    COALESCE(d.Drilling_Cost_USD, 0)
        + COALESCE(n.NPT_Cost_USD, 0)
        + COALESCE(n.Deferred_Cost_USD, 0)
        AS Total_Economic_Impact_USD,

    CASE
        WHEN COALESCE(d.Total_Footage_ft, 0) > 0
        THEN
            (
                COALESCE(d.Drilling_Cost_USD, 0)
                + COALESCE(n.NPT_Cost_USD, 0)
            )
            / d.Total_Footage_ft
    END AS Operational_Cost_per_Foot_USD,

    CASE
        WHEN COALESCE(d.Total_Footage_ft, 0) > 0
        THEN
            (
                COALESCE(d.Drilling_Cost_USD, 0)
                + COALESCE(n.NPT_Cost_USD, 0)
                + COALESCE(n.Deferred_Cost_USD, 0)
            )
            / d.Total_Footage_ft
    END AS Total_Economic_Impact_per_Foot_USD

FROM all_months m

LEFT JOIN drilling_monthly d
    ON m.Month = d.Month

LEFT JOIN npt_monthly n
    ON m.Month = n.Month

ORDER BY m.Month;
"""


# ============================================================
# 2. MONTHLY RIG PERFORMANCE
# ============================================================

monthly_rig_sql = """
WITH drilling_monthly AS (

    SELECT

        strftime('%Y-%m', Date) AS Month,

        Rig_ID,

        COUNT(*) AS Drilling_Records,

        COUNT(DISTINCT Well_ID) AS Wells,

        SUM(Daily_Footage_ft) AS Total_Footage_ft,

        SUM(Drilling_Hours) AS Total_Drilling_Hours,

        CASE
            WHEN SUM(Drilling_Hours) > 0
            THEN
                SUM(Daily_Footage_ft)
                / SUM(Drilling_Hours)
        END AS Average_ROP_ft_hr,

        SUM(Daily_Cost_USD) AS Drilling_Cost_USD,

        CASE
            WHEN SUM(Daily_Footage_ft) > 0
            THEN
                SUM(Daily_Cost_USD)
                / SUM(Daily_Footage_ft)
        END AS Drilling_Cost_per_Foot_USD,

        SUM(Weather_Delay_hr) AS Weather_Delay_hr

    FROM Fact_Drilling_Daily_Report

    GROUP BY
        strftime('%Y-%m', Date),
        Rig_ID
),

npt_monthly AS (

    SELECT

        strftime('%Y-%m', Date) AS Month,

        Rig_ID,

        COUNT(*) AS NPT_Events,

        SUM(Duration_hr) AS NPT_Hours,

        SUM(Cost_USD) AS NPT_Cost_USD,

        SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

        SUM(Total_Impact_USD) AS Total_NPT_Impact_USD

    FROM Fact_NPT

    GROUP BY
        strftime('%Y-%m', Date),
        Rig_ID
)

SELECT

    d.Month,

    d.Rig_ID,

    r.Rig_Name,

    r.Contractor,

    d.Drilling_Records,

    d.Wells,

    d.Total_Footage_ft,

    d.Total_Drilling_Hours,

    d.Average_ROP_ft_hr,

    d.Drilling_Cost_USD,

    d.Drilling_Cost_per_Foot_USD,

    d.Weather_Delay_hr,

    COALESCE(n.NPT_Events, 0)
        AS NPT_Events,

    COALESCE(n.NPT_Hours, 0)
        AS NPT_Hours,

    CASE
        WHEN d.Total_Drilling_Hours > 0
        THEN
            100.0
            * COALESCE(n.NPT_Hours, 0)
            / d.Total_Drilling_Hours
    END AS NPT_Hours_pct,

    COALESCE(n.NPT_Cost_USD, 0)
        AS NPT_Cost_USD,

    COALESCE(n.Deferred_Cost_USD, 0)
        AS Deferred_Cost_USD,

    COALESCE(n.Total_NPT_Impact_USD, 0)
        AS Total_NPT_Impact_USD,

    d.Drilling_Cost_USD
        + COALESCE(n.NPT_Cost_USD, 0)
        AS Operational_Cost_USD,

    d.Drilling_Cost_USD
        + COALESCE(n.NPT_Cost_USD, 0)
        + COALESCE(n.Deferred_Cost_USD, 0)
        AS Total_Economic_Impact_USD

FROM drilling_monthly d

LEFT JOIN npt_monthly n
    ON d.Month = n.Month
    AND d.Rig_ID = n.Rig_ID

LEFT JOIN Dim_Rig r
    ON d.Rig_ID = r.Rig_ID

ORDER BY
    d.Month,
    d.Rig_ID;
"""


# ============================================================
# 3. MONTHLY NPT CATEGORY
# ============================================================

monthly_category_sql = """

SELECT

    strftime('%Y-%m', Date) AS Month,

    NPT_Category,

    COUNT(*) AS NPT_Events,

    SUM(Duration_hr) AS NPT_Hours,

    SUM(Cost_USD) AS NPT_Cost_USD,

    SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

    SUM(Total_Impact_USD) AS Total_Impact_USD

FROM Fact_NPT

GROUP BY

    strftime('%Y-%m', Date),

    NPT_Category

ORDER BY

    Month,

    NPT_Hours DESC;
"""


# ============================================================
# 4. SEASONAL NPT
# ============================================================

seasonal_npt_sql = """

SELECT

    Season,

    COUNT(*) AS NPT_Events,

    SUM(Duration_hr) AS NPT_Hours,

    SUM(Cost_USD) AS NPT_Cost_USD,

    SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

    SUM(Total_Impact_USD) AS Total_Impact_USD,

    AVG(Duration_hr) AS Average_NPT_Duration_hr

FROM Fact_NPT

GROUP BY Season

ORDER BY NPT_Hours DESC;
"""


# ============================================================
# 5. NPT DATA ALIGNMENT CHECK
# ============================================================
#
# Identify NPT dates that have no corresponding drilling record.
#
# These records must NOT be silently discarded.
# ============================================================

alignment_sql = """

WITH drilling_dates AS (

    SELECT DISTINCT Date

    FROM Fact_Drilling_Daily_Report
),

npt_dates AS (

    SELECT

        Date,

        COUNT(*) AS NPT_Events,

        SUM(Duration_hr) AS NPT_Hours,

        SUM(Cost_USD) AS NPT_Cost_USD,

        SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

        SUM(Total_Impact_USD) AS Total_Impact_USD

    FROM Fact_NPT

    GROUP BY Date
)

SELECT

    n.Date,

    n.NPT_Events,

    n.NPT_Hours,

    n.NPT_Cost_USD,

    n.Deferred_Cost_USD,

    n.Total_Impact_USD

FROM npt_dates n

LEFT JOIN drilling_dates d
    ON n.Date = d.Date

WHERE d.Date IS NULL

ORDER BY n.Date;
"""


# ============================================================
# EXECUTE QUERIES
# ============================================================

df_monthly = pd.read_sql_query(
    monthly_drilling_sql,
    conn
)

df_rig = pd.read_sql_query(
    monthly_rig_sql,
    conn
)

df_category = pd.read_sql_query(
    monthly_category_sql,
    conn
)

df_seasonal = pd.read_sql_query(
    seasonal_npt_sql,
    conn
)

df_alignment = pd.read_sql_query(
    alignment_sql,
    conn
)


# ============================================================
# SAVE OUTPUT FILES
# ============================================================

monthly_file = (
    OUTPUT_DIR /
    "Monthly_Drilling_Performance_SQL.csv"
)

rig_file = (
    OUTPUT_DIR /
    "Monthly_Rig_Performance_SQL.csv"
)

category_file = (
    OUTPUT_DIR /
    "Monthly_NPT_Category_SQL.csv"
)

seasonal_file = (
    OUTPUT_DIR /
    "Monthly_Seasonal_NPT_SQL.csv"
)

alignment_file = (
    OUTPUT_DIR /
    "NPT_Data_Alignment_Check_SQL.csv"
)


df_monthly.to_csv(
    monthly_file,
    index=False
)

df_rig.to_csv(
    rig_file,
    index=False
)

df_category.to_csv(
    category_file,
    index=False
)

df_seasonal.to_csv(
    seasonal_file,
    index=False
)

df_alignment.to_csv(
    alignment_file,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("STAGE 2G.5 — SQL TIME-SERIES ANALYTICS")
print("=" * 70)

print(
    f"\nDatabase: {DB_FILE}"
)

print(
    f"Output:   {OUTPUT_DIR}"
)


# ------------------------------------------------------------
# GENERAL RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("MONTHLY PORTFOLIO RESULTS")
print("=" * 70)

print(
    "\nMonthly rows:",
    len(df_monthly)
)

print(
    "\nDate range:"
)

print(
    df_monthly["Month"].min(),
    "to",
    df_monthly["Month"].max()
)

print(
    "\nTotal footage:"
)

print(
    round(
        df_monthly["Total_Footage_ft"].sum(),
        2
    )
)

print(
    "\nTotal drilling hours:"
)

print(
    round(
        df_monthly["Total_Drilling_Hours"].sum(),
        2
    )
)

print(
    "\nTotal drilling cost:"
)

print(
    round(
        df_monthly["Drilling_Cost_USD"].sum(),
        2
    )
)

print(
    "\nTotal NPT events:"
)

print(
    int(
        df_monthly["NPT_Events"].sum()
    )
)

print(
    "\nTotal NPT hours:"
)

print(
    round(
        df_monthly["NPT_Hours"].sum(),
        2
    )
)

print(
    "\nTotal NPT cost:"
)

print(
    round(
        df_monthly["NPT_Cost_USD"].sum(),
        2
    )
)

print(
    "\nTotal deferred cost:"
)

print(
    round(
        df_monthly["Deferred_Cost_USD"].sum(),
        2
    )
)

print(
    "\nTotal NPT impact:"
)

print(
    round(
        df_monthly["Total_NPT_Impact_USD"].sum(),
        2
    )
)


# ============================================================
# MONTHLY SAMPLE
# ============================================================

print("\n" + "=" * 70)
print("MONTHLY PERFORMANCE SAMPLE")
print("=" * 70)

print(
    df_monthly[
        [
            "Month",
            "Total_Footage_ft",
            "Total_Drilling_Hours",
            "Average_ROP_ft_hr",
            "Drilling_Cost_per_Foot_USD",
            "NPT_Hours",
            "NPT_Hours_pct",
            "NPT_Cost_USD",
            "Deferred_Cost_USD"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# ============================================================
# NPT ALIGNMENT RESULTS
# ============================================================

print("\n" + "=" * 70)
print("NPT DATA ALIGNMENT CHECK")
print("=" * 70)

print(
    "\nNPT dates without drilling records:",
    len(df_alignment)
)

if len(df_alignment) > 0:

    print(
        "\nNPT hours outside drilling-date coverage:"
    )

    print(
        round(
            df_alignment["NPT_Hours"].sum(),
            2
        )
    )

    print(
        "\nNPT cost outside drilling-date coverage:"
    )

    print(
        round(
            df_alignment["NPT_Cost_USD"].sum(),
            2
        )
    )

    print(
        "\nDeferred cost outside drilling-date coverage:"
    )

    print(
        round(
            df_alignment["Deferred_Cost_USD"].sum(),
            2
        )
    )

    print(
        "\nAffected dates:"
    )

    print(
        df_alignment.to_string(index=False)
    )

else:

    print(
        "\nNo NPT dates outside drilling-date coverage."
    )


# ============================================================
# VALIDATION CHECKS
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

checks = []


checks.append(
    (
        "Monthly rows > 0",
        len(df_monthly) > 0
    )
)


checks.append(
    (
        "Total footage",
        abs(
            df_monthly["Total_Footage_ft"].sum()
            - 952078.80
        ) < 0.01
    )
)


checks.append(
    (
        "Total drilling hours",
        abs(
            df_monthly["Total_Drilling_Hours"].sum()
            - 28270.76
        ) < 0.01
    )
)


checks.append(
    (
        "Total drilling cost",
        abs(
            df_monthly["Drilling_Cost_USD"].sum()
            - 654712456.04
        ) < 0.01
    )
)


checks.append(
    (
        "Total NPT events",
        int(
            df_monthly["NPT_Events"].sum()
        ) == 677
    )
)


checks.append(
    (
        "Total NPT hours",
        abs(
            df_monthly["NPT_Hours"].sum()
            - 4008.0
        ) < 0.01
    )
)


checks.append(
    (
        "Total NPT cost",
        abs(
            df_monthly["NPT_Cost_USD"].sum()
            - 79204408.0
        ) < 0.01
    )
)


checks.append(
    (
        "Total deferred cost",
        abs(
            df_monthly["Deferred_Cost_USD"].sum()
            - 118945770.0
        ) < 0.01
    )
)


checks.append(
    (
        "Total NPT impact",
        abs(
            df_monthly["Total_NPT_Impact_USD"].sum()
            - 198150178.0
        ) < 0.01
    )
)


passed = 0


for name, result in checks:

    status = "PASS" if result else "FAIL"

    print(
        f"{status:<6} | {name}"
    )

    if result:
        passed += 1


print(
    f"\nValidation result: "
    f"{passed}/{len(checks)} PASS"
)


# ============================================================
# OUTPUT FILES
# ============================================================

print("\n" + "=" * 70)
print("OUTPUT FILES")
print("=" * 70)

print(monthly_file)
print(rig_file)
print(category_file)
print(seasonal_file)
print(alignment_file)


# ============================================================
# CLOSE
# ============================================================

conn.close()


print("\n" + "=" * 70)
print("STAGE 2G.5 COMPLETED")
print("=" * 70)
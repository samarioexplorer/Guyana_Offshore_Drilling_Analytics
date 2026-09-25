import sqlite3
from pathlib import Path
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

if SCRIPT_DIR.name.lower() == "scripts":
    BASE_DIR = SCRIPT_DIR.parent
else:
    BASE_DIR = SCRIPT_DIR.parents[1]

DB_FILE = BASE_DIR / "database" / "guyana_drilling.db"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

print("=" * 70)
print("STAGE 2G.4 — SQL NPT ROOT CAUSE & CATEGORY ANALYSIS")
print("=" * 70)

print(f"Database: {DB_FILE}")
print(f"Output:   {OUTPUT_DIR}")


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(DB_FILE)


# ============================================================
# 1. NPT CATEGORY ANALYSIS
# ============================================================

query_category = """

WITH category_base AS (

    SELECT
        NPT_Category,

        COUNT(*) AS NPT_Events,

        SUM(Duration_hr) AS NPT_Hours,

        SUM(Cost_USD) AS NPT_Cost_USD,

        SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

        SUM(Total_Impact_USD) AS Total_Impact_USD

    FROM Fact_NPT

    GROUP BY
        NPT_Category
),

category_metrics AS (

    SELECT
        *,

        NPT_Hours * 100.0 /
            SUM(NPT_Hours) OVER ()
            AS NPT_Hours_pct,

        NPT_Cost_USD * 100.0 /
            SUM(NPT_Cost_USD) OVER ()
            AS NPT_Cost_pct,

        Total_Impact_USD * 100.0 /
            SUM(Total_Impact_USD) OVER ()
            AS Impact_pct

    FROM category_base
),

category_ranked AS (

    SELECT
        *,

        RANK() OVER (
            ORDER BY NPT_Hours DESC
        ) AS Rank_NPT_Hours,

        RANK() OVER (
            ORDER BY NPT_Cost_USD DESC
        ) AS Rank_NPT_Cost,

        RANK() OVER (
            ORDER BY Total_Impact_USD DESC
        ) AS Rank_Total_Impact

    FROM category_metrics
)

SELECT *

FROM category_ranked

ORDER BY
    NPT_Hours DESC;

"""

df_category = pd.read_sql_query(
    query_category,
    conn
)

category_file = (
    OUTPUT_DIR /
    "NPT_Category_SQL.csv"
)

df_category.to_csv(
    category_file,
    index=False
)


# ============================================================
# 2. NPT SUBCATEGORY ANALYSIS
# ============================================================

query_subcategory = """

SELECT

    NPT_Category,

    NPT_Subcategory,

    COUNT(*) AS NPT_Events,

    SUM(Duration_hr) AS NPT_Hours,

    ROUND(
        SUM(Duration_hr) * 100.0 /
        SUM(SUM(Duration_hr)) OVER (),
        2
    ) AS NPT_Hours_pct,

    SUM(Cost_USD) AS NPT_Cost_USD,

    SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

    SUM(Total_Impact_USD) AS Total_Impact_USD,

    ROUND(
        SUM(Total_Impact_USD) * 100.0 /
        SUM(SUM(Total_Impact_USD)) OVER (),
        2
    ) AS Impact_pct,

    ROUND(
        AVG(Duration_hr),
        2
    ) AS Avg_Duration_hr

FROM Fact_NPT

GROUP BY
    NPT_Category,
    NPT_Subcategory

ORDER BY
    NPT_Hours DESC;

"""

df_subcategory = pd.read_sql_query(
    query_subcategory,
    conn
)

subcategory_file = (
    OUTPUT_DIR /
    "NPT_Subcategory_SQL.csv"
)

df_subcategory.to_csv(
    subcategory_file,
    index=False
)


# ============================================================
# 3. ROOT CAUSE PARETO ANALYSIS
# ============================================================

query_root_cause = """

WITH root_base AS (

    SELECT

        Root_Cause,

        COUNT(*) AS NPT_Events,

        SUM(Duration_hr) AS NPT_Hours,

        SUM(Cost_USD) AS NPT_Cost_USD,

        SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

        SUM(Total_Impact_USD) AS Total_Impact_USD

    FROM Fact_NPT

    GROUP BY
        Root_Cause
),

root_ranked AS (

    SELECT

        *,

        RANK() OVER (
            ORDER BY NPT_Hours DESC
        ) AS Rank_NPT_Hours

    FROM root_base
),

root_pareto AS (

    SELECT

        *,

        SUM(NPT_Hours) OVER (
            ORDER BY NPT_Hours DESC
            ROWS BETWEEN UNBOUNDED PRECEDING
            AND CURRENT ROW
        ) AS Cumulative_NPT_Hours,

        SUM(NPT_Hours) OVER () AS Total_NPT_Hours

    FROM root_ranked
)

SELECT

    Root_Cause,

    NPT_Events,

    NPT_Hours,

    ROUND(
        NPT_Hours * 100.0 /
        Total_NPT_Hours,
        2
    ) AS NPT_Hours_pct,

    Cumulative_NPT_Hours,

    ROUND(
        Cumulative_NPT_Hours * 100.0 /
        Total_NPT_Hours,
        2
    ) AS Cumulative_NPT_Hours_pct,

    NPT_Cost_USD,

    Deferred_Cost_USD,

    Total_Impact_USD,

    Rank_NPT_Hours,

    CASE
        WHEN
            Cumulative_NPT_Hours * 100.0 /
            Total_NPT_Hours <= 80
        THEN 'Pareto Priority'

        ELSE 'Remaining Causes'
    END AS Pareto_Flag

FROM root_pareto

ORDER BY
    NPT_Hours DESC;

"""

df_root = pd.read_sql_query(
    query_root_cause,
    conn
)

root_file = (
    OUTPUT_DIR /
    "NPT_Root_Cause_Pareto_SQL.csv"
)

df_root.to_csv(
    root_file,
    index=False
)


# ============================================================
# 4. SEVERITY ANALYSIS
# ============================================================

query_severity = """

SELECT

    Severity,

    COUNT(*) AS NPT_Events,

    SUM(Duration_hr) AS NPT_Hours,

    ROUND(
        SUM(Duration_hr) * 100.0 /
        SUM(SUM(Duration_hr)) OVER (),
        2
    ) AS NPT_Hours_pct,

    SUM(Cost_USD) AS NPT_Cost_USD,

    SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

    SUM(Total_Impact_USD) AS Total_Impact_USD,

    ROUND(
        AVG(Duration_hr),
        2
    ) AS Avg_Duration_hr,

    ROUND(
        AVG(Total_Impact_USD),
        2
    ) AS Avg_Impact_per_Event_USD

FROM Fact_NPT

GROUP BY
    Severity

ORDER BY
    CASE Severity
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        WHEN 'Low' THEN 3
        ELSE 4
    END;

"""

df_severity = pd.read_sql_query(
    query_severity,
    conn
)

severity_file = (
    OUTPUT_DIR /
    "NPT_Severity_SQL.csv"
)

df_severity.to_csv(
    severity_file,
    index=False
)


# ============================================================
# 5. RESPONSIBLE PARTY ANALYSIS
# ============================================================

query_responsible = """

SELECT

    Responsible_Party,

    COUNT(*) AS NPT_Events,

    SUM(Duration_hr) AS NPT_Hours,

    ROUND(
        SUM(Duration_hr) * 100.0 /
        SUM(SUM(Duration_hr)) OVER (),
        2
    ) AS NPT_Hours_pct,

    SUM(Cost_USD) AS NPT_Cost_USD,

    SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

    SUM(Total_Impact_USD) AS Total_Impact_USD,

    ROUND(
        AVG(Duration_hr),
        2
    ) AS Avg_Duration_hr

FROM Fact_NPT

GROUP BY
    Responsible_Party

ORDER BY
    NPT_Hours DESC;

"""

df_responsible = pd.read_sql_query(
    query_responsible,
    conn
)

responsible_file = (
    OUTPUT_DIR /
    "NPT_Responsible_Party_SQL.csv"
)

df_responsible.to_csv(
    responsible_file,
    index=False
)


# ============================================================
# 6. RIG × CATEGORY ANALYSIS
# ============================================================

query_rig_category = """

SELECT

    Rig_ID,

    NPT_Category,

    COUNT(*) AS NPT_Events,

    SUM(Duration_hr) AS NPT_Hours,

    SUM(Cost_USD) AS NPT_Cost_USD,

    SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

    SUM(Total_Impact_USD) AS Total_Impact_USD

FROM Fact_NPT

GROUP BY
    Rig_ID,
    NPT_Category

ORDER BY
    Rig_ID,
    NPT_Hours DESC;

"""

df_rig_category = pd.read_sql_query(
    query_rig_category,
    conn
)

rig_category_file = (
    OUTPUT_DIR /
    "NPT_Rig_Category_SQL.csv"
)

df_rig_category.to_csv(
    rig_category_file,
    index=False
)


# ============================================================
# 7. RIG × ROOT CAUSE ANALYSIS
# ============================================================

query_rig_root = """

SELECT

    Rig_ID,

    Root_Cause,

    COUNT(*) AS NPT_Events,

    SUM(Duration_hr) AS NPT_Hours,

    SUM(Cost_USD) AS NPT_Cost_USD,

    SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

    SUM(Total_Impact_USD) AS Total_Impact_USD

FROM Fact_NPT

GROUP BY
    Rig_ID,
    Root_Cause

ORDER BY
    Rig_ID,
    NPT_Hours DESC;

"""

df_rig_root = pd.read_sql_query(
    query_rig_root,
    conn
)

rig_root_file = (
    OUTPUT_DIR /
    "NPT_Rig_Root_Cause_SQL.csv"
)

df_rig_root.to_csv(
    rig_root_file,
    index=False
)


# ============================================================
# 8. WELL NPT HOTSPOTS
# ============================================================

query_well = """

SELECT

    Well_ID,

    Rig_ID,

    COUNT(*) AS NPT_Events,

    SUM(Duration_hr) AS NPT_Hours,

    SUM(Cost_USD) AS NPT_Cost_USD,

    SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,

    SUM(Total_Impact_USD) AS Total_Impact_USD,

    ROUND(
        AVG(Duration_hr),
        2
    ) AS Avg_NPT_Duration_hr

FROM Fact_NPT

GROUP BY
    Well_ID,
    Rig_ID

ORDER BY
    NPT_Hours DESC;

"""

df_well = pd.read_sql_query(
    query_well,
    conn
)

well_file = (
    OUTPUT_DIR /
    "NPT_Well_Hotspots_SQL.csv"
)

df_well.to_csv(
    well_file,
    index=False
)


# ============================================================
# CLOSE DATABASE
# ============================================================

conn.close()


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"Total NPT events:     {df_category['NPT_Events'].sum():,.0f}")
print(f"Total NPT hours:      {df_category['NPT_Hours'].sum():,.2f}")
print(f"Total NPT cost:       ${df_category['NPT_Cost_USD'].sum():,.2f}")
print(f"Total deferred cost:  ${df_category['Deferred_Cost_USD'].sum():,.2f}")
print(f"Total NPT impact:     ${df_category['Total_Impact_USD'].sum():,.2f}")

checks = {

    "NPT Events": (
        int(df_category["NPT_Events"].sum()),
        677
    ),

    "NPT Hours": (
        round(df_category["NPT_Hours"].sum(), 2),
        4008.00
    ),

    "NPT Cost": (
        round(df_category["NPT_Cost_USD"].sum(), 2),
        79204408.00
    ),

    "Deferred Cost": (
        round(df_category["Deferred_Cost_USD"].sum(), 2),
        118945770.00
    ),

    "NPT Impact": (
        round(df_category["Total_Impact_USD"].sum(), 2),
        198150178.00
    ),

    "Categories": (
        len(df_category),
        5
    )
}

passed = 0

print("\nValidation checks:")

for name, (actual, expected) in checks.items():

    if actual == expected:

        print(
            f"PASS  {name}: {actual}"
        )

        passed += 1

    else:

        print(
            f"FAIL  {name}: "
            f"actual={actual}, expected={expected}"
        )

print(
    f"\nValidation result: "
    f"{passed}/{len(checks)} PASS"
)


# ============================================================
# CATEGORY SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("NPT CATEGORY SUMMARY")
print("=" * 70)

print(
    df_category[
        [
            "NPT_Category",
            "NPT_Events",
            "NPT_Hours",
            "NPT_Hours_pct",
            "NPT_Cost_USD",
            "Total_Impact_USD",
            "Rank_NPT_Hours"
        ]
    ].to_string(index=False)
)


# ============================================================
# ROOT CAUSE PARETO
# ============================================================

print("\n" + "=" * 70)
print("ROOT CAUSE PARETO")
print("=" * 70)

print(
    df_root[
        [
            "Rank_NPT_Hours",
            "Root_Cause",
            "NPT_Events",
            "NPT_Hours",
            "NPT_Hours_pct",
            "Cumulative_NPT_Hours_pct",
            "Total_Impact_USD",
            "Pareto_Flag"
        ]
    ]
    .head(20)
    .to_string(index=False)
)


# ============================================================
# TOP NPT WELLS
# ============================================================

print("\n" + "=" * 70)
print("TOP NPT WELL HOTSPOTS")
print("=" * 70)

print(
    df_well[
        [
            "Well_ID",
            "Rig_ID",
            "NPT_Events",
            "NPT_Hours",
            "NPT_Cost_USD",
            "Total_Impact_USD"
        ]
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# OUTPUT FILES
# ============================================================

print("\n" + "=" * 70)
print("OUTPUT FILES")
print("=" * 70)

files_created = [

    category_file,
    subcategory_file,
    root_file,
    severity_file,
    responsible_file,
    rig_category_file,
    rig_root_file,
    well_file

]

for file in files_created:

    print(file)


print("\n" + "=" * 70)
print("STAGE 2G.4 COMPLETED")
print("=" * 70)
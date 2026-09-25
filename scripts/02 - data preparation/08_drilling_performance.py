from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# GUYANA OFFSHORE DRILLING ANALYTICS
# Stage 2A — Well Drilling Performance
# ============================================================

print("=" * 80)
print("GUYANA OFFSHORE DRILLING ANALYTICS")
print("Stage 2A — Well Drilling Performance")
print("=" * 80)


# ============================================================
# 1. DATABASE PATH
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = (
    PROJECT_DIR
    / "database"
    / "guyana_drilling.db"
)

print("\n[1] Checking database...")

if not DATABASE_FILE.exists():
    raise FileNotFoundError(
        f"Database not found:\n{DATABASE_FILE}"
    )

print(f"[OK] Database found:")
print(f"     {DATABASE_FILE}")


# ============================================================
# 2. CONNECT TO SQLITE
# ============================================================

print("\n[2] Connecting to SQLite...")

conn = sqlite3.connect(DATABASE_FILE)
conn.execute("PRAGMA foreign_keys = ON;")

print("[OK] SQLite connection established")


# ============================================================
# 3. WELL PERFORMANCE — MAIN QUERY
# ============================================================

print("\n[3] Calculating well drilling performance...")

query = """
SELECT
    w.Well_ID,
    w.Well_Name,
    w.Operator,
    w.Rig_ID,
    r.Rig_Name,
    r.Contractor,
    r.Rig_Type,
    w.Block,
    w.Well_Type,
    w.Country,
    w.Water_Depth_ft,
    w.Water_Depth_Category,
    w.Target_Depth_ft,
    w.Status,

    COUNT(d.Date) AS Drilling_Days,

    MIN(d.Date) AS Drilling_Start_Date,
    MAX(d.Date) AS Drilling_End_Date,

    SUM(d.Daily_Footage_ft) AS Total_Footage_ft,

    SUM(d.Drilling_Hours) AS Total_Drilling_Hours,

    AVG(d.ROP_ft_hr) AS Average_ROP_ft_hr,

    MAX(d.ROP_ft_hr) AS Maximum_ROP_ft_hr,

    SUM(d.Weather_Delay_hr) AS Total_Weather_Delay_hr,

    SUM(d.Daily_Cost_USD) AS Total_Drilling_Cost_USD,

    CASE
        WHEN SUM(d.Daily_Footage_ft) > 0
        THEN
            SUM(d.Daily_Cost_USD)
            / SUM(d.Daily_Footage_ft)
        ELSE NULL
    END AS Cost_per_Foot_USD,

    CASE
        WHEN COUNT(d.Date) > 0
        THEN
            SUM(d.Daily_Footage_ft)
            / COUNT(d.Date)
        ELSE NULL
    END AS Average_Daily_Footage_ft,

    CASE
        WHEN COUNT(d.Date) > 0
        THEN
            SUM(d.Daily_Cost_USD)
            / COUNT(d.Date)
        ELSE NULL
    END AS Average_Daily_Cost_USD

FROM Fact_Drilling_Daily_Report d

INNER JOIN Dim_Well w
    ON d.Well_ID = w.Well_ID

LEFT JOIN Dim_Rig r
    ON d.Rig_ID = r.Rig_ID

GROUP BY
    w.Well_ID,
    w.Well_Name,
    w.Operator,
    w.Rig_ID,
    r.Rig_Name,
    r.Contractor,
    r.Rig_Type,
    w.Block,
    w.Well_Type,
    w.Country,
    w.Water_Depth_ft,
    w.Water_Depth_Category,
    w.Target_Depth_ft,
    w.Status

ORDER BY
    Total_Footage_ft DESC;
"""


well_performance = pd.read_sql_query(query, conn)

print(
    f"[OK] Generated performance records: "
    f"{len(well_performance):,} wells"
)


# ============================================================
# 4. CALCULATED PERFORMANCE METRICS
# ============================================================

print("\n[4] Calculating derived performance metrics...")

well_performance["Target_Attainment_pct"] = (
    well_performance["Total_Footage_ft"]
    / well_performance["Target_Depth_ft"]
    * 100
)

well_performance["Average_Hourly_Footage_ft"] = (
    well_performance["Total_Footage_ft"]
    / well_performance["Total_Drilling_Hours"]
)

well_performance["Weather_Delay_pct"] = (
    well_performance["Total_Weather_Delay_hr"]
    / (
        well_performance["Total_Drilling_Hours"]
        + well_performance["Total_Weather_Delay_hr"]
    )
    * 100
)


# ============================================================
# 5. TOP 10 WELLS — FOOTAGE
# ============================================================

print("\n[5] TOP 10 WELLS BY TOTAL FOOTAGE")
print("-" * 80)

top_footage = well_performance.nlargest(
    10,
    "Total_Footage_ft"
)[
    [
        "Well_ID",
        "Well_Name",
        "Well_Type",
        "Drilling_Days",
        "Total_Footage_ft",
        "Average_ROP_ft_hr",
        "Total_Drilling_Hours",
        "Total_Drilling_Cost_USD"
    ]
]

print(
    top_footage.to_string(
        index=False,
        formatters={
            "Total_Footage_ft": "{:,.1f}".format,
            "Average_ROP_ft_hr": "{:,.2f}".format,
            "Total_Drilling_Hours": "{:,.1f}".format,
            "Total_Drilling_Cost_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# 6. TOP 10 WELLS — ROP
# ============================================================

print("\n[6] TOP 10 WELLS BY AVERAGE ROP")
print("-" * 80)

top_rop = well_performance.nlargest(
    10,
    "Average_ROP_ft_hr"
)[
    [
        "Well_ID",
        "Well_Name",
        "Well_Type",
        "Drilling_Days",
        "Average_ROP_ft_hr",
        "Total_Footage_ft",
        "Cost_per_Foot_USD"
    ]
]

print(
    top_rop.to_string(
        index=False,
        formatters={
            "Average_ROP_ft_hr": "{:,.2f}".format,
            "Total_Footage_ft": "{:,.1f}".format,
            "Cost_per_Foot_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# 7. TOP 10 WELLS — LOWEST COST PER FOOT
# ============================================================

print("\n[7] TOP 10 WELLS BY LOWEST COST/FT")
print("-" * 80)

lowest_cost_ft = well_performance.nsmallest(
    10,
    "Cost_per_Foot_USD"
)[
    [
        "Well_ID",
        "Well_Name",
        "Well_Type",
        "Total_Footage_ft",
        "Average_ROP_ft_hr",
        "Total_Drilling_Cost_USD",
        "Cost_per_Foot_USD"
    ]
]

print(
    lowest_cost_ft.to_string(
        index=False,
        formatters={
            "Total_Footage_ft": "{:,.1f}".format,
            "Average_ROP_ft_hr": "{:,.2f}".format,
            "Total_Drilling_Cost_USD": "${:,.2f}".format,
            "Cost_per_Foot_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# 8. HIGHEST COST PER FOOT
# ============================================================

print("\n[8] TOP 10 WELLS BY HIGHEST COST/FT")
print("-" * 80)

highest_cost_ft = well_performance.nlargest(
    10,
    "Cost_per_Foot_USD"
)[
    [
        "Well_ID",
        "Well_Name",
        "Well_Type",
        "Total_Footage_ft",
        "Average_ROP_ft_hr",
        "Total_Drilling_Cost_USD",
        "Cost_per_Foot_USD"
    ]
]

print(
    highest_cost_ft.to_string(
        index=False,
        formatters={
            "Total_Footage_ft": "{:,.1f}".format,
            "Average_ROP_ft_hr": "{:,.2f}".format,
            "Total_Drilling_Cost_USD": "${:,.2f}".format,
            "Cost_per_Foot_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# 9. WELL PERFORMANCE SCORECARD
# ============================================================

print("\n[9] WELL PERFORMANCE SCORECARD")
print("-" * 80)

scorecard_query = """
SELECT
    w.Well_ID,
    w.Well_Name,
    w.Well_Type,

    SUM(d.Daily_Footage_ft) AS Total_Footage_ft,

    AVG(d.ROP_ft_hr) AS Average_ROP_ft_hr,

    SUM(d.Drilling_Hours) AS Drilling_Hours,

    SUM(d.Daily_Cost_USD) AS Total_Cost_USD,

    SUM(d.Daily_Cost_USD)
        / NULLIF(SUM(d.Daily_Footage_ft), 0)
        AS Cost_per_Foot_USD

FROM Fact_Drilling_Daily_Report d

JOIN Dim_Well w
    ON d.Well_ID = w.Well_ID

GROUP BY
    w.Well_ID,
    w.Well_Name,
    w.Well_Type

ORDER BY
    Total_Cost_USD DESC;
"""

scorecard = pd.read_sql_query(
    scorecard_query,
    conn
)

print(
    scorecard.head(15).to_string(
        index=False,
        formatters={
            "Total_Footage_ft": "{:,.1f}".format,
            "Average_ROP_ft_hr": "{:,.2f}".format,
            "Drilling_Hours": "{:,.1f}".format,
            "Total_Cost_USD": "${:,.2f}".format,
            "Cost_per_Foot_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# 10. OVERALL WELL PERFORMANCE BENCHMARK
# ============================================================

print("\n[10] OVERALL WELL PERFORMANCE BENCHMARK")
print("-" * 80)

benchmark_query = """
SELECT
    COUNT(DISTINCT Well_ID) AS Wells,

    SUM(Daily_Footage_ft) AS Total_Footage_ft,

    SUM(Drilling_Hours) AS Total_Drilling_Hours,

    AVG(ROP_ft_hr) AS Average_ROP_ft_hr,

    SUM(Daily_Cost_USD) AS Total_Drilling_Cost_USD,

    SUM(Daily_Cost_USD)
        / NULLIF(SUM(Daily_Footage_ft), 0)
        AS Overall_Cost_per_Foot_USD,

    SUM(Weather_Delay_hr) AS Total_Weather_Delay_hr

FROM Fact_Drilling_Daily_Report;
"""

benchmark = pd.read_sql_query(
    benchmark_query,
    conn
)

print(
    benchmark.to_string(
        index=False,
        formatters={
            "Total_Footage_ft": "{:,.2f}".format,
            "Total_Drilling_Hours": "{:,.2f}".format,
            "Average_ROP_ft_hr": "{:,.2f}".format,
            "Total_Drilling_Cost_USD": "${:,.2f}".format,
            "Overall_Cost_per_Foot_USD": "${:,.2f}".format,
            "Total_Weather_Delay_hr": "{:,.2f}".format
        }
    )
)


# ============================================================
# 11. EXPORT RESULT
# ============================================================

print("\n[11] Exporting well performance dataset...")

OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "Well_Drilling_Performance.csv"
)

well_performance.to_csv(
    OUTPUT_FILE,
    index=False
)

print(f"[OK] Exported:")
print(f"     {OUTPUT_FILE}")


# ============================================================
# 12. VALIDATION
# ============================================================

print("\n[12] Validation...")

print(
    f"[OK] Wells analyzed: "
    f"{len(well_performance):,}"
)

print(
    f"[OK] Total footage: "
    f"{well_performance['Total_Footage_ft'].sum():,.2f} ft"
)

print(
    f"[OK] Total drilling hours: "
    f"{well_performance['Total_Drilling_Hours'].sum():,.2f} hr"
)

print(
    f"[OK] Total drilling cost: "
    f"${well_performance['Total_Drilling_Cost_USD'].sum():,.2f}"
)

print(
    f"[OK] No. of wells with missing Cost/ft: "
    f"{well_performance['Cost_per_Foot_USD'].isna().sum()}"
)


# ============================================================
# 13. CLOSE DATABASE
# ============================================================

conn.close()

print("\n" + "=" * 80)
print("STAGE 2A — WELL DRILLING PERFORMANCE COMPLETED SUCCESSFULLY")
print("=" * 80)
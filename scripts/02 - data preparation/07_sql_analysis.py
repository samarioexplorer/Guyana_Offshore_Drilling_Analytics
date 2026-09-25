from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# GUYANA OFFSHORE DRILLING ANALYTICS
# Stage 1 — SQL Connectivity & Basic Queries
# ============================================================

print("=" * 75)
print("GUYANA OFFSHORE DRILLING ANALYTICS")
print("Stage 1 — SQL Connectivity & Basic Queries")
print("=" * 75)


# ============================================================
# 1. DATABASE PATH
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "guyana_drilling.db"

print("\n[1] Checking database...")

if not DATABASE_FILE.exists():
    raise FileNotFoundError(
        f"SQLite database not found:\n{DATABASE_FILE}"
    )

print(f"[OK] Database found:")
print(f"     {DATABASE_FILE}")


# ============================================================
# 2. CONNECT TO SQLITE
# ============================================================

print("\n[2] Connecting to SQLite...")

conn = sqlite3.connect(DATABASE_FILE)

# Enable foreign keys
conn.execute("PRAGMA foreign_keys = ON;")

print("[OK] SQLite connection established")


# ============================================================
# 3. DATABASE TABLES
# ============================================================

print("\n[3] Checking database tables...")

tables_query = """
SELECT name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
"""

tables = pd.read_sql_query(tables_query, conn)

print(tables.to_string(index=False))


# ============================================================
# 4. ROW COUNTS
# ============================================================

print("\n[4] Checking row counts...")

row_count_query = """
SELECT 'Dim_Rig' AS Table_Name, COUNT(*) AS Row_Count
FROM Dim_Rig

UNION ALL

SELECT 'Dim_Well', COUNT(*)
FROM Dim_Well

UNION ALL

SELECT 'Dim_Date', COUNT(*)
FROM Dim_Date

UNION ALL

SELECT 'Fact_Drilling_Daily_Report', COUNT(*)
FROM Fact_Drilling_Daily_Report

UNION ALL

SELECT 'Fact_NPT', COUNT(*)
FROM Fact_NPT;
"""

row_counts = pd.read_sql_query(row_count_query, conn)

print(row_counts.to_string(index=False))


# ============================================================
# 5. WELL COUNT
# ============================================================

print("\n[5] Number of wells...")

query = """
SELECT COUNT(*) AS Total_Wells
FROM Dim_Well;
"""

result = pd.read_sql_query(query, conn)

print(f"Total wells: {result.loc[0, 'Total_Wells']:,}")


# ============================================================
# 6. DRILLING RECORD COUNT
# ============================================================

print("\n[6] Number of drilling records...")

query = """
SELECT COUNT(*) AS Total_Drilling_Records
FROM Fact_Drilling_Daily_Report;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total drilling records: "
    f"{result.loc[0, 'Total_Drilling_Records']:,}"
)


# ============================================================
# 7. NPT RECORD COUNT
# ============================================================

print("\n[7] Number of NPT records...")

query = """
SELECT COUNT(*) AS Total_NPT_Records
FROM Fact_NPT;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total NPT records: "
    f"{result.loc[0, 'Total_NPT_Records']:,}"
)


# ============================================================
# 8. DATE RANGE — DRILLING
# ============================================================

print("\n[8] Drilling date range...")

query = """
SELECT
    MIN(Date) AS Start_Date,
    MAX(Date) AS End_Date
FROM Fact_Drilling_Daily_Report;
"""

result = pd.read_sql_query(query, conn)

print(f"Start date: {result.loc[0, 'Start_Date']}")
print(f"End date:   {result.loc[0, 'End_Date']}")


# ============================================================
# 9. DATE RANGE — NPT
# ============================================================

print("\n[9] NPT date range...")

query = """
SELECT
    MIN(Date) AS Start_Date,
    MAX(Date) AS End_Date
FROM Fact_NPT;
"""

result = pd.read_sql_query(query, conn)

print(f"Start date: {result.loc[0, 'Start_Date']}")
print(f"End date:   {result.loc[0, 'End_Date']}")


# ============================================================
# 10. TOTAL FOOTAGE
# ============================================================

print("\n[10] Total drilling footage...")

query = """
SELECT
    SUM(Daily_Footage_ft) AS Total_Footage_ft
FROM Fact_Drilling_Daily_Report;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total footage: "
    f"{result.loc[0, 'Total_Footage_ft']:,.2f} ft"
)


# ============================================================
# 11. TOTAL DRILLING HOURS
# ============================================================

print("\n[11] Total drilling hours...")

query = """
SELECT
    SUM(Drilling_Hours) AS Total_Drilling_Hours
FROM Fact_Drilling_Daily_Report;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total drilling hours: "
    f"{result.loc[0, 'Total_Drilling_Hours']:,.2f} hr"
)


# ============================================================
# 12. AVERAGE ROP
# ============================================================

print("\n[12] Average ROP...")

query = """
SELECT
    AVG(ROP_ft_hr) AS Average_ROP_ft_hr
FROM Fact_Drilling_Daily_Report
WHERE ROP_ft_hr IS NOT NULL;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Average ROP: "
    f"{result.loc[0, 'Average_ROP_ft_hr']:,.2f} ft/hr"
)


# ============================================================
# 13. TOTAL DRILLING COST
# ============================================================

print("\n[13] Total drilling cost...")

query = """
SELECT
    SUM(Daily_Cost_USD) AS Total_Drilling_Cost_USD
FROM Fact_Drilling_Daily_Report;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total drilling cost: "
    f"${result.loc[0, 'Total_Drilling_Cost_USD']:,.2f}"
)


# ============================================================
# 14. TOTAL NPT HOURS
# ============================================================

print("\n[14] Total NPT hours...")

query = """
SELECT
    SUM(Duration_hr) AS Total_NPT_Hours
FROM Fact_NPT;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total NPT hours: "
    f"{result.loc[0, 'Total_NPT_Hours']:,.2f} hr"
)


# ============================================================
# 15. TOTAL NPT COST
# ============================================================

print("\n[15] Total NPT cost...")

query = """
SELECT
    SUM(Cost_USD) AS Total_NPT_Cost_USD
FROM Fact_NPT;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total NPT cost: "
    f"${result.loc[0, 'Total_NPT_Cost_USD']:,.2f}"
)


# ============================================================
# 16. TOTAL DEFERRED COST
# ============================================================

print("\n[16] Total deferred cost...")

query = """
SELECT
    SUM(Deferred_Cost_USD) AS Total_Deferred_Cost_USD
FROM Fact_NPT;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total deferred cost: "
    f"${result.loc[0, 'Total_Deferred_Cost_USD']:,.2f}"
)


# ============================================================
# 17. TOTAL IMPACT
# ============================================================

print("\n[17] Total NPT impact...")

query = """
SELECT
    SUM(Total_Impact_USD) AS Total_Impact_USD
FROM Fact_NPT;
"""

result = pd.read_sql_query(query, conn)

print(
    f"Total NPT impact: "
    f"${result.loc[0, 'Total_Impact_USD']:,.2f}"
)


# ============================================================
# 18. BASIC NPT CATEGORY DISTRIBUTION
# ============================================================

print("\n[18] NPT by category...")

query = """
SELECT
    NPT_Category,
    COUNT(*) AS NPT_Events,
    SUM(Duration_hr) AS NPT_Hours,
    SUM(Cost_USD) AS NPT_Cost_USD
FROM Fact_NPT
GROUP BY NPT_Category
ORDER BY NPT_Hours DESC;
"""

npt_category = pd.read_sql_query(query, conn)

print(
    npt_category.to_string(
        index=False,
        formatters={
            "NPT_Hours": "{:,.2f}".format,
            "NPT_Cost_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# 19. TOP 10 WELLS BY FOOTAGE
# ============================================================

print("\n[19] Top 10 wells by drilling footage...")

query = """
SELECT
    Well_ID,
    SUM(Daily_Footage_ft) AS Total_Footage_ft,
    AVG(ROP_ft_hr) AS Average_ROP_ft_hr,
    SUM(Daily_Cost_USD) AS Total_Cost_USD
FROM Fact_Drilling_Daily_Report
GROUP BY Well_ID
ORDER BY Total_Footage_ft DESC
LIMIT 10;
"""

top_wells = pd.read_sql_query(query, conn)

print(
    top_wells.to_string(
        index=False,
        formatters={
            "Total_Footage_ft": "{:,.2f}".format,
            "Average_ROP_ft_hr": "{:,.2f}".format,
            "Total_Cost_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# 20. TOP 10 WELLS BY NPT HOURS
# ============================================================

print("\n[20] Top 10 wells by NPT hours...")

query = """
SELECT
    Well_ID,
    COUNT(*) AS NPT_Events,
    SUM(Duration_hr) AS NPT_Hours,
    SUM(Cost_USD) AS NPT_Cost_USD
FROM Fact_NPT
GROUP BY Well_ID
ORDER BY NPT_Hours DESC
LIMIT 10;
"""

top_npt_wells = pd.read_sql_query(query, conn)

print(
    top_npt_wells.to_string(
        index=False,
        formatters={
            "NPT_Hours": "{:,.2f}".format,
            "NPT_Cost_USD": "${:,.2f}".format
        }
    )
)


# ============================================================
# 21. DATABASE INTEGRITY CHECK
# ============================================================

print("\n[21] Database integrity check...")

foreign_key_check = pd.read_sql_query(
    "PRAGMA foreign_key_check;",
    conn
)

if foreign_key_check.empty:
    print("[OK] No foreign-key violations.")
else:
    print("[WARNING] Foreign-key violations detected:")
    print(foreign_key_check.to_string(index=False))


# ============================================================
# 22. CLOSE CONNECTION
# ============================================================

conn.close()

print("\n" + "=" * 75)
print("STAGE 1 SQL ANALYSIS COMPLETED SUCCESSFULLY")
print("=" * 75)
import sqlite3
from pathlib import Path
import pandas as pd


# ============================================================
# GUYANA OFFSHORE DRILLING ANALYTICS
# 06_create_sqlite_database.py
#
# Builds SQLite database from the five generated Excel files.
# ============================================================


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATABASE_DIR = PROJECT_ROOT / "database"

DATABASE_DIR.mkdir(exist_ok=True)

DB_PATH = DATABASE_DIR / "guyana_drilling.db"


# ============================================================
# INPUT FILES
# ============================================================

FILES = {
    "Dim_Well": RAW_DIR / "Dim_Well.xlsx",
    "Dim_Rig": RAW_DIR / "Dim_Rig.xlsx",
    "Dim_Date": RAW_DIR / "Dim_Date.xlsx",
    "Fact_Drilling_Daily_Report":
        RAW_DIR / "Fact_Drilling_Daily_Report.xlsx",
    "FACT_NPT_FILE":
        RAW_DIR / "Fact_NPT.xlsx",
}


# ============================================================
# START
# ============================================================

print("=" * 75)
print("GUYANA OFFSHORE DRILLING ANALYTICS")
print("SQLite Data Model Builder")
print("=" * 75)


# ============================================================
# CHECK FILES
# ============================================================

print("\n[1] Checking input files...\n")

for table_name, file_path in FILES.items():

    if file_path.exists():

        print(f"[OK] {table_name}: {file_path}")

    else:

        raise FileNotFoundError(
            f"Missing required file: {file_path}"
        )


# ============================================================
# LOAD EXCEL DATA
# ============================================================

print("\n[2] Loading Excel files...\n")

dataframes = {}

for table_name, file_path in FILES.items():

    df = pd.read_excel(file_path)

    dataframes[table_name] = df

    print(
        f"[OK] {table_name:<35} "
        f"{len(df):>8,} rows | "
        f"{len(df.columns):>3} columns"
    )


# ============================================================
# DISPLAY ACTUAL SCHEMAS
# ============================================================

print("\n[3] Detected schemas\n")

for table_name, df in dataframes.items():

    print(f"{table_name}:")
    print("   " + ", ".join(df.columns))
    print()


# ============================================================
# CONNECT TO SQLITE
# ============================================================

print("[4] Creating SQLite database...\n")

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")


# ============================================================
# DROP EXISTING TABLES
# ============================================================

print("[5] Resetting existing tables...\n")

cursor.execute(
    "DROP TABLE IF EXISTS Fact_NPT"
)

cursor.execute(
    "DROP TABLE IF EXISTS Fact_Drilling_Daily_Report"
)

cursor.execute(
    "DROP TABLE IF EXISTS Dim_Date"
)

cursor.execute(
    "DROP TABLE IF EXISTS Dim_Well"
)

cursor.execute(
    "DROP TABLE IF EXISTS Dim_Rig"
)


# ============================================================
# CREATE DIM_RIG
# ============================================================

print("[6] Creating Dim_Rig...")

cursor.execute("""
CREATE TABLE Dim_Rig (

    Rig_ID TEXT PRIMARY KEY,

    Rig_Name TEXT,

    Contractor TEXT,

    Rig_Type TEXT,

    Max_Water_Depth_ft REAL,

    Day_Rate_USD REAL,

    Rig_Status TEXT,

    Year_Built INTEGER

);
""")


# ============================================================
# CREATE DIM_WELL
# ============================================================

print("[7] Creating Dim_Well...")

cursor.execute("""
CREATE TABLE Dim_Well (

    Well_ID TEXT PRIMARY KEY,

    Well_Name TEXT,

    Operator TEXT,

    Rig_ID TEXT,

    Block TEXT,

    Well_Type TEXT,

    Water_Depth_ft REAL,

    Target_Depth_ft REAL,

    Country TEXT,

    Status TEXT,

    Status_Probability REAL,

    Spud_Date TEXT,

    Water_Depth_Category TEXT,

    FOREIGN KEY (Rig_ID)
        REFERENCES Dim_Rig(Rig_ID)

);
""")


# ============================================================
# CREATE DIM_DATE
# ============================================================

print("[8] Creating Dim_Date...")

cursor.execute("""
CREATE TABLE Dim_Date (

    Date_Key INTEGER PRIMARY KEY,

    Date TEXT UNIQUE,

    Year INTEGER,

    Quarter INTEGER,

    Quarter_Name TEXT,

    Month_Number INTEGER,

    Month_Name TEXT,

    Month_Year TEXT,

    Week INTEGER,

    Day INTEGER,

    Day_of_Year INTEGER,

    Day_Name TEXT,

    Is_Weekend INTEGER,

    Is_Month_End INTEGER

);
""")


# ============================================================
# CREATE FACT DRILLING DAILY REPORT
# ============================================================

print("[9] Creating Fact_Drilling_Daily_Report...")

cursor.execute("""
CREATE TABLE Fact_Drilling_Daily_Report (

    Date TEXT NOT NULL,

    Well_ID TEXT NOT NULL,

    Rig_ID TEXT NOT NULL,

    Previous_Depth_MD_ft REAL,

    Current_Depth_MD_ft REAL,

    Daily_Footage_ft REAL,

    Hole_Section TEXT,

    ROP_ft_hr REAL,

    Drilling_Hours REAL,

    Weather_Condition TEXT,

    Weather_Delay_hr REAL,

    Mud_Weight_ppg REAL,

    Daily_Cost_USD REAL,

    PRIMARY KEY (Date, Well_ID),

    FOREIGN KEY (Date)
        REFERENCES Dim_Date(Date),

    FOREIGN KEY (Well_ID)
        REFERENCES Dim_Well(Well_ID),

    FOREIGN KEY (Rig_ID)
        REFERENCES Dim_Rig(Rig_ID)

);
""")


# ============================================================
# CREATE FACT NPT
# ============================================================

print("[10] Creating Fact_NPT...")

cursor.execute("""
CREATE TABLE Fact_NPT (

    NPT_ID TEXT PRIMARY KEY,

    Date TEXT NOT NULL,

    Well_ID TEXT NOT NULL,

    Rig_ID TEXT NOT NULL,

    Rig_Age REAL,

    Rig_Name TEXT,

    Rig_Type TEXT,

    Contractor TEXT,

    Rig_Status TEXT,

    Rig_Day_Rate REAL,

    Operator TEXT,

    Block TEXT,

    Well_Type TEXT,

    Country TEXT,

    Water_Depth_ft REAL,

    Target_Depth_ft REAL,

    Mechanical_Flag INTEGER,

    Weather_Flag INTEGER,

    Drilling_Flag INTEGER,

    Logistics_Flag INTEGER,

    Personnel_Flag INTEGER,

    NPT_Flag INTEGER,

    Lost_Drilling_Days REAL,

    Productivity_Loss_pct REAL,

    NPT_Category TEXT,

    NPT_Subcategory TEXT,

    Root_Cause TEXT,

    Responsible_Party TEXT,

    Duration_hr REAL,

    Cost_USD REAL,

    Deferred_Cost_USD REAL,

    Total_Impact_USD REAL,

    Duration_Bucket TEXT,

    Cost_Bucket TEXT,

    Severity TEXT,

    Downtime_Type TEXT,

    Shift TEXT,

    Corrective_Action TEXT,

    Action_Status TEXT,

    Month INTEGER,

    Quarter INTEGER,

    Season TEXT,

    FOREIGN KEY (Date)
        REFERENCES Dim_Date(Date),

    FOREIGN KEY (Well_ID)
        REFERENCES Dim_Well(Well_ID),

    FOREIGN KEY (Rig_ID)
        REFERENCES Dim_Rig(Rig_ID)

);
""")


# ============================================================
# DATE STANDARDIZATION FUNCTION
# ============================================================

def standardize_date(df, column="Date"):

    if column in df.columns:

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
            dayfirst=True
        ).dt.strftime("%Y-%m-%d")

    return df


# ============================================================
# LOAD DIM_RIG
# ============================================================

print("\n[11] Loading Dim_Rig...")

df = dataframes["Dim_Rig"].copy()

df.to_sql(
    "Dim_Rig",
    conn,
    if_exists="append",
    index=False
)

print(f"     Loaded {len(df):,} rigs")


# ============================================================
# LOAD DIM_WELL
# ============================================================

print("[12] Loading Dim_Well...")

df = dataframes["Dim_Well"].copy()

df["Spud_Date"] = pd.to_datetime(
    df["Spud_Date"],
    errors="coerce"
).dt.strftime("%Y-%m-%d")

df.to_sql(
    "Dim_Well",
    conn,
    if_exists="append",
    index=False
)

print(f"     Loaded {len(df):,} wells")


# ============================================================
# LOAD DIM_DATE
# ============================================================

print("[13] Loading Dim_Date...")

df = dataframes["Dim_Date"].copy()

df = standardize_date(df, "Date")

df.to_sql(
    "Dim_Date",
    conn,
    if_exists="append",
    index=False
)

print(f"     Loaded {len(df):,} dates")


# ============================================================
# LOAD FACT DRILLING
# ============================================================

print("[14] Loading Fact_Drilling_Daily_Report...")

df = dataframes[
    "Fact_Drilling_Daily_Report"
].copy()

df = standardize_date(df, "Date")

df.to_sql(
    "Fact_Drilling_Daily_Report",
    conn,
    if_exists="append",
    index=False
)

print(
    f"     Loaded {len(df):,} daily drilling records"
)


# ============================================================
# LOAD FACT NPT
# ============================================================

print("[15] Loading Fact_NPT...")
print("[15] Loading Fact_NPT...")

df_npt = dataframes["FACT_NPT_FILE"].copy()

df_npt["NPT_ID"] = df_npt["NPT_ID"].astype(str).str.strip()

df_npt = standardize_date(df_npt, "Date")

print("Fact_NPT validation:")
print("Rows:", len(df_npt))
print("NPT_ID nulls:", df_npt["NPT_ID"].isna().sum())
print("NPT_ID duplicates:", df_npt["NPT_ID"].duplicated().sum())
print("Date nulls:", df_npt["Date"].isna().sum())
print("Sample NPT_ID:", df_npt["NPT_ID"].head(5).tolist())
print("Sample Date:", df_npt["Date"].head(5).tolist())

df_npt.to_sql(
    "Fact_NPT",
    conn,
    if_exists="append",
    index=False
)

print(f"     Loaded {len(df_npt):,} NPT records")


# ============================================================
# INDEXES
# ============================================================

print("\n[16] Creating indexes...\n")

indexes = [

    """
    CREATE INDEX idx_well_rig
    ON Dim_Well(Rig_ID);
    """,

    """
    CREATE INDEX idx_well_operator
    ON Dim_Well(Operator);
    """,

    """
    CREATE INDEX idx_well_block
    ON Dim_Well(Block);
    """,

    """
    CREATE INDEX idx_well_status
    ON Dim_Well(Status);
    """,

    """
    CREATE INDEX idx_date_year
    ON Dim_Date(Year);
    """,

    """
    CREATE INDEX idx_date_month
    ON Dim_Date(Month_Number);
    """,

    """
    CREATE INDEX idx_drilling_date
    ON Fact_Drilling_Daily_Report(Date);
    """,

    """
    CREATE INDEX idx_drilling_well
    ON Fact_Drilling_Daily_Report(Well_ID);
    """,

    """
    CREATE INDEX idx_drilling_rig
    ON Fact_Drilling_Daily_Report(Rig_ID);
    """,

    """
    CREATE INDEX idx_npt_date
    ON Fact_NPT(Date);
    """,

    """
    CREATE INDEX idx_npt_well
    ON Fact_NPT(Well_ID);
    """,

    """
    CREATE INDEX idx_npt_rig
    ON Fact_NPT(Rig_ID);
    """,

    """
    CREATE INDEX idx_npt_category
    ON Fact_NPT(NPT_Category);
    """,

    """
    CREATE INDEX idx_npt_severity
    ON Fact_NPT(Severity);
    """
]


for sql in indexes:

    cursor.execute(sql)


# ============================================================
# COMMIT
# ============================================================

conn.commit()


# ============================================================
# VALIDATION
# ============================================================

print("=" * 75)
print("DATABASE VALIDATION")
print("=" * 75)

tables = [

    "Dim_Rig",
    "Dim_Well",
    "Dim_Date",
    "Fact_Drilling_Daily_Report",
    "Fact_NPT"

]


for table in tables:

    count = cursor.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(
        f"{table:<35} {count:>10,} rows"
    )


# ============================================================
# FOREIGN KEY CHECK
# ============================================================

print("\nForeign-key validation...")

fk_errors = cursor.execute(
    "PRAGMA foreign_key_check;"
).fetchall()


if not fk_errors:

    print("[OK] No foreign-key violations.")

else:

    print(
        f"[WARNING] {len(fk_errors)} "
        "foreign-key violations detected."
    )

    for error in fk_errors[:10]:

        print(error)


# ============================================================
# SAMPLE DATA CHECK
# ============================================================

print("\nSample Dim_Well:")

rows = cursor.execute("""
SELECT
    Well_ID,
    Well_Name,
    Operator,
    Rig_ID,
    Block,
    Well_Type,
    Water_Depth_ft,
    Target_Depth_ft,
    Status
FROM Dim_Well
LIMIT 5;
""").fetchall()


for row in rows:

    print(row)


print("\nSample drilling records:")

rows = cursor.execute("""
SELECT
    Date,
    Well_ID,
    Rig_ID,
    Daily_Footage_ft,
    ROP_ft_hr,
    Drilling_Hours,
    Weather_Delay_hr,
    Daily_Cost_USD
FROM Fact_Drilling_Daily_Report
LIMIT 5;
""").fetchall()


for row in rows:

    print(row)


print("\nSample NPT records:")

rows = cursor.execute("""
SELECT
    NPT_ID,
    Date,
    Well_ID,
    Rig_ID,
    NPT_Category,
    NPT_Subcategory,
    Duration_hr,
    Cost_USD,
    Severity
FROM Fact_NPT
LIMIT 5;
""").fetchall()


for row in rows:

    print(row)


# ============================================================
# DATABASE SIZE
# ============================================================

print("\nDatabase:")

print(DB_PATH)

if DB_PATH.exists():

    size_mb = DB_PATH.stat().st_size / (
        1024 * 1024
    )

    print(
        f"Size: {size_mb:.2f} MB"
    )


# ============================================================
# CLOSE
# ============================================================

conn.close()


print("\n" + "=" * 75)
print("SQLITE DATABASE BUILD COMPLETED SUCCESSFULLY")
print("=" * 75)
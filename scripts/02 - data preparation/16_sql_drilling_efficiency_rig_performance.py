# ================================================================
# STAGE 2G.8 — SQL DRILLING EFFICIENCY & RIG PERFORMANCE
# Project: Guyana Offshore Drilling Analytics
# ================================================================
#
# Purpose:
#   Evaluate drilling efficiency and rig performance using
#   exposure-normalized NPT metrics.
#
# Main analyses:
#   1. Overall drilling efficiency
#   2. Rig performance
#   3. Well performance
#   4. Rig × Well performance
#   5. NPT normalized by drilling days
#   6. NPT normalized by footage drilled
#   7. NPT cost normalized by drilling exposure
#   8. Lost drilling days
#   9. Productivity loss
#  10. Root-cause contribution by rig
#  11. Rig performance score
#  12. High-risk wells
#
# Input:
#   database/guyana_drilling.db
#
# Output:
#   outputs/sql_stage_2G.8_Drilling_Efficiency_Rig_Performance.xlsx
#
# ================================================================

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ================================================================
# 1. PROJECT PATHS
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = (
    PROJECT_ROOT
    / "database"
    / "guyana_drilling.db"
)

OUTPUT_DIR = PROJECT_ROOT / "outputs"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.8_Drilling_Efficiency_Rig_Performance.xlsx"
)


# ================================================================
# 2. HEADER
# ================================================================

print("=" * 72)
print("STAGE 2G.8 — SQL DRILLING EFFICIENCY & RIG PERFORMANCE")
print("=" * 72)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")


# ================================================================
# 3. DATABASE VALIDATION
# ================================================================

if not DB_PATH.exists():

    raise FileNotFoundError(
        f"SQLite database not found: {DB_PATH}"
    )


conn = sqlite3.connect(DB_PATH)


# ================================================================
# 4. TABLE INVENTORY
# ================================================================

tables = pd.read_sql_query(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
    """,
    conn
)

print("\nAvailable SQL tables:")

for table in tables["name"]:
    print(f"  - {table}")


required_tables = [
    "Dim_Well",
    "Dim_Rig",
    "Fact_Drilling_Daily_Report",
    "Fact_NPT",
]


missing_tables = [
    table
    for table in required_tables
    if table not in tables["name"].tolist()
]


if missing_tables:

    conn.close()

    raise RuntimeError(
        "Missing required tables: "
        + ", ".join(missing_tables)
    )


# ================================================================
# 5. LOAD FACT TABLES
# ================================================================

print("\nLoading drilling data...")

daily = pd.read_sql_query(
    "SELECT * FROM Fact_Drilling_Daily_Report",
    conn
)

print(f"Fact_Drilling_Daily_Report rows: {len(daily):,}")


print("\nLoading NPT data...")

npt = pd.read_sql_query(
    "SELECT * FROM Fact_NPT",
    conn
)

print(f"Fact_NPT rows: {len(npt):,}")


print("\nLoading dimensions...")

dim_well = pd.read_sql_query(
    "SELECT * FROM Dim_Well",
    conn
)

dim_rig = pd.read_sql_query(
    "SELECT * FROM Dim_Rig",
    conn
)


# ================================================================
# 6. COLUMN INSPECTION
# ================================================================

print("\nFact_Drilling_Daily_Report columns:")

for column in daily.columns:
    print(f"  - {column}")


print("\nDim_Well columns:")

for column in dim_well.columns:
    print(f"  - {column}")


print("\nDim_Rig columns:")

for column in dim_rig.columns:
    print(f"  - {column}")


# ================================================================
# 7. COLUMN DETECTION
# ================================================================

def find_column(
    possible_names,
    available_columns
):

    for name in possible_names:

        if name in available_columns:
            return name

    return None


# Daily drilling columns

daily_date = find_column(
    ["Date", "Drilling_Date"],
    daily.columns
)

daily_well = find_column(
    ["Well_ID", "WellID"],
    daily.columns
)

daily_rig = find_column(
    ["Rig_ID", "RigID"],
    daily.columns
)

footage_col = find_column(
    [
        "Daily_Footage_ft",
        "Footage_ft",
        "Daily_Footage",
        "Footage"
    ],
    daily.columns
)

rop_col = find_column(
    [
        "ROP_ft_hr",
        "ROP",
        "Rate_of_Penetration_ft_hr"
    ],
    daily.columns
)

daily_cost_col = find_column(
    [
        "Daily_Cost_USD",
        "Cost_USD",
        "Daily_Cost"
    ],
    daily.columns
)


# NPT columns

npt_date = find_column(
    ["Date", "NPT_Date"],
    npt.columns
)

npt_well = find_column(
    ["Well_ID", "WellID"],
    npt.columns
)

npt_rig = find_column(
    ["Rig_ID", "RigID"],
    npt.columns
)

npt_duration = find_column(
    [
        "Duration_hr",
        "NPT_Duration_hr",
        "Duration_Hours"
    ],
    npt.columns
)

npt_cost = find_column(
    [
        "Cost_USD",
        "NPT_Cost_USD",
        "Cost"
    ],
    npt.columns
)

npt_lost_days = find_column(
    [
        "Lost_Drilling_Days",
        "Lost_Days"
    ],
    npt.columns
)

npt_productivity_loss = find_column(
    [
        "Productivity_Loss_pct",
        "Productivity_Loss"
    ],
    npt.columns
)

npt_category = find_column(
    [
        "NPT_Category",
        "Category"
    ],
    npt.columns
)

npt_subcategory = find_column(
    [
        "NPT_Subcategory",
        "Subcategory"
    ],
    npt.columns
)

npt_root_cause = find_column(
    [
        "Root_Cause",
        "RootCause"
    ],
    npt.columns
)

npt_severity = find_column(
    [
        "Severity",
        "NPT_Severity"
    ],
    npt.columns
)


# ================================================================
# 8. DISPLAY DETECTED COLUMNS
# ================================================================

print("\nDetected drilling columns:")

print(f"  Date            : {daily_date}")
print(f"  Well            : {daily_well}")
print(f"  Rig             : {daily_rig}")
print(f"  Daily Footage   : {footage_col}")
print(f"  ROP             : {rop_col}")
print(f"  Daily Cost      : {daily_cost_col}")


print("\nDetected NPT columns:")

print(f"  Date            : {npt_date}")
print(f"  Well            : {npt_well}")
print(f"  Rig             : {npt_rig}")
print(f"  Duration        : {npt_duration}")
print(f"  Cost            : {npt_cost}")
print(f"  Lost Days       : {npt_lost_days}")
print(f"  Productivity    : {npt_productivity_loss}")
print(f"  Category        : {npt_category}")
print(f"  Subcategory     : {npt_subcategory}")
print(f"  Root Cause      : {npt_root_cause}")
print(f"  Severity        : {npt_severity}")


# ================================================================
# 9. REQUIRED COLUMNS
# ================================================================

required_daily = {
    "Well_ID": daily_well,
    "Rig_ID": daily_rig,
    "Daily_Footage_ft": footage_col,
}

missing_daily = [
    key
    for key, value in required_daily.items()
    if value is None
]

if missing_daily:

    conn.close()

    raise RuntimeError(
        "Missing required drilling columns: "
        + ", ".join(missing_daily)
    )


required_npt = {
    "Well_ID": npt_well,
    "Rig_ID": npt_rig,
    "Duration_hr": npt_duration,
    "Cost_USD": npt_cost,
}

missing_npt = [
    key
    for key, value in required_npt.items()
    if value is None
]

if missing_npt:

    conn.close()

    raise RuntimeError(
        "Missing required NPT columns: "
        + ", ".join(missing_npt)
    )


# ================================================================
# 10. DATA TYPE NORMALIZATION
# ================================================================

daily[footage_col] = pd.to_numeric(
    daily[footage_col],
    errors="coerce"
).fillna(0)


if rop_col:

    daily[rop_col] = pd.to_numeric(
        daily[rop_col],
        errors="coerce"
    )


if daily_cost_col:

    daily[daily_cost_col] = pd.to_numeric(
        daily[daily_cost_col],
        errors="coerce"
    ).fillna(0)


npt[npt_duration] = pd.to_numeric(
    npt[npt_duration],
    errors="coerce"
).fillna(0)


npt[npt_cost] = pd.to_numeric(
    npt[npt_cost],
    errors="coerce"
).fillna(0)


if npt_lost_days:

    npt[npt_lost_days] = pd.to_numeric(
        npt[npt_lost_days],
        errors="coerce"
    ).fillna(0)


if npt_productivity_loss:

    npt[npt_productivity_loss] = pd.to_numeric(
        npt[npt_productivity_loss],
        errors="coerce"
    ).fillna(0)


# ================================================================
# 11. DRILLING EXPOSURE BY WELL
# ================================================================

print("\nCalculating drilling exposure...")


well_exposure = (
    daily
    .groupby(daily_well)
    .agg(
        Drilling_Days=(
            daily_well,
            "nunique"
        ),

        Total_Footage_ft=(
            footage_col,
            "sum"
        ),
    )
    .reset_index()
)


# Average ROP

if rop_col:

    avg_rop = (
        daily
        .groupby(daily_well)[rop_col]
        .mean()
        .reset_index()
        .rename(
            columns={
                rop_col: "Avg_ROP_ft_hr"
            }
        )
    )

    well_exposure = well_exposure.merge(
        avg_rop,
        on=daily_well,
        how="left"
    )

else:

    well_exposure["Avg_ROP_ft_hr"] = np.nan


# Daily drilling cost

if daily_cost_col:

    drilling_cost = (
        daily
        .groupby(daily_well)[daily_cost_col]
        .sum()
        .reset_index()
        .rename(
            columns={
                daily_cost_col:
                "Total_Drilling_Cost_USD"
            }
        )
    )

    well_exposure = well_exposure.merge(
        drilling_cost,
        on=daily_well,
        how="left"
    )

else:

    well_exposure[
        "Total_Drilling_Cost_USD"
    ] = 0


# ================================================================
# 12. NPT BY WELL
# ================================================================

well_npt = (
    npt
    .groupby(npt_well)
    .agg(
        NPT_Events=(
            npt_well,
            "size"
        ),

        NPT_Hours=(
            npt_duration,
            "sum"
        ),

        NPT_Cost_USD=(
            npt_cost,
            "sum"
        ),
    )
    .reset_index()
)


if npt_lost_days:

    lost_days = (
        npt
        .groupby(npt_well)[npt_lost_days]
        .sum()
        .reset_index()
        .rename(
            columns={
                npt_lost_days:
                "Lost_Drilling_Days"
            }
        )
    )

    well_npt = well_npt.merge(
        lost_days,
        on=npt_well,
        how="left"
    )

else:

    well_npt["Lost_Drilling_Days"] = 0


if npt_productivity_loss:

    productivity = (
        npt
        .groupby(npt_well)[npt_productivity_loss]
        .mean()
        .reset_index()
        .rename(
            columns={
                npt_productivity_loss:
                "Avg_Productivity_Loss_pct"
            }
        )
    )

    well_npt = well_npt.merge(
        productivity,
        on=npt_well,
        how="left"
    )

else:

    well_npt[
        "Avg_Productivity_Loss_pct"
    ] = 0


# ================================================================
# 13. MERGE WELL PERFORMANCE
# ================================================================

well_performance = well_exposure.merge(
    well_npt,
    left_on=daily_well,
    right_on=npt_well,
    how="left"
)


if npt_well != daily_well:

    well_performance.drop(
        columns=[npt_well],
        inplace=True
    )


# Fill NPT metrics

for column in [
    "NPT_Events",
    "NPT_Hours",
    "NPT_Cost_USD",
    "Lost_Drilling_Days",
    "Avg_Productivity_Loss_pct",
]:

    well_performance[column] = (
        well_performance[column]
        .fillna(0)
    )


# ================================================================
# 14. NORMALIZED WELL METRICS
# ================================================================

well_performance["NPT_Hours_per_Drilling_Day"] = (
    well_performance["NPT_Hours"]
    / well_performance["Drilling_Days"].replace(0, np.nan)
)


well_performance["NPT_Cost_per_Drilling_Day_USD"] = (
    well_performance["NPT_Cost_USD"]
    / well_performance["Drilling_Days"].replace(0, np.nan)
)


well_performance["NPT_Events_per_100_Drilling_Days"] = (
    well_performance["NPT_Events"]
    / well_performance["Drilling_Days"].replace(0, np.nan)
    * 100
)


well_performance["NPT_Cost_per_ft_USD"] = (
    well_performance["NPT_Cost_USD"]
    / well_performance["Total_Footage_ft"].replace(
        0,
        np.nan
    )
)


well_performance["NPT_Hours_per_1000_ft"] = (
    well_performance["NPT_Hours"]
    / well_performance["Total_Footage_ft"].replace(
        0,
        np.nan
    )
    * 1000
)


well_performance["Lost_Days_per_Drilling_Day"] = (
    well_performance["Lost_Drilling_Days"]
    / well_performance["Drilling_Days"].replace(
        0,
        np.nan
    )
)


well_performance["NPT_Cost_Pct_of_Drilling_Cost"] = (
    well_performance["NPT_Cost_USD"]
    / well_performance[
        "Total_Drilling_Cost_USD"
    ].replace(0, np.nan)
    * 100
)


# ================================================================
# 15. RIG EXPOSURE
# ================================================================

rig_exposure = (
    daily
    .groupby(daily_rig)
    .agg(
        Drilling_Days=(
            daily_rig,
            "nunique"
        ),

        Wells_Drilled=(
            daily_well,
            "nunique"
        ),

        Total_Footage_ft=(
            footage_col,
            "sum"
        ),
    )
    .reset_index()
)


if rop_col:

    rig_rop = (
        daily
        .groupby(daily_rig)[rop_col]
        .mean()
        .reset_index()
        .rename(
            columns={
                rop_col:
                "Avg_ROP_ft_hr"
            }
        )
    )

    rig_exposure = rig_exposure.merge(
        rig_rop,
        on=daily_rig,
        how="left"
    )

else:

    rig_exposure[
        "Avg_ROP_ft_hr"
    ] = np.nan


if daily_cost_col:

    rig_drilling_cost = (
        daily
        .groupby(daily_rig)[daily_cost_col]
        .sum()
        .reset_index()
        .rename(
            columns={
                daily_cost_col:
                "Total_Drilling_Cost_USD"
            }
        )
    )

    rig_exposure = rig_exposure.merge(
        rig_drilling_cost,
        on=daily_rig,
        how="left"
    )

else:

    rig_exposure[
        "Total_Drilling_Cost_USD"
    ] = 0


# ================================================================
# 16. RIG NPT
# ================================================================

rig_npt = (
    npt
    .groupby(npt_rig)
    .agg(
        NPT_Events=(
            npt_rig,
            "size"
        ),

        NPT_Hours=(
            npt_duration,
            "sum"
        ),

        NPT_Cost_USD=(
            npt_cost,
            "sum"
        ),

        NPT_Wells_Affected=(
            npt_well,
            "nunique"
        ),
    )
    .reset_index()
)


if npt_lost_days:

    rig_lost_days = (
        npt
        .groupby(npt_rig)[npt_lost_days]
        .sum()
        .reset_index()
        .rename(
            columns={
                npt_lost_days:
                "Lost_Drilling_Days"
            }
        )
    )

    rig_npt = rig_npt.merge(
        rig_lost_days,
        on=npt_rig,
        how="left"
    )

else:

    rig_npt[
        "Lost_Drilling_Days"
    ] = 0


# ================================================================
# 17. RIG PERFORMANCE
# ================================================================

rig_performance = rig_exposure.merge(
    rig_npt,
    left_on=daily_rig,
    right_on=npt_rig,
    how="left"
)


if npt_rig != daily_rig:

    rig_performance.drop(
        columns=[npt_rig],
        inplace=True
    )


for column in [
    "NPT_Events",
    "NPT_Hours",
    "NPT_Cost_USD",
    "NPT_Wells_Affected",
    "Lost_Drilling_Days",
]:

    rig_performance[column] = (
        rig_performance[column]
        .fillna(0)
    )


# ================================================================
# 18. NORMALIZED RIG METRICS
# ================================================================

rig_performance[
    "NPT_Hours_per_Drilling_Day"
] = (
    rig_performance["NPT_Hours"]
    / rig_performance["Drilling_Days"]
    .replace(0, np.nan)
)


rig_performance[
    "NPT_Cost_per_Drilling_Day_USD"
] = (
    rig_performance["NPT_Cost_USD"]
    / rig_performance["Drilling_Days"]
    .replace(0, np.nan)
)


rig_performance[
    "NPT_Events_per_100_Drilling_Days"
] = (
    rig_performance["NPT_Events"]
    / rig_performance["Drilling_Days"]
    .replace(0, np.nan)
    * 100
)


rig_performance[
    "NPT_Cost_per_ft_USD"
] = (
    rig_performance["NPT_Cost_USD"]
    / rig_performance["Total_Footage_ft"]
    .replace(0, np.nan)
)


rig_performance[
    "NPT_Hours_per_1000_ft"
] = (
    rig_performance["NPT_Hours"]
    / rig_performance["Total_Footage_ft"]
    .replace(0, np.nan)
    * 1000
)


rig_performance[
    "Lost_Days_per_Drilling_Day"
] = (
    rig_performance["Lost_Drilling_Days"]
    / rig_performance["Drilling_Days"]
    .replace(0, np.nan)
)


rig_performance[
    "NPT_Cost_Pct_of_Drilling_Cost"
] = (
    rig_performance["NPT_Cost_USD"]
    / rig_performance[
        "Total_Drilling_Cost_USD"
    ].replace(0, np.nan)
    * 100
)


# ================================================================
# 19. RIG PERFORMANCE SCORE
# ================================================================
#
# Lower NPT = better.
#
# Metrics:
#   - NPT hours/day
#   - NPT cost/day
#   - NPT cost/ft
#
# Each metric is converted into a percentile ranking.
#
# Lower percentile = better.
#
# ================================================================

score_columns = [
    "NPT_Hours_per_Drilling_Day",
    "NPT_Cost_per_Drilling_Day_USD",
    "NPT_Cost_per_ft_USD",
]


for column in score_columns:

    rig_performance[
        column + "_Rank"
    ] = (
        rig_performance[column]
        .rank(
            method="average",
            ascending=True,
            pct=True
        )
        * 100
    )


rig_performance["Performance_Score"] = (
    rig_performance[
        "NPT_Hours_per_Drilling_Day_Rank"
    ]
    + rig_performance[
        "NPT_Cost_per_Drilling_Day_USD_Rank"
    ]
    + rig_performance[
        "NPT_Cost_per_ft_USD_Rank"
    ]
) / 3


rig_performance["Performance_Class"] = pd.cut(
    rig_performance["Performance_Score"],
    bins=[
        -np.inf,
        25,
        50,
        75,
        np.inf
    ],
    labels=[
        "Best",
        "Good",
        "Watch",
        "Poor"
    ]
)


rig_performance = rig_performance.sort_values(
    "Performance_Score"
).reset_index(drop=True)


# ================================================================
# 20. NPT ROOT CAUSE BY RIG
# ================================================================

rig_root_cause = (
    npt
    .groupby(
        [
            npt_rig,
            npt_category,
            npt_subcategory,
        ],
        dropna=False
    )
    .agg(
        NPT_Events=(
            npt_rig,
            "size"
        ),

        NPT_Hours=(
            npt_duration,
            "sum"
        ),

        NPT_Cost_USD=(
            npt_cost,
            "sum"
        ),
    )
    .reset_index()
)


rig_root_cause["Rig_Cost_Pct"] = (
    rig_root_cause["NPT_Cost_USD"]
    / rig_root_cause
    .groupby(npt_rig)["NPT_Cost_USD"]
    .transform("sum")
    * 100
)


rig_root_cause = rig_root_cause.sort_values(
    "NPT_Cost_USD",
    ascending=False
).reset_index(drop=True)


# ================================================================
# 21. WELL ROOT CAUSE
# ================================================================

well_root_cause = (
    npt
    .groupby(
        [
            npt_well,
            npt_category,
            npt_subcategory,
        ],
        dropna=False
    )
    .agg(
        NPT_Events=(
            npt_well,
            "size"
        ),

        NPT_Hours=(
            npt_duration,
            "sum"
        ),

        NPT_Cost_USD=(
            npt_cost,
            "sum"
        ),
    )
    .reset_index()
)


well_root_cause = well_root_cause.sort_values(
    "NPT_Cost_USD",
    ascending=False
).reset_index(drop=True)


# ================================================================
# 22. HIGH-RISK WELLS
# ================================================================

high_risk_wells = (
    well_performance
    .sort_values(
        [
            "NPT_Cost_per_Drilling_Day_USD",
            "NPT_Hours_per_Drilling_Day"
        ],
        ascending=False
    )
    .head(15)
    .copy()
)


high_risk_wells.insert(
    0,
    "Risk_Rank",
    range(1, len(high_risk_wells) + 1)
)


# ================================================================
# 23. NPT CATEGORY BY RIG
# ================================================================

category_rig = (
    npt
    .groupby(
        [
            npt_rig,
            npt_category
        ],
        dropna=False
    )
    .agg(
        NPT_Events=(
            npt_category,
            "size"
        ),

        NPT_Hours=(
            npt_duration,
            "sum"
        ),

        NPT_Cost_USD=(
            npt_cost,
            "sum"
        ),
    )
    .reset_index()
)


category_rig["Rig_Cost_Pct"] = (
    category_rig["NPT_Cost_USD"]
    / category_rig
    .groupby(npt_rig)["NPT_Cost_USD"]
    .transform("sum")
    * 100
)


category_rig = category_rig.sort_values(
    "NPT_Cost_USD",
    ascending=False
).reset_index(drop=True)


# ================================================================
# 24. OVERALL PERFORMANCE
# ================================================================

total_drilling_days = (
    daily[daily_well]
    .nunique()
    if daily_date is None
    else daily[daily_date]
    .nunique()
)


total_footage = daily[
    footage_col
].sum()


total_drilling_cost = (
    daily[daily_cost_col].sum()
    if daily_cost_col
    else 0
)


total_npt_events = len(npt)

total_npt_hours = npt[
    npt_duration
].sum()

total_npt_cost = npt[
    npt_cost
].sum()


total_lost_days = (
    npt[npt_lost_days].sum()
    if npt_lost_days
    else 0
)


overall = pd.DataFrame({

    "Metric": [

        "Total Daily Drilling Records",
        "Total Wells",
        "Total Rigs",
        "Total Drilling Days",
        "Total Footage ft",
        "Total Drilling Cost USD",
        "Total NPT Events",
        "Total NPT Hours",
        "Total NPT Cost USD",
        "Total Lost Drilling Days",
        "NPT Hours per Drilling Day",
        "NPT Cost per Drilling Day USD",
        "NPT Cost per Foot USD",
        "NPT Hours per 1000 ft",
    ],

    "Value": [

        len(daily),
        daily[daily_well].nunique(),
        daily[daily_rig].nunique(),
        total_drilling_days,
        total_footage,
        total_drilling_cost,
        total_npt_events,
        total_npt_hours,
        total_npt_cost,
        total_lost_days,

        (
            total_npt_hours
            / total_drilling_days
            if total_drilling_days
            else 0
        ),

        (
            total_npt_cost
            / total_drilling_days
            if total_drilling_days
            else 0
        ),

        (
            total_npt_cost
            / total_footage
            if total_footage
            else 0
        ),

        (
            total_npt_hours
            / total_footage
            * 1000
            if total_footage
            else 0
        ),
    ]
})


# ================================================================
# 25. TOP RIG ROOT CAUSES
# ================================================================

top_rig_root_causes = (
    rig_root_cause
    .head(25)
    .copy()
)


# ================================================================
# 26. TOP WELL ROOT CAUSES
# ================================================================

top_well_root_causes = (
    well_root_cause
    .head(25)
    .copy()
)


# ================================================================
# 27. EXECUTIVE SUMMARY
# ================================================================

best_rig = (
    rig_performance.iloc[0][daily_rig]
    if not rig_performance.empty
    else "N/A"
)

best_score = (
    rig_performance.iloc[0]["Performance_Score"]
    if not rig_performance.empty
    else np.nan
)


worst_rig = (
    rig_performance.iloc[-1][daily_rig]
    if not rig_performance.empty
    else "N/A"
)

worst_score = (
    rig_performance.iloc[-1]["Performance_Score"]
    if not rig_performance.empty
    else np.nan
)


highest_cost_well = (
    well_performance
    .sort_values(
        "NPT_Cost_per_Drilling_Day_USD",
        ascending=False
    )
    .iloc[0][daily_well]
    if not well_performance.empty
    else "N/A"
)


executive_summary = pd.DataFrame({

    "Metric": [

        "Total NPT Cost USD",
        "Total NPT Hours",
        "NPT Hours per Drilling Day",
        "NPT Cost per Drilling Day USD",
        "NPT Cost per Foot USD",
        "NPT Hours per 1000 ft",
        "Total Lost Drilling Days",
        "Best Performing Rig",
        "Best Rig Performance Score",
        "Worst Performing Rig",
        "Worst Rig Performance Score",
        "Highest Exposure-Normalized Well",
    ],

    "Value": [

        total_npt_cost,
        total_npt_hours,

        (
            total_npt_hours
            / total_drilling_days
            if total_drilling_days
            else 0
        ),

        (
            total_npt_cost
            / total_drilling_days
            if total_drilling_days
            else 0
        ),

        (
            total_npt_cost
            / total_footage
            if total_footage
            else 0
        ),

        (
            total_npt_hours
            / total_footage
            * 1000
            if total_footage
            else 0
        ),

        total_lost_days,

        best_rig,
        best_score,

        worst_rig,
        worst_score,

        highest_cost_well,
    ]
})


# ================================================================
# 28. PRINT OVERALL RESULTS
# ================================================================

print("\n" + "=" * 72)
print("OVERALL DRILLING EFFICIENCY")
print("=" * 72)

print(
    f"\nTotal drilling records : {len(daily):,}"
)

print(
    f"Total wells            : "
    f"{daily[daily_well].nunique():,}"
)

print(
    f"Total rigs             : "
    f"{daily[daily_rig].nunique():,}"
)

print(
    f"Total drilling days    : "
    f"{total_drilling_days:,}"
)

print(
    f"Total footage          : "
    f"{total_footage:,.0f} ft"
)

print(
    f"Total NPT hours        : "
    f"{total_npt_hours:,.2f} hr"
)

print(
    f"Total NPT cost         : "
    f"${total_npt_cost:,.2f}"
)

print(
    f"NPT hr / drilling day  : "
    f"{total_npt_hours / total_drilling_days:,.2f}"
)

print(
    f"NPT cost / drilling day: "
    f"${total_npt_cost / total_drilling_days:,.2f}"
)

print(
    f"NPT cost / ft          : "
    f"${total_npt_cost / total_footage:,.2f}"
)


# ================================================================
# 29. PRINT RIG PERFORMANCE
# ================================================================

print("\n" + "=" * 72)
print("RIG PERFORMANCE — EXPOSURE NORMALIZED")
print("=" * 72)

display_columns = [
    daily_rig,
    "Wells_Drilled",
    "Drilling_Days",
    "Total_Footage_ft",
    "NPT_Events",
    "NPT_Hours",
    "NPT_Cost_USD",
    "NPT_Hours_per_Drilling_Day",
    "NPT_Cost_per_Drilling_Day_USD",
    "NPT_Cost_per_ft_USD",
    "Performance_Score",
    "Performance_Class",
]


print(
    rig_performance[
        display_columns
    ].to_string(index=False)
)


# ================================================================
# 30. PRINT HIGH-RISK WELLS
# ================================================================

print("\n" + "=" * 72)
print("TOP 15 HIGH-RISK WELLS")
print("=" * 72)

well_display = [
    "Risk_Rank",
    daily_well,
    "Drilling_Days",
    "Total_Footage_ft",
    "NPT_Events",
    "NPT_Hours",
    "NPT_Cost_USD",
    "NPT_Hours_per_Drilling_Day",
    "NPT_Cost_per_Drilling_Day_USD",
    "NPT_Cost_per_ft_USD",
]


print(
    high_risk_wells[
        well_display
    ].to_string(index=False)
)


# ================================================================
# 31. EXPORT TO EXCEL
# ================================================================

print("\n" + "=" * 72)
print("EXPORTING RESULTS")
print("=" * 72)


with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    executive_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    overall.to_excel(
        writer,
        sheet_name="Overall_Efficiency",
        index=False
    )

    rig_performance.to_excel(
        writer,
        sheet_name="Rig_Performance",
        index=False
    )

    well_performance.to_excel(
        writer,
        sheet_name="Well_Performance",
        index=False
    )

    high_risk_wells.to_excel(
        writer,
        sheet_name="High_Risk_Wells",
        index=False
    )

    rig_root_cause.to_excel(
        writer,
        sheet_name="Rig_Root_Cause",
        index=False
    )

    top_rig_root_causes.to_excel(
        writer,
        sheet_name="Top_Rig_Root_Causes",
        index=False
    )

    well_root_cause.to_excel(
        writer,
        sheet_name="Well_Root_Cause",
        index=False
    )

    top_well_root_causes.to_excel(
        writer,
        sheet_name="Top_Well_Root_Causes",
        index=False
    )

    category_rig.to_excel(
        writer,
        sheet_name="Category_by_Rig",
        index=False
    )


# ================================================================
# 32. EXCEL FORMATTING
# ================================================================

from openpyxl import load_workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment
)
from openpyxl.utils import get_column_letter


wb = load_workbook(
    OUTPUT_FILE
)


header_fill = PatternFill(
    fill_type="solid",
    fgColor="1F4E78"
)


header_font = Font(
    bold=True,
    color="FFFFFF"
)


for ws in wb.worksheets:

    for cell in ws[1]:

        cell.fill = header_fill
        cell.font = header_font

        cell.alignment = Alignment(
            horizontal="center"
        )


    ws.freeze_panes = "A2"


    for column_cells in ws.columns:

        max_length = 0

        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:

            try:

                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

            except Exception:

                pass


        ws.column_dimensions[
            column_letter
        ].width = min(
            max(max_length + 2, 10),
            40
        )


wb.save(
    OUTPUT_FILE
)


# ================================================================
# 33. CLOSE DATABASE
# ================================================================

conn.close()


# ================================================================
# 34. FINAL STATUS
# ================================================================

print("\n" + "=" * 72)
print("STAGE 2G.8 COMPLETED SUCCESSFULLY")
print("=" * 72)

print("\nOutput file:")
print(f"  {OUTPUT_FILE}")

print("\nGenerated sheets:")

sheets = [
    "Executive_Summary",
    "Overall_Efficiency",
    "Rig_Performance",
    "Well_Performance",
    "High_Risk_Wells",
    "Rig_Root_Cause",
    "Top_Rig_Root_Causes",
    "Well_Root_Cause",
    "Top_Well_Root_Causes",
    "Category_by_Rig",
]

for sheet in sheets:
    print(f"  ✓ {sheet}")


print("\nStage 2G.8 is ready for validation.")
print("=" * 72)
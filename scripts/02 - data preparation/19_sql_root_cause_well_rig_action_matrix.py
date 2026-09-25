#!/usr/bin/env python3

"""
========================================================================
STAGE 2G.9.1
SQL ROOT CAUSE × WELL × RIG ACTION MATRIX
========================================================================

Project:
    Guyana Offshore Drilling Analytics

Purpose:
    Identify the specific root causes, wells and rigs driving NPT impact,
    connect them with responsible parties and corrective actions, and
    prioritize operational intervention.

Input:
    SQLite database
        Fact_NPT
        Fact_Drilling_Daily_Report

Output:
    Excel workbook with:
        - Executive Summary
        - Root Cause Action Matrix
        - Rig × Root Cause
        - Well × Root Cause
        - Top Opportunities
        - Responsible Party
        - Action Status
        - Pareto Root Cause
========================================================================
"""

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np


# ======================================================================
# PROJECT PATHS
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.9.1_Root_Cause_Well_Rig_Action_Matrix"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.9.1_Root_Cause_Well_Rig_Action_Matrix.xlsx"
)


# ======================================================================
# HEADER
# ======================================================================

print("=" * 80)
print("STAGE 2G.9.1 — ROOT CAUSE × WELL × RIG ACTION MATRIX")
print("=" * 80)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")


if not DB_PATH.exists():
    raise FileNotFoundError(
        f"Database not found:\n{DB_PATH}"
    )


# ======================================================================
# DATABASE CONNECTION
# ======================================================================

conn = sqlite3.connect(DB_PATH)


# ======================================================================
# TABLE DISCOVERY
# ======================================================================

tables = pd.read_sql_query(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
    """,
    conn
)

print("\nAvailable tables:")
print(tables.to_string(index=False))


table_names = set(tables["name"].tolist())


def find_table(candidates):

    for table in candidates:

        if table in table_names:
            return table

    return None


npt_table = find_table(
    [
        "Fact_NPT",
        "fact_npt",
        "FactNPT"
    ]
)

drilling_table = find_table(
    [
        "Fact_Drilling_Daily_Report",
        "fact_drilling_daily_report",
        "FactDrillingDailyReport"
    ]
)


if npt_table is None:
    raise RuntimeError(
        "Fact_NPT table could not be identified."
    )

if drilling_table is None:
    raise RuntimeError(
        "Fact_Drilling_Daily_Report table could not be identified."
    )


print(f"\nNPT table      : {npt_table}")
print(f"Drilling table : {drilling_table}")


# ======================================================================
# LOAD DATA
# ======================================================================

df_npt = pd.read_sql_query(
    f'SELECT * FROM "{npt_table}"',
    conn
)

df_drilling = pd.read_sql_query(
    f'SELECT * FROM "{drilling_table}"',
    conn
)


print(f"\nNPT rows      : {len(df_npt)}")
print(f"Drilling rows : {len(df_drilling)}")


# ======================================================================
# NORMALIZE COLUMN NAMES
# ======================================================================

df_npt.columns = [
    c.strip()
    for c in df_npt.columns
]

df_drilling.columns = [
    c.strip()
    for c in df_drilling.columns
]


# ======================================================================
# REQUIRED COLUMNS
# ======================================================================

required_npt_columns = [
    "NPT_ID",
    "Date",
    "Well_ID",
    "Rig_ID",
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Severity",
    "Corrective_Action",
    "Action_Status"
]


for column in required_npt_columns:

    if column not in df_npt.columns:

        raise RuntimeError(
            f"Missing required Fact_NPT column: {column}"
        )


# ======================================================================
# NUMERIC CONVERSION
# ======================================================================

numeric_columns = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD"
]


for column in numeric_columns:

    df_npt[column] = pd.to_numeric(
        df_npt[column],
        errors="coerce"
    ).fillna(0)


# ======================================================================
# TEXT CLEANUP
# ======================================================================

text_columns = [
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Severity",
    "Corrective_Action",
    "Action_Status",
    "Well_ID",
    "Rig_ID"
]


for column in text_columns:

    df_npt[column] = (
        df_npt[column]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )


# ======================================================================
# SEVERITY SCORE
# ======================================================================

severity_map = {
    "Low": 1,
    "Medium": 2,
    "High": 3,
    "Critical": 4
}

df_npt["Severity_Score"] = (
    df_npt["Severity"]
    .map(severity_map)
    .fillna(1)
)


# ======================================================================
# ACTION STATUS SCORE
# ======================================================================

action_status_map = {
    "Closed": 1,
    "Completed": 1,
    "Resolved": 1,
    "In Progress": 2,
    "Open": 3,
    "Pending": 3,
    "Unknown": 2
}

df_npt["Action_Status_Score"] = (
    df_npt["Action_Status"]
    .map(action_status_map)
    .fillna(2)
)


# ======================================================================
# NORMALIZATION FUNCTION
# ======================================================================

def min_max(series):

    series = series.astype(float)

    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum):

        return pd.Series(
            np.zeros(len(series)),
            index=series.index
        )

    if maximum == minimum:

        return pd.Series(
            np.ones(len(series)) * 50,
            index=series.index
        )

    return (
        (series - minimum)
        / (maximum - minimum)
        * 100
    )


# ======================================================================
# ROOT CAUSE × WELL × RIG MATRIX
# ======================================================================

matrix = (
    df_npt
    .groupby(
        [
            "Rig_ID",
            "Well_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party"
        ],
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Avg_Severity_Score=("Severity_Score", "mean"),
        Max_Severity_Score=("Severity_Score", "max"),
        Corrective_Actions=("Corrective_Action", "nunique"),
        Action_Statuses=("Action_Status", "nunique")
    )
    .reset_index()
)


# ======================================================================
# IMPACT COMPONENTS
# ======================================================================

matrix["Cost_Impact_Score"] = min_max(
    matrix["Total_Impact_USD"]
)

matrix["NPT_Hours_Score"] = min_max(
    matrix["NPT_Hours"]
)

matrix["Frequency_Score"] = min_max(
    matrix["NPT_Events"]
)

matrix["Severity_Impact_Score"] = min_max(
    matrix["Avg_Severity_Score"]
)


# ======================================================================
# ACTION PRIORITY SCORE
# ======================================================================

matrix["Action_Priority_Score"] = (
      matrix["Cost_Impact_Score"] * 0.40
    + matrix["NPT_Hours_Score"] * 0.25
    + matrix["Frequency_Score"] * 0.15
    + matrix["Severity_Impact_Score"] * 0.20
)


# ======================================================================
# PRIORITY CLASS
# ======================================================================

def priority_class(score):

    if score >= 80:
        return "CRITICAL"

    if score >= 65:
        return "HIGH"

    if score >= 50:
        return "MEDIUM"

    return "LOW"


matrix["Priority"] = (
    matrix["Action_Priority_Score"]
    .apply(priority_class)
)


# ======================================================================
# RANKING
# ======================================================================

matrix = matrix.sort_values(
    [
        "Action_Priority_Score",
        "Total_Impact_USD"
    ],
    ascending=[
        False,
        False
    ]
).reset_index(drop=True)


matrix["Priority_Rank"] = (
    matrix.index + 1
)


# ======================================================================
# ACTION STATUS / CORRECTIVE ACTION DETAIL
# ======================================================================

action_detail = (
    df_npt[
        [
            "Rig_ID",
            "Well_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party",
            "Corrective_Action",
            "Action_Status"
        ]
    ]
    .drop_duplicates()
)


action_detail = (
    action_detail
    .groupby(
        [
            "Rig_ID",
            "Well_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party"
        ]
    )
    .agg(
        Corrective_Action=(
            "Corrective_Action",
            lambda x: " | ".join(
                sorted(
                    set(x.astype(str))
                )
            )
        ),
        Action_Status=(
            "Action_Status",
            lambda x: " | ".join(
                sorted(
                    set(x.astype(str))
                )
            )
        )
    )
    .reset_index()
)


matrix = matrix.merge(
    action_detail,
    on=[
        "Rig_ID",
        "Well_ID",
        "NPT_Category",
        "NPT_Subcategory",
        "Root_Cause",
        "Responsible_Party"
    ],
    how="left"
)


# ======================================================================
# RIG × ROOT CAUSE
# ======================================================================

rig_root_cause = (
    df_npt
    .groupby(
        [
            "Rig_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause"
        ],
        dropna=False
    )
    .agg(
        Wells_Affected=("Well_ID", "nunique"),
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Avg_Severity=("Severity_Score", "mean")
    )
    .reset_index()
)


rig_root_cause["Impact_Score"] = (
    min_max(
        rig_root_cause["Total_Impact_USD"]
    ) * 0.50
    +
    min_max(
        rig_root_cause["NPT_Hours"]
    ) * 0.30
    +
    min_max(
        rig_root_cause["NPT_Events"]
    ) * 0.20
)


rig_root_cause["Priority"] = (
    rig_root_cause["Impact_Score"]
    .apply(priority_class)
)


rig_root_cause = rig_root_cause.sort_values(
    "Impact_Score",
    ascending=False
).reset_index(drop=True)


rig_root_cause["Priority_Rank"] = (
    rig_root_cause.index + 1
)


# ======================================================================
# WELL × ROOT CAUSE
# ======================================================================

well_root_cause = (
    df_npt
    .groupby(
        [
            "Well_ID",
            "Rig_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause"
        ],
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Avg_Severity=("Severity_Score", "mean")
    )
    .reset_index()
)


well_root_cause["Impact_Score"] = (
    min_max(
        well_root_cause["Total_Impact_USD"]
    ) * 0.50
    +
    min_max(
        well_root_cause["NPT_Hours"]
    ) * 0.30
    +
    min_max(
        well_root_cause["NPT_Events"]
    ) * 0.20
)


well_root_cause["Priority"] = (
    well_root_cause["Impact_Score"]
    .apply(priority_class)
)


well_root_cause = well_root_cause.sort_values(
    "Impact_Score",
    ascending=False
).reset_index(drop=True)


well_root_cause["Priority_Rank"] = (
    well_root_cause.index + 1
)


# ======================================================================
# RESPONSIBLE PARTY ANALYSIS
# ======================================================================

responsible_party = (
    df_npt
    .groupby(
        "Responsible_Party",
        dropna=False
    )
    .agg(
        Wells_Affected=("Well_ID", "nunique"),
        Rigs_Affected=("Rig_ID", "nunique"),
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum")
    )
    .reset_index()
)


responsible_party["Impact_Score"] = (
    min_max(
        responsible_party["Total_Impact_USD"]
    ) * 0.50
    +
    min_max(
        responsible_party["NPT_Hours"]
    ) * 0.30
    +
    min_max(
        responsible_party["NPT_Events"]
    ) * 0.20
)


responsible_party["Priority"] = (
    responsible_party["Impact_Score"]
    .apply(priority_class)
)


responsible_party = responsible_party.sort_values(
    "Impact_Score",
    ascending=False
).reset_index(drop=True)


responsible_party["Priority_Rank"] = (
    responsible_party.index + 1
)


# ======================================================================
# ACTION STATUS ANALYSIS
# ======================================================================

action_status = (
    df_npt
    .groupby(
        "Action_Status",
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum")
    )
    .reset_index()
)


action_status = action_status.sort_values(
    "Total_Impact_USD",
    ascending=False
).reset_index(drop=True)


# ======================================================================
# PARETO ROOT CAUSE
# ======================================================================

pareto = (
    df_npt
    .groupby(
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause"
        ],
        dropna=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum")
    )
    .reset_index()
)


pareto = pareto.sort_values(
    "Total_Impact_USD",
    ascending=False
).reset_index(drop=True)


pareto["Cumulative_Impact_USD"] = (
    pareto["Total_Impact_USD"]
    .cumsum()
)


total_impact = pareto["Total_Impact_USD"].sum()


if total_impact > 0:

    pareto["Cumulative_Impact_Pct"] = (
        pareto["Cumulative_Impact_USD"]
        / total_impact
        * 100
    )

else:

    pareto["Cumulative_Impact_Pct"] = 0


pareto["Pareto_Flag"] = np.where(
    pareto["Cumulative_Impact_Pct"] <= 80,
    "TOP_80_PERCENT",
    "REMAINDER"
)


# ======================================================================
# TOP OPPORTUNITIES
# ======================================================================

top_opportunities = matrix.head(25).copy()


# ======================================================================
# EXECUTIVE SUMMARY
# ======================================================================

total_npt_events = len(df_npt)

total_npt_hours = df_npt["Duration_hr"].sum()

total_npt_cost = df_npt["Cost_USD"].sum()

total_deferred_cost = df_npt["Deferred_Cost_USD"].sum()

total_impact = df_npt["Total_Impact_USD"].sum()

critical_count = (
    matrix["Priority"]
    .eq("CRITICAL")
    .sum()
)

high_count = (
    matrix["Priority"]
    .eq("HIGH")
    .sum()
)


top_matrix = (
    matrix.iloc[0]
    if len(matrix) > 0
    else None
)

top_root = (
    pareto.iloc[0]
    if len(pareto) > 0
    else None
)

top_rig = (
    rig_root_cause.iloc[0]
    if len(rig_root_cause) > 0
    else None
)

top_well = (
    well_root_cause.iloc[0]
    if len(well_root_cause) > 0
    else None
)


summary = pd.DataFrame(
    {
        "Metric": [
            "Total NPT Events",
            "Total NPT Hours",
            "Total NPT Cost USD",
            "Total Deferred Cost USD",
            "Total Impact USD",
            "Unique Wells Affected",
            "Unique Rigs Affected",
            "Critical Action Items",
            "High Action Items",
            "Top Root Cause",
            "Top Root Cause Impact USD",
            "Top Rig",
            "Top Rig Root Cause",
            "Top Rig Impact USD",
            "Top Well",
            "Top Well Root Cause",
            "Top Well Impact USD"
        ],
        "Value": [
            total_npt_events,
            total_npt_hours,
            total_npt_cost,
            total_deferred_cost,
            total_impact,
            df_npt["Well_ID"].nunique(),
            df_npt["Rig_ID"].nunique(),
            critical_count,
            high_count,
            top_root["Root_Cause"]
                if top_root is not None else None,
            top_root["Total_Impact_USD"]
                if top_root is not None else None,
            top_rig["Rig_ID"]
                if top_rig is not None else None,
            top_rig["Root_Cause"]
                if top_rig is not None else None,
            top_rig["Total_Impact_USD"]
                if top_rig is not None else None,
            top_well["Well_ID"]
                if top_well is not None else None,
            top_well["Root_Cause"]
                if top_well is not None else None,
            top_well["Total_Impact_USD"]
                if top_well is not None else None
        ]
    }
)


# ======================================================================
# WRITE EXCEL
# ======================================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    matrix.to_excel(
        writer,
        sheet_name="Root_Cause_Action_Matrix",
        index=False
    )

    rig_root_cause.to_excel(
        writer,
        sheet_name="Rig_Root_Cause",
        index=False
    )

    well_root_cause.to_excel(
        writer,
        sheet_name="Well_Root_Cause",
        index=False
    )

    top_opportunities.to_excel(
        writer,
        sheet_name="Top_Opportunities",
        index=False
    )

    responsible_party.to_excel(
        writer,
        sheet_name="Responsible_Party",
        index=False
    )

    action_status.to_excel(
        writer,
        sheet_name="Action_Status",
        index=False
    )

    pareto.to_excel(
        writer,
        sheet_name="Pareto_Root_Cause",
        index=False
    )


# ======================================================================
# CLOSE DATABASE
# ======================================================================

conn.close()


# ======================================================================
# CONSOLE OUTPUT
# ======================================================================

print("\n" + "=" * 80)
print("STAGE 2G.9.1 COMPLETED SUCCESSFULLY")
print("=" * 80)

print("\nOutput file:")
print(OUTPUT_FILE)


print("\nTOP 15 ACTION OPPORTUNITIES:")

print(
    matrix[
        [
            "Priority_Rank",
            "Rig_ID",
            "Well_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party",
            "NPT_Events",
            "NPT_Hours",
            "Total_Impact_USD",
            "Action_Priority_Score",
            "Priority"
        ]
    ]
    .head(15)
    .to_string(index=False)
)


print("\nTOP RIG × ROOT CAUSE:")

print(
    rig_root_cause[
        [
            "Priority_Rank",
            "Rig_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Wells_Affected",
            "NPT_Events",
            "NPT_Hours",
            "Total_Impact_USD",
            "Impact_Score",
            "Priority"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


print("\nTOP WELL × ROOT CAUSE:")

print(
    well_root_cause[
        [
            "Priority_Rank",
            "Well_ID",
            "Rig_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "NPT_Events",
            "NPT_Hours",
            "Total_Impact_USD",
            "Impact_Score",
            "Priority"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


print("\nEXECUTIVE SUMMARY:")
print(summary.to_string(index=False))

print("\n" + "=" * 80)
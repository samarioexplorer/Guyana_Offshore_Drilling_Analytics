#!/usr/bin/env python3

"""
========================================================================
STAGE 2G.9
SQL OPERATIONAL OPPORTUNITY & ROOT-CAUSE PRIORITIZATION
========================================================================

Project:
    Guyana Offshore Drilling Analytics

Purpose:
    Convert drilling performance and NPT/root-cause results into
    prioritized operational opportunities.

Outputs:
    - Root Cause Impact
    - Well Opportunity
    - Rig Opportunity
    - Opportunity Prioritization
    - Pareto Root Cause
    - Executive Summary
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
    / "sql_stage_2G.9_Operational_Opportunity_Prioritization"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.9_Operational_Opportunity_Prioritization.xlsx"
)


# ======================================================================
# DATABASE CONNECTION
# ======================================================================

print("=" * 80)
print("STAGE 2G.9 — OPERATIONAL OPPORTUNITY & ROOT-CAUSE PRIORITIZATION")
print("=" * 80)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")


if not DB_PATH.exists():
    raise FileNotFoundError(
        f"Database not found:\n{DB_PATH}"
    )


conn = sqlite3.connect(DB_PATH)


# ======================================================================
# DATABASE INSPECTION
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


# ======================================================================
# IDENTIFY FACT TABLES
# ======================================================================

table_names = set(tables["name"].tolist())


required_candidates = {
    "drilling": [
        "Fact_Drilling_Daily_Report",
        "fact_drilling_daily_report",
        "FactDrillingDailyReport"
    ],
    "npt": [
        "Fact_NPT",
        "fact_npt",
        "FactNPT"
    ]
}


def find_table(candidates):

    for table in candidates:

        if table in table_names:
            return table

    return None


drilling_table = find_table(
    required_candidates["drilling"]
)

npt_table = find_table(
    required_candidates["npt"]
)


if drilling_table is None:
    raise RuntimeError(
        "Fact drilling table could not be identified."
    )

if npt_table is None:
    raise RuntimeError(
        "Fact NPT table could not be identified."
    )


print(f"\nDrilling fact table : {drilling_table}")
print(f"NPT fact table      : {npt_table}")


# ======================================================================
# LOAD DRILLING DATA
# ======================================================================

drilling_query = f"""
SELECT *
FROM "{drilling_table}"
"""

df_drilling = pd.read_sql_query(
    drilling_query,
    conn
)


print("\nDrilling rows:", len(df_drilling))


# ======================================================================
# LOAD NPT DATA
# ======================================================================

npt_query = f"""
SELECT *
FROM "{npt_table}"
"""

df_npt = pd.read_sql_query(
    npt_query,
    conn
)


print("NPT rows:", len(df_npt))


# ======================================================================
# NORMALIZE COLUMN NAMES
# ======================================================================

df_drilling.columns = [
    c.strip()
    for c in df_drilling.columns
]

df_npt.columns = [
    c.strip()
    for c in df_npt.columns
]


# ======================================================================
# DISPLAY SCHEMA
# ======================================================================

print("\nDrilling columns:")
print(df_drilling.columns.tolist())

print("\nNPT columns:")
print(df_npt.columns.tolist())


# ======================================================================
# BASIC VALIDATION
# ======================================================================

required_drilling_columns = [
    "Well_ID",
    "Rig_ID"
]

required_npt_columns = [
    "Well_ID",
    "Rig_ID",
    "NPT_Category",
    "Duration_hr",
    "Cost_USD"
]


for column in required_drilling_columns:

    if column not in df_drilling.columns:

        raise RuntimeError(
            f"Missing drilling column: {column}"
        )


for column in required_npt_columns:

    if column not in df_npt.columns:

        raise RuntimeError(
            f"Missing NPT column: {column}"
        )


# ======================================================================
# NUMERIC CLEANUP
# ======================================================================

for column in [
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Daily_Cost_USD",
    "Weather_delay_hr"
]:

    if column in df_drilling.columns:

        df_drilling[column] = pd.to_numeric(
            df_drilling[column],
            errors="coerce"
        )


for column in [
    "Duration_hr",
    "Cost_USD"
]:

    df_npt[column] = pd.to_numeric(
        df_npt[column],
        errors="coerce"
    )


# ======================================================================
# WELL PERFORMANCE
# ======================================================================

well_perf = (
    df_drilling
    .groupby("Well_ID")
    .agg(
        Rig_ID=("Rig_ID", "first"),
        Drilling_Days=("Well_ID", "size"),
        Total_Footage_ft=("Daily_Footage_ft", "sum"),
        Avg_ROP_ft_hr=("ROP_ft_hr", "mean"),
        Total_Drilling_Cost_USD=("Daily_Cost_USD", "sum"),
        Weather_Delay_hr=("Weather_Delay_hr", "sum")
    )
    .reset_index()
)


# ======================================================================
# RIG PERFORMANCE
# ======================================================================

rig_perf = (
    df_drilling
    .groupby("Rig_ID")
    .agg(
        Wells_Drilled=("Well_ID", "nunique"),
        Drilling_Days=("Well_ID", "size"),
        Total_Footage_ft=("Daily_Footage_ft", "sum"),
        Avg_ROP_ft_hr=("ROP_ft_hr", "mean"),
        Total_Drilling_Cost_USD=("Daily_Cost_USD", "sum"),
        Weather_Delay_hr=("Weather_Delay_hr", "sum")
    )
    .reset_index()
)


# ======================================================================
# ROOT CAUSE IMPACT
# ======================================================================

root_cause = (
    df_npt
    .groupby("NPT_Category")
    .agg(
        NPT_Events=("NPT_Category", "size"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Avg_NPT_Duration_hr=("Duration_hr", "mean")
    )
    .reset_index()
)


# ======================================================================
# ROOT CAUSE SEVERITY
# ======================================================================

if "Severity" in df_npt.columns:

    severity_map = {
        "Low": 1,
        "Medium": 2,
        "High": 3
    }

    df_npt["Severity_Score"] = (
        df_npt["Severity"]
        .map(severity_map)
        .fillna(1)
    )

else:

    df_npt["Severity_Score"] = 1


severity = (
    df_npt
    .groupby("NPT_Category")
    .agg(
        Avg_Severity_Score=("Severity_Score", "mean")
    )
    .reset_index()
)


root_cause = root_cause.merge(
    severity,
    on="NPT_Category",
    how="left"
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
# ROOT CAUSE NORMALIZED IMPACT
# ======================================================================

root_cause["Cost_Impact_Score"] = min_max(
    root_cause["NPT_Cost_USD"]
)

root_cause["NPT_Impact_Score"] = min_max(
    root_cause["NPT_Hours"]
)

root_cause["Frequency_Score"] = min_max(
    root_cause["NPT_Events"]
)

root_cause["Severity_Score"] = min_max(
    root_cause["Avg_Severity_Score"]
)


# ======================================================================
# ROOT CAUSE OPPORTUNITY SCORE
# ======================================================================

root_cause["Opportunity_Score"] = (
      root_cause["Cost_Impact_Score"] * 0.35
    + root_cause["NPT_Impact_Score"] * 0.25
    + root_cause["Frequency_Score"] * 0.20
    + root_cause["Severity_Score"] * 0.20
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


root_cause["Priority"] = (
    root_cause["Opportunity_Score"]
    .apply(priority_class)
)


root_cause = root_cause.sort_values(
    "Opportunity_Score",
    ascending=False
).reset_index(drop=True)


root_cause["Priority_Rank"] = (
    root_cause.index + 1
)


# ======================================================================
# PARETO ANALYSIS
# ======================================================================

root_cause["Cumulative_Cost_USD"] = (
    root_cause["NPT_Cost_USD"]
    .cumsum()
)

total_cost = root_cause["NPT_Cost_USD"].sum()

if total_cost > 0:

    root_cause["Cumulative_Cost_Pct"] = (
        root_cause["Cumulative_Cost_USD"]
        / total_cost
        * 100
    )

else:

    root_cause["Cumulative_Cost_Pct"] = 0


root_cause["Pareto_Flag"] = np.where(
    root_cause["Cumulative_Cost_Pct"] <= 80,
    "TOP_80_PERCENT",
    "REMAINDER"
)


# ======================================================================
# WELL NPT IMPACT
# ======================================================================

well_npt = (
    df_npt
    .groupby("Well_ID")
    .agg(
        NPT_Events=("NPT_Category", "size"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum")
    )
    .reset_index()
)


# ======================================================================
# WELL OPPORTUNITY
# ======================================================================

well_opportunity = well_perf.merge(
    well_npt,
    on="Well_ID",
    how="left"
)


well_opportunity[
    [
        "NPT_Events",
        "NPT_Hours",
        "NPT_Cost_USD"
    ]
] = well_opportunity[
    [
        "NPT_Events",
        "NPT_Hours",
        "NPT_Cost_USD"
    ]
].fillna(0)


# ======================================================================
# WELL PERFORMANCE GAP
# ======================================================================

benchmark_rop = well_opportunity[
    "Avg_ROP_ft_hr"
].median()


well_opportunity["ROP_Benchmark_ft_hr"] = (
    benchmark_rop
)

well_opportunity["ROP_Gap_ft_hr"] = (
    benchmark_rop
    - well_opportunity["Avg_ROP_ft_hr"]
)

well_opportunity["ROP_Gap_ft_hr"] = (
    well_opportunity["ROP_Gap_ft_hr"]
    .clip(lower=0)
)


well_opportunity["Cost_Impact_Score"] = min_max(
    well_opportunity["NPT_Cost_USD"]
)

well_opportunity["NPT_Impact_Score"] = min_max(
    well_opportunity["NPT_Hours"]
)

well_opportunity["Performance_Gap_Score"] = min_max(
    well_opportunity["ROP_Gap_ft_hr"]
)


well_opportunity["Frequency_Score"] = min_max(
    well_opportunity["NPT_Events"]
)


# ======================================================================
# WELL OPPORTUNITY SCORE
# ======================================================================

well_opportunity["Opportunity_Score"] = (
      well_opportunity["Cost_Impact_Score"] * 0.35
    + well_opportunity["NPT_Impact_Score"] * 0.25
    + well_opportunity["Performance_Gap_Score"] * 0.20
    + well_opportunity["Frequency_Score"] * 0.20
)


well_opportunity["Priority"] = (
    well_opportunity["Opportunity_Score"]
    .apply(priority_class)
)


well_opportunity = well_opportunity.sort_values(
    "Opportunity_Score",
    ascending=False
).reset_index(drop=True)


well_opportunity["Priority_Rank"] = (
    well_opportunity.index + 1
)


# ======================================================================
# RIG NPT IMPACT
# ======================================================================

rig_npt = (
    df_npt
    .groupby("Rig_ID")
    .agg(
        NPT_Events=("NPT_Category", "size"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum")
    )
    .reset_index()
)


rig_opportunity = rig_perf.merge(
    rig_npt,
    on="Rig_ID",
    how="left"
)


rig_opportunity[
    [
        "NPT_Events",
        "NPT_Hours",
        "NPT_Cost_USD"
    ]
] = rig_opportunity[
    [
        "NPT_Events",
        "NPT_Hours",
        "NPT_Cost_USD"
    ]
].fillna(0)


# ======================================================================
# RIG BENCHMARK
# ======================================================================

rig_benchmark_rop = rig_opportunity[
    "Avg_ROP_ft_hr"
].median()


rig_opportunity["ROP_Benchmark_ft_hr"] = (
    rig_benchmark_rop
)

rig_opportunity["ROP_Gap_ft_hr"] = (
    rig_benchmark_rop
    - rig_opportunity["Avg_ROP_ft_hr"]
)

rig_opportunity["ROP_Gap_ft_hr"] = (
    rig_opportunity["ROP_Gap_ft_hr"]
    .clip(lower=0)
)


rig_opportunity["Cost_Impact_Score"] = min_max(
    rig_opportunity["NPT_Cost_USD"]
)

rig_opportunity["NPT_Impact_Score"] = min_max(
    rig_opportunity["NPT_Hours"]
)

rig_opportunity["Performance_Gap_Score"] = min_max(
    rig_opportunity["ROP_Gap_ft_hr"]
)

rig_opportunity["Frequency_Score"] = min_max(
    rig_opportunity["NPT_Events"]
)


# ======================================================================
# RIG OPPORTUNITY SCORE
# ======================================================================

rig_opportunity["Opportunity_Score"] = (
      rig_opportunity["Cost_Impact_Score"] * 0.35
    + rig_opportunity["NPT_Impact_Score"] * 0.25
    + rig_opportunity["Performance_Gap_Score"] * 0.20
    + rig_opportunity["Frequency_Score"] * 0.20
)


rig_opportunity["Priority"] = (
    rig_opportunity["Opportunity_Score"]
    .apply(priority_class)
)


rig_opportunity = rig_opportunity.sort_values(
    "Opportunity_Score",
    ascending=False
).reset_index(drop=True)


rig_opportunity["Priority_Rank"] = (
    rig_opportunity.index + 1
)


# ======================================================================
# TOP OPPORTUNITIES
# ======================================================================

top_root_causes = root_cause.head(10)

top_wells = well_opportunity.head(10)

top_rigs = rig_opportunity.head(10)


# ======================================================================
# EXECUTIVE SUMMARY
# ======================================================================

total_npt_hours = df_npt["Duration_hr"].sum()

total_npt_cost = df_npt["Cost_USD"].sum()

total_npt_events = len(df_npt)

total_drilling_cost = (
    df_drilling["Daily_Cost_USD"].sum()
    if "Daily_Cost_USD" in df_drilling.columns
    else 0
)


summary = pd.DataFrame(
    {
        "Metric": [
            "Total Wells",
            "Total Rigs",
            "Drilling Records",
            "NPT Events",
            "NPT Hours",
            "NPT Cost USD",
            "Total Drilling Cost USD",
            "Median Well ROP ft/hr",
            "Median Rig ROP ft/hr",
            "Top Root Cause",
            "Top Root Cause Score",
            "Top Well Opportunity",
            "Top Well Score",
            "Top Rig Opportunity",
            "Top Rig Score"
        ],

        "Value": [
            df_drilling["Well_ID"].nunique(),
            df_drilling["Rig_ID"].nunique(),
            len(df_drilling),
            total_npt_events,
            total_npt_hours,
            total_npt_cost,
            total_drilling_cost,
            well_perf["Avg_ROP_ft_hr"].median(),
            rig_perf["Avg_ROP_ft_hr"].median(),
            root_cause.iloc[0]["NPT_Category"]
                if len(root_cause) > 0 else None,
            root_cause.iloc[0]["Opportunity_Score"]
                if len(root_cause) > 0 else None,
            well_opportunity.iloc[0]["Well_ID"]
                if len(well_opportunity) > 0 else None,
            well_opportunity.iloc[0]["Opportunity_Score"]
                if len(well_opportunity) > 0 else None,
            rig_opportunity.iloc[0]["Rig_ID"]
                if len(rig_opportunity) > 0 else None,
            rig_opportunity.iloc[0]["Opportunity_Score"]
                if len(rig_opportunity) > 0 else None
        ]
    }
)


# ======================================================================
# WRITE EXCEL OUTPUT
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

    root_cause.to_excel(
        writer,
        sheet_name="Root_Cause_Impact",
        index=False
    )

    well_opportunity.to_excel(
        writer,
        sheet_name="Well_Opportunity",
        index=False
    )

    rig_opportunity.to_excel(
        writer,
        sheet_name="Rig_Opportunity",
        index=False
    )

    top_root_causes.to_excel(
        writer,
        sheet_name="Top_Root_Causes",
        index=False
    )

    top_wells.to_excel(
        writer,
        sheet_name="Top_Wells",
        index=False
    )

    top_rigs.to_excel(
        writer,
        sheet_name="Top_Rigs",
        index=False
    )

    root_cause[
        [
            "NPT_Category",
            "NPT_Cost_USD",
            "Cumulative_Cost_USD",
            "Cumulative_Cost_Pct",
            "Pareto_Flag"
        ]
    ].to_excel(
        writer,
        sheet_name="Pareto_Root_Cause",
        index=False
    )


# ======================================================================
# CLOSE DATABASE
# ======================================================================

conn.close()


# ======================================================================
# FINAL CONSOLE OUTPUT
# ======================================================================

print("\n" + "=" * 80)
print("STAGE 2G.9 COMPLETED SUCCESSFULLY")
print("=" * 80)

print(f"\nOutput file:")
print(OUTPUT_FILE)

print("\nTop Root Causes:")
print(
    top_root_causes[
        [
            "Priority_Rank",
            "NPT_Category",
            "NPT_Events",
            "NPT_Hours",
            "NPT_Cost_USD",
            "Opportunity_Score",
            "Priority"
        ]
    ].to_string(index=False)
)

print("\nTop Wells:")
print(
    top_wells[
        [
            "Priority_Rank",
            "Well_ID",
            "Rig_ID",
            "NPT_Hours",
            "NPT_Cost_USD",
            "ROP_Gap_ft_hr",
            "Opportunity_Score",
            "Priority"
        ]
    ].to_string(index=False)
)

print("\nTop Rigs:")
print(
    top_rigs[
        [
            "Priority_Rank",
            "Rig_ID",
            "Wells_Drilled",
            "NPT_Hours",
            "NPT_Cost_USD",
            "ROP_Gap_ft_hr",
            "Opportunity_Score",
            "Priority"
        ]
    ].to_string(index=False)
)

print("\n" + "=" * 80)
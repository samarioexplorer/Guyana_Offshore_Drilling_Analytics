# ================================================================
# STAGE 2G.8.2
# RIG & WELL PERFORMANCE BENCHMARKING
# ================================================================
#
# Purpose:
#   Benchmark drilling rigs and wells using exposure-normalized
#   drilling and NPT performance metrics.
#
# Benchmark methodology:
#   P50 / median of peer population.
#
# Lower is better for NPT and lost-time metrics.
#
# Main outputs:
#   - Rig Benchmark
#   - Well Benchmark
#   - Rig Opportunity
#   - Well Opportunity
#   - Rig Pareto
#   - Well Pareto
#   - Executive Summary
#   - Data Quality
#
# Input:
#   database/guyana_drilling.db
#
# Output:
#   outputs/sql_stage_2G.8.2_Rig_Well_Performance_Benchmarking.xlsx
# ================================================================

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np


# ================================================================
# 1. PATHS
# ================================================================

PROJECT_ROOT = Path(
    r"C:\Users\aniba\Documents\Guyana_Offshore_Drilling_Analytics"
)

DB_PATH = (
    PROJECT_ROOT
    / "database"
    / "guyana_drilling.db"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.8.2_Rig_Well_Performance_Benchmarking.xlsx"
)

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ================================================================
# 2. HEADER
# ================================================================

print("=" * 80)
print("STAGE 2G.8.2 — RIG & WELL PERFORMANCE BENCHMARKING")
print("=" * 80)

print(f"Project root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_PATH}")


# ================================================================
# 3. DATABASE
# ================================================================

if not DB_PATH.exists():
    raise FileNotFoundError(
        f"Database not found:\n{DB_PATH}"
    )

conn = sqlite3.connect(DB_PATH)

daily = pd.read_sql_query(
    "SELECT * FROM Fact_Drilling_Daily_Report",
    conn
)

npt = pd.read_sql_query(
    "SELECT * FROM Fact_NPT",
    conn
)

dim_well = pd.read_sql_query(
    "SELECT * FROM Dim_Well",
    conn
)

dim_rig = pd.read_sql_query(
    "SELECT * FROM Dim_Rig",
    conn
)

conn.close()


# ================================================================
# 4. VALIDATION
# ================================================================

print("\nInput records:")
print(f"  Drilling records : {len(daily):,}")
print(f"  NPT records      : {len(npt):,}")
print(f"  Wells            : {daily['Well_ID'].nunique():,}")
print(f"  Rigs             : {daily['Rig_ID'].nunique():,}")


required_daily = [
    "Date",
    "Well_ID",
    "Rig_ID",
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Drilling_Hours",
    "Daily_Cost_USD",
]

required_npt = [
    "Date",
    "Well_ID",
    "Rig_ID",
    "Duration_hr",
    "Cost_USD",
    "Lost_Drilling_Days",
]


for col in required_daily:
    if col not in daily.columns:
        raise ValueError(
            f"Missing drilling column: {col}"
        )

for col in required_npt:
    if col not in npt.columns:
        raise ValueError(
            f"Missing NPT column: {col}"
        )


# ================================================================
# 5. DATA TYPES
# ================================================================

daily["Date"] = pd.to_datetime(
    daily["Date"],
    errors="coerce"
)

npt["Date"] = pd.to_datetime(
    npt["Date"],
    errors="coerce"
)


daily_numeric = [
    "Daily_Footage_ft",
    "ROP_ft_hr",
    "Drilling_Hours",
    "Daily_Cost_USD",
]

npt_numeric = [
    "Duration_hr",
    "Cost_USD",
    "Lost_Drilling_Days",
]

for col in daily_numeric:
    daily[col] = pd.to_numeric(
        daily[col],
        errors="coerce"
    ).fillna(0)

for col in npt_numeric:
    npt[col] = pd.to_numeric(
        npt[col],
        errors="coerce"
    ).fillna(0)


# ================================================================
# 6. REMOVE INVALID KEYS
# ================================================================

daily = daily[
    daily["Date"].notna()
    & daily["Well_ID"].notna()
    & daily["Rig_ID"].notna()
].copy()

npt = npt[
    npt["Date"].notna()
    & npt["Well_ID"].notna()
    & npt["Rig_ID"].notna()
].copy()


# ================================================================
# 7. TRUE EXPOSURE KEYS
# ================================================================

daily["Well_Day_Key"] = (
    daily["Well_ID"].astype(str)
    + "|"
    + daily["Date"].dt.strftime("%Y-%m-%d")
)

daily["Rig_Day_Key"] = (
    daily["Rig_ID"].astype(str)
    + "|"
    + daily["Date"].dt.strftime("%Y-%m-%d")
)


# ================================================================
# 8. WELL-DAY EXPOSURE
# ================================================================

well_exposure = (
    daily.groupby("Well_ID")
    .agg(
        Rig_ID=("Rig_ID", "first"),
        Drilling_Days=("Date", "nunique"),
        Well_Days=("Well_Day_Key", "nunique"),
        Footage_ft=("Daily_Footage_ft", "sum"),
        Drilling_Hours=("Drilling_Hours", "sum"),
        Drilling_Cost_USD=("Daily_Cost_USD", "sum"),
        Avg_ROP_ft_hr=("ROP_ft_hr", "mean"),
    )
    .reset_index()
)


# ================================================================
# 9. WELL NPT
# ================================================================

well_npt = (
    npt.groupby("Well_ID")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Lost_Drilling_Days=("Lost_Drilling_Days", "sum"),
    )
    .reset_index()
)


# ================================================================
# 10. WELL PERFORMANCE DATASET
# ================================================================

well = well_exposure.merge(
    well_npt,
    on="Well_ID",
    how="left"
)

for col in [
    "NPT_Events",
    "NPT_Hours",
    "NPT_Cost_USD",
    "Lost_Drilling_Days",
]:

    well[col] = well[col].fillna(0)


# ================================================================
# 11. WELL NORMALIZED METRICS
# ================================================================

well["NPT_Hours_per_Well_Day"] = (
    well["NPT_Hours"]
    / well["Well_Days"].replace(0, np.nan)
)

well["NPT_Cost_per_Well_Day_USD"] = (
    well["NPT_Cost_USD"]
    / well["Well_Days"].replace(0, np.nan)
)

well["NPT_Events_per_100_Well_Days"] = (
    well["NPT_Events"]
    / well["Well_Days"].replace(0, np.nan)
    * 100
)

well["NPT_Hours_per_1000_ft"] = (
    well["NPT_Hours"]
    / well["Footage_ft"].replace(0, np.nan)
    * 1000
)

well["NPT_Cost_per_ft_USD"] = (
    well["NPT_Cost_USD"]
    / well["Footage_ft"].replace(0, np.nan)
)

well["Lost_Days_per_Well_Day"] = (
    well["Lost_Drilling_Days"]
    / well["Well_Days"].replace(0, np.nan)
)

well["NPT_Cost_pct_of_Drilling_Cost"] = (
    well["NPT_Cost_USD"]
    / well["Drilling_Cost_USD"].replace(0, np.nan)
    * 100
)


# ================================================================
# 12. RIG EXPOSURE
# ================================================================

rig_exposure = (
    daily.groupby("Rig_ID")
    .agg(
        Wells=("Well_ID", "nunique"),
        Drilling_Days=("Date", "nunique"),
        Rig_Days=("Rig_Day_Key", "nunique"),
        Well_Days=("Well_Day_Key", "nunique"),
        Footage_ft=("Daily_Footage_ft", "sum"),
        Drilling_Hours=("Drilling_Hours", "sum"),
        Drilling_Cost_USD=("Daily_Cost_USD", "sum"),
        Avg_ROP_ft_hr=("ROP_ft_hr", "mean"),
    )
    .reset_index()
)


# ================================================================
# 13. RIG NPT
# ================================================================

rig_npt = (
    npt.groupby("Rig_ID")
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        NPT_Cost_USD=("Cost_USD", "sum"),
        Lost_Drilling_Days=("Lost_Drilling_Days", "sum"),
    )
    .reset_index()
)


# ================================================================
# 14. RIG PERFORMANCE DATASET
# ================================================================

rig = rig_exposure.merge(
    rig_npt,
    on="Rig_ID",
    how="left"
)

for col in [
    "NPT_Events",
    "NPT_Hours",
    "NPT_Cost_USD",
    "Lost_Drilling_Days",
]:

    rig[col] = rig[col].fillna(0)


# ================================================================
# 15. RIG NORMALIZED METRICS
# ================================================================

rig["NPT_Hours_per_Rig_Day"] = (
    rig["NPT_Hours"]
    / rig["Rig_Days"].replace(0, np.nan)
)

rig["NPT_Cost_per_Rig_Day_USD"] = (
    rig["NPT_Cost_USD"]
    / rig["Rig_Days"].replace(0, np.nan)
)

rig["NPT_Events_per_100_Rig_Days"] = (
    rig["NPT_Events"]
    / rig["Rig_Days"].replace(0, np.nan)
    * 100
)

rig["NPT_Hours_per_1000_ft"] = (
    rig["NPT_Hours"]
    / rig["Footage_ft"].replace(0, np.nan)
    * 1000
)

rig["NPT_Cost_per_ft_USD"] = (
    rig["NPT_Cost_USD"]
    / rig["Footage_ft"].replace(0, np.nan)
)

rig["Lost_Days_per_Rig_Day"] = (
    rig["Lost_Drilling_Days"]
    / rig["Rig_Days"].replace(0, np.nan)
)

rig["NPT_Cost_pct_of_Drilling_Cost"] = (
    rig["NPT_Cost_USD"]
    / rig["Drilling_Cost_USD"].replace(0, np.nan)
    * 100
)


# ================================================================
# 16. BENCHMARK FUNCTION
# ================================================================

def calculate_benchmark(
    df,
    metrics
):

    benchmark = {}

    for metric in metrics:

        benchmark[metric] = df[metric].median()

    return benchmark


# ================================================================
# 17. RIG BENCHMARK
# ================================================================

rig_metrics = [
    "NPT_Hours_per_Rig_Day",
    "NPT_Cost_per_Rig_Day_USD",
    "NPT_Hours_per_1000_ft",
    "NPT_Cost_per_ft_USD",
    "Lost_Days_per_Rig_Day",
]


rig_benchmark_values = calculate_benchmark(
    rig,
    rig_metrics
)


print("\n" + "=" * 80)
print("RIG BENCHMARK — P50")
print("=" * 80)

for metric, value in rig_benchmark_values.items():

    print(
        f"{metric:<40} : {value:,.4f}"
    )


# ================================================================
# 18. RIG BENCHMARK GAPS
# ================================================================

for metric in rig_metrics:

    benchmark_value = rig_benchmark_values[metric]

    rig[metric + "_Benchmark"] = benchmark_value

    rig[metric + "_Gap"] = (
        rig[metric]
        - benchmark_value
    )

    rig[metric + "_Gap_pct"] = (
        (
            rig[metric]
            - benchmark_value
        )
        / benchmark_value
        * 100
        if benchmark_value != 0
        else 0
    )


# ================================================================
# 19. RIG EFFICIENCY INDICES
# ================================================================
#
# Index interpretation:
#
#   100 = benchmark
#   >100 = better than benchmark
#   <100 = worse than benchmark
#
# Because lower NPT is better:
#
#   Index = Benchmark / Actual * 100
#
# ================================================================

for metric in rig_metrics:

    benchmark_value = rig_benchmark_values[metric]

    index_name = (
        metric
        + "_Efficiency_Index"
    )

    rig[index_name] = np.where(
        rig[metric] > 0,
        benchmark_value
        / rig[metric]
        * 100,
        100
    )


rig["Rig_NPT_Intensity_Index"] = (
    rig["NPT_Hours_per_Rig_Day_Efficiency_Index"]
    + rig["NPT_Hours_per_1000_ft_Efficiency_Index"]
) / 2


rig["Rig_Cost_Efficiency_Index"] = (
    rig["NPT_Cost_per_Rig_Day_USD_Efficiency_Index"]
    + rig["NPT_Cost_per_ft_USD_Efficiency_Index"]
) / 2


rig["Rig_Reliability_Index"] = (
    rig["Lost_Days_per_Rig_Day_Efficiency_Index"]
)


rig["Composite_Rig_Performance_Index"] = (
    rig["Rig_NPT_Intensity_Index"] * 0.35
    + rig["Rig_Cost_Efficiency_Index"] * 0.35
    + rig["Rig_Reliability_Index"] * 0.30
)


# ================================================================
# 20. RIG QUARTILES
# ================================================================

rig["Performance_Quartile"] = (
    pd.qcut(
        rig["Composite_Rig_Performance_Index"],
        q=4,
        labels=[
            "Q1 - Lowest",
            "Q2",
            "Q3",
            "Q4 - Highest",
        ],
        duplicates="drop"
    )
)


def classify_rig(index):

    if index >= 110:
        return "Excellent"

    elif index >= 100:
        return "Above Benchmark"

    elif index >= 90:
        return "Watch"

    else:
        return "Below Benchmark"


rig["Performance_Class"] = (
    rig["Composite_Rig_Performance_Index"]
    .apply(classify_rig)
)


# ================================================================
# 21. RIG OPPORTUNITY
# ================================================================
#
# Opportunity exists only when actual performance is worse
# than benchmark.
#
# Potential reduction:
#
#   (Actual rate - Benchmark rate) * exposure
#
# ================================================================

rig["Potential_NPT_Hours_Reduction"] = np.maximum(
    rig["NPT_Hours_per_Rig_Day"]
    - rig_benchmark_values["NPT_Hours_per_Rig_Day"],
    0
) * rig["Rig_Days"]


rig["Potential_NPT_Cost_Reduction_USD"] = np.maximum(
    rig["NPT_Cost_per_Rig_Day_USD"]
    - rig_benchmark_values["NPT_Cost_per_Rig_Day_USD"],
    0
) * rig["Rig_Days"]


rig["Potential_NPT_Hours_Reduction_from_Footage"] = np.maximum(
    rig["NPT_Hours_per_1000_ft"]
    - rig_benchmark_values["NPT_Hours_per_1000_ft"],
    0
) * rig["Footage_ft"] / 1000


rig["Potential_NPT_Cost_Reduction_from_Footage_USD"] = np.maximum(
    rig["NPT_Cost_per_ft_USD"]
    - rig_benchmark_values["NPT_Cost_per_ft_USD"],
    0
) * rig["Footage_ft"]


rig["Primary_Opportunity_USD"] = np.minimum(
    rig["Potential_NPT_Cost_Reduction_USD"],
    rig["NPT_Cost_USD"]
)


# ================================================================
# 22. WELL BENCHMARK
# ================================================================

well_metrics = [
    "NPT_Hours_per_Well_Day",
    "NPT_Cost_per_Well_Day_USD",
    "NPT_Hours_per_1000_ft",
    "NPT_Cost_per_ft_USD",
    "Lost_Days_per_Well_Day",
]


well_benchmark_values = calculate_benchmark(
    well,
    well_metrics
)


print("\n" + "=" * 80)
print("WELL BENCHMARK — P50")
print("=" * 80)

for metric, value in well_benchmark_values.items():

    print(
        f"{metric:<40} : {value:,.4f}"
    )


# ================================================================
# 23. WELL BENCHMARK GAPS
# ================================================================

for metric in well_metrics:

    benchmark_value = well_benchmark_values[metric]

    well[metric + "_Benchmark"] = benchmark_value

    well[metric + "_Gap"] = (
        well[metric]
        - benchmark_value
    )

    well[metric + "_Gap_pct"] = (
        (
            well[metric]
            - benchmark_value
        )
        / benchmark_value
        * 100
        if benchmark_value != 0
        else 0
    )


# ================================================================
# 24. WELL EFFICIENCY INDICES
# ================================================================

for metric in well_metrics:

    benchmark_value = well_benchmark_values[metric]

    index_name = (
        metric
        + "_Efficiency_Index"
    )

    well[index_name] = np.where(
        well[metric] > 0,
        benchmark_value
        / well[metric]
        * 100,
        100
    )


well["Well_NPT_Intensity_Index"] = (
    well["NPT_Hours_per_Well_Day_Efficiency_Index"]
    + well["NPT_Hours_per_1000_ft_Efficiency_Index"]
) / 2


well["Well_Cost_Efficiency_Index"] = (
    well["NPT_Cost_per_Well_Day_USD_Efficiency_Index"]
    + well["NPT_Cost_per_ft_USD_Efficiency_Index"]
) / 2


well["Well_Reliability_Index"] = (
    well["Lost_Days_per_Well_Day_Efficiency_Index"]
)


well["Composite_Well_Performance_Index"] = (
    well["Well_NPT_Intensity_Index"] * 0.35
    + well["Well_Cost_Efficiency_Index"] * 0.35
    + well["Well_Reliability_Index"] * 0.30
)


# ================================================================
# 25. WELL QUARTILES
# ================================================================

well["Performance_Quartile"] = (
    pd.qcut(
        well["Composite_Well_Performance_Index"],
        q=4,
        labels=[
            "Q1 - Lowest",
            "Q2",
            "Q3",
            "Q4 - Highest",
        ],
        duplicates="drop"
    )
)


def classify_well(index):

    if index >= 110:
        return "Excellent"

    elif index >= 100:
        return "Above Benchmark"

    elif index >= 90:
        return "Watch"

    else:
        return "Below Benchmark"


well["Performance_Class"] = (
    well["Composite_Well_Performance_Index"]
    .apply(classify_well)
)


# ================================================================
# 26. WELL OPPORTUNITY
# ================================================================

well["Potential_NPT_Hours_Reduction"] = np.maximum(
    well["NPT_Hours_per_Well_Day"]
    - well_benchmark_values["NPT_Hours_per_Well_Day"],
    0
) * well["Well_Days"]


well["Potential_NPT_Cost_Reduction_USD"] = np.maximum(
    well["NPT_Cost_per_Well_Day_USD"]
    - well_benchmark_values["NPT_Cost_per_Well_Day_USD"],
    0
) * well["Well_Days"]


well["Potential_NPT_Hours_Reduction_from_Footage"] = np.maximum(
    well["NPT_Hours_per_1000_ft"]
    - well_benchmark_values["NPT_Hours_per_1000_ft"],
    0
) * well["Footage_ft"] / 1000


well["Potential_NPT_Cost_Reduction_from_Footage_USD"] = np.maximum(
    well["NPT_Cost_per_ft_USD"]
    - well_benchmark_values["NPT_Cost_per_ft_USD"],
    0
) * well["Footage_ft"]


well["Primary_Opportunity_USD"] = np.minimum(
    well["Potential_NPT_Cost_Reduction_USD"],
    well["NPT_Cost_USD"]
)


# ================================================================
# 27. RIG OPPORTUNITY RANKING
# ================================================================

rig_opportunity = rig[
    [
        "Rig_ID",
        "Wells",
        "Rig_Days",
        "Well_Days",
        "Footage_ft",
        "NPT_Events",
        "NPT_Hours",
        "NPT_Cost_USD",
        "Composite_Rig_Performance_Index",
        "Performance_Class",
        "Potential_NPT_Hours_Reduction",
        "Potential_NPT_Cost_Reduction_USD",
        "Primary_Opportunity_USD",
    ]
].copy()


rig_opportunity = rig_opportunity.sort_values(
    "Primary_Opportunity_USD",
    ascending=False
).reset_index(drop=True)


# ================================================================
# 28. WELL OPPORTUNITY RANKING
# ================================================================

well_opportunity = well[
    [
        "Well_ID",
        "Rig_ID",
        "Drilling_Days",
        "Well_Days",
        "Footage_ft",
        "NPT_Events",
        "NPT_Hours",
        "NPT_Cost_USD",
        "Composite_Well_Performance_Index",
        "Performance_Class",
        "Potential_NPT_Hours_Reduction",
        "Potential_NPT_Cost_Reduction_USD",
        "Primary_Opportunity_USD",
    ]
].copy()


well_opportunity = well_opportunity.sort_values(
    "Primary_Opportunity_USD",
    ascending=False
).reset_index(drop=True)


# ================================================================
# 29. RIG PARETO
# ================================================================

rig_pareto = rig_opportunity.copy()

rig_pareto["Cumulative_Opportunity_USD"] = (
    rig_pareto["Primary_Opportunity_USD"]
    .cumsum()
)

total_rig_opportunity = (
    rig_pareto["Primary_Opportunity_USD"].sum()
)

rig_pareto["Cumulative_Opportunity_pct"] = (
    rig_pareto["Cumulative_Opportunity_USD"]
    / total_rig_opportunity
    * 100
    if total_rig_opportunity > 0
    else 0
)


# ================================================================
# 30. WELL PARETO
# ================================================================

well_pareto = well_opportunity.copy()

well_pareto["Cumulative_Opportunity_USD"] = (
    well_pareto["Primary_Opportunity_USD"]
    .cumsum()
)

total_well_opportunity = (
    well_pareto["Primary_Opportunity_USD"].sum()
)

well_pareto["Cumulative_Opportunity_pct"] = (
    well_pareto["Cumulative_Opportunity_USD"]
    / total_well_opportunity
    * 100
    if total_well_opportunity > 0
    else 0
)


# ================================================================
# 31. TOP OPPORTUNITIES
# ================================================================

top_rig_opportunities = rig_opportunity.head(10).copy()

top_well_opportunities = well_opportunity.head(25).copy()


# ================================================================
# 32. BENCHMARK SUMMARY
# ================================================================

benchmark_summary = pd.DataFrame(
    {
        "Level": (
            ["Rig"] * len(rig_metrics)
            + ["Well"] * len(well_metrics)
        ),
        "Metric": (
            rig_metrics
            + well_metrics
        ),
        "Benchmark_P50": (
            list(rig_benchmark_values.values())
            + list(well_benchmark_values.values())
        ),
        "Direction": [
            "Lower is better"
        ] * (
            len(rig_metrics)
            + len(well_metrics)
        ),
    }
)


# ================================================================
# 33. EXECUTIVE SUMMARY
# ================================================================

best_rig_row = rig.sort_values(
    "Composite_Rig_Performance_Index",
    ascending=False
).iloc[0]

worst_rig_row = rig.sort_values(
    "Composite_Rig_Performance_Index",
    ascending=True
).iloc[0]

best_well_row = well.sort_values(
    "Composite_Well_Performance_Index",
    ascending=False
).iloc[0]

worst_well_row = well.sort_values(
    "Composite_Well_Performance_Index",
    ascending=True
).iloc[0]


executive_summary = pd.DataFrame(
    {
        "Metric": [
            "Number of Rigs",
            "Number of Wells",
            "Total Rig-Days",
            "Total Well-Days",
            "Total Footage (ft)",
            "Total NPT Hours",
            "Total NPT Cost (USD)",
            "Rig Benchmark Method",
            "Well Benchmark Method",
            "Best Rig",
            "Best Rig Performance Index",
            "Worst Rig",
            "Worst Rig Performance Index",
            "Best Well",
            "Best Well Performance Index",
            "Worst Well",
            "Worst Well Performance Index",
            "Total Rig Opportunity (USD)",
            "Total Well Opportunity (USD)",
        ],
        "Value": [
            len(rig),
            len(well),
            rig["Rig_Days"].sum(),
            well["Well_Days"].sum(),
            daily["Daily_Footage_ft"].sum(),
            npt["Duration_hr"].sum(),
            npt["Cost_USD"].sum(),
            "Median / P50",
            "Median / P50",
            best_rig_row["Rig_ID"],
            best_rig_row["Composite_Rig_Performance_Index"],
            worst_rig_row["Rig_ID"],
            worst_rig_row["Composite_Rig_Performance_Index"],
            best_well_row["Well_ID"],
            best_well_row["Composite_Well_Performance_Index"],
            worst_well_row["Well_ID"],
            worst_well_row["Composite_Well_Performance_Index"],
            total_rig_opportunity,
            total_well_opportunity,
        ],
    }
)


# ================================================================
# 34. DATA QUALITY
# ================================================================

data_quality = pd.DataFrame(
    {
        "Check": [
            "Daily drilling records",
            "NPT records",
            "Unique wells",
            "Unique rigs",
            "Unique well-days",
            "Unique rig-days",
            "Duplicate well-day records",
            "Negative footage",
            "Negative drilling hours",
            "Negative NPT duration",
            "Negative NPT cost",
            "Missing drilling dates",
            "Missing NPT dates",
        ],
        "Value": [
            len(daily),
            len(npt),
            daily["Well_ID"].nunique(),
            daily["Rig_ID"].nunique(),
            daily["Well_Day_Key"].nunique(),
            daily["Rig_Day_Key"].nunique(),
            len(daily) - daily["Well_Day_Key"].nunique(),
            (daily["Daily_Footage_ft"] < 0).sum(),
            (daily["Drilling_Hours"] < 0).sum(),
            (npt["Duration_hr"] < 0).sum(),
            (npt["Cost_USD"] < 0).sum(),
            daily["Date"].isna().sum(),
            npt["Date"].isna().sum(),
        ],
    }
)


# ================================================================
# 35. PRINT RIG BENCHMARK
# ================================================================

print("\n" + "=" * 80)
print("RIG PERFORMANCE BENCHMARK")
print("=" * 80)

print(
    rig[
        [
            "Rig_ID",
            "Wells",
            "Rig_Days",
            "NPT_Hours",
            "NPT_Cost_USD",
            "NPT_Hours_per_Rig_Day",
            "NPT_Cost_per_Rig_Day_USD",
            "NPT_Cost_per_ft_USD",
            "Composite_Rig_Performance_Index",
            "Performance_Class",
        ]
    ]
    .sort_values(
        "Composite_Rig_Performance_Index",
        ascending=False
    )
    .to_string(index=False)
)


# ================================================================
# 36. PRINT TOP OPPORTUNITIES
# ================================================================

print("\n" + "=" * 80)
print("TOP RIG OPPORTUNITIES")
print("=" * 80)

print(
    top_rig_opportunities[
        [
            "Rig_ID",
            "Primary_Opportunity_USD",
            "Potential_NPT_Hours_Reduction",
            "Composite_Rig_Performance_Index",
            "Performance_Class",
        ]
    ]
    .to_string(index=False)
)


print("\n" + "=" * 80)
print("TOP 10 WELL OPPORTUNITIES")
print("=" * 80)

print(
    top_well_opportunities[
        [
            "Well_ID",
            "Rig_ID",
            "Primary_Opportunity_USD",
            "Potential_NPT_Hours_Reduction",
            "Composite_Well_Performance_Index",
            "Performance_Class",
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# ================================================================
# 37. EXPORT
# ================================================================

print("\nExporting Excel workbook...")

with pd.ExcelWriter(
    OUTPUT_PATH,
    engine="openpyxl"
) as writer:

    executive_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    benchmark_summary.to_excel(
        writer,
        sheet_name="Benchmark_Summary",
        index=False
    )

    rig.to_excel(
        writer,
        sheet_name="Rig_Benchmark",
        index=False
    )

    well.to_excel(
        writer,
        sheet_name="Well_Benchmark",
        index=False
    )

    rig_opportunity.to_excel(
        writer,
        sheet_name="Rig_Opportunity",
        index=False
    )

    well_opportunity.to_excel(
        writer,
        sheet_name="Well_Opportunity",
        index=False
    )

    top_rig_opportunities.to_excel(
        writer,
        sheet_name="Top_Rig_Opportunities",
        index=False
    )

    top_well_opportunities.to_excel(
        writer,
        sheet_name="Top_Well_Opportunities",
        index=False
    )

    rig_pareto.to_excel(
        writer,
        sheet_name="Rig_Pareto",
        index=False
    )

    well_pareto.to_excel(
        writer,
        sheet_name="Well_Pareto",
        index=False
    )

    data_quality.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# ================================================================
# 38. FINAL VALIDATION
# ================================================================

if not OUTPUT_PATH.exists():

    raise RuntimeError(
        "Excel output was not created."
    )


print("\n" + "=" * 80)
print("STAGE 2G.8.2 COMPLETED SUCCESSFULLY")
print("=" * 80)

print(f"Output file:")
print(OUTPUT_PATH)

print("\nSheets created:")

print(
    [
        "Executive_Summary",
        "Benchmark_Summary",
        "Rig_Benchmark",
        "Well_Benchmark",
        "Rig_Opportunity",
        "Well_Opportunity",
        "Top_Rig_Opportunities",
        "Top_Well_Opportunities",
        "Rig_Pareto",
        "Well_Pareto",
        "Data_Quality",
    ]
)

print("\nBenchmark methodology:")
print("  Rig = P50 / Median")
print("  Well = P50 / Median")

print("\nIndex interpretation:")
print("  100 = benchmark")
print("  >100 = better than benchmark")
print("  <100 = worse than benchmark")

print("\nStage 2G.8.2 is ready for validation.")
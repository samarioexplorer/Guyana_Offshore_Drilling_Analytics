from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# STAGE 2E.1
# ENGINEERING SCORE CALIBRATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INTEGRATED_FILE = PROCESSED_DIR / "Integrated_Drilling_Performance.csv"
PERFORMANCE_SCORE_FILE = PROCESSED_DIR / "Well_Performance_Score.csv"

OUTPUT_FILE = PROCESSED_DIR / "Well_Engineering_Score_Calibrated.csv"
SUMMARY_FILE = PROCESSED_DIR / "Engineering_Score_Calibration_Summary.csv"


# ============================================================
# 1. LOAD DATA
# ============================================================

print("=" * 70)
print("STAGE 2E.1 - ENGINEERING SCORE CALIBRATION")
print("=" * 70)

print("\nLoading datasets...")

df_integrated = pd.read_csv(INTEGRATED_FILE)
df_score = pd.read_csv(PERFORMANCE_SCORE_FILE)

print(f"Integrated dataset: {len(df_integrated):,} rows")
print(f"Performance score dataset: {len(df_score):,} rows")


# ============================================================
# 2. SELECT RELEVANT COLUMNS
# ============================================================

required_integrated = [
    "Well_ID",
    "Rig_ID",
    "Average_ROP_ft_hr",
    "Drilling_Days",
    "Total_Footage_ft",
    "Total_Drilling_Hours",
    "Drilling_Cost_USD",
    "Cost_per_Foot_USD",
    "Operational_Cost_USD",
    "Operational_Cost_per_Foot_USD",
    "NPT_Hours",
    "NPT_Hours_pct",
    "NPT_Cost_USD",
    "Deferred_Cost_USD",
    "Total_Economic_Impact_USD",
    "Total_Economic_Impact_per_Foot_USD",
]

required_score = [
    "Well_ID",
    "Overall_Performance_Score",
    "Efficiency_Score",
    "Cost_Score",
    "Reliability_Score",
    "Economic_Impact_Score",
    "Risk_Tier",
    "Performance_Profile",
]


missing_integrated = [
    col for col in required_integrated
    if col not in df_integrated.columns
]

missing_score = [
    col for col in required_score
    if col not in df_score.columns
]

if missing_integrated:
    raise ValueError(
        f"Missing columns in Integrated_Drilling_Performance.csv: "
        f"{missing_integrated}"
    )

if missing_score:
    raise ValueError(
        f"Missing columns in Well_Performance_Score.csv: "
        f"{missing_score}"
    )


df_integrated = df_integrated[required_integrated].copy()
df_score = df_score[required_score].copy()


# ============================================================
# 3. MERGE
# ============================================================

print("\nMerging integrated performance and Stage 2E score...")

df = pd.merge(
    df_integrated,
    df_score,
    on="Well_ID",
    how="inner",
    validate="one_to_one"
)

print(f"Merged wells: {len(df):,}")

# Calculate average daily footage from the integrated dataset
df["Average_Daily_Footage_ft"] = (
    df["Total_Footage_ft"] / df["Drilling_Days"]
)

# Use the actual NPT percentage field from Stage 2D
df["NPT_Percent"] = df["NPT_Hours_pct"]


if len(df) == 0:
    raise ValueError("Merge produced zero rows.")

if df["Well_ID"].duplicated().any():
    raise ValueError("Duplicate Well_ID detected after merge.")


# ============================================================
# 4. RANK / PERCENTILE FUNCTIONS
# ============================================================

def percentile_score(series, higher_is_better=True):
    """
    Convert a metric into a 0-100 percentile score.

    Higher value is better:
        highest value -> approximately 100

    Lower value is better:
        lowest value -> approximately 100
    """

    rank = series.rank(method="average", pct=True)

    if higher_is_better:
        score = rank * 100
    else:
        score = (1 - rank + (1 / len(series))) * 100

    return score


# ============================================================
# 5. ENGINEERING DIMENSION SCORES
# ============================================================

print("\nCalculating calibrated engineering dimensions...")


# ------------------------------------------------------------
# 5.1 DRILLING EFFICIENCY
# ------------------------------------------------------------

df["Calibrated_Efficiency_Score"] = (
    0.50 * percentile_score(
        df["Average_ROP_ft_hr"],
        higher_is_better=True
    )
    +
    0.50 * percentile_score(
        df["Average_Daily_Footage_ft"],
        higher_is_better=True
    )
)


# ------------------------------------------------------------
# 5.2 OPERATIONAL EFFICIENCY
# ------------------------------------------------------------

df["Operational_Efficiency_Score"] = (
    0.70 * percentile_score(
        df["Operational_Cost_per_Foot_USD"],
        higher_is_better=False
    )
    +
    0.30 * percentile_score(
        df["Cost_per_Foot_USD"],
        higher_is_better=False
    )
)


# ------------------------------------------------------------
# 5.3 RELIABILITY
# ------------------------------------------------------------

df["Reliability_Score_Calibrated"] = (
    0.70 * percentile_score(
        df["NPT_Percent"],
        higher_is_better=False
    )
    +
    0.30 * percentile_score(
        df["NPT_Hours"],
        higher_is_better=False
    )
)


# ------------------------------------------------------------
# 5.4 ECONOMIC EXPOSURE
# ------------------------------------------------------------

df["Economic_Exposure_Score"] = (
    0.70 * percentile_score(
        df["Total_Economic_Impact_per_Foot_USD"],
        higher_is_better=False
    )
    +
    0.30 * percentile_score(
        df["Deferred_Cost_USD"],
        higher_is_better=False
    )
)


# ============================================================
# 6. PERFORMANCE SCORE
# ============================================================

df["Engineering_Performance_Score"] = (
    0.60 * df["Calibrated_Efficiency_Score"]
    +
    0.40 * df["Operational_Efficiency_Score"]
)


# ============================================================
# 7. RISK SCORE
# ============================================================

# Higher score = LOWER risk
#
# This is intentionally different from a traditional
# "risk score" where high value means high risk.

df["Engineering_Risk_Resilience_Score"] = (
    0.60 * df["Reliability_Score_Calibrated"]
    +
    0.40 * df["Economic_Exposure_Score"]
)


# ============================================================
# 8. NORMALIZED RISK INDEX
# ============================================================

# Here:
#   Low Risk     = low numerical Risk Index
#   High Risk    = high numerical Risk Index

df["Risk_Index"] = (
    100 - df["Engineering_Risk_Resilience_Score"]
)


# ============================================================
# 9. DATASET BENCHMARKS
# ============================================================

performance_median = df["Engineering_Performance_Score"].median()
risk_median = df["Engineering_Risk_Resilience_Score"].median()


print("\nDataset benchmarks:")
print(
    f"Performance median: "
    f"{performance_median:.2f}"
)

print(
    f"Risk resilience median: "
    f"{risk_median:.2f}"
)


# ============================================================
# 10. PERFORMANCE / RISK QUADRANT
# ============================================================

def classify_quadrant(row):

    high_performance = (
        row["Engineering_Performance_Score"]
        >= performance_median
    )

    high_resilience = (
        row["Engineering_Risk_Resilience_Score"]
        >= risk_median
    )

    if high_performance and high_resilience:
        return "Benchmark"

    elif high_performance and not high_resilience:
        return "Efficient but Exposed"

    elif not high_performance and high_resilience:
        return "Stable but Inefficient"

    else:
        return "Priority Intervention"


df["Performance_Risk_Quadrant"] = df.apply(
    classify_quadrant,
    axis=1
)


# ============================================================
# 11. PERFORMANCE TIER
# ============================================================

def performance_tier(score):

    if score >= 80:
        return "Excellent"

    elif score >= 65:
        return "Good"

    elif score >= 50:
        return "Watch"

    else:
        return "Needs Improvement"


df["Engineering_Performance_Tier"] = (
    df["Engineering_Performance_Score"]
    .apply(performance_tier)
)


# ============================================================
# 12. RISK TIER
# ============================================================

def risk_tier(score):

    # score = resilience score
    # higher = safer / more resilient

    if score >= 80:
        return "Low Risk"

    elif score >= 65:
        return "Moderate Risk"

    elif score >= 50:
        return "Elevated Risk"

    else:
        return "High Risk"


df["Engineering_Risk_Tier"] = (
    df["Engineering_Risk_Resilience_Score"]
    .apply(risk_tier)
)


# ============================================================
# 13. BENCHMARK FLAG
# ============================================================

df["Benchmark_Flag"] = np.where(
    df["Performance_Risk_Quadrant"] == "Benchmark",
    "YES",
    "NO"
)


# ============================================================
# 14. IMPROVEMENT PRIORITY
# ============================================================

def improvement_priority(row):

    quadrant = row["Performance_Risk_Quadrant"]

    if quadrant == "Priority Intervention":
        return "Critical"

    elif quadrant == "Efficient but Exposed":
        return "High"

    elif quadrant == "Stable but Inefficient":
        return "Medium"

    else:
        return "Low"


df["Improvement_Priority"] = df.apply(
    improvement_priority,
    axis=1
)


# ============================================================
# 15. CALIBRATION DIFFERENCE VS ORIGINAL SCORE
# ============================================================

df["Score_Change_vs_Stage2E"] = (
    df["Engineering_Performance_Score"]
    -
    df["Overall_Performance_Score"]
)


# ============================================================
# 16. RANKINGS
# ============================================================

df["Engineering_Performance_Rank"] = (
    df["Engineering_Performance_Score"]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)

df["Engineering_Risk_Resilience_Rank"] = (
    df["Engineering_Risk_Resilience_Score"]
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)

df["Engineering_Overall_Rank"] = (
    (
        0.60 * df["Engineering_Performance_Score"]
        +
        0.40 * df["Engineering_Risk_Resilience_Score"]
    )
    .rank(
        method="min",
        ascending=False
    )
    .astype(int)
)


# ============================================================
# 17. CORRELATION ANALYSIS
# ============================================================

print("\nCalculating score correlations...")

correlation_rows = []

correlation_rows = []

metrics = {
    "ROP": "Average_ROP_ft_hr",
    "Daily_Footage": "Average_Daily_Footage_ft",
    "Cost_per_Foot": "Cost_per_Foot_USD",
    "Operational_Cost_per_Foot":
        "Operational_Cost_per_Foot_USD",
    "NPT_Percent": "NPT_Percent",
    "NPT_Hours": "NPT_Hours",
    "Economic_Impact_per_Foot":
        "Total_Economic_Impact_per_Foot_USD",
}

score_columns = {
    "Stage2E_Overall": "Overall_Performance_Score",
    "Calibrated_Performance":
        "Engineering_Performance_Score",
    "Risk_Resilience":
        "Engineering_Risk_Resilience_Score",
}


def spearman_correlation(x, y):
    """
    Calculate Spearman correlation using pandas ranks.

    This avoids requiring scipy.
    """

    x_rank = x.rank(method="average")
    y_rank = y.rank(method="average")

    return x_rank.corr(y_rank, method="pearson")


for score_name, score_column in score_columns.items():

    for metric_name, metric_column in metrics.items():

        # Pearson correlation
        pearson = df[score_column].corr(
            df[metric_column],
            method="pearson"
        )

        # Spearman correlation calculated from ranks
        spearman = spearman_correlation(
            df[score_column],
            df[metric_column]
        )

        correlation_rows.append({
            "Score": score_name,
            "Metric": metric_name,
            "Pearson_Correlation": pearson,
            "Spearman_Correlation": spearman
        })


df_correlation = pd.DataFrame(correlation_rows)

# ============================================================
# 18. FINAL COLUMN ORDER
# ============================================================

output_columns = [
    "Well_ID",
    "Rig_ID",

    # Core drilling performance
    "Average_ROP_ft_hr",
    "Average_Daily_Footage_ft",
    "Total_Footage_ft",
    "Total_Drilling_Hours",

    # Cost
    "Drilling_Cost_USD",
    "Cost_per_Foot_USD",
    "Operational_Cost_USD",
    "Operational_Cost_per_Foot_USD",

    # NPT
    "NPT_Hours",
    "NPT_Hours_pct",
    "NPT_Percent",
    "NPT_Cost_USD",

    # Economic exposure
    "Deferred_Cost_USD",
    "Total_Economic_Impact_USD",
    "Total_Economic_Impact_per_Foot_USD",

    # Original Stage 2E
    "Overall_Performance_Score",
    "Efficiency_Score",
    "Cost_Score",
    "Reliability_Score",
    "Economic_Impact_Score",
    "Risk_Tier",
    "Performance_Profile",

    # Calibrated dimensions
    "Calibrated_Efficiency_Score",
    "Operational_Efficiency_Score",
    "Reliability_Score_Calibrated",
    "Economic_Exposure_Score",

    # Calibrated master scores
    "Engineering_Performance_Score",
    "Engineering_Risk_Resilience_Score",
    "Risk_Index",

    # Classification
    "Engineering_Performance_Tier",
    "Engineering_Risk_Tier",
    "Performance_Risk_Quadrant",
    "Benchmark_Flag",
    "Improvement_Priority",

    # Comparison
    "Score_Change_vs_Stage2E",

    # Rankings
    "Engineering_Performance_Rank",
    "Engineering_Risk_Resilience_Rank",
    "Engineering_Overall_Rank",
]


df_output = df[output_columns].copy()


# ============================================================
# 19. SAVE OUTPUTS
# ============================================================

df_output.to_csv(
    OUTPUT_FILE,
    index=False
)

df_correlation.to_csv(
    SUMMARY_FILE,
    index=False
)


# ============================================================
# 20. REPORT
# ============================================================

print("\n" + "=" * 70)
print("CALIBRATION COMPLETE")
print("=" * 70)

print(
    f"\nOutput file:\n{OUTPUT_FILE}"
)

print(
    f"Correlation file:\n{SUMMARY_FILE}"
)

print(
    f"\nWells analyzed: "
    f"{len(df_output):,}"
)


# ------------------------------------------------------------
# Quadrant distribution
# ------------------------------------------------------------

print("\nPerformance / Risk Quadrant:")

quadrant_counts = (
    df_output["Performance_Risk_Quadrant"]
    .value_counts()
)

for quadrant, count in quadrant_counts.items():

    pct = count / len(df_output) * 100

    print(
        f"  {quadrant:<25} "
        f"{count:>3} wells "
        f"({pct:5.1f}%)"
    )


# ------------------------------------------------------------
# Performance tier
# ------------------------------------------------------------

print("\nEngineering Performance Tier:")

tier_counts = (
    df_output["Engineering_Performance_Tier"]
    .value_counts()
)

for tier, count in tier_counts.items():

    pct = count / len(df_output) * 100

    print(
        f"  {tier:<20} "
        f"{count:>3} wells "
        f"({pct:5.1f}%)"
    )


# ------------------------------------------------------------
# Risk tier
# ------------------------------------------------------------

print("\nEngineering Risk Tier:")

risk_counts = (
    df_output["Engineering_Risk_Tier"]
    .value_counts()
)

for tier, count in risk_counts.items():

    pct = count / len(df_output) * 100

    print(
        f"  {tier:<20} "
        f"{count:>3} wells "
        f"({pct:5.1f}%)"
    )


# ============================================================
# 21. TOP BENCHMARKS
# ============================================================

print("\n" + "-" * 70)
print("TOP 10 ENGINEERING BENCHMARKS")
print("-" * 70)

top_benchmarks = (
    df_output[
        df_output["Performance_Risk_Quadrant"]
        == "Benchmark"
    ]
    .sort_values(
        "Engineering_Overall_Rank"
    )
    .head(10)
)

print(
    top_benchmarks[
        [
            "Engineering_Overall_Rank",
            "Well_ID",
            "Rig_ID",
            "Engineering_Performance_Score",
            "Engineering_Risk_Resilience_Score",
            "Average_ROP_ft_hr",
            "NPT_Percent",
            "Operational_Cost_per_Foot_USD",
        ]
    ].to_string(index=False)
)


# ============================================================
# 22. PRIORITY INTERVENTIONS
# ============================================================

print("\n" + "-" * 70)
print("TOP PRIORITY INTERVENTIONS")
print("-" * 70)

priority = (
    df_output[
        df_output["Performance_Risk_Quadrant"]
        == "Priority Intervention"
    ]
    .sort_values(
        [
            "Engineering_Performance_Score",
            "Engineering_Risk_Resilience_Score"
        ],
        ascending=[True, True]
    )
    .head(10)
)

print(
    priority[
        [
            "Well_ID",
            "Rig_ID",
            "Engineering_Performance_Score",
            "Engineering_Risk_Resilience_Score",
            "Average_ROP_ft_hr",
            "NPT_Percent",
            "Operational_Cost_per_Foot_USD",
            "Total_Economic_Impact_per_Foot_USD",
        ]
    ].to_string(index=False)
)


# ============================================================
# 23. SCORE CHANGE
# ============================================================

print("\n" + "-" * 70)
print("LARGEST SCORE CHANGES VS STAGE 2E")
print("-" * 70)

score_change = (
    df_output[
        [
            "Well_ID",
            "Overall_Performance_Score",
            "Engineering_Performance_Score",
            "Score_Change_vs_Stage2E"
        ]
    ]
    .sort_values(
        "Score_Change_vs_Stage2E"
    )
)

print("\nLargest negative changes:")

print(
    score_change.head(5)
    .to_string(index=False)
)

print("\nLargest positive changes:")

print(
    score_change.tail(5)
    .sort_values(
        "Score_Change_vs_Stage2E",
        ascending=False
    )
    .to_string(index=False)
)


# ============================================================
# 24. CORRELATION REPORT
# ============================================================

print("\n" + "-" * 70)
print("SPEARMAN CORRELATION — CALIBRATED SCORES")
print("-" * 70)

print(
    df_correlation[
        df_correlation["Score"].isin(
            [
                "Stage2E_Overall",
                "Calibrated_Performance",
                "Risk_Resilience"
            ]
        )
    ]
    .pivot(
        index="Metric",
        columns="Score",
        values="Spearman_Correlation"
    )
    .round(3)
    .to_string()
)


# ============================================================
# 25. FINAL MESSAGE
# ============================================================

print("\n" + "=" * 70)
print("STAGE 2E.1 FINISHED SUCCESSFULLY")
print("=" * 70)

print("\nNext stage:")
print("Stage 2F - Rig × Well × NPT Matrix")
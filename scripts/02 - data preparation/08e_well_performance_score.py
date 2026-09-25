import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "Integrated_Drilling_Performance.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "Well_Performance_Score.csv"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 90)
print("STAGE 2E — ADVANCED WELL PERFORMANCE & RISK SCORE")
print("=" * 90)

print(f"\nInput:")
print(INPUT_FILE)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Integrated performance file not found:\n{INPUT_FILE}"
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\n[1/8] Loading integrated performance data...")

df = pd.read_csv(INPUT_FILE)

print(f"     Records: {len(df):,}")
print(f"     Wells: {df['Well_ID'].nunique():,}")
print(f"     Rigs: {df['Rig_ID'].nunique():,}")


# ============================================================
# 2. VALIDATION
# ============================================================

print("\n[2/8] Validating required fields...")

required_columns = [
    "Well_ID",
    "Well_Name",
    "Rig_ID",
    "Total_Footage_ft",
    "Drilling_Days",
    "Total_Drilling_Hours",
    "Average_ROP_ft_hr",
    "Drilling_Cost_USD",
    "NPT_Hours",
    "NPT_Hours_pct",
    "NPT_Cost_USD",
    "Deferred_Cost_USD",
    "Operational_Cost_USD",
    "Operational_Cost_per_Foot_USD",
    "Total_Economic_Impact_USD",
    "Total_Economic_Impact_per_Foot_USD",
]

missing = [
    col for col in required_columns
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

print("     Required fields: PASS")


# ============================================================
# 3. DERIVE EFFICIENCY METRICS
# ============================================================

print("\n[3/8] Calculating efficiency metrics...")

df["Footage_per_Drilling_Day_ft"] = (
    df["Total_Footage_ft"]
    / df["Drilling_Days"]
)

df["Effective_Footage_per_Hour_ft"] = (
    df["Total_Footage_ft"]
    / df["Total_Drilling_Hours"]
)


# ============================================================
# 4. PERCENTILE SCORING FUNCTION
# ============================================================

def higher_is_better_score(series):
    """
    Converts a metric into a 0–100 percentile score.
    Higher metric value = higher score.
    """
    return series.rank(
        method="average",
        pct=True
    ) * 100


def lower_is_better_score(series):
    """
    Converts a metric into a 0–100 percentile score.
    Lower metric value = higher score.
    """
    return (
        1
        - series.rank(
            method="average",
            pct=True
        )
    ) * 100


# ============================================================
# 5. COMPONENT SCORES
# ============================================================

print("\n[4/8] Calculating component scores...")


# ------------------------------------------------------------
# EFFICIENCY SCORE
#
# 50% ROP
# 50% Footage / drilling day
# ------------------------------------------------------------

rop_score = higher_is_better_score(
    df["Average_ROP_ft_hr"]
)

footage_day_score = higher_is_better_score(
    df["Footage_per_Drilling_Day_ft"]
)

df["Efficiency_Score"] = (
    0.50 * rop_score
    + 0.50 * footage_day_score
)


# ------------------------------------------------------------
# COST SCORE
#
# Lower Operational Cost / ft = better
# ------------------------------------------------------------

df["Cost_Score"] = lower_is_better_score(
    df["Operational_Cost_per_Foot_USD"]
)


# ------------------------------------------------------------
# RELIABILITY SCORE
#
# Lower NPT % = better
# ------------------------------------------------------------

df["Reliability_Score"] = lower_is_better_score(
    df["NPT_Hours_pct"]
)


# ------------------------------------------------------------
# ECONOMIC IMPACT SCORE
#
# Lower Economic Impact / ft = better
# ------------------------------------------------------------

df["Economic_Impact_Score"] = lower_is_better_score(
    df["Total_Economic_Impact_per_Foot_USD"]
)


# ============================================================
# 6. OVERALL SCORE
# ============================================================

print("\n[5/8] Calculating Overall Performance Score...")

df["Overall_Performance_Score"] = (
    0.25 * df["Efficiency_Score"]
    + 0.25 * df["Cost_Score"]
    + 0.25 * df["Reliability_Score"]
    + 0.25 * df["Economic_Impact_Score"]
)

df["Overall_Performance_Score"] = (
    df["Overall_Performance_Score"]
    .round(2)
)


# ============================================================
# 7. RISK TIER
# ============================================================

print("\n[6/8] Assigning performance tiers...")


def assign_tier(score):

    if score >= 80:
        return "Excellent"

    elif score >= 65:
        return "Good"

    elif score >= 50:
        return "Watch"

    else:
        return "High Risk"


df["Risk_Tier"] = df[
    "Overall_Performance_Score"
].apply(assign_tier)


# ============================================================
# 8. DIAGNOSTIC FLAGS
# ============================================================

print("\n[7/8] Creating diagnostic flags...")


efficiency_median = df[
    "Efficiency_Score"
].median()

cost_median = df[
    "Cost_Score"
].median()

reliability_median = df[
    "Reliability_Score"
].median()

economic_median = df[
    "Economic_Impact_Score"
].median()


df["Efficiency_Flag"] = np.where(
    df["Efficiency_Score"] >= efficiency_median,
    "Strong",
    "Weak"
)

df["Cost_Flag"] = np.where(
    df["Cost_Score"] >= cost_median,
    "Efficient",
    "Inefficient"
)

df["Reliability_Flag"] = np.where(
    df["Reliability_Score"] >= reliability_median,
    "Reliable",
    "NPT Concern"
)

df["Economic_Flag"] = np.where(
    df["Economic_Impact_Score"] >= economic_median,
    "Lower Impact",
    "Higher Impact"
)


# ============================================================
# PERFORMANCE PROFILE
# ============================================================

def performance_profile(row):

    strong = 0

    if row["Efficiency_Score"] >= 65:
        strong += 1

    if row["Cost_Score"] >= 65:
        strong += 1

    if row["Reliability_Score"] >= 65:
        strong += 1

    if row["Economic_Impact_Score"] >= 65:
        strong += 1


    if strong == 4:
        return "All-Round Benchmark"

    elif strong == 3:
        return "Strong Performer"

    elif strong == 2:
        return "Balanced / Watch"

    elif strong == 1:
        return "Specialized Performer"

    return "Underperformer"


df["Performance_Profile"] = df.apply(
    performance_profile,
    axis=1
)


# ============================================================
# RANKINGS
# ============================================================

df["Overall_Rank"] = (
    df["Overall_Performance_Score"]
    .rank(
        ascending=False,
        method="min"
    )
    .astype(int)
)


df["Efficiency_Rank"] = (
    df["Efficiency_Score"]
    .rank(
        ascending=False,
        method="min"
    )
    .astype(int)
)


df["Cost_Rank"] = (
    df["Cost_Score"]
    .rank(
        ascending=False,
        method="min"
    )
    .astype(int)
)


df["Reliability_Rank"] = (
    df["Reliability_Score"]
    .rank(
        ascending=False,
        method="min"
    )
    .astype(int)
)


df["Economic_Impact_Rank"] = (
    df["Economic_Impact_Score"]
    .rank(
        ascending=False,
        method="min"
    )
    .astype(int)
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    "Overall_Performance_Score",
    ascending=False
)


# ============================================================
# ROUND
# ============================================================

numeric_columns = df.select_dtypes(
    include=["float64", "float32"]
).columns

df[numeric_columns] = (
    df[numeric_columns]
    .round(2)
)


# ============================================================
# EXPORT
# ============================================================

print("\n[8/8] Exporting scored dataset...")

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 90)
print("TOP 10 WELLS — OVERALL PERFORMANCE")
print("=" * 90)

print(
    df[
        [
            "Overall_Rank",
            "Well_ID",
            "Well_Name",
            "Rig_ID",
            "Average_ROP_ft_hr",
            "NPT_Hours_pct",
            "Operational_Cost_per_Foot_USD",
            "Total_Economic_Impact_per_Foot_USD",
            "Efficiency_Score",
            "Cost_Score",
            "Reliability_Score",
            "Economic_Impact_Score",
            "Overall_Performance_Score",
            "Risk_Tier",
            "Performance_Profile"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# ============================================================
# BOTTOM 10
# ============================================================

print("\n" + "=" * 90)
print("BOTTOM 10 WELLS — OVERALL PERFORMANCE")
print("=" * 90)

print(
    df[
        [
            "Overall_Rank",
            "Well_ID",
            "Well_Name",
            "Rig_ID",
            "Average_ROP_ft_hr",
            "NPT_Hours_pct",
            "Operational_Cost_per_Foot_USD",
            "Total_Economic_Impact_per_Foot_USD",
            "Overall_Performance_Score",
            "Risk_Tier",
            "Performance_Profile"
        ]
    ]
    .tail(10)
    .sort_values(
        "Overall_Performance_Score"
    )
    .to_string(index=False)
)


# ============================================================
# RISK DISTRIBUTION
# ============================================================

print("\n" + "=" * 90)
print("RISK TIER DISTRIBUTION")
print("=" * 90)

print(
    df["Risk_Tier"]
    .value_counts()
    .to_string()
)


# ============================================================
# PROFILE DISTRIBUTION
# ============================================================

print("\n" + "=" * 90)
print("PERFORMANCE PROFILE DISTRIBUTION")
print("=" * 90)

print(
    df["Performance_Profile"]
    .value_counts()
    .to_string()
)


# ============================================================
# SCORE STATISTICS
# ============================================================

print("\n" + "=" * 90)
print("SCORE STATISTICS")
print("=" * 90)

score_columns = [
    "Efficiency_Score",
    "Cost_Score",
    "Reliability_Score",
    "Economic_Impact_Score",
    "Overall_Performance_Score"
]

print(
    df[score_columns]
    .describe()
    .round(2)
    .to_string()
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 90)
print("VALIDATION")
print("=" * 90)

print(
    f"Wells: {len(df):,}"
)

print(
    f"Unique Well_ID: {df['Well_ID'].nunique():,}"
)

print(
    f"Missing Overall Score: "
    f"{df['Overall_Performance_Score'].isna().sum()}"
)

print(
    f"Minimum Score: "
    f"{df['Overall_Performance_Score'].min():.2f}"
)

print(
    f"Maximum Score: "
    f"{df['Overall_Performance_Score'].max():.2f}"
)

print(
    f"Output file:\n{OUTPUT_FILE}"
)

print("\n" + "=" * 90)
print("STAGE 2E COMPLETED")
print("=" * 90)
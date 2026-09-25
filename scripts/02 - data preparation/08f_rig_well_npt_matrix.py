from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# STAGE 2F
# RIG × WELL × NPT MATRIX
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INTEGRATED_FILE = (
    PROCESSED_DIR /
    "Integrated_Drilling_Performance.csv"
)

CALIBRATED_FILE = (
    PROCESSED_DIR /
    "Well_Engineering_Score_Calibrated.csv"
)

OUTPUT_FILE = (
    PROCESSED_DIR /
    "Rig_Well_NPT_Matrix.csv"
)

RIG_SUMMARY_FILE = (
    PROCESSED_DIR /
    "Rig_Effect_Summary.csv"
)

QUADRANT_FILE = (
    PROCESSED_DIR /
    "Rig_Well_Performance_Quadrants.csv"
)


# ============================================================
# 1. HEADER
# ============================================================

print("=" * 70)
print("STAGE 2F - RIG × WELL × NPT MATRIX")
print("=" * 70)


# ============================================================
# 2. LOAD DATA
# ============================================================

print("\nLoading datasets...")

df = pd.read_csv(INTEGRATED_FILE)
df_score = pd.read_csv(CALIBRATED_FILE)

print(
    f"Integrated dataset: {len(df):,} wells"
)

print(
    f"Calibrated score dataset: {len(df_score):,} wells"
)


# ============================================================
# 3. VALIDATE KEYS
# ============================================================

required_integrated = [
    "Well_ID",
    "Well_Name",
    "Operator",
    "Rig_ID",
    "Rig_Name",
    "Contractor",
    "Rig_Type",
    "Block",
    "Well_Type",
    "Country",
    "Water_Depth_ft",
    "Water_Depth_Category",
    "Target_Depth_ft",
    "Status",
    "Spud_Date",
    "Drilling_Days",
    "Total_Footage_ft",
    "Total_Drilling_Hours",
    "Average_ROP_ft_hr",
    "Maximum_ROP_ft_hr",
    "Total_Weather_Delay_hr",
    "Weather_Delay_pct",
    "Drilling_Cost_USD",
    "Cost_per_Foot_USD",
    "NPT_Events",
    "NPT_Hours",
    "NPT_Hours_pct",
    "NPT_Events_per_Day",
    "NPT_Hours_per_Day",
    "NPT_Cost_USD",
    "NPT_Cost_per_Foot_USD",
    "Deferred_Cost_USD",
    "Total_NPT_Impact_USD",
    "Operational_Cost_USD",
    "Operational_Cost_per_Foot_USD",
    "Total_Economic_Impact_USD",
    "Total_Economic_Impact_per_Foot_USD",
    "NPT_Cost_pct_of_Operational_Cost",
    "Target_Attainment_pct",
]


required_score = [
    "Well_ID",
    "Engineering_Performance_Score",
    "Engineering_Risk_Resilience_Score",
    "Risk_Index",
    "Engineering_Performance_Tier",
    "Engineering_Risk_Tier",
    "Performance_Risk_Quadrant",
    "Benchmark_Flag",
    "Improvement_Priority",
    "Engineering_Overall_Rank",
]


missing_integrated = [
    c for c in required_integrated
    if c not in df.columns
]

missing_score = [
    c for c in required_score
    if c not in df_score.columns
]


if missing_integrated:
    raise ValueError(
        "Missing columns in Integrated dataset: "
        f"{missing_integrated}"
    )

if missing_score:
    raise ValueError(
        "Missing columns in calibrated dataset: "
        f"{missing_score}"
    )


# ============================================================
# 4. ENSURE ONE ROW PER WELL
# ============================================================

if df["Well_ID"].duplicated().any():

    duplicates = (
        df.loc[
            df["Well_ID"].duplicated(keep=False),
            "Well_ID"
        ]
        .unique()
        .tolist()
    )

    raise ValueError(
        f"Duplicate wells found in Integrated dataset: "
        f"{duplicates}"
    )


if df_score["Well_ID"].duplicated().any():

    raise ValueError(
        "Duplicate Well_ID found in calibrated score dataset."
    )


# ============================================================
# 5. MERGE CALIBRATED ENGINEERING SCORE
# ============================================================

print("\nMerging calibrated engineering scores...")

score_columns = [
    "Well_ID",
    "Engineering_Performance_Score",
    "Engineering_Risk_Resilience_Score",
    "Risk_Index",
    "Engineering_Performance_Tier",
    "Engineering_Risk_Tier",
    "Performance_Risk_Quadrant",
    "Benchmark_Flag",
    "Improvement_Priority",
    "Engineering_Overall_Rank",
]

df_score = df_score[score_columns].copy()

df = pd.merge(
    df,
    df_score,
    on="Well_ID",
    how="left",
    validate="one_to_one"
)


# ============================================================
# 6. CHECK SCORE MERGE
# ============================================================

if df["Engineering_Performance_Score"].isna().any():

    missing_scores = (
        df.loc[
            df["Engineering_Performance_Score"].isna(),
            "Well_ID"
        ]
        .tolist()
    )

    raise ValueError(
        "Engineering scores missing for wells: "
        f"{missing_scores}"
    )


# ============================================================
# 7. CREATE RIG × WELL KEY
# ============================================================

df["Rig_Well_Key"] = (
    df["Rig_ID"].astype(str)
    + "_"
    + df["Well_ID"].astype(str)
)


# ============================================================
# 8. RIG-LEVEL BENCHMARKS
# ============================================================

print("\nCalculating rig-level benchmarks...")

rig_stats = (
    df.groupby("Rig_ID")
    .agg(
        Rig_Wells=("Well_ID", "nunique"),
        Rig_Avg_ROP_ft_hr=(
            "Average_ROP_ft_hr",
            "mean"
        ),
        Rig_Avg_Cost_per_Foot_USD=(
            "Cost_per_Foot_USD",
            "mean"
        ),
        Rig_Avg_Operational_Cost_per_Foot_USD=(
            "Operational_Cost_per_Foot_USD",
            "mean"
        ),
        Rig_Avg_NPT_pct=(
            "NPT_Hours_pct",
            "mean"
        ),
        Rig_Avg_NPT_Hours=(
            "NPT_Hours",
            "mean"
        ),
        Rig_Avg_Economic_Impact_per_Foot_USD=(
            "Total_Economic_Impact_per_Foot_USD",
            "mean"
        ),
        Rig_Total_Footage_ft=(
            "Total_Footage_ft",
            "sum"
        ),
        Rig_Total_Drilling_Hours=(
            "Total_Drilling_Hours",
            "sum"
        ),
        Rig_Total_Drilling_Cost_USD=(
            "Drilling_Cost_USD",
            "sum"
        ),
        Rig_Total_NPT_Hours=(
            "NPT_Hours",
            "sum"
        ),
        Rig_Total_NPT_Cost_USD=(
            "NPT_Cost_USD",
            "sum"
        ),
        Rig_Total_Economic_Impact_USD=(
            "Total_Economic_Impact_USD",
            "sum"
        ),
    )
    .reset_index()
)


# ============================================================
# 9. MERGE RIG BENCHMARKS
# ============================================================

df = pd.merge(
    df,
    rig_stats,
    on="Rig_ID",
    how="left",
    validate="many_to_one"
)


# ============================================================
# 10. CALCULATE WELL VS RIG EFFECT
# ============================================================

print("\nCalculating well-versus-rig performance deltas...")


# ROP
df["ROP_vs_Rig_Delta_ft_hr"] = (
    df["Average_ROP_ft_hr"]
    - df["Rig_Avg_ROP_ft_hr"]
)


# Cost
df["Operational_Cost_per_Foot_vs_Rig_Delta_USD"] = (
    df["Operational_Cost_per_Foot_USD"]
    - df["Rig_Avg_Operational_Cost_per_Foot_USD"]
)


# NPT
df["NPT_pct_vs_Rig_Delta_pct_points"] = (
    df["NPT_Hours_pct"]
    - df["Rig_Avg_NPT_pct"]
)


# Economic exposure
df["Economic_Impact_per_Foot_vs_Rig_Delta_USD"] = (
    df["Total_Economic_Impact_per_Foot_USD"]
    - df["Rig_Avg_Economic_Impact_per_Foot_USD"]
)


# ============================================================
# 11. RIG RELATIVE PERFORMANCE
# ============================================================

df["ROP_vs_Rig"] = np.where(
    df["ROP_vs_Rig_Delta_ft_hr"] >= 0,
    "Above Rig Average",
    "Below Rig Average"
)


df["Cost_vs_Rig"] = np.where(
    df["Operational_Cost_per_Foot_vs_Rig_Delta_USD"] <= 0,
    "Better Than Rig Average",
    "Worse Than Rig Average"
)


df["NPT_vs_Rig"] = np.where(
    df["NPT_pct_vs_Rig_Delta_pct_points"] <= 0,
    "Better Than Rig Average",
    "Worse Than Rig Average"
)


df["Economic_Exposure_vs_Rig"] = np.where(
    df["Economic_Impact_per_Foot_vs_Rig_Delta_USD"] <= 0,
    "Better Than Rig Average",
    "Worse Than Rig Average"
)


# ============================================================
# 12. RIG × WELL INTERACTION CLASSIFICATION
# ============================================================

def interaction_class(row):

    good_rop = row["ROP_vs_Rig_Delta_ft_hr"] >= 0

    good_cost = (
        row["Operational_Cost_per_Foot_vs_Rig_Delta_USD"]
        <= 0
    )

    good_npt = (
        row["NPT_pct_vs_Rig_Delta_pct_points"]
        <= 0
    )

    if good_rop and good_cost and good_npt:
        return "Strong Rig-Well Fit"

    if good_rop and good_cost and not good_npt:
        return "Efficient but NPT Exposed"

    if good_rop and not good_cost and good_npt:
        return "Fast but Expensive"

    if not good_rop and good_cost and good_npt:
        return "Slow but Controlled"

    if good_rop and not good_cost and not good_npt:
        return "Fast but High Exposure"

    if not good_rop and good_cost and not good_npt:
        return "Economical but NPT Exposed"

    if not good_rop and not good_cost and good_npt:
        return "Slow and Expensive"

    return "Weak Rig-Well Fit"


df["Rig_Well_Interaction"] = df.apply(
    interaction_class,
    axis=1
)


# ============================================================
# 13. RIG EFFECT INDICATOR
# ============================================================

df["Rig_Effect_Flag"] = np.select(
    [
        (
            df["ROP_vs_Rig_Delta_ft_hr"] < 0
        )
        &
        (
            df["Operational_Cost_per_Foot_vs_Rig_Delta_USD"] > 0
        )
        &
        (
            df["NPT_pct_vs_Rig_Delta_pct_points"] > 0
        ),

        (
            df["ROP_vs_Rig_Delta_ft_hr"] >= 0
        )
        &
        (
            df["Operational_Cost_per_Foot_vs_Rig_Delta_USD"] <= 0
        )
        &
        (
            df["NPT_pct_vs_Rig_Delta_pct_points"] <= 0
        ),
    ],
    [
        "Negative Rig-Well Interaction",
        "Positive Rig-Well Interaction",
    ],
    default="Mixed"
)


# ============================================================
# 14. FINAL OUTPUT COLUMNS
# ============================================================

output_columns = [
    # Identity
    "Rig_Well_Key",
    "Rig_ID",
    "Rig_Name",
    "Contractor",
    "Rig_Type",
    "Well_ID",
    "Well_Name",
    "Operator",
    "Block",
    "Well_Type",
    "Country",

    # Well characteristics
    "Water_Depth_ft",
    "Water_Depth_Category",
    "Target_Depth_ft",
    "Status",
    "Spud_Date",

    # Drilling
    "Drilling_Days",
    "Total_Footage_ft",
    "Total_Drilling_Hours",
    "Average_ROP_ft_hr",
    "Maximum_ROP_ft_hr",
    "Total_Weather_Delay_hr",
    "Weather_Delay_pct",
    "Drilling_Cost_USD",
    "Cost_per_Foot_USD",

    # NPT
    "NPT_Events",
    "NPT_Hours",
    "NPT_Hours_pct",
    "NPT_Events_per_Day",
    "NPT_Hours_per_Day",
    "NPT_Cost_USD",
    "NPT_Cost_per_Foot_USD",
    "Deferred_Cost_USD",
    "Total_NPT_Impact_USD",

    # Economics
    "Operational_Cost_USD",
    "Operational_Cost_per_Foot_USD",
    "Total_Economic_Impact_USD",
    "Total_Economic_Impact_per_Foot_USD",
    "NPT_Cost_pct_of_Operational_Cost",

    # Target
    "Target_Attainment_pct",

    # Engineering score
    "Engineering_Performance_Score",
    "Engineering_Risk_Resilience_Score",
    "Risk_Index",
    "Engineering_Performance_Tier",
    "Engineering_Risk_Tier",
    "Performance_Risk_Quadrant",
    "Benchmark_Flag",
    "Improvement_Priority",
    "Engineering_Overall_Rank",

    # Rig benchmarks
    "Rig_Wells",
    "Rig_Avg_ROP_ft_hr",
    "Rig_Avg_Cost_per_Foot_USD",
    "Rig_Avg_Operational_Cost_per_Foot_USD",
    "Rig_Avg_NPT_pct",
    "Rig_Avg_NPT_Hours",
    "Rig_Avg_Economic_Impact_per_Foot_USD",

    # Rig relative deltas
    "ROP_vs_Rig_Delta_ft_hr",
    "Operational_Cost_per_Foot_vs_Rig_Delta_USD",
    "NPT_pct_vs_Rig_Delta_pct_points",
    "Economic_Impact_per_Foot_vs_Rig_Delta_USD",

    # Relative classifications
    "ROP_vs_Rig",
    "Cost_vs_Rig",
    "NPT_vs_Rig",
    "Economic_Exposure_vs_Rig",

    # Interaction
    "Rig_Well_Interaction",
    "Rig_Effect_Flag",
]


df_output = df[output_columns].copy()


# ============================================================
# 15. SAVE MAIN MATRIX
# ============================================================

df_output.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# 16. RIG EFFECT SUMMARY
# ============================================================

rig_summary = (
    df.groupby(
        [
            "Rig_ID",
            "Rig_Name"
        ]
    )
    .agg(
        Wells=("Well_ID", "nunique"),

        Avg_ROP_ft_hr=(
            "Average_ROP_ft_hr",
            "mean"
        ),

        Avg_Operational_Cost_per_Foot_USD=(
            "Operational_Cost_per_Foot_USD",
            "mean"
        ),

        Avg_NPT_pct=(
            "NPT_Hours_pct",
            "mean"
        ),

        Avg_Economic_Impact_per_Foot_USD=(
            "Total_Economic_Impact_per_Foot_USD",
            "mean"
        ),

        Positive_Rig_Well_Interactions=(
            "Rig_Effect_Flag",
            lambda x: (
                x == "Positive Rig-Well Interaction"
            ).sum()
        ),

        Negative_Rig_Well_Interactions=(
            "Rig_Effect_Flag",
            lambda x: (
                x == "Negative Rig-Well Interaction"
            ).sum()
        ),

        Mixed_Interactions=(
            "Rig_Effect_Flag",
            lambda x: (
                x == "Mixed"
            ).sum()
        ),

        Strong_Rig_Well_Fit=(
            "Rig_Well_Interaction",
            lambda x: (
                x == "Strong Rig-Well Fit"
            ).sum()
        ),

        Priority_Interventions=(
            "Performance_Risk_Quadrant",
            lambda x: (
                x == "Priority Intervention"
            ).sum()
        ),
    )
    .reset_index()
)


rig_summary["Positive_Interaction_pct"] = (
    rig_summary["Positive_Rig_Well_Interactions"]
    / rig_summary["Wells"]
    * 100
)


rig_summary["Negative_Interaction_pct"] = (
    rig_summary["Negative_Rig_Well_Interactions"]
    / rig_summary["Wells"]
    * 100
)


rig_summary["Priority_Intervention_pct"] = (
    rig_summary["Priority_Interventions"]
    / rig_summary["Wells"]
    * 100
)


rig_summary = rig_summary.sort_values(
    "Positive_Interaction_pct",
    ascending=False
)


rig_summary.to_csv(
    RIG_SUMMARY_FILE,
    index=False
)


# ============================================================
# 17. PERFORMANCE QUADRANT FILE
# ============================================================

quadrant = df_output[
    [
        "Rig_ID",
        "Rig_Name",
        "Well_ID",
        "Well_Name",
        "Engineering_Performance_Score",
        "Engineering_Risk_Resilience_Score",
        "Performance_Risk_Quadrant",
        "Improvement_Priority",
        "Average_ROP_ft_hr",
        "NPT_Hours_pct",
        "Operational_Cost_per_Foot_USD",
        "Total_Economic_Impact_per_Foot_USD",
        "Rig_Well_Interaction",
        "Rig_Effect_Flag",
    ]
].copy()


quadrant.to_csv(
    QUADRANT_FILE,
    index=False
)


# ============================================================
# 18. VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(
    f"\nRig × Well records: "
    f"{len(df_output):,}"
)

print(
    f"Unique rigs: "
    f"{df_output['Rig_ID'].nunique():,}"
)

print(
    f"Unique wells: "
    f"{df_output['Well_ID'].nunique():,}"
)

print(
    f"Unique Rig × Well combinations: "
    f"{df_output['Rig_Well_Key'].nunique():,}"
)


if (
    df_output["Rig_Well_Key"].nunique()
    != len(df_output)
):
    raise ValueError(
        "Duplicate Rig × Well combinations detected."
    )


# ============================================================
# 19. INTERACTION DISTRIBUTION
# ============================================================

print("\nRig × Well Interaction:")

interaction_counts = (
    df_output["Rig_Well_Interaction"]
    .value_counts()
)


for category, count in interaction_counts.items():

    pct = (
        count
        / len(df_output)
        * 100
    )

    print(
        f"  {category:<32} "
        f"{count:>3} "
        f"({pct:5.1f}%)"
    )


# ============================================================
# 20. RIG EFFECT DISTRIBUTION
# ============================================================

print("\nRig Effect Flag:")

effect_counts = (
    df_output["Rig_Effect_Flag"]
    .value_counts()
)


for category, count in effect_counts.items():

    pct = (
        count
        / len(df_output)
        * 100
    )

    print(
        f"  {category:<32} "
        f"{count:>3} "
        f"({pct:5.1f}%)"
    )


# ============================================================
# 21. PRIORITY WELLS
# ============================================================

print("\n" + "-" * 70)
print("PRIORITY INTERVENTION WELLS")
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
            "Rig_ID",
            "Well_ID",
            "Engineering_Performance_Score",
            "Engineering_Risk_Resilience_Score",
            "Average_ROP_ft_hr",
            "NPT_Hours_pct",
            "Operational_Cost_per_Foot_USD",
            "Rig_Well_Interaction",
        ]
    ].to_string(index=False)
)


# ============================================================
# 22. STRONG RIG-WELL FITS
# ============================================================

print("\n" + "-" * 70)
print("STRONG RIG-WELL FITS")
print("-" * 70)

strong_fit = df_output[
    df_output["Rig_Well_Interaction"]
    == "Strong Rig-Well Fit"
].sort_values(
    "Engineering_Overall_Rank"
).head(10)


print(
    strong_fit[
        [
            "Rig_ID",
            "Well_ID",
            "Average_ROP_ft_hr",
            "NPT_Hours_pct",
            "Operational_Cost_per_Foot_USD",
            "ROP_vs_Rig_Delta_ft_hr",
            "NPT_pct_vs_Rig_Delta_pct_points",
        ]
    ].to_string(index=False)
)


# ============================================================
# 23. RIG SUMMARY
# ============================================================

print("\n" + "-" * 70)
print("RIG EFFECT SUMMARY")
print("-" * 70)

print(
    rig_summary[
        [
            "Rig_ID",
            "Rig_Name",
            "Wells",
            "Avg_ROP_ft_hr",
            "Avg_Operational_Cost_per_Foot_USD",
            "Avg_NPT_pct",
            "Positive_Interaction_pct",
            "Negative_Interaction_pct",
            "Priority_Intervention_pct",
        ]
    ].to_string(index=False)
)


# ============================================================
# 24. OUTPUT FILES
# ============================================================

print("\n" + "=" * 70)
print("STAGE 2F COMPLETED SUCCESSFULLY")
print("=" * 70)

print(
    f"\nMain matrix:\n{OUTPUT_FILE}"
)

print(
    f"\nRig summary:\n{RIG_SUMMARY_FILE}"
)

print(
    f"\nQuadrant file:\n{QUADRANT_FILE}"
)

print("\nNext stage:")
print("Stage 2G - Advanced SQL Analytics")
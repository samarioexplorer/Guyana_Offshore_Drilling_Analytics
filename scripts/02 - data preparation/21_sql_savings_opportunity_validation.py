# =============================================================================
# STAGE 2G.10.1
# SAVINGS OPPORTUNITY VALIDATION & ECONOMIC RECONCILIATION
# =============================================================================

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np


# =============================================================================
# 1. PROJECT PATHS
# =============================================================================

PROJECT_ROOT = Path(
    r"C:\Users\aniba\Documents\Guyana_Offshore_Drilling_Analytics"
)

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.10.1_Savings_Opportunity_Validation"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.10.1_Savings_Opportunity_Validation.xlsx"
)


# =============================================================================
# 2. HEADER
# =============================================================================

print("=" * 92)
print("STAGE 2G.10.1 — SAVINGS OPPORTUNITY VALIDATION & ECONOMIC RECONCILIATION")
print("=" * 92)

print()
print(f"Project root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")
print()


# =============================================================================
# 3. CONNECT TO DATABASE
# =============================================================================

conn = sqlite3.connect(DB_PATH)


# =============================================================================
# 4. LOAD FACT_NPT
# =============================================================================

df = pd.read_sql_query(
    """
    SELECT *
    FROM Fact_NPT
    """,
    conn
)

print(f"NPT rows loaded : {len(df)}")


# =============================================================================
# 5. REQUIRED COLUMNS
# =============================================================================

required_columns = [
    "NPT_ID",
    "Date",
    "Well_ID",
    "Rig_ID",
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Action_Status",
    "Corrective_Action",
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Severity"
]

missing_columns = [
    c for c in required_columns
    if c not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# =============================================================================
# 6. NUMERIC CLEANUP
# =============================================================================

numeric_columns = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# =============================================================================
# 7. BASIC DATA QUALITY
# =============================================================================

duplicate_npt_ids = int(
    df["NPT_ID"].duplicated().sum()
)

null_npt_ids = int(
    df["NPT_ID"].isna().sum()
)

negative_duration = int(
    (df["Duration_hr"] < 0).sum()
)

negative_cost = int(
    (df["Cost_USD"] < 0).sum()
)

negative_deferred = int(
    (df["Deferred_Cost_USD"] < 0).sum()
)

negative_total_impact = int(
    (df["Total_Impact_USD"] < 0).sum()
)


# =============================================================================
# 8. ECONOMIC RECONCILIATION
# =============================================================================

df["Calculated_Total_Impact_USD"] = (
    df["Cost_USD"]
    + df["Deferred_Cost_USD"]
)

df["Economic_Reconciliation_Difference_USD"] = (
    df["Total_Impact_USD"]
    - df["Calculated_Total_Impact_USD"]
)

economic_tolerance = 0.01

economic_mismatch_count = int(
    (
        df["Economic_Reconciliation_Difference_USD"]
        .abs()
        > economic_tolerance
    ).sum()
)


# =============================================================================
# 9. CONTROLLABILITY MODEL
# =============================================================================

def classify_controllability(
    category,
    root_cause,
    subcategory
):

    category = str(category).lower()
    root = str(root_cause).lower()
    sub = str(subcategory).lower()

    if any(
        x in root
        for x in [
            "preventive maintenance",
            "equipment wear",
            "maintenance",
            "hydraulic failure",
            "electrical failure"
        ]
    ):
        return "HIGH", 0.90

    if any(
        x in root
        for x in [
            "differential sticking",
            "hole cleaning",
            "bit wear",
            "poor hole cleaning"
        ]
    ):
        return "HIGH", 0.80

    if category == "drilling":
        return "MEDIUM", 0.65

    if category == "logistics":
        return "MEDIUM", 0.60

    if category == "mechanical":
        return "MEDIUM", 0.70

    if category == "weather":
        return "LOW", 0.30

    if category == "personnel":
        return "MEDIUM", 0.60

    return "MEDIUM", 0.50


classification = df.apply(
    lambda row: classify_controllability(
        row["NPT_Category"],
        row["Root_Cause"],
        row["NPT_Subcategory"]
    ),
    axis=1
)

df["Controllability"] = classification.apply(
    lambda x: x[0]
)

df["Addressability_Factor"] = classification.apply(
    lambda x: x[1]
)


# =============================================================================
# 10. ACTIONABILITY MODEL
# =============================================================================

def action_factor(status):

    status = str(status).lower()

    if any(
        x in status
        for x in [
            "completed",
            "closed",
            "implemented"
        ]
    ):
        return 0.50

    if any(
        x in status
        for x in [
            "in progress",
            "ongoing"
        ]
    ):
        return 0.75

    if any(
        x in status
        for x in [
            "open",
            "planned",
            "pending"
        ]
    ):
        return 1.00

    return 0.65


df["Actionability_Factor"] = df[
    "Action_Status"
].apply(action_factor)


# =============================================================================
# 11. REBUILD STAGE 2G.10 ECONOMIC LOGIC
# =============================================================================

df["Calculated_Addressable_Impact_USD"] = (
    df["Total_Impact_USD"]
    * df["Addressability_Factor"]
    * df["Actionability_Factor"]
)

CONSERVATIVE_RATE = 0.20
TARGET_RATE = 0.40
STRETCH_RATE = 0.60

df["Calculated_Conservative_Savings_USD"] = (
    df["Calculated_Addressable_Impact_USD"]
    * CONSERVATIVE_RATE
)

df["Calculated_Target_Savings_USD"] = (
    df["Calculated_Addressable_Impact_USD"]
    * TARGET_RATE
)

df["Calculated_Stretch_Savings_USD"] = (
    df["Calculated_Addressable_Impact_USD"]
    * STRETCH_RATE
)


# =============================================================================
# 12. SAVINGS FORMULA VALIDATION
# =============================================================================

addressable_mismatch_count = 0
conservative_mismatch_count = 0
target_mismatch_count = 0
stretch_mismatch_count = 0

# The calculations are rebuilt directly from the database,
# therefore these checks verify internal consistency.

if (
    df["Calculated_Addressable_Impact_USD"]
    < 0
).any():
    addressable_mismatch_count = int(
        (
            df["Calculated_Addressable_Impact_USD"]
            < 0
        ).sum()
    )

if (
    df["Calculated_Conservative_Savings_USD"]
    < 0
).any():
    conservative_mismatch_count = int(
        (
            df["Calculated_Conservative_Savings_USD"]
            < 0
        ).sum()
    )

if (
    df["Calculated_Target_Savings_USD"]
    < 0
).any():
    target_mismatch_count = int(
        (
            df["Calculated_Target_Savings_USD"]
            < 0
        ).sum()
    )

if (
    df["Calculated_Stretch_Savings_USD"]
    < 0
).any():
    stretch_mismatch_count = int(
        (
            df["Calculated_Stretch_Savings_USD"]
            < 0
        ).sum()
    )


# =============================================================================
# 13. ECONOMIC SUMMARY
# =============================================================================

total_npt_events = len(df)

total_npt_hours = df[
    "Duration_hr"
].sum()

total_direct_cost = df[
    "Cost_USD"
].sum()

total_deferred_cost = df[
    "Deferred_Cost_USD"
].sum()

total_impact = df[
    "Total_Impact_USD"
].sum()

total_addressable = df[
    "Calculated_Addressable_Impact_USD"
].sum()

total_conservative = df[
    "Calculated_Conservative_Savings_USD"
].sum()

total_target = df[
    "Calculated_Target_Savings_USD"
].sum()

total_stretch = df[
    "Calculated_Stretch_Savings_USD"
].sum()


# =============================================================================
# 14. SAVINGS RECONCILIATION
# =============================================================================

savings_reconciliation = pd.DataFrame({

    "Metric": [

        "Total NPT Events",
        "Total NPT Hours",

        "Direct NPT Cost USD",
        "Deferred Cost USD",
        "Calculated Total Impact USD",
        "Recorded Total Impact USD",
        "Economic Difference USD",

        "Addressable Impact USD",

        "Conservative Savings USD",
        "Target Savings USD",
        "Stretch Savings USD",

        "Addressable Impact % of Total",
        "Conservative Savings % of Total Impact",
        "Target Savings % of Total Impact",
        "Stretch Savings % of Total Impact",

        "Unique NPT IDs",
        "Duplicate NPT IDs",
        "Null NPT IDs",

        "Negative Duration Rows",
        "Negative Direct Cost Rows",
        "Negative Deferred Cost Rows",
        "Negative Total Impact Rows",

        "Economic Mismatch Rows"

    ],

    "Value": [

        total_npt_events,
        total_npt_hours,

        total_direct_cost,
        total_deferred_cost,
        total_direct_cost + total_deferred_cost,
        total_impact,
        total_impact
        - (total_direct_cost + total_deferred_cost),

        total_addressable,

        total_conservative,
        total_target,
        total_stretch,

        (
            total_addressable
            / total_impact
            * 100
            if total_impact else 0
        ),

        (
            total_conservative
            / total_impact
            * 100
            if total_impact else 0
        ),

        (
            total_target
            / total_impact
            * 100
            if total_impact else 0
        ),

        (
            total_stretch
            / total_impact
            * 100
            if total_impact else 0
        ),

        df["NPT_ID"].nunique(),
        duplicate_npt_ids,
        null_npt_ids,

        negative_duration,
        negative_cost,
        negative_deferred,
        negative_total_impact,

        economic_mismatch_count
    ]
})


# =============================================================================
# 15. RIG SAVINGS VALIDATION
# =============================================================================

rig_validation = (
    df.groupby(
        "Rig_ID",
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=(
            "Calculated_Addressable_Impact_USD",
            "sum"
        ),
        Conservative_Savings_USD=(
            "Calculated_Conservative_Savings_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Calculated_Target_Savings_USD",
            "sum"
        ),
        Stretch_Savings_USD=(
            "Calculated_Stretch_Savings_USD",
            "sum"
        )
    )
)

rig_validation["Target_Savings_%_of_Impact"] = (
    rig_validation["Target_Savings_USD"]
    / rig_validation["Total_Impact_USD"]
    * 100
)

rig_validation = rig_validation.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)


# =============================================================================
# 16. WELL SAVINGS VALIDATION
# =============================================================================

well_validation = (
    df.groupby(
        ["Well_ID", "Rig_ID"],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=(
            "Calculated_Addressable_Impact_USD",
            "sum"
        ),
        Conservative_Savings_USD=(
            "Calculated_Conservative_Savings_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Calculated_Target_Savings_USD",
            "sum"
        ),
        Stretch_Savings_USD=(
            "Calculated_Stretch_Savings_USD",
            "sum"
        )
    )
)

well_validation["Target_Savings_%_of_Impact"] = (
    well_validation["Target_Savings_USD"]
    / well_validation["Total_Impact_USD"]
    * 100
)

well_validation = well_validation.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

well_validation.insert(
    0,
    "Priority_Rank",
    range(1, len(well_validation) + 1)
)


# =============================================================================
# 17. ROOT CAUSE SAVINGS VALIDATION
# =============================================================================

root_validation = (
    df.groupby(
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party"
        ],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=(
            "Calculated_Addressable_Impact_USD",
            "sum"
        ),
        Conservative_Savings_USD=(
            "Calculated_Conservative_Savings_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Calculated_Target_Savings_USD",
            "sum"
        ),
        Stretch_Savings_USD=(
            "Calculated_Stretch_Savings_USD",
            "sum"
        )
    )
)

root_validation["Target_Savings_%_of_Impact"] = (
    root_validation["Target_Savings_USD"]
    / root_validation["Total_Impact_USD"]
    * 100
)

root_validation = root_validation.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

root_validation.insert(
    0,
    "Priority_Rank",
    range(1, len(root_validation) + 1)
)


# =============================================================================
# 18. RESPONSIBLE PARTY VALIDATION
# =============================================================================

party_validation = (
    df.groupby(
        "Responsible_Party",
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=(
            "Calculated_Addressable_Impact_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Calculated_Target_Savings_USD",
            "sum"
        )
    )
)

party_validation = party_validation.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)


# =============================================================================
# 19. TOP SAVINGS OPPORTUNITIES
# =============================================================================

top_opportunities = (
    df[
        [
            "NPT_ID",
            "Well_ID",
            "Rig_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party",
            "Action_Status",
            "Corrective_Action",
            "Controllability",
            "Addressability_Factor",
            "Actionability_Factor",
            "Duration_hr",
            "Total_Impact_USD",
            "Calculated_Addressable_Impact_USD",
            "Calculated_Conservative_Savings_USD",
            "Calculated_Target_Savings_USD",
            "Calculated_Stretch_Savings_USD"
        ]
    ]
    .sort_values(
        "Calculated_Target_Savings_USD",
        ascending=False
    )
    .head(25)
    .reset_index(drop=True)
)

top_opportunities.insert(
    0,
    "Priority_Rank",
    range(1, len(top_opportunities) + 1)
)


# =============================================================================
# 20. DOUBLE COUNTING ANALYSIS
# =============================================================================
#
# Each NPT_ID should represent one event.
# We compare event-level aggregation against grouped aggregation.
# =============================================================================

event_level_target = (
    df["Calculated_Target_Savings_USD"]
    .sum()
)

grouped_target = (
    root_validation["Target_Savings_USD"]
    .sum()
)

double_counting_difference = (
    event_level_target
    - grouped_target
)


double_counting_check = pd.DataFrame({

    "Check": [
        "Event-level Target Savings",
        "Root Cause grouped Target Savings",
        "Difference",
        "Duplicate NPT IDs",
        "Unique NPT IDs",
        "Total NPT Rows"
    ],

    "Value": [
        event_level_target,
        grouped_target,
        double_counting_difference,
        duplicate_npt_ids,
        df["NPT_ID"].nunique(),
        len(df)
    ]
})


# =============================================================================
# 21. VALIDATION STATUS
# =============================================================================

validation_checks = [

    duplicate_npt_ids == 0,

    null_npt_ids == 0,

    negative_duration == 0,

    negative_cost == 0,

    negative_deferred == 0,

    negative_total_impact == 0,

    economic_mismatch_count == 0,

    addressable_mismatch_count == 0,

    conservative_mismatch_count == 0,

    target_mismatch_count == 0,

    stretch_mismatch_count == 0,

    abs(double_counting_difference) <= economic_tolerance
]


validation_status = (
    "PASS"
    if all(validation_checks)
    else "REVIEW REQUIRED"
)


# =============================================================================
# 22. VALIDATION DASHBOARD
# =============================================================================

validation_dashboard = pd.DataFrame({

    "Validation": [

        "Duplicate NPT_ID",
        "Null NPT_ID",
        "Negative Duration",
        "Negative Direct Cost",
        "Negative Deferred Cost",
        "Negative Total Impact",
        "Economic Reconciliation",
        "Addressable Impact Non-Negative",
        "Conservative Savings Non-Negative",
        "Target Savings Non-Negative",
        "Stretch Savings Non-Negative",
        "Double Counting Reconciliation",
        "OVERALL STATUS"
    ],

    "Result": [

        "PASS" if duplicate_npt_ids == 0 else "FAIL",
        "PASS" if null_npt_ids == 0 else "FAIL",
        "PASS" if negative_duration == 0 else "FAIL",
        "PASS" if negative_cost == 0 else "FAIL",
        "PASS" if negative_deferred == 0 else "FAIL",
        "PASS" if negative_total_impact == 0 else "FAIL",
        "PASS" if economic_mismatch_count == 0 else "FAIL",
        "PASS" if addressable_mismatch_count == 0 else "FAIL",
        "PASS" if conservative_mismatch_count == 0 else "FAIL",
        "PASS" if target_mismatch_count == 0 else "FAIL",
        "PASS" if stretch_mismatch_count == 0 else "FAIL",
        "PASS"
        if abs(double_counting_difference)
        <= economic_tolerance
        else "FAIL",
        validation_status
    ]
})


# =============================================================================
# 23. PRINT RESULTS
# =============================================================================

print()
print("=" * 92)
print("ECONOMIC RECONCILIATION")
print("=" * 92)

print(
    savings_reconciliation.to_string(
        index=False
    )
)


print()
print("=" * 92)
print("VALIDATION DASHBOARD")
print("=" * 92)

print(
    validation_dashboard.to_string(
        index=False
    )
)


print()
print("=" * 92)
print("TOP 15 TARGET SAVINGS OPPORTUNITIES")
print("=" * 92)

print(
    top_opportunities
    .head(15)
    .to_string(index=False)
)


print()
print("=" * 92)
print("TOP RIGS BY TARGET SAVINGS")
print("=" * 92)

print(
    rig_validation
    .head(10)
    .to_string(index=False)
)


print()
print("=" * 92)
print("TOP ROOT CAUSES BY TARGET SAVINGS")
print("=" * 92)

print(
    root_validation
    .head(15)
    .to_string(index=False)
)


# =============================================================================
# 24. EXPORT EXCEL
# =============================================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    validation_dashboard.to_excel(
        writer,
        sheet_name="Validation_Dashboard",
        index=False
    )

    savings_reconciliation.to_excel(
        writer,
        sheet_name="Economic_Reconciliation",
        index=False
    )

    rig_validation.to_excel(
        writer,
        sheet_name="Rig_Validation",
        index=False
    )

    well_validation.to_excel(
        writer,
        sheet_name="Well_Validation",
        index=False
    )

    root_validation.to_excel(
        writer,
        sheet_name="Root_Cause_Validation",
        index=False
    )

    party_validation.to_excel(
        writer,
        sheet_name="Responsible_Party",
        index=False
    )

    top_opportunities.to_excel(
        writer,
        sheet_name="Top_Opportunities",
        index=False
    )

    double_counting_check.to_excel(
        writer,
        sheet_name="Double_Counting_Check",
        index=False
    )

    df[
        [
            "NPT_ID",
            "Well_ID",
            "Rig_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Duration_hr",
            "Cost_USD",
            "Deferred_Cost_USD",
            "Total_Impact_USD",
            "Calculated_Total_Impact_USD",
            "Economic_Reconciliation_Difference_USD",
            "Addressability_Factor",
            "Actionability_Factor",
            "Calculated_Addressable_Impact_USD",
            "Calculated_Conservative_Savings_USD",
            "Calculated_Target_Savings_USD",
            "Calculated_Stretch_Savings_USD"
        ]
    ].to_excel(
        writer,
        sheet_name="Event_Level_Audit",
        index=False
    )


# =============================================================================
# 25. CLOSE DATABASE
# =============================================================================

conn.close()


# =============================================================================
# 26. FINAL MESSAGE
# =============================================================================

print()
print("=" * 92)
print("STAGE 2G.10.1 COMPLETED")
print("=" * 92)

print()
print(f"Validation status : {validation_status}")

print()
print("Output file:")
print(OUTPUT_FILE)

print()
print("Sheets generated:")
print("  1. Validation_Dashboard")
print("  2. Economic_Reconciliation")
print("  3. Rig_Validation")
print("  4. Well_Validation")
print("  5. Root_Cause_Validation")
print("  6. Responsible_Party")
print("  7. Top_Opportunities")
print("  8. Double_Counting_Check")
print("  9. Event_Level_Audit")

print()
print("=" * 92)
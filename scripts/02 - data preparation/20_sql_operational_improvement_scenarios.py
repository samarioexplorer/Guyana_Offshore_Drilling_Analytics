# =============================================================================
# STAGE 2G.10 — OPERATIONAL IMPROVEMENT SCENARIOS & SAVINGS POTENTIAL
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
    / "sql_stage_2G.10_Operational_Improvement_Scenarios"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.10_Operational_Improvement_Scenarios.xlsx"
)


# =============================================================================
# 2. HEADER
# =============================================================================

print("=" * 88)
print("STAGE 2G.10 — OPERATIONAL IMPROVEMENT SCENARIOS & SAVINGS POTENTIAL")
print("=" * 88)

print()
print(f"Project root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")
print()


# =============================================================================
# 3. CONNECT TO SQLITE
# =============================================================================

conn = sqlite3.connect(DB_PATH)


# =============================================================================
# 4. VALIDATE TABLES
# =============================================================================

tables = pd.read_sql_query(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name
    """,
    conn
)

print("Available tables:")
print(tables.to_string(index=False))
print()


# =============================================================================
# 5. LOAD FACT_NPT
# =============================================================================

df = pd.read_sql_query(
    """
    SELECT *
    FROM Fact_NPT
    """,
    conn
)

print(f"NPT rows      : {len(df)}")


# =============================================================================
# 6. VALIDATE REQUIRED COLUMNS
# =============================================================================

required_columns = [
    "Date",
    "Well_ID",
    "Rig_ID",
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "NPT_Events",
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",
    "Severity",
    "Action_Status",
    "Corrective_Action"
]

# Some datasets may not contain NPT_Events as a physical column.
# Create it when necessary because each row represents an NPT event.

if "NPT_Events" not in df.columns:
    df["NPT_Events"] = 1

missing = [
    c for c in required_columns
    if c not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns in Fact_NPT: {missing}"
    )


# =============================================================================
# 7. NUMERIC CLEANUP
# =============================================================================

numeric_columns = [
    "NPT_Events",
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    ).fillna(0)


# =============================================================================
# 8. NORMALIZE TEXT
# =============================================================================

text_columns = [
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Severity",
    "Action_Status",
    "Corrective_Action",
    "Well_ID",
    "Rig_ID"
]

for col in text_columns:
    df[col] = (
        df[col]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
    )


# =============================================================================
# 9. CONTROLLABILITY MODEL
# =============================================================================
#
# Controllability represents how strongly the operator / drilling contractor
# can influence the cause.
#
# 1.00 = highly controllable
# 0.75 = strongly controllable
# 0.50 = partially controllable
# 0.25 = weakly controllable
# 0.10 = largely uncontrollable
#
# The purpose is NOT to claim that the entire impact can be eliminated.
# It is to estimate the portion that is realistically addressable.
# =============================================================================

def classify_controllability(category, root_cause, subcategory):

    category = str(category).lower()
    root = str(root_cause).lower()
    sub = str(subcategory).lower()

    # -------------------------------------------------------------------------
    # Highly controllable
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Strongly controllable
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # Moderately controllable
    # -------------------------------------------------------------------------

    if category == "drilling":
        return "MEDIUM", 0.65

    if category == "logistics":
        return "MEDIUM", 0.60

    if category == "mechanical":
        return "MEDIUM", 0.70

    # -------------------------------------------------------------------------
    # Weather / external conditions
    # -------------------------------------------------------------------------

    if category == "weather":
        return "LOW", 0.30

    # -------------------------------------------------------------------------
    # Personnel
    # -------------------------------------------------------------------------

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

df["Controllability"] = classification.apply(lambda x: x[0])
df["Addressability_Factor"] = classification.apply(lambda x: x[1])


# =============================================================================
# 10. ACTIONABILITY MODEL
# =============================================================================
#
# Historical action status modifies how aggressively savings can be assumed.
#
# Closed / Completed:
#   Existing action has already been implemented.
#
# In Progress:
#   Some improvement potential remains.
#
# Open / Planned:
#   Larger opportunity remains.
#
# Unknown:
#   Conservative factor.
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
# 11. ADDRESSABLE IMPACT
# =============================================================================

df["Addressable_Impact_USD"] = (
    df["Total_Impact_USD"]
    * df["Addressability_Factor"]
    * df["Actionability_Factor"]
)


# =============================================================================
# 12. SAVINGS SCENARIOS
# =============================================================================
#
# Conservative = 20% of addressable impact
# Target       = 40%
# Stretch      = 60%
#
# These are scenario assumptions, not guaranteed savings.
# =============================================================================

CONSERVATIVE_RATE = 0.20
TARGET_RATE = 0.40
STRETCH_RATE = 0.60

df["Conservative_Savings_USD"] = (
    df["Addressable_Impact_USD"]
    * CONSERVATIVE_RATE
)

df["Target_Savings_USD"] = (
    df["Addressable_Impact_USD"]
    * TARGET_RATE
)

df["Stretch_Savings_USD"] = (
    df["Addressable_Impact_USD"]
    * STRETCH_RATE
)


# =============================================================================
# 13. PRIORITY SCORE
# =============================================================================

df["Savings_Priority_Score"] = (
    df["Target_Savings_USD"]
    .rank(pct=True)
    * 100
)


# =============================================================================
# 14. PRIORITY CLASSIFICATION
# =============================================================================

def priority_class(score):

    if score >= 80:
        return "CRITICAL"

    if score >= 60:
        return "HIGH"

    if score >= 40:
        return "MEDIUM"

    return "LOW"


df["Priority"] = df[
    "Savings_Priority_Score"
].apply(priority_class)


# =============================================================================
# 15. ROOT CAUSE SCENARIOS
# =============================================================================

root_cause_scenarios = (
    df.groupby(
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party",
            "Controllability"
        ],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_Events", "sum"),
        NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Conservative_Savings_USD=(
            "Conservative_Savings_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Target_Savings_USD",
            "sum"
        ),
        Stretch_Savings_USD=(
            "Stretch_Savings_USD",
            "sum"
        )
    )
)


root_cause_scenarios["Target_Savings_Pct_of_Impact"] = np.where(
    root_cause_scenarios["Total_Impact_USD"] > 0,
    root_cause_scenarios["Target_Savings_USD"]
    / root_cause_scenarios["Total_Impact_USD"]
    * 100,
    0
)


root_cause_scenarios = root_cause_scenarios.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

root_cause_scenarios.insert(
    0,
    "Priority_Rank",
    range(1, len(root_cause_scenarios) + 1)
)


# =============================================================================
# 16. RIG SCENARIOS
# =============================================================================

rig_scenarios = (
    df.groupby(
        ["Rig_ID", "Controllability"],
        as_index=False
    )
    .agg(
        Wells_Affected=("Well_ID", "nunique"),
        NPT_Events=("NPT_Events", "sum"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Conservative_Savings_USD=(
            "Conservative_Savings_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Target_Savings_USD",
            "sum"
        ),
        Stretch_Savings_USD=(
            "Stretch_Savings_USD",
            "sum"
        )
    )
)

rig_scenarios = rig_scenarios.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

rig_scenarios.insert(
    0,
    "Priority_Rank",
    range(1, len(rig_scenarios) + 1)
)


# =============================================================================
# 17. WELL SCENARIOS
# =============================================================================

well_scenarios = (
    df.groupby(
        ["Well_ID", "Rig_ID"],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_Events", "sum"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Conservative_Savings_USD=(
            "Conservative_Savings_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Target_Savings_USD",
            "sum"
        ),
        Stretch_Savings_USD=(
            "Stretch_Savings_USD",
            "sum"
        )
    )
)

well_scenarios = well_scenarios.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

well_scenarios.insert(
    0,
    "Priority_Rank",
    range(1, len(well_scenarios) + 1)
)


# =============================================================================
# 18. RESPONSIBLE PARTY SCENARIOS
# =============================================================================

responsible_party = (
    df.groupby(
        ["Responsible_Party"],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_Events", "sum"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Conservative_Savings_USD=(
            "Conservative_Savings_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Target_Savings_USD",
            "sum"
        ),
        Stretch_Savings_USD=(
            "Stretch_Savings_USD",
            "sum"
        )
    )
)

responsible_party = responsible_party.sort_values(
    "Target_Savings_USD",
    ascending=False
).reset_index(drop=True)

responsible_party.insert(
    0,
    "Priority_Rank",
    range(1, len(responsible_party) + 1)
)


# =============================================================================
# 19. SCENARIO SUMMARY
# =============================================================================

total_impact = df["Total_Impact_USD"].sum()
addressable_impact = df["Addressable_Impact_USD"].sum()

scenario_summary = pd.DataFrame({
    "Metric": [
        "Total NPT Events",
        "Total NPT Hours",
        "Direct NPT Cost USD",
        "Deferred Cost USD",
        "Total Impact USD",
        "Addressable Impact USD",
        "Addressable Impact % of Total",
        "Conservative Savings USD",
        "Target Savings USD",
        "Stretch Savings USD",
        "Conservative Savings % of Total Impact",
        "Target Savings % of Total Impact",
        "Stretch Savings % of Total Impact",
        "Unique Wells",
        "Unique Rigs",
        "Unique Root Causes",
        "High / Critical Root Cause Opportunities"
    ],
    "Value": [
        df["NPT_Events"].sum(),
        df["Duration_hr"].sum(),
        df["Cost_USD"].sum(),
        df["Deferred_Cost_USD"].sum(),
        total_impact,
        addressable_impact,
        (
            addressable_impact / total_impact * 100
            if total_impact > 0 else 0
        ),
        df["Conservative_Savings_USD"].sum(),
        df["Target_Savings_USD"].sum(),
        df["Stretch_Savings_USD"].sum(),
        (
            df["Conservative_Savings_USD"].sum()
            / total_impact * 100
            if total_impact > 0 else 0
        ),
        (
            df["Target_Savings_USD"].sum()
            / total_impact * 100
            if total_impact > 0 else 0
        ),
        (
            df["Stretch_Savings_USD"].sum()
            / total_impact * 100
            if total_impact > 0 else 0
        ),
        df["Well_ID"].nunique(),
        df["Rig_ID"].nunique(),
        df["Root_Cause"].nunique(),
        (
            root_cause_scenarios[
                root_cause_scenarios["Target_Savings_USD"]
                >= root_cause_scenarios["Target_Savings_USD"]
                .quantile(0.75)
            ].shape[0]
        )
    ]
})


# =============================================================================
# 20. TOP OPPORTUNITIES
# =============================================================================

top_opportunities = (
    df[
        [
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
            "NPT_Events",
            "Duration_hr",
            "Total_Impact_USD",
            "Addressable_Impact_USD",
            "Conservative_Savings_USD",
            "Target_Savings_USD",
            "Stretch_Savings_USD",
            "Savings_Priority_Score",
            "Priority"
        ]
    ]
    .sort_values(
        "Target_Savings_USD",
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
# 21. CONTROLLABILITY SUMMARY
# =============================================================================

controllability_summary = (
    df.groupby(
        ["Controllability", "Addressability_Factor"],
        as_index=False
    )
    .agg(
        NPT_Events=("NPT_Events", "sum"),
        NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum")
    )
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# =============================================================================
# 22. SCENARIO ASSUMPTIONS
# =============================================================================

scenario_assumptions = pd.DataFrame({
    "Scenario": [
        "Conservative",
        "Target",
        "Stretch"
    ],
    "Savings_Rate_on_Addressable_Impact": [
        CONSERVATIVE_RATE,
        TARGET_RATE,
        STRETCH_RATE
    ],
    "Interpretation": [
        "Limited improvement / cautious execution",
        "Realistic operational improvement program",
        "Aggressive improvement with strong execution"
    ]
})


# =============================================================================
# 23. DATA QUALITY CHECK
# =============================================================================

data_quality = pd.DataFrame({
    "Check": [
        "NPT rows",
        "Missing Root Cause",
        "Missing Responsible Party",
        "Missing Action Status",
        "Missing Corrective Action",
        "Negative Total Impact",
        "Negative Duration",
        "Total Impact Reconciliation"
    ],
    "Value": [
        len(df),
        (df["Root_Cause"] == "Unknown").sum(),
        (df["Responsible_Party"] == "Unknown").sum(),
        (df["Action_Status"] == "Unknown").sum(),
        (df["Corrective_Action"] == "Unknown").sum(),
        (df["Total_Impact_USD"] < 0).sum(),
        (df["Duration_hr"] < 0).sum(),
        (
            df["Total_Impact_USD"].sum()
            - (
                df["Cost_USD"].sum()
                + df["Deferred_Cost_USD"].sum()
            )
        )
    ]
})


# =============================================================================
# 24. EXECUTIVE PRINT
# =============================================================================

print()
print("=" * 88)
print("SCENARIO SUMMARY")
print("=" * 88)

print(
    scenario_summary.to_string(index=False)
)

print()
print("=" * 88)
print("TOP 15 SAVINGS OPPORTUNITIES")
print("=" * 88)

print(
    top_opportunities.head(15).to_string(index=False)
)


# =============================================================================
# 25. EXPORT EXCEL
# =============================================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    scenario_summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    root_cause_scenarios.to_excel(
        writer,
        sheet_name="Root_Cause_Scenarios",
        index=False
    )

    rig_scenarios.to_excel(
        writer,
        sheet_name="Rig_Scenarios",
        index=False
    )

    well_scenarios.to_excel(
        writer,
        sheet_name="Well_Scenarios",
        index=False
    )

    responsible_party.to_excel(
        writer,
        sheet_name="Responsible_Party",
        index=False
    )

    top_opportunities.to_excel(
        writer,
        sheet_name="Top_Opportunities",
        index=False
    )

    controllability_summary.to_excel(
        writer,
        sheet_name="Controllability",
        index=False
    )

    scenario_assumptions.to_excel(
        writer,
        sheet_name="Scenario_Assumptions",
        index=False
    )

    data_quality.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# =============================================================================
# 26. CLOSE CONNECTION
# =============================================================================

conn.close()


# =============================================================================
# 27. FINAL MESSAGE
# =============================================================================

print()
print("=" * 88)
print("STAGE 2G.10 COMPLETED SUCCESSFULLY")
print("=" * 88)

print()
print(f"Output file:")
print(OUTPUT_FILE)

print()
print("Sheets generated:")
print("  1. Executive_Summary")
print("  2. Root_Cause_Scenarios")
print("  3. Rig_Scenarios")
print("  4. Well_Scenarios")
print("  5. Responsible_Party")
print("  6. Top_Opportunities")
print("  7. Controllability")
print("  8. Scenario_Assumptions")
print("  9. Data_Quality")

print()
print("Scenario rates:")
print(f"  Conservative : {CONSERVATIVE_RATE:.0%}")
print(f"  Target       : {TARGET_RATE:.0%}")
print(f"  Stretch      : {STRETCH_RATE:.0%}")

print()
print("=" * 88)
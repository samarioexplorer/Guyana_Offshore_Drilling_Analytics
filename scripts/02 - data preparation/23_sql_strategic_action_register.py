import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np


# =============================================================================
# STAGE 2G.11.1
# STRATEGIC ACTION REGISTER & KPI FRAMEWORK
#
# Purpose:
# Convert event-level NPT opportunities into strategic operational actions.
#
# Economic principle:
# Preserve the validated Stage 2G.10.1 economic logic.
# Do NOT create a new economic model.
# =============================================================================


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = (
    PROJECT_ROOT
    / "database"
    / "guyana_drilling.db"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.11.1_Strategic_Action_Register"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.11.1_Strategic_Action_Register.xlsx"
)


print("=" * 80)
print("STAGE 2G.11.1 — STRATEGIC ACTION REGISTER & KPI FRAMEWORK")
print("=" * 80)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")


# =============================================================================
# 1. LOAD DATA
# =============================================================================

conn = sqlite3.connect(DB_PATH)

npt = pd.read_sql_query(
    "SELECT * FROM Fact_NPT",
    conn
)

drilling = pd.read_sql_query(
    "SELECT * FROM Fact_Drilling_Daily_Report",
    conn
)

conn.close()


print(f"\nNPT rows loaded      : {len(npt):,}")
print(f"Drilling rows loaded : {len(drilling):,}")


# =============================================================================
# 2. BASIC VALIDATION
# =============================================================================

required_npt_columns = [
    "NPT_ID",
    "Well_ID",
    "Rig_ID",
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Corrective_Action",
    "Action_Status",
    "Severity",
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD"
]

missing_columns = [
    c for c in required_npt_columns
    if c not in npt.columns
]

if missing_columns:
    raise ValueError(
        "Missing required Fact_NPT columns: "
        + ", ".join(missing_columns)
    )


# =============================================================================
# 3. NUMERIC CLEANUP
# =============================================================================

numeric_columns = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD"
]

for col in numeric_columns:

    npt[col] = pd.to_numeric(
        npt[col],
        errors="coerce"
    ).fillna(0)


# =============================================================================
# 4. NORMALIZE TEXT
# =============================================================================

text_columns = [
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Corrective_Action",
    "Action_Status",
    "Severity"
]

for col in text_columns:

    npt[col] = (
        npt[col]
        .astype(str)
        .str.strip()
    )


# =============================================================================
# 5. STRATEGIC ACTION DEFINITION
#
# One strategic action represents a recurring combination of:
#
# NPT Category
# NPT Subcategory
# Root Cause
# Responsible Party
# Corrective Action
#
# This avoids creating one management action per NPT event.
# =============================================================================

strategic_keys = [
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Corrective_Action"
]


# =============================================================================
# 6. ACTION CLUSTER ID
# =============================================================================

npt["Action_Cluster_Key"] = (
    npt[strategic_keys]
    .fillna("Unknown")
    .astype(str)
    .agg("|".join, axis=1)
)

unique_clusters = (
    npt["Action_Cluster_Key"]
    .drop_duplicates()
    .tolist()
)

cluster_map = {
    key: f"SA-{i:04d}"
    for i, key in enumerate(
        unique_clusters,
        start=1
    )
}

npt["Strategic_Action_ID"] = (
    npt["Action_Cluster_Key"]
    .map(cluster_map)
)


# =============================================================================
# 7. ACTION STATUS
# =============================================================================

def dominant_status(series):

    values = (
        series
        .astype(str)
        .str.strip()
    )

    priority = {
        "Open": 4,
        "Planned": 4,
        "Pending": 4,
        "In Progress": 3,
        "Ongoing": 3,
        "Closed": 2,
        "Completed": 2,
        "Implemented": 2
    }

    ranked = sorted(
        values.unique(),
        key=lambda x: priority.get(x, 1),
        reverse=True
    )

    return ranked[0] if ranked else "Unknown"


# =============================================================================
# 8. PRIORITY
#
# Priority is based on the aggregated strategic action economic impact,
# NPT burden and event frequency.
# =============================================================================

cluster_base = (
    npt.groupby(
        "Strategic_Action_ID"
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum")
    )
    .reset_index()
)


max_impact = max(
    cluster_base["Total_Impact_USD"].max(),
    1
)

max_hours = max(
    cluster_base["Baseline_NPT_Hours"].max(),
    1
)

max_events = max(
    cluster_base["NPT_Events"].max(),
    1
)

cluster_base["Impact_Score"] = (
    cluster_base["Total_Impact_USD"]
    / max_impact
    * 100
)

cluster_base["NPT_Hours_Score"] = (
    cluster_base["Baseline_NPT_Hours"]
    / max_hours
    * 100
)

cluster_base["Frequency_Score"] = (
    cluster_base["NPT_Events"]
    / max_events
    * 100
)

cluster_base["Priority_Score"] = (
    0.50 * cluster_base["Impact_Score"]
    + 0.30 * cluster_base["NPT_Hours_Score"]
    + 0.20 * cluster_base["Frequency_Score"]
)


def priority_label(score):

    if score >= 80:
        return "CRITICAL"

    if score >= 65:
        return "HIGH"

    if score >= 50:
        return "MEDIUM"

    return "LOW"


cluster_base["Priority"] = (
    cluster_base["Priority_Score"]
    .apply(priority_label)
)


# =============================================================================
# 9. STRATEGIC ACTION AGGREGATION
# =============================================================================

strategic_actions = (
    npt.groupby(
        [
            "Strategic_Action_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party",
            "Corrective_Action"
        ]
    )
    .agg(
        NPT_Events=("NPT_ID", "count"),
        Affected_Wells=("Well_ID", "nunique"),
        Affected_Rigs=("Rig_ID", "nunique"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Direct_NPT_Cost_USD=("Cost_USD", "sum"),
        Deferred_Cost_USD=("Deferred_Cost_USD", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Avg_Duration_hr=("Duration_hr", "mean"),
        Action_Status=("Action_Status", dominant_status)
    )
    .reset_index()
)


# =============================================================================
# 10. MERGE PRIORITY
# =============================================================================

strategic_actions = strategic_actions.merge(
    cluster_base[
        [
            "Strategic_Action_ID",
            "Impact_Score",
            "NPT_Hours_Score",
            "Frequency_Score",
            "Priority_Score",
            "Priority"
        ]
    ],
    on="Strategic_Action_ID",
    how="left"
)


# =============================================================================
# 11. ADDRESSABILITY
#
# Same factors used by Stage 2G.10.1.
# =============================================================================

def addressability_factor(row):

    text = " ".join([
        str(row["Root_Cause"]),
        str(row["NPT_Subcategory"]),
        str(row["Corrective_Action"])
    ]).lower()

    category = str(
        row["NPT_Category"]
    ).lower()

    if any(
        x in text
        for x in [
            "preventive maintenance",
            "equipment wear",
            "maintenance",
            "hydraulic failure",
            "electrical failure"
        ]
    ):
        return 0.90

    if any(
        x in text
        for x in [
            "differential sticking",
            "hole cleaning",
            "bit wear",
            "poor hole cleaning"
        ]
    ):
        return 0.80

    if category == "drilling":
        return 0.65

    if category == "logistics":
        return 0.60

    if category == "mechanical":
        return 0.70

    if category == "weather":
        return 0.30

    if category == "personnel":
        return 0.60

    return 0.50


strategic_actions["Addressability_Factor"] = (
    strategic_actions.apply(
        addressability_factor,
        axis=1
    )
)


# =============================================================================
# 12. ACTIONABILITY
# =============================================================================

def actionability_factor(status):

    text = str(status).strip().lower()

    if any(
        x in text
        for x in [
            "closed",
            "completed",
            "implemented"
        ]
    ):
        return 0.50

    if any(
        x in text
        for x in [
            "in progress",
            "ongoing"
        ]
    ):
        return 0.75

    if any(
        x in text
        for x in [
            "open",
            "planned",
            "pending"
        ]
    ):
        return 1.00

    return 0.65


strategic_actions["Actionability_Factor"] = (
    strategic_actions["Action_Status"]
    .apply(actionability_factor)
)


# =============================================================================
# 13. ECONOMIC RECONCILIATION
#
# The event-level economics are aggregated exactly.
# =============================================================================

strategic_actions["Addressable_Impact_USD"] = (
    strategic_actions["Total_Impact_USD"]
    * strategic_actions["Addressability_Factor"]
    * strategic_actions["Actionability_Factor"]
)

strategic_actions["Conservative_Savings_USD"] = (
    strategic_actions["Addressable_Impact_USD"]
    * 0.20
)

strategic_actions["Target_Savings_USD"] = (
    strategic_actions["Addressable_Impact_USD"]
    * 0.40
)

strategic_actions["Stretch_Savings_USD"] = (
    strategic_actions["Addressable_Impact_USD"]
    * 0.60
)


# =============================================================================
# 14. KPI DEFINITION
# =============================================================================

def define_kpi(category, subcategory):

    category = str(category).lower()
    subcategory = str(subcategory).lower()

    if category == "drilling":
        return "NPT Hours + ROP"

    if category == "mechanical":
        return "Mechanical NPT Hours"

    if category == "weather":
        return "Weather NPT Hours"

    if category == "logistics":
        return "Logistics NPT Hours"

    if category == "personnel":
        return "Personnel NPT Hours"

    return "NPT Hours"


strategic_actions["KPI"] = strategic_actions.apply(
    lambda row: define_kpi(
        row["NPT_Category"],
        row["NPT_Subcategory"]
    ),
    axis=1
)


# =============================================================================
# 15. KPI TARGET
# =============================================================================

strategic_actions["Target_NPT_Reduction_pct"] = np.where(
    strategic_actions["Priority"] == "CRITICAL",
    0.40,
    np.where(
        strategic_actions["Priority"] == "HIGH",
        0.35,
        np.where(
            strategic_actions["Priority"] == "MEDIUM",
            0.25,
            0.15
        )
    )
)

strategic_actions["Target_NPT_Hours"] = (
    strategic_actions["Baseline_NPT_Hours"]
    * (
        1
        - strategic_actions["Target_NPT_Reduction_pct"]
    )
)

strategic_actions["KPI_Baseline"] = (
    strategic_actions["Baseline_NPT_Hours"]
)

strategic_actions["KPI_Target"] = (
    strategic_actions["Target_NPT_Hours"]
)


# =============================================================================
# 16. IMPLEMENTATION HORIZON
# =============================================================================

def horizon(priority):

    if priority == "CRITICAL":
        return "0-30 Days"

    if priority == "HIGH":
        return "31-90 Days"

    if priority == "MEDIUM":
        return "91-180 Days"

    return ">180 Days"


strategic_actions["Implementation_Horizon"] = (
    strategic_actions["Priority"]
    .apply(horizon)
)

strategic_actions["Monitoring_Frequency"] = (
    "Weekly"
)


# =============================================================================
# 17. RANK STRATEGIC ACTIONS
# =============================================================================

strategic_actions = strategic_actions.sort_values(
    [
        "Priority_Score",
        "Target_Savings_USD"
    ],
    ascending=False
).reset_index(drop=True)


strategic_actions["Action_Rank"] = (
    strategic_actions.index + 1
)


# =============================================================================
# 18. ACTION DETAIL / EVENT AUDIT
# =============================================================================

event_audit = npt[
    [
        "NPT_ID",
        "Well_ID",
        "Rig_ID",
        "NPT_Category",
        "NPT_Subcategory",
        "Root_Cause",
        "Responsible_Party",
        "Corrective_Action",
        "Action_Status",
        "Duration_hr",
        "Cost_USD",
        "Deferred_Cost_USD",
        "Total_Impact_USD",
        "Strategic_Action_ID"
    ]
].copy()


# =============================================================================
# 19. RIG ACTION PLAN
# =============================================================================

rig_action_plan = (
    npt.merge(
        strategic_actions[
            [
                "Strategic_Action_ID",
                "Target_Savings_USD",
                "Priority"
            ]
        ],
        on="Strategic_Action_ID",
        how="left"
    )
    .groupby("Rig_ID")
    .agg(
        Strategic_Actions=(
            "Strategic_Action_ID",
            "nunique"
        ),
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum")
    )
    .reset_index()
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# =============================================================================
# 20. WELL ACTION PLAN
# =============================================================================

well_action_plan = (
    npt.merge(
        strategic_actions[
            [
                "Strategic_Action_ID",
                "Target_Savings_USD",
                "Priority"
            ]
        ],
        on="Strategic_Action_ID",
        how="left"
    )
    .groupby(
        [
            "Well_ID",
            "Rig_ID"
        ]
    )
    .agg(
        Strategic_Actions=(
            "Strategic_Action_ID",
            "nunique"
        ),
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum")
    )
    .reset_index()
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# =============================================================================
# 21. ROOT CAUSE ACTION PLAN
# =============================================================================

root_cause_action_plan = (
    strategic_actions
    .groupby(
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause"
        ]
    )
    .agg(
        Strategic_Actions=(
            "Strategic_Action_ID",
            "nunique"
        ),
        NPT_Events=("NPT_Events", "sum"),
        Baseline_NPT_Hours=(
            "Baseline_NPT_Hours",
            "sum"
        ),
        Total_Impact_USD=(
            "Total_Impact_USD",
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
    .reset_index()
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# =============================================================================
# 22. RESPONSIBLE PARTY
# =============================================================================

responsible_party = (
    strategic_actions
    .groupby("Responsible_Party")
    .agg(
        Strategic_Actions=(
            "Strategic_Action_ID",
            "nunique"
        ),
        NPT_Events=("NPT_Events", "sum"),
        Baseline_NPT_Hours=(
            "Baseline_NPT_Hours",
            "sum"
        ),
        Total_Impact_USD=(
            "Total_Impact_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Target_Savings_USD",
            "sum"
        )
    )
    .reset_index()
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# =============================================================================
# 23. KPI FRAMEWORK
# =============================================================================

total_npt_hours = (
    strategic_actions["Baseline_NPT_Hours"].sum()
)

total_impact = (
    strategic_actions["Total_Impact_USD"].sum()
)

target_savings = (
    strategic_actions["Target_Savings_USD"].sum()
)

critical_actions = (
    strategic_actions["Priority"]
    .eq("CRITICAL")
    .sum()
)

high_actions = (
    strategic_actions["Priority"]
    .eq("HIGH")
    .sum()
)


kpi_framework = pd.DataFrame([
    {
        "KPI": "Total NPT Hours",
        "Definition": "Total non-productive drilling hours",
        "Baseline": total_npt_hours,
        "Target": total_npt_hours * 0.65,
        "Target_Reduction_pct": 0.35,
        "Frequency": "Weekly",
        "Owner": "Drilling Operations"
    },
    {
        "KPI": "Economic Impact",
        "Definition": "Total NPT economic impact",
        "Baseline": total_impact,
        "Target": total_impact * 0.65,
        "Target_Reduction_pct": 0.35,
        "Frequency": "Monthly",
        "Owner": "Operations Management"
    },
    {
        "KPI": "Target Savings",
        "Definition": "Validated expected savings",
        "Baseline": 0,
        "Target": target_savings,
        "Target_Reduction_pct": None,
        "Frequency": "Monthly",
        "Owner": "Operations Management"
    },
    {
        "KPI": "Strategic Action Closure Rate",
        "Definition": "Closed strategic actions / total actions",
        "Baseline": (
            strategic_actions[
                "Action_Status"
            ]
            .astype(str)
            .str.lower()
            .eq("closed")
            .mean()
        ),
        "Target": 0.90,
        "Target_Reduction_pct": None,
        "Frequency": "Weekly",
        "Owner": "Action Owners"
    },
    {
        "KPI": "Critical Action Closure",
        "Definition": "Closed critical actions / critical actions",
        "Baseline": (
            (
                strategic_actions["Priority"]
                .eq("CRITICAL")
            )
            &
            (
                strategic_actions[
                    "Action_Status"
                ]
                .astype(str)
                .str.lower()
                .eq("closed")
            )
        ).sum()
        /
        max(critical_actions, 1),
        "Target": 0.90,
        "Target_Reduction_pct": None,
        "Frequency": "Weekly",
        "Owner": "Operations Management"
    }
])


# =============================================================================
# 24. IMPLEMENTATION ROADMAP
# =============================================================================

roadmap = (
    strategic_actions
    .groupby("Implementation_Horizon")
    .agg(
        Strategic_Actions=(
            "Strategic_Action_ID",
            "nunique"
        ),
        NPT_Events=("NPT_Events", "sum"),
        Baseline_NPT_Hours=(
            "Baseline_NPT_Hours",
            "sum"
        ),
        Total_Impact_USD=(
            "Total_Impact_USD",
            "sum"
        ),
        Target_Savings_USD=(
            "Target_Savings_USD",
            "sum"
        )
    )
    .reset_index()
)

roadmap_order = {
    "0-30 Days": 1,
    "31-90 Days": 2,
    "91-180 Days": 3,
    ">180 Days": 4
}

roadmap["Sort_Order"] = (
    roadmap["Implementation_Horizon"]
    .map(roadmap_order)
)

roadmap = (
    roadmap
    .sort_values("Sort_Order")
    .drop(columns="Sort_Order")
)


# =============================================================================
# 25. SAVINGS BY ACTION
# =============================================================================

savings_by_action = strategic_actions[
    [
        "Action_Rank",
        "Strategic_Action_ID",
        "NPT_Category",
        "NPT_Subcategory",
        "Root_Cause",
        "Responsible_Party",
        "Corrective_Action",
        "Priority",
        "NPT_Events",
        "Baseline_NPT_Hours",
        "Total_Impact_USD",
        "Addressable_Impact_USD",
        "Conservative_Savings_USD",
        "Target_Savings_USD",
        "Stretch_Savings_USD"
    ]
].copy()


# =============================================================================
# 26. EXECUTIVE SUMMARY
# =============================================================================

summary = pd.DataFrame(
    [
        [
            "NPT Events",
            len(npt)
        ],
        [
            "Strategic Actions",
            len(strategic_actions)
        ],
        [
            "Action Reduction",
            f"{len(npt) - len(strategic_actions):,}"
        ],
        [
            "NPT Hours",
            total_npt_hours
        ],
        [
            "Total Economic Impact USD",
            total_impact
        ],
        [
            "Target Savings USD",
            target_savings
        ],
        [
            "Critical Strategic Actions",
            critical_actions
        ],
        [
            "High Strategic Actions",
            high_actions
        ],
        [
            "Affected Wells",
            npt["Well_ID"].nunique()
        ],
        [
            "Affected Rigs",
            npt["Rig_ID"].nunique()
        ]
    ],
    columns=[
        "Metric",
        "Value"
    ]
)


# =============================================================================
# 27. DATA QUALITY
# =============================================================================

dq = []


dq.append(
    {
        "Check": "NPT rows",
        "Value": len(npt),
        "Status": (
            "PASS"
            if len(npt) > 0
            else "FAIL"
        )
    }
)


dq.append(
    {
        "Check": "Strategic Action IDs",
        "Value": strategic_actions[
            "Strategic_Action_ID"
        ].nunique(),
        "Status": (
            "PASS"
            if strategic_actions[
                "Strategic_Action_ID"
            ].nunique()
            == len(strategic_actions)
            else "FAIL"
        )
    }
)


dq.append(
    {
        "Check": "Duplicate NPT IDs",
        "Value": npt["NPT_ID"].duplicated().sum(),
        "Status": (
            "PASS"
            if npt["NPT_ID"].duplicated().sum() == 0
            else "FAIL"
        )
    }
)


dq.append(
    {
        "Check": "Missing Responsible Party",
        "Value": npt[
            "Responsible_Party"
        ].isna().sum(),
        "Status": (
            "PASS"
            if npt[
                "Responsible_Party"
            ].isna().sum() == 0
            else "FAIL"
        )
    }
)


dq.append(
    {
        "Check": "Missing Corrective Action",
        "Value": npt[
            "Corrective_Action"
        ].isna().sum(),
        "Status": (
            "PASS"
            if npt[
                "Corrective_Action"
            ].isna().sum() == 0
            else "FAIL"
        )
    }
)


dq.append(
    {
        "Check": "Economic Reconciliation",
        "Value": (
            strategic_actions[
                "Total_Impact_USD"
            ].sum()
            - npt[
                "Total_Impact_USD"
            ].sum()
        ),
        "Status": (
            "PASS"
            if abs(
                strategic_actions[
                    "Total_Impact_USD"
                ].sum()
                -
                npt[
                    "Total_Impact_USD"
                ].sum()
            ) < 0.01
            else "FAIL"
        )
    }
)


dq.append(
    {
        "Check": "Target Savings Non-Negative",
        "Value": (
            strategic_actions[
                "Target_Savings_USD"
            ] < 0
        ).sum(),
        "Status": (
            "PASS"
            if (
                strategic_actions[
                    "Target_Savings_USD"
                ] < 0
            ).sum() == 0
            else "FAIL"
        )
    }
)


dq.append(
    {
        "Check": "Target NPT Non-Negative",
        "Value": (
            strategic_actions[
                "Target_NPT_Hours"
            ] < 0
        ).sum(),
        "Status": (
            "PASS"
            if (
                strategic_actions[
                    "Target_NPT_Hours"
                ] < 0
            ).sum() == 0
            else "FAIL"
        )
    }
)


data_quality = pd.DataFrame(dq)


# =============================================================================
# 28. WRITE EXCEL
# =============================================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    strategic_actions.to_excel(
        writer,
        sheet_name="Strategic_Action_Register",
        index=False
    )

    strategic_actions.to_excel(
        writer,
        sheet_name="Action_Detail",
        index=False
    )

    rig_action_plan.to_excel(
        writer,
        sheet_name="Rig_Action_Plan",
        index=False
    )

    well_action_plan.to_excel(
        writer,
        sheet_name="Well_Action_Plan",
        index=False
    )

    root_cause_action_plan.to_excel(
        writer,
        sheet_name="Root_Cause_Action_Plan",
        index=False
    )

    responsible_party.to_excel(
        writer,
        sheet_name="Responsible_Party",
        index=False
    )

    kpi_framework.to_excel(
        writer,
        sheet_name="KPI_Framework",
        index=False
    )

    roadmap.to_excel(
        writer,
        sheet_name="Implementation_Roadmap",
        index=False
    )

    savings_by_action.to_excel(
        writer,
        sheet_name="Savings_By_Action",
        index=False
    )

    event_audit.to_excel(
        writer,
        sheet_name="Event_Audit",
        index=False
    )

    data_quality.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# =============================================================================
# 29. FINAL OUTPUT
# =============================================================================

print("\n" + "=" * 80)
print("STAGE 2G.11.1 — RESULTS")
print("=" * 80)

print(
    f"\nNPT events                : "
    f"{len(npt):,}"
)

print(
    f"Strategic actions        : "
    f"{len(strategic_actions):,}"
)

print(
    f"Action reduction         : "
    f"{len(npt) - len(strategic_actions):,}"
)

print(
    f"Baseline NPT hours       : "
    f"{total_npt_hours:,.2f}"
)

print(
    f"Total economic impact    : "
    f"${total_impact:,.2f}"
)

print(
    f"Target savings           : "
    f"${target_savings:,.2f}"
)

print(
    f"Critical actions         : "
    f"{critical_actions:,}"
)

print(
    f"High actions             : "
    f"{high_actions:,}"
)

print("\nTop 10 Strategic Actions:")

print(
    strategic_actions[
        [
            "Action_Rank",
            "Strategic_Action_ID",
            "NPT_Category",
            "Root_Cause",
            "Responsible_Party",
            "NPT_Events",
            "Baseline_NPT_Hours",
            "Target_Savings_USD",
            "Priority"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


print("\nData Quality:")
print(
    data_quality.to_string(index=False)
)

print("\nOutput file:")
print(OUTPUT_FILE)

print("\n" + "=" * 80)
print("STAGE 2G.11.1 COMPLETED")
print("=" * 80)
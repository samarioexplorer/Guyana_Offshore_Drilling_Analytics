import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np


# ================================================================
# STAGE 2G.11
# OPERATIONAL IMPROVEMENT ACTION PLAN & KPI FRAMEWORK
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "outputs"
    / "sql_stage_2G.11_Operational_Improvement_Action_Plan"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "sql_stage_2G.11_Operational_Improvement_Action_Plan.xlsx"
)

print("=" * 80)
print("STAGE 2G.11 — OPERATIONAL IMPROVEMENT ACTION PLAN & KPI FRAMEWORK")
print("=" * 80)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_FILE}")


# ================================================================
# 1. LOAD DATABASE
# ================================================================

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

print(f"\nNPT rows loaded       : {len(npt):,}")
print(f"Drilling rows loaded  : {len(drilling):,}")


# ================================================================
# 2. NUMERIC CLEANUP
# ================================================================

numeric_cols = [
    "Duration_hr",
    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD"
]

for col in numeric_cols:
    if col in npt.columns:
        npt[col] = pd.to_numeric(
            npt[col],
            errors="coerce"
        ).fillna(0)


# ================================================================
# 3. CONTROLLABILITY
# ================================================================

def addressability_factor(row):

    text = " ".join([
        str(row.get("Root_Cause", "")),
        str(row.get("NPT_Subcategory", "")),
        str(row.get("Corrective_Action", ""))
    ]).lower()

    category = str(
        row.get("NPT_Category", "")
    ).lower()

    if any(x in text for x in [
        "preventive maintenance",
        "equipment wear",
        "maintenance",
        "hydraulic failure",
        "electrical failure"
    ]):
        return 0.90

    if any(x in text for x in [
        "differential sticking",
        "hole cleaning",
        "bit wear",
        "poor hole cleaning"
    ]):
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


# ================================================================
# 4. ACTIONABILITY
# ================================================================

def actionability_factor(status):

    text = str(status).strip().lower()

    if any(x in text for x in [
        "closed",
        "completed",
        "implemented"
    ]):
        return 0.50

    if any(x in text for x in [
        "in progress",
        "ongoing"
    ]):
        return 0.75

    if any(x in text for x in [
        "open",
        "planned",
        "pending"
    ]):
        return 1.00

    return 0.65


# ================================================================
# 5. APPLY ECONOMIC MODEL
# ================================================================

npt["Addressability_Factor"] = npt.apply(
    addressability_factor,
    axis=1
)

npt["Actionability_Factor"] = npt[
    "Action_Status"
].apply(actionability_factor)

npt["Addressable_Impact_USD"] = (
    npt["Total_Impact_USD"]
    * npt["Addressability_Factor"]
    * npt["Actionability_Factor"]
)

npt["Conservative_Savings_USD"] = (
    npt["Addressable_Impact_USD"] * 0.20
)

npt["Target_Savings_USD"] = (
    npt["Addressable_Impact_USD"] * 0.40
)

npt["Stretch_Savings_USD"] = (
    npt["Addressable_Impact_USD"] * 0.60
)


# ================================================================
# 6. PRIORITY SCORE
# ================================================================

severity_map = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}

npt["Severity_Score"] = (
    npt["Severity"]
    .astype(str)
    .str.lower()
    .map(severity_map)
    .fillna(2)
)


# Normalize components
max_impact = max(npt["Total_Impact_USD"].max(), 1)
max_hours = max(npt["Duration_hr"].max(), 1)
max_severity = 4

npt["Impact_Score"] = (
    npt["Total_Impact_USD"] / max_impact * 100
)

npt["NPT_Hours_Score"] = (
    npt["Duration_hr"] / max_hours * 100
)

npt["Severity_Component"] = (
    npt["Severity_Score"] / max_severity * 100
)

npt["Priority_Score"] = (
    0.50 * npt["Impact_Score"]
    + 0.30 * npt["NPT_Hours_Score"]
    + 0.20 * npt["Severity_Component"]
)


def priority(score):

    if score >= 80:
        return "CRITICAL"

    if score >= 65:
        return "HIGH"

    if score >= 50:
        return "MEDIUM"

    return "LOW"


npt["Priority"] = npt[
    "Priority_Score"
].apply(priority)


# ================================================================
# 7. TARGET NPT REDUCTION
# ================================================================

npt["Target_NPT_Reduction_pct"] = np.where(
    npt["Priority"] == "CRITICAL",
    0.40,
    np.where(
        npt["Priority"] == "HIGH",
        0.35,
        np.where(
            npt["Priority"] == "MEDIUM",
            0.25,
            0.15
        )
    )
)

npt["Baseline_NPT_Hours"] = npt["Duration_hr"]

npt["Target_NPT_Hours"] = (
    npt["Baseline_NPT_Hours"]
    * (
        1 - npt["Target_NPT_Reduction_pct"]
    )
)


# ================================================================
# 8. KPI ASSIGNMENT
# ================================================================

def assign_kpi(row):

    category = str(
        row["NPT_Category"]
    ).lower()

    subcategory = str(
        row["NPT_Subcategory"]
    ).lower()

    if category == "drilling":
        return "NPT Hours + ROP"

    if "weather" in category:
        return "Weather NPT Hours"

    if category == "mechanical":
        return "Mechanical NPT Hours"

    if category == "logistics":
        return "Logistics NPT Hours"

    if category == "personnel":
        return "Personnel NPT Hours"

    return "NPT Hours"


npt["KPI"] = npt.apply(
    assign_kpi,
    axis=1
)

npt["KPI_Baseline"] = npt["Baseline_NPT_Hours"]

npt["KPI_Target"] = npt["Target_NPT_Hours"]


# ================================================================
# 9. IMPLEMENTATION HORIZON
# ================================================================

def implementation_horizon(priority):

    if priority == "CRITICAL":
        return "0-30 Days"

    if priority == "HIGH":
        return "31-90 Days"

    if priority == "MEDIUM":
        return "91-180 Days"

    return ">180 Days"


npt["Implementation_Horizon"] = (
    npt["Priority"]
    .apply(implementation_horizon)
)

npt["Monitoring_Frequency"] = "Weekly"


# ================================================================
# 10. ACTION ID
# ================================================================

npt = npt.sort_values(
    [
        "Priority_Score",
        "Target_Savings_USD"
    ],
    ascending=False
).reset_index(drop=True)

npt["Action_ID"] = [
    f"ACT-{i:05d}"
    for i in range(1, len(npt) + 1)
]


# ================================================================
# 11. ACTION REGISTER
# ================================================================

action_columns = [
    "Action_ID",
    "NPT_ID",
    "Rig_ID",
    "Well_ID",
    "NPT_Category",
    "NPT_Subcategory",
    "Root_Cause",
    "Responsible_Party",
    "Corrective_Action",
    "Action_Status",
    "Severity",

    "Duration_hr",
    "Baseline_NPT_Hours",
    "Target_NPT_Reduction_pct",
    "Target_NPT_Hours",

    "Cost_USD",
    "Deferred_Cost_USD",
    "Total_Impact_USD",

    "Addressability_Factor",
    "Actionability_Factor",
    "Addressable_Impact_USD",

    "Conservative_Savings_USD",
    "Target_Savings_USD",
    "Stretch_Savings_USD",

    "KPI",
    "KPI_Baseline",
    "KPI_Target",

    "Priority_Score",
    "Priority",
    "Implementation_Horizon",
    "Monitoring_Frequency"
]

action_register = npt[
    [c for c in action_columns if c in npt.columns]
].copy()


# ================================================================
# 12. RIG ACTION PLAN
# ================================================================

rig_plan = (
    npt.groupby("Rig_ID")
    .agg(
        Actions=("Action_ID", "count"),
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Stretch_Savings_USD=("Stretch_Savings_USD", "sum")
    )
    .reset_index()
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# ================================================================
# 13. WELL ACTION PLAN
# ================================================================

well_plan = (
    npt.groupby(
        ["Well_ID", "Rig_ID"]
    )
    .agg(
        Actions=("Action_ID", "count"),
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Stretch_Savings_USD=("Stretch_Savings_USD", "sum")
    )
    .reset_index()
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# ================================================================
# 14. ROOT CAUSE ACTION PLAN
# ================================================================

root_cause_plan = (
    npt.groupby(
        [
            "NPT_Category",
            "NPT_Subcategory",
            "Root_Cause",
            "Responsible_Party"
        ]
    )
    .agg(
        Actions=("Action_ID", "count"),
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Stretch_Savings_USD=("Stretch_Savings_USD", "sum")
    )
    .reset_index()
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# ================================================================
# 15. RESPONSIBLE PARTY
# ================================================================

responsible_party = (
    npt.groupby("Responsible_Party")
    .agg(
        Actions=("Action_ID", "count"),
        NPT_Events=("NPT_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Addressable_Impact_USD=("Addressable_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum"),
        Stretch_Savings_USD=("Stretch_Savings_USD", "sum")
    )
    .reset_index()
    .sort_values(
        "Target_Savings_USD",
        ascending=False
    )
)


# ================================================================
# 16. KPI FRAMEWORK
# ================================================================

total_npt_hours = npt["Duration_hr"].sum()
total_impact = npt["Total_Impact_USD"].sum()
target_savings = npt["Target_Savings_USD"].sum()

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
        "KPI": "NPT Cost Impact",
        "Definition": "Total NPT economic impact",
        "Baseline": total_impact,
        "Target": total_impact * 0.65,
        "Target_Reduction_pct": 0.35,
        "Frequency": "Monthly",
        "Owner": "Operations Management"
    },
    {
        "KPI": "Target Savings",
        "Definition": "Expected savings from action plan",
        "Baseline": 0,
        "Target": target_savings,
        "Target_Reduction_pct": None,
        "Frequency": "Monthly",
        "Owner": "Operations Management"
    },
    {
        "KPI": "Action Closure Rate",
        "Definition": "Closed actions / total actions",
        "Baseline": (
            (npt["Action_Status"]
             .astype(str)
             .str.lower()
             .eq("closed")
             ).mean()
        ),
        "Target": 0.90,
        "Target_Reduction_pct": None,
        "Frequency": "Weekly",
        "Owner": "Action Owners"
    },
    {
        "KPI": "Critical Action Closure",
        "Definition": "Critical actions closed / critical actions",
        "Baseline": (
            (
                (npt["Priority"] == "CRITICAL")
                &
                (
                    npt["Action_Status"]
                    .astype(str)
                    .str.lower()
                    .eq("closed")
                )
            ).sum()
            /
            max(
                (npt["Priority"] == "CRITICAL").sum(),
                1
            )
        ),
        "Target": 0.90,
        "Target_Reduction_pct": None,
        "Frequency": "Weekly",
        "Owner": "Operations Management"
    }
])


# ================================================================
# 17. PRIORITY MATRIX
# ================================================================

priority_matrix = (
    npt.groupby("Priority")
    .agg(
        Actions=("Action_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum")
    )
    .reset_index()
)

priority_order = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4
}

priority_matrix["Sort_Order"] = (
    priority_matrix["Priority"]
    .map(priority_order)
)

priority_matrix = priority_matrix.sort_values(
    "Sort_Order"
).drop(columns="Sort_Order")


# ================================================================
# 18. SAVINGS BY ACTION
# ================================================================

savings_by_action = action_register[
    [
        "Action_ID",
        "Rig_ID",
        "Well_ID",
        "NPT_Category",
        "Root_Cause",
        "Responsible_Party",
        "Priority",
        "Total_Impact_USD",
        "Addressable_Impact_USD",
        "Conservative_Savings_USD",
        "Target_Savings_USD",
        "Stretch_Savings_USD"
    ]
].sort_values(
    "Target_Savings_USD",
    ascending=False
)


# ================================================================
# 19. IMPLEMENTATION ROADMAP
# ================================================================

roadmap = (
    npt.groupby("Implementation_Horizon")
    .agg(
        Actions=("Action_ID", "count"),
        Baseline_NPT_Hours=("Duration_hr", "sum"),
        Total_Impact_USD=("Total_Impact_USD", "sum"),
        Target_Savings_USD=("Target_Savings_USD", "sum")
    )
    .reset_index()
)

horizon_order = {
    "0-30 Days": 1,
    "31-90 Days": 2,
    "91-180 Days": 3,
    ">180 Days": 4
}

roadmap["Sort_Order"] = (
    roadmap["Implementation_Horizon"]
    .map(horizon_order)
)

roadmap = roadmap.sort_values(
    "Sort_Order"
).drop(columns="Sort_Order")


# ================================================================
# 20. DATA QUALITY
# ================================================================

dq = []

dq.append({
    "Check": "NPT rows",
    "Value": len(npt),
    "Status": "PASS" if len(npt) > 0 else "FAIL"
})

dq.append({
    "Check": "Unique Action IDs",
    "Value": npt["Action_ID"].nunique(),
    "Status": (
        "PASS"
        if npt["Action_ID"].nunique() == len(npt)
        else "FAIL"
    )
})

dq.append({
    "Check": "Duplicate NPT IDs",
    "Value": npt["NPT_ID"].duplicated().sum(),
    "Status": (
        "PASS"
        if npt["NPT_ID"].duplicated().sum() == 0
        else "FAIL"
    )
})

dq.append({
    "Check": "Negative Target Savings",
    "Value": (
        npt["Target_Savings_USD"] < 0
    ).sum(),
    "Status": (
        "PASS"
        if (npt["Target_Savings_USD"] < 0).sum() == 0
        else "FAIL"
    )
})

dq.append({
    "Check": "Missing Responsible Party",
    "Value": npt["Responsible_Party"].isna().sum(),
    "Status": (
        "PASS"
        if npt["Responsible_Party"].isna().sum() == 0
        else "FAIL"
    )
})

dq.append({
    "Check": "Missing Corrective Action",
    "Value": npt["Corrective_Action"].isna().sum(),
    "Status": (
        "PASS"
        if npt["Corrective_Action"].isna().sum() == 0
        else "FAIL"
    )
})

dq.append({
    "Check": "Negative Target NPT",
    "Value": (
        npt["Target_NPT_Hours"] < 0
    ).sum(),
    "Status": (
        "PASS"
        if (npt["Target_NPT_Hours"] < 0).sum() == 0
        else "FAIL"
    )
})

data_quality = pd.DataFrame(dq)


# ================================================================
# 21. EXECUTIVE SUMMARY
# ================================================================

summary = pd.DataFrame([
    ["NPT Events", len(npt)],
    ["NPT Hours", npt["Duration_hr"].sum()],
    ["Total Impact USD", npt["Total_Impact_USD"].sum()],
    ["Addressable Impact USD", npt["Addressable_Impact_USD"].sum()],
    ["Target Savings USD", npt["Target_Savings_USD"].sum()],
    ["Stretch Savings USD", npt["Stretch_Savings_USD"].sum()],
    ["Unique Wells", npt["Well_ID"].nunique()],
    ["Unique Rigs", npt["Rig_ID"].nunique()],
    ["Critical Actions", (npt["Priority"] == "CRITICAL").sum()],
    ["High Actions", (npt["Priority"] == "HIGH").sum()],
    ["Medium Actions", (npt["Priority"] == "MEDIUM").sum()],
    ["Low Actions", (npt["Priority"] == "LOW").sum()],
    [
        "Overall Status",
        "PASS"
        if all(data_quality["Status"] == "PASS")
        else "REVIEW"
    ]
], columns=["Metric", "Value"])


# ================================================================
# 22. WRITE EXCEL
# ================================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    summary.to_excel(
        writer,
        sheet_name="Executive_Summary",
        index=False
    )

    action_register.to_excel(
        writer,
        sheet_name="Action_Register",
        index=False
    )

    rig_plan.to_excel(
        writer,
        sheet_name="Rig_Action_Plan",
        index=False
    )

    well_plan.to_excel(
        writer,
        sheet_name="Well_Action_Plan",
        index=False
    )

    root_cause_plan.to_excel(
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

    priority_matrix.to_excel(
        writer,
        sheet_name="Priority_Matrix",
        index=False
    )

    savings_by_action.to_excel(
        writer,
        sheet_name="Savings_By_Action",
        index=False
    )

    roadmap.to_excel(
        writer,
        sheet_name="Implementation_Roadmap",
        index=False
    )

    data_quality.to_excel(
        writer,
        sheet_name="Data_Quality",
        index=False
    )


# ================================================================
# 23. FINAL CONSOLE OUTPUT
# ================================================================

print("\n" + "=" * 80)
print("STAGE 2G.11 — RESULTS")
print("=" * 80)

print(f"\nActions generated        : {len(action_register):,}")
print(f"Baseline NPT hours       : {npt['Duration_hr'].sum():,.2f}")
print(
    f"Total economic impact    : "
    f"${npt['Total_Impact_USD'].sum():,.2f}"
)
print(
    f"Addressable impact       : "
    f"${npt['Addressable_Impact_USD'].sum():,.2f}"
)
print(
    f"Target savings           : "
    f"${npt['Target_Savings_USD'].sum():,.2f}"
)
print(
    f"Stretch savings          : "
    f"${npt['Stretch_Savings_USD'].sum():,.2f}"
)

print(
    f"\nCritical actions         : "
    f"{(npt['Priority'] == 'CRITICAL').sum():,}"
)

print(
    f"High actions             : "
    f"{(npt['Priority'] == 'HIGH').sum():,}"
)

print(
    f"Medium actions           : "
    f"{(npt['Priority'] == 'MEDIUM').sum():,}"
)

print(
    f"Low actions              : "
    f"{(npt['Priority'] == 'LOW').sum():,}"
)

print("\nData Quality:")
print(data_quality.to_string(index=False))

print(f"\nOutput file:")
print(OUTPUT_FILE)

print("\n" + "=" * 80)
print("STAGE 2G.11 COMPLETED")
print("=" * 80)
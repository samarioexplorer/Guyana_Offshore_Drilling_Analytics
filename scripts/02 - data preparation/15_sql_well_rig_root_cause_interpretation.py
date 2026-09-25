"""
Stage 2G.6B — Well × Rig × Root Cause Engineering Interpretation

Project: Guyana Offshore Drilling Analytics

Purpose
-------
Turn the Stage 2G.6 SQL outputs into an engineering interpretation layer.

The analysis answers:
    1. Which wells generate the most NPT?
    2. Which rigs generate the most NPT?
    3. Which root causes dominate?
    4. Which Well × Rig × Root Cause combinations are hotspots?
    5. Is the signal more concentrated by Well or by Rig?
    6. Which causes are systemic versus concentrated?
    7. What percentage of impact is represented by the Pareto leaders?
    8. Which high-severity issues deserve priority?

IMPORTANT
---------
This is observational analytics. A high NPT value associated with a rig or
well does NOT by itself prove causation. The script labels results as
"evidence / association" and recommends engineering review before causal
conclusions.

Run from the project root:
    python scripts/15_sql_well_rig_root_cause_interpretation.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_PATH = OUTPUT_DIR / "Stage_2G6B_Engineering_Interpretation.txt"

SEVERITY_WEIGHT = {
    "LOW": 1.0,
    "MEDIUM": 2.0,
    "HIGH": 3.0,
}


def fail(message: str) -> None:
    print(f"\nERROR: {message}\n")
    sys.exit(1)


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def norm(value) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def find_col(columns, aliases):
    lookup = {norm(c): c for c in columns}
    for alias in aliases:
        if norm(alias) in lookup:
            return lookup[norm(alias)]
    return None


def table_columns(conn, table):
    rows = conn.execute(
        f"PRAGMA table_info({q(table)})"
    ).fetchall()
    return [r[1] for r in rows]


def find_table(conn, aliases):
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()

    lookup = {norm(r[0]): r[0] for r in rows}
    for alias in aliases:
        if norm(alias) in lookup:
            return lookup[norm(alias)]
    return None


def load_fact_npt(conn, table):
    cols = table_columns(conn, table)

    aliases = {
        "NPT_ID": ["NPT_ID", "NPTID", "ID"],
        "Date": ["Date", "NPT_Date", "Event_Date"],
        "Well_ID": ["Well_ID", "WellID", "Well"],
        "Rig_ID": ["Rig_ID", "RigID", "Rig"],
        "NPT_Category": ["NPT_Category", "Category", "NPTCategory"],
        "NPT_Subcategory": [
            "NPT_Subcategory",
            "Subcategory",
            "NPTSubcategory",
        ],
        "Root_Cause": [
            "Root_Cause",
            "RootCause",
            "Cause",
            "NPT_Root_Cause",
        ],
        "Duration_hr": [
            "Duration_hr",
            "NPT_Hours",
            "Duration_Hours",
            "Duration",
        ],
        "Severity": ["Severity", "NPT_Severity"],
        "NPT_Rig_Cost_USD": [
            "NPT_Rig_Cost_USD",
            "NPT_Cost_USD",
            "Cost_USD",
            "Cost",
        ],
        "Deferred_Production_Impact_USD": [
            "Deferred_Production_Impact_USD",
            "Deferred_Production_USD",
            "Deferred_Production_Cost_USD",
            "Deferred_Production",
            "Production_Loss_USD",
        ],
        "Total_Impact_USD": [
            "Total_Impact_USD",
            "Total_Impact",
            "Economic_Impact_USD",
        ],
    }

    selected = {}
    for target, aliases_for_target in aliases.items():
        selected[target] = find_col(cols, aliases_for_target)

    required = [
        "Well_ID",
        "Rig_ID",
        "NPT_Category",
        "NPT_Subcategory",
        "Duration_hr",
        "Severity",
    ]

    missing = [c for c in required if not selected[c]]
    if missing:
        fail(
            "FACT_NPT missing required columns: "
            + ", ".join(missing)
            + f"\nAvailable columns: {', '.join(cols)}"
        )

    parts = []
    for target, source in selected.items():
        if source:
            parts.append(f"{q(source)} AS {q(target)}")
        elif target == "NPT_Rig_Cost_USD":
            parts.append("0.0 AS NPT_Rig_Cost_USD")
        elif target == "Deferred_Production_Impact_USD":
            parts.append("0.0 AS Deferred_Production_Impact_USD")
        elif target == "Total_Impact_USD":
            parts.append("0.0 AS Total_Impact_USD")

    df = pd.read_sql_query(
        f"SELECT {', '.join(parts)} FROM {q(table)}",
        conn,
    )

    df["Well_ID"] = df["Well_ID"].astype(str).str.strip()
    df["Rig_ID"] = df["Rig_ID"].astype(str).str.strip()
    df["NPT_Category"] = df["NPT_Category"].fillna("Unknown").astype(str).str.strip()
    df["NPT_Subcategory"] = (
        df["NPT_Subcategory"].fillna("Unknown").astype(str).str.strip()
    )
    df["Root_Cause"] = (
        df["Root_Cause"].fillna("Unknown").astype(str).str.strip()
        if "Root_Cause" in df.columns
        else "Unknown"
    )
    df["Severity"] = (
        df["Severity"].fillna("Unknown").astype(str).str.upper().str.strip()
    )

    for col in [
        "Duration_hr",
        "NPT_Rig_Cost_USD",
        "Deferred_Production_Impact_USD",
        "Total_Impact_USD",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    if (df["Total_Impact_USD"] == 0).all():
        df["Total_Impact_USD"] = (
            df["NPT_Rig_Cost_USD"]
            + df["Deferred_Production_Impact_USD"]
        )

    return df


def aggregate(df, dimensions):
    out = (
        df.groupby(dimensions, dropna=False)
        .agg(
            NPT_Events=("Well_ID", "size"),
            NPT_Hours=("Duration_hr", "sum"),
            NPT_Rig_Cost_USD=("NPT_Rig_Cost_USD", "sum"),
            Deferred_Production_Impact_USD=(
                "Deferred_Production_Impact_USD",
                "sum",
            ),
            Total_Impact_USD=("Total_Impact_USD", "sum"),
            High_Events=("Severity", lambda x: (x == "HIGH").sum()),
            Medium_Events=("Severity", lambda x: (x == "MEDIUM").sum()),
            Low_Events=("Severity", lambda x: (x == "LOW").sum()),
        )
        .reset_index()
    )

    out["NPT_Hours_per_Event"] = (
        out["NPT_Hours"] / out["NPT_Events"].replace(0, pd.NA)
    ).fillna(0.0)

    out["High_Severity_Pct"] = (
        out["High_Events"] / out["NPT_Events"].replace(0, pd.NA) * 100
    ).fillna(0.0)

    return out.sort_values(
        ["Total_Impact_USD", "NPT_Hours"],
        ascending=False,
    )


def pareto(df, dimensions):
    out = aggregate(df, dimensions).reset_index(drop=True)
    total = out["Total_Impact_USD"].sum()

    if total > 0:
        out["Cumulative_Impact_USD"] = out["Total_Impact_USD"].cumsum()
        out["Cumulative_Impact_Pct"] = (
            out["Cumulative_Impact_USD"] / total * 100
        )
    else:
        out["Cumulative_Impact_USD"] = 0.0
        out["Cumulative_Impact_Pct"] = 0.0

    out["Pareto_80_Flag"] = out["Cumulative_Impact_Pct"] <= 80
    out.insert(0, "Rank", range(1, len(out) + 1))
    return out


def concentration_score(grouped, total):
    if total <= 0 or grouped.empty:
        return 0.0
    return float(grouped.iloc[0]["Total_Impact_USD"] / total * 100)


def make_engineering_priority(root_cause):
    """
    Priority is based on a transparent composite of:
        - economic impact
        - NPT hours
        - high severity
    It is a prioritization tool, not a causal model.
    """
    out = root_cause.copy()

    impact_median = out["Total_Impact_USD"].median()
    hours_median = out["NPT_Hours"].median()

    if impact_median <= 0:
        impact_median = 1.0
    if hours_median <= 0:
        hours_median = 1.0

    out["Impact_Index"] = out["Total_Impact_USD"] / impact_median
    out["Hours_Index"] = out["NPT_Hours"] / hours_median

    out["Severity_Index"] = (
        out["Low_Events"]
        + 2 * out["Medium_Events"]
        + 3 * out["High_Events"]
    )

    out["Engineering_Priority_Score"] = (
        0.50 * out["Impact_Index"]
        + 0.30 * out["Hours_Index"]
        + 0.20 * out["Severity_Index"]
    )

    out = out.sort_values(
        [
            "Engineering_Priority_Score",
            "Total_Impact_USD",
            "NPT_Hours",
        ],
        ascending=False,
    ).reset_index(drop=True)

    out.insert(0, "Engineering_Priority_Rank", range(1, len(out) + 1))

    return out


def make_root_cause_classification(df):
    """
    Classifies each root cause according to concentration across wells and
    rigs. This is an analytical classification, not proof of causation.
    """
    cause = aggregate(
        df,
        ["NPT_Category", "NPT_Subcategory", "Root_Cause"],
    )

    well_counts = (
        df.groupby(
            ["NPT_Category", "NPT_Subcategory", "Root_Cause"]
        )["Well_ID"]
        .nunique()
        .rename("Affected_Wells")
        .reset_index()
    )

    rig_counts = (
        df.groupby(
            ["NPT_Category", "NPT_Subcategory", "Root_Cause"]
        )["Rig_ID"]
        .nunique()
        .rename("Affected_Rigs")
        .reset_index()
    )

    out = cause.merge(
        well_counts,
        on=["NPT_Category", "NPT_Subcategory", "Root_Cause"],
    ).merge(
        rig_counts,
        on=["NPT_Category", "NPT_Subcategory", "Root_Cause"],
    )

    max_wells = max(df["Well_ID"].nunique(), 1)
    max_rigs = max(df["Rig_ID"].nunique(), 1)

    out["Well_Coverage_Pct"] = out["Affected_Wells"] / max_wells * 100
    out["Rig_Coverage_Pct"] = out["Affected_Rigs"] / max_rigs * 100

    def classify(row):
        if row["Rig_Coverage_Pct"] >= 75 and row["Well_Coverage_Pct"] >= 50:
            return "SYSTEMIC / BROAD"
        if row["Rig_Coverage_Pct"] >= 75:
            return "RIG-BROAD"
        if row["Well_Coverage_Pct"] >= 50:
            return "WELL-BROAD"
        if row["Affected_Wells"] <= 2 and row["Affected_Rigs"] <= 2:
            return "LOCALIZED"
        return "CONCENTRATED"

    out["Observed_Distribution"] = out.apply(classify, axis=1)

    return out.sort_values(
        "Total_Impact_USD",
        ascending=False,
    )


def make_well_vs_rig_signal(df):
    well = aggregate(df, ["Well_ID"])
    rig = aggregate(df, ["Rig_ID"])

    total_impact = df["Total_Impact_USD"].sum()
    total_hours = df["Duration_hr"].sum()
    total_events = len(df)

    well_summary = pd.DataFrame(
        {
            "Dimension": ["Well"],
            "Entities": [df["Well_ID"].nunique()],
            "Total_Impact_USD": [total_impact],
            "Total_NPT_Hours": [total_hours],
            "Total_NPT_Events": [total_events],
            "Top_Entity": [
                well.iloc[0]["Well_ID"] if not well.empty else "N/A"
            ],
            "Top_Entity_Impact_USD": [
                well.iloc[0]["Total_Impact_USD"] if not well.empty else 0
            ],
            "Top_Entity_Impact_Pct": [
                concentration_score(well, total_impact)
            ],
        }
    )

    rig_summary = pd.DataFrame(
        {
            "Dimension": ["Rig"],
            "Entities": [df["Rig_ID"].nunique()],
            "Total_Impact_USD": [total_impact],
            "Total_NPT_Hours": [total_hours],
            "Total_NPT_Events": [total_events],
            "Top_Entity": [
                rig.iloc[0]["Rig_ID"] if not rig.empty else "N/A"
            ],
            "Top_Entity_Impact_USD": [
                rig.iloc[0]["Total_Impact_USD"] if not rig.empty else 0
            ],
            "Top_Entity_Impact_Pct": [
                concentration_score(rig, total_impact)
            ],
        }
    )

    return pd.concat(
        [well_summary, rig_summary],
        ignore_index=True,
    )


def write_report(
    df,
    well,
    rig,
    root,
    hotspots,
    causes,
    pareto_root,
    pareto_well,
    pareto_rig,
    signal,
):
    total_events = len(df)
    total_hours = df["Duration_hr"].sum()
    total_rig_cost = df["NPT_Rig_Cost_USD"].sum()
    total_deferred = df["Deferred_Production_Impact_USD"].sum()
    total_impact = df["Total_Impact_USD"].sum()

    lines = []

    lines.append("=" * 78)
    lines.append("STAGE 2G.6B — ENGINEERING INTERPRETATION")
    lines.append("Well × Rig × Root Cause Analysis")
    lines.append("=" * 78)
    lines.append("")
    lines.append("DATASET SUMMARY")
    lines.append("-" * 78)
    lines.append(f"NPT Events                         : {total_events:,.0f}")
    lines.append(f"NPT Hours                          : {total_hours:,.1f}")
    lines.append(f"NPT Rig Cost (USD)                 : ${total_rig_cost:,.2f}")
    lines.append(
        f"Deferred Production Impact (USD)  : ${total_deferred:,.2f}"
    )
    lines.append(f"Total Impact (USD)                 : ${total_impact:,.2f}")
    lines.append(f"Unique Wells                       : {df['Well_ID'].nunique():,}")
    lines.append(f"Unique Rigs                        : {df['Rig_ID'].nunique():,}")
    lines.append(
        f"Root Cause combinations            : "
        f"{len(root):,}"
    )
    lines.append("")

    lines.append("1. TOP 10 WELLS BY TOTAL IMPACT")
    lines.append("-" * 78)
    lines.append(
        well[
            [
                "Well_ID",
                "NPT_Events",
                "NPT_Hours",
                "Total_Impact_USD",
                "High_Events",
            ]
        ].head(10).to_string(index=False)
    )
    lines.append("")

    lines.append("2. TOP 10 RIGS BY TOTAL IMPACT")
    lines.append("-" * 78)
    lines.append(
        rig[
            [
                "Rig_ID",
                "NPT_Events",
                "NPT_Hours",
                "Total_Impact_USD",
                "High_Events",
            ]
        ].head(10).to_string(index=False)
    )
    lines.append("")

    lines.append("3. TOP ROOT CAUSES")
    lines.append("-" * 78)
    lines.append(
        root[
            [
                "NPT_Category",
                "NPT_Subcategory",
                "Root_Cause",
                "NPT_Events",
                "NPT_Hours",
                "Total_Impact_USD",
                "High_Events",
            ]
        ].head(15).to_string(index=False)
    )
    lines.append("")

    lines.append("4. TOP WELL × RIG × ROOT CAUSE HOTSPOTS")
    lines.append("-" * 78)
    lines.append(
        hotspots[
            [
                "Well_ID",
                "Rig_ID",
                "NPT_Category",
                "NPT_Subcategory",
                "Root_Cause",
                "NPT_Events",
                "NPT_Hours",
                "Total_Impact_USD",
                "High_Events",
            ]
        ].head(15).to_string(index=False)
    )
    lines.append("")

    lines.append("5. ROOT CAUSE DISTRIBUTION")
    lines.append("-" * 78)
    lines.append(
        causes[
            [
                "NPT_Category",
                "NPT_Subcategory",
                "Root_Cause",
                "Affected_Wells",
                "Affected_Rigs",
                "Well_Coverage_Pct",
                "Rig_Coverage_Pct",
                "Observed_Distribution",
                "Total_Impact_USD",
            ]
        ].head(20).to_string(index=False)
    )
    lines.append("")

    lines.append("6. WELL VS RIG CONCENTRATION")
    lines.append("-" * 78)
    lines.append(signal.to_string(index=False))
    lines.append("")
    lines.append(
        "Interpretation rule: a higher top-entity concentration means the "
        "impact is more concentrated in that dimension. This is evidence of "
        "association, not proof of causation."
    )
    lines.append("")

    lines.append("7. PARETO — WELLS")
    lines.append("-" * 78)
    lines.append(
        pareto_well[
            [
                "Rank",
                "Well_ID",
                "Total_Impact_USD",
                "Cumulative_Impact_Pct",
            ]
        ].head(15).to_string(index=False)
    )
    lines.append("")

    lines.append("8. PARETO — RIGS")
    lines.append("-" * 78)
    lines.append(
        pareto_rig[
            [
                "Rank",
                "Rig_ID",
                "Total_Impact_USD",
                "Cumulative_Impact_Pct",
            ]
        ].to_string(index=False)
    )
    lines.append("")

    lines.append("9. PARETO — ROOT CAUSES")
    lines.append("-" * 78)
    lines.append(
        pareto_root[
            [
                "Rank",
                "NPT_Category",
                "NPT_Subcategory",
                "Root_Cause",
                "Total_Impact_USD",
                "Cumulative_Impact_Pct",
            ]
        ].head(20).to_string(index=False)
    )
    lines.append("")

    lines.append("10. ENGINEERING INTERPRETATION")
    lines.append("-" * 78)

    if not root.empty:
        top = root.iloc[0]
        lines.append(
            f"- Highest-impact root-cause combination: "
            f"{top['NPT_Category']} / {top['NPT_Subcategory']} / "
            f"{top['Root_Cause']} "
            f"(${top['Total_Impact_USD']:,.0f})."
        )

    if not well.empty:
        lines.append(
            f"- Highest-impact well: {well.iloc[0]['Well_ID']} "
            f"(${well.iloc[0]['Total_Impact_USD']:,.0f})."
        )

    if not rig.empty:
        lines.append(
            f"- Highest-impact rig: {rig.iloc[0]['Rig_ID']} "
            f"(${rig.iloc[0]['Total_Impact_USD']:,.0f})."
        )

    if not hotspots.empty:
        h = hotspots.iloc[0]
        lines.append(
            f"- Highest-priority Well × Rig × Root Cause hotspot: "
            f"{h['Well_ID']} × {h['Rig_ID']} × "
            f"{h['NPT_Category']} / {h['NPT_Subcategory']} / "
            f"{h['Root_Cause']}."
        )

    lines.append(
        "- Review repeated causes across multiple wells as potential "
        "systemic/process signals."
    )
    lines.append(
        "- Review causes concentrated on one rig across several wells as "
        "potential rig/equipment/maintenance signals."
    )
    lines.append(
        "- Review causes concentrated on one well as potential "
        "well-condition/formation/operational-context signals."
    )
    lines.append(
        "- Before assigning causal responsibility, compare exposure, "
        "well section, activity, operating environment, maintenance history, "
        "and rig utilization."
    )
    lines.append("")

    lines.append("11. ENGINEERING ACTION FRAMEWORK")
    lines.append("-" * 78)
    lines.append(
        "A. CRITICAL: investigate high-impact + high-severity hotspots first."
    )
    lines.append(
        "B. RIG REVIEW: compare the same root cause across rigs."
    )
    lines.append(
        "C. WELL REVIEW: compare the same rig across different wells."
    )
    lines.append(
        "D. SYSTEMIC REVIEW: prioritize causes affecting many wells/rigs."
    )
    lines.append(
        "E. PREVENTION: link corrective actions to maintenance, BHA, "
        "drilling parameters, logistics, weather planning and crew readiness."
    )
    lines.append("")

    lines.append("=" * 78)
    lines.append("STAGE 2G.6B COMPLETE")
    lines.append("=" * 78)

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    print("=" * 78)
    print("STAGE 2G.6B — WELL × RIG × ROOT CAUSE ENGINEERING INTERPRETATION")
    print("=" * 78)

    if not DB_PATH.exists():
        fail(f"Database not found: {DB_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    try:
        print("\n[1/9] Locating FACT_NPT...")
        fact = find_table(
            conn,
            ["Fact_NPT", "FACT_NPT", "fact_npt"],
        )

        if not fact:
            fail("FACT_NPT table was not found.")

        print(f"      FACT_NPT: {fact}")

        print("\n[2/9] Loading NPT data...")
        df = load_fact_npt(conn, fact)

        print(f"      Events: {len(df):,}")
        print(f"      Wells : {df['Well_ID'].nunique():,}")
        print(f"      Rigs  : {df['Rig_ID'].nunique():,}")

        print("\n[3/9] Building dimensional rankings...")
        well = aggregate(df, ["Well_ID"])
        rig = aggregate(df, ["Rig_ID"])
        root = aggregate(
            df,
            ["NPT_Category", "NPT_Subcategory", "Root_Cause"],
        )

        print("\n[4/9] Building Well × Rig × Root Cause hotspots...")
        hotspot = aggregate(
            df,
            [
                "Well_ID",
                "Rig_ID",
                "NPT_Category",
                "NPT_Subcategory",
                "Root_Cause",
            ],
        )

        hotspot = make_engineering_priority(hotspot)

        print("\n[5/9] Classifying root-cause distribution...")
        causes = make_root_cause_classification(df)

        print("\n[6/9] Building Pareto analysis...")
        pareto_well = pareto(df, ["Well_ID"])
        pareto_rig = pareto(df, ["Rig_ID"])
        pareto_root = pareto(
            df,
            ["NPT_Category", "NPT_Subcategory", "Root_Cause"],
        )

        print("\n[7/9] Comparing Well vs Rig concentration...")
        signal = make_well_vs_rig_signal(df)

        print("\n[8/9] Exporting Stage 2G.6B outputs...")

        outputs = {
            "Stage_2G6B_Well_Ranking.csv": well,
            "Stage_2G6B_Rig_Ranking.csv": rig,
            "Stage_2G6B_Root_Cause_Ranking.csv": root,
            "Stage_2G6B_Well_Rig_Root_Cause_Hotspots.csv": hotspot,
            "Stage_2G6B_Root_Cause_Distribution.csv": causes,
            "Stage_2G6B_Well_Pareto.csv": pareto_well,
            "Stage_2G6B_Rig_Pareto.csv": pareto_rig,
            "Stage_2G6B_Root_Cause_Pareto.csv": pareto_root,
            "Stage_2G6B_Well_vs_Rig_Concentration.csv": signal,
        }

        for filename, frame in outputs.items():
            frame.to_csv(
                OUTPUT_DIR / filename,
                index=False,
            )
            print(f"      ✓ {filename}")

        write_report(
            df=df,
            well=well,
            rig=rig,
            root=root,
            hotspots=hotspot,
            causes=causes,
            pareto_root=pareto_root,
            pareto_well=pareto_well,
            pareto_rig=pareto_rig,
            signal=signal,
        )

        print(f"      ✓ {REPORT_PATH.name}")

        print("\n[9/9] Displaying executive findings...")

        print("\nTOP 10 WELLS")
        print(
            well[
                [
                    "Well_ID",
                    "NPT_Events",
                    "NPT_Hours",
                    "Total_Impact_USD",
                ]
            ].head(10).to_string(index=False)
        )

        print("\nTOP 10 RIGS")
        print(
            rig[
                [
                    "Rig_ID",
                    "NPT_Events",
                    "NPT_Hours",
                    "Total_Impact_USD",
                ]
            ].head(10).to_string(index=False)
        )

        print("\nTOP 10 ROOT CAUSES")
        print(
            root[
                [
                    "NPT_Category",
                    "NPT_Subcategory",
                    "Root_Cause",
                    "NPT_Hours",
                    "Total_Impact_USD",
                ]
            ].head(10).to_string(index=False)
        )

        print("\nTOP 10 WELL × RIG × ROOT CAUSE HOTSPOTS")
        print(
            hotspot[
                [
                    "Engineering_Priority_Rank",
                    "Well_ID",
                    "Rig_ID",
                    "NPT_Category",
                    "NPT_Subcategory",
                    "Root_Cause",
                    "NPT_Hours",
                    "Total_Impact_USD",
                    "High_Events",
                ]
            ].head(10).to_string(index=False)
        )

        print("\n" + "=" * 78)
        print("STAGE 2G.6B COMPLETE")
        print("=" * 78)
        print(f"Report: {REPORT_PATH}")

    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()

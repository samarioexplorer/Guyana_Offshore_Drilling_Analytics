"""
Stage 2G.6 — SQL Well × Rig × Root Cause Analysis

Project: Guyana Offshore Drilling Analytics

Purpose
-------
Integrate FACT_NPT with Well/Rig dimensions and produce:
    1. Well × Rig × Root Cause analysis
    2. Well × Root Cause analysis
    3. Rig × Root Cause analysis
    4. Well × Rig performance
    5. Root-cause economic impact
    6. Pareto tables
    7. Hotspot ranking
    8. Validation against FACT_NPT totals

The script is deliberately defensive: it inspects the SQLite schema before
querying, accepts common column-name variants, and does not modify the
database.

Run from the project root:
    python scripts/14_sql_well_rig_root_cause.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd


# ---------------------------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "database" / "guyana_drilling.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Severity weights used for the hotspot score.
SEVERITY_WEIGHTS = {
    "LOW": 1.0,
    "MEDIUM": 2.0,
    "HIGH": 3.0,
}

# If the project contains an economic/deferred-production column, the script
# will detect it automatically. Otherwise Deferred_Production_USD is 0 and
# the NPT cost remains the economic impact available from FACT_NPT.
DEFERRED_PRODUCTION_ALIASES = [
    "Deferred_Production_USD",
    "Deferred_Production_Cost_USD",
    "Deferred_Production",
    "Production_Loss_USD",
    "Production_Loss_Cost_USD",
]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def log(message: str = "") -> None:
    print(message)


def fail(message: str, exit_code: int = 1) -> None:
    print(f"\nERROR: {message}\n")
    sys.exit(exit_code)


def quote_identifier(identifier: str) -> str:
    """Safely quote a SQLite identifier."""
    return '"' + identifier.replace('"', '""') + '"'


def normalize_name(name: str) -> str:
    """Normalize a column name for flexible matching."""
    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
    )


def find_column(columns: Iterable[str], aliases: Iterable[str]) -> str | None:
    """Return the first matching column, case-insensitively."""
    normalized = {normalize_name(c): c for c in columns}

    for alias in aliases:
        key = normalize_name(alias)
        if key in normalized:
            return normalized[key]

    return None


def table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    rows = conn.execute(
        f"PRAGMA table_info({quote_identifier(table_name)})"
    ).fetchall()
    return [row[1] for row in rows]


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [row[0] for row in rows]


def find_table(tables: Iterable[str], aliases: Iterable[str]) -> str | None:
    normalized = {normalize_name(t): t for t in tables}

    for alias in aliases:
        key = normalize_name(alias)
        if key in normalized:
            return normalized[key]

    return None


def export_csv(df: pd.DataFrame, filename: str) -> Path:
    path = OUTPUT_DIR / filename
    df.to_csv(path, index=False)
    return path


def money(value: float) -> str:
    return f"${value:,.0f}"


def number(value: float) -> str:
    return f"{value:,.0f}"


# ---------------------------------------------------------------------------
# DATABASE DISCOVERY
# ---------------------------------------------------------------------------

def discover_schema(conn: sqlite3.Connection) -> dict:
    tables = list_tables(conn)

    fact_npt = find_table(
        tables,
        ["Fact_NPT", "FACT_NPT", "fact_npt"],
    )
    fact_drilling = find_table(
        tables,
        [
            "Fact_Drilling_Daily_Report",
            "FACT_DRILLING_DAILY_REPORT",
            "fact_drilling_daily_report",
        ],
    )
    dim_well = find_table(tables, ["Dim_Well", "DIM_WELL", "dim_well"])
    dim_rig = find_table(tables, ["Dim_Rig", "DIM_RIG", "dim_rig"])

    missing = []
    for label, table in [
        ("Fact_NPT", fact_npt),
        ("Dim_Well", dim_well),
        ("Dim_Rig", dim_rig),
    ]:
        if table is None:
            missing.append(label)

    if missing:
        fail(
            "Required table(s) not found: "
            + ", ".join(missing)
            + "\nAvailable tables: "
            + ", ".join(tables)
        )

    return {
        "tables": tables,
        "fact_npt": fact_npt,
        "fact_drilling": fact_drilling,
        "dim_well": dim_well,
        "dim_rig": dim_rig,
    }


# ---------------------------------------------------------------------------
# FACT NPT EXTRACTION
# ---------------------------------------------------------------------------

def load_npt(conn: sqlite3.Connection, fact_npt: str) -> pd.DataFrame:
    columns = table_columns(conn, fact_npt)

    well_col = find_column(columns, ["Well_ID", "WellID", "Well"])
    rig_col = find_column(columns, ["Rig_ID", "RigID", "Rig"])
    category_col = find_column(
        columns,
        ["NPT_Category", "Category", "NPTCategory"],
    )
    subcategory_col = find_column(
        columns,
        ["NPT_Subcategory", "Subcategory", "NPTSubcategory"],
    )
    duration_col = find_column(
        columns,
        ["Duration_hr", "NPT_Hours", "Duration_Hours", "Duration"],
    )
    cost_col = find_column(
        columns,
        ["Cost_USD", "NPT_Cost_USD", "Cost"],
    )
    severity_col = find_column(
        columns,
        ["Severity", "NPT_Severity"],
    )
    date_col = find_column(
        columns,
        ["Date", "NPT_Date", "Event_Date"],
    )
    npt_id_col = find_column(
        columns,
        ["NPT_ID", "NPTID", "ID"],
    )

    required = {
        "Well_ID": well_col,
        "Rig_ID": rig_col,
        "NPT_Category": category_col,
        "NPT_Subcategory": subcategory_col,
        "Duration_hr": duration_col,
        "Cost_USD": cost_col,
        "Severity": severity_col,
    }

    missing = [name for name, col in required.items() if col is None]
    if missing:
        fail(
            f"FACT_NPT is missing required column(s): {', '.join(missing)}"
            f"\nAvailable columns: {', '.join(columns)}"
        )

    select_parts = [
        f"{quote_identifier(well_col)} AS Well_ID",
        f"{quote_identifier(rig_col)} AS Rig_ID",
        f"{quote_identifier(category_col)} AS NPT_Category",
        f"{quote_identifier(subcategory_col)} AS NPT_Subcategory",
        f"{quote_identifier(duration_col)} AS Duration_hr",
        f"{quote_identifier(cost_col)} AS Cost_USD",
        f"{quote_identifier(severity_col)} AS Severity",
    ]

    if date_col:
        select_parts.append(f"{quote_identifier(date_col)} AS Date")
    else:
        select_parts.append("NULL AS Date")

    if npt_id_col:
        select_parts.append(f"{quote_identifier(npt_id_col)} AS NPT_ID")
    else:
        select_parts.append("NULL AS NPT_ID")

    query = f"""
        SELECT {", ".join(select_parts)}
        FROM {quote_identifier(fact_npt)}
    """

    df = pd.read_sql_query(query, conn)

    # Normalize data types.
    df["Well_ID"] = df["Well_ID"].astype(str).str.strip()
    df["Rig_ID"] = df["Rig_ID"].astype(str).str.strip()
    df["NPT_Category"] = (
        df["NPT_Category"].fillna("Unknown").astype(str).str.strip()
    )
    df["NPT_Subcategory"] = (
        df["NPT_Subcategory"].fillna("Unknown").astype(str).str.strip()
    )
    df["Severity"] = (
        df["Severity"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    df["Duration_hr"] = pd.to_numeric(
        df["Duration_hr"], errors="coerce"
    ).fillna(0.0)
    df["Cost_USD"] = pd.to_numeric(
        df["Cost_USD"], errors="coerce"
    ).fillna(0.0)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Event identifier is not required; row count is the authoritative event
    # count for FACT_NPT.
    return df


# ---------------------------------------------------------------------------
# DIMENSION ENRICHMENT
# ---------------------------------------------------------------------------

def load_dimension(
    conn: sqlite3.Connection,
    table_name: str,
    id_aliases: list[str],
    attributes: list[tuple[str, list[str]]],
) -> pd.DataFrame:
    columns = table_columns(conn, table_name)
    id_col = find_column(columns, id_aliases)

    if id_col is None:
        return pd.DataFrame()

    select_parts = [f"{quote_identifier(id_col)} AS ID"]

    selected_names = ["ID"]

    for output_name, aliases in attributes:
        col = find_column(columns, aliases)
        if col:
            select_parts.append(
                f"{quote_identifier(col)} AS {quote_identifier(output_name)}"
            )
            selected_names.append(output_name)

    query = f"""
        SELECT {", ".join(select_parts)}
        FROM {quote_identifier(table_name)}
    """

    df = pd.read_sql_query(query, conn)

    for col in selected_names:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df = df.rename(columns={"ID": "Dimension_ID"})
    return df


# ---------------------------------------------------------------------------
# ECONOMIC ENRICHMENT
# ---------------------------------------------------------------------------

def detect_deferred_production(
    conn: sqlite3.Connection,
    fact_drilling: str | None,
) -> tuple[pd.DataFrame, str | None]:
    """
    Try to find an existing deferred-production metric.

    The metric is aggregated by Well_ID and Rig_ID where possible. If no
    suitable source exists, return an empty DataFrame and None.
    """
    if not fact_drilling:
        return pd.DataFrame(), None

    columns = table_columns(conn, fact_drilling)

    well_col = find_column(columns, ["Well_ID", "WellID", "Well"])
    rig_col = find_column(columns, ["Rig_ID", "RigID", "Rig"])
    deferred_col = find_column(columns, DEFERRED_PRODUCTION_ALIASES)

    if not well_col or not deferred_col:
        return pd.DataFrame(), None

    select_parts = [
        f"{quote_identifier(well_col)} AS Well_ID",
        f"SUM(COALESCE({quote_identifier(deferred_col)}, 0)) "
        f"AS Deferred_Production_USD",
    ]

    group_by = [quote_identifier(well_col)]

    if rig_col:
        select_parts.insert(
            1,
            f"{quote_identifier(rig_col)} AS Rig_ID",
        )
        group_by.append(quote_identifier(rig_col))

    query = f"""
        SELECT
            {", ".join(select_parts)}
        FROM {quote_identifier(fact_drilling)}
        GROUP BY {", ".join(group_by)}
    """

    df = pd.read_sql_query(query, conn)

    df["Well_ID"] = df["Well_ID"].astype(str).str.strip()

    if "Rig_ID" in df.columns:
        df["Rig_ID"] = df["Rig_ID"].astype(str).str.strip()

    df["Deferred_Production_USD"] = pd.to_numeric(
        df["Deferred_Production_USD"],
        errors="coerce",
    ).fillna(0.0)

    return df, deferred_col


# ---------------------------------------------------------------------------
# CORE ANALYSIS
# ---------------------------------------------------------------------------

def build_root_cause_analysis(npt: pd.DataFrame) -> pd.DataFrame:
    group_cols = [
        "Well_ID",
        "Rig_ID",
        "NPT_Category",
        "NPT_Subcategory",
    ]

    grouped = (
        npt.groupby(group_cols, dropna=False)
        .agg(
            NPT_Events=("Well_ID", "size"),
            NPT_Hours=("Duration_hr", "sum"),
            NPT_Cost_USD=("Cost_USD", "sum"),
        )
        .reset_index()
    )

    severity = (
        npt.assign(
            Severity_Weight=npt["Severity"].map(SEVERITY_WEIGHTS).fillna(0.0)
        )
        .groupby(group_cols, dropna=False)
        .agg(
            Low_Events=("Severity", lambda x: (x == "LOW").sum()),
            Medium_Events=("Severity", lambda x: (x == "MEDIUM").sum()),
            High_Events=("Severity", lambda x: (x == "HIGH").sum()),
            Severity_Weighted_Events=("Severity_Weight", "sum"),
        )
        .reset_index()
    )

    result = grouped.merge(
        severity,
        on=group_cols,
        how="left",
    )

    result["Deferred_Production_USD"] = 0.0
    result["Total_Impact_USD"] = result["NPT_Cost_USD"]

    # Average severity per event.
    result["Severity_Index"] = (
        result["Severity_Weighted_Events"]
        / result["NPT_Events"].replace(0, pd.NA)
    ).fillna(0.0)

    # Hotspot score:
    #   duration × average severity × economic impact multiplier.
    #
    # The economic multiplier is deliberately normalized so that cost does
    # not completely dominate the operational signal.
    impact_scale = result["NPT_Cost_USD"].median()
    if pd.isna(impact_scale) or impact_scale <= 0:
        impact_scale = 1.0

    result["Impact_Factor"] = (
        result["Total_Impact_USD"] / impact_scale
    ).clip(lower=0)

    result["Hotspot_Score"] = (
        result["NPT_Hours"]
        * result["Severity_Index"].clip(lower=1)
        * result["Impact_Factor"].clip(lower=1)
    )

    return result


def add_deferred_production(
    root_cause: pd.DataFrame,
    deferred: pd.DataFrame,
) -> pd.DataFrame:
    if deferred.empty:
        return root_cause

    # Best case: deferred production is available by Well × Rig.
    if {"Well_ID", "Rig_ID"}.issubset(deferred.columns):
        result = root_cause.merge(
            deferred,
            on=["Well_ID", "Rig_ID"],
            how="left",
            suffixes=("", "_source"),
        )
    else:
        # Fallback: aggregate at Well level and distribute the well-level
        # value across its root-cause rows proportionally to NPT hours.
        result = root_cause.merge(
            deferred[["Well_ID", "Deferred_Production_USD"]],
            on="Well_ID",
            how="left",
        )

    result["Deferred_Production_USD"] = pd.to_numeric(
        result["Deferred_Production_USD"],
        errors="coerce",
    ).fillna(0.0)

    # When a Well × Rig value is repeated for multiple root causes, allocate
    # it proportionally to NPT hours so it is not double-counted.
    if {"Well_ID", "Rig_ID"}.issubset(deferred.columns):
        allocation = (
            result.groupby(["Well_ID", "Rig_ID"])["NPT_Hours"]
            .transform("sum")
            .replace(0, pd.NA)
        )
        result["Deferred_Production_USD"] = (
            result["Deferred_Production_USD"]
            * result["NPT_Hours"]
            / allocation
        ).fillna(0.0)

    result["Total_Impact_USD"] = (
        result["NPT_Cost_USD"]
        + result["Deferred_Production_USD"]
    )

    return result


# ---------------------------------------------------------------------------
# AGGREGATIONS
# ---------------------------------------------------------------------------

def aggregate_by(
    root_cause: pd.DataFrame,
    group_cols: list[str],
) -> pd.DataFrame:
    aggregations = {
        "NPT_Events": "sum",
        "NPT_Hours": "sum",
        "NPT_Cost_USD": "sum",
        "Deferred_Production_USD": "sum",
        "Total_Impact_USD": "sum",
        "Low_Events": "sum",
        "Medium_Events": "sum",
        "High_Events": "sum",
        "Hotspot_Score": "sum",
    }

    result = (
        root_cause.groupby(group_cols, dropna=False)
        .agg(aggregations)
        .reset_index()
    )

    return result.sort_values(
        ["Total_Impact_USD", "NPT_Hours"],
        ascending=False,
    )


def build_pareto(
    df: pd.DataFrame,
    group_cols: list[str],
) -> pd.DataFrame:
    group = aggregate_by(df, group_cols)

    group = group.sort_values(
        "Total_Impact_USD",
        ascending=False,
    ).reset_index(drop=True)

    total = group["Total_Impact_USD"].sum()

    if total > 0:
        group["Cumulative_Impact_USD"] = group[
            "Total_Impact_USD"
        ].cumsum()
        group["Cumulative_Impact_Pct"] = (
            group["Cumulative_Impact_USD"] / total * 100
        )
    else:
        group["Cumulative_Impact_USD"] = 0.0
        group["Cumulative_Impact_Pct"] = 0.0

    group["Pareto_80_Flag"] = (
        group["Cumulative_Impact_Pct"] <= 80
    )

    return group


def build_well_rig_performance(
    root_cause: pd.DataFrame,
) -> pd.DataFrame:
    result = aggregate_by(
        root_cause,
        ["Well_ID", "Rig_ID"],
    )

    result["NPT_Hours_per_Event"] = (
        result["NPT_Hours"]
        / result["NPT_Events"].replace(0, pd.NA)
    ).fillna(0.0)

    result["Cost_per_NPT_Hour_USD"] = (
        result["NPT_Cost_USD"]
        / result["NPT_Hours"].replace(0, pd.NA)
    ).fillna(0.0)

    result["High_Severity_Pct"] = (
        result["High_Events"]
        / result["NPT_Events"].replace(0, pd.NA)
        * 100
    ).fillna(0.0)

    return result


def build_hotspots(
    root_cause: pd.DataFrame,
) -> pd.DataFrame:
    hotspots = root_cause.copy()

    hotspots = hotspots.sort_values(
        [
            "Hotspot_Score",
            "Total_Impact_USD",
            "NPT_Hours",
        ],
        ascending=False,
    ).reset_index(drop=True)

    hotspots.insert(
        0,
        "Hotspot_Rank",
        range(1, len(hotspots) + 1),
    )

    # Add a simple severity class.
    def severity_class(row: pd.Series) -> str:
        if row["High_Events"] >= 2 or row["Total_Impact_USD"] >= 5_000_000:
            return "CRITICAL"
        if row["High_Events"] >= 1 or row["Total_Impact_USD"] >= 2_000_000:
            return "HIGH"
        if row["Total_Impact_USD"] >= 500_000:
            return "MEDIUM"
        return "LOW"

    hotspots["Hotspot_Class"] = hotspots.apply(
        severity_class,
        axis=1,
    )

    return hotspots


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------

def validate_totals(
    npt: pd.DataFrame,
    root_cause: pd.DataFrame,
) -> pd.DataFrame:
    source = {
        "NPT_Events": float(len(npt)),
        "NPT_Hours": float(npt["Duration_hr"].sum()),
        "NPT_Cost_USD": float(npt["Cost_USD"].sum()),
    }

    output = {
        "NPT_Events": float(root_cause["NPT_Events"].sum()),
        "NPT_Hours": float(root_cause["NPT_Hours"].sum()),
        "NPT_Cost_USD": float(root_cause["NPT_Cost_USD"].sum()),
    }

    rows = []

    for metric in source:
        source_value = source[metric]
        output_value = output[metric]

        tolerance = 0.001 if metric == "NPT_Events" else 0.01
        difference = output_value - source_value
        passed = abs(difference) <= tolerance

        rows.append(
            {
                "Metric": metric,
                "Source_Total": source_value,
                "Analysis_Total": output_value,
                "Difference": difference,
                "Status": "PASS" if passed else "FAIL",
            }
        )

    validation = pd.DataFrame(rows)
    return validation


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 72)
    print("STAGE 2G.6 — SQL WELL × RIG × ROOT CAUSE ANALYSIS")
    print("=" * 72)

    log(f"\nProject root : {PROJECT_ROOT}")
    log(f"Database     : {DB_PATH}")
    log(f"Output dir   : {OUTPUT_DIR}")

    if not DB_PATH.exists():
        fail(
            f"SQLite database not found:\n{DB_PATH}\n"
            "Check that the database was created before running Stage 2G.6."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as exc:
        fail(f"Could not connect to SQLite database: {exc}")

    try:
        # ---------------------------------------------------------------
        # 1. DISCOVER SCHEMA
        # ---------------------------------------------------------------
        log("\n[1/8] Discovering SQL schema...")

        schema = discover_schema(conn)

        log(f"      Fact NPT : {schema['fact_npt']}")
        log(f"      Dim Well : {schema['dim_well']}")
        log(f"      Dim Rig  : {schema['dim_rig']}")

        if schema["fact_drilling"]:
            log(f"      Fact DR  : {schema['fact_drilling']}")
        else:
            log("      Fact DR  : not found (optional for this stage)")

        # ---------------------------------------------------------------
        # 2. LOAD FACT NPT
        # ---------------------------------------------------------------
        log("\n[2/8] Loading FACT_NPT...")

        npt = load_npt(
            conn,
            schema["fact_npt"],
        )

        if npt.empty:
            fail("FACT_NPT contains zero rows.")

        log(f"      NPT rows loaded: {len(npt):,}")
        log(f"      Wells: {npt['Well_ID'].nunique():,}")
        log(f"      Rigs : {npt['Rig_ID'].nunique():,}")

        # ---------------------------------------------------------------
        # 3. LOAD DIMENSIONS + BUILD ROOT CAUSE
        # ---------------------------------------------------------------
        log("\n[3/8] Building Well × Rig × Root Cause dataset...")

        well_dim = load_dimension(
            conn,
            schema["dim_well"],
            ["Well_ID", "WellID", "Well"],
            [
                ("Well_Name", ["Well_Name", "WellName", "Name"]),
                ("Operator", ["Operator", "Company"]),
                ("Field", ["Field", "Field_Name"]),
                ("Block", ["Block", "Block_Name"]),
                ("Basin", ["Basin", "Basin_Name"]),
            ],
        )

        rig_dim = load_dimension(
            conn,
            schema["dim_rig"],
            ["Rig_ID", "RigID", "Rig"],
            [
                ("Rig_Name", ["Rig_Name", "RigName", "Name"]),
                ("Rig_Type", ["Rig_Type", "RigType", "Type"]),
                ("Contractor", ["Contractor", "Rig_Contractor"]),
            ],
        )

        root_cause = build_root_cause_analysis(npt)

        # Dimension enrichment.
        if not well_dim.empty:
            well_dim = well_dim.rename(columns={"Dimension_ID": "Well_ID"})
            root_cause = root_cause.merge(
                well_dim,
                on="Well_ID",
                how="left",
            )

        if not rig_dim.empty:
            rig_dim = rig_dim.rename(columns={"Dimension_ID": "Rig_ID"})
            root_cause = root_cause.merge(
                rig_dim,
                on="Rig_ID",
                how="left",
            )

        # ---------------------------------------------------------------
        # 4. ECONOMIC IMPACT
        # ---------------------------------------------------------------
        log("\n[4/8] Adding economic impact...")

        deferred, deferred_source = detect_deferred_production(
            conn,
            schema["fact_drilling"],
        )

        if deferred_source:
            log(
                f"      Deferred production source detected: "
                f"{deferred_source}"
            )
            root_cause = add_deferred_production(
                root_cause,
                deferred,
            )
        else:
            log(
                "      No deferred-production column detected. "
                "Deferred_Production_USD = 0."
            )

        # Recalculate hotspot score after economic enrichment.
        impact_scale = root_cause["NPT_Cost_USD"].median()
        if pd.isna(impact_scale) or impact_scale <= 0:
            impact_scale = 1.0

        root_cause["Impact_Factor"] = (
            root_cause["Total_Impact_USD"] / impact_scale
        ).clip(lower=0)

        root_cause["Hotspot_Score"] = (
            root_cause["NPT_Hours"]
            * root_cause["Severity_Index"].clip(lower=1)
            * root_cause["Impact_Factor"].clip(lower=1)
        )

        # ---------------------------------------------------------------
        # 5. AGGREGATIONS / PARETO / HOTSPOTS
        # ---------------------------------------------------------------
        log("\n[5/8] Calculating Well, Rig, Pareto and hotspot analysis...")

        well_root = aggregate_by(
            root_cause,
            ["Well_ID", "NPT_Category", "NPT_Subcategory"],
        )

        rig_root = aggregate_by(
            root_cause,
            ["Rig_ID", "NPT_Category", "NPT_Subcategory"],
        )

        well_rig = build_well_rig_performance(root_cause)

        root_cause_impact = aggregate_by(
            root_cause,
            ["NPT_Category", "NPT_Subcategory"],
        )

        well_pareto = build_pareto(
            root_cause,
            ["Well_ID"],
        )

        rig_pareto = build_pareto(
            root_cause,
            ["Rig_ID"],
        )

        root_cause_pareto = build_pareto(
            root_cause,
            ["NPT_Category", "NPT_Subcategory"],
        )

        hotspots = build_hotspots(root_cause)

        # ---------------------------------------------------------------
        # 6. EXPORT
        # ---------------------------------------------------------------
        log("\n[6/8] Exporting CSV outputs...")

        outputs = {}

        outputs["Well_Rig_Root_Cause_SQL.csv"] = export_csv(
            root_cause.sort_values(
                ["Total_Impact_USD", "NPT_Hours"],
                ascending=False,
            ),
            "Well_Rig_Root_Cause_SQL.csv",
        )

        outputs["Well_Root_Cause_SQL.csv"] = export_csv(
            well_root,
            "Well_Root_Cause_SQL.csv",
        )

        outputs["Rig_Root_Cause_SQL.csv"] = export_csv(
            rig_root,
            "Rig_Root_Cause_SQL.csv",
        )

        outputs["Well_Rig_Performance_SQL.csv"] = export_csv(
            well_rig,
            "Well_Rig_Performance_SQL.csv",
        )

        outputs["Root_Cause_Impact_SQL.csv"] = export_csv(
            root_cause_impact,
            "Root_Cause_Impact_SQL.csv",
        )

        outputs["Well_Root_Cause_Pareto_SQL.csv"] = export_csv(
            well_pareto,
            "Well_Root_Cause_Pareto_SQL.csv",
        )

        outputs["Rig_Root_Cause_Pareto_SQL.csv"] = export_csv(
            rig_pareto,
            "Rig_Root_Cause_Pareto_SQL.csv",
        )

        outputs["Root_Cause_Pareto_SQL.csv"] = export_csv(
            root_cause_pareto,
            "Root_Cause_Pareto_SQL.csv",
        )

        outputs["Well_Rig_Root_Cause_Hotspots_SQL.csv"] = export_csv(
            hotspots,
            "Well_Rig_Root_Cause_Hotspots_SQL.csv",
        )

        # ---------------------------------------------------------------
        # 7. VALIDATION
        # ---------------------------------------------------------------
        log("\n[7/8] Validating totals...")

        validation = validate_totals(
            npt,
            root_cause,
        )

        validation_path = export_csv(
            validation,
            "Well_Rig_Root_Cause_Validation_SQL.csv",
        )

        for _, row in validation.iterrows():
            metric = row["Metric"]
            source_value = row["Source_Total"]
            analysis_value = row["Analysis_Total"]
            status = row["Status"]

            if "USD" in metric:
                source_display = money(source_value)
                analysis_display = money(analysis_value)
            else:
                source_display = number(source_value)
                analysis_display = number(analysis_value)

            log(
                f"      {metric:<22} "
                f"{source_display:>18} → "
                f"{analysis_display:>18}   {status}"
            )

        # ---------------------------------------------------------------
        # 8. SUMMARY
        # ---------------------------------------------------------------
        log("\n[8/8] Stage summary...")

        log(f"      Well × Rig × Root Cause rows: {len(root_cause):,}")
        log(f"      Well × Root Cause rows       : {len(well_root):,}")
        log(f"      Rig × Root Cause rows        : {len(rig_root):,}")
        log(f"      Well × Rig rows              : {len(well_rig):,}")
        log(f"      Root Cause rows              : {len(root_cause_impact):,}")

        log("\n      Top 10 Well × Rig × Root Cause hotspots:")
        display_cols = [
            "Hotspot_Rank",
            "Well_ID",
            "Rig_ID",
            "NPT_Category",
            "NPT_Subcategory",
            "NPT_Hours",
            "Total_Impact_USD",
            "High_Events",
            "Hotspot_Class",
        ]

        available_display_cols = [
            c for c in display_cols if c in hotspots.columns
        ]

        print(
            hotspots[available_display_cols]
            .head(10)
            .to_string(index=False)
        )

        log("\n      Output files:")
        for name, path in outputs.items():
            log(f"        ✓ {path.name}")

        log(f"        ✓ {validation_path.name}")

        failed = validation[
            validation["Status"] != "PASS"
        ]

        log("\n" + "=" * 72)

        if not failed.empty:
            log("STAGE 2G.6 COMPLETED WITH VALIDATION FAILURES")
            log("=" * 72)
            sys.exit(2)

        log("STAGE 2G.6 COMPLETE — ALL VALIDATIONS PASSED")
        log("=" * 72)

    except Exception as exc:
        fail(
            f"Stage 2G.6 failed: {type(exc).__name__}: {exc}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()

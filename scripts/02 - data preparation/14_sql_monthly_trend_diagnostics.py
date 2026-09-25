"""
Stage 2G.5-A — SQL Monthly Trend Diagnostics
Guyana Offshore Drilling Analytics

Purpose
-------
Diagnose monthly drilling and NPT trends using SQL-derived monthly data.

Inputs
------
database/guyana_drilling.db

Outputs
-------
data/processed/Monthly_Trend_Diagnostics_SQL.csv
data/processed/Monthly_Trend_Anomalies_SQL.csv
data/processed/Monthly_Trend_Summary_SQL.csv

Methodology
-----------
1. Aggregate drilling and NPT independently by calendar month.
2. Use UNION of drilling and NPT months so NPT-only months are retained.
3. Calculate month-over-month deltas.
4. Classify monthly operating condition.
5. Flag anomalous months using robust percentile/IQR-style thresholds.
6. Do not interpret NPT% for NPT-only months because drilling hours are zero.
7. Validate portfolio totals against the database.
"""

from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent

if SCRIPT_DIR.name.lower() == "scripts":
    BASE_DIR = SCRIPT_DIR.parent
else:
    BASE_DIR = SCRIPT_DIR.parents[1]

DB_FILE = BASE_DIR / "database" / "guyana_drilling.db"
OUTPUT_DIR = BASE_DIR / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "Monthly_Trend_Diagnostics_SQL.csv"
ANOMALY_FILE = OUTPUT_DIR / "Monthly_Trend_Anomalies_SQL.csv"
SUMMARY_FILE = OUTPUT_DIR / "Monthly_Trend_Summary_SQL.csv"


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------
def pct_change(current, previous):
    if pd.isna(previous) or previous == 0:
        return np.nan
    return (current / previous - 1.0) * 100.0


def classify_month(row):
    """
    Mutually interpretable monthly operating-condition classification.

    Priority:
    NPT-only > Weather Stress + High NPT Exposure >
    High Economic Impact > Low Activity >
    Improving/Deteriorating/Stable
    """
    if row["Drilling_Hours"] == 0 and row["NPT_Hours"] > 0:
        return "NPT-Only"

    if row["Drilling_Hours"] == 0:
        return "No Activity"

    if row["Low_Activity_Flag"]:
        return "Low Activity"

    if row["Weather_Stress_Flag"] and row["High_NPT_Exposure_Flag"]:
        return "Weather Stress + High NPT Exposure"

    if row["Weather_Stress_Flag"]:
        return "Weather Stress"

    if row["High_NPT_Exposure_Flag"]:
        return "High NPT Exposure"

    if row["High_Economic_Impact_Flag"]:
        return "High Economic Impact"

    return row["Trend_Class"]


def iqr_upper(series, multiplier=1.5):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < 4:
        return np.inf
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    return q3 + multiplier * (q3 - q1)


# ---------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------
monthly_sql = """
WITH
drilling_monthly AS (
    SELECT
        strftime('%Y-%m', Date) AS Month,
        COUNT(*) AS Drilling_Records,
        COUNT(DISTINCT Well_ID) AS Active_Wells,
        SUM(Daily_Footage_ft) AS Total_Footage_ft,
        SUM(Drilling_Hours) AS Drilling_Hours,
        SUM(Daily_Cost_USD) AS Drilling_Cost_USD,
        AVG(ROP_ft_hr) AS Average_ROP_ft_hr,
        MAX(ROP_ft_hr) AS Maximum_ROP_ft_hr,
        SUM(Weather_Delay_hr) AS Weather_Delay_hr
    FROM Fact_Drilling_Daily_Report
    GROUP BY strftime('%Y-%m', Date)
),
npt_monthly AS (
    SELECT
        strftime('%Y-%m', Date) AS Month,
        COUNT(*) AS NPT_Events,
        SUM(Duration_hr) AS NPT_Hours,
        SUM(Cost_USD) AS NPT_Cost_USD,
        SUM(Deferred_Cost_USD) AS Deferred_Cost_USD,
        SUM(Total_Impact_USD) AS NPT_Impact_USD,
        SUM(CASE WHEN NPT_Category = 'Weather'
                 THEN Duration_hr ELSE 0 END) AS Weather_NPT_Hours
    FROM Fact_NPT
    GROUP BY strftime('%Y-%m', Date)
),
all_months AS (
    SELECT Month FROM drilling_monthly
    UNION
    SELECT Month FROM npt_monthly
)
SELECT
    m.Month,
    COALESCE(d.Drilling_Records, 0) AS Drilling_Records,
    COALESCE(d.Active_Wells, 0) AS Active_Wells,
    COALESCE(d.Total_Footage_ft, 0) AS Total_Footage_ft,
    COALESCE(d.Drilling_Hours, 0) AS Drilling_Hours,
    COALESCE(d.Drilling_Cost_USD, 0) AS Drilling_Cost_USD,
    d.Average_ROP_ft_hr,
    d.Maximum_ROP_ft_hr,
    COALESCE(d.Weather_Delay_hr, 0) AS Weather_Delay_hr,
    COALESCE(n.NPT_Events, 0) AS NPT_Events,
    COALESCE(n.NPT_Hours, 0) AS NPT_Hours,
    COALESCE(n.NPT_Cost_USD, 0) AS NPT_Cost_USD,
    COALESCE(n.Deferred_Cost_USD, 0) AS Deferred_Cost_USD,
    COALESCE(n.NPT_Impact_USD, 0) AS NPT_Impact_USD,
    COALESCE(n.Weather_NPT_Hours, 0) AS Weather_NPT_Hours
FROM all_months m
LEFT JOIN drilling_monthly d ON m.Month = d.Month
LEFT JOIN npt_monthly n ON m.Month = n.Month
ORDER BY m.Month;
"""


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------
def main():
    print("=" * 70)
    print("STAGE 2G.5-A — SQL MONTHLY TREND DIAGNOSTICS")
    print("=" * 70)
    print()
    print(f"Database: {DB_FILE}")
    print(f"Output:   {OUTPUT_DIR}")
    print()

    if not DB_FILE.exists():
        raise FileNotFoundError(f"Database not found: {DB_FILE}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query(monthly_sql, conn)

        # Independent global validation totals
        global_drilling = pd.read_sql_query(
            """
            SELECT
                COUNT(*) AS Records,
                SUM(Daily_Footage_ft) AS Footage,
                SUM(Drilling_Hours) AS Hours,
                SUM(Daily_Cost_USD) AS Cost,
                SUM(Weather_Delay_hr) AS Weather
            FROM Fact_Drilling_Daily_Report
            """,
            conn,
        ).iloc[0]

        global_npt = pd.read_sql_query(
            """
            SELECT
                COUNT(*) AS Events,
                SUM(Duration_hr) AS Hours,
                SUM(Cost_USD) AS Cost,
                SUM(Deferred_Cost_USD) AS Deferred,
                SUM(Total_Impact_USD) AS Impact
            FROM Fact_NPT
            """,
            conn,
        ).iloc[0]

    if df.empty:
        raise ValueError("Monthly SQL query returned no rows.")

    # -----------------------------------------------------------------
    # Numeric normalization
    # -----------------------------------------------------------------
    numeric_cols = [
        "Drilling_Records", "Active_Wells", "Total_Footage_ft",
        "Drilling_Hours", "Drilling_Cost_USD", "Average_ROP_ft_hr",
        "Maximum_ROP_ft_hr", "Weather_Delay_hr", "NPT_Events",
        "NPT_Hours", "NPT_Cost_USD", "Deferred_Cost_USD",
        "NPT_Impact_USD", "Weather_NPT_Hours"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Month"] = pd.to_datetime(df["Month"] + "-01")
    df = df.sort_values("Month").reset_index(drop=True)

    # -----------------------------------------------------------------
    # Derived monthly KPIs
    # -----------------------------------------------------------------
    df["Drilling_Cost_per_Foot_USD"] = np.where(
        df["Total_Footage_ft"] > 0,
        df["Drilling_Cost_USD"] / df["Total_Footage_ft"],
        np.nan,
    )

    df["NPT_Hours_pct"] = np.where(
        df["Drilling_Hours"] > 0,
        df["NPT_Hours"] / (df["Drilling_Hours"] + df["NPT_Hours"]) * 100,
        np.nan,
    )

    df["NPT_Cost_per_Foot_USD"] = np.where(
        df["Total_Footage_ft"] > 0,
        df["NPT_Cost_USD"] / df["Total_Footage_ft"],
        np.nan,
    )

    df["Operational_Cost_USD"] = (
        df["Drilling_Cost_USD"] + df["NPT_Cost_USD"]
    )

    df["Operational_Cost_per_Foot_USD"] = np.where(
        df["Total_Footage_ft"] > 0,
        df["Operational_Cost_USD"] / df["Total_Footage_ft"],
        np.nan,
    )

    df["Total_Economic_Impact_USD"] = (
        df["Drilling_Cost_USD"]
        + df["NPT_Cost_USD"]
        + df["Deferred_Cost_USD"]
    )

    df["Total_Economic_Impact_per_Foot_USD"] = np.where(
        df["Total_Footage_ft"] > 0,
        df["Total_Economic_Impact_USD"] / df["Total_Footage_ft"],
        np.nan,
    )

    df["Weather_Delay_pct"] = np.where(
        df["Drilling_Hours"] > 0,
        df["Weather_Delay_hr"] / df["Drilling_Hours"] * 100,
        np.nan,
    )

    df["Weather_NPT_pct"] = np.where(
        df["NPT_Hours"] > 0,
        df["Weather_NPT_Hours"] / df["NPT_Hours"] * 100,
        np.nan,
    )

    df["Total_Activity_Hours"] = df["Drilling_Hours"] + df["NPT_Hours"]

    # -----------------------------------------------------------------
    # Month-over-month changes
    # -----------------------------------------------------------------
    change_metrics = {
        "Average_ROP_ft_hr": "ROP_MoM_pct",
        "Total_Footage_ft": "Footage_MoM_pct",
        "Drilling_Cost_per_Foot_USD": "Drilling_Cost_per_Foot_MoM_pct",
        "NPT_Hours": "NPT_Hours_MoM_pct",
        "NPT_Hours_pct": "NPT_Hours_pct_MoM_pct",
        "NPT_Cost_USD": "NPT_Cost_MoM_pct",
        "Deferred_Cost_USD": "Deferred_Cost_MoM_pct",
        "Total_Economic_Impact_USD": "Economic_Impact_MoM_pct",
        "Weather_Delay_pct": "Weather_Delay_pct_MoM_pct",
    }

    for metric, output_col in change_metrics.items():
        previous = df[metric].shift(1)
        df[output_col] = [
            pct_change(cur, prev)
            for cur, prev in zip(df[metric], previous)
        ]

    # -----------------------------------------------------------------
    # Portfolio benchmark thresholds
    # -----------------------------------------------------------------
    valid_drilling = df[df["Drilling_Hours"] > 0].copy()

    median_footage = valid_drilling["Total_Footage_ft"].median()
    median_npt_pct = valid_drilling["NPT_Hours_pct"].median()
    median_weather_pct = valid_drilling["Weather_Delay_pct"].median()
    median_impact = valid_drilling["Total_Economic_Impact_USD"].median()

    high_npt_threshold = valid_drilling["NPT_Hours_pct"].quantile(0.75)
    weather_stress_threshold = valid_drilling["Weather_Delay_pct"].quantile(0.75)
    high_impact_threshold = valid_drilling["Total_Economic_Impact_USD"].quantile(0.75)

    # Anomaly thresholds
    anomaly_metrics = [
        "Average_ROP_ft_hr",
        "Total_Footage_ft",
        "Drilling_Cost_per_Foot_USD",
        "NPT_Hours",
        "NPT_Hours_pct",
        "NPT_Cost_USD",
        "Deferred_Cost_USD",
        "Total_Economic_Impact_USD",
        "Weather_Delay_pct",
    ]

    anomaly_thresholds = {
        metric: iqr_upper(valid_drilling[metric])
        for metric in anomaly_metrics
    }

    # -----------------------------------------------------------------
    # Trend classification
    # -----------------------------------------------------------------
    def trend_class(row):
        if row["Drilling_Hours"] == 0:
            return "N/A"

        signals = 0

        # Positive operational indicators
        if row["ROP_MoM_pct"] > 5:
            signals += 1
        elif row["ROP_MoM_pct"] < -5:
            signals -= 1

        if row["Drilling_Cost_per_Foot_MoM_pct"] < -5:
            signals += 1
        elif row["Drilling_Cost_per_Foot_MoM_pct"] > 5:
            signals -= 1

        # Negative exposure indicators
        if row["NPT_Hours_pct_MoM_pct"] < -5:
            signals += 1
        elif row["NPT_Hours_pct_MoM_pct"] > 5:
            signals -= 1

        if row["Economic_Impact_MoM_pct"] < -5:
            signals += 1
        elif row["Economic_Impact_MoM_pct"] > 5:
            signals -= 1

        if signals >= 2:
            return "Improving"
        if signals <= -2:
            return "Deteriorating"
        return "Stable"

    df["Trend_Class"] = df.apply(trend_class, axis=1)

    # -----------------------------------------------------------------
    # Operating-condition flags
    # -----------------------------------------------------------------
    df["NPT_Only_Flag"] = (
        (df["Drilling_Hours"] == 0) & (df["NPT_Hours"] > 0)
    )

    df["Low_Activity_Flag"] = (
        (df["Drilling_Hours"] > 0)
        & (df["Total_Footage_ft"] < median_footage * 0.50)
    )

    df["High_NPT_Exposure_Flag"] = (
        (df["Drilling_Hours"] > 0)
        & (df["NPT_Hours_pct"] >= high_npt_threshold)
    )

    df["Weather_Stress_Flag"] = (
        (df["Drilling_Hours"] > 0)
        & (df["Weather_Delay_pct"] >= weather_stress_threshold)
    )

    df["High_Economic_Impact_Flag"] = (
        (df["Drilling_Hours"] > 0)
        & (df["Total_Economic_Impact_USD"] >= high_impact_threshold)
    )

    df["Operating_Condition"] = df.apply(classify_month, axis=1)

    # -----------------------------------------------------------------
    # Anomaly detection
    # -----------------------------------------------------------------
    anomaly_cols = []
    for metric in anomaly_metrics:
        col = f"Anomaly_{metric}"
        threshold = anomaly_thresholds[metric]

        df[col] = (
            (df[metric] > threshold)
            & (
                df["Drilling_Hours"] > 0
                if metric not in ["NPT_Hours", "NPT_Cost_USD",
                                  "Deferred_Cost_USD",
                                  "Total_Economic_Impact_USD"]
                else True
            )
        )
        anomaly_cols.append(col)

    df["Anomaly_Count"] = df[anomaly_cols].sum(axis=1)

    df["Anomaly_Flag"] = np.where(
        df["Anomaly_Count"] > 0,
        "Anomalous",
        "Normal"
    )

    # -----------------------------------------------------------------
    # Best / worst month flags
    # -----------------------------------------------------------------
    active = df[df["Drilling_Hours"] > 0]

    df["Best_ROP_Flag"] = False
    df["Worst_ROP_Flag"] = False
    df["Best_Footage_Flag"] = False
    df["Worst_Footage_Flag"] = False
    df["Best_Cost_per_Foot_Flag"] = False
    df["Worst_Cost_per_Foot_Flag"] = False
    df["Highest_NPT_Flag"] = False
    df["Lowest_NPT_Flag"] = False
    df["Highest_NPT_pct_Flag"] = False
    df["Lowest_NPT_pct_Flag"] = False
    df["Highest_Impact_Flag"] = False
    df["Lowest_Impact_Flag"] = False

    if not active.empty:
        df.loc[active["Average_ROP_ft_hr"].idxmax(), "Best_ROP_Flag"] = True
        df.loc[active["Average_ROP_ft_hr"].idxmin(), "Worst_ROP_Flag"] = True
        df.loc[active["Total_Footage_ft"].idxmax(), "Best_Footage_Flag"] = True
        df.loc[active["Total_Footage_ft"].idxmin(), "Worst_Footage_Flag"] = True
        df.loc[
            active["Drilling_Cost_per_Foot_USD"].idxmin(),
            "Best_Cost_per_Foot_Flag"
        ] = True
        df.loc[
            active["Drilling_Cost_per_Foot_USD"].idxmax(),
            "Worst_Cost_per_Foot_Flag"
        ] = True
        df.loc[active["NPT_Hours"].idxmax(), "Highest_NPT_Flag"] = True
        df.loc[active["NPT_Hours"].idxmin(), "Lowest_NPT_Flag"] = True
        df.loc[active["NPT_Hours_pct"].idxmax(), "Highest_NPT_pct_Flag"] = True
        df.loc[active["NPT_Hours_pct"].idxmin(), "Lowest_NPT_pct_Flag"] = True
        df.loc[
            active["Total_Economic_Impact_USD"].idxmax(),
            "Highest_Impact_Flag"
        ] = True
        df.loc[
            active["Total_Economic_Impact_USD"].idxmin(),
            "Lowest_Impact_Flag"
        ] = True

    # -----------------------------------------------------------------
    # Formatting
    # -----------------------------------------------------------------
    df["Month"] = df["Month"].dt.strftime("%Y-%m")

    # Reorder columns
    preferred = [
        "Month",
        "Drilling_Records",
        "Active_Wells",
        "Total_Footage_ft",
        "Drilling_Hours",
        "Average_ROP_ft_hr",
        "Maximum_ROP_ft_hr",
        "Drilling_Cost_USD",
        "Drilling_Cost_per_Foot_USD",
        "Weather_Delay_hr",
        "Weather_Delay_pct",
        "NPT_Events",
        "NPT_Hours",
        "NPT_Hours_pct",
        "NPT_Cost_USD",
        "NPT_Cost_per_Foot_USD",
        "Deferred_Cost_USD",
        "NPT_Impact_USD",
        "Operational_Cost_USD",
        "Operational_Cost_per_Foot_USD",
        "Total_Economic_Impact_USD",
        "Total_Economic_Impact_per_Foot_USD",
        "Weather_NPT_Hours",
        "Weather_NPT_pct",
        "Total_Activity_Hours",
        "ROP_MoM_pct",
        "Footage_MoM_pct",
        "Drilling_Cost_per_Foot_MoM_pct",
        "NPT_Hours_MoM_pct",
        "NPT_Hours_pct_MoM_pct",
        "NPT_Cost_MoM_pct",
        "Deferred_Cost_MoM_pct",
        "Economic_Impact_MoM_pct",
        "Weather_Delay_pct_MoM_pct",
        "Trend_Class",
        "Operating_Condition",
        "NPT_Only_Flag",
        "Low_Activity_Flag",
        "High_NPT_Exposure_Flag",
        "Weather_Stress_Flag",
        "High_Economic_Impact_Flag",
        "Anomaly_Count",
        "Anomaly_Flag",
        "Best_ROP_Flag",
        "Worst_ROP_Flag",
        "Best_Footage_Flag",
        "Worst_Footage_Flag",
        "Best_Cost_per_Foot_Flag",
        "Worst_Cost_per_Foot_Flag",
        "Highest_NPT_Flag",
        "Lowest_NPT_Flag",
        "Highest_NPT_pct_Flag",
        "Lowest_NPT_pct_Flag",
        "Highest_Impact_Flag",
        "Lowest_Impact_Flag",
    ]

    df = df[[c for c in preferred if c in df.columns]]

    # -----------------------------------------------------------------
    # Anomaly detail table
    # -----------------------------------------------------------------
    anomaly_df = df[
        (df["Anomaly_Flag"] == "Anomalous")
        | df["NPT_Only_Flag"]
        | df["High_NPT_Exposure_Flag"]
        | df["Weather_Stress_Flag"]
        | df["High_Economic_Impact_Flag"]
    ].copy()

    anomaly_df.to_csv(ANOMALY_FILE, index=False)

    # -----------------------------------------------------------------
    # Executive summary
    # -----------------------------------------------------------------
    active = df[df["Drilling_Hours"] > 0].copy()

    def month_for(metric, mode="max"):
        if active.empty:
            return None
        idx = active[metric].idxmax() if mode == "max" else active[metric].idxmin()
        return active.loc[idx, "Month"]

    summary_rows = [
        ["Monthly rows", len(df)],
        ["Date range", f"{df['Month'].min()} to {df['Month'].max()}"],
        ["Best ROP month", month_for("Average_ROP_ft_hr", "max")],
        ["Worst ROP month", month_for("Average_ROP_ft_hr", "min")],
        ["Highest footage month", month_for("Total_Footage_ft", "max")],
        ["Lowest footage month", month_for("Total_Footage_ft", "min")],
        ["Best drilling cost/ft month", month_for("Drilling_Cost_per_Foot_USD", "min")],
        ["Worst drilling cost/ft month", month_for("Drilling_Cost_per_Foot_USD", "max")],
        ["Highest NPT hours month", month_for("NPT_Hours", "max")],
        ["Lowest NPT hours month", month_for("NPT_Hours", "min")],
        ["Highest NPT% month", month_for("NPT_Hours_pct", "max")],
        ["Lowest NPT% month", month_for("NPT_Hours_pct", "min")],
        ["Highest economic impact month", month_for("Total_Economic_Impact_USD", "max")],
        ["Lowest economic impact month", month_for("Total_Economic_Impact_USD", "min")],
        ["Improving months", int((df["Trend_Class"] == "Improving").sum())],
        ["Stable months", int((df["Trend_Class"] == "Stable").sum())],
        ["Deteriorating months", int((df["Trend_Class"] == "Deteriorating").sum())],
        ["NPT-only months", int(df["NPT_Only_Flag"].sum())],
        ["Anomalous months", int((df["Anomaly_Flag"] == "Anomalous").sum())],
        ["High NPT exposure months", int(df["High_NPT_Exposure_Flag"].sum())],
        ["Weather stress months", int(df["Weather_Stress_Flag"].sum())],
        ["High economic impact months", int(df["High_Economic_Impact_Flag"].sum())],
    ]

    summary_df = pd.DataFrame(summary_rows, columns=["Metric", "Value"])
    summary_df.to_csv(SUMMARY_FILE, index=False)

    # -----------------------------------------------------------------
    # Portfolio validation
    # -----------------------------------------------------------------
    checks = []

    checks.append(
        ("Monthly rows > 0", len(df) > 0)
    )

    checks.append(
        (
            "Total drilling records",
            int(df["Drilling_Records"].sum()) == int(global_drilling["Records"])
        )
    )

    checks.append(
        (
            "Total footage",
            abs(df["Total_Footage_ft"].sum() - float(global_drilling["Footage"])) < 0.01
        )
    )

    checks.append(
        (
            "Total drilling hours",
            abs(df["Drilling_Hours"].sum() - float(global_drilling["Hours"])) < 0.01
        )
    )

    checks.append(
        (
            "Total drilling cost",
            abs(df["Drilling_Cost_USD"].sum() - float(global_drilling["Cost"])) < 0.01
        )
    )

    checks.append(
        (
            "Total NPT events",
            int(df["NPT_Events"].sum()) == int(global_npt["Events"])
        )
    )

    checks.append(
        (
            "Total NPT hours",
            abs(df["NPT_Hours"].sum() - float(global_npt["Hours"])) < 0.01
        )
    )

    checks.append(
        (
            "Total NPT cost",
            abs(df["NPT_Cost_USD"].sum() - float(global_npt["Cost"])) < 0.01
        )
    )

    checks.append(
        (
            "Total deferred cost",
            abs(df["Deferred_Cost_USD"].sum() - float(global_npt["Deferred"])) < 0.01
        )
    )

    checks.append(
        (
            "Total NPT impact",
            abs(df["NPT_Impact_USD"].sum() - float(global_npt["Impact"])) < 0.01
        )
    )

    # -----------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------
    df.to_csv(OUTPUT_FILE, index=False)

    print("=" * 70)
    print("MONTHLY TREND DIAGNOSTICS")
    print("=" * 70)
    print()
    print(f"Monthly rows: {len(df)}")
    print(f"Date range: {df['Month'].min()} to {df['Month'].max()}")
    print()
    print("BEST / WORST MONTHS")
    print("-" * 70)
    print(f"Best ROP:                 {month_for('Average_ROP_ft_hr', 'max')}")
    print(f"Worst ROP:                {month_for('Average_ROP_ft_hr', 'min')}")
    print(f"Highest footage:          {month_for('Total_Footage_ft', 'max')}")
    print(f"Lowest footage:           {month_for('Total_Footage_ft', 'min')}")
    print(f"Best drilling cost/ft:    {month_for('Drilling_Cost_per_Foot_USD', 'min')}")
    print(f"Worst drilling cost/ft:   {month_for('Drilling_Cost_per_Foot_USD', 'max')}")
    print(f"Highest NPT hours:        {month_for('NPT_Hours', 'max')}")
    print(f"Highest NPT%:             {month_for('NPT_Hours_pct', 'max')}")
    print(f"Highest economic impact:  {month_for('Total_Economic_Impact_USD', 'max')}")
    print()
    print("MONTH CLASSIFICATION")
    print("-" * 70)
    print(df["Operating_Condition"].value_counts().to_string())
    print()
    print("TREND CLASSIFICATION")
    print("-" * 70)
    print(df["Trend_Class"].value_counts(dropna=False).to_string())
    print()
    print("ANOMALIES / EXPOSURE")
    print("-" * 70)
    print(f"Anomalous months:         {(df['Anomaly_Flag'] == 'Anomalous').sum()}")
    print(f"NPT-only months:          {df['NPT_Only_Flag'].sum()}")
    print(f"High NPT exposure:        {df['High_NPT_Exposure_Flag'].sum()}")
    print(f"Weather stress:           {df['Weather_Stress_Flag'].sum()}")
    print(f"High economic impact:     {df['High_Economic_Impact_Flag'].sum()}")
    print()
    print("VALIDATION")
    print("-" * 70)

    passed = 0
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL':6} | {name}")
        if ok:
            passed += 1

    print()
    print(f"Validation result: {passed}/{len(checks)} PASS")

    if passed != len(checks):
        raise RuntimeError("One or more validation checks failed.")

    print()
    print("OUTPUT FILES")
    print("-" * 70)
    print(OUTPUT_FILE)
    print(ANOMALY_FILE)
    print(SUMMARY_FILE)
    print()
    print("Stage 2G.5-A completed successfully.")


if __name__ == "__main__":
    main()

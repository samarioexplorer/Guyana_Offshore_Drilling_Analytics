"""
Project 01 — Guyana Offshore Drilling Performance & NPT Analytics

04_generate_fact_drilling_daily_report.py

Generates a physically coherent daily drilling fact table from DIM WELL,
DIM RIG and DIM DATE.

Grain
-----
One row per Well_ID + Date for an actual drilling day.

Core engineering relationships
------------------------------
Daily_Footage_ft = Current_Depth_MD_ft - Previous_Depth_MD_ft
ROP_ft_hr        = Daily_Footage_ft / Drilling_Hours
Current_Depth_MD_ft <= Target_Depth_ft

NPT design
----------
NPT is intentionally NOT stored as a daily total in this fact table.
FACT NPT remains the authoritative event-level source. Aggregate it by
Well_ID + Date in SQL/Power BI when required.

Inputs are expected under ../data/raw relative to this script:
    Dim_Well.xlsx
    Dim_Rig.xlsx
    Dim_Date.xlsx

Output:
    Fact_Drilling_Daily_Report.xlsx
"""

from __future__ import annotations

from pathlib import Path
import sys
import numpy as np
import pandas as pd

SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = RAW_DIR / "Fact_Drilling_Daily_Report.xlsx"
WELL_FILE = RAW_DIR / "Dim_Well.xlsx"
RIG_FILE = RAW_DIR / "Dim_Rig.xlsx"
DATE_FILE = RAW_DIR / "Dim_Date.xlsx"

# ----------------------------- helpers -----------------------------------

def parse_excel_date_series(series: pd.Series) -> pd.Series:
    """Parse normal Excel/Pandas dates and Excel serial dates safely."""
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_datetime(series, unit="D", origin="1899-12-30", errors="coerce")
    return pd.to_datetime(series, errors="coerce")


def require_columns(df: pd.DataFrame, required: list[str], table_name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"{table_name} is missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )


def section_for_depth(depth_ft: float, target_depth_ft: float) -> str:
    progress = depth_ft / target_depth_ft if target_depth_ft else 0.0
    if progress <= 0.12:
        return "Surface"
    if progress <= 0.35:
        return "Intermediate 1"
    if progress <= 0.65:
        return "Intermediate 2"
    if progress <= 0.88:
        return "Production"
    return "TD / Reservoir"


def base_rop_by_section(section: str, rng: np.random.Generator) -> float:
    ranges = {
        "Surface": (38.0, 50.0),
        "Intermediate 1": (34.0, 46.0),
        "Intermediate 2": (29.0, 41.0),
        "Production": (24.0, 36.0),
        "TD / Reservoir": (20.0, 31.0),
    }
    lo, hi = ranges[section]
    return float(rng.uniform(lo, hi))


def mud_weight_by_section(section: str, rng: np.random.Generator) -> float:
    ranges = {
        "Surface": (9.5, 10.8),
        "Intermediate 1": (10.5, 11.8),
        "Intermediate 2": (11.3, 12.8),
        "Production": (12.0, 14.0),
        "TD / Reservoir": (12.5, 15.5),
    }
    lo, hi = ranges[section]
    return round(float(rng.uniform(lo, hi)), 1)


def choose_weather(rng: np.random.Generator) -> tuple[str, float]:
    condition = str(
        rng.choice(["Normal", "Moderate", "Severe"], p=[0.88, 0.09, 0.03])
    )
    if condition == "Normal":
        delay = 0.0
    elif condition == "Moderate":
        delay = float(rng.integers(2, 7))
    else:
        delay = float(rng.integers(8, 13))
    return condition, delay


def generate_well_records(
    well_row: pd.Series,
    rig_row: pd.Series,
    date_set: set[pd.Timestamp],
    rng: np.random.Generator,
) -> list[dict]:
    well_id = str(well_row["Well_ID"])
    rig_id = str(well_row["Rig_ID"])
    spud_date = pd.to_datetime(well_row["Spud_Date"], errors="coerce")
    target_depth = float(well_row["Target_Depth_ft"])
    rig_day_rate = float(rig_row["Day_Rate_USD"])

    if pd.isna(spud_date):
        raise ValueError(f"{well_id}: invalid Spud_Date")
    if target_depth <= 0:
        raise ValueError(f"{well_id}: Target_Depth_ft must be > 0")
    if rig_day_rate <= 0:
        raise ValueError(f"{rig_id}: Rig_Day_Rate_USD must be > 0")

    current_depth = 0.0
    records: list[dict] = []

    # A drilling campaign should not be forced to 90 rows.
    # 365 is only an upper guardrail.
    for day_offset in range(365):
        if current_depth >= target_depth:
            break

        date = spud_date + pd.Timedelta(days=day_offset)
        if date not in date_set:
            raise ValueError(
                f"{well_id}: {date.date()} is outside DIM DATE coverage."
            )

        # A small chance of a non-drilling calendar day. Because this fact
        # table is for actual drilling days, skipped days produce no row.
        if rng.random() < 0.04:
            continue

        section = section_for_depth(current_depth, target_depth)
        rop_target = max(12.0, base_rop_by_section(section, rng) + rng.normal(0, 2.0))

        weather_condition, weather_delay = choose_weather(rng)
        available_hours = max(6.0, 24.0 - weather_delay)
        drilling_hours = float(
            np.clip(
                rng.normal(loc=min(19.5, available_hours - 1.0), scale=1.5),
                6.0,
                available_hours,
            )
        )

        candidate_footage = rop_target * drilling_hours
        remaining_depth = target_depth - current_depth
        daily_footage = min(candidate_footage, remaining_depth)
        if daily_footage <= 0:
            break

        actual_rop = daily_footage / drilling_hours
        previous_depth = current_depth
        current_depth = current_depth + daily_footage

        rig_cost = rig_day_rate * (drilling_hours / 24.0)
        other_operating = max(25_000.0, float(rng.normal(65_000.0, 12_000.0)))
        daily_cost = rig_cost + other_operating

        records.append(
            {
                "Date": date,
                "Well_ID": well_id,
                "Rig_ID": rig_id,
                "Previous_Depth_MD_ft": round(previous_depth, 1),
                "Current_Depth_MD_ft": round(current_depth, 1),
                "Daily_Footage_ft": round(daily_footage, 1),
                "Hole_Section": section_for_depth(
                    max(previous_depth, current_depth - 0.5), target_depth
                ),
                "ROP_ft_hr": round(actual_rop, 2),
                "Drilling_Hours": round(drilling_hours, 2),
                "Weather_Condition": weather_condition,
                "Weather_Delay_hr": round(weather_delay, 1),
                "Mud_Weight_ppg": mud_weight_by_section(section, rng),
                "Daily_Cost_USD": round(daily_cost, 2),
            }
        )

    if current_depth < target_depth:
        raise RuntimeError(
            f"{well_id}: target depth not reached after 365 calendar days. "
            f"Final={current_depth:.1f} ft; Target={target_depth:.1f} ft."
        )

    return records


# ------------------------------ main -------------------------------------

def main() -> int:
    rng = np.random.default_rng(SEED)

    for p in (WELL_FILE, RIG_FILE, DATE_FILE):
        if not p.exists():
            raise FileNotFoundError(f"Missing input: {p}")

    dim_well = pd.read_excel(WELL_FILE)
    dim_rig = pd.read_excel(RIG_FILE)
    dim_date = pd.read_excel(DATE_FILE)

    require_columns(dim_well, ["Well_ID", "Rig_ID", "Spud_Date", "Target_Depth_ft"], "DIM WELL")
    require_columns(dim_rig, ["Rig_ID", "Day_Rate_USD"], "DIM RIG")
    require_columns(dim_date, ["Date"], "DIM DATE")

    dim_well["Spud_Date"] = parse_excel_date_series(dim_well["Spud_Date"])
    dim_date["Date"] = parse_excel_date_series(dim_date["Date"])

    if dim_well["Well_ID"].duplicated().any():
        raise ValueError("DIM WELL contains duplicate Well_ID values.")
    if dim_rig["Rig_ID"].duplicated().any():
        raise ValueError("DIM RIG contains duplicate Rig_ID values.")
    if dim_date["Date"].duplicated().any():
        raise ValueError("DIM DATE contains duplicate Date values.")

    rig_lookup = dim_rig.copy()
    rig_lookup["Rig_ID"] = rig_lookup["Rig_ID"].astype(str)
    rig_lookup = rig_lookup.set_index("Rig_ID")

    valid_rigs = set(rig_lookup.index)
    missing_rigs = sorted(set(dim_well["Rig_ID"].astype(str)) - valid_rigs)
    if missing_rigs:
        raise ValueError(f"DIM WELL contains unknown Rig_ID values: {missing_rigs}")

    date_set = set(pd.DatetimeIndex(dim_date["Date"]).normalize())

    all_records: list[dict] = []
    print(f"Wells found: {len(dim_well)}")

    for _, well_row in dim_well.iterrows():
        rig_row = rig_lookup.loc[str(well_row["Rig_ID"])]
        records = generate_well_records(well_row, rig_row, date_set, rng)
        all_records.extend(records)
        print(
            f"{well_row['Well_ID']} -> {len(records)} drilling days | "
            f"TD={float(well_row['Target_Depth_ft']):,.0f} ft | "
            f"Final={records[-1]['Current_Depth_MD_ft']:,.1f} ft"
        )

    fact = pd.DataFrame(all_records)
    if fact.empty:
        raise RuntimeError("Generated fact table is empty.")

    fact["Date"] = pd.to_datetime(fact["Date"])
    if fact.duplicated(["Well_ID", "Date"]).any():
        raise RuntimeError("Duplicate Well_ID + Date records detected.")

    target_map = dim_well.set_index("Well_ID")["Target_Depth_ft"]
    target = fact["Well_ID"].map(target_map)

    # Engineering QC.
    if (fact["Previous_Depth_MD_ft"] < 0).any():
        raise RuntimeError("Negative previous depth detected.")
    if (fact["Current_Depth_MD_ft"] < fact["Previous_Depth_MD_ft"]).any():
        raise RuntimeError("Current depth regressed.")
    if (fact["Current_Depth_MD_ft"] > target + 0.2).any():
        raise RuntimeError("Current depth exceeds Target_Depth_ft.")

    footage_error = (
        fact["Current_Depth_MD_ft"]
        - fact["Previous_Depth_MD_ft"]
        - fact["Daily_Footage_ft"]
    ).abs()
    if (footage_error > 0.2).any():
        raise RuntimeError("Footage does not reconcile with depth progression.")

    rop_error = (
        fact["Daily_Footage_ft"] / fact["Drilling_Hours"]
        - fact["ROP_ft_hr"]
    ).abs()
    if (rop_error > 0.05).any():
        raise RuntimeError("ROP does not reconcile with footage/drilling hours.")

    if ((fact["Drilling_Hours"] <= 0) | (fact["Drilling_Hours"] > 24)).any():
        raise RuntimeError("Drilling_Hours outside 0–24 hours.")
    if ((fact["Weather_Delay_hr"] < 0) | (fact["Weather_Delay_hr"] > 24)).any():
        raise RuntimeError("Weather_Delay_hr outside 0–24 hours.")
    if (fact["Daily_Cost_USD"] <= 0).any():
        raise RuntimeError("Non-positive daily cost detected.")

    fact.sort_values(["Well_ID", "Date"], inplace=True, ignore_index=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fact.to_excel(OUTPUT_FILE, index=False, sheet_name="FACT DAILY DRILLING REPORT")

    print("\nGENERATION COMPLETE")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Rows: {len(fact):,}")
    print(f"Wells: {fact['Well_ID'].nunique():,}")
    print(f"Avg ROP: {fact['ROP_ft_hr'].mean():.2f} ft/hr")
    print(f"Avg drilling hours/day: {fact['Drilling_Hours'].mean():.2f}")
    print(f"Total footage: {fact['Daily_Footage_ft'].sum():,.0f} ft")
    print(f"Total daily operating cost: ${fact['Daily_Cost_USD'].sum():,.0f}")
    print("\nNPT remains authoritative in FACT NPT; aggregate it separately in SQL/Power BI.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

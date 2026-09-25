from __future__ import annotations
from pathlib import Path
import sys
import numpy as np
import pandas as pd

SEED = 42
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RIG_FILE = RAW_DIR / "Dim_Rig.xlsx"
DAILY_FILE = RAW_DIR / "Fact_Drilling_Daily_Report.xlsx"
OUTPUT_FILE = RAW_DIR / "Fact_NPT.xlsx"

CATEGORIES = {
    "Mechanical": {
        "p": 0.050,
        "subs": ["Top Drive","Drawworks","Mud Pump","BOP / Well Control","Power Generation","Hydraulic System"],
        "roots": ["Component failure","Preventive maintenance issue","Electrical fault","Hydraulic issue"],
    },
    "Weather": {
        "p": 0.030,
        "subs": ["Heavy Rain","High Wind","Rough Seas","Lightning"],
        "roots": ["Weather suspension","Marine conditions","Reduced operating window"],
    },
    "Drilling": {
        "p": 0.055,
        "subs": ["Stuck Pipe","Lost Circulation","Wellbore Instability","Hole Cleaning","Fishing","Lost Time While Drilling"],
        "roots": ["Formation response","Drilling parameter issue","Hole cleaning","Wellbore condition"],
    },
    "Logistics": {
        "p": 0.030,
        "subs": ["Supply Boat Delay","Port Delay","Cement Delay","Mud / Chemical Supply","Equipment Delivery"],
        "roots": ["Late delivery","Marine logistics","Supplier delay","Inventory constraint"],
    },
    "Personnel": {
        "p": 0.012,
        "subs": ["Crew Change","Training","Personnel Availability","HSE Meeting"],
        "roots": ["Crew availability","Training requirement","Operational meeting"],
    },
}

DURATIONS = [2,4,6,8,12,18,24]
DURATION_WEIGHTS = np.array([0.35,0.30,0.18,0.10,0.05,0.015,0.005])

REQUIRED = [
    "Date","Well_ID","Rig_ID","Drilling_Hours",
    "Weather_Condition","Weather_Delay_hr","ROP_ft_hr"
]

def require_columns(df, cols, name):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")

def main():
    rng = np.random.default_rng(SEED)
    rig = pd.read_excel(RIG_FILE)
    daily = pd.read_excel(DAILY_FILE)

    require_columns(rig, ["Rig_ID","Day_Rate_USD"], "DIM RIG")
    require_columns(daily, REQUIRED, "FACT DAILY DRILLING REPORT")

    rig["Rig_ID"] = rig["Rig_ID"].astype(str)
    daily["Well_ID"] = daily["Well_ID"].astype(str)
    daily["Rig_ID"] = daily["Rig_ID"].astype(str)
    daily["Date"] = pd.to_datetime(daily["Date"], errors="coerce")

    day_rate = rig.set_index("Rig_ID")["Day_Rate_USD"].astype(float)
    records = []
    npt_id = 1

    for _, day in daily.iterrows():
        drilling = float(day["Drilling_Hours"])
        weather_delay = float(day["Weather_Delay_hr"])
        available = max(0.0, 24.0 - drilling - weather_delay)
        if available < 1.5:
            continue

        probs = {k: v["p"] for k, v in CATEGORIES.items()}
        weather = str(day["Weather_Condition"]).lower()
        if weather == "severe":
            probs["Weather"] *= 2.5
        elif weather == "moderate":
            probs["Weather"] *= 1.5
        if float(day["ROP_ft_hr"]) < 28:
            probs["Drilling"] *= 1.35

        total_p = sum(probs.values())
        if rng.random() >= min(0.22, total_p):
            continue

        event_count = 2 if available >= 6 and rng.random() < 0.10 else 1
        names = list(probs)
        chosen = rng.choice(
            names, size=event_count, replace=False,
            p=np.array(list(probs.values())) / total_p
        )

        remaining = available
        for cat in chosen:
            possible = [d for d in DURATIONS if d <= remaining + 1e-9]
            if not possible:
                break
            w = DURATION_WEIGHTS[:len(possible)]
            w = w / w.sum()
            duration = min(float(rng.choice(possible, p=w)), remaining)
            if duration < 1.5:
                break

            severity = (
                "Low" if duration <= 4 else
                "Medium" if duration <= 8 else
                "High" if duration <= 18 else
                "Critical"
            )
            cfg = CATEGORIES[str(cat)]
            sub = str(rng.choice(cfg["subs"]))
            root = str(rng.choice(cfg["roots"]))

            rid = str(day["Rig_ID"])
            if rid not in day_rate.index:
                raise ValueError(f"Unknown Rig_ID: {rid}")

            rig_cost = duration * float(day_rate.loc[rid]) / 24.0
            deferred = duration * float(rng.uniform(25000, 65000))
            total = rig_cost + deferred

            records.append({
                "NPT_ID": f"NPT{npt_id:05d}",
                "Date": day["Date"],
                "Well_ID": str(day["Well_ID"]),
                "Rig_ID": rid,
                "NPT_Category": str(cat),
                "NPT_Subcategory": sub,
                "Root_Cause": root,
                "Duration_hr": round(duration,1),
                "Severity": severity,
                "NPT_Rig_Cost_USD": round(rig_cost,2),
                "Deferred_Production_Impact_USD": round(deferred,2),
                "Total_Impact_USD": round(total,2),
            })
            npt_id += 1
            remaining -= duration
            if remaining < 1.5:
                break

    npt = pd.DataFrame(records)
    if npt.empty:
        raise RuntimeError("No NPT events generated.")

    if npt["NPT_ID"].duplicated().any():
        raise RuntimeError("Duplicate NPT_ID values found.")

    daily_keys = set(zip(daily["Well_ID"], daily["Date"]))
    if not set(zip(npt["Well_ID"], npt["Date"])).issubset(daily_keys):
        raise RuntimeError("Orphan NPT Well_ID + Date detected.")

    npt_daily = npt.groupby(["Well_ID","Date"])["Duration_hr"].sum()
    daily_idx = daily.set_index(["Well_ID","Date"])
    for key, hrs in npt_daily.items():
        d = daily_idx.loc[key]
        available = max(0.0, 24.0 - float(d["Drilling_Hours"]) - float(d["Weather_Delay_hr"]))
        if float(hrs) > available + 0.01:
            raise RuntimeError(f"NPT exceeds available time for {key}")

    npt = npt.sort_values(["Date","Well_ID","NPT_ID"]).reset_index(drop=True)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    npt.to_excel(OUTPUT_FILE, index=False, sheet_name="FACT NPT")

    print("="*72)
    print("PROJECT 01 — FACT NPT")
    print("="*72)
    print(f"Output: {OUTPUT_FILE}")
    print(f"NPT events: {len(npt):,}")
    print(f"Total NPT hours: {npt['Duration_hr'].sum():,.1f}")
    print(f"NPT rig cost: ${npt['NPT_Rig_Cost_USD'].sum():,.0f}")
    print(f"Total economic impact: ${npt['Total_Impact_USD'].sum():,.0f}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

import pandas as pd
import numpy as np

np.random.seed(42)

# =====================================================
# LOAD DATA
# =====================================================

df_daily = pd.read_excel("../data/raw/Fact_Drilling_Daily_Report.xlsx")
df_rig = pd.read_excel("../data/raw/Dim_Rig.xlsx")
df_well = pd.read_excel("../data/raw/Dim_Well.xlsx")

print(df_rig.columns)
print(df_well.columns)

# =====================================================
# MASTER DATA
# =====================================================

NPT_CATEGORIES = {

    "Mechanical":[
        "Top Drive Failure",
        "Mud Pump Failure",
        "BOP Repair",
        "Draw Works Failure",
        "Generator Failure",
        "Rotary Table Failure",
        "Power System Failure"
    ],

    "Weather":[
        "High Waves",
        "Strong Wind",
        "Heavy Rain",
        "Lightning",
        "Poor Visibility"
    ],

    "Drilling":[
        "Stuck Pipe",
        "Lost Circulation",
        "Well Control",
        "Fishing Operation",
        "Hole Cleaning",
        "Bit Failure"
    ],

    "Logistics":[
        "Waiting on Boat",
        "Waiting on Cement",
        "Waiting on Materials",
        "Fuel Supply Delay",
        "Delayed Helicopter"
    ],

    "Personnel":[
        "Crew Change",
        "Medical Evacuation",
        "Training",
        "Safety Stand Down"
    ]
}

ROOT_CAUSES = {

    "Mechanical":[
        "Equipment Wear",
        "Hydraulic Failure",
        "Electrical Failure",
        "Poor Preventive Maintenance",
        "OEM Defect"
    ],

    "Weather":[
        "High Waves",
        "Storm",
        "Heavy Rain",
        "Strong Wind",
        "Lightning"
    ],

    "Drilling":[
        "Formation Instability",
        "Differential Sticking",
        "Bit Wear",
        "Unexpected Pressure"
    ],

    "Logistics":[
        "Late Supply Vessel",
        "Material Shortage",
        "Port Congestion",
        "Customs Clearance"
    ],

    "Personnel":[
        "Crew Rotation",
        "Medical Emergency",
        "Training Requirement"
    ]
}

RESPONSIBLE_PARTIES = {

    "Mechanical":[
        "Drilling Contractor",
        "Maintenance Team",
        "OEM Vendor"
    ],

    "Weather":[
        "Marine Operations",
        "Weather"
    ],

    "Drilling":[
        "Operator",
        "Directional Drilling",
        "Mud Engineering"
    ],

    "Logistics":[
        "Supply Chain",
        "Marine Logistics",
        "Procurement"
    ],

    "Personnel":[
        "HR",
        "Rig Management",
        "Medical Team"
    ]
}

CORRECTIVE_ACTIONS = {

    "Mechanical":[
        "Replace Equipment",
        "Repair Component",
        "Preventive Maintenance",
        "OEM Inspection"
    ],

    "Weather":[
        "Suspend Operations",
        "Resume Operations",
        "Wait on Weather"
    ],

    "Drilling":[
        "Condition Hole",
        "Run Fishing Tools",
        "Increase Mud Weight",
        "Adjust Drilling Parameters"
    ],

    "Logistics":[
        "Mobilize Supply Vessel",
        "Expedite Shipment",
        "Air Freight Materials"
    ],

    "Personnel":[
        "Crew Replacement",
        "Medical Clearance",
        "Safety Briefing"
    ]
}

# =====================================================
# FUNCTIONS
# =====================================================

def get_season(date):

    if date.month in [5,6,7,8]:
        return "Long Rainy Season"

    elif date.month in [11,12,1]:
        return "Short Rainy Season"

    return "Dry Season"


def get_severity(duration):

    if duration <= 4:
        return "Low"

    elif duration <= 12:
        return "Medium"

    return "High"


def get_probabilities(season, rig_age, water_depth):

    p = {
        "Mechanical":0.30,
        "Weather":0.15,
        "Drilling":0.25,
        "Logistics":0.20,
        "Personnel":0.10
    }

    if season == "Long Rainy Season":
        p["Weather"] += 0.20
        p["Mechanical"] -= 0.10
        p["Logistics"] -= 0.05
        p["Personnel"] -= 0.05

    if rig_age >= 20:
        p["Mechanical"] += 0.10
        p["Drilling"] -= 0.05
        p["Personnel"] -= 0.05

    if water_depth == "Ultra Deepwater":
        p["Drilling"] += 0.10
        p["Logistics"] -= 0.05
        p["Personnel"] -= 0.05

    total = sum(p.values())

    for k in p:
        p[k] /= total

    return p


# =====================================================
# GENERATE FACT TABLE
# =====================================================

records = []

npt_id = 1

print(f"Daily drilling records: {len(df_daily)}")

for _, row in df_daily.iterrows():

    # 15% probability of NPT

    if np.random.rand() > 0.15:
        continue

    date = pd.to_datetime(row["Date"])

    month = date.month_name()

    quarter = f"Q{date.quarter}"

    season = get_season(date)

    rig = df_rig[df_rig["Rig_ID"] == row["Rig_ID"]].iloc[0]

    well = df_well[df_well["Well_ID"] == row["Well_ID"]].iloc[0]

    rig_age = 2026 - rig["Year_Built"]

    water_depth = well["Water_Depth_Category"]

    probabilities = get_probabilities(
        season,
        rig_age,
        water_depth
    )

    category = np.random.choice(
        list(probabilities.keys()),
        p=list(probabilities.values())
    )

    subcategory = np.random.choice(NPT_CATEGORIES[category])

    root_cause = np.random.choice(ROOT_CAUSES[category])

    responsible_party = np.random.choice(RESPONSIBLE_PARTIES[category])

    corrective_action = np.random.choice(CORRECTIVE_ACTIONS[category])

    duration = np.random.choice(
        [2,4,6,8,12,18,24],
        p=[0.25,0.25,0.20,0.15,0.08,0.05,0.02]
    )

    severity = get_severity(duration)

    # Duration bucket
    if duration <= 4:
   
      duration_bucket = "Minor"

    elif duration <= 8:
    
      duration_bucket = "Moderate"

    elif duration <= 18:

      duration_bucket = "Major"

    else:

      duration_bucket = "Critical"


    downtime_type = np.random.choice(
        ["Planned","Unplanned"],
        p=[0.08,0.92]
    )

    shift = np.random.choice(
        ["Day","Night"],
        p=[0.55,0.45]
    )

    action_status = np.random.choice(
        ["Open","In Progress","Closed"],
        p=[0.10,0.20,0.70]
    )

    hourly_rate = rig["Day_Rate_USD"] / 24

    direct_cost = int(hourly_rate * duration)

    deferred_cost = int(
        direct_cost * np.random.uniform(0.5,2.5)
    )

    total_cost = direct_cost + deferred_cost

    # Cost bucket
    if total_cost < 100000:

        cost_bucket = "< $100K"
    
    elif total_cost < 250000:
        
        cost_bucket = "$100K - $250K"

    elif total_cost < 500000:
        
        cost_bucket = "$250K - $500K"
    
    elif total_cost < 1000000:
        
        cost_bucket = "$500K - $1M"
    
    else:
        
        cost_bucket = "> $1M"

    records.append({

        "NPT_ID":f"NPT{npt_id:05d}",

        "Date":date,

        "Well_ID":row["Well_ID"],

        "Rig_ID":row["Rig_ID"],

        "Rig_Age":rig_age,

        "Rig_Name": rig["Rig_Name"],

        "Rig_Type": rig["Rig_Type"],

        "Contractor": rig["Contractor"],

        "Rig_Status": rig["Rig_Status"],

        "Rig_Age": rig_age,
        
        "Rig_Day_Rate": rig["Day_Rate_USD"],

        "Operator": well["Operator"],

        "Block": well["Block"],

        "Well_Type": well["Well_Type"],

        "Country": well["Country"],

        "Water_Depth_ft": well["Water_Depth_ft"],

        "Target_Depth_ft": well["Target_Depth_ft"],

        "Mechanical_Flag": 1 if category=="Mechanical" else 0,
        
        "Weather_Flag": 1 if category=="Weather" else 0,
        
        "Drilling_Flag": 1 if category=="Drilling" else 0,
        
        "Logistics_Flag": 1 if category=="Logistics" else 0,
        
        "Personnel_Flag": 1 if category=="Personnel" else 0,

        "NPT_Flag": 1,
        
        "Lost_Drilling_Days": round(duration / 24, 2),
        
        "Productivity_Loss_pct": round(duration / 24 * 100, 1),

        "NPT_Category":category,

        "NPT_Subcategory":subcategory,

        "Root_Cause":root_cause,

        "Responsible_Party":responsible_party,

        "Duration_hr":duration,

        "Cost_USD":direct_cost,

        "Deferred_Cost_USD":deferred_cost,

        "Total_Impact_USD":total_cost,

        "Duration_Bucket": duration_bucket,

        "Cost_Bucket": cost_bucket,

        "Severity":severity,

        "Downtime_Type":downtime_type,

        "Shift":shift,

        "Corrective_Action":corrective_action,

        "Action_Status":action_status,

        "Month":month,

        "Quarter":quarter,

        "Season":season

    })

    npt_id += 1

# =====================================================
# SAVE
# =====================================================

fact_npt = pd.DataFrame(records)

fact_npt["Date"] = fact_npt["Date"].dt.strftime("%d-%m-%Y")

fact_npt.to_excel(
    "../data/raw/Fact_NPT.xlsx",
    index=False
)

print(f"\nNPT Records Generated: {len(fact_npt)}")

print(fact_npt.head())

print(fact_npt.describe(include="all"))
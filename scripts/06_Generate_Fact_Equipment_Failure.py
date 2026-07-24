import pandas as pd
import numpy as np

np.random.seed(42)

df_npt = pd.read_excel("../data/raw/Fact_NPT.xlsx")
df_rig = pd.read_excel("../data/raw/Dim_Rig.xlsx")

FAILURE_CODES = {
    "Top Drive Failure": "EQ001",
    "Mud Pump Failure": "EQ002",
    "BOP Repair": "EQ003",
    "Generator Failure": "EQ004",
    "Draw Works Failure": "EQ005",
    "Rotary Table Failure": "EQ006",
    "Power System Failure": "EQ007"
}

FAILURE_CAUSE = {

    "Top Drive Failure":[
        "Bearing Failure",
        "Gearbox Failure",
        "Hydraulic Leak"
    ],

    "Mud Pump Failure":[
        "Liner Wear",
        "Piston Failure",
        "Valve Damage"
    ],

    "BOP Repair":[
        "Seal Failure",
        "Hydraulic Leak",
        "Control Failure"
    ],

    "Generator Failure":[
        "Engine Failure",
        "Electrical Fault",
        "Cooling Failure"
    ],

    "Draw Works Failure":[
        "Brake Failure",
        "Gearbox Damage"
    ],

    "Rotary Table Failure":[
        "Motor Failure",
        "Bearing Wear"
    ],

    "Power System Failure":[
        "Electrical Short",
        "Transformer Failure"
    ]

}

REPAIR_ACTIONS = [

    "Replace Component",
    "Repair Component",
    "OEM Service",
    "Preventive Maintenance",
    "Calibration",
    "Functional Test"

]

FAILURE_STATUS = [

    "Closed",
    "Closed",
    "Closed",
    "In Progress"

]

records = []

failure_id = 1

mechanical = df_npt[df_npt["NPT_Category"]=="Mechanical"]

print("Mechanical Events:",len(mechanical))

for _, row in mechanical.iterrows():

    equipment = row["NPT_Subcategory"]

# -------------------------
# Equipment hierarchy
# -------------------------

    equipment_system = np.random.choice([
        "Hoisting",
        "Circulating",
        "Rotating",
        "Well Control",
        "Power",
        "Marine"
    ])

    equipment_subsystem = np.random.choice([
        "Top Drive",
        "Mud Pumps",
        "Drawworks",
        "BOP",
        "Generator",
        "Thrusters"
    ])

    component = np.random.choice([
        "Hydraulic Pump",
        "Gearbox",
        "Bearing",
        "Motor",
        "Seal",
        "Control Module"
    ])

    oem = np.random.choice([
        "NOV",
        "Cameron",
        "Caterpillar",
        "MH Wirth",
        "GE Oil & Gas",
        "ABB"
    ])

    root_cause = np.random.choice(FAILURE_CAUSE[equipment])

    failure_mechanism = np.random.choice([
        "Fatigue",
        "Corrosion",
        "Wear",
        "Electrical",
        "Hydraulic",
        "Overheating"
    ])

    failure_type = np.random.choice(
        ["Sudden", "Progressive"],
        p=[0.65,0.35]
    )

    criticality = np.random.choice(
        ["Low","Medium","High","Critical"],
        p=[0.15,0.35,0.35,0.15]
    )

    repeat_failure = np.random.choice(
        ["Yes","No"],
        p=[0.20,0.80]
    )

    failure_priority = np.random.choice(
    ["P1", "P2", "P3", "P4"],
    p=[0.10, 0.30, 0.40, 0.20]
)
    
    failure_status = np.random.choice(
    ["Open", "Closed", "Under Investigation"],
    p=[0.05, 0.85, 0.10]
)
    
    repair_action = np.random.choice(
        REPAIR_ACTIONS
    )
        
    status = np.random.choice(
        FAILURE_STATUS
    )
        

    rig = df_rig[df_rig["Rig_ID"]==row["Rig_ID"]].iloc[0]
        
    mttr = np.random.randint(2,18)

        # Repair cost
    repair_cost = int(
        rig["Day_Rate_USD"] / 24 * mttr * np.random.uniform(1.5, 4.5)
    )

    # Downtime cost
    downtime_cost = int(
        rig["Day_Rate_USD"] / 24 * mttr
    )

    # Revenue loss
    revenue_loss = np.random.randint(
        50000,
        1500000
    )

    # Total cost
    total_failure_cost = (
        repair_cost
        + downtime_cost
        + revenue_loss
    )

    maintenance_type = np.random.choice(
        [
            "Corrective",
            "Preventive",
            "Predictive",
            "Emergency"
        ],
        p=[0.55,0.15,0.10,0.20]
    )

    downtime_cost = int(
        rig["Day_Rate_USD"] / 24 * mttr
    )

    total_failure_cost = (
        repair_cost
        + downtime_cost
        + revenue_loss
    )

    repair_team = np.random.choice([
        "Rig Maintenance",
        "OEM Service",
        "Electrical Team",
        "Mechanical Team"
    ])

    
    technicians = np.random.randint(2,8)

    labor_hours = technicians * mttr

        
    mtbf = np.random.randint(150,1200)

    spare_required = np.random.choice(
        ["Yes","No"],
        p=[0.70,0.30]
    )

    spare_part = np.random.choice([
        "Seal Kit",
        "Bearing",
        "Hydraulic Hose",
        "Electric Motor",
        "Gearbox",
        "Control Card"
    ])

    lead_time = np.random.randint(1,30)

    deferred_footage = np.random.randint(
        100,
        1200
    )

    deferred_production = np.random.randint(
        500,
        8000
    )

    revenue_loss = np.random.randint(
        50000,
        1500000
    )

    severity = row["Severity"]

    downtime = row["Duration_hr"]

    repair_cost = row["Cost_USD"]

    # Duration Bucket
    if mttr <= 4:
        duration_bucket = "0-4 hr"

    elif mttr <= 8:
        duration_bucket = "4-8 hr"

    elif mttr <= 12:
        duration_bucket = "8-12 hr"

    else:
        duration_bucket = ">12 hr"

    # Cost Bucket
    if repair_cost < 50000:
        cost_bucket = "<50k"

    elif repair_cost < 150000:
        cost_bucket = "50k-150k"

    elif repair_cost < 300000:
        cost_bucket = "150k-300k"

    else:
        cost_bucket = ">300k"

    records.append({

    "Failure_ID":f"EQF{failure_id:05d}",

    "Date":row["Date"],

    "Well_ID": row["Well_ID"],   

    "Rig_ID":row["Rig_ID"],

    "Rig_Name":rig["Rig_Name"],

    "Contractor":rig["Contractor"],

    "Rig_Type":rig["Rig_Type"],

    "Equipment":equipment,

    "Equipment_System": equipment_system,

    "Equipment_Subsystem": equipment_subsystem,

    "Component": component,

    "OEM": oem,

    "Failure_Code":FAILURE_CODES[equipment],

    "Failure_Category":"Mechanical",

    "Failure_Cause":root_cause,

    "Failure_Mechanism": failure_mechanism,

    "Failure_Type": failure_type,

    "Criticality": criticality,

    "Repeat_Failure": repeat_failure,

    "Maintenance_Type": maintenance_type,

    "Repair_Team": repair_team,

    "Repair_Cost_USD": repair_cost,

    "Downtime_Cost_USD": downtime_cost,

    "Revenue_Loss_USD": revenue_loss,

    "Total_Failure_Cost_USD": total_failure_cost,

    "Technicians": technicians,

    "Labor_Hours": labor_hours,

    "Spare_Part_Required": spare_required,

    "Spare_Part": spare_part,

    "Lead_Time_Days": lead_time,

    "Deferred_Footage_ft": deferred_footage,

    "Deferred_Production_bbl": deferred_production,

    "Revenue_Loss_USD": revenue_loss,

    "Duration_Bucket": duration_bucket,

    "Cost_Bucket": cost_bucket,

    "Repair_Action":repair_action,

    "Repair_Status":status,

    "Severity":severity,

    "Downtime_hr":downtime,

    "Repair_Cost_USD":repair_cost,

    "MTTR_hr":mttr,

    "MTBF_hr":mtbf,

    "Year_Built":rig["Year_Built"],

    "Rig_Age":2026-rig["Year_Built"]

    })

    failure_id += 1

fact_equipment = pd.DataFrame(records)

fact_equipment.to_excel(
    "../data/raw/Fact_Equipment_Failure.xlsx",
    index=False
)

print()

print("Equipment Failures:",len(fact_equipment))

print()

print(fact_equipment.head())

print()

print(fact_equipment.describe(include="all"))
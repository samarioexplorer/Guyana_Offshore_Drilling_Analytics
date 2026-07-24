# ============================================================
# FACT_BHA_RUN GENERATOR
# VERSION 2.3
# Guyana Offshore Drilling Analytics
# ============================================================

import pandas as pd
import numpy as np
import random
from pathlib import Path

# ------------------------------------------------------------
# RANDOM SEED
# ------------------------------------------------------------

random.seed(42)
np.random.seed(42)

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

BASE_PATH = Path("../data/raw")

# ------------------------------------------------------------
# LOAD SOURCE TABLES
# ------------------------------------------------------------

df_well = pd.read_excel(BASE_PATH / "Dim_Well.xlsx")

df_rig = pd.read_excel(BASE_PATH / "Dim_Rig.xlsx")

df_failure = pd.read_excel(BASE_PATH / "Fact_Equipment_Failure.xlsx")

df_npt = pd.read_excel(BASE_PATH / "Fact_NPT.xlsx")

# ------------------------------------------------------------
# DATE CONVERSION
# ------------------------------------------------------------

df_failure["Date"] = pd.to_datetime(
    df_failure["Date"],
    dayfirst=True
)

df_npt["Date"] = pd.to_datetime(
    df_npt["Date"],
    dayfirst=True
)

df_well["Spud_Date"] = pd.to_datetime(
    df_well["Spud_Date"],
    dayfirst=True
)

# ------------------------------------------------------------
# BASIC VALIDATION
# ------------------------------------------------------------

print()

print("="*60)
print("SOURCE TABLES")
print("="*60)

print(f"Wells Loaded                : {len(df_well)}")
print(f"Rigs Loaded                 : {len(df_rig)}")
print(f"NPT Events                  : {len(df_npt)}")
print(f"Equipment Failures          : {len(df_failure)}")

print()

# ------------------------------------------------------------
# GLOBAL PARAMETERS
# ------------------------------------------------------------

MAX_BHA_RUNS = 12

MIN_FOOTAGE = 400

MAX_FOOTAGE = 6500

RIG_UTILIZATION = 0.97

WEATHER_DOWNTIME_FACTOR = 0.03

SAFETY_FACTOR = 1.15

# ------------------------------------------------------------
# GLOBAL COUNTERS
# ------------------------------------------------------------

bha_counter = 1

records = []

print("Initialization completed.")

print()

# ============================================================
# WELL PROGRAM
# ============================================================

WELL_PROGRAM = [

    {
        "Hole_Section": '36"',
        "Bit_Size_in": 36.0,
        "Top": 0,
        "Base": 300,
        "Min_Run": 1,
        "Max_Run": 1
    },

    {
        "Hole_Section": '26"',
        "Bit_Size_in": 26.0,
        "Top": 300,
        "Base": 2500,
        "Min_Run": 1,
        "Max_Run": 2
    },

    {
        "Hole_Section": '17-1/2"',
        "Bit_Size_in": 17.5,
        "Top": 2500,
        "Base": 8000,
        "Min_Run": 2,
        "Max_Run": 3
    },

    {
        "Hole_Section": '12-1/4"',
        "Bit_Size_in": 12.25,
        "Top": 8000,
        "Base": 13500,
        "Min_Run": 2,
        "Max_Run": 3
    },

    {
        "Hole_Section": '8-1/2"',
        "Bit_Size_in": 8.5,
        "Top": 13500,
        "Base": 18500,
        "Min_Run": 2,
        "Max_Run": 4
    }

]

# ============================================================
# GEOLOGICAL MODEL
# ============================================================

FORMATION_PROFILE = {

    '36"': {

        "Formation": "Seabed",
        "Lithology": "Soft Clay",
        "UCS": 300,
        "Abrasiveness": 0.20,
        "ROP": 220,
        "Mud_Weight": (8.5,8.8),
        "Pore_Pressure": 8.6,
        "Fracture_Gradient": 10.5

    },

    '26"': {

        "Formation": "Surface Sands",
        "Lithology": "Sandstone",
        "UCS": 2500,
        "Abrasiveness": 0.35,
        "ROP": 160,
        "Mud_Weight": (9.0,9.8),
        "Pore_Pressure": 9.2,
        "Fracture_Gradient": 11.8

    },

    '17-1/2"': {

        "Formation": "Upper Campanian",
        "Lithology": "Shale",
        "UCS": 8500,
        "Abrasiveness": 0.60,
        "ROP": 80,
        "Mud_Weight": (11.0,12.2),
        "Pore_Pressure": 11.5,
        "Fracture_Gradient": 14.8

    },

    '12-1/4"': {

        "Formation": "Lower Campanian",
        "Lithology": "Siltstone",
        "UCS": 14000,
        "Abrasiveness": 0.85,
        "ROP": 45,
        "Mud_Weight": (13.0,14.5),
        "Pore_Pressure": 13.8,
        "Fracture_Gradient": 16.8

    },

    '8-1/2"': {

        "Formation": "Reservoir Sand",
        "Lithology": "Sandstone",
        "UCS": 6500,
        "Abrasiveness": 0.55,
        "ROP": 65,
        "Mud_Weight": (14.5,15.8),
        "Pore_Pressure": 15.2,
        "Fracture_Gradient": 18.0

    }

}

# ============================================================
# DIRECTIONAL TRAJECTORY
# ============================================================

TRAJECTORY = {

    '36"': {

        "Inc_Start": 0,
        "Inc_End": 2,
        "Dogleg": 0.5

    },

    '26"': {

        "Inc_Start": 2,
        "Inc_End": 8,
        "Dogleg": 1.0

    },

    '17-1/2"': {

        "Inc_Start": 8,
        "Inc_End": 35,
        "Dogleg": 2.5

    },

    '12-1/4"': {

        "Inc_Start": 35,
        "Inc_End": 60,
        "Dogleg": 3.0

    },

    '8-1/2"': {

        "Inc_Start": 60,
        "Inc_End": 90,
        "Dogleg": 2.0

    }

}

# ============================================================
# BIT LIBRARY
# ============================================================

BIT_LIBRARY = {

    "PDC": {

        "Manufacturers": ["SLB","Baker Hughes","NOV","Ulterra"],

        "Models": ["MDSi616","FXD616","Tektonic","Kymera"],

        "Life": 320

    },

    "Hybrid": {

        "Manufacturers": ["Baker Hughes","NOV","Varel"],

        "Models": ["Kymera","Tektonic","XR616"],

        "Life": 220

    },

    "Roller Cone": {

        "Manufacturers": ["Varel","NOV"],

        "Models": ["XR616","MDSi616"],

        "Life": 140

    }

}

# ============================================================
# DOWNHOLE TOOLS
# ============================================================

MOTOR_TYPES = [

    "Conventional",
    "High Performance",
    "Mud Motor"

]

RSS_TYPES = [

    "None",
    "PowerDrive",
    "AutoTrak"

]

MWD_SERVICES = [

    "SLB",
    "Halliburton",
    "Baker Hughes"

]

# ============================================================
# BIT DULL GRADES
# ============================================================

BIT_DULL_GRADES = [

    "1-1-WT-A-X-I-NO-TD",
    "2-2-WT-A-X-I-NO-TD",
    "3-3-WT-A-X-I-BT-PR",
    "4-4-WT-A-X-I-BT-WT"

]

# ============================================================
# IADC FORMATION CODES
# ============================================================

IADC_CODES = [

    "111",
    "115",
    "215",
    "517",
    "537",
    "617"

]

print("Engineering libraries loaded.")
print()

# ============================================================
# START WELL SIMULATION
# ============================================================

for _, well in df_well.iterrows():

    # --------------------------------------------------------
    # WELL INFORMATION
    # --------------------------------------------------------

    well_id = well["Well_ID"]
    rig_id = well["Rig_ID"]

    current_depth = 0

    run_number = 1

    current_date = pd.to_datetime(
        well["Spud_Date"]
    )

    current_inclination = 0.0

    current_azimuth = random.uniform(0,360)

    # ========================================================
    # LOOP THROUGH WELL PROGRAM
    # ========================================================

    for section in WELL_PROGRAM:

        hole_section = section["Hole_Section"]

        bit_size = section["Bit_Size_in"]

        section_top = section["Top"]

        section_base = section["Base"]

        current_depth = max(
            current_depth,
            section_top
        )

        # ----------------------------------------------------
        # ENGINEERING LIBRARIES
        # ----------------------------------------------------

        geology = FORMATION_PROFILE[hole_section]

        trajectory = TRAJECTORY[hole_section]

        formation = geology["Formation"]

        lithology = geology["Lithology"]

        ucs = geology["UCS"]

        abrasiveness = geology["Abrasiveness"]

        formation_rop = geology["ROP"]

        pore_pressure = geology["Pore_Pressure"]

        fracture_gradient = geology["Fracture_Gradient"]

        # ----------------------------------------------------
        # DRILL SECTION UNTIL TD IS REACHED
        # ----------------------------------------------------

        while current_depth < section_base:

            # ================================================
            # START DEPTH
            # ================================================

            start_depth = current_depth

            remaining_interval = section_base - start_depth

            # ================================================
            # FOOTAGE MODEL
            # ================================================

            if hole_section == '36"':

                target_footage = random.randint(
                    250,
                    350
                )

            elif hole_section == '26"':

                target_footage = random.randint(
                    800,
                    2200
                )

            elif hole_section == '17-1/2"':

                target_footage = random.randint(
                    1500,
                    3200
                )

            elif hole_section == '12-1/4"':

                target_footage = random.randint(
                    1800,
                    3200
                )

            else:

                target_footage = random.randint(
                    1200,
                    2600
                )

            footage = min(
                target_footage,
                remaining_interval
            )

            end_depth = start_depth + footage

            current_depth = end_depth

            # ================================================
            # DATES
            # ================================================

            average_rop = formation_rop * random.uniform(
                0.85,
                1.15
            )

            rotating_hours = footage / average_rop

            sliding_hours = rotating_hours * random.uniform(
                0.10,
                0.35
            )

            circulating_hours = rotating_hours + sliding_hours

            connection_hours = footage / 100 * random.uniform(
                0.15,
                0.30
            )

            reaming_hours = random.uniform(
                0.5,
                3.0
            )

            total_hours = (

                circulating_hours +

                connection_hours +

                reaming_hours

            )

            days_on_bha = total_hours / 24

            start_date = current_date

            end_date = start_date + pd.Timedelta(
                days=days_on_bha
            )

            current_date = end_date

            # ================================================
            # CALENDAR
            # ================================================

            year = end_date.year

            quarter = f"Q{((end_date.month-1)//3)+1}"

            month = end_date.strftime("%B")

                # ========================================================
            # DIRECTIONAL MODEL
            # ========================================================

            target_inc = random.uniform(
                trajectory["Inc_Start"],
                trajectory["Inc_End"]
            )

            inclination = round(
                max(current_inclination, target_inc),
                1
            )

            current_inclination = inclination

            current_azimuth += random.uniform(-4, 4)

            if current_azimuth < 0:
                current_azimuth += 360

            if current_azimuth > 360:
                current_azimuth -= 360

            azimuth = round(current_azimuth, 1)

            dogleg = round(
                trajectory["Dogleg"] *
                random.uniform(0.80, 1.20),
                2
            )

            # ========================================================
            # BIT SELECTION
            # ========================================================

            if hole_section in ['36"', '26"']:

                bit_type = "Roller Cone"

            elif hole_section == '17-1/2"':

                bit_type = random.choice(
                    ["Roller Cone", "Hybrid"]
                )

            else:

                bit_type = random.choice(
                    ["Hybrid", "PDC"]
                )

            bit_library = BIT_LIBRARY[bit_type]

            bit_manufacturer = random.choice(
                bit_library["Manufacturers"]
            )

            bit_model = random.choice(
                bit_library["Models"]
            )

            base_bit_life = bit_library["Life"]

            # ========================================================
            # DOWNHOLE TOOLS
            # ========================================================

            if hole_section in ['36"', '26"']:

                rss_type = "None"

                motor_type = "Conventional"

            else:

                rss_type = random.choice(RSS_TYPES)

                motor_type = random.choice(MOTOR_TYPES)

            mwd_service = random.choice(
                MWD_SERVICES
            )

            # ========================================================
            # MUD PROGRAM
            # ========================================================

            mud_weight = round(

                random.uniform(
                    geology["Mud_Weight"][0],
                    geology["Mud_Weight"][1]
                ),

                1

            )

            # ========================================================
            # DRILLING PARAMETERS
            # ========================================================

            if hole_section == '36"':

                wob = random.randint(20, 40)

                rpm = random.randint(60, 90)

                flow_rate = random.randint(900, 1200)

            elif hole_section == '26"':

                wob = random.randint(30, 50)

                rpm = random.randint(70, 110)

                flow_rate = random.randint(800, 1100)

            elif hole_section == '17-1/2"':

                wob = random.randint(35, 55)

                rpm = random.randint(100, 160)

                flow_rate = random.randint(650, 900)

            elif hole_section == '12-1/4"':

                wob = random.randint(20, 40)

                rpm = random.randint(120, 180)

                flow_rate = random.randint(450, 700)

            else:

                wob = random.randint(15, 30)

                rpm = random.randint(140, 220)

                flow_rate = random.randint(300, 500)

            # ========================================================
            # HYDRAULICS
            # ========================================================

            pump_pressure = int(

                700 +

                (mud_weight * 140) +

                (flow_rate * 1.8) +

                (current_depth / 18)

            )

            # ========================================================
            # ROP MODEL
            # ========================================================

            rop_factor = random.uniform(0.85, 1.15)

            average_rop = round(

                formation_rop *

                rop_factor,

                1

            )

            maximum_rop = round(

                average_rop *

                random.uniform(1.15, 1.35),

                1

            )

            minimum_rop = round(

                average_rop *

                random.uniform(0.55, 0.80),

                1

            )

            # ========================================================
            # TVD
            # ========================================================

            true_vertical_depth = round(

                end_depth *

                np.cos(np.radians(inclination)),

                0

            )

                # ========================================================
            # BIT LIFE MODEL
            # ========================================================

            wear_factor = abrasiveness * (ucs / 8000)

            bit_life = max(
                80,
                base_bit_life / wear_factor
            )

            bit_hours = rotating_hours

            bit_wear_pct = round(

                min(
                    100,
                    (bit_hours / bit_life) * 100
                ),

                1

            )

            # ========================================================
            # BIT DULL GRADE
            # ========================================================

            if bit_wear_pct < 20:

                bit_dull_grade = "1-1-WT-A-X-I-NO-TD"

            elif bit_wear_pct < 45:

                bit_dull_grade = "2-2-WT-A-X-I-NO-TD"

            elif bit_wear_pct < 75:

                bit_dull_grade = "3-3-WT-A-X-I-BT-PR"

            else:

                bit_dull_grade = "4-4-WT-A-X-I-BT-WT"

            iadc_code = random.choice(IADC_CODES)

            # ========================================================
            # EQUIPMENT RELIABILITY
            # ========================================================

            motor_hours = circulating_hours

            rss_hours = circulating_hours if rss_type != "None" else 0

            mwd_hours = circulating_hours

            motor_failure_probability = motor_hours / 500

            rss_failure_probability = rss_hours / 700

            mwd_failure_probability = mwd_hours / 900

            failure_score = (

                motor_failure_probability +

                rss_failure_probability +

                mwd_failure_probability

            )

            if failure_score > 1.8:

                mechanical_failures = random.randint(2,4)

            elif failure_score > 1.0:

                mechanical_failures = random.randint(1,2)

            else:

                mechanical_failures = 0

            # ========================================================
            # PULL REASON
            # ========================================================

            if bit_wear_pct > 85:

                pull_reason = "Bit Worn"

            elif mechanical_failures > 0:

                pull_reason = random.choice([

                    "Motor Failure",

                    "BHA Failure"

                ])

            elif current_depth >= section_base:

                pull_reason = "Section TD"

            else:

                pull_reason = "Poor ROP"

            # ========================================================
            # NPT MODEL
            # ========================================================

            npt_period = df_npt[

                (df_npt["Well_ID"] == well_id)

                &

                (df_npt["Date"] >= start_date)

                &

                (df_npt["Date"] <= end_date)

            ]

            npt_hours = round(

                npt_period["Duration_hr"].sum(),

                1

            )

            if mechanical_failures > 0:

                npt_hours += random.randint(4,12)

            npt_pct = round(

                (npt_hours / total_hours) * 100,

                1

            )

            # ========================================================
            # COST MODEL
            # ========================================================

            bit_cost = random.randint(

                35000,

                90000

            )

            motor_cost = random.randint(

                25000,

                75000

            )

            rss_cost = 0

            if rss_type != "None":

                rss_cost = random.randint(

                    90000,

                    180000

                )

            mwd_cost = random.randint(

                25000,

                60000

            )

            services_cost = random.randint(

                15000,

                45000

            )

            rig_day_rate = random.randint(

                350000,

                500000

            )

            rig_cost = round(

                rig_day_rate *

                days_on_bha,

                0

            )

            mud_cost = round(

                footage *

                mud_weight *

                1.4,

                0

            )

            logistics_cost = random.randint(

                8000,

                25000

            )

            personnel_cost = round(

                days_on_bha *

                18000,

                0

            )

            fuel_cost = round(

                days_on_bha *

                14000,

                0

            )

            total_bha_cost = (

                bit_cost +

                motor_cost +

                rss_cost +

                mwd_cost

            )

            total_run_cost = (

                total_bha_cost +

                services_cost +

                rig_cost +

                mud_cost +

                logistics_cost +

                personnel_cost +

                fuel_cost

            )

            cost_per_foot = round(

                total_run_cost /

                footage,

                2

            )

            # ========================================================
            # RUN EFFICIENCY
            # ========================================================

            run_efficiency_pct = round(

                max(

                    0,

                    100 -

                    npt_pct -

                    bit_wear_pct * 0.05

                ),

                1

            )

            # ========================================================
            # ROP CATEGORY
            # ========================================================

            if average_rop >= 0.95 * formation_rop:

                rop_category = "Excellent"

            elif average_rop >= 0.80 * formation_rop:

                rop_category = "Good"

            elif average_rop >= 0.65 * formation_rop:

                rop_category = "Average"

            else:

                rop_category = "Poor"

            # ========================================================
            # COST CATEGORY
            # ========================================================

            if cost_per_foot < 150:

                cost_category = "Low"

            elif cost_per_foot < 250:

                cost_category = "Medium"

            elif cost_per_foot < 350:

                cost_category = "High"

            else:

                cost_category = "Very High"

            # ========================================================
            # BHA SUCCESS
            # ========================================================

            score = 100

            score -= npt_pct

            score -= bit_wear_pct * 0.10

            score -= mechanical_failures * 12

            if score >= 90:

                bha_success = "Excellent"

            elif score >= 75:

                bha_success = "Good"

            elif score >= 60:

                bha_success = "Average"

            else:

                bha_success = "Poor"

            # ========================================================
            # CREATE RECORD
            # ========================================================

            records.append({

                "BHA_Run_ID": f"BHAR{bha_counter:05d}",

                "Well_ID": well_id,

                "Rig_ID": rig_id,

                "Run_Number": run_number,

                "Start_Date": start_date,

                "End_Date": end_date,

                "Year": year,

                "Quarter": quarter,

                "Month": month,

                "Days_On_BHA": round(days_on_bha,2),

                "Start_Depth_ft": start_depth,

                "End_Depth_ft": end_depth,

                "Footage_ft": footage,

                "True_Vertical_Depth_ft": true_vertical_depth,

                "Hole_Section": hole_section,

                "Formation": formation,

                "Lithology": lithology,

                "UCS_psi": ucs,

                "Abrasiveness_Index": abrasiveness,

                "Pore_Pressure_ppg": pore_pressure,

                "Fracture_Gradient_ppg": fracture_gradient,

                "Bit_Manufacturer": bit_manufacturer,

                "Bit_Model": bit_model,

                "Bit_Type": bit_type,

                "Bit_Size_in": bit_size,

                "Motor_Type": motor_type,

                "RSS_Type": rss_type,

                "MWD_Service": mwd_service,

                "Bit_Dull_Grade": bit_dull_grade,

                "Bit_Hours": round(bit_hours,1),

                "Bit_Life_hr": round(bit_life,1),

                "Bit_Wear_pct": bit_wear_pct,

                "IADC_Code": iadc_code,

                "Inclination_deg": inclination,

                "Azimuth_deg": azimuth,

                "Dogleg_Severity_deg_100ft": dogleg,

                "Average_ROP_ft_hr": average_rop,

                "Maximum_ROP_ft_hr": maximum_rop,

                "Minimum_ROP_ft_hr": minimum_rop,

                "Average_Mud_Weight_ppg": mud_weight,

                "Flow_Rate_gpm": flow_rate,

                "Pump_Pressure_psi": pump_pressure,

                "Weight_On_Bit_klbs": wob,

                "RPM": rpm,

                "Rotating_Hours": round(rotating_hours,1),

                "Sliding_Hours": round(sliding_hours,1),

                "Circulating_Hours": round(circulating_hours,1),

                "Connection_Hours": round(connection_hours,1),

                "Reaming_Hours": round(reaming_hours,1),

                "Motor_Hours": round(motor_hours,1),

                "RSS_Hours": round(rss_hours,1),

                "MWD_Hours": round(mwd_hours,1),

                "Mechanical_Failures": mechanical_failures,

                "NPT_Hours": npt_hours,

                "NPT_pct": npt_pct,

                "Bit_Cost_USD": bit_cost,

                "Motor_Cost_USD": motor_cost,

                "RSS_Cost_USD": rss_cost,

                "MWD_Cost_USD": mwd_cost,

                "Services_Cost_USD": services_cost,

                "Mud_Cost_USD": mud_cost,

                "Rig_Cost_USD": rig_cost,

                "Fuel_Cost_USD": fuel_cost,

                "Personnel_Cost_USD": personnel_cost,

                "Logistics_Cost_USD": logistics_cost,

                "Total_BHA_Cost_USD": total_bha_cost,

                "Total_Run_Cost_USD": total_run_cost,

                "Cost_Per_Foot_USD": cost_per_foot,

                "Pull_Reason": pull_reason,

                "Run_Efficiency_pct": run_efficiency_pct,

                "ROP_Category": rop_category,

                "Cost_Category": cost_category,

                "BHA_Success": bha_success

            })

            bha_counter += 1

            run_number += 1

# ============================================================
# CREATE DATAFRAME
# ============================================================

fact_bha = pd.DataFrame(records)

print()
print("="*70)
print("QUALITY CHECKS")
print("="*70)

print(f"Total BHA Runs              : {len(fact_bha)}")
print(f"Unique Wells                : {fact_bha['Well_ID'].nunique()}")
print(f"Unique Rigs                 : {fact_bha['Rig_ID'].nunique()}")

print()

print("Average Footage:")
print(round(fact_bha["Footage_ft"].mean(),1))

print()

print("Average ROP:")
print(round(fact_bha["Average_ROP_ft_hr"].mean(),1))

print()

print("Average Cost/Foot:")
print(round(fact_bha["Cost_Per_Foot_USD"].mean(),2))

print()

print("Average Run Cost:")
print(round(fact_bha["Total_Run_Cost_USD"].mean(),0))

print()

print("Average NPT:")
print(round(fact_bha["NPT_Hours"].mean(),1))

print()

print("="*70)
print("SUCCESS DISTRIBUTION")
print("="*70)

print(fact_bha["BHA_Success"].value_counts())

print()

print("="*70)
print("BIT TYPES")
print("="*70)

print(fact_bha["Bit_Type"].value_counts())

print()

print("="*70)
print("HOLE SECTIONS")
print("="*70)

print(fact_bha["Hole_Section"].value_counts())

print()

print("="*70)
print("FORMATIONS")
print("="*70)

print(fact_bha["Formation"].value_counts())

print()

print("="*70)
print("NUMERIC SUMMARY")
print("="*70)

print(fact_bha.describe())

print()

# ============================================================
# EXPORT
# ============================================================

OUTPUT = BASE_PATH / "Fact_BHA_Run.xlsx"

fact_bha.to_excel(
    OUTPUT,
    index=False
)

print("="*70)
print("FACT_BHA_RUN CREATED")
print("="*70)

print()

print(f"Saved to : {OUTPUT}")

print()

print("Shape")

print(fact_bha.shape)

print()

print("Columns")

print(list(fact_bha.columns))

print()

print("Preview")

print(fact_bha.head())
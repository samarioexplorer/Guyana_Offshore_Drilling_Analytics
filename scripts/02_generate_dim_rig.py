import pandas as pd

rigs = [
    {
    "Rig_ID": "R001",
    "Rig_Name": "Noble Bob Douglas",
    "Contractor": "Noble",
    "Rig_Type": "Drillship",
    "Max_Water_Depth_ft": 12000,
    "Day_Rate_USD": 475000,
    "Rig_Status": "Active",
    "Year_Built": 2013
    },
    {
        "Rig_ID": "R002",
        "Rig_Name": "Stena Carron",
        "Contractor": "Stena Drilling",
        "Rig_Type": "Drillship",
        "Max_Water_Depth_ft": 10000,
        "Day_Rate_USD": 460000,
        "Rig_Status": "Active",
        "Year_Built": 2015
    },
    {
        "Rig_ID": "R003",
        "Rig_Name": "Stena DrillMAX",
        "Contractor": "Stena Drilling",
        "Rig_Type": "Drillship",
        "Max_Water_Depth_ft": 12000,
        "Day_Rate_USD": 480000,
        "Rig_Status": "Maintenance",
        "Year_Built": 2018

    },
    {
        "Rig_ID": "R004",
        "Rig_Name": "Noble Don Taylor",
        "Contractor": "Noble",
        "Rig_Type": "Drillship",
        "Max_Water_Depth_ft": 12000,
        "Day_Rate_USD": 490000,
        "Rig_Status": "StandBy",
        "Year_Built": 2020
    }
]

df_rig = pd.DataFrame(rigs)

print(df_rig)

df_rig.to_excel("../data/raw/Dim_Rig.xlsx", index=False)
import pandas as pd
import numpy as np

# Make random values reproducible
np.random.seed(42)

# Number of wells
n_wells = 50

# Add a start date for the wells
start_date = pd.Timestamp("2023-01-01")

# Generate random spud dates within 2 years from the start date
spud_dates = start_date + pd.to_timedelta(
    np.random.randint(0, 730, n_wells),
    unit="D"
)

# Generate IDs
well_ids = [f"W{i:03}" for i in range(1, n_wells + 1)]

# Generate well names
well_names = [f"ATL-{i:03}" for i in range(1, n_wells + 1)]

# Well types
well_types = [
    "Exploration",
    "Development",
    "Appraisal"
]

rig_ids = [
    "R001",
    "R002",
    "R003",
    "R004"
]

# Well types
Rig_Name = [
    "Noble Bob Douglas",
    "Stena Carron",
    "Stena DrillMAX",
    "Noble Don Taylor"
]

# Operators
operators = [
    "Atlantic Energy Guyana"
]

# 
country = [
    "Guyana"
]


# Offshore blocks
blocks = [
    "Stabroek"
]

# Statuses
statuses = [
    "Planned",
    "Drilling",
    "Completed",
    "Suspended"
]

def water_depth_category(depth):
    if depth < 5000:
        return "Deepwater"
    elif depth < 6000:
        return "Ultra Deepwater"
    else:
        return "Extreme Deepwater"

# Generate the DataFrame
df = pd.DataFrame({
    "Well_ID": well_ids,
    "Well_Name": well_names,
    "Operator": np.random.choice(operators, n_wells),
    "Rig_ID": np.random.choice(rig_ids, n_wells),
    "Block": np.random.choice(blocks, n_wells),
    "Well_Type": np.random.choice(well_types, n_wells),
    "Water_Depth_ft": np.random.randint(4500, 7000, n_wells),
    "Target_Depth_ft": np.random.randint(15000, 23000, n_wells),
    "Country": np.random.choice(country, n_wells),
    "Status": np.random.choice(statuses, n_wells),
    "Status_Probability": np.random.choice(statuses, n_wells, p=[0.15, 0.20, 0.60, 0.05]),
    "Spud_Date": spud_dates})

df["Water_Depth_Category"] = df["Water_Depth_ft"].apply(water_depth_category)

print(df.head())

df.to_excel(
    "../data/raw/Dim_Well.xlsx",
    index=False
)

print(df.info())

print(df.describe())
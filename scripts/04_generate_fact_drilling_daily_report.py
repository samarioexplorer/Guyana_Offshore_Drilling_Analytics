import pandas as pd
import numpy as np

np.random.seed(42)

df_well = pd.read_excel("../data/raw/Dim_Well.xlsx")
df_rig = pd.read_excel("../data/raw/Dim_Rig.xlsx")
df_date = pd.read_excel("../data/raw/Dim_Date.xlsx")

records = []

print(f"Number of wells: {len(df_well)}")

for _, well in df_well.iterrows():

    start_date = pd.to_datetime(well["Spud_Date"])

    dates = pd.date_range(
        start=start_date,
        periods=90,
        freq="D"
    )

    print(f"{well['Well_ID']} -> {len(dates)} drilling days")

    for date in dates:

        # 1. Weather
        delay_type = np.random.choice(
            ["None", "Moderate", "Severe"],
            p=[0.88, 0.09, 0.03]
        )

        if delay_type == "None":
            weather_delay = 0
        elif delay_type == "Moderate":
            weather_delay = np.random.randint(2, 7)
        else:
            weather_delay = np.random.randint(8, 13)

        # 2. Effective drilling hours
        effective_hours = 24 - weather_delay

        # 3. Generate ROP
        rop = round(np.random.uniform(22, 48), 1)

        # 4. Calculate daily footage
        daily_footage = int(
            rop *
            effective_hours *
            np.random.uniform(0.75, 0.90)
        )

        # 5. Get rig information
        rig = df_rig[df_rig["Rig_ID"] == well["Rig_ID"]].iloc[0]

        rig_day_rate = rig["Day_Rate_USD"]

        # 6. Variable operating cost
        variable_cost = np.random.randint(40000, 90000)

        daily_cost = rig_day_rate + variable_cost

        # 7. Save the record
        records.append({
            "Date": date,
            "Well_ID": well["Well_ID"],
            "Rig_ID": well["Rig_ID"],
            "Daily_Footage_ft": daily_footage,
            "ROP_ft_hr": rop,
            "Mud_Weight_ppg": round(np.random.uniform(9.5, 15.5), 1),
            "Daily_Cost_USD": daily_cost,
            "Weather_Delay_hr": weather_delay
        })

print(f"Total records: {len(records)}")

fact_daily = pd.DataFrame(records)

print(fact_daily.shape)
print(fact_daily.head())
print(fact_daily.tail())

fact_daily.to_excel(
    "../data/raw/Fact_Drilling_Daily_Report.xlsx",
    index=False
)

df_test = pd.read_excel("../data/raw/Fact_Drilling_Daily_Report.xlsx")

print("Rows written:", len(df_test))
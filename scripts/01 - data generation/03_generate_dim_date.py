import pandas as pd

start_date = "2023-01-01"
end_date = "2026-12-31"

dates = pd.date_range(start=start_date, end=end_date, freq="D")

df_date = pd.DataFrame({
    "Date": dates
})

df_date["Year"] = df_date["Date"].dt.year
df_date["Quarter"] = df_date["Date"].dt.quarter
df_date["Quarter_Name"] = "Q" + df_date["Quarter"].astype(str)
df_date["Month_Number"] = df_date["Date"].dt.month
df_date["Month_Name"] = df_date["Date"].dt.month_name()
df_date["Month_Year"] = df_date["Date"].dt.strftime("%b-%Y")
df_date["Day"] = df_date["Date"].dt.day
df_date["Day_of_Year"] = df_date["Date"].dt.dayofyear
df_date["Day_Name"] = df_date["Date"].dt.day_name()
df_date["Week"] = df_date["Date"].dt.isocalendar().week

df_date["Is_Weekend"] = df_date["Day_Name"].isin(
    ["Saturday", "Sunday"]
)
df_date["Is_Month_End"] = df_date["Date"].dt.is_month_end

df_date["Date_Key"] = (
    df_date["Date"]
    .dt.strftime("%Y%m%d")
    .astype(int)
)

df_date = df_date[
    [
        "Date_Key",
        "Date",
        "Year",
        "Quarter",
        "Quarter_Name",
        "Month_Number",
        "Month_Name",
        "Month_Year",
        "Week",
        "Day",
        "Day_of_Year",
        "Day_Name",
        "Is_Weekend",
        "Is_Month_End"
    ]
]

df_date.to_excel(
    "../data/raw/Dim_Date.xlsx",
    index=False
)

print(df_date.head())

print(df_date.dtypes)
/*
PROJECT 01 — Guyana Offshore Drilling Performance & NPT Analytics
SQL STARTER / DATA CONTRACT

Purpose:
  Establish the relational model, QC rules, and first analytical queries.

Current verified dimensions:
  Dim_Date(Date_Key, Date, Year, Quarter, Quarter_Name, Month_Number,
           Month_Name, Month_Year, Week, Day, Day_of_Year, Day_Name,
           Is_Weekend, Is_Month_End)

  Dim_Rig(Rig_ID, Rig_Name, Contractor, Rig_Type, Max_Water_Depth_ft,
          Day_Rate_USD, Rig_Status, Year_Built)

The exact schemas of Dim_Well, Fact_Drilling_Daily_Report and Fact_NPT
will be populated from the consolidated workbook and SHOULD NOT be guessed.
*/

/* ================================================================
   1. TARGET TABLES
   ================================================================ */

-- Dimensions already verified
CREATE TABLE Dim_Date (
    Date_Key             INT          PRIMARY KEY,
    Date                 DATE         NOT NULL,
    Year                 INT          NOT NULL,
    Quarter              INT          NOT NULL,
    Quarter_Name         VARCHAR(10)  NOT NULL,
    Month_Number         INT          NOT NULL,
    Month_Name           VARCHAR(20)  NOT NULL,
    Month_Year           VARCHAR(20)  NOT NULL,
    Week                 INT          NOT NULL,
    Day                  INT          NOT NULL,
    Day_of_Year          INT          NOT NULL,
    Day_Name             VARCHAR(20)  NOT NULL,
    Is_Weekend            BOOLEAN      NOT NULL,
    Is_Month_End          BOOLEAN      NOT NULL
);

CREATE TABLE Dim_Rig (
    Rig_ID               VARCHAR(20)  PRIMARY KEY,
    Rig_Name             VARCHAR(100) NOT NULL,
    Contractor            VARCHAR(100) NOT NULL,
    Rig_Type             VARCHAR(50)  NOT NULL,
    Max_Water_Depth_ft   DECIMAL(10,2),
    Day_Rate_USD          DECIMAL(18,2),
    Rig_Status            VARCHAR(30),
    Year_Built            INT
);

/*
PLACEHOLDER — populate only after workbook audit.
CREATE TABLE Dim_Well (...);
CREATE TABLE Fact_Drilling_Daily_Report (...);
CREATE TABLE Fact_NPT (...);
*/

/* ================================================================
   2. TARGET RELATIONSHIPS
   ================================================================ */

/*
Dim_Date[Date_Key]       1 ─── * Fact_Drilling_Daily_Report[Date_Key]
Dim_Date[Date_Key]       1 ─── * Fact_NPT[Date_Key]
Dim_Rig[Rig_ID]          1 ─── * Fact_Drilling_Daily_Report[Rig_ID]
Dim_Rig[Rig_ID]          1 ─── * Fact_NPT[Rig_ID]
Dim_Well[Well_ID]        1 ─── * Fact_Drilling_Daily_Report[Well_ID]
Dim_Well[Well_ID]        1 ─── * Fact_NPT[Well_ID]
*/

/* ================================================================
   3. DATA QUALITY RULES
   ================================================================ */

-- DIMENSION RULES
-- D1: Primary keys must be unique and non-null.
-- D2: Every fact foreign key must exist in its dimension.
-- D3: Dates must fall within Dim_Date coverage.

-- DRILLING FACT RULES
-- F1: Daily_Footage_ft >= 0
-- F2: ROP_ft_hr >= 0
-- F3: Drilling hours between 0 and 24, if field exists.
-- F4: Daily_Cost_USD >= 0
-- F5: Weather delay hours between 0 and 24, if field exists.
-- F6: No duplicate grain records once the natural grain is established.

-- NPT FACT RULES
-- N1: NPT Duration_hr > 0
-- N2: NPT Duration_hr <= 24 for a single daily event, unless event-level
--     records explicitly span multiple days.
-- N3: Cost_USD >= 0
-- N4: NPT category/subcategory must be populated.
-- N5: Severity must map consistently to duration or the documented rule.

/* ================================================================
   4. BASE ANALYTICAL QUERIES
   ================================================================ */

-- Q1. Rig profile
SELECT
    Rig_ID,
    Rig_Name,
    Contractor,
    Rig_Type,
    Max_Water_Depth_ft,
    Day_Rate_USD,
    Rig_Status,
    Year_Built
FROM Dim_Rig
ORDER BY Day_Rate_USD DESC;

-- Q2. Potential hourly rig cost
SELECT
    Rig_ID,
    Rig_Name,
    Day_Rate_USD,
    Day_Rate_USD / 24.0 AS Hourly_Rig_Cost_USD
FROM Dim_Rig
ORDER BY Hourly_Rig_Cost_USD DESC;

/*
Q3. Intended NPT cost reconciliation (activate once the fact table schema
is verified):

SELECT
    n.Well_ID,
    n.Rig_ID,
    SUM(n.Duration_hr) AS NPT_Hours,
    SUM(n.Duration_hr * r.Day_Rate_USD / 24.0) AS Estimated_NPT_Rig_Cost_USD,
    SUM(n.Cost_USD) AS Recorded_NPT_Cost_USD
FROM Fact_NPT n
JOIN Dim_Rig r ON r.Rig_ID = n.Rig_ID
GROUP BY n.Well_ID, n.Rig_ID;
*/

/* ================================================================
   5. ANALYTICAL DESIGN — PROJECT 01
   ================================================================ */

/* Required KPI families:

TIME
  Total drilling days
  Total drilling hours
  NPT hours
  NPT %

PERFORMANCE
  Average ROP
  Median ROP
  Daily footage
  Footage per drilling day
  Rig/well benchmark

ECONOMICS
  Total drilling cost
  Estimated NPT rig-time cost
  Cost per drilling day
  Cost per foot
  Potential savings scenarios

NPT
  NPT by category
  NPT by subcategory
  NPT by rig
  NPT by well
  NPT Pareto contribution
*/

/* ================================================================
   6. SAVINGS SCENARIO
   ================================================================ */

/*
Potential savings from reducing NPT by X%:

Potential_Saving_USD = Current_NPT_Rig_Cost_USD * Reduction_Percentage

Examples to calculate in the analytical layer:
  10%
  20%
  30%

Do not hard-code these scenarios into the source data.
*/

/* ================================================================
   7. IMPORTANT MODELING PRINCIPLE
   ================================================================ */

/*
Do NOT mix daily drilling cost and NPT cost blindly.
Before calculating total economics, determine whether:
  (a) Daily_Cost_USD already includes rig time during NPT, or
  (b) NPT cost is a separate accounting measure.

The final model must avoid double-counting the same economic loss.
*/

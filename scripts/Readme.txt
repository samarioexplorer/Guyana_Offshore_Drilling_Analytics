# Python Engineering & Data Layer

The `python/` directory contains the Python engineering layer of the **Guyana Offshore Drilling Analytics** project.

Its purpose is to provide a reproducible workflow for synthetic data generation, analytical data preparation, and validation/reconciliation before the data is consumed by the SQL and Power BI layers.

---

## 1. Engineering Workflow

The Python layer follows a three-stage pipeline:

```text
┌───────────────────────────────┐
│ 01 — Data Generation         │
│ Synthetic offshore datasets  │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ 02 — Data Preparation        │
│ Cleaning & transformation     │
└───────────────┬───────────────┘
                │
                ▼
┌───────────────────────────────┐
│ 03 — Validation &            │
│      Reconciliation           │
│ Quality & metric controls     │
└───────────────┬───────────────┘
                │
                ▼
        Processed Data
                │
        ┌───────┴───────┐
        ▼               ▼
      SQLite          Power BI
```

This separation keeps **data creation, transformation, and validation** logically independent.

---

## 2. Directory Structure

```text
python/
│
├── 01_data_generation/
│   └── generate_drilling_data.py
│
├── 02_data_preparation/
│   └── prepare_drilling_data.py
│
├── 03_validation/
│   └── validate_reconciliation.py
│
└── README.md
```

---

## 3. 01 — Data Generation

### Location

```text
python/01_data_generation/
```

### Purpose

The data-generation layer creates a realistic synthetic offshore drilling environment for analytical development and testing.

The generated data represents operational entities and events such as:

* Wells
* Rigs
* Dates
* Daily drilling performance
* Drilling footage
* Drilling hours
* Rate of penetration
* NPT events
* NPT categories
* NPT root causes
* NPT duration
* NPT economic impact

The generation process is designed to produce a sufficiently rich dataset for SQL analysis, Power BI modelling, KPI development, and scenario analysis.

### Key principle

The dataset is **synthetic** and is intended for analytics demonstration, portfolio development, and technical testing.

It should not be interpreted as proprietary operational data from an actual operator or drilling contractor.

---

## 4. 02 — Data Preparation

### Location

```text
python/02_data_preparation/
```

### Purpose

The preparation layer converts generated data into consistent analytical datasets suitable for downstream SQL and Power BI processing.

Typical transformations include:

* Data cleaning
* Data-type standardization
* Date normalization
* Key preparation
* Relationship preparation
* Derived operational fields
* NPT classification
* NPT cost calculations
* Analytical field preparation
* Processed dataset generation

The objective is to ensure that downstream analytical layers receive data that is:

**Consistent → Structured → Reproducible → Analysis-ready**

---

## 5. 03 — Validation & Reconciliation

### Location

```text
python/03_validation/
```

### Purpose

The validation layer provides automated checks to confirm that the prepared data remains internally consistent before it is consumed by the analytical model.

Validation areas include:

### Structural validation

* Row counts
* Required columns
* Data types
* Duplicate records
* Missing critical values

### Referential validation

* Well keys
* Rig keys
* Date keys
* Relationship integrity

### Operational validation

* Drilling hours
* Drilling footage
* Rate of penetration
* NPT duration
* NPT event counts

### Economic validation

* NPT cost
* Cost per foot
* Rig economic impact
* Aggregated operational cost

### Cross-layer reconciliation

The validation framework also supports reconciliation between:

```text
Python
   ↓
Processed Data
   ↓
SQLite / SQL
   ↓
Power BI
```

This helps ensure that the same business metrics remain consistent across the analytical stack.

---

## 6. Reconciliation Benchmarks

The project uses validated benchmark values as control totals for downstream QA.

| Metric        | Validated Value |
| ------------- | --------------: |
| NPT Events    |             677 |
| NPT Hours     |        4,008 hr |
| Total Footage |    952,078.8 ft |
| Average ROP   |     33.67 ft/hr |
| Cost per Foot |         $687.67 |
| Drilling Days |             666 |

These values provide reference points for identifying discrepancies between the Python, SQL, and Power BI layers.

---

## 7. Data Quality Philosophy

The Python layer follows a simple engineering principle:

> **Do not allow visualization to become the first place where data quality problems are discovered.**

Validation is therefore treated as a separate engineering stage rather than an informal dashboard check.

The workflow is:

```text
Generate
   ↓
Prepare
   ↓
Validate
   ↓
Load
   ↓
Analyze
   ↓
Visualize
   ↓
QA
```

This approach reduces the risk of propagating data-quality issues into the SQL database and Power BI semantic model.

---

## 8. Relationship to the SQL Layer

Python prepares and validates the analytical datasets.

The SQL layer then provides:

* Relational storage
* Analytical queries
* Aggregations
* Operational analysis
* Root-cause analysis
* Management outputs
* Scenario-supporting datasets

Conceptually:

```text
Python Engineering Layer
          │
          ▼
    Processed Data
          │
          ▼
       SQLite
          │
          ▼
     SQL Analytics
          │
          ▼
     Power BI Model
```

---

## 9. Relationship to Power BI

The processed and validated datasets ultimately support the Power BI analytical model.

Power BI provides the final decision-support layer, including:

* Executive Command Center
* Operational Performance
* NPT & Root Cause Analysis
* Rig Performance
* KPI monitoring
* Economic impact analysis
* Scenario analysis

Python therefore acts as the **data engineering and quality foundation**, while Power BI acts as the **analytical and decision-support interface**.

---

## 10. Reproducibility

The Python environment is defined in the project-level:

```text
requirements.txt
```

Core dependencies include:

```text
pandas
numpy
Faker
openpyxl
```

The scripts should be executed in sequence:

```text
01_data_generation
        ↓
02_data_preparation
        ↓
03_validation
```

Running the stages sequentially provides a reproducible path from synthetic source data to validated analytical datasets.

---

## 11. Design Principles

The Python layer follows these principles:

### Separation of concerns

Data generation, transformation, and validation are maintained as separate stages.

### Reproducibility

The workflow should be executable again without manually reconstructing the dataset.

### Traceability

Derived metrics and transformations should be explainable from their source fields and business rules.

### Validation before visualization

Data-quality checks occur before the data reaches the reporting layer.

### Analytical consistency

Business definitions should remain consistent across Python, SQL, and Power BI.

### Portfolio transparency

The project clearly distinguishes synthetic data from real-world operational information.

---

## 12. Role in the Overall Architecture

The complete project architecture is:

```text
┌───────────────────────────────────────────────┐
│           PYTHON ENGINEERING LAYER            │
│                                               │
│  Generation → Preparation → Validation        │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│                SQL / SQLITE LAYER             │
│                                               │
│  Relational Model → Analytics → Outputs       │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│                 POWER BI LAYER                │
│                                               │
│  Semantic Model → DAX → Visualization         │
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│              QA & DECISION SUPPORT            │
│                                               │
│  KPI Validation → Scenario Analysis           │
│  Economic Impact → Executive Insights         │
└───────────────────────────────────────────────┘
```

The result is an end-to-end analytics workflow combining:

**Data Engineering + Python + SQL + Power BI + DAX + QA + Operational Economics**

---

## 13. Scope & Data Disclaimer

This project uses synthetic data created for educational, analytical, and portfolio-development purposes.

The operational values, wells, rigs, drilling performance, NPT events, costs, and other analytical records are not presented as proprietary field data.

The project demonstrates the **methodology and analytical architecture** rather than representing an actual field development plan or operational recommendation for a specific offshore asset.

---

## 14. Next Layer

The Python engineering layer feeds the project's broader analytical architecture:

```text
Python
   ↓
SQL
   ↓
Power BI
   ↓
Technical Appendix
   ↓
Executive Portfolio Presentation
```

Together, these components demonstrate the ability to take an offshore drilling analytics problem from **data generation and engineering through validated analysis and executive decision support**.

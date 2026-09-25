# SQL Engineering Layer

## Guyana Offshore Drilling Analytics

The SQL layer provides the analytical and validation backbone of the **Guyana Offshore Drilling Analytics** project.

It transforms the structured drilling database into operational-performance, non-productive-time (NPT), economic-impact, optimization, and scenario-analysis outputs consumed by the Power BI reporting layer.

The SQL workflow is designed around four principles:

* **Reproducibility** — analytical logic is organized into repeatable stages.
* **Traceability** — every KPI can be traced back to underlying drilling and NPT records.
* **Reconciliation** — critical results are independently validated before being used in Power BI.
* **Engineering relevance** — the analysis focuses on drilling performance, NPT drivers, rig economics, operational risks, and improvement opportunities.

---

## 1. SQL Architecture

The analytical database is implemented in SQLite.

The core dimensional model consists of:

```text
                    ┌──────────────┐
                    │   Dim_Date   │
                    └──────┬───────┘
                           │
                           │
┌──────────────┐     ┌─────▼────────────────────┐
│   Dim_Well   │────►│ Fact_Drilling_Daily_     │
└──────┬───────┘     │ Report                    │
       │             └──────────┬────────────────┘
       │                        │
       │                        │
┌──────▼───────┐                │
│   Dim_Rig    │────────────────┘
└──────┬───────┘
       │
       │
       ▼
┌────────────────┐
│    Fact_NPT    │
└────────────────┘
```

### Core tables

| Table                        | Purpose                                               |
| ---------------------------- | ----------------------------------------------------- |
| `Dim_Date`                   | Date dimension supporting temporal analysis           |
| `Dim_Well`                   | Well-level attributes and drilling metadata           |
| `Dim_Rig`                    | Rig characteristics and economic parameters           |
| `Fact_Drilling_Daily_Report` | Daily drilling-performance records                    |
| `Fact_NPT`                   | Non-productive-time events and root-cause information |

The model separates **descriptive dimensions** from **operational facts**, allowing the same underlying data to support multiple analytical perspectives.

---

# 2. SQL Analytical Pipeline

The SQL scripts follow a staged analytical workflow:

```text
01 Foundation
      │
      ▼
02 Operational Performance
      │
      ▼
03 NPT & Root Causes
      │
      ▼
04 Optimization
      │
      ▼
05 Scenario Analysis
      │
      ▼
06 QA & Reconciliation
```

This progression mirrors the business logic of the project:

> **What happened? → Why did it happen? → What did it cost? → What can be improved? → How was the result validated?**

---

# 3. Repository Structure

```text
sql/
│
├── README.md
│
├── 01_foundation/
│   ├── 01_schema_validation.sql
│   ├── 02_row_counts.sql
│   └── 03_referential_integrity.sql
│
├── 02_operational_performance/
│   ├── 01_drilling_performance.sql
│   ├── 02_well_performance.sql
│   ├── 03_rig_performance.sql
│   └── 04_drilling_benchmarks.sql
│
├── 03_npt_analysis/
│   ├── 01_npt_summary.sql
│   ├── 02_npt_by_category.sql
│   ├── 03_root_cause_analysis.sql
│   └── 04_npt_economic_impact.sql
│
├── 04_optimization/
│   ├── 01_npt_reduction_actions.sql
│   ├── 02_strategic_actions.sql
│   └── 03_operational_control_tower.sql
│
├── 05_scenario_analysis/
│   └── 01_scenario_impact.sql
│
└── 06_qa_reconciliation/
    ├── 01_python_sql_reconciliation.sql
    ├── 02_sql_powerbi_reconciliation.sql
    └── 03_final_benchmark_validation.sql
```

> **Note:** The directory structure represents the intended portfolio organization of the SQL layer. The SQL analytical layer is implemented through SQLite and Python orchestration scripts located under scripts/02 - data preparation/ and scripts/03 - validation/.

---

# 4. Foundation Layer

The foundation scripts establish confidence in the database before analytical queries are executed.

### Primary controls

* Table existence
* Row-count verification
* Required-field checks
* Primary-key uniqueness
* Foreign-key relationships
* Null-value inspection
* Referential-integrity checks
* Date-range validation

The purpose is to prevent downstream KPI errors caused by structural or data-quality issues.

---

# 5. Operational Performance

The operational-performance layer evaluates drilling execution at well and rig level.

Key metrics include:

* Total footage drilled
* Drilling hours
* Drilling days
* Average rate of penetration (ROP)
* Cost per foot
* Rig economic impact
* Well-level drilling performance
* Rig-level performance

Validated project benchmarks include:

| Metric              |       Result |
| ------------------- | -----------: |
| Total footage       | 952,078.8 ft |
| Average ROP         |  33.67 ft/hr |
| Cost per foot       |      $687.67 |
| Drilling days       |          666 |
| Rig economic impact |     $198.15M |

These queries provide the operational baseline against which NPT and optimization analyses are evaluated.

---

# 6. NPT Analysis

The NPT layer identifies where drilling time is being lost and quantifies the associated operational and economic consequences.

### NPT dimensions

NPT is analyzed by:

* Rig
* Well
* Date
* NPT category
* Root cause
* Duration
* Economic consequence

### NPT categories

The project includes:

* Mechanical
* Weather
* Drilling
* Logistics
* Personnel

The database contains:

| Metric      |   Result |
| ----------- | -------: |
| NPT records |      677 |
| NPT hours   | 4,008 hr |

NPT analysis is deliberately separated from drilling-performance analysis so that downtime does not distort productive drilling metrics.

---

# 7. Root-Cause Analysis

The root-cause layer moves the analysis from descriptive reporting toward operational diagnosis.

The project identifies recurring causes such as:

* Unexpected Pressure
* Formation Instability
* Differential Sticking
* Bit Wear
* Equipment Wear
* Poor Preventive Maintenance
* Electrical Failure

The SQL analysis can rank causes by:

* Event frequency
* Total duration
* Economic impact
* Rig exposure
* Operational consequence

This allows the Power BI layer to present the principal sources of NPT rather than simply reporting aggregate downtime.

---

# 8. Economic Impact

The economic-impact queries translate operational losses into financial terms.

The analysis links:

```text
NPT Duration
      ↓
Downtime Cost
      ↓
Well / Rig Exposure
      ↓
Economic Impact
```

This provides a financial dimension to drilling-performance analysis and allows operational risks to be discussed in terms meaningful to both engineering and management stakeholders.

The validated aggregate rig economic impact is:

**$198.15M**

---

# 9. Optimization Layer

The optimization layer converts analytical findings into potential operational actions.

The analysis includes:

* NPT reduction opportunities
* Root-cause prioritization
* Strategic improvement actions
* Operational control-tower outputs
* Potential reduction in NPT exposure

One validated strategic-action analysis identified:

```text
Baseline NPT exposure:       677 events
Strategic action events:     502
Potential reduction:         175
```

These values represent analytical scenario outputs rather than observed future performance.

The distinction between **historical actuals** and **scenario-based potential impacts** is maintained throughout the project.

---

# 10. Scenario Analysis

Scenario analysis evaluates the potential effect of operational interventions without altering the historical database.

The general framework is:

```text
Historical Baseline
        │
        ▼
Identify NPT Exposure
        │
        ▼
Apply Improvement Assumption
        │
        ▼
Calculate Potential Reduction
        │
        ▼
Estimate Potential Economic Impact
```

Scenario outputs should therefore be interpreted as **analytical estimates under defined assumptions**, not forecasts or guaranteed savings.

---

# 11. QA & Reconciliation

The final SQL stage provides independent validation of the analytical pipeline.

The validation philosophy is:

```text
Python
  │
  ▼
Processed Data
  │
  ▼
SQLite / SQL
  │
  ▼
Power BI
  │
  ▼
Dashboard QA
```

Critical metrics are reconciled between layers.

### Final benchmark set

| KPI                 | Expected result |
| ------------------- | --------------: |
| Wells               |              50 |
| Rigs                |               4 |
| Dates               |           1,461 |
| Drilling records    |           1,474 |
| NPT records         |             677 |
| NPT hours           |        4,008 hr |
| Total footage       |    952,078.8 ft |
| Average ROP         |     33.67 ft/hr |
| Cost/ft             |         $687.67 |
| Drilling days       |             666 |
| Rig economic impact |        $198.15M |

These values form the project's **cross-layer reconciliation baseline**.

---

# 12. Metric Definitions

To prevent ambiguity between SQL, DAX, and presentation outputs, the principal metrics are defined consistently.

### Total Footage

Total drilled footage across the applicable drilling records.

```text
Total Footage = SUM(Drilled Footage)
```

### Average ROP

Average drilling rate expressed in feet per hour.

```text
ROP = Drilled Footage / Drilling Hours
```

The project benchmark is:

**33.67 ft/hr**

### NPT Hours

Total duration of recorded NPT events.

```text
NPT Hours = SUM(NPT Duration)
```

The project benchmark is:

**4,008 hr**

### Cost per Foot

Total drilling-related economic cost divided by total footage.

```text
Cost / ft = Total Cost / Total Footage
```

The project benchmark is:

**$687.67/ft**

### Drilling Days

Distinct operational drilling dates represented in the drilling-performance dataset.

```text
Drilling Days = DISTINCT(Date)
```

The validated benchmark is:

**666 days**

---

# 13. SQL Design Principles

The SQL layer follows several engineering principles.

### Separation of concerns

Data validation, operational analysis, NPT analysis, optimization, and reconciliation are separated into logical stages.

### Traceability

Queries should make it possible to trace a dashboard KPI back to the underlying fact table and dimensions.

### Reconciliation before presentation

A metric should be validated at the SQL level before being treated as a Power BI benchmark.

### Historical vs. scenario data

Observed historical performance is kept conceptually separate from potential improvement scenarios.

### Consistent definitions

Metric definitions are maintained consistently across:

```text
Python → SQL → DAX → Power BI → Presentation
```

---

# 14. Relationship to Power BI

SQL is the analytical foundation for the Power BI reporting layer.

The overall architecture is:

```text
┌──────────────────────┐
│ Python Engineering   │
│ Generation / Prep /  │
│ Validation            │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ SQLite Database      │
│ Dim + Fact Model     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ SQL Analytics        │
│ Performance / NPT /  │
│ Economics / Scenarios│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Power BI             │
│ KPI / Visualization  │
│ / Interactive QA     │
└──────────────────────┘
```

The SQL layer therefore acts as the **analytical bridge between data engineering and business intelligence**.

---

# 15. Reproducibility

The SQL scripts are designed to be executed against the project SQLite database.

Recommended execution sequence:

```text
01 Foundation
        ↓
02 Operational Performance
        ↓
03 NPT Analysis
        ↓
04 Optimization
        ↓
05 Scenario Analysis
        ↓
06 QA / Reconciliation
```

Before executing analytical scripts, confirm that the SQLite database has been generated and populated by the Python data-engineering layer.

---

# 16. Project Outcome

The SQL layer demonstrates the ability to move beyond dashboard construction into a complete analytical workflow involving:

* Relational data modeling
* SQL aggregation
* Drilling-performance analysis
* NPT analysis
* Root-cause analysis
* Economic-impact analysis
* Operational optimization
* Scenario modeling
* Cross-layer reconciliation
* BI-ready data preparation

The resulting workflow supports a professional analytics pipeline:

> **Generate → Prepare → Validate → Model → Analyze → Optimize → Reconcile → Visualize**

---

## Technology

* **SQLite**
* **SQL**
* **Python**
* **Power BI**
* **DAX**
* **Excel / PowerPoint** for analytical outputs and QA documentation

---

## Status

**SQL analytical layer: Validated**

The principal operational, NPT, economic, optimization, and reconciliation outputs have been validated against the project's established benchmark values.

The SQL layer is intended to remain transparent, reproducible, and traceable to the underlying drilling data.

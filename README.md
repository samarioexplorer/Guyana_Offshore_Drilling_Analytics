# Guyana Offshore Drilling Analytics

## Operational Performance, NPT Root Cause & Economic Impact

**Power BI · SQL · Python · DAX · Operational Analytics**

A portfolio-grade drilling analytics solution that transforms well, rig, drilling-performance and NPT data into an integrated decision-support framework.

**Operational Data → Performance → NPT → Root Cause → Economics → Operational Action**

---

## 1. Business Challenge

The objective is to transform drilling-performance data into actionable operational visibility.

The analytical framework addresses four core questions:

- **Performance:** How efficiently are wells and rigs drilling?
- **Downtime:** Where is time being lost?
- **Root Cause:** Why is NPT occurring?
- **Economics:** What is the business consequence?

The solution establishes consistent project-wide KPIs, identifies performance variation, traces NPT from category to root cause, and translates operational loss into economic impact.

---

## 2. Key Project Results

| KPI | Validated Result |
|---|---:|
| Total Footage | **952,078.8 ft** |
| NPT Hours | **4,008 hr** |
| NPT Events | **677** |
| Average ROP | **33.67 ft/hr** |
| NPT / Day | **6.02 hr/day** |
| Cost / Foot | **$687.67/ft** |
| Drilling Days | **666** |
| Rig Economic Impact | **$198.15M** |
| NPT Economic Impact | **$79.20M** |

---

## 3. Solution Architecture

```text
SOURCE DATA
Well · Rig · Drilling · NPT
        │
        ▼
PYTHON
Data preparation / structured datasets
        │
        ▼
SQL / SQLite
Analytical layer / NPT analysis / benchmarking
        │
        ▼
POWER BI + DAX
Semantic model / KPI logic / interactive analysis
        │
        ▼
DECISION SUPPORT
Performance · NPT · Root Cause · Economics · Action
        │
        ▼
QA / RELEASE CONTROL
Reconciliation · Filter Context · Visual QA
```

---

## 4. Data Model

The Power BI semantic layer uses a star-schema approach.

### Dimensions

- `Dim_Date` — calendar and date attributes
- `Dim_Well` — well ID, status and water-depth context
- `Dim_Rig` — rig, day rate and capability
- `Dim_Scenario` — Baseline / Conservative / Target / Stretch
- `Dim_KPI` — KPI catalog and definitions

### Facts

- `Fact_Drilling_Daily_Report` — daily drilling-performance grain
- `Fact_NPT_PBI` — enriched NPT event grain

Dimensions provide stable filter context while facts retain their operational grain.

---

## 5. SQL Analytical Layer

SQL converts operational records into reconciled benchmarks, NPT diagnostics and decision-ready outputs.

1. **Source** — SQLite operational tables
2. **Profile** — counts, keys, duplicates, nulls and referential integrity
3. **Analyze** — NPT by category, root cause, rig, well and monthly trend
4. **Reconcile** — ROP, NPT/day, NPT hours, footage, cost/ft and economic impact
5. **Serve** — enriched facts, scenario outputs and KPI / decision catalogs for Power BI

### Reconciliation anchor

**33.67 ft/hr · 6.02 NPT hr/day · 4,008 NPT hr · 952,078.8 ft · $687.67/ft · 666 drilling days · $198.15M rig economic impact**

---

## 6. Core KPI Definitions

### Average ROP
`Total Footage ÷ Drilling Hours`

### NPT Hours
`SUM(NPT Duration)`

### NPT / Day
`NPT Hours ÷ Drilling Days`

### Cost / Foot
`Drilling Cost ÷ Total Footage`

### Rig Economic Impact
`SUM(Rig Economic Impact)`

### NPT Event Count
`DISTINCTCOUNT(NPT_ID)`

### Drilling Days
Distinct active drilling dates.

---

## 7. NPT Calculation Logic

```text
NPT Event
Date · Well · Rig · Category · Root Cause
        │
        ▼
Duration
2 / 4 / 6 / 8 / 12 / 18 / 24 hr
        │
        ▼
Severity
Low ≤ 4 hr · Medium ≤ 12 hr · High > 12 hr
        │
        ▼
Rig Cost
Duration × Rig Day Rate / 24
        │
        ▼
Deferred Production
Event Duration × Production-Value Proxy
        │
        ▼
Total Economic Impact
Rig Cost + Deferred Production
```

This allows an NPT event to be traced from hours to cause, rig/well context, direct cost and total economic exposure.

---

## 8. Power BI Dashboard

### 01 — Executive Operational Command Center
Executive status, operational risks, root causes, improvement initiatives and scenario context.

### 02 — Operational Performance
Drilling efficiency, ROP, footage, drilling time and NPT performance.

### 03 — NPT & Root Cause Analysis
NPT hours, events, categories, root causes, trends and economic consequence.

### 04 — Rig Performance
Rig-level benchmarking across ROP, NPT, footage, cost and economic impact.

---

## 9. Operational Improvement Framework

Six initiatives are surfaced through the executive layer:

1. **Mechanical Reliability Program**
2. **Weather & Marine Operations Resilience**
3. **Drilling Dysfunction Reduction Program**
4. **Supply Chain & Logistics Optimization**
5. **Drilling Performance Optimization**
6. **People, Competency & Operational Readiness**

### Scenario framework

- **Baseline** — current-state reference
- **Conservative** — partial realization
- **Target** — planned improvement case
- **Stretch** — upper-bound improvement case

Scenario percentages represent assumed realization of improvement potential; they are not forecasts.

---

## 10. QA & Validation

QA was treated as a release-control layer.

Validation covered:

- Source integrity
- Counts and keys
- Duplicate / null checks
- Referential integrity
- Economic reconciliation
- Semantic model relationships
- DAX dependency and denominator behavior
- Scenario architecture
- Dashboard and drill-through behavior
- Executive baseline consistency
- Visual presentation and units

### Key QA case

A Rig Performance NPT-hours filter-context issue initially caused the project-level NPT total to repeat across rig rows.

The issue was isolated and corrected so rig-level NPT reconciles to the validated **4,008-hour project total**.

> A visual is released only when its number, filter behavior and business meaning reconcile.

---

## 11. Technical Portfolio Positioning

This project demonstrates an integrated capability across:

- Drilling / Wells Engineering
- Operational Performance Analytics
- NPT and Root Cause Analysis
- SQL / SQLite
- Python data preparation and validation
- Power BI semantic modeling
- DAX KPI design
- Scenario analysis
- Economic-impact analysis
- Analytical QA and reconciliation

The project is positioned as an **engineering analytics solution**, rather than only as a visualization exercise.

---

## 12. Repository Structure

```text
Guyana_Offshore_Drilling_Analytics/
│
├── README.md
├── LICENSE
├── requirements.txt
│
├── data/
│   ├── raw/
│   └── processed/
│
├── database/
│   └── guyana_drilling.db
│
├── python/
│   ├── data_generation/
│   ├── transformation/
│   └── validation/
│
├── sql/
│   ├── analysis/
│   ├── benchmarking/
│   └── outputs/
│
├── powerbi/
│   └── Guyana_Offshore_Drilling_Analytics.pbix
│
├── powerpoint/
│   └── Guyana_Offshore_Drilling_Analytics_Final_Portfolio.pptx
│
├── qa/
│   ├── screenshots/
│   ├── validation/
│   └── reports/
│
└── docs/
    ├── data_dictionary.md
    ├── metric_definitions.md
    └── methodology.md
```

---

## 13. Portfolio Deliverables

- Final Power BI dashboard
- Final 20-slide portfolio presentation
- Technical appendix
- SQLite analytical database
- Python processing / validation layer
- SQL analytical and benchmarking layer
- QA evidence
- Metric definitions
- Methodology documentation

---

## 14. Final Portfolio Statement

**Guyana Offshore Drilling Analytics** demonstrates how operational drilling data can be transformed into a validated decision-support product connecting performance, downtime, root cause, economic consequence and operational action.

**Drilling / Wells Engineering · Operational Performance Analytics · Power BI / SQL / Python / DAX**

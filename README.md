# SaaS Product Analytics — Customer Churn Analysis

> End-to-end product analytics project covering data cleaning, EDA, SQL analysis, ML modeling with explainability, and an interactive Power BI dashboard.

---

## Project Overview

This project analyzes customer churn for a SaaS telecom provider using the [Telco Customer Churn dataset](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) (7,043 customers, 21 features). The goal is to identify which customers are most likely to churn, understand the drivers behind churn, and quantify the business impact — delivering actionable insights a product or retention team can act on immediately.

**Key result:** LightGBM model achieved **AUC-ROC of 0.848**, identifying a high-risk customer segment responsible for over **$1.67M in annualized revenue loss**.

---

## Table of Contents

- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Phase Breakdown](#phase-breakdown)
- [Key Findings](#key-findings)
- [Model Performance](#model-performance)
- [Dashboard Preview](#dashboard-preview)
- [How to Run](#how-to-run)
- [Business Recommendations](#business-recommendations)

---

## Project Structure

```
product-analyst-project/
├── data/
│   ├── WA_Fn-UseC_-Telco-Customer-Churn.csv   # Raw dataset
│   ├── telco_churn_cleaned.csv                 # Phase 1 output
│   ├── churn_predictions.csv                   # Phase 4 ML output
│   └── shap_values.csv                         # SHAP feature values
├── notebooks/
│   ├── phase1_data_cleaning.ipynb
│   ├── phase2_eda.ipynb
│   ├── phase3_sql_analysis.ipynb
│   └── phase4_modeling.ipynb
├── sql/
│   ├── churn_by_contract.csv
│   ├── churn_by_tenure_segment.csv
│   ├── revenue_at_risk.csv
│   └── customer_profile_comparison.csv
├── visuals/
│   ├── 01_churn_distribution.png
│   ├── 02_demographics_churn.png
│   ├── 03_contract_churn.png
│   ├── 04_service_payment_churn.png
│   ├── 05_tenure_distribution.png
│   ├── 06_charges_churn.png
│   ├── 07_correlation_heatmap.png
│   ├── 08_model_comparison.png
│   ├── 09_shap_importance.png
│   ├── 10_shap_beeswarm.png
│   └── 11_shap_waterfall.png
├── churn_dashboard.pbix                        # Power BI file
├── dashboard_preview.pdf                       # Dashboard export
└── README.md
```

---

## Tech Stack

| Area | Tools |
|---|---|
| Data wrangling | Python, Pandas, NumPy |
| Visualization | Matplotlib, Seaborn |
| SQL analysis | SQLite (via Python) |
| Machine learning | XGBoost, LightGBM, Scikit-learn |
| Explainability | SHAP |
| Dashboard | Power BI Desktop, DAX |

---

## Phase Breakdown

### Phase 1 — Data Cleaning
- Loaded 7,043 rows × 21 columns
- Fixed `TotalCharges` dtype (loaded as string due to blank values)
- Imputed 11 null values in new customers (tenure = 0)
- Encoded `Churn` column to binary (Yes → 1, No → 0)
- Saved clean dataset for all downstream phases

### Phase 2 — Exploratory Data Analysis
- Visualized churn distribution: **26.54% churn rate** (class imbalance noted)
- Compared churn across demographics: senior citizens churn at **~42%** vs 24% for others
- Found contract type as the single strongest churn driver
- Discovered high MonthlyCharges + low tenure = highest churn risk cluster
- Produced 7 publication-quality charts saved to `visuals/`

### Phase 3 — SQL Analysis
- Loaded cleaned CSV into SQLite in-memory database
- Wrote 10 queries covering:
  - Basic aggregations (GROUP BY, AVG, COUNT)
  - Custom segmentation (CASE WHEN tenure bins)
  - High-value customer identification (subqueries)
  - Window functions (RANK OVER PARTITION BY, running totals)
  - Revenue at risk quantification
- Exported 4 result CSVs for Power BI integration

### Phase 4 — ML Modeling
- Encoded 15 categorical features using LabelEncoder
- Split data 80/20 with stratified sampling to preserve churn ratio
- Trained XGBoost and LightGBM with class imbalance handling
- Validated with 5-fold cross-validation (no overfitting confirmed)
- Applied SHAP TreeExplainer for global and local explainability
- Exported predictions with risk tier labels (Low / Medium / High)

### Phase 5 — Power BI Dashboard
- **Page 1 — Executive Overview:** 4 KPI cards + donut + contract bar chart
- **Page 2 — Churn Deep Dive:** Interactive slicer filtering 4 charts simultaneously
- **Page 3 — Model Output:** Risk tier donut, probability bar, at-risk customer table with conditional formatting

---

## Key Findings

### 1. Contract type is the #1 churn driver
| Contract | Churn Rate |
|---|---|
| Month-to-month | 43.0% |
| One year | 11.3% |
| Two year | 2.8% |

Month-to-month customers churn at **15x the rate** of two-year contract customers.

### 2. The danger zone is the first 12 months
- Average tenure of churned customers: **~18 months**
- Average tenure of retained customers: **~38 months**
- ~50% of all churn happens within the first year

### 3. High charges + fiber optic = highest risk profile
- Fiber optic users churn at **~42%** — the highest of any internet service type
- Churned customers pay on average **$74/month** vs $61 for retained customers
- Electronic check payment method correlates with **45% churn rate**

### 4. Senior citizens are a high-risk segment
- Senior citizens churn at **~42%** vs ~24% for non-seniors
- Customers without a partner or dependents churn significantly more

### 5. Auto-pay dramatically reduces churn
- Customers on automatic payment methods churn at **~15%**
- Electronic check customers churn at **~45%**
- Nudging customers toward auto-pay is a low-cost, high-impact retention lever

---

## Model Performance

| Model | AUC-ROC | 5-Fold CV Mean | CV Std |
|---|---|---|---|
| XGBoost | 0.843 | 0.843 | ±0.008 |
| LightGBM | 0.848 | 0.848 | ±0.007 |

**Winner: LightGBM** — marginally higher AUC, faster training, native imbalance handling.

### Top 5 churn predictors (SHAP)
1. `tenure` — short tenure = highest churn risk
2. `Contract` — month-to-month = 4× more likely to churn
3. `MonthlyCharges` — higher charge = higher risk
4. `InternetService` — fiber optic users churn most
5. `TotalCharges` — low total spend = early-stage, high-risk customer

---

## Dashboard Preview

See `dashboard_preview.pdf` for the full 3-page dashboard.

**Page 1 — Executive Overview**
KPI cards showing 7K customers, 26.54% churn rate, $139K monthly revenue lost, $1.67M annualized revenue lost.

**Page 2 — Churn Deep Dive**
Interactive slicer by contract type filtering 4 charts: internet service breakdown, payment method churn, senior citizen churn, tenure vs charges scatter.

**Page 3 — Model Output**
282 high-risk customers identified. At-risk table with red gradient conditional formatting on predicted churn probability.

---

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/LokeshGaddam14/product-analyst-project.git
cd product-analyst-project
```

### 2. Install dependencies
```bash
pip install pandas numpy matplotlib seaborn xgboost lightgbm shap scikit-learn
```

### 3. Download the dataset
Download `WA_Fn-UseC_-Telco-Customer-Churn.csv` from [Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) and place it in the `data/` folder.

### 4. Run notebooks in order
```
notebooks/phase1_data_cleaning.ipynb
notebooks/phase2_eda.ipynb
notebooks/phase3_sql_analysis.ipynb
notebooks/phase4_modeling.ipynb
```

### 5. Open dashboard
Open `churn_dashboard.pbix` in Power BI Desktop. If prompted to refresh data, point the data source to your local `data/` folder.

---

## Business Recommendations

Based on the analysis, here are three concrete actions ranked by expected impact:

**1. Convert month-to-month customers to annual contracts**
Month-to-month customers are 15× more likely to churn. A targeted offer (discount, feature unlock) timed at month 3–6 — before the churn spike — could significantly improve retention.

**2. Create an early-tenure onboarding program**
50% of all churn happens in the first 12 months. A structured 90-day onboarding sequence for new customers — especially fiber optic subscribers — addresses the highest-risk window directly.

**3. Nudge electronic check payers toward auto-pay**
Electronic check customers churn at 45% vs 15% for auto-pay customers. Even a small incentive (one month discount) to switch payment method could recover a measurable portion of monthly revenue lost.

---

## About

Built as a portfolio project demonstrating end-to-end product analytics skills: data wrangling, exploratory analysis, SQL, machine learning, explainability, and business intelligence dashboarding.

**Author:** Lokesh Gaddam
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/lokesh-gaddam-054b23252)
**Dataset:** [Telco Customer Churn — Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)

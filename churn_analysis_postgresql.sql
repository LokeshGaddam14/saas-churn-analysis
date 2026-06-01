-- ============================================================
-- RaoDo Data Analyst Challenge — Customer Churn Analysis
-- Dataset: Telco Customer Churn (7,043 customers)
-- Author: Lokesh Gaddam | lokeshgaddam2514@gmail.com
-- Database: PostgreSQL
-- ============================================================

-- ============================================================
-- SETUP: Create and load the table
-- ============================================================

CREATE TABLE IF NOT EXISTS telco_churn (
    customer_id        VARCHAR(20),
    gender             VARCHAR(10),
    senior_citizen     INT,           -- 0 = No, 1 = Yes
    partner            VARCHAR(5),
    dependents         VARCHAR(5),
    tenure             INT,
    phone_service      VARCHAR(5),
    multiple_lines     VARCHAR(20),
    internet_service   VARCHAR(20),
    online_security    VARCHAR(20),
    online_backup      VARCHAR(20),
    device_protection  VARCHAR(20),
    tech_support       VARCHAR(20),
    streaming_tv       VARCHAR(20),
    streaming_movies   VARCHAR(20),
    contract           VARCHAR(20),
    paperless_billing  VARCHAR(5),
    payment_method     VARCHAR(40),
    monthly_charges    NUMERIC(8,2),
    total_charges      NUMERIC(10,2),
    churn              INT            -- 0 = No, 1 = Yes
);

-- After loading CSV via \COPY or pgAdmin:
-- \COPY telco_churn FROM 'telco_churn_cleaned.csv' CSV HEADER;


-- ============================================================
-- SECTION 1: OVERALL CHURN METRICS
-- ============================================================

-- 1.1 Overall churn rate
SELECT
    COUNT(*)                                          AS total_customers,
    SUM(churn)                                        AS churned_customers,
    COUNT(*) - SUM(churn)                             AS retained_customers,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)           AS churn_rate_pct,
    ROUND((COUNT(*) - SUM(churn)) * 100.0 / COUNT(*), 2) AS retention_rate_pct
FROM telco_churn;


-- 1.2 Revenue at risk from churned customers
SELECT
    SUM(CASE WHEN churn = 1 THEN monthly_charges ELSE 0 END)       AS monthly_revenue_lost,
    ROUND(SUM(CASE WHEN churn = 1 THEN monthly_charges ELSE 0 END) * 12, 2) AS annualized_revenue_at_risk,
    ROUND(AVG(CASE WHEN churn = 1 THEN monthly_charges END), 2)    AS avg_monthly_charge_churned,
    ROUND(AVG(CASE WHEN churn = 0 THEN monthly_charges END), 2)    AS avg_monthly_charge_retained
FROM telco_churn;


-- ============================================================
-- SECTION 2: CHURN BY SEGMENT
-- ============================================================

-- 2.1 Churn by contract type
SELECT
    contract,
    COUNT(*)                                        AS total_customers,
    SUM(churn)                                      AS churned,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)         AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2)                  AS avg_monthly_charges
FROM telco_churn
GROUP BY contract
ORDER BY churn_rate_pct DESC;


-- 2.2 Churn by internet service type
SELECT
    internet_service,
    COUNT(*)                                        AS total_customers,
    SUM(churn)                                      AS churned,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)         AS churn_rate_pct
FROM telco_churn
GROUP BY internet_service
ORDER BY churn_rate_pct DESC;


-- 2.3 Churn by payment method
SELECT
    payment_method,
    COUNT(*)                                        AS total_customers,
    SUM(churn)                                      AS churned,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)         AS churn_rate_pct
FROM telco_churn
GROUP BY payment_method
ORDER BY churn_rate_pct DESC;


-- 2.4 Churn by gender
SELECT
    gender,
    COUNT(*)                                        AS total_customers,
    SUM(churn)                                      AS churned,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)         AS churn_rate_pct
FROM telco_churn
GROUP BY gender;


-- 2.5 Churn by senior citizen status
SELECT
    CASE WHEN senior_citizen = 1 THEN 'Senior' ELSE 'Non-Senior' END AS segment,
    COUNT(*)                                        AS total_customers,
    SUM(churn)                                      AS churned,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)         AS churn_rate_pct
FROM telco_churn
GROUP BY senior_citizen;


-- ============================================================
-- SECTION 3: TENURE-BASED COHORT ANALYSIS
-- ============================================================

-- 3.1 Churn by tenure band (custom segmentation)
SELECT
    CASE
        WHEN tenure BETWEEN 0  AND 12  THEN '0-12 months (New)'
        WHEN tenure BETWEEN 13 AND 24  THEN '13-24 months (Developing)'
        WHEN tenure BETWEEN 25 AND 48  THEN '25-48 months (Established)'
        WHEN tenure BETWEEN 49 AND 72  THEN '49-72 months (Loyal)'
        ELSE '72+ months (Champion)'
    END AS tenure_segment,
    COUNT(*)                                        AS total_customers,
    SUM(churn)                                      AS churned,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)         AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2)                  AS avg_monthly_charges
FROM telco_churn
GROUP BY tenure_segment
ORDER BY MIN(tenure);


-- 3.2 Average tenure comparison: churned vs retained
SELECT
    CASE WHEN churn = 1 THEN 'Churned' ELSE 'Retained' END AS status,
    ROUND(AVG(tenure), 1)                           AS avg_tenure_months,
    ROUND(MIN(tenure), 1)                           AS min_tenure,
    ROUND(MAX(tenure), 1)                           AS max_tenure,
    COUNT(*)                                        AS customer_count
FROM telco_churn
GROUP BY churn;


-- 3.3 Monthly cohort churn rate (tenure as proxy for join month)
SELECT
    tenure                                          AS months_with_company,
    COUNT(*)                                        AS cohort_size,
    SUM(churn)                                      AS churned_count,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)         AS churn_rate_pct
FROM telco_churn
WHERE tenure <= 24
GROUP BY tenure
ORDER BY tenure;


-- ============================================================
-- SECTION 4: HIGH-VALUE CUSTOMER ANALYSIS
-- ============================================================

-- 4.1 High-value customer definition (above average monthly charges)
SELECT
    customer_id,
    contract,
    tenure,
    monthly_charges,
    total_charges,
    churn
FROM telco_churn
WHERE monthly_charges > (SELECT AVG(monthly_charges) FROM telco_churn)
ORDER BY monthly_charges DESC
LIMIT 20;


-- 4.2 High-risk, high-value customers (churn risk segment)
SELECT
    COUNT(*)                                                    AS high_risk_high_value_count,
    ROUND(SUM(monthly_charges), 2)                              AS monthly_revenue_at_risk,
    ROUND(SUM(monthly_charges) * 12, 2)                         AS annualized_revenue_at_risk
FROM telco_churn
WHERE churn = 1
  AND monthly_charges > (SELECT AVG(monthly_charges) FROM telco_churn)
  AND contract = 'Month-to-month';


-- 4.3 Revenue at risk by contract + internet service (cross-segment)
SELECT
    contract,
    internet_service,
    COUNT(*)                                                    AS churned_customers,
    ROUND(SUM(monthly_charges), 2)                              AS monthly_revenue_lost,
    ROUND(SUM(monthly_charges) * 12, 2)                         AS annualized_revenue_at_risk
FROM telco_churn
WHERE churn = 1
GROUP BY contract, internet_service
ORDER BY annualized_revenue_at_risk DESC;


-- ============================================================
-- SECTION 5: WINDOW FUNCTIONS & ADVANCED ANALYTICS
-- ============================================================

-- 5.1 Rank customers by monthly charges within each contract type
SELECT
    customer_id,
    contract,
    monthly_charges,
    churn,
    RANK() OVER (PARTITION BY contract ORDER BY monthly_charges DESC) AS rank_within_contract,
    ROUND(AVG(monthly_charges) OVER (PARTITION BY contract), 2)       AS avg_charges_in_contract
FROM telco_churn
ORDER BY contract, rank_within_contract
LIMIT 30;


-- 5.2 Running total of churned customers by tenure (cohort progression)
SELECT
    tenure,
    SUM(churn)                                          AS churned_this_month,
    SUM(SUM(churn)) OVER (ORDER BY tenure)              AS cumulative_churn,
    COUNT(*)                                            AS customers_at_tenure,
    SUM(COUNT(*)) OVER (ORDER BY tenure)                AS cumulative_customers
FROM telco_churn
GROUP BY tenure
ORDER BY tenure;


-- 5.3 Percentile rank of each customer's monthly charges within their segment
SELECT
    customer_id,
    contract,
    monthly_charges,
    churn,
    ROUND(PERCENT_RANK() OVER (
        PARTITION BY contract ORDER BY monthly_charges
    ) * 100, 1) AS percentile_in_contract
FROM telco_churn
WHERE churn = 1
ORDER BY contract, monthly_charges DESC
LIMIT 30;


-- 5.4 Lag analysis — charge difference from contract group average
SELECT
    customer_id,
    contract,
    monthly_charges,
    churn,
    ROUND(AVG(monthly_charges) OVER (PARTITION BY contract), 2) AS contract_avg,
    ROUND(monthly_charges - AVG(monthly_charges) OVER (PARTITION BY contract), 2) AS diff_from_avg
FROM telco_churn
WHERE churn = 1
ORDER BY diff_from_avg DESC
LIMIT 20;


-- ============================================================
-- SECTION 6: RETENTION OPPORTUNITY ANALYSIS
-- ============================================================

-- 6.1 Customers most likely to benefit from auto-pay nudge
SELECT
    payment_method,
    contract,
    COUNT(*)                                            AS at_risk_customers,
    ROUND(SUM(monthly_charges), 2)                      AS monthly_revenue_at_risk,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)             AS churn_rate_pct
FROM telco_churn
WHERE payment_method = 'Electronic check'
  AND contract = 'Month-to-month'
GROUP BY payment_method, contract;


-- 6.2 Customers without tech support: churn comparison
SELECT
    tech_support,
    COUNT(*)                                            AS total_customers,
    SUM(churn)                                          AS churned,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 2)             AS churn_rate_pct
FROM telco_churn
GROUP BY tech_support
ORDER BY churn_rate_pct DESC;


-- 6.3 Month-to-month customers approaching 12-month mark (upgrade opportunity)
SELECT
    customer_id,
    tenure,
    monthly_charges,
    internet_service,
    payment_method
FROM telco_churn
WHERE contract = 'Month-to-month'
  AND churn = 0
  AND tenure BETWEEN 9 AND 12
ORDER BY monthly_charges DESC;


-- 6.4 Summary: Retention impact if electronic check users converted to auto-pay
-- (Based on auto-pay churn rate of ~15% vs electronic check ~45%)
SELECT
    COUNT(*)                                            AS electronic_check_customers,
    SUM(churn)                                          AS currently_churning,
    ROUND(SUM(monthly_charges), 2)                      AS monthly_revenue_at_risk,
    ROUND(COUNT(*) * 0.45, 0)                           AS expected_churn_at_current_rate,
    ROUND(COUNT(*) * 0.15, 0)                           AS expected_churn_if_converted_to_autopay,
    ROUND((COUNT(*) * 0.45 - COUNT(*) * 0.15) * AVG(monthly_charges), 2) AS monthly_revenue_saved_by_conversion
FROM telco_churn
WHERE payment_method = 'Electronic check';


-- ============================================================
-- END OF FILE
-- ============================================================

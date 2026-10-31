-- Access-site infection after PCI (simulated data)
-- Tables: procedures, operators, infection_events
-- Rates are per 1,000 procedures. Dialect: SQLite.

-- Q1: Overall infection rates
SELECT
    COUNT(*)                                                    AS procedures,
    SUM(suspected_infection_30d)                                AS suspected,
    SUM(confirmed_infection_30d)                                AS confirmed,
    ROUND(1000.0 * SUM(suspected_infection_30d) / COUNT(*), 1)  AS suspected_per_1000,
    ROUND(1000.0 * SUM(confirmed_infection_30d) / COUNT(*), 1)  AS confirmed_per_1000
FROM procedures;

-- Q2: Infection rate by case type
SELECT
    case_type,
    COUNT(*)                                                    AS procedures,
    SUM(suspected_infection_30d)                                AS suspected,
    SUM(confirmed_infection_30d)                                AS confirmed,
    ROUND(1000.0 * SUM(suspected_infection_30d) / COUNT(*), 1)  AS suspected_per_1000,
    ROUND(1000.0 * SUM(confirmed_infection_30d) / COUNT(*), 1)  AS confirmed_per_1000
FROM procedures
GROUP BY case_type
ORDER BY suspected_per_1000 DESC;

-- Q3: STEMI vs elective, split by access route
SELECT
    case_type,
    access_site,
    COUNT(*)                                                    AS procedures,
    SUM(suspected_infection_30d)                                AS suspected,
    ROUND(1000.0 * SUM(suspected_infection_30d) / COUNT(*), 1)  AS suspected_per_1000
FROM procedures
WHERE case_type IN ('STEMI', 'Elective')
GROUP BY case_type, access_site
ORDER BY case_type, access_site;

-- Q4: Monthly rate with a 3-month moving average (window function)
WITH monthly AS (
    SELECT
        SUBSTR(procedure_date, 1, 7)                            AS month,
        COUNT(*)                                                AS procedures,
        SUM(suspected_infection_30d)                            AS suspected
    FROM procedures
    GROUP BY SUBSTR(procedure_date, 1, 7)
)
SELECT
    month,
    procedures,
    suspected,
    ROUND(1000.0 * suspected / procedures, 1)                   AS rate_per_1000,
    ROUND(1000.0 * SUM(suspected) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
          / SUM(procedures) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1)
                                                                AS moving_avg_3m_per_1000
FROM monthly
ORDER BY month;

-- Q5: Operator comparison (JOIN) with ranking
-- Caution: each operator has only a few events, so differences are mostly chance.
-- This query shows the SQL technique, not a fair way to judge operators.
SELECT
    o.operator_id,
    o.years_experience,
    COUNT(*)                                                    AS procedures,
    SUM(p.suspected_infection_30d)                              AS suspected,
    ROUND(1000.0 * SUM(p.suspected_infection_30d) / COUNT(*), 1) AS suspected_per_1000,
    RANK() OVER (ORDER BY 1.0 * SUM(p.suspected_infection_30d) / COUNT(*) DESC)
                                                                AS rate_rank
FROM procedures p
JOIN operators o ON o.operator_id = p.operator_id
GROUP BY o.operator_id, o.years_experience
ORDER BY rate_rank;

-- Q6: Severity and culture result of suspected infections
SELECT
    p.case_type,
    e.severity,
    COUNT(*)                                                    AS events,
    SUM(e.confirmed)                                            AS confirmed,
    SUM(e.readmitted)                                           AS readmitted
FROM infection_events e
JOIN procedures p ON p.procedure_id = e.procedure_id
GROUP BY p.case_type, e.severity
ORDER BY p.case_type, events DESC;

-- Q7: Organisms in confirmed infections
SELECT
    organism,
    COUNT(*)                                                    AS confirmed_infections
FROM infection_events
WHERE confirmed = 1
GROUP BY organism
ORDER BY confirmed_infections DESC;

-- Q8: When do infections appear? Days from procedure to onset
SELECT
    CASE
        WHEN days_to_onset <= 3  THEN '1-3 days'
        WHEN days_to_onset <= 7  THEN '4-7 days'
        WHEN days_to_onset <= 14 THEN '8-14 days'
        ELSE '15-30 days'
    END                                                         AS onset_window,
    COUNT(*)                                                    AS events,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS percent_of_events
FROM infection_events
GROUP BY onset_window
ORDER BY MIN(days_to_onset);

-- Q9: Skin preparation and case type (process measure)
SELECT
    case_type,
    CASE WHEN skin_prep_complete = 1 THEN 'Complete' ELSE 'Incomplete' END
                                                                AS skin_prep,
    COUNT(*)                                                    AS procedures,
    SUM(suspected_infection_30d)                                AS suspected,
    ROUND(1000.0 * SUM(suspected_infection_30d) / COUNT(*), 1)  AS suspected_per_1000
FROM procedures
GROUP BY case_type, skin_prep
ORDER BY case_type, skin_prep;

-- Q10: Highest-risk profile: femoral access with incomplete skin preparation
WITH high_risk AS (
    SELECT *
    FROM procedures
    WHERE access_site = 'Femoral' AND skin_prep_complete = 0
)
SELECT
    COUNT(*)                                                    AS procedures,
    SUM(suspected_infection_30d)                                AS suspected,
    ROUND(1000.0 * SUM(suspected_infection_30d) / COUNT(*), 1)  AS suspected_per_1000,
    (SELECT ROUND(1000.0 * SUM(suspected_infection_30d) / COUNT(*), 1) FROM procedures)
                                                                AS overall_per_1000
FROM high_risk;

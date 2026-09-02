DROP VIEW IF EXISTS vw_campaign_performance;
DROP VIEW IF EXISTS vw_campaign_incrementality;

CREATE VIEW vw_campaign_performance AS
SELECT
    c.campaign_id,
    c.campaign_name,
    c.channel,
    COUNT(DISTINCT e.customer_id) AS reached_customers,
    SUM(e.impressions) AS impressions,
    SUM(e.clicks) AS clicks,
    SUM(e.converted) AS conversions,
    ROUND(SUM(e.order_value), 2) AS observed_revenue,
    ROUND(SUM(e.media_cost), 2) AS spend,
    ROUND(1.0 * SUM(e.clicks) / NULLIF(SUM(e.impressions), 0), 4) AS ctr,
    ROUND(1.0 * SUM(e.converted) / NULLIF(COUNT(DISTINCT e.customer_id), 0), 4) AS conversion_rate,
    ROUND(SUM(e.media_cost) / NULLIF(SUM(e.converted), 0), 2) AS cpa,
    ROUND(SUM(e.order_value) / NULLIF(SUM(e.media_cost), 0), 2) AS observed_roas
FROM campaigns c
JOIN exposures e USING (campaign_id)
WHERE e.assignment = 'treatment'
GROUP BY 1, 2, 3;

CREATE VIEW vw_campaign_incrementality AS
WITH experiment AS (
    SELECT
        campaign_id,
        assignment,
        COUNT(DISTINCT customer_id) AS customers,
        SUM(converted) AS conversions,
        SUM(media_cost) AS spend
    FROM exposures
    GROUP BY 1, 2
), pivoted AS (
    SELECT
        campaign_id,
        MAX(CASE WHEN assignment = 'treatment' THEN customers END) AS treatment_customers,
        MAX(CASE WHEN assignment = 'treatment' THEN conversions END) AS treatment_conversions,
        MAX(CASE WHEN assignment = 'control' THEN customers END) AS control_customers,
        MAX(CASE WHEN assignment = 'control' THEN conversions END) AS control_conversions,
        MAX(CASE WHEN assignment = 'treatment' THEN spend END) AS spend
    FROM experiment
    GROUP BY 1
)
SELECT
    c.campaign_id,
    c.campaign_name,
    c.channel,
    p.treatment_customers,
    p.control_customers,
    ROUND(1.0 * p.treatment_conversions / p.treatment_customers, 4) AS treatment_cvr,
    ROUND(1.0 * p.control_conversions / p.control_customers, 4) AS control_cvr,
    ROUND(1.0 * p.treatment_conversions / p.treatment_customers - 1.0 * p.control_conversions / p.control_customers, 4) AS absolute_lift,
    ROUND(p.spend, 2) AS spend
FROM pivoted p
JOIN campaigns c USING (campaign_id);


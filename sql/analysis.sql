-- 1. Which channels create incremental demand instead of only claiming existing demand?
SELECT
    channel,
    COUNT(*) AS campaigns,
    ROUND(AVG(absolute_lift) * 100, 2) AS avg_lift_percentage_points,
    ROUND(SUM(spend), 2) AS spend
FROM vw_campaign_incrementality
GROUP BY channel
ORDER BY avg_lift_percentage_points DESC;

-- 2. Which campaigns combine scale and efficient observed performance?
SELECT campaign_name, channel, reached_customers, conversions, cpa, observed_roas
FROM vw_campaign_performance
ORDER BY observed_roas DESC, conversions DESC;

-- 3. Where does observed ROAS risk overstating impact?
SELECT
    p.campaign_name,
    p.channel,
    p.observed_roas,
    ROUND(i.absolute_lift * 100, 2) AS lift_percentage_points
FROM vw_campaign_performance p
JOIN vw_campaign_incrementality i USING (campaign_id)
ORDER BY p.observed_roas DESC;


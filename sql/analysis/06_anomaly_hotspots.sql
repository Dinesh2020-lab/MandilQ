-- Q: Which markets generate the most price anomalies?
SELECT state, market, commodity, COUNT(*) AS n_anomalies, ROUND(MAX(ABS(robust_z))::numeric, 1) AS max_abs_z
FROM v_anomalies GROUP BY state, market, commodity ORDER BY n_anomalies DESC LIMIT 25;

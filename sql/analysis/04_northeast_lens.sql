-- Q: How do North-East prices compare with the all-India median? (check n_obs for sparsity)
WITH india AS (
  SELECT commodity, year, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY avg_modal_price) AS india_median
  FROM v_monthly_prices GROUP BY commodity, year)
SELECT m.commodity, m.state, m.year, ROUND(AVG(m.avg_modal_price)::numeric, 0) AS state_avg,
       ROUND(i.india_median::numeric, 0) AS india_median,
       ROUND((AVG(m.avg_modal_price) / i.india_median - 1)::numeric * 100, 1) AS pct_vs_india,
       SUM(m.n_obs) AS n_obs
FROM v_monthly_prices m JOIN india i USING (commodity, year)
WHERE m.state IN ('Tripura','Manipur','Assam','Meghalaya','Mizoram','Nagaland','Arunachal Pradesh','Sikkim')
GROUP BY m.commodity, m.state, m.year, i.india_median ORDER BY m.commodity, m.state, m.year;

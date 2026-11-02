-- Q: How large is the gap between the cheapest and dearest state per commodity-month?
WITH ranked AS (
  SELECT commodity, month_start, state, avg_modal_price,
         RANK() OVER (PARTITION BY commodity, month_start ORDER BY avg_modal_price) AS lo,
         RANK() OVER (PARTITION BY commodity, month_start ORDER BY avg_modal_price DESC) AS hi
  FROM v_monthly_prices)
SELECT commodity, month_start,
       MAX(CASE WHEN lo = 1 THEN state END) AS cheapest_state,
       MAX(CASE WHEN hi = 1 THEN state END) AS dearest_state,
       ROUND((MAX(avg_modal_price) - MIN(avg_modal_price))::numeric, 0) AS spread_inr_per_quintal
FROM ranked GROUP BY commodity, month_start ORDER BY spread_inr_per_quintal DESC LIMIT 50;

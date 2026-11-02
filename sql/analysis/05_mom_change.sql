-- Q: Which commodity-state months saw the sharpest month-on-month price jumps?
SELECT commodity, state, month_start, ROUND(avg_modal_price::numeric, 0) AS price,
       ROUND((avg_modal_price / NULLIF(LAG(avg_modal_price) OVER w, 0) - 1)::numeric * 100, 1) AS mom_pct
FROM v_monthly_prices WINDOW w AS (PARTITION BY commodity, state ORDER BY month_start)
ORDER BY mom_pct DESC NULLS LAST LIMIT 50;

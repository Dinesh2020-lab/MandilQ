-- Q: In which months is each commodity typically cheapest / dearest?
SELECT commodity, month, ROUND(seasonal_index::numeric, 3) AS seasonal_index,
       RANK() OVER (PARTITION BY commodity ORDER BY seasonal_index DESC) AS peak_rank
FROM v_seasonality ORDER BY commodity, month;

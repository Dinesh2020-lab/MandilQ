-- Q: Which commodity-state pairs have the most volatile monthly prices?
SELECT commodity, state, ROUND(cv::numeric, 3) AS cv,
       NTILE(4) OVER (PARTITION BY commodity ORDER BY cv DESC) AS volatility_quartile
FROM v_volatility ORDER BY cv DESC LIMIT 50;

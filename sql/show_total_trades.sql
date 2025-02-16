SELECT
    politician_name,
    COUNT(trade_id) AS total_trades,
    COUNT(CASE WHEN transaction_type = 'P' THEN trade_id ELSE NULL END) AS total_purchases,
    COUNT(CASE WHEN transaction_type = 'S' THEN trade_id ELSE NULL END) AS total_sales
FROM
    house_data
GROUP BY
    politician_name
ORDER BY
    total_trades DESC;
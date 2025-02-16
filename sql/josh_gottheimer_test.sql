SELECT AVG(days_difference)
FROM (
    SELECT transaction_type, transaction_date, notification_date, notification_date::date - transaction_date::date AS days_difference, asset_name, asset_ticker
    FROM house_data
    WHERE politician_name = 'Josh Gottheimer'
      AND asset_type = 'ST'
) AS subquery;
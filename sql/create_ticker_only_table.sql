CREATE TABLE house_data_filtered AS 
SELECT * FROM house_data
WHERE LENGTH(asset_ticker) > 0
AND asset_type = 'ST';

ALTER TABLE house_data_filtered
ADD PRIMARY KEY (trade_id);
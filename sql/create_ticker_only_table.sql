CREATE TABLE house_data_filtered AS 
SELECT * FROM house_data
WHERE LENGTH(asset_ticker) > 0;
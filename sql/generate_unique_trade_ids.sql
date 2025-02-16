-- This is a temporary fix. Using this in a full implementation could cause errors with the IDs
ALTER TABLE house_data ADD COLUMN trade_id SERIAL PRIMARY KEY;
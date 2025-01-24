CREATE TABLE politicians AS
SELECT DISTINCT politician
FROM house_data;

ALTER TABLE politicians
ADD COLUMN politician_id SERIAL PRIMARY KEY;
CREATE TABLE politicians AS
SELECT DISTINCT politician_name
FROM house_data;

ALTER TABLE politicians
ADD COLUMN politician_id SERIAL PRIMARY KEY;

ALTER TABLE house_data
ADD CONSTRAINT fk_politician 
FOREIGN KEY (politician) 
REFERENCES politicians(politician_id);

UPDATE house_data
SET politician_id = politicians.politician_id
FROM politicians
WHERE house_data.politician = politicians.politician_character;
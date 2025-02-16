ALTER TABLE house_data
ADD COLUMN politician_id INT;

UPDATE house_data hd
SET politician_id = p.politician_id
FROM politicians p
WHERE hd.politician_name = p.politician_name;

ALTER TABLE house_data
ADD CONSTRAINT fk_house_data_politician
FOREIGN KEY (politician_id)
REFERENCES politicians (politician_id)
ON DELETE CASCADE;
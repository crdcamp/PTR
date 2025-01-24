CREATE TABLE house_data (
   politician VARCHAR(50),
   doc_id VARCHAR (10),
   transaction_type VARCHAR(20),
   transaction_date DATE,
   notification_date DATE,
   asset_name VARCHAR(300),
   asset_ticker VARCHAR(10),
   asset_type CHAR(5),
   min_amount INTEGER,
   max_amount INTEGER,
   trade_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY
);
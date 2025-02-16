-- For individual CSV files (change the date in the csv file name accordingly)
-- Will make this more flexible down the road
\copy house_data FROM 'C:/Users/crdca/Desktop/CSite/PTR/data/csv/csv_cleaned/2021_house_trades_cleaned.csv' WITH (FORMAT csv, HEADER true);
\copy house_data FROM 'C:/Users/crdca/Desktop/CSite/PTR/data/csv/csv_cleaned/2022_house_trades_cleaned.csv' WITH (FORMAT csv, HEADER true);
\copy house_data FROM 'C:/Users/crdca/Desktop/CSite/PTR/data/csv/csv_cleaned/2023_house_trades_cleaned.csv' WITH (FORMAT csv, HEADER true);
\copy house_data FROM 'C:/Users/crdca/Desktop/CSite/PTR/data/csv/csv_cleaned/2024_house_trades_cleaned.csv' WITH (FORMAT csv, HEADER true);
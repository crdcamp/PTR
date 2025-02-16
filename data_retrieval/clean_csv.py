from config import CSV_DIR, CSV_CLEANED_DIR
import pandas as pd

# TO DO:
"""
- Should add a log for when lines are skipped when reading CSV
- Need to add a function that deletes lines that do not have 7 columns
- Need to sort by publish date before saving CSVs

"""

def clean_csv(start_year, end_year):

    """
    This function could be optimized for larger datasets, but that doesn't
    seem necessary at the moment

    """

    for year in range(start_year, end_year + 1):
        for file in CSV_DIR.glob(f"{year}_house_trades.csv"):    

            # Read with quotes escaped properly
            df = pd.read_csv(file, quoting=1, on_bad_lines='skip')

            # Split Asset column
            df["Asset Name"] = df.Asset.str.split("(").str[0].str.strip()
            df["Asset Ticker"] = df.Asset.str.split("(").str[1].str.split(")").str[0].fillna('')
            df.loc[df["Asset Ticker"].str.match('^[A-Za-z.]+$') == False, "Asset Ticker"] = ''
            df.loc[df["Asset Ticker"].str.islower(), "Asset Ticker"] = ''
            df["Asset Type"] = df.Asset.str.split("[").str[1].str.split("]").str[0].fillna('')
            df.drop("Asset", axis=1, inplace=True)

            # Split Amount column
            df["Min Amount"] = pd.to_numeric(df.Amount.str.split("-").str[0].str.replace(r'[^\d.]', '', regex=True), errors='coerce')
            df["Max Amount"] = pd.to_numeric(df.Amount.str.split("-").str[1].str.replace(r'[^\d.]', '', regex=True), errors='coerce')
            df.drop("Amount", axis=1, inplace=True)

            # Convert to float first to handle NaN, then to int
            df["Min Amount"] = df["Min Amount"].fillna(0).astype(int)
            df["Max Amount"] = df["Max Amount"].fillna(0).astype(int)

            # Clear all whitespace from the Asset Ticker column for database filtering
            df["Asset Ticker"] = df["Asset Ticker"].str.strip()

            output_path = CSV_CLEANED_DIR / f"{year}_house_trades_cleaned.csv"

            # Save the csv while ensuring incomplete rows are dropped
            df.dropna().to_csv(output_path, index=False, quoting=1)
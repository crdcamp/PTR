from config import METADATA_DIR, PDF_DIR
from utils import year_error_handling, handle_download, handle_zip_content, safe_read_csv
import requests
import io
import pandas as pd

def download_ptr_metadata(start_year, end_year):
    year_error_handling(start_year, end_year)

    with requests.Session() as session:
        for year in range(start_year, end_year + 1):
            fd_url = f"https://disclosures-clerk.house.gov/public_disc/financial-pdfs/{year}FD.ZIP"
            fd_csv = f"{year}FD.csv"
            output_path = METADATA_DIR / fd_csv

            content = handle_download(session, fd_url)
            if not content:
                continue

            metadata_txt = handle_zip_content(content)
            if not metadata_txt:
                continue

            try:
                df = pd.read_csv(io.StringIO(metadata_txt), delimiter="\t")
                
                # Apply filtering logic
                df = df[df["FilingType"] == "P"]  # "P" is for "Periodic Transaction Report"
                df["FilingDate"] = pd.to_datetime(df["FilingDate"])
                df["DocID"] = df["DocID"].astype(str)
                df = df[df["DocID"].str.len() == 8]

                # Generate URL column
                df["URL"] = df.apply(
                    lambda row: f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{row['Year']}/{row['DocID']}.pdf",
                    axis=1
                )

                # Sort by FilingDate in descending order
                df.sort_values(by="FilingDate", ascending=False, inplace=True)

                # Save the processed DataFrame
                df.to_csv(output_path, sep="\t", index=False)
                print(f"Processed {fd_csv} saved to {output_path}")
            except Exception as e:
                print(f"Error processing data for year {year}: {e}")

def download_ptr_pdfs(start_year, end_year):
    year_error_handling(start_year, end_year)

    with requests.Session() as session:
        for metadata_file in METADATA_DIR.iterdir():
            # Skip files that don't match the expected pattern
            if "FD" not in metadata_file.name or not metadata_file.name.endswith(".csv"):
                continue

            # Extract year from file name
            try:
                year = int(metadata_file.stem[:-2])
            except ValueError:
                print(f"Skipping file with unexpected name format: {metadata_file.name}")
                continue

            year_dir = PDF_DIR / str(year)
            year_dir.mkdir(parents=True, exist_ok=True)

            df = safe_read_csv(metadata_file, sep="\t")
            if df is None:
                continue

            for url in df["URL"]:
                filename = url.split("/")[-1]
                filepath = year_dir / filename

                # Skip if file already exists
                if filepath.exists():
                    print(f"File already exists, skipping: {filename}")
                    continue

                content = handle_download(session, url)
                if not content:
                    continue

                try:
                    with open(filepath, "wb") as f:
                        f.write(content)
                    print(f"Downloaded PDF: {filename} to {year_dir}")
                except Exception as e:
                    print(f"Error saving PDF: {url} - {e}")
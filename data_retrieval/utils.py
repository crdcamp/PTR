from config import CSV_DIR, CSV_CLEANED_DIR
import logging
from pathlib import Path
from datetime import datetime
from pathlib import Path
import io
import requests
import zipfile
from typing import Optional
import pandas as pd

# Will need to check later if this error handling actually holds up
# Probably should add logging to all (if not most) of these...

logger = logging.getLogger(__name__)

""""
Not even sure if it's actually working honestly.... gonna take some tedious 
testing and a bunch of work to find out

After looking in to it, I think I have quite a mess on our hands with most
print statements and loging (logging is especially messy). 
I'll have to do a deep dive into this.

"""

def check_if_processed(year):
    """Return set of already processed rows for a given year"""
    validated_path = CSV_CLEANED_DIR / f"{year}_house_trades_cleaned.csv"
    source_path = CSV_DIR / f"{year}_house_trades.csv"

    result = {
        "status": "error",
        "message": "",
        "discrepancies": []
    }

    try:
        if not validated_path.exists():
            result["message"] = f"Validated file path not found: {validated_path}"
            logger.error(result["message"])
            return result

        if not source_path.exists():
            result["message"] = f"Source file path not found: {source_path}"
            logger.error(result["message"])
            return result

        validated_df = pd.read_csv(validated_path, header=0)
        source_df = pd.read_csv(source_path, header=0)

        validated_rows = set(map(tuple, validated_df.itertuples(index=False)))
        source_rows = set(map(tuple, source_df.itertuples(index=False)))

        processed_rows = validated_rows.intersection(source_rows)

        result["status"] = "success"
        return {"status": "success", "processed_rows": processed_rows}
        
    except Exception as e:
        result["message"] = f"Error processing files: {str(e)}"
        logger.error(result["message"])
        return result

def year_error_handling(start_year, end_year):
    current_year = datetime.now().year

    if not isinstance(start_year, int) or not isinstance(end_year, int):
        raise TypeError("Start and end years must be integers")

    if start_year < 2015 or end_year > current_year:  # Metadata structure changes prior to 2015, so we'll 
        raise ValueError(f"Years must be between 2015 and the current year ({current_year})")

def handle_download(session: requests.Session, url: str, timeout: int = 30) -> Optional[bytes]:
    """Handle download with consistent error handling"""
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        if not response.content:
            print(f"Error: Empty response received for {url}")
            return None
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading from {url}: {e}")
        return None

def handle_zip_content(content: bytes, file_index: int = 0) -> Optional[str]:
    """Extract content from zip file with consistent error handling"""
    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as zip_ref:
            zip_contents = zip_ref.namelist()
            if not zip_contents:
                print("No files found in ZIP")
                return None
            with zip_ref.open(zip_contents[file_index]) as file:
                return file.read().decode("utf-8")
    except (zipfile.BadZipFile, IndexError) as e:
        print(f"Error processing ZIP file: {e}")
        return None

def safe_read_csv(filepath: Path, **kwargs) -> Optional[pd.DataFrame]:
    """Safely read CSV with consistent error handling"""
    try:
        return pd.read_csv(filepath, **kwargs)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None
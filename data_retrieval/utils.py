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


def validate_trades(year):
    # Declare file paths
    source_path = CSV_DIR / f"{year}_house_trades.csv"
    validated_path = CSV_CLEANED_DIR / f"{year}_house_trades_cleaned.csv"

    # Validate file paths
    if not validated_path.exists() or not source_path.exists():
        logger.warning(f"File path(s) not found")
        return False
    
    try:
        # Read source and validated CSVs
        source_df = pd.read_csv(source_path)
        validated_df = pd.read_csv(validated_path)

        # Access the DocID column both CSVs
        source_doc_ids = set(source_df["DocID"])
        validated_doc_ids = set(validated_df["DocID"])

        









def validate_trades(year):
    source_path = CSV_DIR / f"{year}_house_trades.csv"
    validated_path = CSV_CLEANED_DIR / f"{year}_house_trades_cleaned.csv"

    if not validated_path.exists() or not source_path.exists():
        logger.warning(f"Cannot find file path(s) for {year}")
        return set()

    try:
        validated_df = pd.read_csv(validated_path)
        source_df = pd.read_csv(source_path)
        
        validated_doc_ids = set(validated_df["DocID"])
        source_doc_ids = set(source_df["DocID"])
        
        already_processed = source_doc_ids.intersection(validated_doc_ids)
        for doc_id in already_processed:
            logger.warning(f"{doc_id} has already been processed. Skipping")
            
        return already_processed
        
    except Exception as e:
        logger.error(f"Error reading files: {e}")
        return set()

def year_error_handling(start_year, end_year):
    current_year = datetime.now().year

    if not isinstance(start_year, int) or not isinstance(end_year, int):
        raise TypeError("Start and end years must be integers")

    if start_year < 2015 or end_year > current_year:  # Metadata structure changes prior to 2015
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
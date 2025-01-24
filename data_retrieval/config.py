import os
from pathlib import Path

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__))).parent

METADATA_DIR = BASE_DIR / "data" / "metadata"
PDF_DIR = BASE_DIR / "data" / "pdf"
CSV_DIR = BASE_DIR / "data" / "csv"
CSV_CLEANED_DIR = BASE_DIR / "data" / "csv" / "csv_cleaned"
DATABASE_DIR = BASE_DIR / "database"

for directory in [METADATA_DIR, PDF_DIR, CSV_DIR, CSV_CLEANED_DIR, DATABASE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
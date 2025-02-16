from config import METADATA_DIR, PDF_DIR, CSV_DIR, CSV_CLEANED_DIR
from utils import year_error_handling
import os
import pandas as pd
from anthropic import Anthropic
import base64
from dotenv import load_dotenv
import time
from tqdm import tqdm
import logging

# THESE LOGS NEED TO BE CLEANED UP!!!!!!!!!!

# Set up logging to both file and console
logging.basicConfig(
   level=logging.INFO,
   format='%(levelname)s - %(message)s',
   handlers=[
       logging.FileHandler('processing.log'),
       logging.StreamHandler()
   ]
)

logger = logging.getLogger(__name__)

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
   raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

MODEL_NAME = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 8192
RETRY_ATTEMPTS = 2
RATE_LIMIT_WAIT = 70
SERVER_ERROR_WAIT = 5
client = None

EXTRACTION_PROMPT = """
Extract every transaction from this Periodic Transaction Report into a CSV table. For each field in the output:
1. Surround every field with double quotes, even numbers and dates
2. Use the following columns, in order: "Asset","Transaction Type","Date","Notification Date","Amount". Every row should have 7 columns.

Follow these formatting rules exactly:
1. Asset names must include square brackets containing any type codes (e.g., "[ST]", "[HN]")
2. Asset names must be complete, including share classes and "(partial)" designations
3. Preserve exact ticker symbols in parentheses
4. Keep complete transaction types (e.g., "S", "P", "S (partial)")
5. Present dates in MM/DD/YYYY format
6. Maintain exact amount ranges with dollar signs (e.g., "$1001 - $15000")
7. Exclude Owner, ID, Filing Status, and Subholding fields
8. Include full company names and designations (e.g., "Class A Ordinary Shares", "Inc.", "plc")
9. Only output the CSV content. DO NOT add any comments or additional text beyond the formatting rules.

Output example format:
"Asset","Transaction Type","Date","Notification Date","Amount"
"Apple Inc. (AAPL) [ST]","P","01/15/2024","01/16/2024","$1001 - $15000"
"""

def antropic_api_setup():
   global client
   if not ANTHROPIC_API_KEY:
       raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

   client = Anthropic(
      api_key=ANTHROPIC_API_KEY,
      default_headers={"anthropic-beta": "pdfs-2024-09-25"}
   )

def check_if_processed(year):
   """Return set of already processed DocIDs for a given year"""
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

       # Convert DocIDs to strings for consistent comparison
       validated_ids = set(validated_df["DocID"].astype(str))
       source_ids = set(source_df["DocID"].astype(str))

       processed_docids = validated_ids.intersection(source_ids)

       result["status"] = "success"
       return {"status": "success", "processed_docids": processed_docids}
       
   except Exception as e:
       result["message"] = f"Error processing files: {str(e)}"
       logger.error(result["message"])
       return result

def load_metadata(year):
   """Load and process metadata file for a given year to match DocID with politician names"""
   metadata_file = METADATA_DIR / f"{year}FD.csv"
   try:
       if not metadata_file.exists():
           logger.error(f"Metadata file not found: {metadata_file}")
           return {}
       
       metadata_df = pd.read_csv(metadata_file, delimiter="\t")
       name_lookup = {
           str(row['DocID']): f"{row['First']} {row['Last']}".strip()
           for _, row in metadata_df.iterrows()
       }
       return name_lookup
       
   except Exception as e:
       logger.error(f"Error loading metadata: {str(e)}")
       return {}

def extract_pdf_as_csv(start_year, end_year):
    year_error_handling(start_year, end_year)
    antropic_api_setup()

    for year in range(start_year, end_year + 1):
        logger.info(f"Processing year {year}")
        processed_trades = check_if_processed(year)
        name_lookup = load_metadata(year)

        # Track files processed in this run
        processed_in_this_run = set()
        failed_files = []

        """Set up paths and files"""
        pdf_path = PDF_DIR / str(year)
        if not pdf_path.exists():
            logger.warning(f"Directory for year {year} not found. Skipping...")
            continue

        pdf_files = list(pdf_path.glob("*.pdf"))
        
        csv_filename = f"{year}_house_trades.csv"
        csv_path = CSV_DIR / csv_filename
        csv_headers = '"Politician","DocID","Asset","Transaction Type","Date","Notification Date","Amount"\n'

        # Initialize CSV if it doesn't exist
        needs_header = not csv_path.exists()
        if needs_header:
            with open(csv_path, 'w', encoding="utf-8") as f:
                f.write(csv_headers)

        # Get processed DocIDs
        if processed_trades["status"] == "success":
            processed_docids = processed_trades["processed_docids"]
            logger.info(f"Found {len(processed_docids)} previously processed DocIDs")
        else:
            processed_docids = set()
            logger.warning("No previously processed DocIDs found")

        # Check existing CSV for DocIDs
        existing_docids = set()
        if csv_path.exists():
            existing_df = pd.read_csv(csv_path)
            existing_docids = set(existing_df['DocID'].astype(str).str.strip())
            logger.info(f"Found {len(existing_docids)} existing DocIDs in CSV")

        # Filter unprocessed files
        all_processed_ids = processed_docids.union(existing_docids)
        unprocessed_files = [
            pdf_file for pdf_file in pdf_files 
            if pdf_file.stem.strip() not in all_processed_ids
        ]
        
        logger.info(f"Found {len(unprocessed_files)} files to process")
        progress_bar = tqdm(unprocessed_files, desc=f"Processing PDFs for {year}", unit="file")

        """Process PDFs"""
        for pdf_file in progress_bar:
            docid = pdf_file.stem.strip()

            # Skip if processed in this run or previously
            if docid in processed_in_this_run or docid in all_processed_ids:
                continue

            retry_attempts = 0
            success = False
            while retry_attempts <= RETRY_ATTEMPTS and not success:
                try:
                    politician_name = name_lookup.get(docid, "Unknown")
                    
                    with open(pdf_file, "rb") as f:
                        binary_data = f.read()
                        base64_string = base64.b64encode(binary_data).decode("utf-8")
                    
                    messages = [{
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": base64_string
                                }
                            },
                            {"type": "text", "text": EXTRACTION_PROMPT}
                        ]
                    }]
                    
                    response = client.messages.create(
                        model=MODEL_NAME,
                        max_tokens=MAX_TOKENS,
                        messages=messages
                    )
                    
                    content = response.content[0].text
                    if not content.strip() or not any(line.count(',') >= 4 for line in content.split('\n') if line.strip()):
                        raise ValueError("Response validation failed: Invalid or empty content")
                    
                    # Skip header line except for first file
                    content_lines = content.split('\n')
                    data_lines = [line for line in content_lines if line.strip() and not line.startswith('"Asset",')]
                    
                    modified_lines = [f'"{politician_name}","{docid}",{line}' for line in data_lines]
                    
                    if not modified_lines:
                        raise ValueError("No valid data lines found in response")
                    
                    with open(csv_path, 'a', encoding="utf-8") as f:
                        f.write('\n'.join(modified_lines) + '\n')
                    
                    success = True
                    processed_in_this_run.add(docid)
                    progress_bar.write(f"Successfully processed {pdf_file.name}")

                except Exception as e:
                    error_message = str(e)
                    retry_attempts += 1
                    logger.error(f"Error processing {pdf_file.name}: {error_message}")
                    
                    if "Error code: 429" in error_message and "rate_limit_error" in error_message:
                        logger.warning(f"Rate limit hit - waiting {RATE_LIMIT_WAIT} seconds")
                        time.sleep(RATE_LIMIT_WAIT)
                    elif "Error code: 500" in error_message:
                        if retry_attempts <= RETRY_ATTEMPTS:
                            logger.warning(f"Server error - waiting {SERVER_ERROR_WAIT} seconds")
                            time.sleep(SERVER_ERROR_WAIT)
                        else:
                            logger.error(f"Max retries reached for {pdf_file.name}")
                    else:
                        logger.error(f"Unrecoverable error for {pdf_file.name}")
                        break
            
            if not success:
                logger.error(f"Failed to process {pdf_file.name} after {retry_attempts} attempts")
                failed_files.append(pdf_file.name)

        # End of year summary
        logger.info(f"Completed year {year}")
        logger.info(f"Successfully processed {len(processed_in_this_run)} new files")
        if failed_files:
            logger.warning(f"Failed to process {len(failed_files)} files: {', '.join(failed_files)}")
        logger.info(f"Output saved to {csv_filename}")
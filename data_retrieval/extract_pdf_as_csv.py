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

# Set up logging to both file and console
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum level of messages to show
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('processing.log'),  # Save to a file
        logging.StreamHandler()  # Show in console
    ]
)

logger = logging.getLogger(__name__)

# I HATE TO SAY IT.... BUT YOU MIGHT NEED TO CHECK THE TRADES USING DOCID INSTEAD

# VERY IMPORTANT!!!!!! ADJUST THE EXTRACTION FUNCTION SO IT DOESN'T OVERWRITE THE CSV FILES

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
    """Return set of already processed rows for a given year"""
    validated_path = CSV_CLEANED_DIR / f"{year}_house_trades_cleaned.csv"
    source_path = CSV_DIR / f"{year}_house_trades.csv"

    result = {
        "status": "error",
        "message": "",
        "discrepancies": []
    }

    try: # THESE WILL STOP THE SCTIPT. WE DON'T WANT THAT!!!!
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

def load_metadata(year):
    """Load and process metadata file for a given year to match DocID with politician names"""
    metadata_file = METADATA_DIR / f"{year}FD.csv"
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file for year {year} not found") # Make this better. Horrendous error handling.
    
    # Create a lookup dictionary with DocID as key and politician name as value
    metadata_df = pd.read_csv(metadata_file, delimiter="\t")
    name_lookup = {}
    for _, row in metadata_df.iterrows():
        docid = str(row['DocID'])
        name = f"{row['First']} {row['Last']}".strip()
        name_lookup[docid] = name
    return name_lookup

def extract_pdf_as_csv(start_year, end_year):
    year_error_handling(start_year, end_year)
    antropic_api_setup()

    for year in range(start_year, end_year + 1):
        processed_trades = check_if_processed(year)
        name_lookup = load_metadata(year)

        """Set up PDF paths and files"""
        pdf_path = PDF_DIR / str(year)
        pdf_files = list(pdf_path.glob("*.pdf"))
        
        """Set up CSV paths and files"""
        csv_filename = f"{year}_house_trades.csv"
        csv_path = CSV_DIR / csv_filename
        csv_headers = '"Politician","DocID","Asset","Transaction Type","Date","Notification Date","Amount"\n'

        # Initialize CSV if it doesn't exist
        is_first_file = not csv_path.exists()
        if is_first_file:
            with open(csv_path, 'w', encoding="utf-8") as f:
                f.write(csv_headers)

        # This needs to be changed. Something about this print statement is just... gross
        if not pdf_path.exists():
            print(f"Directory for year {year} does not found. Skipping...")
            continue
        
        """Set up progress bar"""
        progress_bar = tqdm(pdf_files, desc=f"Processing PDFs for {year}", unit="file")

        # Check if we have any processed trades to compare against
        if processed_trades["status"] == "success":
            processed_rows = processed_trades["processed_rows"]
            logger.info(f"Found {len(processed_rows)} previously processed trades for {year}")
        else:
            processed_rows = set()
            logger.warning(f"No previously processed trades found for {year}")

        # If the CSV exists, we'll read it to check for duplicates
        if csv_path.exists():
            logger.info(f"Found existing CSV file: {csv_path}")
            existing_df = pd.read_csv(csv_path)
            existing_rows = set(map(tuple, existing_df.itertuples(index=False)))
            logger.info(f"Found {len(existing_rows)} existing rows in CSV for {year}")
            
            # Filter out any PDF files that have already been processed
            unprocessed_files = []
            for pdf_file in pdf_files:
                if any(pdf_file.stem in str(row) for row in processed_rows.union(existing_rows)):
                    logger.debug(f"Skipping already processed file: {pdf_file.name}")
                else:
                    unprocessed_files.append(pdf_file)
                    logger.debug(f"Adding unprocessed file to queue: {pdf_file.name}")
            
            logger.info(f"Found {len(unprocessed_files)} unprocessed files out of {len(pdf_files)} total files for {year}")
            progress_bar = tqdm(unprocessed_files, desc=f"Processing PDFs for {year}", unit="file")
        else:
            logger.info(f"No existing CSV file found at {csv_path}. Will process all PDF files.")
            unprocessed_files = pdf_files

        progress_bar = tqdm(unprocessed_files, desc=f"Processing PDFs for {year}", unit="file")

        """Iterate through the files and use Antropic API calls to extract PDFs as CSV"""
        for pdf_file in progress_bar:
            docid = pdf_file.stem

            if docid not in processed_trades:
                retry_attempts = 0
                success = False
                while retry_attempts <= 2 and not success:
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
                        
                        if not is_first_file:
                            content = '\n'.join(content.split('\n')[1:])
                        
                        modified_lines = []
                        for line in content.split('\n'):
                            if line.strip() and not line.startswith('"Asset",'):
                                modified_lines.append(f'"{politician_name}","{docid}",{line}')
                        
                        if not modified_lines:
                            raise ValueError("No valid data lines found in response")
                        
                        with open(csv_path, 'a', encoding="utf-8") as f:
                            f.write('\n'.join(modified_lines) + '\n')
                        
                        success = True
                        is_first_file = False
                        progress_bar.write(f"Successfully processed {pdf_file.name} on attempt {retry_attempts + 1}")

                    except Exception as e:
                        error_message = str(e)
                        retry_attempts += 1
                        
                        if "Error code: 429" in error_message and "rate_limit_error" in error_message:
                            progress_bar.write(f"Rate limit error encountered on attempt {retry_attempts}. Waiting for {RATE_LIMIT_WAIT} seconds...")
                            time.sleep(RATE_LIMIT_WAIT)
                        elif "Error code: 500" in error_message:
                            progress_bar.write(f"Internal server error for {pdf_file.name}, attempt {retry_attempts}...")
                            if retry_attempts <= RETRY_ATTEMPTS:
                                time.sleep(SERVER_ERROR_WAIT)
                            else:
                                progress_bar.write(f"Max retry attempts reached for {pdf_file.name}. Skipping.")
                        else:
                            progress_bar.write(f"Unrecoverable error for {pdf_file.name} on attempt {retry_attempts}: {error_message}")
                            break
                
                if not success:
                    progress_bar.write(f"Failed to process {pdf_file.name} after {retry_attempts} attempts")
                    print(f"Completed processing for year {year}. Output saved to {csv_filename}")
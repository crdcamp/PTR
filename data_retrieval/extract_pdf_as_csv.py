from config import METADATA_DIR, PDF_DIR, CSV_DIR
from utils import year_error_handling, check_if_processed
import os
import pandas as pd
from anthropic import Anthropic
import base64
from dotenv import load_dotenv
import time
from tqdm import tqdm

load_dotenv()

"""
CLEAN THIS MESS UP WHEN check_if_processed is working!!!

I get the overwheling sense there is a lot of unecessary
crap in this file thanks to my ai associates
"""

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

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

def load_metadata(year):
    """Load and process metadata file for a given year"""
    metadata_file = METADATA_DIR / f"{year}FD.csv"
    if not metadata_file.exists():
        raise FileNotFoundError(f"Metadata file for year {year} not found") # Put the utilities function here
    
    metadata_df = pd.read_csv(metadata_file, delimiter="\t")
    # Create a lookup dictionary with DocID as key and politician name as value
    name_lookup = {}
    for _, row in metadata_df.iterrows():
        docid = str(row['DocID'])
        name = f"{row['First']} {row['Last']}".strip()
        name_lookup[docid] = name
    return name_lookup

def extract_pdf_as_csv(start_year, end_year):
   year_error_handling(start_year, end_year)
   client = Anthropic(
       api_key=ANTHROPIC_API_KEY,
       default_headers={"anthropic-beta": "pdfs-2024-09-25"}
   )
   
   MODEL_NAME = "claude-3-5-sonnet-20241022"
   
   for year in range(start_year, end_year + 1):
       print(f"\nProcessing year {year}...")
       
       processed_ids = check_if_processed(year)
       name_lookup = load_metadata(year)
       pdf_year_dir = PDF_DIR / str(year)

       if not pdf_year_dir.exists():
           print(f"Directory for year {year} does not exist. Skipping...")
           continue

       csv_filename = f"{year}_house_trades.csv"
       csv_path = CSV_DIR / csv_filename
       
       is_first_file = True
       headers = '"Politician","DocID","Asset","Transaction Type","Date","Notification Date","Amount"\n'
       
       pdf_files = list(pdf_year_dir.glob("*.pdf"))
       progress_bar = tqdm(pdf_files, desc=f"Processing PDFs for {year}", unit="file")
           
       for pdf_file in progress_bar:
           docid = pdf_file.stem
           if docid not in processed_ids:

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
                        max_tokens=8192,
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
                    
                    content_to_write = headers if is_first_file else ''
                    content_to_write += '\n'.join(modified_lines)
                    
                    with open(csv_path, 'w' if is_first_file else 'a', encoding="utf-8") as f:
                        f.write(content_to_write + '\n')
                    
                    success = True
                    is_first_file = False
                    progress_bar.write(f"Successfully processed {pdf_file.name} on attempt {retry_attempts + 1}")

                except Exception as e:
                    error_message = str(e)
                    retry_attempts += 1
                    
                    if "Error code: 429" in error_message and "rate_limit_error" in error_message:
                        progress_bar.write(f"Rate limit error encountered on attempt {retry_attempts}. Waiting for 70 seconds...")
                        time.sleep(70)
                    elif "Error code: 500" in error_message:
                        progress_bar.write(f"Internal server error for {pdf_file.name}, attempt {retry_attempts}...")
                        if retry_attempts <= 2:
                            time.sleep(5)
                        else:
                            progress_bar.write(f"Max retry attempts reached for {pdf_file.name}. Skipping.")
                    else:
                        progress_bar.write(f"Unrecoverable error for {pdf_file.name} on attempt {retry_attempts}: {error_message}")
                        break
            
            if not success:
                progress_bar.write(f"Failed to process {pdf_file.name} after {retry_attempts} attempts")
                print(f"Completed processing for year {year}. Output saved to {csv_filename}")
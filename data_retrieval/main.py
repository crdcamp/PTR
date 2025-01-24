from download_metadata_and_pdfs import download_ptr_metadata, download_ptr_pdfs
from extract_pdf_as_csv import extract_pdf_as_csv
from clean_csv import clean_csv

# NEED TO ADD STATE / DISTRICT TO THE DATA SET

# For getting the PDF data
def download_and_install_pdf(start_year, end_year):
    download_ptr_metadata(start_year, end_year)
    download_ptr_pdfs(start_year, end_year)

# For extracting the CSV data
def extract_and_clean_csv(start_year, end_year):
    extract_pdf_as_csv(start_year,end_year)
    clean_csv(start_year, end_year)
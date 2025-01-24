# An Overview of PTR

The aim of PTR is to create an automated finance project connected to a SQL database. This database will ultimately be used to download, extract, and analyze trades made by members of the United States Congress. Due to differences in reporting formats, web scraping methods, and data structures, PTR is currently focused only on trades published by the House of Representatives. Data from the Senate will be implemented only once the House of Representatives is 100% complete.

And, for what it's worth, I'll try my best to make this process as simple as possible.

## Background Information

PTR stands for (and is named after) **"Periodic Transaction Report"**. These are financial disclosure reports which "...include information about the source, type, amount, or value of the incomes of Members, officers, certain employees of the U.S. House of Representatives and related offices, and candidates for the U.S. House of Representatives". The project's source of metadata and general information about these disclosures can be found [here](https://disclosures-clerk.house.gov/FinancialDisclosure).

## Some Disclaimers

It's worth noting that **this project has a lot of development left**. Thankfully, I'm past the most difficult challenges and many of the initial goals have been met. Most notably, **PTR requires the usage of paid [Anthropic API](https://www.anthropic.com/api) calls**. The cost of these calls tends to add up a bit. For instance, one year of data tends to cost around $45 to extract into a usable CSV format. Additionally, the increasing complexity and scope of the project has resulted in a bunch of new objectives, future optimizations, and further organization that I need to address.

As a final disclaimer, some of the scripts are incomplete. To my own relief, the data gathering and extraction (which is by far the most tedious part) is effectively finished for the House of Representatives. The script can sucessfully extract the data as a CSV file, yet some final tweaks are needed for complete reliability when interacting with the [Anthropic API](https://www.anthropic.com/api).

# Getting Everything Ready - You'll Need These

- [Python](https://www.python.org/downloads/)
- [Node.js](https://nodejs.org/en/download)
- [PostgreSQL](https://www.postgresql.org/download/) (Optional for now. Include SQL Shell and PgAdmin when installing)
- [Anthropic API](https://www.anthropic.com/api) and (by extension) a [Claude AI](https://claude.ai/login) account. This will also require entering payment information in order to use the API service.

## Python and Node.js

Install Python dependencies using [pip](https://pip.pypa.io/en/stable/).

```bash
pip install -r requirements.txt
```

Install [Node.js](https://nodejs.org/en/download) using [npm](https://docs.npmjs.com/).

```bash
npm install
```

## PostgreSQL (Optional for Now)

If not set up already, create a [PostgreSQL](https://www.postgresql.org/account/signup/) account and download/install [PostgreSQL](https://www.postgresql.org/download/).

Once [PostgreSQL](https://www.postgresql.org/download/) is set up and installed, follow these steps to set up your database:

1. Open SQL Shell (psql) and connect to the default postgres database.

```psql
Server [localhost]:
Database [postgres]:
Port [5432]:
Username [postgres]: postgres
Password for user postgres: [your PostgreSQL password created during installation]
```

2. After you're logged in, create the PTR database.

```psql
CREATE DATABASE PTR
CREATE TABLE house_trades;
```

3. Just to confirm that we're on the same page, your end result in the psql shell after logging in to a new session should be as follows.

```psql
Server: localhost (default, press Enter)
Database: PTR
Port: 5432 (default, press Enter)
Username: postgres
Password: [your PostgreSQL password created during installation]
PTR=#
```

# Getting the Data

The U.S. Congress really went out of their way to make these trades difficult to get in a clean format. So, we've got some preparation to do. It starts with retrieving some metadata and a lot of PDFs. You can download, unzpip, filter, and install the metadata to the project folder with a single function.

## Quick Start - The download_and_install_years() Function

This is what I meant when I said that many of the tedious aspects of the project are complete. This simple function will take care of every zip file, Document ID complication, file name, and pretty much every obstacle in the way of downloading the PDFs. Simply go to **main.py** (located in data_retrieval) and type the function as follows.

```python
download_and_install_years(start_year, end_year)
```

**Note: Dates prior to 2015 will not be accepted. Handwritten reports are ignored as well, so a small amount of data may be missing**. I will also develop more flexible functions for these operations once they are needed.

## Downloading the House Metadata

**If you're a bit curious and maybe even want to go through a couple more steps for getting the PDFs, follow along here**. Otherwise, I'd recommend skipping to [here](#extracting-the-data). Anyway, you can get the metadata from the [Clerk of the United States House of Representatives](https://disclosures-clerk.house.gov/FinancialDisclosure) by running the following function in **main.py** (located in data_retrieval).

```python
download_ptr_metadata(start_year, end_year)
```

This metadata includes an essential piece of information: a **Document ID** for the politician's corresponding financial disclosure. Of course, this data doesn't have trades or financial information included. There are only references (the Document ID column) to the Periodic Transaction Reports. Unfortunately, there's a minimum year of 2015, as the metadata format changes prior (Can be fixed).

Note: There is definitely a better way to access functions in main.py when they more are developed. For now, main.py is a happy place where everything is.

## Downloading the House Periodic Transaction Reports

Every Periodic Transaction Report (PTR) is in PDF format and defined by a Document ID, but there are some weird steps you have to go through to get them.

[PTRs apply to people beyond just House Representatives](#background-information), so these functions also take care of a good chunk of filtering and data organization. Maybe someone can make a relation of all these governmental figures, but we'll just stick with the House for now.

In **main.py** (located in data_retrieval), delete the download_ptr_metadata() function from earlier, type this in its replacement, and run it.

```python
download_ptr_pdfs(start_year, end_year)
```

This uses the metadata (Document IDs) to make links to House of Representative's trades **between 2015 and present** and download their corresponding PDFs.

# Extracting the Data

Here comes the part of the project that utilizes the Anthropic API for converting these PDFs into a nice CSV format. As mentioned before, congress really went out of their way to make this data accessible. So, I had to resort to AI to get them into a CSV format. I tried everything else and simply couldn't get the consistency that the AI delivers!

**Note: This portion of the project is complete (check out the files), but I have yet to update this guide.**

# Bank Statement PDF to Excel and CSV Converter

Convert your bank statement PDFs into clean, structured Excel or CSV files with ease.
This has been designed and tested on UK bank statements, but it may be compatible with other English language statements.  Please try it and let us know if it is!

## Compatible Statements
- HSBC Personal Current Accounts
- HSBC Advance Current Accounts
- HSBC Instant & Flexible Savings Accounts
- HSBC Online Bonus Saver Accounts

## Coming soon...
- HSBC Credit Cards
- HSBC Business Accounts
- Halifax Current Accounts
- Halifax Savings Accounts
- Halifax Credit Cards
- Natwest Current Accounts

## Features

- **Fast Multiple Statement Processing**: Extracts transactions from hundreds of statements in just a few minutes
- **Excel export**: Outputs combined transaction data as `.xlsx` and `.csv` files for easy analysis
- **Automated Quality Checks**: Tests to make sure all transaction values match against the movement between opening and closing statement balances
- **Data privacy**: Processes files locally; no data leaves your machine. The process can be run with your computer fully off-line

## Set-up & Usage

### Step 1 (Optional but recommended) - Install UV
We use the wonderful [Astral's uv](https://github.com/astral-sh/uv) as a package manager, as this simplifies project dependencies and environments across users, developers, and operating systems.

If you don't already have **uv** you can install it using one of the following methods:

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Or, from [PyPI](https://pypi.org/project/uv/):

```bash
# With pip.
pip install uv
```

```bash
# Or pipx.
pipx install uv
```

### Step 2 - Download or clone this repository

Either download the zip archive locally by clicking the green 'Code' button at the top of this screen and choosing the 'Download ZIP' option.

Or, if you have git installed, you can clone the repository using the below command:
    
```bash
git clone https://github.com/StillwatersTechnology/bank_statements_to_excel.git
cd bank_statements_to_excel
```

### Step 3 - Set up your environment and install dependencies

If you have uv installed, make sure you are in the bank_statements_to_excel folder and run:

```bash
uv sync
```

This should set up a virtual environment with all the dependencies and make sure the correct version of python is running within this project folder.

If you're not using uv you'll need a python version of >= 3.10.  You can create your own virtual environment and use 'pip install' to set up your environment using the requirements.txt file.
From within the bank_statements_to_excel you can run:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Download pdf's of your bank statements and place them within the 'statements' folder.  You can add as many files as you like, and there is no specific naming convention required.  The convertor will run through all the statements and compile them into single excel and .csv files.  You may want to test with a single statement initially, and review the output before running through years of statements.
Once your statement (or statements) are in the folder you can run the convertor:

If you're using uv:
```bash
uv run bstec
```

Or, without uv:
```bash
python src/bstec
```

Follow the on-screen instructions.  Each statement will be converted and you'll see messages showing the results of all the balance checks.
A statement with no transactions will be skipped.  These are usually savings accounts with no activity and no monthly interest.

Once complete, you'll be prompted to locate your Excel and CSV files in the appropriate exports folders.  It's also worth chcking the 'logs' folder as this will contain a file for each run showing the status of each statement conversion.

## Issues

If you have any problems, please check that the bank statements you are using is listed within the [Compatible Statements](#compatible-statements) list at the top of this README file.  If you are using a supported statement, please open an issue here: https://github.com/StillwatersTechnology/bank_statements_to_excel/issues

Please give as much information as possible, but be careful not to divulge any personal information such as bank account numbers or your personal address - please don't upload or attach your bank statement! 

One possible cause of failure may be a transaction type that isn't listed in 'TRANSACTION_TYPES' in the [transaction_types.py](modules/transaction_types.py) file.  If there's a transaction type on your statement that isn't listed, let us know in your issue and we'll add it.  You can also try adding it yourself to see if it solves the problem, and submit a pull request if you like.

Another possible point of failure may be overseas transactions, as these may list values in multiple currencies.  If there are any of these you can let us know the currency and the basic format of the transaction on your statement.

## Requirements

- Python 3.10+
- See [requirements.txt](requirements.txt) or [pyproject.toml](pyproject.toml) for dependencies. Alternatively, if you're using uv, you can run:

```bash
uv tree
```

## Limitations

- We only have access to our own statements for testing so there could be format or transaction types that we have missed.  Please let us know if you experience issues and we'll contact you and try to resolve the issue.
- Only supports English-language statements by default.
- If a bank makes fundamental changes to the format of their pdf statements then this will break...  but we will try to mend it!

## Export Formats Warning

As we are at a very early stage of development, it is likely that the format of the export files will change frequently. If you are consuming the exports within a database or Excel, you should bear this in mind.  We will endeavbour to keep field names the same, but additional fields may be added to exports as required.  If the version number is 0.1.* we may add additional fields within the existing fields, or re-order the fields.  Once the version number reaches 0.2.* we will only tag new fields on to the end of existing fields and will not re-order. Once we reach version 1.0.0 the existing export formats and fields will remain fixed until the next major release. 


## Contributing

### Testing
If you have am account listed in the [Compatible Statements](#compatible-statements), please give this project a try and let us know how you get on. Here are areas we're keen to get your thoughts on...
* Did you manage to install and run, and was there anything we could make easier?
* Are you happy with the command-line interface, or would you prefer a graphical user interface?
* In our tests we processed 200 of our own statements in around 150 seconds.  Are you getting the same level of performance?
* What information, if any, is on your bank statements that we're not currently including in the excel and csv export files?
* Do you have any other suggestions for improvements?

Please raise issues for any feedback - thank you!

### Development
After the initial round of testing and feedback we'll publish a roadmap of enhancements and features, and this should assist anyone wishing to kindly contribute.  There may be a significant change in the structure of the project to facilitate the expansion of bank and statement coverage.  Initially it's thought this will involve a method of identifying the bank and account type from the raw pdf file, and then referencing a configuration file of specific markers to identify key blocks of data.

Pull requests and issue reports are welcome!

## License

- MIT license <https://opensource.org/licenses/MIT>

---

*This project is not affiliated with any bank. Use at your own risk.*

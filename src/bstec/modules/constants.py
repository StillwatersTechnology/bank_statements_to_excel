import pathlib

from .transaction_types import TRANSACTION_TYPES  # noqa: F401

ACCOUNT_INFO_HEADER = "Account Name Sortcode Account Number Sheet Number"  # Header for account info line
# TRANSACTION_HEADER = "Date Payment type and details Paidout Paidin Balance"  # Header for transaction lines
OPENING_BALANCE_LINE = "Opening Balance"  # opening balance line
PAYMENTS_IN_LINE = "Payments In"  # payments in line
PAYMENTS_OUT_LINE = "Payments Out"  # payments out line
CLOSING_BALANCE_LINE = "Closing Balance"  # closing balance line
BBF_LINE = "BALANCE BROUGHT FORWARD"  # balance brought forward line
BCF_LINE = "BALANCE CARRIED FORWARD"  # balance carried forward line
DATE_FORMAT = "%d %b %y"
DATE_FORMAT_DESC = "%d %B %Y"
CURRENCY_PATTERN = r"(^\d+)(\.{1})(\d{2})$"
POLARITY_SWAPS_MAX_TRIES = 5000
SPLITTER_LENGTH = 50

SPLITTER = "-" * SPLITTER_LENGTH  # A string of dashes used as a separator in reports
SPLITTER_WITH_NEWLINE = SPLITTER + "\n"  # A string of dashes with a newline for better readability

# current working directory
CURRENT_WORKING_DIRECTORY = pathlib.Path().absolute()
STATEMENT_DIRECTORY = CURRENT_WORKING_DIRECTORY / "statements"
EXPORT_CSV_DIRECTORY = CURRENT_WORKING_DIRECTORY / "exports_csv"
EXPORT_EXCEL_DIRECTORY = CURRENT_WORKING_DIRECTORY / "exports_excel"
LOG_DIRECTORY = CURRENT_WORKING_DIRECTORY / "logs"
TEST_DIRECTORY = CURRENT_WORKING_DIRECTORY / "tests"
NOTEBOOK_DIRECTORY = CURRENT_WORKING_DIRECTORY / "notebooks"

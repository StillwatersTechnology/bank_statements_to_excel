from .transaction_types import TRANSACTION_TYPES  # noqa: F401

ACCOUNT_INFO_HEADER = (
    "Account Name Sortcode Account Number Sheet Number"  # Header for account info line
)
# TRANSACTION_HEADER = "Date Payment type and details Paidout Paidin Balance"  # Header for transaction lines
OPENING_BALANCE_LINE = "OpeningBalance"  # opening balance line
PAYMENTS_IN_LINE = "Payments In"  # payments in line
PAYMENTS_OUT_LINE = "Payments Out"  # payments out line
CLOSING_BALANCE_LINE = "ClosingBalance"  # closing balance line
BBF_LINE = "BALANCEBROUGHTFORWARD"  # balance brought forward line
BCF_LINE = "BALANCECARRIEDFORWARD"  # balance carried forward line
DATE_FORMAT = "%d %b %y"
DATE_FORMAT_DESC = "%d %B %Y"
CURRENCY_PATTERN = r"(^\d+)(\.{1})(\d{2})$"
POLARITY_SWAPS_MAX_TRIES = 5000
SPLITTER_LENGTH = 50

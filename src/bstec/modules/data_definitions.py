from dataclasses import dataclass
from datetime import date
from typing import NamedTuple


class ExportColumns(NamedTuple):
    id_transaction: str
    id_statement: str
    filename: str
    account_name: str
    account: str
    statement_date: str
    page_number: int
    sheet_number: int
    transaction_number: int
    date_transaction: date
    type_transaction: str
    credit_debit: str
    description: str
    description_long: str
    opening_balance: float
    value: float
    closing_balance: float


class ExportReportColumns(NamedTuple):
    id_statement: str
    filename: str
    account_name: str
    account: str
    statement_date: str
    opening_balance: float
    closing_balance: float
    skipped: bool = False  # Indicates whether the statement was skipped due to the absence of transactions


@dataclass
class ConsistencyCheckResult:
    # Dummy values used to force a failure in consistency checks
    id_statement: str
    account: str
    statement_date: date
    movement_statement: float = 12345.67  # Represents the overall movement in the statement
    movement_transaction_blocks: float = 23456.78  # Represents the movement in transaction blocks
    movement_day_blocks: float = 34567.89  # Represents the movement in day blocks
    movement_transactions: float = 45678.90  # Represents the movement in individual transactions
    message: str = "No issues detected."  # Default message indicating the transaction passed checks or failed checks
    passed_checks: bool = False  # Indicates if the transaction passed all consistency checks


@dataclass
class ExportResult:
    is_export_successful: bool = True
    is_log_successful: bool = True
    export_excel: str = ""
    log_excel: str = ""
    export_csv: str = ""
    log_csv: str = ""
    message: str = "Default message"  # Represents the status or result of the export operation
    has_error: bool = False
    error_message: str = ""

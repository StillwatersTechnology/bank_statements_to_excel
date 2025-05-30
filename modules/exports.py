import os
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

import pandas as pd

from .classes import Statement


@dataclass
class ExportColumns:
    id_transaction: UUID
    id_statement: UUID
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


data_instances: list[ExportColumns] = []


# Prepare the data for export
def prepare_export_data(stmt: Statement):
    """
    Prepares and appends export data instances from a given Statement object.

    Iterates through each page and its transaction blocks within the statement,
    extracting transaction details and constructing ExportColumns instances for each transaction.
    The resulting data instances are appended to the global or external `data_instances` list.

    Args:
        stmt (Statement): The statement object containing pages and transaction data to be exported.

    Note:
        - Assumes `data_instances` and `ExportColumns` are defined in the outer scope.
        - Page and transaction numbers are incremented by 1 to convert from zero-based to one-based indexing.
    """
    for page in stmt.pages:
        if page.transaction_block is not None:
            for day_block in page.transaction_block.day_blocks:
                for transaction in day_block.transactions:
                    data_instances.append(
                        ExportColumns(
                            id_statement=stmt.id,
                            filename=stmt.filename,
                            account_name=stmt.account_name,
                            account=stmt.sort_code + " " + stmt.account_number,
                            statement_date=stmt.statement_date_desc,
                            page_number=page.page_number
                            + 1,  # page number is zero indexed
                            sheet_number=page.sheet_number,
                            id_transaction=transaction.id,
                            date_transaction=transaction.date_transaction,
                            type_transaction=transaction.type_transaction,
                            credit_debit="Credit" if transaction.value > 0 else "Debit",
                            description=transaction.description,
                            description_long=transaction.description_long,
                            opening_balance=transaction.opening_balance,
                            value=transaction.value,
                            closing_balance=transaction.closing_balance,
                            transaction_number=transaction.transaction_number
                            + 1,  # transaction number is zero indexed
                        )
                    )


# Export the prepared data
def export_data():
    """
    Exports the current data instances to CSV and Excel files in dedicated export folders.

    - Creates 'exports_csv' and 'exports_excel' directories if they do not exist.
    - If there are no data instances, prints a message and returns.
    - Otherwise, combines the data instances into a DataFrame and exports them:
        - As a CSV file in the 'exports_csv' folder.
        - As an Excel file in the 'exports_excel' folder.
    - Filenames include a timestamp to ensure uniqueness.
    - Prints messages indicating the export status and file locations.

    Returns:
        str: The timestamp used in the exported filenames, or None if no data was exported.
    """
    # Export the data to CSV and Excel files
    if not os.path.exists("exports_csv"):
        os.makedirs("exports_csv")
    if not os.path.exists("exports_excel"):
        os.makedirs("exports_excel")
    # Export to CSV and Excel
    if len(data_instances) == 0:
        print("No data to export")
        return
    else:
        print(
            "Combining statements and exporting to CSV and Excel files in the relevant export folders"
        )
        current_time: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        df: pd.DataFrame = pd.DataFrame(data_instances)
        df.to_csv(f"exports_csv/bank_transactions_{current_time}.csv", index=False)
        df.to_excel(  # type: ignore
            excel_writer=f"exports_excel/bank_transactions_{current_time}.xlsx",
            index=False,
        )
        print(
            f"Exported transactions to CSV and Excel files with timestamp: {current_time}. You can find them in the 'exports_csv' and 'exports_excel' folders."
        )
    return current_time

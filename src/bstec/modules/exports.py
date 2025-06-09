from datetime import datetime

# import pandas as pd
import polars as pl

from .classes import Statement
from .constants import EXPORT_CSV_DIRECTORY, EXPORT_EXCEL_DIRECTORY, LOG_DIRECTORY
from .data_definitions import ExportColumns, ExportReportColumns, ExportResult

export_report: list[ExportReportColumns] = []

data_instances: list[ExportColumns] = []


def update_export_report(stmt: Statement):
    """
    Updates the export report with the details of the given statement.

    Appends an ExportReportColumns instance to the global export_report list,
    capturing the statement's ID, filename, account name, account details,
    statement date, opening balance, closing balance, and whether it was skipped.

    Args:
        stmt (Statement): The statement object containing the details to be recorded.
        skipped (bool): Indicates if the statement was skipped due to no transactions.
    """
    export_report.append(
        ExportReportColumns(
            id_statement=stmt.id,
            filename=stmt.filename,
            account_name=stmt.account_name,
            account=stmt.sort_code + " " + stmt.account_number,
            statement_date=stmt.statement_date_desc,
            opening_balance=stmt.opening_balance,
            closing_balance=stmt.closing_balance,
            skipped=stmt.skipped,
        )
    )


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
                            page_number=page.page_number + 1,  # page number is zero indexed
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
                            transaction_number=transaction.transaction_number + 1,  # transaction number is zero indexed
                        )
                    )


# Export the prepared data
def export_data(excel: bool = True, csv: bool = True) -> ExportResult:
    """
    Exports the current data instances to CSV and Excel files in dedicated export folders.

    - If there are no data instances, prints a message and returns.
    - Otherwise, combines the data instances into a DataFrame and exports them:
        - As a CSV file in the 'exports_csv' folder.
        - As an Excel file in the 'exports_excel' folder.
    - Filenames include a timestamp to ensure uniqueness.
    - writes messages to the result variable indicating the export status and file locations.

    Returns:
        ExportResult: An instance containing the results of the export operation,
        including file paths, success status, and any error messages.
    """
    result: ExportResult = ExportResult()

    # Export to CSV and Excel
    if len(data_instances) == 0:
        result.message = "No data to export"
        result.is_export_successful = False
    else:
        try:
            current_time: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            df: pl.DataFrame = pl.DataFrame(data_instances)
            if excel:
                export_file = f"{EXPORT_EXCEL_DIRECTORY}/bank_transactions_{current_time}.xlsx"
                df.write_excel(export_file)
                result.export_excel = export_file
                result.message += f"Exported data to Excel file: {export_file}\n"
            if csv:
                export_file = f"{EXPORT_CSV_DIRECTORY}/bank_transactions_{current_time}.csv"
                df.write_csv(export_file)
                result.export_csv = export_file
                result.message += f"Exported data to CSV file: {export_file}\n"
            # Generate report
            export_report_data(current_time, excel, csv, result)
        except Exception as e:
            print(df)
            result.has_error = True
            result.error_message = str(e)
            result.message += "Error exporting data"
            result.is_export_successful = False
    return result


def export_report_data(current_time, excel, csv, result) -> ExportResult:
    """
    Generates a report of the export process, including exporting the log to Excel and CSV files.
    This function creates a DataFrame from the global export_report list and attempts to write it to
    both Excel and CSV files in the specified log directory.
    Args:
        current_time (str): The current timestamp used for naming the export files.
        excel (bool): Flag indicating whether to export the report to an Excel file.
        csv (bool): Flag indicating whether to export the report to a CSV file.
        result (ExportResult): The result object to store the export status and file paths.
    Returns:
        ExportResult: The updated result object containing the export status and file paths.
    """
    # Report generation
    df = pl.DataFrame(export_report)
    if excel:
        try:
            log_excel = f"{LOG_DIRECTORY}/log_excel_{current_time}.xlsx"
            df.write_excel(log_excel)
            result.log_excel = log_excel
            result.message += f"Exported log to Excel file: {log_excel}\n"
        except Exception as e:
            result.is_log_successful = False
            result.error_message += f"Error exporting log to Excel: {e}\n"
    if csv:
        try:
            log_csv = f"{LOG_DIRECTORY}/log_csv_{current_time}.csv"
            df.write_csv(log_csv)
            result.log_csv = log_csv
            result.error_message += f"Exported log to CSV file: {log_csv}\n"
        except Exception as e:
            result.is_log_successful = False
            result.error_message += f"Error exporting log to CSV: {e}\n"
    return result

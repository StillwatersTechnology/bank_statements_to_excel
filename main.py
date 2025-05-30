import os
from os import listdir

import pandas as pd

from modules.classes import Statement
from modules.constants import (
    SPLITTER_LENGTH,
)
from modules.exports import export_data, prepare_export_data

report: list[tuple[str, str, str, float | None, float | None, bool]] = []


def main():
    """
    Main function for the bank statement parser application.

    This function guides the user through the process of parsing bank statement PDF files located in the 'statements' directory.
    It performs the following steps:
    1. Displays introductory information and instructions to the user.
    2. Prompts the user to confirm readiness to process files, with options to proceed, review instructions again, or exit.
    3. Lists and filters PDF files in the 'statements' directory, ensuring only valid files are processed.
    4. For each PDF file:
        - Processes the statement and checks if it contains transactions.
        - Runs a series of tests to validate the statement data.
        - Prepares data for export if the statement passes all tests.
        - Records processing results for reporting.
    5. After processing all files:
        - Exports the processed data to CSV and Excel files in the 'logs' directory, timestamped with the current date and time.
        - Generates a summary report of all processed statements.
        - Informs the user about the location and names of the generated log files.

    Raises:
        Exception: If a statement fails the validation tests.
    """
    print_splitter()
    print("Welcome to the bank statement parser")
    print_splitter()
    print(
        "This program will parse your bank statement and extract the relevant transactions"
    )
    print("It will also run a series of tests to ensure the data is correct")
    print("Please make sure your bank statements are in the 'statements' directory")
    print("The program will process all PDF files in the directory")
    print(
        "The program will also create a CSV file and an Excel file with the extracted data"
    )
    print("The files will be saved in the relevant 'exports' directories")
    print_splitter()

    while True:
        user_input = (
            input("Are you ready to process the files? (yes/no/exit): ").strip().lower()
        )
        if user_input == "yes":
            files = listdir(
                "statements"
            )  # List of PDF files in the statements directory
            # Filter out non-PDF files
            for filename in files:
                if not filename.endswith(".pdf"):
                    files.remove(filename)
            if len(files) == 0:
                print("No PDF files found in the statements directory.")
                print("Please add some PDF files and try again.")
                return
            print(f"Found {len(files)} PDF files in the statements directory.")
            break
        elif user_input == "no":
            print(
                "Please make sure your bank statements are in the 'statements' directory."
            )
            print("The program will process all PDF files in the directory.")
            print(
                "The program will also create a CSV file and an Excel file with the extracted data."
            )
            print("The files will be saved in the relevant 'exports' directories.")
        elif user_input == "exit":
            return

    for filename in files:
        print_splitter()
        print("processing... ", filename)
        stmt = Statement(f"statements/{filename}")

        if stmt.skipped:  # if the statement is skipped, don't bother testing it
            print(
                f"Statement {filename} for account: {stmt.account_number} has been skipped as it doesn't appear to contain any transactions. Please check the file for errors."
            )
        else:
            test_results = tests(stmt)
            if test_results:
                # statements.append(stmt)
                print(
                    f"Statement {filename} for account: {stmt.account_number} passed all tests."
                )
                prepare_export_data(stmt)
            else:
                raise Exception(
                    f"Statement {stmt.id} failed tests. This statement dated {stmt.statement_date_desc} is invalid."
                )
        report.append(  # add the statement to the report
            (
                filename,
                stmt.account_number,
                stmt.sort_code,
                stmt.opening_balance,
                stmt.closing_balance,
                stmt.skipped,
            )
        )
    print_splitter()
    print("All statements processed.")
    # Create CSV and Excel files
    current_time = export_data()
    print_splitter()
    # Report generation
    if not os.path.exists("logs"):
        os.makedirs("logs")
    df = pd.DataFrame(
        report,
        columns=[
            "Filename",
            "Account Number",
            "Sort Code",
            "Opening Balance",
            "Closing Balance",
            "Skipped",
        ],
    )
    df.to_csv(f"logs/log_csv_{current_time}.csv", index=False)
    df.to_excel(  # type: ignore
        excel_writer=f"logs/log_excel_{current_time}.xlsx",
        index=False,
    )
    print(
        f"Please check the logs!: CSV and Excel files created in the logs directory with the current date and time: {current_time}\n"
        f"The CSV file is named 'log_csv_{current_time}.csv' and the Excel file is named 'log_excel_{current_time}.xlsx'\n"
        f"The number of files processed should match the number of files in the statements directory.  A file may be skipped if it doesn't contain any transactions."
    )
    print_splitter()


def tests(statement: Statement) -> bool:
    """
    Performs a series of consistency checks on the balance movements within a bank statement.

    This function calculates and compares the following:
    - The overall movement in the statement (closing_balance - opening_balance).
    - The sum of movements in each page's transaction block.
    - The cumulative movement across all day blocks within all transaction blocks.
    - The total value of all individual transactions.

    It prints the calculated values and checks if they all match (rounded to 2 decimal places).
    If all values match, it prints a success message and returns True.
    Otherwise, it prints a failure message and returns False.

    Args:
        statement (Statement): The bank statement object containing pages, balances, and transactions.

    Returns:
        bool: True if all calculated movements match, False otherwise.
    """
    # define statement movement
    movement_statement: float = -99999999.23  # dummy values should force a mis-match
    movement_transaction_blocks: float = -55555555.34
    movement_days: float = -34343434.56
    movement_transactions: float = 12341234.87
    if statement.closing_balance is not None and statement.opening_balance is not None:
        movement_statement = statement.closing_balance - statement.opening_balance
    # pages movement
    movement_transaction_blocks = sum(
        page.transaction_block.closing_balance - page.transaction_block.opening_balance
        for page in statement.pages
        if page.transaction_block is not None
        and page.transaction_block.closing_balance is not None
        and page.transaction_block.opening_balance is not None
    )
    # the cumulative movement of block of days
    movement_days = sum(
        sum(
            day_block.closing_balance - day_block.opening_balance
            for day_block in page.transaction_block.day_blocks
            if day_block.closing_balance is not None
            and day_block.opening_balance is not None
        )
        for page in statement.pages
        if page.transaction_block is not None
    )
    # the total value of all transactions
    movement_transactions = sum(
        sum(
            sum(transaction.value for transaction in day_block.transactions)
            for day_block in page.transaction_block.day_blocks
        )
        for page in statement.pages
        if page.transaction_block is not None
    )
    print_splitter()
    print("TEST RESULTS - balance movements")
    print("Statement: ", round(movement_statement, 2))
    print("Page Transaction Blocks: ", round(movement_transaction_blocks, 2))
    print("Blocks of daily transactions: ", round(movement_days, 2))
    print("All individual transactions: ", round(movement_transactions, 2))

    if (
        round(movement_statement, 2)
        == round(movement_transaction_blocks, 2)
        == round(movement_days, 2)
        == round(movement_transactions, 2)
    ):
        print("SUCCESS! Statement balance checks are all GOOD")
        return True
    else:
        print(
            "FAILURE! Statement balance checks do not all match - please check the statement and re-try"
        )
        return False


def print_splitter():
    print()
    print(f"{''.join(['-' for _ in range(SPLITTER_LENGTH)])}")
    print()


if __name__ == "__main__":
    main()
    # Run the main function to process the bank statements

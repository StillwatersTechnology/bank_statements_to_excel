from os import listdir
from time import perf_counter

from bstec.modules import (
    SPLITTER,
    STATEMENT_DIRECTORY,
    Statement,
    consistency_checks,
    export_data,
    export_report,
    prepare_export_data,
    update_export_report,
)


def main(quiet: bool = False) -> None:
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
    if not quiet:
        print_splitter()
        print("Welcome to the bank statement parser")
        print_splitter()
        print("This program will parse your bank statement and extract the relevant transactions")
        print("It will also run a series of tests to ensure the data is correct")
        print("Please make sure your bank statements are in the 'statements' directory")
        print("The program will process all PDF files in the directory")
        print("The program will also create a CSV file and an Excel file with the extracted data")
        print("The files will be saved in the relevant 'exports' directories")
        print_splitter()

    while True:
        if not quiet:
            user_input = input("Are you ready to process the files? (yes/no/exit): ").strip().lower()
        else:
            user_input = "yes"
        if user_input == "yes":
            timer_start = perf_counter()  # Start the timer
            files = listdir(STATEMENT_DIRECTORY)  # List of PDF files in the statements directory
            # Filter out non-PDF files using a list comprehension
            files = [filename for filename in files if filename.endswith(".pdf")]
            if len(files) == 0:
                print("No PDF files found in the statements directory.")
                print("Please add some PDF files and try again.")
                return
            print(f"Found {len(files)} PDF files in the statements directory.")
            break
        elif user_input == "no":
            print("Please make sure your bank statements are in the 'statements' directory.")
            print("The program will process all PDF files in the directory.")
            print("The program will also create a CSV file and an Excel file with the extracted data.")
            print("The files will be saved in the relevant 'exports' directories.")
        elif user_input == "exit":
            return

    for filename in files:
        if not quiet:
            print_splitter()
            print("processing... ", filename)
        stmt = Statement(f"{STATEMENT_DIRECTORY}/{filename}")
        if not quiet:
            print(stmt)

        if stmt.skipped:  # If the statement has been skipped, it means it either has no pages or no transactions
            print(
                f"Statement {filename} for account: {stmt.account_number} has been skipped as it doesn't contain any transactions."
                f" Please check the file for errors."
            )
        else:
            check_results = consistency_checks(stmt)
            if not quiet:
                print(check_results.message)
            if check_results.passed_checks:
                prepare_export_data(stmt)
            else:
                raise Exception(f"Statement {stmt.id} failed tests. The statement dated {stmt.statement_date_desc} is invalid.")
        update_export_report(stmt)  # update the export report with the statement data
    if not quiet:
        print_splitter()
        print("All statements processed.")
    # Create CSV and Excel files
    export_info = export_data(excel=True, csv=True)
    if not quiet:
        print_splitter()
        print(export_info.message)
    if not export_info.is_export_successful:
        print(export_info.error_message)
    else:
        timer_end = perf_counter()  # End the timer
        elapsed_time = timer_end - timer_start
        print(f"{len(export_report)} statements completed and exported in {elapsed_time:.2f} seconds")


def print_splitter():
    print()
    print(f"{SPLITTER}")
    print()

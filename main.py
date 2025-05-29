import os
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from os import listdir
from random import randint
from typing import Union
from uuid import UUID, uuid4

import pandas as pd
from pdfplumber import open as pdf_open

ACCOUNT_INFO_HEADER = (
    "Account Name Sortcode Account Number Sheet Number"  # Header for account info line
)
TRANSACTION_HEADER = "Date Payment type and details Paidout Paidin Balance"  # Header for transaction lines
OPENING_BALANCE_LINE = "OpeningBalance"  # opening balance line
PAYMENTS_IN_LINE = "Payments In"  # payments in line
PAYMENTS_OUT_LINE = "Payments Out"  # payments out line
CLOSING_BALANCE_LINE = "ClosingBalance"  # closing balance line
BBF_LINE = "BALANCEBROUGHTFORWARD"  # balance brought forward line
BCF_LINE = "BALANCECARRIEDFORWARD"  # balance carried forward line
DATE_FORMAT = "%d %b %y"
DATE_FORMAT_DESC = "%d %B %Y"
CURRENCY_PATTERN = r"(^\d+)(\.{1})(\d{2})$"
TRANSACTION_TYPES = [
    ("BP", "Bill Payment"),
    ("VIS", "Card Online"),
    (")))", "Card In Person"),
    ("DD", "Direct Debit"),
    ("ATM", "Cash Withdrawal"),
    ("CR", "Credit"),
    ("SO", "Standing Order"),
    ("DR", "Debit"),
    ("TFR", "Transfer"),
]
POLARITY_SWAPS_MAX_TRIES = 5000
SPLITTER_LENGTH = 50
date_log: list[
    dict[str, Union[UUID, int, date]]
] = []  # a list to hold the dates by statment and sheet number, in order to reduce the risk of duplication and return the previous date if a sheet transaction block begins without one
report: list[tuple[str, str, str, float | None, float | None, bool]] = []


def main():
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


class Statement:
    """
    Represents a bank statement extracted from a PDF file.

    Attributes:
        id (UUID): Unique identifier for the statement.
        filename (str): Path to the PDF file containing the statement.
        pages (list[Page]): List of Page objects representing the pages of the statement.
        sort_code (str): Bank sort code extracted from the statement.
        account_number (str): Bank account number extracted from the statement.
        account_name (str): Account holder's name extracted from the statement.
        statement_date_from (date | None): Start date of the statement period.
        statement_date_to (date | None): End date of the statement period.
        opening_balance (float | None): Opening balance for the statement period.
        closing_balance (float | None): Closing balance for the statement period.
        payments_in (float | None): Total payments in during the statement period.
        payments_out (float | None): Total payments out during the statement period.
        statement_date_desc (str): Human-readable description of the statement period.

    Methods:
        __init__(filename: str):
            Initializes a Statement object, extracts text, account info, balances, payments, and statement dates.

        _get_statement_dates():
            Determines the start and end dates of the statement period from transaction blocks.

        _extract_blalance_and_payment_info():
            Extracts opening/closing balances and payments in/out from the first page of the statement.

        _extract_account_info():
            Extracts account name, sort code, and account number from the statement.

        _extract_text():
            Reads the PDF file and populates the pages attribute with Page objects.
    """

    def __init__(self, filename: str):
        self.id: UUID = uuid4()
        self.filename: str = filename
        self.pages: list[Page] = []
        self.sort_code: str = "<missing sort code>"
        self.account_number: str = "<missing account number>"
        self.account_name: str = "<missing account name>"
        self.statement_date_from: date | None = None
        self.statement_date_to: date | None = None
        self.opening_balance: float | None = None
        self.closing_balance: float | None = None
        self.payments_in: float | None = None
        self.payments_out: float | None = None
        self.skipped: bool = False
        self._extract_text()
        self._extract_account_info()
        self._extract_blalance_and_payment_info()
        self._get_statement_dates()
        self._check_for_skipped()
        self.statement_date_desc: str = (
            "<file skipped>"
            if self.skipped
            else f"{self.statement_date_from:{DATE_FORMAT_DESC}} to {self.statement_date_to:{DATE_FORMAT_DESC}}"
        )  # human-readable description of the statement period

    def _check_for_skipped(self):
        """
        Check if the statement contains pages and transaction blocks.
        If not, flag the statement as skipped.
        """
        if len(self.pages) == 0:
            self.skipped = True
        else:
            if not any(page.transaction_block for page in self.pages):
                # if there are no transaction blocks, skip the statement
                self.skipped = True

    def _get_statement_dates(self):
        start_date = next(
            (
                page.transaction_block.date_bbf
                for page in self.pages
                if page.transaction_block and page.transaction_block.is_first
            ),
            None,
        )
        end_date = next(
            (
                page.transaction_block.date_bcf
                for page in self.pages
                if page.transaction_block and page.transaction_block.is_last
            ),
            None,
        )
        if start_date and end_date:
            self.statement_date_from = start_date + timedelta(days=1)
            self.statement_date_to = end_date

    def _extract_blalance_and_payment_info(self):
        for line in self.pages[0].lines:
            if OPENING_BALANCE_LINE in line.text:
                debit_flag: bool = False
                if line.text.split()[-1] == "D":
                    debit_flag = True
                    line.text = line.text.replace("D", "")
                self.opening_balance = float(
                    str(line.text.split()[-1])
                    .replace(",", "")
                    .replace("£", "")
                    .replace("$", "")
                    .replace("EUR", "")
                )
                if debit_flag:
                    self.opening_balance = self.opening_balance * -1
            elif PAYMENTS_IN_LINE in line.text:
                self.payments_in = float(
                    str(line.text.split()[-1])
                    .replace(",", "")
                    .replace("£", "")
                    .replace("$", "")
                    .replace("EUR", "")
                )
            elif PAYMENTS_OUT_LINE in line.text:
                self.payments_out = float(
                    str(line.text.split()[-1])
                    .replace(",", "")
                    .replace("£", "")
                    .replace("$", "")
                    .replace("EUR", "")
                )
            elif CLOSING_BALANCE_LINE in line.text:
                debit_flag: bool = False
                if line.text.split()[-1] == "D":
                    debit_flag = True
                    line.text = line.text.replace("D", "")
                self.closing_balance = float(
                    str(line.text.split()[-1])
                    .replace(",", "")
                    .replace("£", "")
                    .replace("$", "")
                    .replace("EUR", "")
                )
                if debit_flag:
                    self.closing_balance = self.closing_balance * -1

    def _extract_account_info(self):
        account_info_line = next(
            (
                line.line_number_page
                for line in self.pages[0].lines
                if ACCOUNT_INFO_HEADER in line.text
            ),
            None,
        )
        if account_info_line is not None:
            account_info = self.pages[0].lines[account_info_line + 1].text
            # print(account_info)
            account_info_parts = account_info.split()
            # print(account_info_parts)
            if len(account_info_parts) >= 4:
                # remove the final part of the line which is the sheet number
                account_info_parts.pop()
                # the final part of the line is the account number
                self.account_number = account_info_parts.pop()
                # the second to last part of the line is the sort code
                self.sort_code = account_info_parts.pop()
                # the rest of the line is the account name
                self.account_name = " ".join(account_info_parts)

    def _extract_text(self):
        with pdf_open(self.filename) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    self.pages.append(
                        Page(page.page_number - 1, text, self.id)
                    )  # page number reduced by 1 to make it zero indexed


class Page:
    """
    Represents a page within a statement, containing text, metadata, and extracted information.

    Attributes:
        id (UUID): Unique identifier for the page.
        id_statement (UUID): Identifier of the associated statement.
        page_number (int): The page number within the statement.
        text (str): The raw text content of the page.
        sheet_number (int): The extracted sheet number (default -1 if not found).
        lines (list[Line]): List of Line objects extracted from the page text.
        transaction_block (TransactionBlock | None): Extracted transaction block, if present.

    Methods:
        _get_transaction_block():
            Attempts to extract a TransactionBlock from the page and assigns it to transaction_block if found.

        _extract_lines():
            Splits the page text into lines and populates the lines attribute with Line objects.

        _extract_sheet_number():
            Searches for the account info header in the lines and extracts the sheet number from the corresponding line.
    """

    def __init__(self, page_number: int, text: str, id_statement: UUID):  # type: ignore
        self.id: UUID = uuid4()
        self.id_statement: UUID = id_statement
        self.page_number: int = page_number
        self.text: str = text
        self.sheet_number: int = -1  # dummy sheet number
        self.lines: list[Line] = []
        self.transaction_block: TransactionBlock | None = None
        self._extract_lines()
        self._extract_sheet_number()
        self._get_transaction_block()

    def _get_transaction_block(self):
        tb = TransactionBlock(self)
        if tb and tb.lines and len(tb.lines) > 0:
            self.transaction_block = tb

    def _extract_lines(self):
        line_number = 0
        for line in self.text.split("\n"):
            if line.strip():
                self.lines.append(Line(text=line, line_number_page=line_number))
                line_number += 1

    def _extract_sheet_number(self):
        account_info_line = next(
            (
                line.line_number_page
                for line in self.lines
                if ACCOUNT_INFO_HEADER in line.text
            ),
            None,
        )
        if account_info_line is not None:
            account_info = self.lines[
                account_info_line + 1
            ].text  # info is 1 line beneath the header
            account_info_parts = account_info.split()
            if len(account_info_parts) >= 4:
                # the final part of the line is the sheet number
                self.sheet_number = int(account_info_parts.pop())


class Line:
    """
    Represents a line from a banking statement, extracting and storing relevant transaction information.

    Attributes:
        id (UUID): Unique identifier for the line.
        line_number_page (int): The line number on the page.
        line_number_transaction_block (int | None): The line number within a transaction block.
        line_number_day_block (int | None): The line number within a day block.
        line_number_transaction (int | None): The line number within a transaction.
        text (str): The raw text of the line.
        date (date | None): The date extracted from the line, if present.
        type_transaction (str | None): The type of transaction, if identified.
        balance (float | None): The balance after the transaction, if present.
        value_transaction (float | None): The value of the transaction, if present.
        text_transaction (str): The narrative or description of the transaction.

    Methods:
        __init__(text: str, line_number_page: int):
            Initializes a Line instance and extracts information from the text.

        __repr__():
            Returns a string representation of the Line instance, including key extracted fields.

        _extract_info():
            Parses the line text to extract date, transaction type, value, balance, and narrative.
    """

    def __init__(self, text: str, line_number_page: int):
        self.id: UUID = uuid4()
        self.line_number_page: int = line_number_page
        self.line_number_transaction_block: int | None = None
        self.line_number_day_block: int | None = None
        self.line_number_transaction: int | None = None
        self.text: str = text
        self.date: date | None = None
        self.type_transaction: str | None = None
        self.balance: float | None = None
        self.value_transaction: float | None = None
        self.text_transaction: str = ""
        self._extract_info()

    def __repr__(self):
        return f"{self.line_number_transaction_block}: {self.text} --- date: {self.date}, type_transaction: {self.type_transaction}, text_transaction: {self.text_transaction}, value_transaction: {self.value_transaction}, balance: {self.balance}, line_number_transaction: {self.line_number_transaction}"

    def _extract_info(self):
        text_parts = self.text.split()
        debit_flag: bool = False
        if text_parts[-1] == "D":
            del text_parts[-1]  # remove the D from the end of the line
            debit_flag = True
        tp_length = len(text_parts)
        # check for date
        if tp_length >= 3:
            possible_date = " ".join(text_parts[:3])
            try:
                date = make_date(possible_date)
            except Exception:
                date = None
            if date is not None:
                self.date = date
        # check for opening balance
        if tp_length >= 2:
            text_last = str(text_parts[tp_length - 1]).strip().replace(",", "", 1)
            text_ntl = str(text_parts[tp_length - 2]).strip().replace(",", "", 1)
            float_ntl = None
            float_last = None
            if re.findall(CURRENCY_PATTERN, text_last):
                float_last = float(text_last)
                if debit_flag:
                    float_last = float_last * -1
            else:
                float_last = None
            if float_last is not None:
                if re.findall(CURRENCY_PATTERN, text_ntl):
                    float_ntl = float(text_ntl)
                else:
                    float_ntl = None
            if float_last is not None and float_ntl is not None:
                self.balance = float_last
                self.value_transaction = float_ntl
            elif float_last is not None:
                self.value_transaction = float_last
            # look for a transaction type
            valid_types = [type[0] for type in TRANSACTION_TYPES]
            possible_type_transaction = None
            if self.date is not None and len(text_parts) > 3:
                possible_type_transaction = text_parts[3]
            elif len(text_parts) > 0:
                possible_type_transaction = text_parts[0]
            if (
                possible_type_transaction is not None
                and possible_type_transaction in valid_types
            ):
                self.type_transaction = possible_type_transaction

        # set the narrative
        start_point = 0
        end_point = tp_length
        if self.date is not None:
            start_point += 3
        if self.type_transaction is not None:
            start_point += 1
        if debit_flag:
            end_point -= 1
        if self.balance is not None:
            end_point -= 1
        if self.value_transaction is not None:
            end_point -= 1
        try:
            self.text_transaction = " ".join(text_parts[start_point:end_point])
        except Exception:
            self.text_transaction = "<no transaction text>"


class TransactionBlock:
    """
    Represents a block of transactions within a page of a bank statement.

    A TransactionBlock is responsible for extracting and organizing transaction lines
    from a given Page, determining opening and closing balances, and grouping lines
    into DayBlocks based on transaction dates.

    Attributes:
        id (UUID): Unique identifier for the transaction block.
        id_page (UUID): Unique identifier for the associated Page.
        page (Page): The Page object this transaction block belongs to.
        page_number (int): The page number within the statement.
        opening_balance (float | None): The opening balance for this transaction block.
        closing_balance (float | None): The closing balance for this transaction block.
        start_line (int | None): The starting line number of the transaction block within the page.
        end_line (int | None): The ending line number of the transaction block within the page.
        is_first (bool): Indicates if this is the first transaction block on the statement.
        is_last (bool): Indicates if this is the last transaction block on the statement.
        date_bbf (date | None): Date of the balance brought forward (if first transaction block).
        date_bcf (date | None): Date of the balance carried forward (if last transaction block).
        lines (list[Line] | None): List of Line objects belonging to this transaction block.
        day_blocks (list[DayBlock]): List of DayBlock objects grouped by transaction date.

    Methods:
        __repr__():
            Returns a string representation of the TransactionBlock.

        _extract_day_blocks():
            Groups transaction lines into DayBlocks based on transaction dates and balances.

        _get_lines():
            Extracts the relevant lines from the Page for this transaction block and sets their
            transaction block line numbers.

        _extract_info():
            Determines the start and end lines of the transaction block, extracts opening and
            closing balances, and identifies if the block is the first or last in the statement.
    """

    def __init__(self, Page: Page):
        self.id: UUID = uuid4()
        self.id_page: UUID = Page.id
        self.page = Page
        self.page_number: int = Page.page_number
        self.opening_balance: float | None = None
        self.closing_balance: float | None = None
        self.start_line: int | None = 0
        self.end_line: int | None = 0
        self.is_first: bool = False
        self.is_last: bool = False
        self.date_bbf: date | None = (
            None  # the date of the balance brought forward (if first transaction block)
        )
        self.date_bcf: date | None = (
            None  # the date of the balance carried forward (if last transaction block)
        )
        self._extract_info()
        self.lines: list[Line] | None = None
        self._get_lines()
        self.day_blocks: list[DayBlock] = []
        self._extract_day_blocks()

    def __repr__(self):
        return f"tblock: {self.id}; sheet: {self.page.sheet_number}; start_line: {self.start_line}; end_line: {self.end_line}; opening balance: {self.opening_balance}; closting balance: {self.closing_balance}"

    def _extract_day_blocks(self):
        # id_transaction_block, day_block_number, lines: list = None
        day_block_number: int = 0
        day_block_lines: list[Line] = []
        opening_balance: float | None = None
        closing_balance: float | None = None
        block_date: date | None = None

        if self.lines is not None:
            for line in self.lines:
                if (
                    line.line_number_page == self.start_line
                ):  # first line is always the start of the first day block
                    day_block_lines.append(line)  # add the line to the day block
                    opening_balance = (
                        self.opening_balance
                    )  # set the opening balance to that of the transaction block
                    if (
                        line.date is None
                    ):  # if the first line doesn't have a date it must take the last date from the previous sheet
                        block_date = last_date_from_previous_sheet(
                            self.page.id_statement, self.page.sheet_number
                        )
                    else:
                        block_date = line.date
                elif (
                    line.date is not None
                ):  # a date on any other line signals the start of a new day block
                    day_block_number += 1  # increment day block number
                    block_date = (
                        line.date
                    )  # set the block date to that of the current line
                    day_block_lines = []  # empty current day block lines
                    day_block_lines.append(line)
                else:  # the line is added to the current day block
                    day_block_lines.append(line)

                # Last line on a page gets the closing transaction block balance, otherwise the line balance if there is one
                if line.line_number_page == self.end_line:
                    closing_balance = self.closing_balance
                else:
                    closing_balance = line.balance

                if (
                    closing_balance is not None and block_date is not None
                ):  # a closing balance means the end of the day block and it can be created
                    # try:
                    self.day_blocks.append(
                        DayBlock(
                            id_transaction_block=self.id,
                            day_block_number=day_block_number,
                            date=block_date,
                            opening_balance=opening_balance,
                            closing_balance=closing_balance,
                            lines=day_block_lines,
                        )
                    )
                    date_log.append(
                        {
                            "id_statement": self.page.id_statement,
                            "sheet_number": self.page.sheet_number,
                            "date": block_date,
                        }
                    )
                    opening_balance = float(
                        closing_balance
                    )  # the closing balance becomes the opening balance for the next day block
                    # except Exception:
                    #     Exception(
                    #         f"Error adding day block for statement: {self.page.id_statement}; sheet: {self.page.sheet_number}; date: {block_date}"
                    #     )

    def _get_lines(self):
        if self.start_line is not None and self.end_line is not None:
            self.lines = [
                line for line in self.page.lines[self.start_line : self.end_line + 1]
            ]
            for line in self.lines:
                line.line_number_transaction_block = (
                    line.line_number_page - self.start_line
                )

    def _extract_info(self):
        # balance brought forward
        self.start_line: int | None = next(
            (
                line.line_number_page + 1
                for line in self.page.lines
                if BBF_LINE in line.text
            ),  # block starts 1 line after the bbf line
            None,
        )
        if self.start_line is not None:
            bbf_text = self.page.lines[
                self.start_line - 1
            ].text  # balance brought forward is one line before the block start line
            bbf_parts = bbf_text.split()
            if len(bbf_parts) >= 1:
                debit_flag: bool = False
                if bbf_parts[-1] == "D":
                    debit_flag = True
                    bbf_parts.pop()
                self.opening_balance = float(
                    str(bbf_parts.pop().strip()).replace(",", "")
                )
                if debit_flag:
                    self.opening_balance = self.opening_balance * -1
            if len(bbf_parts) >= 3:
                date_str = " ".join(bbf_parts[:3])
                self.date_bbf = make_date(date_str)
                self.is_first = True

        # balance carried forward
        self.end_line: int | None = next(
            (
                line.line_number_page - 1
                for line in self.page.lines
                if BCF_LINE in line.text
            ),  # block ends 1 line before the bcf line
            None,
        )
        if self.end_line is not None:
            bcf_text = self.page.lines[
                self.end_line + 1
            ].text  # balance carried forward is one line after the block end
            bcf_parts = bcf_text.split()
            if len(bcf_parts) >= 1:
                debit_flag: bool = False
                if (
                    bcf_parts[-1] == "D"
                ):  # if the last part of the line is a D then the closing balance is negative
                    debit_flag = True
                    bcf_parts.pop()
                self.closing_balance = float(
                    str(bcf_parts.pop().strip()).replace(",", "")
                )
                if debit_flag:
                    self.closing_balance = self.closing_balance * -1
            if (
                len(bcf_parts) >= 3
            ):  # if there are at least 3 parts to the line then the date is in the first 3 parts
                date_str = " ".join(bcf_parts[:3])
                self.date_bcf = make_date(date_str)
                self.is_last = True


class DayBlock:
    """
    Represents a block of transactions for a specific day within a transaction block.

    Attributes:
        id (UUID): Unique identifier for the DayBlock instance.
        id_transaction_block (UUID): Identifier of the parent transaction block.
        day_block_number (int): Sequential number of the day block within the transaction block.
        date (date): The date this day block represents.
        opening_balance (float | None): The opening balance for the day, if available.
        closing_balance (float | None): The closing balance for the day, if available.
        lines (list[Line] | None): List of Line objects representing raw transaction lines for the day.
        transactions (list[Transaction]): List of Transaction objects extracted from lines.

    Methods:
        __repr__(): Returns a string representation of the DayBlock instance.
        _extract_transactions(): Processes the lines to extract transactions, assigns transaction numbers,
            and attempts to balance the sum of transaction values with the movement (closing - opening balance).
            If the sum does not match, attempts to swap transaction polarities to achieve balance.
            Raises an Exception if unable to balance after a number of attempts.
    """

    def __init__(
        self,
        id_transaction_block: UUID,
        day_block_number: int,
        date: date,
        opening_balance: float | None = None,
        closing_balance: float | None = None,
        lines: list[Line] | None = None,
    ):
        self.id = uuid4()
        self.id_transaction_block = id_transaction_block
        self.day_block_number: int = day_block_number
        self.date = date
        self.opening_balance: float | None = opening_balance
        self.closing_balance: float | None = closing_balance
        self.lines: list[Line] | None = lines
        self.transactions: list[Transaction] = []
        self._extract_transactions()

    def __repr__(self):
        return f"day_block: {self.id}; t_block: {self.id_transaction_block}; date: {self.date}; opening_balance: {self.opening_balance}; closing_balance: {self.closing_balance}"

    def _extract_transactions(self):
        transaction_number: int = 0
        transaction_lines: list[Line] = []
        value_transactions: (
            float | None
        ) = -43214321.55  # dummy value to force a mis-match
        movement: float | None = None
        last_value: float | None = None
        if self.lines is not None:
            for index, line in enumerate(self.lines):
                if index == 0:
                    transaction_lines.append(
                        line
                    )  # add the line to the transaction lines
                    last_value = line.value_transaction
                elif (
                    line.type_transaction is not None and last_value is not None
                ):  # if it's a new transaction line
                    # number the current transaction lines
                    for ix, ln in enumerate(transaction_lines):
                        ln.line_number_transaction = ix
                    # add the transaction
                    self.transactions.append(
                        Transaction(
                            id_day_block=self.id,
                            transaction_number=transaction_number,
                            date_transaction=self.date,
                            lines=transaction_lines,
                        )
                    )
                    transaction_lines = []  # empty the transaction lines
                    transaction_number += 1  # increment the transaction number
                    transaction_lines.append(
                        line
                    )  # add the line to the transaction lines
                    last_value = line.value_transaction
                else:
                    transaction_lines.append(
                        line
                    )  # add the line to the transaction lines
                    last_value = line.value_transaction
                if index + 1 == len(
                    self.lines
                ):  # if this is the last line in the block
                    # number the transaction lines
                    for ix, ln in enumerate(transaction_lines):
                        ln.line_number_transaction = ix
                    # add the transaction
                    self.transactions.append(
                        Transaction(
                            id_day_block=self.id,
                            transaction_number=transaction_number,
                            date_transaction=self.date,
                            lines=transaction_lines,
                        )
                    )
                    transaction_lines = []

        if self.closing_balance is not None and self.opening_balance is not None:
            movement = abs(
                self.closing_balance - self.opening_balance
            )  # the movement is the absolute value of the difference between the closing and opening balance
            if (
                self.closing_balance < self.opening_balance
            ):  # if the closing balance is less than the opening balance then the movement is negative
                movement = movement * -1
        value_transactions = sum(transaction.value for transaction in self.transactions)
        if movement is not None and round(movement, 2) != round(value_transactions, 2):
            # print("date: ", self.date)
            # re-evaluate polarity of transactions
            polarity_swaps = [
                transaction
                for transaction in self.transactions
                if transaction.value_alt is not None
            ]
            for _ in range(POLARITY_SWAPS_MAX_TRIES):
                swap_int = randint(
                    0, len(polarity_swaps) - 1
                )  # randomly select a candidate to swap
                swap = polarity_swaps[swap_int]
                alt_val = swap.value_alt
                swap.value_alt = swap.value
                swap.value = alt_val if alt_val is not None else 0
                new_total = sum(transaction.value for transaction in self.transactions)
                if round(new_total, 2) == round(movement, 2):
                    #     print(movement, new_total)
                    #     print(self.transactions)
                    break

            value_transactions = sum(
                transaction.value for transaction in self.transactions
            )
            if round(value_transactions, 2) != round(movement, 2):
                for t in self.transactions:
                    print(t)
                print(value_transactions, movement)
                raise Exception(f"cannot balance transactions for {self}")

        # calculate the opening_balance and closing_balance of the transactions based on their value movement from the opening_balance of the day block
        running_balance: float = self.opening_balance if self.opening_balance else 0.0
        for transaction in self.transactions:
            transaction.opening_balance = running_balance
            running_balance += transaction.value
            transaction.closing_balance = running_balance


class Transaction:
    """
    Represents a financial transaction consisting of one or more lines within a day block.

    Attributes:
        id (UUID): Unique identifier for the transaction, generated automatically.
        id_day_block (UUID): Identifier for the associated day block.
        transaction_number (int): Sequential number of the transaction within the day block.
        date_transaction (date): Date when the transaction occurred.
        lines (list[Line]): List of Line objects representing the transaction details.
        type_transaction (str | None): Type of the transaction (e.g., "CR", "TFR"), extracted from the lines.
        value (float | None): Signed value of the transaction, determined by type and line value.
        value_alt (float | None): Alternative value, used for testing polarity within the day block.
        description (str): Short description of the transaction.
        description_long (str): Extended description, potentially concatenated from multiple lines.

    Methods:
        __repr__(): Returns a string representation of the transaction.
        _extract_info(): Extracts and sets transaction type, descriptions, and values from the lines.
    """

    def __init__(
        self,
        id_day_block: UUID,
        transaction_number: int,
        date_transaction: date,
        lines: list[Line],
    ):
        self.id: UUID = uuid4()
        self.id_day_block: UUID = id_day_block
        self.transaction_number: int = transaction_number
        self.date_transaction: date = date_transaction
        self.lines: list[Line] = lines
        self.type_transaction: str = "<no type>"
        self.value: float = -9999.88  # dummy value to force a mis-match
        self.value_alt: float | None = (
            None  # if unsure of the polarity we hold the negative here for testing within the day block
        )
        self.description: str = "<no description>"
        self.description_long: str = "<not description>"
        self._extract_info()
        self.opening_balance: float = 0.0
        self.closing_balance: float = 0.0

    def __repr__(self):
        return f"transaction: {self.id}; day_block: {self.id_day_block}; tr_number: {self.transaction_number}; date: {self.date_transaction}; type: {self.type_transaction}; description: {self.description}; value: {self.value}; value_alt: {self.value_alt}"

    def _extract_info(self):
        if len(self.lines) > 0:
            for line in self.lines:
                if line.line_number_transaction == 0:
                    self.type_transaction = (
                        line.type_transaction if line.type_transaction else "<no type>"
                    )
                    self.description = line.text_transaction
                    self.description_long = self.description
                elif line.line_number_transaction and line.line_number_transaction >= 1:
                    self.description_long += "|" + line.text_transaction
                if line.value_transaction is not None:
                    if self.type_transaction == "CR":
                        self.value = line.value_transaction
                    else:
                        self.value = line.value_transaction * -1
                    if self.type_transaction in ["TFR", "VIS", "BP"]:
                        self.value_alt = line.value_transaction


def make_date(date_str: str) -> date:
    """
    Converts a date string into a `date` object using the specified date format.

    Args:
        date_str (str): The date string to convert. Expected format is defined by `DATE_FORMAT` (e.g., '03 Jun 25').

    Returns:
        date: The corresponding `date` object if parsing is successful.

    Raises:
        Exception: If the input string does not match the expected date format.
        Exception: If no date is provided to the function.
    """
    true_date: date | None = None
    date_str = date_str.replace(",", "")
    try:
        true_date = datetime.date(datetime.strptime(date_str, DATE_FORMAT))
    except ValueError:
        raise Exception(
            f"'{date_str}' doesn't match the expected date format (e.g.'03 Jun 25')"
        )
    except TypeError:
        raise Exception("No date provided to the make_date function")
    return true_date


def last_date_from_previous_sheet(id_statement: UUID, sheet_number: int) -> date:
    """
    Returns the latest date from the previous sheet for a given statement ID.

    Args:
        id_statement (UUID): The unique identifier of the statement.
        sheet_number (int): The current sheet number.

    Returns:
        date: The latest date found in the previous sheet (sheet_number - 1) for the specified statement.

    Raises:
        ValueError: If no matching log line is found for the previous sheet.

    Note:
        Assumes that `date_log` is a list of dictionaries with keys "id_statement", "sheet_number", and "date".
    """
    last_date: date = max(
        log_line["date"]
        for log_line in date_log
        if log_line["id_statement"] == id_statement
        and log_line["sheet_number"] == sheet_number - 1
    )  # type: ignore - this is only assigning the date pare of the dictionary so not sure why it's complaining!
    return last_date


def tests(statement: Statement) -> bool:
    """
    Performs a series of consistency checks on a bank statement object to verify that the calculated balance movements at various levels (statement, page transaction blocks, daily blocks, and individual transactions) all match.

    Args:
        statement (Statement): The bank statement object containing balances and transactions, structured with pages, transaction blocks, day blocks, and transactions.

    Returns:
        bool: True if all calculated movements match (rounded to 2 decimal places), False otherwise.

    Prints:
        - The calculated movement at each level.
        - A success message if all movements match.
        - A failure message if any movement does not match.
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


def print_splitter():
    print()
    print(f"{''.join(['-' for _ in range(SPLITTER_LENGTH)])}")
    print()


if __name__ == "__main__":
    main()
    # Run the main function to process the bank statements

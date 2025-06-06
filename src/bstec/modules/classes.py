import re
from datetime import date, timedelta
from random import randint
from uuid import UUID, uuid4

from pdfplumber import open as pdf_open

from .constants import (
    ACCOUNT_INFO_HEADER,
    BBF_LINE,
    BCF_LINE,
    CLOSING_BALANCE_LINE,
    CURRENCY_PATTERN,
    DATE_FORMAT_DESC,
    OPENING_BALANCE_LINE,
    PAYMENTS_IN_LINE,
    PAYMENTS_OUT_LINE,
    POLARITY_SWAPS_MAX_TRIES,
    TRANSACTION_TYPES,
)
from .dateutils import date_log, last_date_from_previous_sheet, make_date


class Statement:
    """
    Represents a bank statement extracted from a PDF file.

    The Statement class is responsible for parsing and storing information from a bank statement PDF, including account details, statement
    period, balances, and transaction summaries. Upon initialization, it processes the provided PDF file to extract relevant data such as
    account name, sort code, account number, statement date range, opening and closing balances, and total payments in and out.
    It also determines if the statement should be flagged as skipped (e.g., if no transaction blocks are found).

    Attributes:
        id (UUID): Unique identifier for the statement.
        filename (str): Path to the PDF file containing the statement.
        pages (list[Page]): List of Page objects representing each page of the statement.
        sort_code (str): Bank sort code extracted from the statement.
        account_number (str): Account number extracted from the statement.
        account_name (str): Account holder's name extracted from the statement.
        statement_date_from (date | None): Start date of the statement period.
        statement_date_to (date | None): End date of the statement period.
        opening_balance (float | None): Opening balance at the start of the statement period.
        closing_balance (float | None): Closing balance at the end of the statement period.
        payments_in (float | None): Total payments into the account during the statement period.
        payments_out (float | None): Total payments out of the account during the statement period.
        skipped (bool): Indicates if the statement was skipped due to missing or incomplete data.
        statement_date_desc (str): Human-readable description of the statement period or skip status.

    Methods:
        _extract_pages(): Extracts text from each page of the PDF and populates the pages attribute.
        _extract_account_info(): Extracts account name, sort code, and account number from the statement.
        _extract_balance_and_payment_info(): Extracts opening/closing balances and payment totals.
        _get_statement_dates(): Determines the statement period based on transaction blocks.
        _check_for_skipped(): Flags the statement as skipped if no valid transaction blocks are found.
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
        self._extract_pages()
        self._extract_account_info()
        self._extract_balance_and_payment_info()
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
        """
        Determines and sets the statement date range for the account.

        Finds the start and end dates of the statement period by searching through the pages for the first and last transaction blocks.
        If both dates are found, sets `self.statement_date_from` to one day after the start date and `self.statement_date_to` to end date.
        """
        start_date = next(
            (page.transaction_block.date_bbf for page in self.pages if page.transaction_block and page.transaction_block.is_first),
            None,
        )
        end_date = next(
            (page.transaction_block.date_bcf for page in self.pages if page.transaction_block and page.transaction_block.is_last),
            None,
        )
        if start_date and end_date:
            self.statement_date_from = start_date + timedelta(days=1)
            self.statement_date_to = end_date

    def _extract_balance_and_payment_info(self):
        """
        Extracts balance and payment information from the first page's lines.

        This method scans through the lines of the first page in `self.pages` to find and extract the opening balance, payments in, payments
        out, and closing balance. It identifies each value by searching for specific keywords (`OPENING_BALANCE_LINE`, `PAYMENTS_IN_LINE`,
        `PAYMENTS_OUT_LINE`, `CLOSING_BALANCE_LINE`) in the line text. The method handles different currency symbols
        (such as "£", "$", "EUR") and removes commas from the extracted amounts. If a balance is marked as a debit
        (indicated by a trailing "D"), the value is converted to a negative number.

        Attributes Set:
            self.opening_balance (float): The extracted opening balance, negative if marked as debit.
            self.payments_in (float): The total payments in.
            self.payments_out (float): The total payments out.
            self.closing_balance (float): The extracted closing balance, negative if marked as debit.
        """
        for line in self.pages[0].lines:
            if OPENING_BALANCE_LINE in line.text or str(OPENING_BALANCE_LINE).replace(" ", "") in line.text:
                debit_flag: bool = False
                if line.text.split()[-1] == "D":
                    debit_flag = True
                    line.text = line.text.replace("D", "")
                self.opening_balance = float(
                    str(line.text.split()[-1]).replace(",", "").replace("£", "").replace("$", "").replace("EUR", "")
                )
                if debit_flag:
                    self.opening_balance = self.opening_balance * -1
            elif PAYMENTS_IN_LINE in line.text or str(PAYMENTS_IN_LINE).replace(" ", "") in line.text:
                self.payments_in = float(str(line.text.split()[-1]).replace(",", "").replace("£", "").replace("$", "").replace("EUR", ""))
            elif PAYMENTS_OUT_LINE in line.text or str(PAYMENTS_OUT_LINE).replace(" ", "") in line.text:
                self.payments_out = float(str(line.text.split()[-1]).replace(",", "").replace("£", "").replace("$", "").replace("EUR", ""))
            elif CLOSING_BALANCE_LINE in line.text or str(CLOSING_BALANCE_LINE).replace(" ", "") in line.text:
                debit_flag: bool = False
                if line.text.split()[-1] == "D":
                    debit_flag = True
                    line.text = line.text.replace("D", "")
                self.closing_balance = float(
                    str(line.text.split()[-1]).replace(",", "").replace("£", "").replace("$", "").replace("EUR", "")
                )
                if debit_flag:
                    self.closing_balance = self.closing_balance * -1

    def _extract_account_info(self):
        """
        Extracts account information (account name, sort code, and account number) from the first page of the document.

        This method searches for a line containing the `ACCOUNT_INFO_HEADER` in the text lines of the first page.
        If found, it retrieves the following line, splits it into parts, and assigns:
            - The last part (before the sheet number) as the account number,
            - The second to last part as the sort code,
            - The remaining parts as the account name.

        Assumes that the account information line contains at least four parts, with last part being the sheet number, which is discarded.

        Sets:
            self.account_name (str): The extracted account name.
            self.sort_code (str): The extracted sort code.
            self.account_number (str): The extracted account number.
        """
        account_info_line = next(
            (line.line_number_page for line in self.pages[0].lines if ACCOUNT_INFO_HEADER in line.text),
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

    def _extract_pages(self):
        """
        Extracts text from each page of the PDF file specified by `self.filename` and appends
        a `Page` object containing the extracted text, zero-indexed page number, and document ID
        to `self.pages`. Handles exceptions that may occur during file opening or processing.

        Raises:
            Prints an error message if the PDF file cannot be opened or processed.
        """
        try:
            with pdf_open(self.filename) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        self.pages.append(Page(page.page_number - 1, text, self.id))  # page number reduced by 1 to make it zero indexed
        except Exception as e:
            print(f"Error opening or processing PDF file '{self.filename}': {e}")


class Page:
    """
    Represents a single page of a bank statement, encapsulating its text content, metadata, and extracted information.

    Attributes:
        id (UUID): Unique identifier for the page.
        id_statement (UUID): Identifier of the statement this page belongs to.
        page_number (int): The page number within the statement.
        text (str): The raw text content of the page.
        sheet_number (int): The extracted sheet number from the account information section (default -1 if not found).
        lines (list[Line]): List of Line objects representing non-empty lines from the page text.
        transaction_block (TransactionBlock | None): Extracted transaction block if present, otherwise None.

    Methods:
        __init__(page_number: int, text: str, id_statement: UUID):
            Initializes a Page instance, extracts lines, sheet number, and transaction block.

        _get_transaction_block():
            Initializes and assigns a TransactionBlock to the page if transactions are found.

        _extract_lines():
            Extracts non-empty lines from the page text and creates Line objects for each.

        _extract_sheet_number():
            Extracts the sheet number from the account information section of the page lines.
    """

    def __init__(self, page_number: int, text: str, id_statement: UUID):  # type: ignore
        self.id: UUID = uuid4()
        self.id_statement: UUID = id_statement
        self.page_number: int = page_number
        self.text: str = text
        self.sheet_number: int = -1  # dummy sheet number
        self.account_info_line: int = 999  # default value, will be set if account info is found
        self.lines: list[Line] = []
        self.transaction_block: TransactionBlock | None = None
        self._extract_lines()
        self._extract_sheet_number()
        self._get_transaction_block()

    def _get_transaction_block(self):
        """
        Initializes a TransactionBlock instance and assigns it to the `transaction_block` attribute
        if the created block contains at least one line.

        Returns:
            None
        """
        tb = TransactionBlock(self)
        if tb and tb.lines and len(tb.lines) > 0:
            self.transaction_block = tb

    def _extract_lines(self):
        """
        Extracts non-empty lines from the object's `text` attribute, creates `Line` objects for each, and appends them to the `lines` list.

        Each `Line` object is initialized with the line's text and its corresponding line number within the page.

        Returns:
            None
        """
        line_number = 0
        for line in self.text.split("\n"):
            if line.strip():
                self.lines.append(Line(text=line, line_number_page=line_number))
                line_number += 1

    def _extract_sheet_number(self):
        """
        Extracts the sheet number from the account information section of the lines.

        This method searches for the line containing the account information header,
        then retrieves the line immediately following it, which is expected to contain
        the account information. It splits this line into parts and, if there are at
        least four parts, assigns the last part (expected to be the sheet number) to
        the `self.sheet_number` attribute as an integer.

        Assumes:
            - `self.lines` is a list of objects with `text` and `line_number_page` attributes.
            - `ACCOUNT_INFO_HEADER` is a string constant present in the relevant header line.
            - The sheet number is the last whitespace-separated value in the account info line.

        Raises:
            - ValueError: If the extracted sheet number cannot be converted to an integer.
        """
        self.account_info_line = next(
            (line.line_number_page for line in self.lines if ACCOUNT_INFO_HEADER in line.text),
            None,
        )
        if self.account_info_line is not None:
            account_info = self.lines[self.account_info_line + 1].text  # info is 1 line beneath the header
            account_info_parts = account_info.split()
            if len(account_info_parts) >= 4:
                # the final part of the line is the sheet number
                self.sheet_number = int(account_info_parts.pop())


class Line:
    """
    Represents a single line entry from a banking statement, encapsulating parsed transaction details.

    Attributes:
        id (UUID): Unique identifier for the line.
        line_number_page (int): The line number on the page.
        line_number_transaction_block (int | None): The line number within the transaction block, if applicable.
        line_number_day_block (int | None): The line number within the day block, if applicable.
        line_number_transaction (int | None): The line number within the transaction, if applicable.
        text (str): The raw text of the line.
        date (date | None): The transaction date, if parsed from the text.
        type_transaction (str | None): The type of transaction, if recognized.
        balance (float | None): The resulting balance after the transaction, if parsed.
        value_transaction (float | None): The value of the transaction, if parsed.
        text_transaction (str): The narrative or description of the transaction.

    Methods:
        __init__(text: str, line_number_page: int):
            Initializes a Line instance and attempts to extract transaction information from the provided text.

        __repr__():
            Returns a string representation of the Line instance, including key parsed attributes.

        _extract_info():
            Parses the raw text to extract transaction details such as date, balance, transaction value, type, and description.
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
        return (
            f"{self.line_number_page}.{self.line_number_transaction_block}: {self.text} --- date: {self.date}, "
            f"type_transaction: {self.type_transaction}, text_transaction: {self.text_transaction}, "
            f"value_transaction: {self.value_transaction}, balance: {self.balance}, "
            f"line_number_transaction: {self.line_number_transaction}"
        )

    def _extract_info(self):
        """
        Extracts and parses transaction information from the instance's `text` attribute.

        This method analyzes the text, attempting to extract and set the following attributes:
        - `date`: The transaction date, if present at the start of the text.
        - `balance`: The resulting balance after the transaction, if present.
        - `value_transaction`: The value of the transaction, if present.
        - `type_transaction`: The type of transaction, if recognized.
        - `text_transaction`: The narrative or description of the transaction.

        The method also handles debit transactions indicated by a trailing "D" and parses currency values using a predefined pattern.
        If parsing fails at any step, the corresponding attribute may remain unset or set to a default value.
        """
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
            if possible_type_transaction is not None and possible_type_transaction in valid_types:
                self.type_transaction = possible_type_transaction

        # set the narrative
        start_point = 0
        end_point = tp_length
        if self.date is not None:
            start_point += 3
        if self.type_transaction is not None:
            start_point += 1
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
    Represents a block of transactions within a bank statement page.
    A TransactionBlock groups together a contiguous set of transaction lines on a statement page,
    bounded by a "balance brought forward" (BBF) and a "balance carried forward" (BCF) line.
    It extracts and organizes information such as opening and closing balances, the range of lines
    it covers, and further subdivides its lines into day blocks (DayBlock) based on transaction dates.
    Attributes:
        id (UUID): Unique identifier for the transaction block.
        id_page (UUID): Identifier of the associated Page.
        page (Page): The Page object this transaction block belongs to.
        page_number (int): The page number within the statement.
        opening_balance (float | None): The opening balance at the start of the block.
        closing_balance (float | None): The closing balance at the end of the block.
        start_line (int | None): The line number (on the page) where the block starts.
        end_line (int | None): The line number (on the page) where the block ends.
        is_first (bool): True if this is the first transaction block on the statement.
        is_last (bool): True if this is the last transaction block on the statement.
        date_bbf (date | None): Date of the balance brought forward (if first block).
        date_bcf (date | None): Date of the balance carried forward (if last block).
        lines (list[Line] | None): The list of Line objects belonging to this block.
        day_blocks (list[DayBlock]): List of DayBlock objects, each representing a day's transactions within the block.
    Methods:
        __repr__(): Returns a string representation of the transaction block.
        _extract_day_blocks(): Groups lines into day blocks based on dates and populates self.day_blocks.
        _get_lines(): Extracts the lines belonging to this transaction block from the page.
        _extract_info(): Extracts opening/closing balances, start/end lines, and relevant dates from the page lines.
    Usage:
        Typically instantiated with a Page object, after which it automatically extracts its information
        and subdivides itself into day blocks.
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
        self.date_bbf: date | None = None  # the date of the balance brought forward (if first transaction block)
        self.date_bcf: date | None = None  # the date of the balance carried forward (if last transaction block)
        self._extract_info()
        self.lines: list[Line] | None = None
        self._get_lines()
        self.day_blocks: list[DayBlock] = []
        self._extract_day_blocks()

    def __repr__(self):
        return (
            f"tblock: {self.id}; sheet: {self.page.sheet_number}; start_line: {self.start_line}; end_line: {self.end_line};"
            f" opening balance: {self.opening_balance}; closing balance: {self.closing_balance}"
        )

    def _extract_day_blocks(self):
        """
        Extracts and groups lines into day blocks within a transaction block.

        This method iterates over the lines associated with the transaction block, grouping them into day blocks based on the presence of a
        date in each line. The first line of the transaction block always starts the first day block. If a line contains a date, it marks
        the beginning of a new day block. Each day block is assigned an opening balance, closing balance, and date. The method also handles
        cases where the first line does not have a date by retrieving the last date from the previous sheet. At the end of each day block,
        a `DayBlock` object is created and appended to the `day_blocks` list, and relevant date information is logged.

        Side Effects:
            - Modifies `self.day_blocks` by appending new `DayBlock` instances.
            - Updates the `date_log` with date information for each day block.

        Assumes:
            - `self.lines` is a list of `Line` objects, each with attributes such as `line_number_page`, `date`, and `balance`.
            - `self.page`, `self.opening_balance`, `self.closing_balance`, `self.start_line`, and `self.end_line` are properly initialized.
            - `last_date_from_previous_sheet` is a function available in the current scope.
        """
        # id_transaction_block, day_block_number, lines: list = None
        day_block_number: int = 0
        day_block_lines: list[Line] = []
        opening_balance: float | None = None
        closing_balance: float | None = None
        block_date: date | None = None

        if self.lines is not None:
            for line in self.lines:
                if line.line_number_page == self.start_line:  # first line is always the start of the first day block
                    day_block_lines.append(line)  # add the line to the day block
                    opening_balance = self.opening_balance  # set the opening balance to that of the transaction block
                    if line.date is None:  # if the first line doesn't have a date it must take the last date from the previous sheet
                        block_date = last_date_from_previous_sheet(self.page.id_statement, self.page.sheet_number)
                    else:
                        block_date = line.date
                elif line.date is not None:  # a date on any other line signals the start of a new day block
                    day_block_number += 1  # increment day block number
                    block_date = line.date  # set the block date to that of the current line
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
                    opening_balance = float(closing_balance)  # the closing balance becomes the opening balance for the next day block

    def _get_lines(self):
        """
        Extracts a subset of lines from the page based on the specified start and end line indices,
        and updates each line's `line_number_transaction_block` attribute to reflect its position
        relative to the start of the selection.

        If both `self.start_line` and `self.end_line` are not None, this method:
            - Slices `self.page.lines` from `self.start_line` to `self.end_line` (inclusive)
              and assigns the result to `self.lines`.
            - For each line in `self.lines`, sets `line.line_number_transaction_block` to the
              difference between the line's original page number (`line.line_number_page`) and
              `self.start_line`.
        """
        if self.start_line is not None and self.end_line is not None:
            self.lines = [line for line in self.page.lines[self.start_line : self.end_line + 1]]
            for line in self.lines:
                line.line_number_transaction_block = line.line_number_page - self.start_line

    def _extract_info(self):
        """
        Extracts and sets information about the opening and closing balances from the page lines.

        This method searches for lines containing the balance brought forward (BBF) and balance carried forward (BCF) markers.
        It determines the start and end lines for a block of interest, extracts the opening and closing balances (including
        handling debit flags), and parses the associated dates. Sets the following instance attributes if found:

        - self.start_line: The line number where the block starts (after BBF line), or None if not found.
        - self.opening_balance: The opening balance as a float (negative if marked as debit).
        - self.date_bbf: The date associated with the opening balance, if available.
        - self.is_first: True if the BBF line and date are found.

        - self.end_line: The line number where the block ends (before BCF line), or None if not found.
        - self.closing_balance: The closing balance as a float (negative if marked as debit).
        - self.date_bcf: The date associated with the closing balance, if available.
        - self.is_last: True if the BCF line and date are found.

        Assumes that BBF_LINE and BCF_LINE are defined constants and that self.page.lines is a list of line objects
        with 'text' and 'line_number_page' attributes. Also assumes the existence of a make_date function for parsing dates.
        """
        # balance brought forward
        self.start_line: int | None = next(
            (
                line.line_number_page + 1
                for line in self.page.lines
                if BBF_LINE in line.text or str(BBF_LINE).replace(" ", "") in line.text
            ),  # block starts 1 line after the bbf line
            None,
        )
        if self.start_line is not None:
            bbf_text = self.page.lines[self.start_line - 1].text  # balance brought forward is one line before the block start line
            bbf_parts = bbf_text.split()
            if len(bbf_parts) >= 1:
                debit_flag: bool = False
                if bbf_parts[-1] == "D":
                    debit_flag = True
                    bbf_parts.pop()
                self.opening_balance = float(str(bbf_parts.pop().strip()).replace(",", ""))
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
                if BCF_LINE in line.text or str(BCF_LINE).replace(" ", "") in line.text
            ),  # block ends 1 line before the bcf line
            None,
        )
        if self.end_line is not None:
            bcf_text = self.page.lines[self.end_line + 1].text  # balance carried forward is one line after the block end
            bcf_parts = bcf_text.split()
            if len(bcf_parts) >= 1:
                debit_flag: bool = False
                if bcf_parts[-1] == "D":  # if the last part of the line is a D then the closing balance is negative
                    debit_flag = True
                    bcf_parts.pop()
                self.closing_balance = float(str(bcf_parts.pop().strip()).replace(",", ""))
                if debit_flag:
                    self.closing_balance = self.closing_balance * -1
            if len(bcf_parts) >= 3:  # if there are at least 3 parts to the line then the date is in the first 3 parts
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
        return (
            f"day_block: {self.id}; t_block: {self.id_transaction_block}; date: {self.date};"
            f" opening_balance: {self.opening_balance}; closing_balance: {self.closing_balance}"
        )

    def _extract_transactions(self):
        """
        Extracts and groups lines into transactions, assigns transaction numbers, and calculates transaction values and balances.

        This method processes the lines associated with the current object, grouping them into transactions based on the presence of a
        transaction type. For each transaction, it assigns line numbers, appends the transaction to the object's transaction list, and
        updates the transaction number. At the end of processing, it ensures the last transaction is added.

        After extracting transactions, it calculates the total movement (difference between closing and opening balances) and compares it
        to the sum of transaction values. If there is a mismatch, it attempts to correct the polarity of transactions with alternate values,
        retrying up to a maximum number of times. If the values still do not match, it raises an exception.

        Finally, it calculates and assigns the opening and closing balances for each transaction based on the day's opening balance and the
        cumulative transaction values.

        Raises:
            Exception: If the sum of transaction values cannot be balanced with the calculated movement after polarity swaps.
        """
        transaction_number: int = 0
        transaction_lines: list[Line] = []
        value_transactions: float | None = -43214321.55  # dummy value to force a mis-match
        movement: float | None = None
        last_value: float | None = None
        if self.lines is not None:
            for index, line in enumerate(self.lines):
                if index == 0:
                    transaction_lines.append(line)  # add the line to the transaction lines
                    last_value = line.value_transaction
                elif line.type_transaction is not None and last_value is not None:  # if it's a new transaction line
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
                    transaction_lines.append(line)  # add the line to the transaction lines
                    last_value = line.value_transaction
                else:
                    transaction_lines.append(line)  # add the line to the transaction lines
                    last_value = line.value_transaction
                if index + 1 == len(self.lines):  # if this is the last line in the block
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
            polarity_swaps = [transaction for transaction in self.transactions if transaction.value_alt is not None]
            for _ in range(POLARITY_SWAPS_MAX_TRIES):
                swap_int = randint(0, len(polarity_swaps) - 1)  # randomly select a candidate to swap
                swap = polarity_swaps[swap_int]
                alt_val = swap.value_alt
                swap.value_alt = swap.value
                swap.value = alt_val if alt_val is not None else 0
                new_total = sum(transaction.value for transaction in self.transactions)
                if round(new_total, 2) == round(movement, 2):
                    #     print(movement, new_total)
                    #     print(self.transactions)
                    break

            value_transactions = sum(transaction.value for transaction in self.transactions)
            if round(value_transactions, 2) != round(movement, 2):
                for t in self.transactions:
                    print(t)
                print(value_transactions, movement)
                raise Exception(f"cannot balance transactions for {self}")

        # calculate the opening_balance and closing_balance of transactions based on their value movement from opening_balance of day block
        running_balance: float = self.opening_balance if self.opening_balance else 0.0
        for transaction in self.transactions:
            transaction.opening_balance = running_balance
            running_balance += transaction.value
            transaction.closing_balance = running_balance


class Transaction:
    """
    Represents a financial transaction consisting of one or more lines within a day block.

    Attributes:
        id (UUID): Unique identifier for the transaction.
        id_day_block (UUID): Identifier for the associated day block.
        transaction_number (int): Sequential number of the transaction within the day block.
        date_transaction (date): Date of the transaction.
        lines (list[Line]): List of Line objects representing the transaction's details.
        type_transaction (str): Type of the transaction (e.g., "CR", "TFR", etc.).
        value (float): Main value of the transaction, with sign based on type.
        value_alt (float | None): Alternative value, used for certain transaction types or polarity checks.
        description (str): Short description of the transaction.
        description_long (str): Extended description, possibly concatenated from multiple lines.
        opening_balance (float): Opening balance before the transaction.
        closing_balance (float): Closing balance after the transaction.

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
        self.value_alt: float | None = None  # if unsure of the polarity we hold the negative here for testing within the day block
        self.description: str = "<no description>"
        self.description_long: str = "<not description>"
        self._extract_info()
        self.opening_balance: float = 0.0
        self.closing_balance: float = 0.0

    def __repr__(self):
        return (
            f"transaction: {self.id}; day_block: {self.id_day_block}; tr_number: {self.transaction_number};"
            f" date: {self.date_transaction}; type: {self.type_transaction}; description: {self.description};"
            f" value: {self.value}; value_alt: {self.value_alt}"
        )

    def _extract_info(self):
        if len(self.lines) > 0:
            for line in self.lines:
                if line.line_number_transaction == 0:
                    self.type_transaction = line.type_transaction if line.type_transaction else "<no type>"
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

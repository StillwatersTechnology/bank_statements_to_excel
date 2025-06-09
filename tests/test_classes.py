from bstec.modules.utils import make_date

"""
Test cases for the basic properties of various classes in the BSTEC module.
These tests ensure that the basic attributes and values of Statement, Page, Line, TransactionBlock,
DayBlock, Transaction, and Credit classes are correctly initialized and accessible.

pytest fixtures are used to create instances of these classes with predefined values for testing.
the fixtures are defined in conftest.py for use in these tests.

mock statements are used to provide a controlled environment for testing.
the mock statements are located in the TEST_DIRECTORY/mock_statements directory.
rather than simply mocking the data, we use actual PDF files that have been created for testing purposes.
This allows us to test the parsing and extraction of data from real PDF files, ensuring that the module works as expected.
"""


def test_statement_basic(statement_basic):
    """
    Test the basic properties and values of a Statement object.

    This test verifies that:
    - The Statement object is not None.
    - The Statement has a non-None ID.
    - The account name, sort code, and account number match expected values.
    - The closing and opening balances are as expected.
    - The payments in and out are correct.
    - The 'skipped' attribute is False.
    - The statement date description matches the expected string.
    """
    assert statement_basic is not None, "Statement object should not be None"
    assert statement_basic.id is not None, "Statement ID should not be None"
    assert statement_basic.account_name == "Mr Jonathan Doe", "Account name should be 'Mr Jonathan Doe'"
    assert statement_basic.sort_code == "22-22-22", "Sort code should be '22-22-22'"
    assert statement_basic.account_number == "11111111", "Account number should be '11111111'"
    assert statement_basic.closing_balance == 508.87, "Closing balance should be 508.87"
    assert statement_basic.opening_balance == 656.04, "Opening balance should be 656.04"
    assert statement_basic.payments_in == 50.00, "Payments in should be 50.00"
    assert statement_basic.payments_out == 197.17, "Payments out should be 197.17"
    assert not statement_basic.skipped, "Skipped should be False"
    assert statement_basic.statement_date_desc == "11 April 2025 to 10 May 2025", (
        "Statement date description should be '11 April 2025 to 10 May 2025'"
    )


def test_page_basic(page_basic):
    """
    Test the basic properties of the `page_basic` object.

    This test verifies that:
    - The `page_basic` object is not None.
    - The `id_statement` attribute of `page_basic` is not None.
    - The `sheet_number` attribute equals 558.
    - The `transaction_block` attribute is not None.
    - The `account_info_line` attribute does not equal 999.

    """
    assert page_basic is not None, "Page object should not be None"
    assert page_basic.id_statement is not None, "Page should have a valid statement"
    assert page_basic.sheet_number == 558, "Page number should be 558"
    assert page_basic.transaction_block is not None, "Page should have transactions"
    assert page_basic.account_info_line != 999, "Account info line should not be 999"


def test_line_basic(line_basic):
    """
    Test the basic properties of the 'line_basic' object.

    This test verifies that:
    - The 'line_basic' object is not None.
    - The 'line_number_transaction' attribute equals 1.
    - The 'type_transaction' attribute is None.
    - The 'text_transaction' attribute equals "INTERNET TRANSFER".
    - The 'value_transaction' attribute equals 10.8.
    - The 'balance' attribute equals 479.37.
    - The 'date' attribute is None, as this is not the first line of the transaction block.
    """
    assert line_basic is not None, "Line object should not be None"
    assert line_basic.line_number_transaction == 1, "Line number should be 1"
    assert line_basic.type_transaction is None, "Type transaction should be None"
    assert line_basic.text_transaction == "INTERNET TRANSFER", "Text transaction should be 'INTERNET TRANSFER'"
    assert line_basic.value_transaction == 10.8, "Value transaction should be 10.8"
    assert line_basic.balance == 479.37, "Balance should be 479.37"
    assert line_basic.date is None, "Date should be None as this is not the 1st line of the transaction block"


def test_transaction_block_basic(transaction_block_basic):
    """
    Test the basic properties of a transaction block.

    This test verifies that:
    - The transaction block is not None.
    - The transaction block contains lines.
    - The transaction block has exactly 16 lines.
    - The opening balance is 656.04.
    - The closing balance is 508.87.
    - The BBF (brought forward) date is '10 Apr 25'.
    - The CBF (carried forward) date is '10 May 25'.
    """
    assert transaction_block_basic is not None, "Transaction block should not be None"
    assert transaction_block_basic.lines, "Transaction block should have lines"
    assert len(transaction_block_basic.lines) == 16, "Transaction block should have 16 lines"
    assert transaction_block_basic.opening_balance == 656.04, "Opening balance should be 656.04"
    assert transaction_block_basic.closing_balance == 508.87, "Closing balance should be 508.87"
    assert transaction_block_basic.date_bbf == make_date("10 Apr 25"), "BBF date should be '10 Apr 25'"
    assert transaction_block_basic.date_bcf == make_date("10 May 25"), "CBF date should be '10 May 25'"


def test_day_block_basic(day_block_basic):
    """
    Test the basic properties and integrity of the 'day_block_basic' fixture.

    This test verifies:
    - The 'day_block_basic' object is not None.
    - The 'date' attribute matches the expected value ("22 Apr 25").
    - The 'lines' attribute contains exactly 3 items.
    - The 'opening_balance' is 574.64.
    - The 'closing_balance' is 490.17.
    - The 'transactions' attribute contains exactly 2 items.

    Raises:
        AssertionError: If any of the above conditions are not met.
    """
    assert day_block_basic is not None, "Day block should not be None"
    assert day_block_basic.date == make_date("22 Apr 25"), "Day block date should be '22 Apr 25'"
    assert len(day_block_basic.lines) == 3, "Day block should have 3 lines"
    assert day_block_basic.opening_balance == 574.64, "Opening balance should be 574.64"
    assert day_block_basic.closing_balance == 490.17, "Closing balance should be 490.17"
    assert len(day_block_basic.lines) == 3, "Day block should have 3 lines"
    assert len(day_block_basic.transactions) == 2, "Day block should have 2 transactions"


def test_transaction_basic(transaction_basic):
    """
    Test the basic properties of a transaction object.

    This test verifies that the `transaction_basic` fixture is correctly initialized with the expected values:
    - The transaction object is not None.
    - The transaction date matches the expected date.
    - The transaction value, opening balance, and closing balance are as expected.
    - The short and long descriptions are correct.
    - The transaction type is correct.
    - The transaction contains exactly two lines.
    """
    assert transaction_basic is not None, "Transaction should not be None"
    assert transaction_basic.date_transaction == make_date("22 Apr 25"), "Transaction date should be '22 Apr 25'"
    assert transaction_basic.value == -84.00, "Transaction value should be 84.00"
    assert transaction_basic.opening_balance == 574.64, "Transaction opening balance should be 574.64"
    assert transaction_basic.closing_balance == 490.64, "Transaction closing balance should be 490.64"
    assert transaction_basic.description == "123123 11111111", "Transaction description should be '123123 11111111'"
    assert transaction_basic.description_long == "123123 11111111|INTERNET TRANSFER", (
        "Transaction long description should be '123123 11111111|INTERNET TRANSFER'"
    )
    assert transaction_basic.type_transaction == "TFR", "Transaction type should be 'TFR'"
    assert len(transaction_basic.lines) == 2, "Transaction should have 2 lines"


def test_credit_basic(credit_basic):
    """
    Test the basic properties of a credit transaction object.

    This test verifies that the `credit_basic` fixture is correctly initialized with the expected values:
    - The transaction object is not None.
    - The transaction date matches the expected date.
    - The transaction value, opening balance, and closing balance are as expected.
    - The short and long descriptions are correct.
    - The transaction type is 'CR' (credit).
    - The transaction contains exactly one line.
    """
    assert credit_basic is not None, "Credit transaction should not be None"
    assert credit_basic.date_transaction == make_date("06 May 25"), "Credit transaction date should be '06 May 25'"
    assert credit_basic.value == 50.00, "Credit transaction value should be 50.00"
    assert credit_basic.opening_balance == 479.37, "Credit transaction opening balance should be 479.37"
    assert credit_basic.closing_balance == 529.37, "Credit transaction closing balance should be 529.37"
    assert credit_basic.description == "STILLS/NASH", "Credit transaction description should be 'STILLS/NASH'"
    assert credit_basic.description_long == "STILLS/NASH", "Credit transaction long description should be 'STILLS/NASH'"
    assert credit_basic.type_transaction == "CR", "Credit transaction type should be 'CR'"
    assert len(credit_basic.lines) == 1, "Credit transaction should have 1 line"

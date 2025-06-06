"""
Fixtures for testing the BSTEC module.
These fixtures provide mock data for testing the Statement, Page, Line, TransactionBlock,
DayBlock, Transaction, and Credit classes.

mock statements are used to provide a controlled environment for testing.
the mock statements are located in the TEST_DIRECTORY/mock_statements directory.
rather than simply mocking the data, we use actual PDF files that have been created for testing purposes.
This allows us to test the parsing and extraction of data from real PDF files, ensuring that the module works as expected.
"""

import pytest

from bstec.modules import STATEMENT_DIRECTORY, TEST_DIRECTORY, Statement

print(f"Test directory: {TEST_DIRECTORY}")
print(f"Statement directory: {STATEMENT_DIRECTORY}")

mock_directory = f"{TEST_DIRECTORY}/mock_statements"
print(f"Mock directory: {mock_directory}")


@pytest.fixture()
def statement_basic():
    stmt = Statement(f"{mock_directory}/hsbc_current_basic.pdf")
    return stmt


@pytest.fixture
def page_basic(statement_basic):
    """Fixture to return the first page of the basic statement"""
    return statement_basic.pages[0]


@pytest.fixture
def line_basic(page_basic):
    """Fixture to return the first line of the first page of the basic statement"""
    return page_basic.lines[36]  # 36.10: INTERNET TRANSFER 10.80 479.37 --- date: None, type_transaction: None,
    # text_transaction: INTERNET TRANSFER, value_transaction: 10.8, balance: 479.37, line_number_transaction: 1


@pytest.fixture
def transaction_block_basic(page_basic):
    """Fixture to return the transaction block of the defined page of the basic statement"""
    return page_basic.transaction_block


@pytest.fixture
def day_block_basic(transaction_block_basic):
    """Fixture to return the day block of the first page of the basic statement"""
    return transaction_block_basic.day_blocks[1]  # 22nd April 2025


@pytest.fixture
def transaction_basic(day_block_basic):
    """Fixture to return the first transaction of defined transaction block of the basic statement"""
    return day_block_basic.transactions[0]  #  1st transaction of the 22nd April 2025 day block - an internet transfer of 84.00


@pytest.fixture
def credit_basic(transaction_block_basic):
    """Fixture to return the credits of the defined transaction block of the basic statement"""
    return transaction_block_basic.day_blocks[3].transactions[0]  #  1st transaction of the 6th May 25 day block - a credit of 50.00

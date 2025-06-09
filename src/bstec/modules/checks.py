from .classes import Statement
from .data_definitions import ConsistencyCheckResult


def consistency_checks(statement: Statement) -> ConsistencyCheckResult:
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
    result = ConsistencyCheckResult(
        id_statement=statement.id,
        account=statement.account_number,
        statement_date=statement.statement_date_desc,
    )

    if statement.closing_balance is None:
        result.message = "Statement closing balance is None, cannot perform consistency checks."
        result.passed_checks = False
        return result
    elif statement.opening_balance is None:
        result.message = "Statement opening balance is None, cannot perform consistency checks."
        result.passed_checks = False
        return result
    else:
        result.movement_statement = round(statement.closing_balance - statement.opening_balance, 2)
    # page transaction block movement
    result.movement_transaction_blocks = round(
        sum(
            page.transaction_block.closing_balance - page.transaction_block.opening_balance
            for page in statement.pages
            if page.transaction_block is not None
            and page.transaction_block.closing_balance is not None
            and page.transaction_block.opening_balance is not None
        ),
        2,
    )
    # the cumulative movement of block of days
    result.movement_day_blocks = round(
        sum(
            sum(
                day_block.closing_balance - day_block.opening_balance
                for day_block in page.transaction_block.day_blocks
                if day_block.closing_balance is not None and day_block.opening_balance is not None
            )
            for page in statement.pages
            if page.transaction_block is not None
        ),
        2,
    )
    # the total value of all transactions
    result.movement_transactions = round(
        sum(
            sum(sum(transaction.value for transaction in day_block.transactions) for day_block in page.transaction_block.day_blocks)
            for page in statement.pages
            if page.transaction_block is not None
        ),
        2,
    )
    result.passed_checks = (
        result.movement_statement == result.movement_transaction_blocks == result.movement_day_blocks == result.movement_transactions
    )
    result.message = (
        "CONSISTENCY CHECK RESULTS:\n"
        f"Statement: {round(result.movement_statement, 2)}\n"
        f"Transaction Blocks: {round(result.movement_transaction_blocks, 2)}\n"
        f"Day Blocks: {round(result.movement_day_blocks, 2)}\n"
        f"Individual Transactions: {round(result.movement_transactions, 2)}\n"
        "SUCCESS! Statement balance checks are all GOOD"
        if result.passed_checks
        else "FAILURE! Statement balance checks do not all match - please check the statement and re-try"
    )
    return result

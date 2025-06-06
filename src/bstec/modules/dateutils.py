from datetime import date, datetime
from typing import Union
from uuid import UUID

from .constants import DATE_FORMAT

date_log: list[dict[str, Union[UUID, int, date]]] = []


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
    except ValueError as err:
        raise Exception(f"'{date_str}' doesn't match the expected date format (e.g.'03 Jun 25')") from err
    except TypeError as err:
        raise Exception("No date provided to the make_date function") from err
    return true_date


def last_date_from_previous_sheet(id_statement: UUID, sheet_number: int) -> date:
    """
    Returns the latest date from the previous sheet for a given statement ID.

    Args:
        id_statement (UUID): The unique identifier of the statement.
        sheet_number (int): The current sheet number.

    Returns:
        date: The most recent date from the previous sheet (sheet_number - 1) associated with the given statement ID.

    Raises:
        ValueError: If there are no matching log lines for the previous sheet.
    """
    last_date: date = max(
        log_line["date"]
        for log_line in date_log
        if log_line["id_statement"] == id_statement and log_line["sheet_number"] == sheet_number - 1
    )  # type: ignore - this is only assigning the date pare of the dictionary so not sure why it's complaining!
    if not last_date:
        raise ValueError(
            f"No previous sheet found for statement ID {id_statement} and sheet number {sheet_number - 1},"
            "but transaction block date is required."
        )
    # If we have a date, return it
    return last_date

from datetime import date
from uuid import uuid4

import pytest

import bstec.modules.dateutils as dateutils


def test_make_date():
    # Test valid date string returns the correct date object
    assert dateutils.make_date("03 Jun 25") == date(2025, 6, 3)

    # Test invalid date string
    with pytest.raises(Exception) as excinfo:
        dateutils.make_date("Invalid Date")
    assert "doesn't match the expected date format" in str(excinfo.value)

    # Test empty date string
    with pytest.raises(Exception) as excinfo:
        dateutils.make_date("")
    assert "doesn't match the expected date format" in str(excinfo.value)


def test_last_date_from_previous_sheet():
    # Test valid case
    dateutils.date_log.clear()
    test_uuid = uuid4()
    dateutils.date_log.append({"id_statement": test_uuid, "sheet_number": 1, "date": date(2024, 5, 10)})
    result = dateutils.last_date_from_previous_sheet(test_uuid, 2)
    assert result == date(2024, 5, 10)

    # # Test no matching case
    with pytest.raises(ValueError):
        dateutils.last_date_from_previous_sheet(test_uuid, 1)  # No previous sheet to get date from

    # Test with no previous sheet
    dateutils.date_log.clear()
    with pytest.raises(ValueError):
        dateutils.last_date_from_previous_sheet(test_uuid, 2)

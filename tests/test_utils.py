from datetime import date
from uuid import uuid4

import pytest

import bstec.modules.utils as utils


def test_make_date():
    # Test valid date string returns the correct date object
    assert utils.make_date("03 Jun 25") == date(2025, 6, 3)

    # Test invalid date string
    with pytest.raises(Exception) as excinfo:
        utils.make_date("Invalid Date")
    assert "doesn't match the expected date format" in str(excinfo.value)

    # Test empty date string
    with pytest.raises(Exception) as excinfo:
        utils.make_date("")
    assert "doesn't match the expected date format" in str(excinfo.value)


def test_last_date_from_previous_sheet():
    # Test valid case
    utils.date_log.clear()
    test_uuid = uuid4()
    utils.date_log.append({"id_statement": test_uuid, "sheet_number": 1, "date": date(2024, 5, 10)})
    result = utils.last_date_from_previous_sheet(test_uuid, 2)
    assert result == date(2024, 5, 10)

    # # Test no matching case
    with pytest.raises(ValueError):
        utils.last_date_from_previous_sheet(test_uuid, 1)  # No previous sheet to get date from

    # Test with no previous sheet
    utils.date_log.clear()
    with pytest.raises(ValueError):
        utils.last_date_from_previous_sheet(test_uuid, 2)

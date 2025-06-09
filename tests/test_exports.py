from os import listdir

import polars as pl
import pytest

from bstec.modules import (
    EXPORT_CSV_DIRECTORY,
    EXPORT_EXCEL_DIRECTORY,
    data_instances,
    export_data,
    prepare_export_data,
)


@pytest.fixture()
def mock_export_data(statement_basic):
    prepare_export_data(statement_basic)
    return data_instances


def test_prepare_export_data(mock_export_data, statement_basic):
    assert len(mock_export_data) == 9, "Expected 9 data instances, but got a different number."

    # Check if the export data was prepared correctly (this would depend on the implementation of prepare_export_data)
    # This is a placeholder assertion; actual checks would depend on what prepare_export_data does
    assert mock_export_data[0].id_statement == statement_basic.id, (
        "First data instance should match the statement ID."
    )  # Ensure the first instance has the correct statement ID
    assert mock_export_data[0].account_name == statement_basic.account_name, (
        "First data instance should have the correct account name."
    )  # Ensure the first instance has the correct account name
    assert mock_export_data[0].page_number == 1, "First data instance should be on page 1."  # Ensure the first instance is on page 1
    assert mock_export_data[0].transaction_number == 1, (
        "First data instance should be the first transaction."
    )  # Ensure the first instance is the first transaction
    assert mock_export_data[0].type_transaction == "BP", (
        "First data instance should be a bill payment transaction."
    )  # Ensure the first instance is a bill payment transaction
    assert mock_export_data[0].value == -30, (
        "First data instance should have the correct value."
    )  # Ensure the first instance has the correct value
    assert mock_export_data[0].closing_balance == 626.04, (
        "First data instance should have the correct closing balance."
    )  # Ensure the first instance has the correct closing balance
    assert mock_export_data[0].description == "Grace Kelly", (
        "First data instance should have the correct description."
    )  # Ensure the first instance has the correct description


"""
define a test for the export_data function that checks if the data is exported correctly to CSV and Excel files.
it must also check the exportdirectories exist and contain the expected files.
"""


def test_export_data(mock_export_data):
    # Check if the export directories exist
    assert EXPORT_CSV_DIRECTORY.exists(), f"CSV export directory {EXPORT_CSV_DIRECTORY} does not exist."
    assert EXPORT_EXCEL_DIRECTORY.exists(), f"Excel export directory {EXPORT_EXCEL_DIRECTORY} does not exist."

    export_info = export_data()  # Call the export function to create the files and return the timestamp

    file_csv = str(export_info.export_csv).replace(f"{EXPORT_CSV_DIRECTORY}/", "")
    file_excel = str(export_info.export_excel).replace(f"{EXPORT_EXCEL_DIRECTORY}/", "")

    # Check if the CSV file was created
    csv_files = listdir(EXPORT_CSV_DIRECTORY)
    assert file_csv in csv_files, f"CSV file {file_csv} does not exist."

    # Check if the Excel file was created
    excel_files = listdir(EXPORT_EXCEL_DIRECTORY)
    assert file_excel in excel_files, f"Excel file {file_excel} does not exist."

    # Optionally, you can check the content of the files, but this is more complex and requires reading the files.
    df_csv = pl.read_csv(export_info.export_csv)
    df_excel = pl.read_excel(export_info.export_excel)

    assert df_csv[0, "description"] == mock_export_data[0].description  # Check if the first description matches the expected value
    assert df_excel[0, "description"] == mock_export_data[0].description  # Check if the first description matches the expected value
    assert (
        df_csv[5, "opening_balance"] == mock_export_data[5].opening_balance
    )  # Check if the first opening balance matches the expected value
    assert (
        df_excel[5, "opening_balance"] == mock_export_data[5].opening_balance
    )  # Check if the first opening balance matches the expected value
    assert len(df_csv) == len(mock_export_data), "CSV file should have the same number of rows as data instances."
    assert len(df_excel) == len(mock_export_data), "Excel file should have the same number of rows as data instances."
    assert round(df_csv[4, "closing_balance"], 2) == round(mock_export_data[4].closing_balance, 2), (
        "CSV file should have the correct closing balance for the 5th transaction."
    )
    assert round(df_excel[4, "closing_balance"], 2) == round(mock_export_data[4].closing_balance, 2), (
        "Excel file should have the correct closing balance for the 5th transaction."
    )
    assert sum(df_csv["value"].round(2)) == sum([round(transaction.value, 2) for transaction in mock_export_data]), (
        "CSV file should have the correct total value."
    )
    assert sum(df_excel["value"].round(2)) == sum([round(transaction.value, 2) for transaction in mock_export_data]), (
        "Excel file should have the correct total value."
    )

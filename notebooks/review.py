import marimo

__generated_with = "0.13.15"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell
def setup_1():
    # Initialization code that runs before all other cells
    import os

    # imports
    import marimo as mo
    import matplotlib.pyplot as plt

    from bstec.modules import (
        EXPORT_CSV_DIRECTORY,
        LOG_DIRECTORY,
    )

    # # Get my_package directory path from Notebook
    # parent_dir = str(Path().resolve().parents[0])
    # sys.path.insert(0, parent_dir)
    # print(f"Parent directory: {parent_dir}")

    # from src.modules import Statement  # noqa: E402
    # from modules import Statement

    files_log = os.listdir(LOG_DIRECTORY)
    files_exports = os.listdir(EXPORT_CSV_DIRECTORY)
    paths_log = [os.path.join(LOG_DIRECTORY, basename) for basename in files_log if basename.endswith(".csv")]
    paths_exports = [os.path.join(EXPORT_CSV_DIRECTORY, basename) for basename in files_exports if basename.endswith(".csv")]
    latest_log = max(paths_log, key=os.path.getctime)
    latest_export = max(paths_exports, key=os.path.getctime)
    plt.rcParams["figure.figsize"] = [12, 6]
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    return latest_export, latest_log, mo, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    # Review

    ## 📋 Latest Import Log
    """
    )
    return


@app.cell(hide_code=True)
def _(latest_log, mo):
    mo.sql(f"""
    SELECT * FROM read_csv('{latest_log}')
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""##🧮 Latest Transaction Data""")
    return


@app.cell(hide_code=True)
def _(latest_export, mo):
    df_credits_top10 = mo.sql(
        f"""
        SELECT account, UPPER(description) as description, SUM(value) as Credit_Value FROM read_csv('{latest_export}') CSV
        WHERE credit_debit = 'Credit' and type_transaction <> 'TFR'
        GROUP BY account, description
        ORDER BY Credit_Value DESC
        LIMIT 10
        """,
        output=False,
    )
    return (df_credits_top10,)


@app.cell(hide_code=True)
def _(latest_export, mo):
    mo.sql(f"""
    SELECT * FROM read_csv('{latest_export}')
    """)
    return


@app.cell(hide_code=True)
def _(latest_export, mo):
    df_debits_top10 = mo.sql(
        f"""
        SELECT account, UPPER(description) as description, SUM(value*-1) as Debit_Value FROM read_csv('{latest_export}') CSV
        WHERE credit_debit = 'Debit' and type_transaction <> 'TFR'
        GROUP BY account, description
        ORDER BY Debit_Value DESC
        LIMIT 10
        """,
        output=False,
    )
    return (df_debits_top10,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""##📈 Incomings""")
    return


@app.cell(hide_code=True)
def _(df_credits_top10, plt):
    # print(df_credits_top10)
    df_credits_top10.sort_values(by="Credit_Value", ascending=True, inplace=True)
    _fig, _ax = plt.subplots(figsize=(12, 6))
    _ax.spines["top"].set_visible(False)
    # Customize the plot
    _ax.xaxis.set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    _ax.set_title("Top 10 Credit Transactions by Description")
    _ax.set_xlabel("Value")
    _ax.set_ylabel("Transaction Description")
    _ax.grid(True, linestyle="--", alpha=0.7)
    _ax.barh(df_credits_top10.description, df_credits_top10.Credit_Value, color="navy")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""##📉 Outgoings""")
    return


@app.cell(hide_code=True)
def _(df_debits_top10, plt):
    # print(df_credits_top10)
    df_debits_top10.sort_values(by="Debit_Value", ascending=True, inplace=True)
    _fig, _ax = plt.subplots(figsize=(12, 6))
    _ax.spines["top"].set_visible(False)
    # Customize the plot
    _ax.xaxis.set_major_formatter(plt.matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    _ax.set_title("Top 10 Debit Transactions by Description")
    _ax.set_xlabel("Value")
    _ax.set_ylabel("Transaction Description")
    _ax.grid(True, linestyle="--", alpha=0.7)
    _ax.barh(df_debits_top10.description, df_debits_top10.Debit_Value, color="navy")
    return


if __name__ == "__main__":
    app.run()

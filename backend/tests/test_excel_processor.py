import io
import pandas as pd

from services.excel_processor import ExcelProcessor


def _write_excel_bytes(df_dict):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, df in df_dict.items():
            df.to_excel(writer, sheet_name=name, index=False)
    buf.seek(0)
    return buf.getvalue()


def test_extract_amount_various_formats():
    ep = ExcelProcessor()
    assert ep._extract_amount("1,234.56") == 1234.56
    assert ep._extract_amount("(1,234.56)") == -1234.56
    assert ep._extract_amount("1234") == 1234.0
    assert ep._extract_amount("1,234 CR") == 1234.0
    assert ep._extract_amount("1,234 DR") == 1234.0
    assert ep._extract_amount(1234) == 1234.0


def test_extract_transactions_detects_amount_column_and_parses_values():
    ep = ExcelProcessor()

    df = pd.DataFrame([
        {"Date": "01/01/2025", "Description": "Salary", "Amount": "50,000"},
        {"Date": "05/01/2025", "Description": "Grocery", "Amount": "(2,500)"},
        {"Date": "06/01/2025", "Description": "UPI from JOHN@OKBANK", "Amount": "1,200 CR"}
    ])

    xls = _write_excel_bytes({"Sheet1": df})
    txns = ep.extract_transactions(xls, "test.xlsx")

    # Expect 3 transactions with proper credit/debit interpretation
    assert len(txns) == 3

    # First: credit 50000
    assert any(t["credit"] == 50000.0 and t["debit"] == 0.0 for t in txns)
    # Second: debit 2500
    assert any(t["debit"] == 2500.0 and t["credit"] == 0.0 for t in txns)
    # Third: credit parsed from CR
    assert any(t["credit"] == 1200.0 for t in txns)


def test_extract_transactions_with_crdr_indicator():
    ep = ExcelProcessor()
    # Some statements have an AMOUNT column and a separate CR/DR column
    df = pd.DataFrame([
        {"Date": "01/01/2025", "Narration": "Salary", "Amount": "50,000", "Cr/Dr": "CR"},
        {"Date": "05/01/2025", "Narration": "Grocery", "Amount": "2,500", "Cr/Dr": "DR"},
    ])

    xls = _write_excel_bytes({"Sheet1": df})
    txns = ep.extract_transactions(xls, "test2.xlsx")
    assert len(txns) == 2
    assert any(t["credit"] == 50000.0 for t in txns)
    assert any(t["debit"] == 2500.0 for t in txns)

"""CSV loading helpers for TAIVAS.

Returns structured warnings instead of raising UI-level exceptions.
"""

import pandas as pd


def read_csv_with_warnings(uploaded_file):
    """Read a CSV-like file object and return (dataframe_or_none, warnings)."""
    warnings = []
    if uploaded_file is None:
        return None, warnings
    try:
        df = pd.read_csv(uploaded_file)
    except pd.errors.EmptyDataError:
        return None, ["Uploaded CSV appears empty or unreadable. TAIVAS will continue with default/manual inputs."]
    except pd.errors.ParserError:
        return None, ["Uploaded CSV could not be parsed cleanly. Please review the file structure."]
    except Exception as exc:
        return None, [f"CSV read failed: {exc}"]

    if df.empty:
        return None, ["Uploaded CSV is empty. TAIVAS will continue with default/manual inputs."]
    duplicate_columns = df.columns[df.columns.duplicated()].tolist()
    if duplicate_columns:
        warnings.append("Uploaded CSV has duplicate column names. Some fields may require review.")
    return df, warnings

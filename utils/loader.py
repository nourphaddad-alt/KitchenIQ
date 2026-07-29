import pandas as pd


def load_file(uploaded_file):
    """
    Reads a CSV or Excel report
    and returns a pandas DataFrame.
    """

    if uploaded_file is None:
        return None

    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    elif filename.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)

    return None
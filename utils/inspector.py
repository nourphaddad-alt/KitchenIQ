def inspect_dataframe(data):

    return {
        "rows": data.shape[0],
        "columns": data.shape[1],
        "column_names": list(data.columns)
    }
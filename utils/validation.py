def validate_restaurant_name(restaurant_name):
    if not restaurant_name.strip():
        return False, "Please enter the restaurant name."

    return True, ""


def validate_required_columns(dataframe, required_columns):
    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        return (
            False,
            "The uploaded report is missing required columns: "
            + ", ".join(missing_columns),
        )

    return True, ""
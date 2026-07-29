from data.schemas.uber_eats import UBER_EATS_REQUIRED_COLUMNS


def validate_required_columns(dataframe, required_columns):
    missing = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing:
        return False, missing

    return True, []
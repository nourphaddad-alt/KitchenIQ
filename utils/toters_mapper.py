import pandas as pd

from data.schemas.toters import (
    TOTERS_REQUIRED_COLUMNS,
    TOTERS_CATEGORY_MAPPING,
)


def map_toters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts a Toters Invoice Report into the
    KitchenIQ canonical Toters structure.
    """

    # Check required columns
    missing = [
        column
        for column in TOTERS_REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing Toters columns: {missing}"
        )

    return df.copy()
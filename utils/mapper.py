from data.schemas.uber_eats import UBER_EATS_COLUMNS
from data.schemas.deliveroo import DELIVEROO_COLUMNS


def map_uber_eats(dataframe):
    dataframe = dataframe.rename(columns=UBER_EATS_COLUMNS)
    return dataframe


def map_deliveroo(dataframe):
    dataframe = dataframe.rename(columns=DELIVEROO_COLUMNS)
    return dataframe

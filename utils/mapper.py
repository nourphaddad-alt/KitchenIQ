from data.schemas.uber_eats import UBER_EATS_COLUMNS


def map_uber_eats(dataframe):
    dataframe = dataframe.rename(columns=UBER_EATS_COLUMNS)
    return dataframe
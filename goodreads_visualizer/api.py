import pandas as pd

try:
    from goodreads_visualizer import df_utils, db
except ModuleNotFoundError:
    import db
    import df_utils


def get_user_books_data(user_id, year):
    if year == "All time":
        user_data = db.get_user_books_data(user_id)
    else:
        user_data = db.get_user_books_data(user_id, year)

    user_df = pd.DataFrame(user_data)
    df_utils.format_df_datetimes(user_df)

    return user_df


def get_user_books_data_for_years(user_id, years):
    user_data = db.get_user_books_data_for_years(user_id, years)
    user_df = pd.DataFrame(user_data)
    df_utils.format_df_datetimes(user_df)

    return user_df

from typing import Union, Optional


import calendar
import numpy as np
import pandas as pd

# import requests


try:
    from goodreads_visualizer import page_parser, url_utils, df_utils, db, api, models
except ModuleNotFoundError:
    import api
    import db

    # import page_parser
    # import url_utils

YearType = Optional[Union[str, int]]


def get_user_data(user_id: Union[str, int], year: YearType) -> models.BookData:
    user_df = api.get_user_books_data(user_id, year)

    years = sorted(
        list(
            set(user_df[pd.notna(user_df["date_read"])]["date_read"].dt.strftime("%Y"))
        )
        + ["All time"],
        reverse=True,
    )
    years = sorted(db.get_user_years(user_id) + ["All time"], reverse=True)

    return (
        models.BookData(
            count=user_df.shape[0],
            max_rating=round(user_df["rating"].max()),
            average_rating=round(user_df["rating"].mean(), 1),
            average_length=round(user_df["num_pages"].mean(), 2),
            max_length=round(user_df["num_pages"].max()),
        ),
        years,
    )


def generate_distribution(data, nbins=15):
    # Find the min and max values for the data
    min_val, max_val = min(data), max(data)

    # Calculate the bin width using the range of data and the desired number of bins
    # The bin width should be a whole number, so we round up to ensure that all data fits into the bins
    range_val = max_val - min_val
    bin_width = max(int(np.ceil(range_val / nbins)), 1)  # Bin width at least 1

    # Calculate the bin edges, ensuring they are whole numbers
    bin_edges = np.arange(min_val, max_val, bin_width).tolist()

    # Add an extra bin edge to include the max value
    if bin_edges[-1] < max_val:
        bin_edges.append(bin_edges[-1] + bin_width)

    # Use numpy to calculate the histogram
    hist, _ = np.histogram(data, bins=bin_edges)

    # Create a list of tuples (bin_start, bin_end, count) to represent the distribution
    distribution = [
        (int(bin_edges[i]), int(bin_edges[i + 1]), hist[i]) for i in range(len(hist))
    ]

    return distribution


def books_read_by_month_data(df: pd.DataFrame) -> pd.DataFrame:
    # Group by month and count the number of books
    books_per_month = df.groupby(df["date_read"].dt.month).size().reset_index()
    books_per_month = (
        books_per_month.set_index("date_read")
        .reindex(range(1, 13), fill_value=0)
        .reset_index()
    )
    books_per_month.columns = ["date_read", "num_books"]
    books_per_month["date_read"] = books_per_month["date_read"].apply(
        lambda x: calendar.month_abbr[x]
    )

    books_per_month.columns = ["Month", "Number of Books"]
    return books_per_month


def books_read_by_month_graph_data(user_data_df: pd.DataFrame) -> models.GraphData:
    df = books_read_by_month_data(user_data_df)
    return models.GraphData(
        type="bar",
        labels=df["Month"].tolist(),
        x_axis_label="Month",
        y_axis_label="Books read",
        datasets=[
            models.Dataset(
                label="Books read",
                data=df["Number of Books"].tolist(),
                background_color="#068D9D",
                border_width=1,
            )
        ],
    )


def books_read_by_month_and_year(df: pd.DataFrame) -> pd.DataFrame:
    copy = df.copy()
    copy["month"] = copy["date_read"].apply(lambda x: calendar.month_abbr[x.month])
    copy["year"] = copy["date_read"].apply(lambda x: x.year)

    copy = copy.groupby(["month", "year"]).size().reset_index(name="count")
    return copy


def books_read_compared_to_year_data(
    user_id: Union[str, int], year: YearType, year_to_compare: YearType
) -> pd.DataFrame:
    years_ints = [int(year), int(year_to_compare)]
    user_data = api.get_user_books_data_for_years(user_id, years_ints)

    start_of_time_frame = pd.to_datetime(f"{year_to_compare}-01-01")
    end_of_time_frame = pd.to_datetime(f"{year}-12-31")
    all_months = pd.DataFrame(
        pd.date_range(start=start_of_time_frame, end=end_of_time_frame, freq="MS"),
        columns=["date_read"],
    )
    all_months = books_read_by_month_and_year(all_months)
    all_months["count"] = 0

    books_read_last_two_years_counts = books_read_by_month_and_year(user_data)

    both_dfs = pd.concat([all_months, books_read_last_two_years_counts])

    return both_dfs.groupby(["month", "year"])["count"].sum().reset_index()


def books_compared_to_year_graph_data(
    user_id: Union[str, int], year: YearType, year_to_compare: YearType
) -> models.GraphData:
    df = books_read_compared_to_year_data(user_id, year, year_to_compare)

    return models.GraphData(
        type="line",
        labels=list(set(df["month"].tolist())),
        datasets=[
            models.Dataset(
                label=f"Books read {year}",
                data=df[df["year"] == int(year)]["count"].tolist(),
                background_color="#93D5BD",
                border_width=3,
                border_color="#93D5BD",
            ),
            models.Dataset(
                label=f"Books read {year_to_compare}",
                data=df[df["year"] == int(year_to_compare)]["count"].tolist(),
                background_color="#43A5C9",
                border_width=3,
                border_color="#43A5C9",
            ),
        ],
    )


def book_length_distribution(user_data_df: pd.DataFrame) -> models.GraphData:
    distribution = generate_distribution(user_data_df["num_pages"].tolist())
    labels = [f"{x[0]}-{x[1]}" for x in distribution]

    return models.GraphData(
        type="bar",
        labels=labels,
        x_axis_label="Number of pages",
        y_axis_label="Number of books",
        datasets=[
            models.Dataset(
                label="Number of books",
                data=distribution,
                background_color="#53599A",
                border_width=1,
            )
        ],
        tooltip={"title": "Number of pages", "label": "Number of books"},
    )


def book_rating_distribution(user_data_df: pd.DataFrame) -> models.GraphData:
    rating_df = (
        user_data_df["rating"]
        .value_counts()
        .reindex(range(1, 6), fill_value=0)
        .reset_index()
    )

    return models.GraphData(
        type="bar",
        labels=rating_df["rating"].tolist(),
        x_axis_label="Book rating",
        y_axis_label="Number of books",
        datasets=[
            models.Dataset(
                label="Number of books",
                data=rating_df["count"].tolist(),
                background_color="#6D9DC5",
                border_width=1,
            )
        ],
        tooltip={"title": "Book rating", "label": "Number of books"},
    )


def book_publish_year_distribution(user_data_df: pd.DataFrame) -> models.GraphData:
    df_pub_dist = user_data_df[pd.notna(user_data_df["date_published"])][
        "date_published"
    ].reset_index()
    pub_date_list = [x.year for x in df_pub_dist["date_published"].tolist()]

    distribution = generate_distribution(pub_date_list)
    labels = [f"{x[0]}-{x[1]}" for x in distribution]

    return models.GraphData(
        type="bar",
        labels=labels,
        x_axis_label="Publication year",
        y_axis_label="Number of books",
        datasets=[
            models.Dataset(
                label="Number of books",
                data=distribution,
                background_color="#53599A",
                border_width=1,
            )
        ],
        tooltip={"title": "Publication year", "label": "Number of books"},
    )


def graphs_data_for_year(user_id: Union[str, int], year: YearType) -> models.GraphsData:
    year = year if year else pd.to_datetime("today").year

    user_data = api.get_user_books_data(user_id, year)
    user_data_df = pd.DataFrame(user_data)

    books_read_by_month = books_read_by_month_graph_data(user_data_df)
    books_read_compared_to_year = books_compared_to_year_graph_data(
        user_id, int(year), int(year) - 1
    )
    book_length_distribution_data = book_length_distribution(user_data)
    book_rating_distribution_data = book_rating_distribution(user_data)
    book_publish_year_distribution_data = book_publish_year_distribution(user_data)

    return models.GraphsData(
        books_read_this_year=books_read_by_month,
        books_read_compared_to_year=books_read_compared_to_year,
        book_length_distribution=book_length_distribution_data,
        book_rating_distribution=book_rating_distribution_data,
        book_publish_year_distribution=book_publish_year_distribution_data,
    )

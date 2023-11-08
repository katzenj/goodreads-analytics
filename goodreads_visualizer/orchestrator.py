from typing import Dict, List, Tuple, Union, Optional


import calendar
import numpy as np


try:
    from goodreads_visualizer import api, db, models, goodreads_api
except ModuleNotFoundError:
    import api
    import db
    import goodreads_api
    import models

YearType = Optional[Union[str, int]]


def get_user_data(user_id: Union[str, int], selected_year: YearType) -> models.BookData:
    if selected_year == "All time":
        year = None
    else:
        year = selected_year

    last_sync_date = api.get_last_sync_date(user_id)
    read_books = []
    if last_sync_date is None:
        _res = sync_user_data(user_id)

    read_books = api.get_read_books_for_user(user_id, year)

    ratings = [book.rating for book in read_books if book.rating is not None]
    num_pages = [book.num_pages for book in read_books if book.num_pages is not None]
    years = sorted(db.get_user_years(user_id) + ["All time"], reverse=True)

    return (
        models.BookData(
            count=len(read_books),
            max_rating=round(max(ratings)),
            average_rating=round(np.mean(ratings), 1),
            average_length=round(np.mean(num_pages), 2),
            max_length=round(max(num_pages)),
        ),
        years,
    )


def graphs_data_for_year(
    user_id: Union[str, int], selected_year: YearType
) -> models.GraphsData:
    if selected_year == "All time":
        year = None
    else:
        year = selected_year

    read_books = api.get_read_books_for_user(user_id, year)

    books_read_by_month = _books_read_by_month_graph_data(read_books)

    books_read_compared_to_year = None
    if year is not None:
        books_read_compared_to_year = _books_compared_to_year_graph_data(
            user_id, int(year), int(year) - 1
        )

    book_length_distribution_data = _book_length_distribution(read_books)
    book_rating_distribution_data = _book_rating_distribution(read_books)
    book_publish_year_distribution_data = _book_publish_year_distribution(read_books)

    return models.GraphsData(
        books_read=books_read_by_month,
        books_read_compared_to_year=books_read_compared_to_year,
        book_length_distribution=book_length_distribution_data,
        book_rating_distribution=book_rating_distribution_data,
        book_publish_year_distribution=book_publish_year_distribution_data,
    )


def sync_user_data(user_id: Union[str, int]) -> None:
    books_data = goodreads_api.fetch_books_data(user_id)
    res = api.upsert_data(user_id, books_data)
    return res


# PRIVATE FUNCTIONS


def _generate_distribution(data, nbins=15):
    # Find the min and max values for the data
    min_val, max_val = min(data), max(data)

    # Calculate the bin width using the range of data and the desired number of bins
    # The bin width should be a whole number, so we round up to ensure that all data
    # fits into the bins
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


def _books_read_by_month_graph_data(books: List[models.Book]) -> models.GraphData:
    counts = [0] * 12
    for book in books:
        idx = book.date_read.month - 1
        counts[idx] += 1

    return models.GraphData(
        type="bar",
        labels=calendar.month_abbr[1:],
        x_axis_label="Month",
        y_axis_label="Books read",
        datasets=[
            models.Dataset(
                label="Books read",
                data=counts,
                background_color="#068D9D",
                border_width=1,
            )
        ],
    )


def _books_read_compared_to_year_data(
    user_id: Union[str, int], year: YearType, year_to_compare: YearType
) -> Dict[Tuple[str, int], int]:
    years_ints = [int(year), int(year_to_compare)]
    user_data = api.get_user_books_data_for_years(user_id, years_ints)
    month_year_counts = {
        (calendar.month_abbr[month], year): 0
        for month in range(1, 13)
        for year in years_ints
    }

    for data in user_data:
        month_year_counts[
            (calendar.month_abbr[data.date_read.month], data.date_read.year)
        ] += 1

    return month_year_counts


def _books_compared_to_year_graph_data(
    user_id: Union[str, int], year: YearType, year_to_compare: YearType
) -> models.GraphData:
    data = _books_read_compared_to_year_data(user_id, year, year_to_compare)

    year_one_data = [data[(month, year)] for month in calendar.month_abbr[1:]]
    year_two_data = [
        data[(month, year_to_compare)] for month in calendar.month_abbr[1:]
    ]
    return models.GraphData(
        type="line",
        labels=calendar.month_abbr[1:],
        datasets=[
            models.Dataset(
                label=f"Books read {year}",
                data=year_one_data,
                background_color="#93D5BD",
                border_width=3,
                border_color="#93D5BD",
            ),
            models.Dataset(
                label=f"Books read {year_to_compare}",
                data=year_two_data,
                background_color="#43A5C9",
                border_width=3,
                border_color="#43A5C9",
            ),
        ],
    )


def _book_length_distribution(read_books: List[models.Book]) -> models.GraphData:
    distribution = _generate_distribution(
        [book.num_pages for book in read_books if book.num_pages is not None]
    )
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


def _book_rating_distribution(read_books: List[models.Book]) -> models.GraphData:
    rating_counts = [0] * 5
    for book in read_books:
        if book.rating is None:
            continue

        rating_counts[book.rating - 1] += 1

    return models.GraphData(
        type="bar",
        labels=list(range(1, 6)),
        x_axis_label="Book rating",
        y_axis_label="Number of books",
        datasets=[
            models.Dataset(
                label="Number of books",
                data=rating_counts,
                background_color="#6D9DC5",
                border_width=1,
            )
        ],
        tooltip={"title": "Book rating", "label": "Number of books"},
    )


def _book_publish_year_distribution(read_books: List[models.Book]) -> models.GraphData:
    published_years = [
        book.date_published.year
        for book in read_books
        if book.date_published is not None
    ]
    distribution = _generate_distribution(published_years)
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

from datetime import datetime
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


def get_user_books_data(
    user_id: Union[str, int], selected_year: YearType
) -> models.BookData:
    if selected_year == "All time":
        year = None
    else:
        year = selected_year

    last_sync_date = api.get_last_sync_date(user_id)
    read_books = []
    if last_sync_date is None:
        sync_user_name(user_id)
        sync_user_data(user_id)

    read_books = api.get_read_books_for_user(user_id, year)

    ratings = [book.rating for book in read_books if book.rating is not None]
    num_pages = [book.num_pages for book in read_books if book.num_pages is not None]
    min_rated_book = _optional_min_rated_book(read_books)
    max_rated_book = _optional_max_rated_book(read_books)
    longest_book = _optional_longest_book(read_books)
    shortest_book = _optional_shortest_book(read_books)

    return models.BookData(
        count=len(read_books),
        total_pages=f"{sum(num_pages):,}",
        max_rated_book=max_rated_book,
        min_rated_book=min_rated_book,
        max_rating=_optional_rounded_max(ratings),
        min_rating=_optional_rounded_min(ratings),
        average_rating=round(np.mean(ratings), 1),
        average_length=round(np.mean(num_pages)),
        max_length=_optional_rounded_max(num_pages),
        longest_book=longest_book,
        shortest_book=shortest_book,
        list=sorted(read_books, key=lambda x: x.date_read, reverse=True),
    )


def get_user_name(user_id: Union[str, int]) -> str:
    return api.get_user_name(user_id)


def get_user_years(user_id: Union[str, int]) -> List[str]:
    extra_years = ["All time", str(datetime.now().year)]
    return sorted(set(db.get_user_years(user_id) + extra_years), reverse=True)


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


def sync_user_data(user_id: Union[str, int]) -> bool:
    # api.delete_cached_dashboard(user_id)
    books_data = goodreads_api.fetch_books_data(user_id)
    return api.upsert_books_data(user_id, books_data)


def sync_user_name(user_id: Union[str, int]) -> bool:
    user_name = goodreads_api.fetch_user_name(user_id)
    return api.upsert_user_name(user_id, user_name)


def fetch_cached_dashboard(
    user_id: Union[str, int], year: Optional[Union[str, int]]
) -> Optional[models.Dashboard]:
    res_dict = api.fetch_cached_dashboard(user_id, year)

    graphs_dict = res_dict["graphs"]
    metrics_dict = res_dict["metrics"]

    return models.Dashboard(
        metrics=models.BookData.from_dict(metrics_dict),
        graphs=models.GraphsData.from_dict(graphs_dict),
    )


def upsert_dashboard(
    user_id: Union[str, int],
    year: Optional[Union[str, int]],
    metrics: models.BookData,
    graphs: models.GraphsData,
) -> bool:
    dashboard = models.Dashboard(metrics=metrics, graphs=graphs)
    return api.upsert_dashboard(user_id, year, dashboard)


# PRIVATE FUNCTIONS


def _optional_rounded_max(data: List[Optional[int]]) -> Optional[int]:
    if len(data) == 0:
        return None

    return round(max(data))


def _optional_min_rated_book(data: List[models.Book]) -> Optional[models.Book]:
    if len(data) == 0:
        return None

    min_rating = min([book.rating for book in data if book.rating is not None])
    min_rated_books = [book for book in data if book.rating == min_rating]

    # Get lowest rated book that was read latest.
    return max(min_rated_books, key=lambda x: x.date_read)


def _optional_max_rated_book(data: List[models.Book]) -> Optional[models.Book]:
    if len(data) == 0:
        return None

    return max(data, key=lambda x: (x.rating, x.date_read))


def _optional_longest_book(data: List[models.Book]) -> Optional[models.Book]:
    if len(data) == 0:
        return None

    return max(data, key=lambda x: x.num_pages)


def _optional_shortest_book(data: List[models.Book]) -> Optional[models.Book]:
    if len(data) == 0:
        return None

    return min(data, key=lambda x: x.num_pages)


def _optional_rounded_min(data: List[Optional[int]]) -> Optional[int]:
    if len(data) == 0:
        return None

    return round(min(data))


def _generate_distribution(data, nbins=15):
    if len(data) == 0:
        return []

    if len(data) == 1:
        return [(data[0], data[0], 1)]

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
        (int(bin_edges[i]), int(bin_edges[i + 1]), int(hist[i]))
        for i in range(len(hist))
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

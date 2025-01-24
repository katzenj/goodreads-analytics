import calendar
from datetime import datetime
from typing import Dict, List, Optional, Tuple, cast

import numpy as np

try:
    from goodreads_visualizer import models
except ModuleNotFoundError:
    from . import models


def get_user_books_data(
    books: List[models.Book], year: Optional[int]
) -> models.BookData:
    read_books = []
    if year is not None:
        for book in books:
            if book.date_read is None:
                continue
            elif int(book.date_read.year) == int(year):
                read_books.append(book)

    ratings = [book.rating for book in read_books if book.rating is not None]
    num_pages = [book.num_pages for book in read_books if book.num_pages is not None]
    min_rated_book = _optional_min_rated_book(read_books)
    max_rated_book = _optional_max_rated_book(read_books)
    longest_book = _optional_longest_book(read_books)
    shortest_book = _optional_shortest_book(read_books)
    average_rating = round(np.mean(ratings)) if len(ratings) > 0 else 0
    average_length = round(np.mean(num_pages)) if len(num_pages) > 0 else 0

    return models.BookData(
        count=len(read_books),
        total_pages=f"{sum(num_pages):,}",
        max_rated_book=max_rated_book,
        min_rated_book=min_rated_book,
        max_rating=_optional_rounded_max(ratings),
        min_rating=_optional_rounded_min(ratings),
        average_rating=str(average_rating),
        average_length=str(average_length),
        max_length=_optional_rounded_max(num_pages),
        longest_book=longest_book,
        shortest_book=shortest_book,
        list=sorted(read_books, key=lambda x: x.date_read, reverse=True),
    )


def graphs_data_for_year(
    all_read_books: List[models.Book], year: Optional[int] = None
) -> models.GraphsData:
    read_books = []
    if year is not None:
        for book in all_read_books:
            if book.date_read is None:
                continue
            elif int(book.date_read.year) == int(year):
                read_books.append(book)

    if year is not None:
        read_books_this_year = [
            book for book in read_books if int(book.date_read.year) == int(year)
        ]
        read_books_both_years = [
            book
            for book in read_books
            if int(book.date_read.year) in [int(year), int(year) - 1]
        ]
    else:
        read_books_this_year = all_read_books
        read_books_both_years = all_read_books

    books_read_by_month = _books_read_by_month_graph_data(read_books_this_year)

    books_read_compared_to_year = None
    if year is not None:
        books_read_compared_to_year = _books_compared_to_year_graph_data(
            read_books_both_years, int(year), int(year) - 1
        )

    book_length_distribution_data = _book_length_distribution(read_books_this_year)
    book_rating_distribution_data = _book_rating_distribution(read_books_this_year)
    book_publish_year_distribution_data = _book_publish_year_distribution(
        read_books_this_year
    )

    return models.GraphsData(
        books_read=books_read_by_month,
        books_read_compared_to_year=books_read_compared_to_year,
        book_length_distribution=book_length_distribution_data,
        book_rating_distribution=book_rating_distribution_data,
        book_publish_year_distribution=book_publish_year_distribution_data,
    )


# PRIVATE FUNCTIONS


def _optional_rounded_max(data: List[Optional[int]]) -> Optional[int]:
    filtered = [x for x in data if x is not None]
    if len(data) == 0:
        return None

    return round(max(filtered))


def _optional_min_rated_book(data: List[models.Book]) -> Optional[models.Book]:
    if len(data) == 0:
        return None

    min_rating = min([book.rating for book in data if book.rating is not None])
    min_rated_books = cast(
        List[models.Book], [book for book in data if book.rating == min_rating]
    )

    # Get lowest rated book that was read latest.
    return max(min_rated_books, key=lambda x: cast(datetime, x.date_read))


def _optional_max_rated_book(data: List[models.Book]) -> Optional[models.Book]:
    if len(data) == 0:
        return None
    filtered = [book for book in data if book.rating is not None]

    return max(filtered, key=lambda x: (x.rating, x.date_read))


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

    return round(min(cast(List[int], data)))


def _generate_distribution(data, nbins=None):
    if len(data) == 0:
        return []

    if len(data) == 1:
        return [(data[0], data[0], 1)]

    # Find the min and max values for the data
    min_val, max_val = min(data), max(data)
    range_val = max_val - min_val

    # Determine the number of bins if not specified
    if nbins is None:
        # Freedman-Diaconis rule: bin width = 2 * IQR * n^(-1/3)
        # Alternatively, Sturges' formula: bin count = log2(n) + 1
        q75, q25 = np.percentile(data, [75, 25])
        iqr = q75 - q25
        bin_width = (2 * iqr) / (len(data) ** (1 / 3))
        nbins = max(int(range_val / bin_width), 1)

    # Calculate the bin edges
    bin_edges = np.linspace(min_val, max_val, nbins + 1)

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
        if book.date_read is None:
            continue

        idx = book.date_read.month - 1
        counts[idx] += 1

    return models.GraphData(
        type="bar",
        labels=list(calendar.month_abbr[1:]),
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
    read_books: List[models.Book], year: int, year_to_compare: int
) -> Dict[Tuple[str, int], int]:
    years_ints = [int(year), int(year_to_compare)]
    month_year_counts = {
        (calendar.month_abbr[month], year): 0
        for month in range(1, 13)
        for year in years_ints
    }

    for book in read_books:
        if book.date_read is None:
            continue
        month_year_counts[
            (calendar.month_abbr[book.date_read.month], book.date_read.year)
        ] += 1

    return month_year_counts


def _books_compared_to_year_graph_data(
    read_books: List[models.Book], year: int, year_to_compare: int
) -> models.GraphData:
    data = _books_read_compared_to_year_data(read_books, year, year_to_compare)

    year_one_data = [data[(month, year)] for month in calendar.month_abbr[1:]]
    year_two_data = [
        data[(month, year_to_compare)] for month in calendar.month_abbr[1:]
    ]
    return models.GraphData(
        type="line",
        labels=list(calendar.month_abbr[1:]),
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
        [book.num_pages for book in read_books if book.num_pages is not None], nbins=5
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
        labels=[str(x) for x in range(1, 6)],
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

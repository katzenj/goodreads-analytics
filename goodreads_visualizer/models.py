from datetime import date
from typing import Any, Dict, List, Optional

from dataclasses import dataclass, fields


@dataclass
class DataclassBase:
    @classmethod
    def class_fields(cls):
        return {field.name for field in fields(cls)}

    @classmethod
    def from_dict(cls, data):
        sliced = {k: v for k, v in data.items() if k in cls.class_fields()}
        return cls(**sliced)


@dataclass
class Book:
    title: str
    author: str
    date_read: Optional[date]
    date_added: date
    rating: Optional[int]
    num_pages: int
    avg_rating: float
    date_published: Optional[date]
    isbn: str

    @property
    def cover_url(self):
        return f"https://covers.openlibrary.org/b/isbn/{self.isbn}-M.jpg"

    @property
    def star_rating(self):
        if self.rating is None:
            return None

        # return "⭐" * self.rating
        stars = (
            """
        <svg width="20" height="16" viewBox="0 0 576 512" xmlns="http://www.w3.org/2000/svg">
            <path fill="#000000" d="M259.3 17.8L194 150.2L47.9 171.5c-26.2 3.8-36.7 36.1-17.7 54.6l105.7 103l-25 145.5c-4.5 26.3 23.2 46 46.4 33.7L288 439.6l130.7 68.7c23.2 12.2 50.9-7.4 46.4-33.7l-25-145.5l105.7-103c19-18.5 8.5-50.8-17.7-54.6L382 150.2L316.7 17.8c-11.7-23.6-45.6-23.9-57.4 0"/>
        </svg>
        """
            * self.rating
        )
        return f"""
            <div class="flex flex-row">
                {stars}
            </div>
            """

    def serialize(self):
        return {
            "title": self.title,
            "author": self.author,
            "date_read": self.date_read.isoformat() if self.date_read else None,
            "date_added": self.date_added.isoformat(),
            "rating": self.rating,
            "num_pages": self.num_pages,
            "avg_rating": self.avg_rating,
            "date_published": (
                self.date_published.isoformat() if self.date_published else None
            ),
            "isbn": self.isbn,
        }


@dataclass
class BookData(DataclassBase):
    count: int
    total_pages: str
    max_rating: Optional[int]
    max_rated_book: Optional[Book]
    min_rating: Optional[int]
    min_rated_book: Optional[Book]
    average_rating: Optional[str]
    average_length: Optional[str]
    max_length: Optional[int]
    longest_book: Optional[Book]
    shortest_book: Optional[Book]
    list: List[Book]

    def serialize(self):
        return {
            "count": self.count,
            "total_pages": self.total_pages,
            "max_rating": self.max_rating,
            "max_rated_book": self.max_rated_book.serialize(),
            "min_rating": self.min_rating,
            "min_rated_book": self.min_rated_book.serialize(),
            "average_rating": self.average_rating,
            "average_length": self.average_length,
            "max_length": self.max_length,
            "list": [book for book in self.list],
        }


@dataclass
class Dataset(DataclassBase):
    label: str
    data: List[Any]
    background_color: str = "#068D9D"
    border_width: int = 1
    border_color: str = None

    def serialize(self):
        return {
            "label": self.label,
            "data": self.data,
            "backgroundColor": self.background_color,
            "borderColor": self.border_color or "null",
            "borderWidth": self.border_width,
        }


@dataclass
class GraphData(DataclassBase):
    type: str
    labels: List[str]
    datasets: List[Dataset]
    x_axis_label: str = None
    y_axis_label: str = None
    tooltip: Dict[Any, Any] = None

    def serialize(self):
        return {
            "type": self.type,
            "x_axis_label": self.x_axis_label or "",
            "y_axis_label": self.y_axis_label or "",
            "labels": self.labels,
            "datasets": [dataset.serialize() for dataset in self.datasets],
            "tooltip": self.tooltip if self.tooltip else "",
        }

    @classmethod
    def from_dict(cls, data):
        # Deserialize datasets by calling Dataset.from_dict recursively
        data["datasets"] = [Dataset.from_dict(item) for item in data["datasets"]]
        return super().from_dict(data)


@dataclass
class GraphsData(DataclassBase):
    books_read: GraphData
    books_read_compared_to_year: GraphData = None
    book_length_distribution: GraphData = None
    book_rating_distribution: GraphData = None
    book_publish_year_distribution: GraphData = None

    def serialize(self):
        return {
            "books_read": self.books_read.serialize(),
            "books_read_compared_to_year": (
                self.books_read_compared_to_year.serialize()
                if self.books_read_compared_to_year
                else "null"
            ),
            "book_length_distribution": (
                self.book_length_distribution.serialize()
                if self.book_length_distribution
                else "null"
            ),
            "book_rating_distribution": (
                self.book_rating_distribution.serialize()
                if self.book_rating_distribution
                else "null"
            ),
            "book_publish_year_distribution": (
                self.book_publish_year_distribution.serialize()
                if self.book_publish_year_distribution
                else "null"
            ),
        }

    @classmethod
    def from_dict(cls, data):
        # Deserialize GraphData by calling GraphData.from_dict recursively
        data["books_read"] = GraphData.from_dict(data["books_read"])
        if data["books_read_compared_to_year"] is not None:
            data["books_read_compared_to_year"] = GraphData.from_dict(
                data["books_read_compared_to_year"]
            )
        if data["book_length_distribution"] is not None:
            data["book_length_distribution"] = GraphData.from_dict(
                data["book_length_distribution"]
            )
        if data["book_rating_distribution"] is not None:
            data["book_rating_distribution"] = GraphData.from_dict(
                data["book_rating_distribution"]
            )
        if data["book_publish_year_distribution"] is not None:
            data["book_publish_year_distribution"] = GraphData.from_dict(
                data["book_publish_year_distribution"]
            )
        return super().from_dict(data)


@dataclass
class Dashboard:
    metrics: BookData
    graphs: GraphsData

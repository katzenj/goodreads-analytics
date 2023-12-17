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
    read_count: Optional[int]
    date_published: Optional[date]
    date_started: Optional[date]
    cover_url: str
    user_id: int
    id: Optional[int]
    isbn: str
    review: str

    def serialize(self):
        return {
            "title": self.title,
            "author": self.author,
            "date_read": self.date_read.isoformat() if self.date_read else None,
            "date_added": self.date_added.isoformat(),
            "rating": self.rating,
            "num_pages": self.num_pages,
            "avg_rating": self.avg_rating,
            "read_count": self.read_count,
            "date_published": (
                self.date_published.isoformat() if self.date_published else None
            ),
            "date_started": (
                self.date_started.isoformat() if self.date_started else None
            ),
            "cover_url": self.cover_url,
            "user_id": self.user_id,
            "isbn": self.isbn,
            "review": self.review,
        }


@dataclass
class BookData(DataclassBase):
    count: str
    max_rating: str
    average_rating: str
    average_length: str
    max_length: str
    list: List[Book]

    def serialize(self):
        return {
            "count": self.count,
            "max_rating": self.max_rating,
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

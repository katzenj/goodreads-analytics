from typing import Any, Dict, List

from dataclasses import dataclass


@dataclass
class BookData:
    count: str
    max_rating: str
    average_rating: str
    average_length: str
    max_length: str

    def serialize(self):
        return {
            "count": self.count,
            "max_rating": self.max_rating,
            "average_rating": self.average_rating,
            "average_length": self.average_length,
            "max_length": self.max_length,
        }


@dataclass
class Dataset:
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
            "borderColor": "null" if self.border_color is None else self.border_color,
            "borderWidth": self.border_width,
        }


@dataclass
class GraphData:
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


@dataclass
class GraphsData:
    books_read_this_year: GraphData
    books_read_compared_to_year: GraphData = None
    book_length_distribution: GraphData = None
    book_rating_distribution: GraphData = None
    book_publish_year_distribution: GraphData = None

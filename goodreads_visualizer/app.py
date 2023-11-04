from typing import Any, List

import calendar
from flask import Flask, render_template, request
from dataclasses import dataclass

import os
import pandas as pd

# import requests
# import streamlit as st

# from dominate.tags import div, img, p
from dotenv import load_dotenv


if os.getenv("PYTHON_ENV") == "development":
    load_dotenv(".env.local")
else:
    load_dotenv(".env")


try:
    from goodreads_visualizer import page_parser, url_utils, df_utils, db, api
    from goodreads_visualizer.sections import BooksReadThisYear, BooksReadComparedToYear
except ModuleNotFoundError:
    import api
    import db

    # import page_parser
    # import url_utils


app = Flask(__name__)


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

    def serialize(self):
        return {
            "type": self.type,
            "labels": self.labels,
            "datasets": [dataset.serialize() for dataset in self.datasets],
        }


@dataclass
class GraphsData:
    books_read_this_year: GraphData
    books_read_compared_to_year: GraphData = None


def get_user_data(user_id, year):
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
        BookData(
            count=user_df.shape[0],
            max_rating=round(user_df["rating"].max()),
            average_rating=round(user_df["rating"].mean()),
            average_length=round(user_df["num_pages"].mean(), 2),
            max_length=round(user_df["num_pages"].max()),
        ),
        years,
    )


def books_read_by_month(df: pd.DataFrame) -> pd.DataFrame:
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


def books_read_by_month_and_year(df: pd.DataFrame) -> pd.DataFrame:
    copy = df.copy()
    copy["month"] = copy["date_read"].apply(lambda x: calendar.month_abbr[x.month])
    copy["year"] = copy["date_read"].apply(lambda x: x.year)

    copy = copy.groupby(["month", "year"]).size().reset_index(name="count")
    return copy


def books_compared_to_year_graph_data(user_id, year, year_to_compare):
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


def graphs_data_for_year(year):
    user_id = "142394620"
    user_data = api.get_user_books_data(user_id, year)
    books_by_month_df = books_read_by_month(pd.DataFrame(user_data))

    if year is None:
        year = pd.to_datetime("today").year

    books_compared_to_year = books_compared_to_year_graph_data(
        user_id, int(year), int(year) - 1
    )

    return GraphsData(
        books_read_this_year=GraphData(
            type="bar",
            labels=books_by_month_df["Month"].tolist(),
            datasets=[
                Dataset(
                    label="Books read",
                    data=books_by_month_df["Number of Books"].tolist(),
                    background_color="#068D9D",
                    border_width=1,
                )
            ],
        ),
        books_read_compared_to_year=GraphData(
            type="line",
            labels=list(set(books_compared_to_year["month"].tolist())),
            datasets=[
                Dataset(
                    label=f"Books read {year}",
                    data=books_compared_to_year[
                        books_compared_to_year["year"] == int(year)
                    ]["count"].tolist(),
                    background_color="#93D5BD",
                    border_width=3,
                    border_color="#93D5BD",
                ),
                Dataset(
                    label=f"Books read {int(year) - 1}",
                    data=books_compared_to_year[
                        books_compared_to_year["year"] == int(year) - 1
                    ]["count"].tolist(),
                    background_color="#43A5C9",
                    border_width=3,
                    border_color="#43A5C9",
                ),
            ],
        ),
    )


@app.route("/")
def index():
    user_id = "142394620"

    data, years = get_user_data(user_id, None)

    return render_template("index.html", years=years, data=data)


@app.route("/users/<user_id>")
def user_data(user_id):
    data, years = get_user_data(user_id, None)
    graphs_data = graphs_data_for_year(None)
    print()

    return render_template(
        "users/index.html", years=years, data=data, graphs_data=graphs_data
    )


@app.route("/refresh", methods=["GET", "POST"])
def refresh():
    user_id = "142394620"
    year = request.args.get("year")

    data, years = get_user_data(user_id, year)

    graphs_data = graphs_data_for_year(year)

    return render_template(
        "data_partial.html", years=years, data=data, graphs_data=graphs_data
    )

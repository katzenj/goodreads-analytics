from flask import Flask, render_template, request
from dataclasses import dataclass

# import altair as alt
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
    from goodreads_visualizer import page_parser, url_utils, df_utils, db
    from goodreads_visualizer.sections import BooksReadThisYear, BooksReadComparedToYear
except ModuleNotFoundError:
    import db
    import df_utils

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


def get_user_data(user_id, year):
    if year == "All time":
        user_data = db.get_user_books_data(user_id)
    else:
        user_data = db.get_user_books_data(user_id, year)

    user_df = pd.DataFrame(user_data)
    df_utils.format_df_datetimes(user_df)

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


@app.route("/")
def index():
    user_id = "142394620"

    data, years = get_user_data(user_id, None)

    return render_template("index.html", years=years, data=data)


@app.route("/refresh", methods=["GET", "POST"])
def refresh():
    user_id = "142394620"
    year = request.args.get("year")

    data, years = get_user_data(user_id, year)

    return render_template("data_partial.html", years=years, data=data)

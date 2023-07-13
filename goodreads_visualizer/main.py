from typing import Dict, Optional, Union
import os
import pandas as pd
import re
import requests
import streamlit as st
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from datetime import datetime
import calendar
import altair as alt

try:
    from goodreads_visualizer import page_parser, url_utils
except ModuleNotFoundError:
    import page_parser
    import url_utils


def convert_string_to_datetime(string: Optional[str]) -> Optional[datetime]:
    if string is None or pd.isna(string):
        return None

    date_fmt_one = re.match(r"\d{4}-\d{2}-\d{2}", string)
    if date_fmt_one:
        return datetime.strptime(date_fmt_one.group(), "%Y-%m-%d").date()

    date_fmt_two = re.match(r"\w{3}\s+(\d{1,2},)?\s{0,}\d{4}", string)
    if not date_fmt_two:
        return None

    if isinstance(string, datetime):
        return string

    matched_str = date_fmt_two.group()
    try:
        return datetime.strptime(matched_str, "%b %d, %Y").date()
    except ValueError:
        return datetime.strptime(matched_str, "%b %Y").date()


def format_goodreads_url(url: str, params: Dict[str, Union[str, int]] = {}) -> str:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params.update(params)

    if "print" not in query_params:
        query_params["print"] = ["true"]

    encoded_params = encoded_params = urlencode(query_params, doseq=True)
    modified_parts = list(parsed_url)
    modified_parts[4] = encoded_params
    return urlunparse(modified_parts)


def parse_url(url: str) -> str:
    parsed_url = urlparse(url)
    if parsed_url.startswith("/user/show"):
        user_id = parsed_url.path.split("/")[3]
    elif parsed_url.startswith("/review/list"):
        user_id = parsed_url.path.split("/")[3]
    else:
        raise ValueError("Invalid URL")
    return f"https://www.goodreads.com/review/list/{user_id}"


@st.cache_data(show_spinner=False)
def get_all_book_data(base_url: str) -> pd.DataFrame:
    request_url = url_utils.format_goodreads_url(base_url)
    response = requests.get(request_url)

    parser = page_parser.PageParser(response.text)
    last_page_number = parser.last_page_number()

    progress_bar = st.progress(1 / last_page_number, text="Loading your books...")

    all_data = []
    all_data.extend(parser.parse_page())

    # Start at 2, already parsed page 1
    for page_number in range(2, last_page_number + 1):
        progress_bar.progress(
            page_number / last_page_number,
            text="Loading your books...",
        )

        request_url = format_goodreads_url(base_url, {"page": page_number})
        print(f"Page number: {page_number}")
        print(f"URL: {request_url}")
        response = requests.get(request_url)
        print(f"Status Code: {response.status_code}")
        parser = page_parser.PageParser(response.text)
        all_data.extend(parser.parse_page())

    progress_bar.empty()

    return pd.DataFrame(all_data)


def format_df(df: pd.DataFrame) -> None:
    df["date_read"] = pd.to_datetime(df["date_read"].apply(convert_string_to_datetime))
    df["date_started"] = pd.to_datetime(
        df["date_started"].apply(convert_string_to_datetime)
    )
    df["date_pub"] = pd.to_datetime(df["date_pub"].apply(convert_string_to_datetime))
    df["date_added"] = pd.to_datetime(
        df["date_added"].apply(convert_string_to_datetime)
    )
    df["rating"] = df["rating"].apply(convert_rating_to_number)


def get_books_read_this_year(df: pd.DataFrame) -> pd.DataFrame:
    current_year = pd.to_datetime("today").year
    df_current_year = df[df["date_read"].dt.year == current_year]
    return df_current_year


def convert_rating_to_number(rating: Optional[Union[str, int, float]]) -> Optional[int]:
    if isinstance(rating, (int, float)):
        return rating

    if rating == "did not like it":
        return 1
    elif rating == "it was ok":
        return 2
    elif rating == "liked it":
        return 3
    elif rating == "really liked it":
        return 4
    elif rating == "it was amazing":
        return 5
    else:
        return None


@st.cache_data
def books_read_by_month(df: pd.DataFrame) -> pd.DataFrame:
    # Group by month and count the number of books
    books_per_month_current_year = (
        df.groupby(df["date_read"].dt.month).size().reset_index()
    )
    books_per_month_current_year = (
        books_per_month_current_year.set_index("date_read")
        .reindex(range(1, 13), fill_value=0)
        .reset_index()
    )
    books_per_month_current_year.columns = ["date_read", "num_books"]
    books_per_month_current_year["date_read"] = books_per_month_current_year[
        "date_read"
    ].apply(lambda x: calendar.month_abbr[x])

    books_per_month_current_year.columns = ["Month", "Number of Books"]
    return books_per_month_current_year


@st.cache_data
def books_read_by_month_and_year(df: pd.DataFrame) -> pd.DataFrame:
    copy = df.copy()
    copy["month"] = copy["date_read"].apply(lambda x: calendar.month_abbr[x.month])
    copy["year"] = copy["date_read"].apply(lambda x: x.year)

    copy = copy.groupby(["month", "year"]).size().reset_index(name="count")
    return copy


@st.cache_data
def download_df(df: pd.DataFrame, format: str) -> bytes:
    if format == "csv":
        return df.to_csv(index=False).encode("utf-8")
    elif format == "json":
        return df.to_json(orient="records").encode("utf-8")
    else:
        raise ValueError(f"Format {format} not supported.")


def show_data(df: pd.DataFrame) -> None:
    format_df(df)
    df

    # --- Download buttons ---
    st.download_button(
        "Download as CSV",
        download_df(df, "csv"),
        "goodreads_export.csv",
        "text/csv",
        key="download-csv",
    )
    st.download_button(
        "Download as JSON",
        download_df(df, "json"),
        "goodreads_export.json",
        "application/json",
        key="download-json",
    )

    # --- Current year's data ---
    current_year = pd.to_datetime("today").year
    df_read_current_year = df[df["date_read"].dt.year == current_year]
    books_per_month_current_year = books_read_by_month(df_read_current_year)

    row1_col1, _, row1_col2 = st.columns([0.4, 0.2, 0.4])
    with row1_col1:
        st.write("### Books Read This Year")
        chart = (
            alt.Chart(books_per_month_current_year)
            .mark_bar(color="#47AFAE")
            .encode(
                x=alt.X("Month", sort=list(books_per_month_current_year["Month"])),
                y="Number of Books",
            )
        )
        st.altair_chart(chart, use_container_width=True)

    with row1_col2:
        st.write("### Books Read Compared to Last Year")
        months = [calendar.month_abbr[i] for i in range(1, 13)]
        dates_and_counts = []
        for month in months:
            dates_and_counts.append([month, current_year - 1, 0])
            dates_and_counts.append([month, current_year, 0])

        base_df = pd.DataFrame(dates_and_counts, columns=["month", "year", "count"])
        books_last_two_years_df = df[
            df["date_read"].dt.year.isin([current_year - 1, current_year])
        ]
        books_read_last_two_years_counts = books_read_by_month_and_year(
            books_last_two_years_df
        )
        all_months_df = pd.concat([base_df, books_read_last_two_years_counts])

        month_year_count_df = (
            all_months_df.groupby(["month", "year"])["count"].sum().reset_index()
        )

        chart = (
            alt.Chart(month_year_count_df)
            .mark_line()
            .encode(
                x=alt.X("month", sort=months),
                y="count:Q",
                strokeWidth=alt.value(3),
                color=alt.Color(
                    "year:N",
                    scale=alt.Scale(scheme="greenblue"),
                ),
                tooltip=["month", "count"],
            )
        )

        st.altair_chart(chart)

    row2_col1, _, row2_col2 = st.columns([0.4, 0.2, 0.4])
    with row2_col1:
        st.write("### Book Length Distribution")

        df_page_dist = df["num_pages"].reset_index()
        bar = (
            alt.Chart(df_page_dist)
            .mark_bar()
            .encode(
                x=alt.X(
                    "num_pages",
                    title="Number of Pages",
                    bin=alt.Bin(maxbins=20),
                ),
                y=alt.Y(aggregate="count", title="Number of Books"),
            )
        )
        st.altair_chart(bar, use_container_width=True)

    with row2_col2:
        st.write("### Rating Distribution")

        df_rating = (
            df["rating"].value_counts().reindex(range(1, 6), fill_value=0).reset_index()
        )
        bar = (
            alt.Chart(df_rating)
            .mark_bar(width=50)
            .encode(
                x=alt.X(
                    "rating",
                    title="Book Rating",
                    scale=alt.Scale(domain=[1, 5]),
                    axis=alt.Axis(format="i", tickCount=5),
                ),
                y=alt.Y("count", title="Number of Books"),
            )
        )
        st.altair_chart(bar, use_container_width=True)


if __name__ == "__main__":
    st.set_page_config(page_title="Goodreads Analysis", layout="wide")

    st.write("# Goodreads Visualizer")
    goodreads_url = st.text_input(
        "Enter your Goodreads URL",
        key="goodreads-url",
        placeholder="https://www.goodreads.com/review/list/142394620-jordan?print=true",
    )

    if goodreads_url:
        df = get_all_book_data(goodreads_url)
        show_data(df)
    elif os.getenv("PYTHON_ENV") == "development" and st.button("Load Sample Data"):
        df = pd.read_csv("files/goodreads_export.csv")
        show_data(df)

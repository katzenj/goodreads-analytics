from typing import Any, Dict, List, Optional

import altair as alt
import os
import pandas as pd
import requests
import streamlit as st

from datetime import datetime, timedelta
from dateutil.parser import parse
from dominate.tags import div, img, p
from dotenv import load_dotenv
from supabase import create_client, Client


if os.getenv("PYTHON_ENV") == "development":
    load_dotenv(".env.local")
else:
    load_dotenv(".env")


try:
    from goodreads_visualizer import page_parser, url_utils, df_utils, upsert_utils
    from goodreads_visualizer.sections import BooksReadThisYear, BooksReadComparedToYear
except ModuleNotFoundError:
    from sections import BooksReadThisYear, BooksReadComparedToYear
    import df_utils
    import page_parser
    import upsert_utils
    import url_utils

ALL_COLUMNS = [
    "title",
    "author",
    "isbn",
    "date_read",
    "date_added",
    "rating",
    "num_pages",
    "avg_rating",
    "read_count",
    "date_published",
    "date_started",
    "review",
    "user_id",
]


url = os.getenv("SUPABASE_URL")
key = os.getenv("SERVICE_KEY")
supabase: Client = create_client(url, key)


@st.cache_data(show_spinner=False, ttl=600)
def get_all_book_data_cached(base_url: str) -> pd.DataFrame:
    return get_all_book_data(base_url)


def get_all_book_data(base_url: str) -> pd.DataFrame:
    request_url = url_utils.format_goodreads_url(base_url)
    user_id = url_utils.parse_user_id(base_url)
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

        request_url = url_utils.format_goodreads_url(base_url, {"page": page_number})
        response = requests.get(request_url)
        parser = page_parser.PageParser(response.text)
        all_data.extend(parser.parse_page())

    progress_bar.empty()

    df = pd.DataFrame(all_data)
    df["user_id"] = user_id
    return df


def show_data(df: pd.DataFrame) -> None:
    df_utils.format_df_datetimes(df)

    with st.expander("Show data in table"):
        df_reset_index = df[
            [
                "title",
                "author",
                "date_read",
                "date_added",
                "rating",
                "num_pages",
                "avg_rating",
                "read_count",
                "date_published",
            ]
        ].reset_index(drop=True)
        df_reset_index

        # --- Download buttons ---
        st.download_button(
            "Download as CSV",
            df_utils.download_df(df, "csv"),
            "goodreads_export.csv",
            "text/csv",
            key="download-csv",
        )
        st.download_button(
            "Download as JSON",
            df_utils.download_df(df, "json"),
            "goodreads_export.json",
            "application/json",
            key="download-json",
        )

    current_year = pd.to_datetime("today").year

    # --- Year in Review ---
    st.write("<hr/>", unsafe_allow_html=True)
    st.write("### Year in Review")
    dates = list(set(df[pd.notna(df["date_read"])]["date_read"].dt.strftime("%Y")))
    dates.sort(reverse=True)

    year = st.selectbox("Year", dates, index=0)
    df_read_year = df[df["date_read"].dt.year == int(year)]
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Books read", df_read_year.shape[0])
        st.metric(
            "Average book length", f'{int(df_read_year["num_pages"].mean())} pages'
        )

        with st.expander(f"Show all books read in {year}"):
            div_ele = div(class_name="book-list")
            for row in df_read_year.sort_values(by="date_read").iterrows():
                row_values = row[1]
                list_div = div(class_name="book-list-item")
                list_div.add(img(src=row_values["cover_url"]))
                list_div.add(p(f"{row_values['title']} by {row_values['author']}"))
                div_ele.add(list_div)

            st.write(str(div_ele), unsafe_allow_html=True)

    with col2:
        st.metric("Average book rating", round(df_read_year["rating"].mean(), 2))
        highest_rated_books = df_read_year[
            df_read_year["rating"] == df_read_year["rating"].max()
        ]
        title = (
            "Highest rated books"
            if len(highest_rated_books["title"]) > 1
            else "Highest rated book"
        )
        st.metric("Highest rating", highest_rated_books["rating"].max())

        with st.expander(title):
            for row in highest_rated_books.iterrows():
                cover_url = row[1]["cover_url"]
                rated_title = row[1]["title"]
                st.write(f"- {rated_title}")
                if cover_url is not None and pd.notna(cover_url):
                    st.image(cover_url)

    # --- Current year's data ---
    current_year = pd.to_datetime("today").year

    st.write("<hr/>", unsafe_allow_html=True)
    row1_col1, _, row1_col2 = st.columns([0.4, 0.1, 0.4])
    with row1_col1:
        df_read_current_year = df[df["date_read"].dt.year == current_year]
        BooksReadThisYear(df_read_current_year).render_section()

    with row1_col2:
        BooksReadComparedToYear(df, current_year, current_year - 1).render_section()

    st.write("<hr/>", unsafe_allow_html=True)
    row2_col1, _, row2_col2 = st.columns([0.4, 0.1, 0.4])
    with row2_col1:
        st.write("### Book Length Distribution")

        df_page_dist = df["num_pages"].reset_index()
        bar = (
            alt.Chart(df_page_dist)
            .mark_bar(color="#53599A")
            .encode(
                x=alt.X(
                    "num_pages",
                    title="Number of Pages",
                    bin=alt.Bin(maxbins=20),
                ),
                y=alt.Y(aggregate="count", title="Number of Books"),
            )
        )
        st.altair_chart(bar)

    with row2_col2:
        st.write("### Rating Distribution")

        df_rating = (
            df["rating"].value_counts().reindex(range(1, 6), fill_value=0).reset_index()
        )
        bar = (
            alt.Chart(df_rating)
            .mark_bar(width=50, color="#6D9DC5")
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
        st.altair_chart(bar)

    st.write("<hr/>", unsafe_allow_html=True)
    row3_col1, _, row3_col2 = st.columns([0.4, 0.1, 0.4])
    with row3_col1:
        st.write("### Book Publish Year Distribution")
        df_pub_dist = df[pd.notna(df["date_published"])]["date_published"].reset_index()
        bar = (
            alt.Chart(df_pub_dist)
            .mark_bar(color="#80DED9", width=5)
            .encode(
                x=alt.X(
                    "date_published",
                    title="Year Published",
                    timeUnit="year",
                ),
                y=alt.Y(aggregate="count", title="Number of Books"),
            )
        )
        st.altair_chart(bar)


def load_data_for_user_from_db(user_id: int) -> List[Dict[str, Any]]:
    res = supabase.table("books").select("*").eq("user_id", user_id).execute()
    return res.data


def get_last_sync_date(user_id):
    last_sync = (
        supabase.table("syncs")
        .select("*")
        .eq("user_id", user_id)
        .order("id", desc=True)
        .limit(1)
        .execute()
        .data
    )

    if last_sync is None or len(last_sync) == 0:
        return None

    return parse(last_sync[0]["created_at"]).replace(tzinfo=None)


def load_synced_user_data(user_id):
    last_sync_date = get_last_sync_date(user_id)
    if last_sync_date is None:
        return False

    # Last synced less than a day ago
    return last_sync_date >= datetime.now() - timedelta(days=1)


def load_data_for_user(
    user_data: List[Dict[str, Any]], user_id: int, goodreads_url: str
) -> pd.DataFrame:

    df = None
    if len(user_data) > 0 and load_synced_user_data(user_id):
        df = pd.DataFrame(user_data)
    else:
        df = get_all_book_data_cached(goodreads_url)
        upsert_data(user_id, df)

    df["date_read"] = pd.to_datetime(df["date_read"]).dt.strftime("%b %d, %Y")
    df["date_published"] = pd.to_datetime(df["date_published"]).dt.strftime("%b %d, %Y")
    df["date_added"] = pd.to_datetime(df["date_added"]).dt.strftime("%b %d, %Y")

    return df


def upsert_data(user_id: Optional[int], df: pd.DataFrame) -> bool:
    last_sync_date = get_last_sync_date(user_id)
    if (
        last_sync_date is not None and
        last_sync_date >= datetime.now() - timedelta(minutes=5)
    ):
        print("Synced in last 5 minutes, skipping")
        return False

    if user_id is None:
        return False

    df_to_save = df.where(pd.notna(df), None)
    df_to_save.fillna("", inplace=True)  # Fill the rating and other Nans

    rows_to_upsert = []
    for row in df_to_save.iterrows():
        row_data = upsert_utils.prepare_row_for_upsert(row[1].to_dict())
        rows_to_upsert.append(row_data)

    supabase.table("books").upsert(rows_to_upsert, on_conflict="title, author, user_id").execute()
    supabase.table("syncs").insert({"user_id": user_id}).execute()
    return True


st.set_page_config(page_title="Goodreads Visualizer", layout="wide")

with open("files/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.write("# Goodreads Visualizer")
goodreads_url = st.text_input(
    "Enter your Goodreads URL",
    key="goodreads-url",
    placeholder="https://www.goodreads.com/review/list/142394620",
)

user_id = None
df = None
user_data = []

if goodreads_url:
    user_id = int(url_utils.parse_user_id(goodreads_url))
    user_data = load_data_for_user_from_db(user_id)
    df = load_data_for_user(user_data, user_id, goodreads_url)
elif os.getenv("PYTHON_ENV") == "development" and st.button("Load Sample Data"):
    df = pd.read_csv("files/goodreads_export.csv")


if user_id:
    load_sync_data = load_synced_user_data(user_id)

    if not load_sync_data and st.button("Re-sync Goodreads Data"):
        df = get_all_book_data(goodreads_url)
        upsert_data(user_id, df)

if df is not None:
    show_data(df)

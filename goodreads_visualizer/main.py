import datetime
import os
import pandas as pd
import requests
import streamlit as st

import altair as alt


try:
    from goodreads_visualizer import page_parser, url_utils, df_utils
    from goodreads_visualizer.sections import BooksReadThisYear, BooksReadComparedToYear
except ModuleNotFoundError:
    from sections import BooksReadThisYear, BooksReadComparedToYear
    import df_utils
    import page_parser
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
    "synced_at",
]


@st.cache_data(show_spinner=False)
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
    df["synced_at"] = datetime.datetime.now()
    return df


def show_data(df: pd.DataFrame) -> None:
    df_utils.format_df_datetimes(df)
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
            "date_published"
        ]
    ].reset_index(drop=True)
    with st.expander("Show data in table"):
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
        st.metric("Average book length", f'{int(df_read_year["num_pages"].mean())} pages')

        with st.expander(f"Show all books read in {year}"):
            for row in df_read_year.iterrows():
                row_vals = row[1]
                st.write(f" - {row_vals['title']} by {row_vals['author']}")


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


def load_data_for_user(db, user_id, goodreads_url):
    if not db[db["user_id"] == user_id].empty:
        df = db[db["user_id"] == user_id]
    else:
        df = get_all_book_data_cached(goodreads_url)
        upsert_data(db, df)
    return df


def upsert_data(db, df):
    db.drop(db[db["user_id"] == user_id].index, inplace=True)
    updated_db = pd.concat([db, df])
    updated_db.to_csv("data/db.csv", index=False)


st.set_page_config(page_title="Goodreads Visualizer", layout="wide")

st.write("# Goodreads Visualizer")
goodreads_url = st.text_input(
    "Enter your Goodreads URL",
    key="goodreads-url",
    placeholder="https://www.goodreads.com/review/list/142394620",
)

try:
    db = pd.read_csv("data/db.csv")
except Exception:
    db = pd.DataFrame(columns=ALL_COLUMNS)

user_id = None
df = None

if goodreads_url:
    user_id = int(url_utils.parse_user_id(goodreads_url))
    df = load_data_for_user(db, user_id, goodreads_url)
elif os.getenv("PYTHON_ENV") == "development" and st.button("Load Sample Data"):
    df = pd.read_csv("files/goodreads_export.csv")

if user_id and st.button("Re-sync Goodreads Data"):
    df = get_all_book_data(goodreads_url)
    upsert_data(db, df)

if df is not None:
    show_data(df)

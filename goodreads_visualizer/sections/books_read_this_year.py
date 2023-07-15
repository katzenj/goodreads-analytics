import altair as alt
import calendar
import streamlit as st
import pandas as pd


class BooksReadThisYear:
    def __init__(self, df_read_current_year: pd.DataFrame) -> None:
        self.books_per_month_current_year = self.books_read_by_month(
            df_read_current_year
        )

    def render_section(self):
        st.write("### Books Read This Year")
        chart = (
            alt.Chart(self.books_per_month_current_year)
            .mark_bar(color="#068D9D")
            .encode(
                x=alt.X("Month", sort=list(self.books_per_month_current_year["Month"])),
                y="Number of Books",
            )
        )
        st.altair_chart(chart, use_container_width=True)

    @staticmethod
    @st.cache_data
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

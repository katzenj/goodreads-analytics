import calendar
import altair as alt
import pandas as pd
import streamlit as st


class BooksReadComparedToYear:
    def __init__(self, df: pd.DataFrame, year, year_to_compare) -> None:
        self.df = df
        self.year = year
        self.year_to_compare = year_to_compare

    def render_section(self):
        st.write("### Books Read Compared to Last Year")
        months = [calendar.month_abbr[i] for i in range(1, 13)]
        dates_and_counts = []
        for month in months:
            dates_and_counts.append([month, self.year_to_compare, 0])
            dates_and_counts.append([month, self.year, 0])

        base_df = pd.DataFrame(dates_and_counts, columns=["month", "year", "count"])
        years = [self.year_to_compare, self.year]
        books_last_two_years_df = self.df[self.df["date_read"].dt.year.isin(years)]
        books_read_last_two_years_counts = self.books_read_by_month_and_year(
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

    @staticmethod
    @st.cache_data
    def books_read_by_month_and_year(df: pd.DataFrame) -> pd.DataFrame:
        copy = df.copy()
        copy["month"] = copy["date_read"].apply(lambda x: calendar.month_abbr[x.month])
        copy["year"] = copy["date_read"].apply(lambda x: x.year)

        copy = copy.groupby(["month", "year"]).size().reset_index(name="count")
        return copy

from typing import Optional, Union

import pandas as pd

from dateutil.parser import parse


def format_df_datetimes(df: pd.DataFrame) -> None:
    df["date_read"] = df["date_read"].apply(lambda x: parse_dt(x))
    df["date_started"] = df["date_started"].apply(lambda x: parse_dt(x))
    df["date_published"] = df["date_published"].apply(lambda x: parse_dt(x))
    df["date_added"] = df["date_added"].apply(lambda x: parse_dt(x))


def parse_dt(dt):
    if pd.isna(dt):
        return None
    return parse(dt)


def get_books_read_this_year(df: pd.DataFrame) -> pd.DataFrame:
    current_year = pd.to_datetime("today").year
    df_current_year = df[df["date_read"].dt.year == current_year]
    return df_current_year


def convert_datetime_to_string(
    val: Optional[Union[pd.Timestamp, str]]
) -> Optional[str]:
    if val is None or pd.isna(val):
        return None
    else:
        return val.strftime("%Y-%m-%d")


def download_df(df: pd.DataFrame, format: str) -> bytes:
    copy = df.copy()[
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
            "date_started",
            "cover_url",
        ]
    ]
    copy["date_read"] = copy["date_read"].apply(convert_datetime_to_string)
    copy["date_added"] = copy["date_added"].apply(convert_datetime_to_string)
    copy["date_started"] = copy["date_started"].apply(convert_datetime_to_string)
    copy["date_published"] = copy["date_published"].apply(convert_datetime_to_string)

    if format == "csv":
        return copy.to_csv(index=False).encode("utf-8")
    elif format == "json":
        return copy.to_json(orient="records").encode("utf-8")
    else:
        raise ValueError(f"Format {format} not supported.")

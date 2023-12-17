from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union


from dateutil.parser import parse

try:
    from goodreads_visualizer import db, models
except ModuleNotFoundError:
    import db
    import models


def get_read_books_for_user(
    user_id: Union[str, int], year: Optional[Union[str, int]]
) -> List[models.Book]:
    if year is None:
        user_data = db.get_user_books_data(user_id)
    else:
        user_data = db.get_user_books_data(user_id, year)

    data_models = []
    for data in user_data:
        if data["date_read"] is None:
            continue

        data_models.append(
            models.Book(
                title=data["title"],
                author=data["author"],
                date_read=_parse_optional_date(data["date_read"]),
                date_added=_parse_optional_date(data["date_added"]),
                rating=data["rating"],
                num_pages=data["num_pages"],
                avg_rating=data["avg_rating"],
                read_count=data["read_count"],
                date_published=_parse_optional_date(data["date_published"]),
                date_started=_parse_optional_date(data["date_started"]),
                review=data["review"],
                user_id=data["user_id"],
                id=data["id"],
                isbn=data["isbn"],
                cover_url=data["cover_url"],
            )
        )

    return data_models


def get_user_books_data_for_years(
    user_id: Union[str, int], years: List[Union[str, int]]
) -> List[models.Book]:
    user_data = db.get_user_books_data_for_years(user_id, years)

    data_models = []
    for data in user_data:
        data_models.append(
            models.Book(
                title=data["title"],
                author=data["author"],
                date_read=_parse_optional_date(data["date_read"]),
                date_added=_parse_optional_date(data["date_added"]),
                rating=data["rating"],
                num_pages=data["num_pages"],
                avg_rating=data["avg_rating"],
                read_count=data["read_count"],
                date_published=_parse_optional_date(data["date_published"]),
                date_started=_parse_optional_date(data["date_started"]),
                review=data["review"],
                user_id=data["user_id"],
                id=data["id"],
                isbn=data["isbn"],
                cover_url=data["cover_url"],
            )
        )
    return data_models


def get_last_sync_date(user_id: Union[str, int]) -> Optional[datetime]:
    return db.get_last_sync_date(user_id)


def get_user_name(user_id: Union[str, int]) -> str:
    return db.get_user_name(user_id)


def upsert_books_data(user_id: Optional[int], books: List[models.Book]) -> bool:
    return db.upsert_books_data(user_id, books)


def upsert_user_name(user_id: Union[str, int], name: str) -> bool:
    return db.upsert_user_name(user_id, name)


def fetch_cached_dashboard(
    user_id: str, year: Optional[Union[str, int]]
) -> Optional[Dict[Any, Any]]:
    return db.fetch_cached_dashboard(user_id, year)


def upsert_dashboard(
    user_id: str, year: Optional[Union[str, int]], dashboard: models.Dashboard
) -> bool:
    return db.upsert_dashboard(user_id, year, dashboard)


def delete_cached_dashboard(user_id: str) -> bool:
    return db.delete_cached_dashboard(user_id)


# PRIVATE FUNCTIONS


def _parse_optional_date(optional_date: Optional[str]) -> Optional[date]:
    if optional_date is None:
        return None
    else:
        return parse(optional_date)

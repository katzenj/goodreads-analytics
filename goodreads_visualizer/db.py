from typing import Any, Dict, List, Optional, Union

import os

from datetime import date
from dateutil.parser import parse
from dotenv import load_dotenv
from supabase import create_client, Client


if os.getenv("PYTHON_ENV") == "development":
    load_dotenv(".env.local")
else:
    load_dotenv(".env.production")


try:
    from goodreads_visualizer import models
except ModuleNotFoundError:
    import models


url = os.getenv("SUPABASE_URL")
key = os.getenv("SERVICE_KEY")
supabase: Client = create_client(url, key)


def get_user_books_data(
    user_id: Union[int, str], year: Optional[Union[str, int]] = None
) -> List[Dict[str, Any]]:
    if year is not None:
        start_of_year = date(year=int(year), month=1, day=1)
        end_of_year = date(year=int(year), month=12, day=31)
        res = (
            supabase.table("books")
            .select("*")
            .eq("user_id", user_id)
            .gte("date_read", start_of_year)
            .lte("date_read", end_of_year)
            .execute()
        )
        return res.data

    res = supabase.table("books").select("*").eq("user_id", user_id).execute()
    return res.data


def get_user_books_data_for_years(
    user_id: Union[int, str], years: List[Union[str, int]]
) -> List[Dict[str, Any]]:
    year_ints = [int(year) for year in years]
    start_of_timeframe = date(year=min(year_ints), month=1, day=1)
    end_of_timeframe = date(year=max(year_ints), month=12, day=31)
    res = (
        supabase.table("books")
        .select("*")
        .eq("user_id", user_id)
        .gte("date_read", start_of_timeframe)
        .lte("date_read", end_of_timeframe)
        .execute()
    )
    return res.data


def get_user_years(user_id: Union[int, str]) -> List[Dict[str, Any]]:
    res = (
        supabase.table("books")
        .select("date_read")
        .eq("user_id", user_id)
        .not_.is_("date_read", "null")
        .execute()
    )
    return list(set(str(parse(x["date_read"]).year) for x in res.data))


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

    return parse(last_sync[0]["created_at"])


def get_user_name(user_id: Union[str, int]) -> Optional[str]:
    res = supabase.table("users").select("name").eq("external_id", user_id).execute()
    if len(res.data) == 0:
        return None

    return res.data[0]["name"]


def upsert_books_data(user_id: Optional[int], books: List[models.Book]) -> bool:
    if user_id is None:
        return False

    unique_books = _unique_books(books)
    serialized_books = [book.serialize() for book in unique_books]

    supabase.table("books").upsert(
        serialized_books, on_conflict="title, author, user_id"
    ).execute()
    supabase.table("syncs").insert({"user_id": user_id}).execute()
    return True


def upsert_user_name(user_id: Union[str, int], name: str) -> bool:
    res = (
        supabase.table("users")
        .upsert({"external_id": user_id, "name": name}, on_conflict="external_id")
        .execute()
    )
    return True


def _unique_books(books: List[models.Book]) -> List[models.Book]:
    seen = set()
    res = []
    for book in books:
        tup = (book.title, book.author, book.user_id)
        if tup in seen:
            continue
        else:
            seen.add(tup)
            res.append(book)
    return res

from typing import Any, Dict, List, Optional

import os
import pandas as pd

from datetime import datetime, timedelta
from dateutil.parser import parse
from supabase import create_client, Client

try:
    from goodreads_visualizer import upsert_utils
except ModuleNotFoundError:
    import upsert_utils




url = os.getenv("SUPABASE_URL")
key = os.getenv("SERVICE_KEY")
supabase: Client = create_client(url, key)


def load_user_books(user_id: int) -> List[Dict[str, Any]]:
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

    unique_books = upsert_utils.unique_books(rows_to_upsert)

    supabase.table("books") \
        .upsert(unique_books, on_conflict="title, author, user_id") \
        .execute()
    supabase.table("syncs").insert({"user_id": user_id}).execute()
    return True

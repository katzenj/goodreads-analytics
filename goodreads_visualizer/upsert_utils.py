from datetime import datetime, date
from dateutil.parser import parse
from typing import Any, Dict, List, Optional, Union


def unique_books(books: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    res = []
    for book in books:
        tup = (book["title"], book["author"], book["user_id"])
        if tup in seen:
            continue
        else:
            seen.add(tup)
            res.append(book)
    return res


def convert_date_for_upsert(date_obj: Optional[Union[str, datetime]]) -> Optional[str]:
    if date_obj is None or date_obj == "":
        return None

    if isinstance(date_obj, str):
        return str(parse(date_obj))
    elif type(date_obj) == date:
        return str(date_obj)
    else:
        return str(date_obj.to_pydatetime())


def convert_value_for_upsert(value: Optional[Union[str, int]], value_type) -> Optional[int]:
    if value is None or value == "":
        return None

    return value_type(value)


def prepare_row_for_upsert(row_data: Dict[str, Any]) -> Dict[str, Any]:
    row_data_copy = row_data.copy()

    if "Unnamed: 0" in row_data_copy:
        del row_data_copy["Unnamed: 0"]

    row_data_copy["date_added"] = convert_date_for_upsert(row_data_copy["date_added"])
    row_data_copy["date_published"] = convert_date_for_upsert(row_data_copy["date_published"])
    row_data_copy["date_read"] = convert_date_for_upsert(row_data_copy["date_read"])
    row_data_copy["date_started"] = convert_date_for_upsert(row_data_copy["date_started"])
    row_data_copy["num_pages"] = convert_value_for_upsert(row_data_copy["num_pages"], int)
    row_data_copy["rating"] = convert_value_for_upsert(row_data_copy["rating"], int)
    row_data_copy["avg_rating"] = convert_value_for_upsert(row_data_copy["avg_rating"], float)

    return row_data_copy

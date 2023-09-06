from datetime import datetime, date
from typing import Any, Dict, Optional, Union


def convert_date_for_upsert(date_obj: Optional[Union[str, datetime]]) -> str:
    if date_obj is None or date_obj == "":
        return None

    if type(date_obj) == str:
        return datetime.strptime(date_obj, "%b %d, %Y")
    elif type(date_obj) == date:
        return str(date_obj)
    else:
        return str(date_obj.to_pydatetime())


def convert_value_for_upsert(value: Optional[Union[str, int]], value_type) -> int:
    if value is None or value == "":
        return None

    return value_type(value)


def prepare_row_for_upsert(row_data: Dict[str, Any]) -> Dict[str, Any]:
    row_data_copy = row_data.copy()

    row_data_copy["date_added"] = convert_date_for_upsert(row_data_copy["date_added"])
    row_data_copy["date_published"] = convert_date_for_upsert(row_data_copy["date_published"])
    row_data_copy["date_read"] = convert_date_for_upsert(row_data_copy["date_read"])
    row_data_copy["date_started"] = convert_date_for_upsert(row_data_copy["date_started"])
    row_data_copy["num_pages"] = convert_value_for_upsert(row_data_copy["num_pages"], int)
    row_data_copy["rating"] = convert_value_for_upsert(row_data_copy["rating"], int)
    row_data_copy["avg_rating"] = convert_value_for_upsert(row_data_copy["avg_rating"], float)

    return row_data_copy

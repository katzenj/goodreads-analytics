import re
from typing import Dict, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def format_goodreads_url(url: str, params: Dict[str, Union[str, int]] = {}) -> str:
    user_id = parse_user_id(url)
    user_url = _format_user_url(user_id)
    parsed_url = urlparse(user_url)
    query_params = parse_qs(parsed_url.query)
    query_params.update(params)

    if "print" not in query_params:
        query_params["print"] = ["true"]

    encoded_params = encoded_params = urlencode(query_params, doseq=True)
    modified_parts = list(parsed_url)
    modified_parts[4] = encoded_params
    return urlunparse(modified_parts)


def parse_user_id(url: str) -> str:
    matches = re.findall(r"(\d{9})(?:-\w+)?", url)

    if matches:
        user_id = matches[0]
    else:
        raise ValueError("Invalid URL")

    return user_id


def _format_user_url(user_id: str) -> str:
    return f"https://www.goodreads.com/review/list/{user_id}"

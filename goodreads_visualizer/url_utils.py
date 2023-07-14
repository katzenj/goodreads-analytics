import re
from typing import Dict, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def format_goodreads_url(url: str, params: Dict[str, Union[str, int]] = {}) -> str:
    user_url = _format_user_url(url)
    parsed_url = urlparse(user_url)
    query_params = parse_qs(parsed_url.query)
    query_params.update(params)

    if "print" not in query_params:
        query_params["print"] = ["true"]

    encoded_params = encoded_params = urlencode(query_params, doseq=True)
    modified_parts = list(parsed_url)
    modified_parts[4] = encoded_params
    return urlunparse(modified_parts)


def _format_user_url(url: str) -> str:
    parsed_url = urlparse(url)
    if parsed_url.path.startswith("/user/show"):
        user_id = parsed_url.path.split("/")[3]
    elif parsed_url.path.startswith("/review/list"):
        user_id = parsed_url.path.split("/")[3]
    elif re.search(r"\d{9}(-\w+)?", url):
        user_id = re.search(r"\d{9}(-\w+)?", url).group()
    else:
        raise ValueError("Invalid URL")
    return f"https://www.goodreads.com/review/list/{user_id}"

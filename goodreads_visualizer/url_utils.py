import re
from typing import Dict, Union
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


# Method 1: Using urllib.parse
def update_query_params(url, params):
    # Parse the URL
    parsed_url = urlparse(url)

    # Get existing query parameters
    query_params = parse_qs(parsed_url.query)

    # Update with new parameters
    query_params.update(params)

    # Create new query string
    new_query = urlencode(query_params, doseq=True)

    # Reconstruct the URL
    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment,
        )
    )


def format_goodreads_url(url: str, params: Dict[str, Union[str, int]] = {}) -> str:
    user_id = parse_user_id(url)
    user_url = format_user_url(user_id)
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


def format_user_url(user_id: str) -> str:
    return f"https://www.goodreads.com/review/list/{user_id}"


def get_user_profile_url(user_id: str) -> str:
    return f"https://www.goodreads.com/user/show/{user_id}"

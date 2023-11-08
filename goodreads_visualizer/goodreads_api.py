import pandas as pd
import requests


try:
    from goodreads_visualizer import page_parser, url_utils
except ModuleNotFoundError:
    import page_parser
    import url_utils


def fetch_books_data(user_id: str) -> pd.DataFrame:
    request_url = url_utils.format_user_url(user_id)
    response = requests.get(request_url)

    parser = page_parser.PageParser(response.text)
    last_page_number = parser.last_page_number()

    all_data = []
    all_data.extend(parser.parse_page())

    # Start at 2, already parsed page 1
    for page_number in range(2, last_page_number + 1):
        request_url = url_utils.format_goodreads_url(request_url, {"page": page_number})
        response = requests.get(request_url)
        parser = page_parser.PageParser(response.text)
        all_data.extend(parser.parse_page())

    df = pd.DataFrame(all_data)
    df["user_id"] = user_id
    return df

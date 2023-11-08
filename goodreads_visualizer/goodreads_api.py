from typing import List
from bs4 import BeautifulSoup
import requests

try:
    from goodreads_visualizer import page_parser, url_utils, models
except ModuleNotFoundError:
    import models
    import page_parser
    import url_utils


def fetch_books_data(user_id: str) -> List[models.Book]:
    base_url = url_utils.format_user_url(user_id)
    request_url = url_utils.format_goodreads_url(base_url)
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

    books = []
    for data in all_data:
        books.append(
            models.Book(
                title=data["title"],
                author=data["author"],
                date_read=data["date_read"],
                date_added=data["date_added"],
                rating=data["rating"],
                num_pages=data["num_pages"],
                avg_rating=data["avg_rating"],
                read_count=data["read_count"],
                date_published=data["date_published"],
                date_started=data["date_started"],
                review=data["review"],
                user_id=user_id,
                id=None,
                isbn=data["isbn"],
                cover_url=data["cover_url"],
            )
        )

    return books


def fetch_user_name(user_id: str):
    request_url = url_utils.get_user_profile_url(user_id)
    response = requests.get(request_url)
    soup = BeautifulSoup(response.text, "html.parser")
    header = soup.find(id="profileNameTopHeading")
    return header.get_text().strip()

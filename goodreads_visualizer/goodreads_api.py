import os
from typing import List
from datetime import datetime

import requests
from dotenv import load_dotenv

try:
    from goodreads_visualizer import models
except ModuleNotFoundError:
    import models

BASE = "https://www.goodreads.com/user/show/142394620-jordan" 


if os.getenv("PYTHON_ENV") == "development":
    load_dotenv(".env.local")
else:
    load_dotenv(".env.production")


def fetch_books_data(user_id: str) -> List[models.Book]:
    base_url = f"https://www.goodreads.com/user/show/{user_id}"
    api_url = "https://katzenj-goodreadsapi.web.val.run"
    body = {
        "url": base_url,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": os.getenv("PERSONAL_GOODREADS_API_KEY"),
    }
    response = requests.post(api_url, json=body, headers=headers)
    json = response.json()
    books_data = json["books"]
    books = []
    for book in books_data:
        books.append(
            models.Book(
                title=book["title"],
                author=book["authorName"],
                date_read=parse_datetime(book["userReadAt"]),
                date_added=parse_datetime(book["userDateAdded"]),
                rating=book["userRating"],
                num_pages=book["numPages"],
                avg_rating=book["averageRating"],
                date_published=parse_datetime(book["pubDate"]),
                isbn=book["isbn"],
            )
        )

    return books

def parse_datetime(date_string):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ')
    except (ValueError, TypeError):
        return None

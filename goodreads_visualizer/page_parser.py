import re
from bs4 import BeautifulSoup


class PageParser:
    DATE_PATTERN = r"\w{3}\s+(\d{1,2},)?\s{0,}\d{4}"

    def __init__(self, response_text: str) -> None:
        self.soup = BeautifulSoup(response_text, "html.parser")

    def parse_page(self) -> list:
        books_data = self.soup.find_all("tr", {"class": "bookalike review"})

        page_data = []
        for book in books_data:
            data = self._parse_book_row(book)
            page_data.append(data)

        return page_data

    def last_page_number(self):
        pagination_div = self.soup.find("div", {"id": "reviewPagination"})
        pages = pagination_div.find_all("a")
        page_numbers = []
        for page in pages:
            if page.get("class") == ["next_page"] or page.get("class") == [
                "previous_page"
            ]:
                continue
            page_numbers.append(page.get_text())

        return int(page_numbers[-1])

    def _parse_book_row(self, book_row) -> None:
        title = (
            book_row.find("td", {"class": "field title"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        author = (
            book_row.find("td", {"class": "field author"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
            .replace("\n*", "")
        )
        isbn = (
            book_row.find("td", {"class": "field isbn"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        num_pages_str = (
            book_row.find("td", {"class": "field num_pages"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        num_pages_matches = re.findall("\d+", num_pages_str)
        num_pages = int(num_pages_matches[0]) if num_pages_matches else None
        avg_rating = (
            book_row.find("td", {"class": "field avg_rating"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        rating = (
            book_row.find("td", {"class": "field rating"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        review = (
            book_row.find("td", {"class": "field review"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        read_count = (
            book_row.find("td", {"class": "field read_count"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        date_pub = (
            book_row.find("td", {"class": "field date_pub"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        # TODO: when read count > 1, date_started is a list of dates
        date_started_base = (
            book_row.find("td", {"class": "field date_started"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )

        date_started_match = re.match(self.DATE_PATTERN, date_started_base)
        date_started = date_started_match.group() if date_started_match else None
        # TODO: when read count > 1, date_read is a list of dates
        date_read_base = (
            book_row.find("td", {"class": "field date_read"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        date_read_match = re.match(self.DATE_PATTERN, date_read_base)
        date_read = date_read_match.group() if date_read_match else None
        date_added = (
            book_row.find("td", {"class": "field date_added"})
            .find("div", {"class": "value"})
            .get_text()
            .strip()
        )
        return {
            "title": title,
            "author": author,
            "isbn": isbn,
            "num_pages": num_pages,
            "avg_rating": avg_rating,
            "rating": rating,
            "review": review,
            "read_count": read_count,
            "date_pub": date_pub,
            "date_started": date_started,
            "date_read": date_read,
            "date_added": date_added,
        }

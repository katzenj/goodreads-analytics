from typing import Any, Dict, List


def unique_books(books: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    res = []
    for book in books:
        tup = (book.title, book.author, book.user_id)
        if tup in seen:
            continue
        else:
            seen.add(tup)
            res.append(book)
    return res

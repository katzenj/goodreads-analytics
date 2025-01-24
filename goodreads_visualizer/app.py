from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for

try :
    from goodreads_visualizer import orchestrator, goodreads_api, url_utils
except ModuleNotFoundError:
    from . import orchestrator, goodreads_api, url_utils


app = Flask(__name__)


def get_year_param(args):
    year = args.get("year")

    if year is None or year == "All time":
        return None

    return year


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["goodreads_url"]
        user_id = url_utils.parse_user_id(url)
        year = datetime.now().year
        return redirect(url_for("reading_data", user_id=user_id, year=year))

    return render_template("index.html")


@app.route("/load_data", methods=["POST"])
def load_data_for_url():
    url = request.form["goodreads_url"]
    user_id = url_utils.parse_user_id(url)
    return redirect(url_for("reading_data", user_id=user_id))


@app.route("/users/<user_id>", methods=["GET", "POST"])
def reading_data(user_id):
    year = request.args.get("year") or request.form.get("year")
    if year == "":
        year = None
    else:
        year = int(str(year))

    books = goodreads_api.fetch_books_data(user_id)
    all_read_books = []
    years = set()
    for book in books:
        if book.date_read is not None:
            all_read_books.append(book)
            years.add(book.date_read.year)

    years = [str(x) for x in sorted(years, reverse=True)]

    data = orchestrator.get_user_books_data(books, year)
    graphs_data = orchestrator.graphs_data_for_year(all_read_books, year)

    return render_template(
        "users/index.html",
        user_id=user_id,
        years=years,
        data=data,
        graphs_data=graphs_data.serialize(),
        selected_year=str(year),
    )

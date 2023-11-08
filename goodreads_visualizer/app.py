from flask import Flask, render_template, request, redirect, url_for

import os

from dotenv import load_dotenv


if os.getenv("PYTHON_ENV") == "development":
    load_dotenv(".env.local")
else:
    load_dotenv(".env")


try:
    from goodreads_visualizer import orchestrator
except ModuleNotFoundError:
    pass


app = Flask(__name__)


def get_year_param(args):
    year = args.get("year")

    if year is None or year == "All time":
        return None

    return year


@app.route("/")
def index():
    user_id = "142394620"

    data, years = orchestrator.get_user_data(user_id, None)

    return render_template("index.html", years=years, data=data)


@app.route("/sync", methods=["POST"])
def sync():
    user_id = request.form["user_id"]

    orchestrator.sync_user_data(user_id)

    return redirect(url_for("reading_data", user_id=user_id))


@app.route("/users/<user_id>", methods=["GET", "POST"])
def reading_data(user_id):
    selected_year = get_year_param(request.args)
    print("jordan year", selected_year)
    data, years = orchestrator.get_user_data(user_id, selected_year)
    graphs_data = orchestrator.graphs_data_for_year(user_id, selected_year)

    if request.method == "POST":
        year = request.form["year"]
        # Redirect to the same page with the year as a query parameter
        return redirect(url_for("reading_data", user_id=user_id, year=year))

    return render_template(
        "users/index.html",
        years=years,
        data=data,
        graphs_data=graphs_data,
        selected_year=selected_year,
        user_id=user_id,
    )

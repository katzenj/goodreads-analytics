from flask import Flask, render_template, request, redirect, url_for


from goodreads_visualizer import api


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
    selected_year = request.args.get("year")
    data, years = orchestrator.get_user_data(user_id, selected_year)
    graphs_data = orchestrator.graphs_data_for_year(user_id, selected_year)

    if request.method == "POST":
        year = request.form["year"]
        # Redirect to the same page with the year as a query parameter
        return redirect(url_for("reading_data", user_id=user_id, year=year))

    last_synced_at = api.get_last_sync_date(user_id)
    formatted_last_synced_at = last_synced_at.strftime("%b %d, %Y @ %I:%M %p")

    return render_template(
        "users/index.html",
        years=years,
        data=data,
        graphs_data=graphs_data.serialize(),
        selected_year=selected_year,
        user_id=user_id,
        last_synced_at=formatted_last_synced_at,
    )

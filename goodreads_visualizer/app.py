from flask import Flask, render_template, request, redirect, url_for


from goodreads_visualizer import api, orchestrator, url_utils, utils


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
        return redirect(url_for("reading_data", user_id=user_id))

    return render_template("index.html")


@app.route("/sync", methods=["POST"])
def sync():
    user_id = request.form["user_id"]

    orchestrator.sync_user_data(user_id)
    orchestrator.sync_user_name(user_id)
    return redirect(url_for("reading_data", user_id=user_id))


@app.route("/load_data", methods=["POST"])
def load_data_for_url():
    url = request.form["goodreads_url"]
    user_id = url_utils.parse_user_id(url)
    return redirect(url_for("reading_data", user_id=user_id))


@app.route("/users/<user_id>", methods=["GET", "POST"])
def reading_data(user_id):
    selected_year = request.args.get("year")
    data, years, user_name = orchestrator.get_user_data(user_id, selected_year)
    graphs_data = orchestrator.graphs_data_for_year(user_id, selected_year)

    if request.method == "POST":
        year = request.form["year"]
        # Redirect to the same page with the year as a query parameter
        return redirect(url_for("reading_data", user_id=user_id, year=year))

    goodreads_url = url_utils.format_user_url(user_id)
    last_synced_at = api.get_last_sync_date(user_id)
    formatted_last_synced_at = utils.format_datetime_in_pt(last_synced_at)

    return render_template(
        "users/index.html",
        years=years,
        data=data,
        graphs_data=graphs_data.serialize(),
        selected_year=selected_year,
        user_id=user_id,
        last_synced_at=formatted_last_synced_at,
        goodreads_url=goodreads_url,
        user_name=user_name,
    )

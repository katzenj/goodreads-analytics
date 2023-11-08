from datetime import datetime
import pytz


def format_datetime_in_pt(dt: datetime):
    pt_timezone = pytz.timezone("America/Los_Angeles")
    pt_dt = dt.astimezone(pt_timezone)
    return pt_dt.strftime("%b %d, %Y @ %-I:%M %p")

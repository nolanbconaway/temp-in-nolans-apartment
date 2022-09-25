"""Temperature in my apartment app."""

import datetime
import os
import typing

import pytz
from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError
from werkzeug.exceptions import BadRequest

from .converters import DateConverter

app = Flask(__name__)
app.url_map.converters["date"] = DateConverter

# set up database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
db = SQLAlchemy(app)

# set up limiter
limiter = Limiter(
    app, key_func=get_remote_address, default_limits=["200 per day", "10 per minute"]
)


@limiter.request_filter
def ip_whitelist():
    """Do not limit local dev debugging."""
    return request.remote_addr == "127.0.0.1"


class Snapshot(db.Model):
    """Snapshot data model."""

    __tablename__ = "snapshots"
    id = db.Column(db.Integer, primary_key=True)
    dttm_utc = db.Column(db.DateTime)
    fahrenheit = db.Column(db.Float)

    def as_dict(self):
        """Return view as a dictionary."""
        return dict(id=self.id, dttm_utc=self.dttm_utc, fahrenheit=self.fahrenheit)


def get_readings(
    lower_utc: datetime.datetime, upper_utc: datetime.datetime = None
) -> typing.List[dict]:
    """Get temperature readings from the database in the period of lower to upper.

    Limits are inclusive, upper defaults to one minute ago.
    """
    query = Snapshot.query.filter(Snapshot.dttm_utc >= lower_utc)
    if upper_utc is not None:
        query = query.filter(Snapshot.dttm_utc <= upper_utc)

    query = query.order_by(Snapshot.dttm_utc)

    return list(i.as_dict() for i in query)


def latest_reading() -> dict:
    """Return the most recent temperature reading."""
    return Snapshot.query.order_by(Snapshot.dttm_utc.desc()).first().as_dict()


def utc_to_nyc(utc: datetime.datetime, naive: bool = False) -> datetime.datetime:
    """Convert a UTC datetime to NYC time."""
    if utc.tzinfo is None:
        utc = pytz.timezone("UTC").localize(utc)
    result = pytz.timezone("US/Eastern").normalize(utc.replace(microsecond=0))
    if naive:
        return result.replace(tzinfo=None)
    return result


def nyc_to_utc(nyc: datetime.datetime, naive: bool = False) -> datetime.datetime:
    """Convert a NYC datetime to UTC time.

    Optionally make the datetime timezone naive.
    """
    if nyc.tzinfo is None:
        nyc = pytz.timezone("US/Eastern").localize(nyc)
    result = pytz.timezone("UTC").normalize(nyc.replace(microsecond=0))
    if naive:
        return result.replace(tzinfo=None)
    return result


def temp_requirements(dttm: datetime.datetime) -> datetime.datetime:
    """Get temperature requirements per NYC law."""
    if dttm.date().month < 10 and dttm.date().month > 5:
        return None
    if dttm.time().hour < 6 or dttm.time().hour > 21:
        return 62
    else:
        return 68


@app.errorhandler(OperationalError)
def handle_bad_request(e):
    """Handle bad requests."""
    print(e)
    return render_template("operationalerror.html"), 400


@app.route("/")
def today():
    """Provide the main ui."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=1440)
    readings = get_readings(cutoff)

    if not readings:
        return render_template("noreadings.html"), 400

    dttm_utc, temps = zip(*((r["dttm_utc"], r["fahrenheit"]) for r in readings))

    # get nyc time, temp requirements
    dttms = list(map(utc_to_nyc, dttm_utc))
    reqs = list(map(temp_requirements, dttms))

    # get latest data
    latest = latest_reading()

    # render
    return render_template(
        "today.html",
        dttms=dttms,
        temps=temps,
        reqs=reqs,
        latest_fahrenheit=int(round(latest["fahrenheit"])),
        latest_dttm_nyc=utc_to_nyc(latest["dttm_utc"]),
    )


@app.route("/date/<date:date_nyc>")
def view_date(date_nyc):
    """Show the readings from a given date."""
    # vaidate date input
    if date_nyc.date() < datetime.date(2019, 1, 5):
        raise BadRequest("My database only has data from Jan 5 2019.")

    if date_nyc.date() > utc_to_nyc(datetime.datetime.utcnow(), naive=True).date():
        raise BadRequest("Cannot look into the future!")

    # get limits of date
    lower_utc = nyc_to_utc(
        datetime.datetime(date_nyc.year, date_nyc.month, date_nyc.day, 0, 0, 0),
        naive=True,
    )
    upper_utc = nyc_to_utc(
        datetime.datetime(date_nyc.year, date_nyc.month, date_nyc.day, 23, 59, 59),
        naive=True,
    )

    # query database
    dttm_utc, temps = zip(
        *(
            (r["dttm_utc"], r["fahrenheit"])
            for r in get_readings(lower_utc=lower_utc, upper_utc=upper_utc)
        )
    )

    # get nyc time, temp requirements
    dttms = list(map(utc_to_nyc, dttm_utc))
    reqs = list(map(temp_requirements, dttms))

    # render
    return render_template(
        "date.html",
        date_nyc=date_nyc,
        previous_date=date_nyc - datetime.timedelta(days=1),
        next_date=date_nyc + datetime.timedelta(days=1),
        dttms=dttms,
        temps=temps,
        reqs=reqs,
    )

import datetime
import os
import typing

import pytz
from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

app = Flask(__name__)

# set up database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
print(os.environ["DATABASE_URI"])
db = SQLAlchemy(app)

# set up limiter
limiter = Limiter(
    app, key_func=get_remote_address, default_limits=["200 per day", "5 per minute"]
)


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


def utc_to_nyc(utc: datetime.datetime) -> datetime.datetime:
    """Convert a UTC datetime to NYC time."""
    return pytz.timezone("US/Eastern").normalize(
        pytz.timezone("UTC").localize(utc.replace(microsecond=0))
    )


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
    return render_template("operationalerror.html"), 400


@app.route("/")
def today():
    """Provide the main ui."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=1440)

    dttm_utc, temps = zip(
        *((r["dttm_utc"], r["fahrenheit"]) for r in get_readings(cutoff))
    )

    # get nyc time, temp requirements
    dttms = list(map(utc_to_nyc, dttm_utc))
    reqs = list(map(temp_requirements, dttms))

    # get latest data
    latest = latest_reading()

    # render
    return render_template(
        "base.html",
        dttms=dttms,
        temps=temps,
        reqs=reqs,
        fahrenheit=int(round(latest["fahrenheit"])),
        last_update=utc_to_nyc(latest["dttm_utc"]),
    )

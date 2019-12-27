import datetime
import os

import pytz
import sqlalchemy.exc
from flask import Flask, redirect, render_template, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# set up database
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
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


@app.errorhandler(sqlalchemy.exc.OperationalError)
def handle_bad_request(e):
    """Handle bad requests."""
    return render_template("operationalerror.html"), 400


@app.route("/")
def today():
    """Provide the main ui."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=1440)
    rows = (
        Snapshot.query.filter(Snapshot.dttm_utc >= cutoff)
        .order_by(Snapshot.dttm_utc)
        .all()
    )

    # unzip the rows
    dttm_utc, temps = zip(*((r.dttm_utc, r.fahrenheit) for r in rows))

    # get nyc time, temp requirements
    dttms = list(map(utc_to_nyc, dttm_utc))
    reqs = list(map(temp_requirements, dttms))

    # get latest data
    latest = Snapshot.query.order_by(Snapshot.dttm_utc.desc()).first()

    # render
    return render_template(
        "base.html",
        dttms=dttms,
        temps=temps,
        reqs=reqs,
        fahrenheit=int(round(latest.fahrenheit)),
        last_update=utc_to_nyc(latest.dttm_utc),
    )

import datetime
import os

import pytz
import sqlalchemy.exc
from flask import Flask, redirect, render_template, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_sqlalchemy import SQLAlchemy

SHOW_RADIATOR_MODEL = False

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


def utc_to_nyc(utc):
    """Convert a UTC datetime to NYC time."""
    return pytz.timezone("US/Eastern").normalize(
        pytz.timezone("UTC").localize(utc.replace(microsecond=0))
    )


def temp_requirements(dttm):
    """Get temperature requirements per NYC law.

    https://www1.nyc.gov/nyc-resources/service/1815/residential-heat-and-hot-water-requirements
    """
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


def infer_radiator(rows, timeout=20):
    """Infer when the radiator was on.

    Accepts a list of sqlalchemy rows and returns a list of (start, stop) tuples.
    Assumes the rows are ordered by time.
    """
    # get start time. we need 15 mins of data to make the call
    start_utc = rows[0].dttm_utc + datetime.timedelta(minutes=15)

    def temp_at_lower_bound(idx):
        """Get the temp at the latest point between 15 and 20 mins ago.

        For speed, provide the index of the row you want the lower bound for. This will
        search between that row and the one 25 rows before. We assume the rows are
        sorted by datetime and I know that we usually get rows per minute so this
        should work.
        """
        lag15 = rows[idx].dttm_utc - datetime.timedelta(minutes=15)
        lag20 = rows[idx].dttm_utc - datetime.timedelta(minutes=20)
        lowerbound = 0 if idx < 25 else idx - 25
        return [
            i.fahrenheit
            for i in rows[lowerbound:idx]
            if i.dttm_utc >= lag20 and i.dttm_utc <= lag15
        ][-1]

    def mins_elapsed(upper, lower):
        """Get the elapsed minutes between two datetimes."""
        return (upper - lower).total_seconds() / 60

    # figure out if the radiator was on based on X increase over N minutes.
    radiator_on = [
        r.dttm_utc
        for i, r in enumerate(rows)
        if r.dttm_utc >= start_utc
        and (r.fahrenheit - temp_at_lower_bound(i)) > (0.007 * 15)
    ]

    # that should result in a few OFF points within an ON zone and vice versa,
    # since the model is very imperfect. So we need to cluster the ON regions.
    # I have chosen to delimit based on <timeout> minutes of consecutive OFF.
    limits = []
    for startpoint in radiator_on[:-1]:

        # move along if this moment is already part of a cycle.
        if limits and startpoint <= limits[-1][-1]:
            continue

        endpoint = startpoint
        for candidate in filter(lambda x: x > startpoint, radiator_on):
            # if the timeout is reached, the cycle is over
            if mins_elapsed(candidate, endpoint) > timeout:
                break

            # otherwise increment the endpoint
            endpoint = candidate

        # add if the total elapsed time is enough
        if mins_elapsed(endpoint, startpoint) >= timeout:
            limits.append((startpoint, endpoint))

    return limits


@app.route("/")
def today():
    """Provide the main ui."""
    # get timeseries. back 1455 mins for the radiator detector.
    # will trim the extra 15 mins off later.
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=1455)
    rows = (
        Snapshot.query.filter(Snapshot.dttm_utc >= cutoff)
        .order_by(Snapshot.dttm_utc)
        .all()
    )

    # get radiator ON/OFF limits if we are showing that
    if SHOW_RADIATOR_MODEL:
        radiator_limits_utc = infer_radiator(rows)
        radiator_limits = [tuple(map(utc_to_nyc, i)) for i in radiator_limits_utc]
    else:
        radiator_limits = []

    # remove extra 15 mins now that we know the limits
    rows = [i for i in rows if i.dttm_utc > cutoff + datetime.timedelta(minutes=15)]

    # unzip the rows
    dttm_utc, temps = zip(*((r.dttm_utc, r.fahrenheit) for r in rows))

    # get nyc time, temp requirements, radiator indicator
    dttms = list(map(utc_to_nyc, dttm_utc))
    reqs = list(map(temp_requirements, dttms))
    radiator = [any(i >= l and i <= u for l, u in radiator_limits) for i in dttms]

    # get latest data
    latest = Snapshot.query.order_by(Snapshot.dttm_utc.desc()).first()

    # render
    return render_template(
        "base.html",
        dttms=dttms,
        temps=temps,
        reqs=reqs,
        radiator=radiator,
        n_radiators=len(radiator_limits),
        show_radiator_model=SHOW_RADIATOR_MODEL,
        fahrenheit=int(round(latest.fahrenheit)),
        last_update=utc_to_nyc(latest.dttm_utc),
    )

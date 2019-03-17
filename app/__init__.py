from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for

from flask_sqlalchemy import SQLAlchemy
import sqlalchemy.exc

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import pytz
import datetime
import os

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

    def temp_at_lower_bound(dttm):
        """Get the temp at the latest point between 15 and 20 mins ago."""
        lag15 = dttm - datetime.timedelta(minutes=15)
        lag20 = dttm - datetime.timedelta(minutes=20)
        return [
            i.fahrenheit for i in rows if i.dttm_utc >= lag20 and i.dttm_utc <= lag15
        ][-1]

    def mins_elapsed(upper, lower):
        """Get the elapsed minutes between two datetimes."""
        return (upper - lower).total_seconds() / 60

    radiator_on = [
        i.dttm_utc
        for i in rows
        if i.dttm_utc >= start_utc
        and (i.fahrenheit - temp_at_lower_bound(i.dttm_utc)) > (0.007 * 15)
    ]

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

    # get radiator ON/OFF limits
    radiator_limits_utc = infer_radiator(rows)
    radiator_limits = [tuple(map(utc_to_nyc, i)) for i in radiator_limits_utc]

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
        fahrenheit=int(round(latest.fahrenheit)),
        last_update=utc_to_nyc(latest.dttm_utc),
    )

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
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URI']
db = SQLAlchemy(app)

# set up limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "5 per minute"]
)


class Snapshot(db.Model):
    """Snapshot data model."""

    __tablename__ = 'snapshots'
    id = db.Column(db.Integer, primary_key=True)
    dttm_utc = db.Column(db.DateTime)
    fahrenheit = db.Column(db.Float)


def utc_to_nyc(utc):
    """Convert a UTC datetime to NYC time."""
    return (
        utc
        .replace(tzinfo=pytz.utc)
        .astimezone(pytz.timezone('US/Eastern'))
        .replace(tzinfo=pytz.timezone('US/Eastern'), microsecond=0)
    )


def unzip_rows(rows):
    """Handle a sequence of SQL rows and make it useful."""
    dttms, temps = zip(*((utc_to_nyc(i.dttm_utc), i.fahrenheit) for i in rows))
    reqs = list(map(temp_requirements, dttms))
    return dttms, temps, reqs


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
    return render_template('operationalerror.html'), 400


@app.route("/")
def today():

    # get timeseries
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=1440)
    rows = (
        Snapshot
        .query
        .filter(Snapshot.dttm_utc >= cutoff)
        .order_by(Snapshot.dttm_utc)
        .all()
    )
    dttms, temps, reqs = unzip_rows(rows)

    # get latest data
    latest = Snapshot.query.order_by(Snapshot.dttm_utc.desc()).first()

    # render
    return render_template(
        'base.html',
        dttms=dttms,
        temps=temps,
        reqs=reqs,
        fahrenheit=int(round(latest.fahrenheit)),
        last_update=utc_to_nyc(latest.dttm_utc),
    )

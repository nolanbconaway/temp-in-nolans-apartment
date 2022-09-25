"""Test the app."""
import datetime

import pytest

import app


@pytest.fixture
def client():
    """Test app fixture."""
    with app.app.test_client() as client:
        yield client


def test_latest_reading(client, monkeypatch):
    """Test that the latest reading is served correctly."""
    readings = [
        {"id": 1, "dttm_utc": datetime.datetime(2019, 1, 1, 1, 1), "fahrenheit": 70},
        {"id": 2, "dttm_utc": datetime.datetime(2019, 1, 1, 1, 2), "fahrenheit": 71},
    ]
    latest = readings[-1]
    monkeypatch.setattr(app, "get_readings", lambda *x, **y: readings)
    monkeypatch.setattr(app, "latest_reading", lambda *x, **y: latest)

    rv = client.get("/")
    html = rv.data.decode("utf-8")
    assert f'{latest["fahrenheit"]}&deg;F' in html


def test_historical(client, monkeypatch):
    """Test that the historical readings are served correctly."""
    readings = [
        {"id": 1, "dttm_utc": datetime.datetime(2019, 1, 6, 1, 1), "fahrenheit": 70},
        {"id": 2, "dttm_utc": datetime.datetime(2019, 1, 6, 1, 2), "fahrenheit": 71},
    ]
    monkeypatch.setattr(app, "get_readings", lambda *x, **y: readings)

    rv = client.get("/date/2019-01-06")
    html = rv.data.decode("utf-8")
    assert "January 06 2019" in html


def test_datetime_roundtrip():
    """Test the timezone conversion functions."""
    utc_naive = datetime.datetime.utcnow().replace(microsecond=0)
    nyc = app.utc_to_nyc(utc_naive)
    assert app.nyc_to_utc(nyc, naive=True) == utc_naive


def test_no_readings_handler(client, monkeypatch):
    """Test the edge case when there are no readings."""
    readings = []
    monkeypatch.setattr(app, "get_readings", lambda *x, **y: readings)

    rv = client.get("/")
    html = rv.data.decode("utf-8")
    assert "no recent readings" in html

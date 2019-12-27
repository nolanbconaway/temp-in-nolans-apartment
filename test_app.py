"""Test the app."""
import datetime
import tempfile

import pytest

import app


@pytest.fixture
def client(monkeypatch):
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

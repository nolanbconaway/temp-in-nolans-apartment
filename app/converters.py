"""Flask URL converters."""

import datetime

from werkzeug.routing import BaseConverter


class DateConverter(BaseConverter):
    """Custom converter for dates."""

    def to_python(self, value):
        """Make a string into a date."""
        return datetime.datetime.strptime(value, "%Y-%m-%d")

    def to_url(self, value):
        """Make a date into a string."""
        return value.strftime("%Y-%m-%d")

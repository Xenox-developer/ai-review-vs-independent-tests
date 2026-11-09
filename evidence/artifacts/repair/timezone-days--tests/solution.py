from datetime import datetime
from zoneinfo import ZoneInfo


def solve(data):
    """Count offset-aware event timestamps by their date in the target zone."""
    zone = ZoneInfo(data['zone'])
    result = {}
    for value in data['events']:
        if not isinstance(value, str):
            raise ValueError('Event timestamps must be ISO8601 strings')
        # Normalize the UTC designator for Python versions predating Z support.
        timestamp = datetime.fromisoformat(
            value[:-1] + '+00:00' if value.endswith('Z') else value
        )
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError('Event timestamps must include a UTC offset')
        try:
            key = timestamp.astimezone(zone).date().isoformat()
        except OverflowError as error:
            raise ValueError('Local date is outside the supported range') from error
        result[key] = result.get(key, 0) + 1
    return result

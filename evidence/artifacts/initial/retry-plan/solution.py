def solve(data):
    """Return attempt timestamps for a capped exponential retry schedule."""
    if not isinstance(data, dict):
        raise ValueError('data must contain the retry fields')

    values = {}
    for name in ('max_attempts', 'base', 'cap', 'budget'):
        if name not in data:
            raise ValueError('missing field: ' + name)
        value = data[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(name + ' must be a nonnegative integer')
        values[name] = value

    attempts = values['max_attempts']
    if attempts > 100:
        raise ValueError('max_attempts must be at most 100')
    if attempts == 0:
        return []

    times = [0]
    delay = min(values['base'], values['cap'])
    for _ in range(attempts - 1):
        timestamp = times[-1] + delay
        if timestamp > values['budget']:
            break
        times.append(timestamp)
        delay = min(delay * 2, values['cap'])
    return times

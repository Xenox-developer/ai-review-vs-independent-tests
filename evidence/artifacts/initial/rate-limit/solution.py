from collections import deque


def solve(data):
    """Apply the sliding window independently to each key's accepted events."""
    window = data['window']
    limit = data['limit']
    histories = {}
    result = []

    for event in data['events']:
        timestamp = event['t']
        history = histories.setdefault(event['key'], deque())
        cutoff = timestamp - window
        while history and history[0] <= cutoff:
            history.popleft()

        if len(history) < limit:
            history.append(timestamp)
            result.append({'allowed': True, 'retry_after': 0})
        else:
            result.append({
                'allowed': False,
                'retry_after': history[0] + window - timestamp,
            })

    return result

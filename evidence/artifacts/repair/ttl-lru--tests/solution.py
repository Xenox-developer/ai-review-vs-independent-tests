from collections import OrderedDict


def solve(data):
    """Process cache events without modifying the input."""
    capacity = data['capacity']
    ttl = data['ttl']
    cache = OrderedDict()
    # Fixed TTL and nondecreasing event times keep this in expiry order.
    expirations = OrderedDict()
    results = []

    for event in data['events']:
        now = event['t']
        while expirations:
            oldest = next(iter(expirations))
            if expirations[oldest] > now:
                break
            del expirations[oldest]
            del cache[oldest]

        key = event['key']
        if event['op'] == 'put':
            cache[key] = event['value']
            cache.move_to_end(key)
            expirations[key] = now + ttl
            expirations.move_to_end(key)
            if len(cache) > capacity:
                evicted, _ = cache.popitem(last=False)
                del expirations[evicted]
        else:
            if key in cache:
                results.append(cache[key])
                cache.move_to_end(key)
            else:
                results.append(None)

    return results

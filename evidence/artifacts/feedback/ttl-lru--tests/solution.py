def solve(data):
    cache = {}
    out = []
    for e in data['events']:
        if e['op'] == 'put':
            cache[e['key']] = (e['value'], e['t'] + data['ttl'])
            if len(cache) > data['capacity']: cache.pop(next(iter(cache)))
        else:
            v = cache.get(e['key'])
            out.append(v[0] if v and v[1] >= e['t'] else None)
    return out

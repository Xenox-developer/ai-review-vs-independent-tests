def solve(data):
    times = []; out = []
    for e in data['events']:
        times = [t for t in times if t >= e['t'] - data['window']]
        allowed = len(times) < data['limit']
        out.append({'allowed':allowed,'retry_after':0 if allowed else data['window']})
        times.append(e['t'])
    return out

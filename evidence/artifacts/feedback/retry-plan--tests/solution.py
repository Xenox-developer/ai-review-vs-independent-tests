def solve(data):
    times = [0]
    for k in range(data['max_attempts'] - 1):
        t = times[-1] + data['base'] * 2**k
        if t >= data['budget']: break
        times.append(t)
    return times

def solve(data):
    result = {}
    for value in data['events']:
        key = value[:10]
        result[key] = result.get(key,0) + 1
    return result

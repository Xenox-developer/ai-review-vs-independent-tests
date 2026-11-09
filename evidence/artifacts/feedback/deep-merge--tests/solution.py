def solve(data):
    result = dict(data['base'])
    result.update(data['patch'])
    return result

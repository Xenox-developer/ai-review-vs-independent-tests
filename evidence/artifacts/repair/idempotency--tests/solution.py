def _json_equal(left, right):
    """Compare JSON values, preserving the distinction between bool and number."""
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, dict):
        return (isinstance(right, dict)
                and left.keys() == right.keys()
                and all(_json_equal(value, right[key])
                        for key, value in left.items()))
    if isinstance(left, list):
        return (isinstance(right, list)
                and len(left) == len(right)
                and all(_json_equal(a, b) for a, b in zip(left, right)))
    if isinstance(left, (int, float)):
        return isinstance(right, (int, float)) and left == right
    return type(left) is type(right) and left == right


def solve(data):
    seen = {}
    statuses = []
    applied = 0
    for request in data['requests']:
        key = request['key']
        payload = request['payload']
        if key in seen:
            statuses.append('duplicate' if _json_equal(seen[key], payload)
                            else 'conflict')
        elif request['ok']:
            seen[key] = payload
            statuses.append('applied')
            applied += 1
        else:
            statuses.append('failed')
    return {'statuses': statuses, 'applied': applied}

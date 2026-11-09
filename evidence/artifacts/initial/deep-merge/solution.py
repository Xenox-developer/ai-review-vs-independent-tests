"""Recursive JSON object merge without modifying either input."""

from copy import deepcopy


def solve(data):
    def merge(base, patch):
        result = deepcopy(base) if isinstance(base, dict) else {}
        for key, value in patch.items():
            if value is None:
                result.pop(key, None)
            elif isinstance(value, dict):
                result[key] = merge(result.get(key), value)
            else:
                result[key] = deepcopy(value)
        return result

    return merge(data['base'], data['patch'])

def solve(data):
    limit = data['limit']
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError('limit must be an integer between 1 and 100')

    def key(row):
        return row['timestamp'], row['id']

    after = data.get('after')
    rows = data['rows']
    if after is not None:
        cursor = tuple(after)
        rows = [row for row in rows if key(row) > cursor]
    ordered = sorted(rows, key=key)
    items = ordered[:limit]
    next_cursor = list(key(items[-1])) if len(ordered) > limit else None
    return {'items': items, 'next': next_cursor}

def solve(data):
    rows = sorted(data['rows'], key=lambda r: r['timestamp'])
    if data.get('after'):
        rows = [r for r in rows if r['timestamp'] > data['after'][0]]
    items = rows[:data['limit']]
    return {'items': items, 'next': [items[-1]['timestamp'], items[-1]['id']] if items else None}

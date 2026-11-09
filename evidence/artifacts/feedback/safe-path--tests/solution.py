def solve(data):
    value = data['path']
    if value.startswith('/') or '..' in value: raise ValueError('path')
    return value.strip('/')

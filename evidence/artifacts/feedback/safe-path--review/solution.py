from urllib.parse import unquote


def solve(data):
    path = unquote(data['path'], encoding='utf-8', errors='strict')
    if not path or path.startswith('/') or '\\' in path or '\x00' in path:
        raise ValueError('invalid relative path')

    components = path.split('/')
    if '..' in components:
        raise ValueError('parent component is not allowed')

    result = '/'.join(part for part in components if part not in ('', '.'))
    if not result:
        raise ValueError('empty relative path')
    return result

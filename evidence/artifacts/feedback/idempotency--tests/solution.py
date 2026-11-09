def solve(data):
    seen = {}
    out = []
    applied = 0
    for r in data['requests']:
        if r['key'] in seen: out.append('duplicate'); continue
        seen[r['key']] = r['payload']
        out.append('applied' if r['ok'] else 'failed')
        applied += bool(r['ok'])
    return {'statuses':out,'applied':applied}

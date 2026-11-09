"""Authored synthetic contracts and literal oracle examples, frozen before inference.

This module must NEVER be copied into a measured worker workspace.
"""
import json
import textwrap


def example(value, expected=None, error=None):
    return {"input": value, **({"error": error} if error else {"expect": expected})}


TASKS = []


def task(name, spec, starter, reference, public, hidden):
    TASKS.append(dict(id=name, spec=spec.strip(), starter=textwrap.dedent(starter).lstrip(),
                      reference=textwrap.dedent(reference).lstrip(), public=public, hidden=hidden))


task("pagination", """
Implement solve(data). data contains rows [{id: integer, timestamp: integer}], limit,
and optional after=[timestamp,id] (or null). Sort ascending by (timestamp,id), keep
only rows strictly greater than after, and return the first limit rows. Preserve all
row fields. limit must be an integer 1..100 inclusive; bool is invalid; raise
ValueError for invalid limit. Return {items: [...], next: [timestamp,id] or null}.
next is the last returned key ONLY if additional eligible rows remain. Do not
mutate input. Rows have unique ids; other inputs follow the stated schema.
""", """
def solve(data):
    rows = sorted(data['rows'], key=lambda r: r['timestamp'])
    if data.get('after'):
        rows = [r for r in rows if r['timestamp'] > data['after'][0]]
    items = rows[:data['limit']]
    return {'items': items, 'next': [items[-1]['timestamp'], items[-1]['id']] if items else None}
""", """
def solve(data):
    limit = data['limit']
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError('limit')
    rows = sorted(data['rows'], key=lambda r: (r['timestamp'], r['id']))
    after = data.get('after')
    if after is not None:
        rows = [r for r in rows if (r['timestamp'], r['id']) > tuple(after)]
    items = rows[:limit]
    return {'items': items, 'next': [items[-1]['timestamp'], items[-1]['id']] if len(rows) > limit else None}
""", [example({"rows":[],"limit":2}, {"items":[],"next":None})], [
    example({"rows":[{"id":2,"timestamp":1},{"id":1,"timestamp":1},{"id":3,"timestamp":2}],"limit":1}, {"items":[{"id":1,"timestamp":1}],"next":[1,1]}),
    example({"rows":[{"id":2,"timestamp":1},{"id":1,"timestamp":1}],"after":[1,1],"limit":5}, {"items":[{"id":2,"timestamp":1}],"next":None}),
    example({"rows":[{"id":1,"timestamp":0,"extra":"v"}],"after":None,"limit":1}, {"items":[{"id":1,"timestamp":0,"extra":"v"}],"next":None}),
    *[example({"rows":[],"limit":v}, error="ValueError") for v in [0,-1,101,True,1.0,"2"]],
    example({"rows":[{"id":1,"timestamp":0}],"after":[0,1],"limit":100}, {"items":[],"next":None})])

task("retry-plan", """
Implement solve(data) returning the integer timestamps of attempts, starting at 0.
max_attempts counts the first attempt. Delay before retry k (k starts at 0) is
min(base*2**k, cap); cumulative attempt time must be <= budget (inclusive).
max_attempts is an integer 0..100, base/cap/budget are nonnegative integers;
bool is invalid for all four. Invalid fields raise ValueError. base > cap is
allowed. Zero delay is allowed. Do not mutate input.
""", """
def solve(data):
    times = [0]
    for k in range(data['max_attempts'] - 1):
        t = times[-1] + data['base'] * 2**k
        if t >= data['budget']: break
        times.append(t)
    return times
""", """
def solve(data):
    n, base, cap, budget = [data[k] for k in ('max_attempts','base','cap','budget')]
    if any(type(v) is not int or v < 0 for v in (n,base,cap,budget)) or n > 100:
        raise ValueError('invalid field')
    result = []
    t = 0
    for i in range(n):
        if t > budget: break
        result.append(t)
        t += min(base * 2**i, cap)
    return result
""", [example({"max_attempts":3,"base":2,"cap":10,"budget":9},[0,2,6])], [
    example({"max_attempts":0,"base":1,"cap":4,"budget":0},[]),
    example({"max_attempts":4,"base":2,"cap":3,"budget":8},[0,2,5,8]),
    example({"max_attempts":3,"base":10,"cap":1,"budget":2},[0,1,2]),
    example({"max_attempts":4,"base":0,"cap":5,"budget":0},[0,0,0,0]),
    example({"max_attempts":1,"base":1,"cap":1,"budget":0},[0]),
    *[example({"max_attempts":3,"base":1,"cap":4,"budget":10, k:v},error="ValueError") for k,v in [("max_attempts",101),("max_attempts",True),("base",-1),("cap",False),("budget",1.5)]]])

task("ttl-lru", """
Implement solve(data) for a TTL/LRU cache. capacity is a positive integer and ttl
is a nonnegative integer. Events in nondecreasing integer time order are
{op:'put',t,key,value} or {op:'get',t,key}. Before EVERY event remove entries with
expiry <= t. put sets/replaces value, expiry=t+ttl, and makes key most recent;
if over capacity evict least recent. get returns value or null and, on a hit,
makes key most recent WITHOUT extending expiry. Return a list of get results.
Values are JSON primitives; keys are strings. Do not mutate input.
""", """
def solve(data):
    cache = {}
    out = []
    for e in data['events']:
        if e['op'] == 'put':
            cache[e['key']] = (e['value'], e['t'] + data['ttl'])
            if len(cache) > data['capacity']: cache.pop(next(iter(cache)))
        else:
            v = cache.get(e['key'])
            out.append(v[0] if v and v[1] >= e['t'] else None)
    return out
""", """
from collections import OrderedDict
def solve(data):
    cache = OrderedDict()
    out = []
    for e in data['events']:
        for key in list(cache):
            if cache[key][1] <= e['t']: del cache[key]
        key = e['key']
        if e['op'] == 'put':
            cache.pop(key, None)
            cache[key] = (e['value'], e['t'] + data['ttl'])
            if len(cache) > data['capacity']: cache.popitem(last=False)
        elif key in cache:
            out.append(cache[key][0]); cache.move_to_end(key)
        else: out.append(None)
    return out
""", [example({"capacity":1,"ttl":10,"events":[{"op":"get","t":0,"key":"x"}]},[None])], [
    example({"capacity":1,"ttl":2,"events":[{"op":"put","t":0,"key":"x","value":1},{"op":"get","t":2,"key":"x"}]},[None]),
    example({"capacity":2,"ttl":10,"events":[{"op":"put","t":0,"key":"a","value":1},{"op":"put","t":0,"key":"b","value":2},{"op":"get","t":1,"key":"a"},{"op":"put","t":1,"key":"c","value":3},{"op":"get","t":2,"key":"b"},{"op":"get","t":2,"key":"a"},{"op":"get","t":10,"key":"a"}]},[1,None,1,None]),
    example({"capacity":2,"ttl":3,"events":[{"op":"put","t":0,"key":"a","value":1},{"op":"put","t":1,"key":"b","value":2},{"op":"put","t":2,"key":"a","value":3},{"op":"put","t":2,"key":"c","value":4},{"op":"get","t":2,"key":"b"},{"op":"get","t":4,"key":"a"},{"op":"get","t":5,"key":"a"}]},[None,3,None]),
    example({"capacity":1,"ttl":0,"events":[{"op":"put","t":0,"key":"a","value":False},{"op":"get","t":0,"key":"a"}]},[None]),
    example({"capacity":1,"ttl":5,"events":[{"op":"put","t":0,"key":"a","value":0},{"op":"get","t":1,"key":"a"},{"op":"get","t":4,"key":"a"},{"op":"get","t":5,"key":"a"}]},[0,0,None])])

task("idempotency", """
Implement solve(data), processing requests {key, payload, ok}. payload is any JSON
value. Equal JSON objects ignore key order; arrays preserve order; booleans are
different from numbers; numeric 1 equals 1.0. Successful requests are persisted
by key. A later equal payload returns 'duplicate' even if ok is false. A later
different payload returns 'conflict'. A new key with ok=false returns 'failed'
and stores nothing; with ok=true returns 'applied' and stores payload. Return
{statuses: [...], applied: count}. Failed requests must be retryable. No mutation.
""", """
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
""", """
def tagged(v):
    if v is None: return ('null',)
    if isinstance(v, bool): return ('bool', v)
    if isinstance(v, (int,float)): return ('number', v)
    if isinstance(v,str): return ('string',v)
    if isinstance(v,list): return ('array',tuple(tagged(x) for x in v))
    return ('object',tuple(sorted((k,tagged(x)) for k,x in v.items())))
def solve(data):
    seen = {}; statuses = []; count = 0
    for r in data['requests']:
        key, payload = r['key'], tagged(r['payload'])
        if key in seen: status = 'duplicate' if seen[key] == payload else 'conflict'
        elif not r['ok']: status = 'failed'
        else: seen[key] = payload; status = 'applied'; count += 1
        statuses.append(status)
    return {'statuses':statuses,'applied':count}
""", [example({"requests":[]},{"statuses":[],"applied":0})], [
    example({"requests":[{"key":"k","payload":1,"ok":False},{"key":"k","payload":2,"ok":True},{"key":"k","payload":1,"ok":True}]},{"statuses":["failed","applied","conflict"],"applied":1}),
    example({"requests":[{"key":"k","payload":{"a":1,"b":[2,3]},"ok":True},{"key":"k","payload":{"b":[2,3],"a":1.0},"ok":False},{"key":"k","payload":{"b":[3,2],"a":1},"ok":True}]},{"statuses":["applied","duplicate","conflict"],"applied":1}),
    example({"requests":[{"key":"k","payload":True,"ok":True},{"key":"k","payload":1,"ok":True}]},{"statuses":["applied","conflict"],"applied":1}),
    example({"requests":[{"key":"a","payload":None,"ok":True},{"key":"b","payload":None,"ok":True},{"key":"a","payload":None,"ok":False}]},{"statuses":["applied","applied","duplicate"],"applied":2})])

task("timezone-days", """
Implement solve(data): given zone (IANA timezone) and events (ISO8601 timestamps),
return {local YYYY-MM-DD: count} after converting each timestamp to that zone.
Accept Z or numeric UTC offsets; timestamps without an offset must raise
ValueError, even if other events are valid. Invalid dates raise ValueError.
Use standard-library zoneinfo, account for daylight saving time. Empty events
returns {}. Input zone is valid. Do not mutate input.
""", """
def solve(data):
    result = {}
    for value in data['events']:
        key = value[:10]
        result[key] = result.get(key,0) + 1
    return result
""", """
from datetime import datetime
from zoneinfo import ZoneInfo
def solve(data):
    result = {}; zone = ZoneInfo(data['zone'])
    for value in data['events']:
        stamp = datetime.fromisoformat(value.replace('Z','+00:00'))
        if stamp.tzinfo is None or stamp.utcoffset() is None: raise ValueError('naive timestamp')
        key = stamp.astimezone(zone).date().isoformat()
        result[key] = result.get(key,0) + 1
    return result
""", [example({"zone":"UTC","events":["2026-01-01T12:00:00Z"]},{"2026-01-01":1})], [
    example({"zone":"America/New_York","events":["2026-03-08T04:59:59Z","2026-03-08T05:00:00Z","2026-03-08T07:00:00Z"]},{"2026-03-07":1,"2026-03-08":2}),
    example({"zone":"America/New_York","events":["2026-11-01T05:30:00Z","2026-11-01T06:30:00Z","2026-11-02T04:59:59Z","2026-11-02T05:00:00Z"]},{"2026-11-01":3,"2026-11-02":1}),
    example({"zone":"Asia/Kathmandu","events":["2026-01-01T18:15:00Z","2026-01-02T00:30:00+06:30"]},{"2026-01-02":1,"2026-01-01":1}),
    example({"zone":"UTC","events":["2026-01-01T12:00:00"]},error="ValueError"),
    example({"zone":"UTC","events":["2026-02-30T12:00:00Z"]},error="ValueError"),
    example({"zone":"UTC","events":[]},{})])

task("safe-path", """
Implement solve(data) returning a canonical relative POSIX path. data.path is a
URL-encoded string: percent-decode EXACTLY ONCE with urllib.parse.unquote using
strict UTF-8 errors. Reject by raising ValueError: empty result; leading slash;
backslash; NUL; any decoded component exactly '..'. Remove empty components
and '.' components, joining with '/'; reject if nothing remains. Dots inside
ordinary names are allowed. A percent sequence remaining after one decode is
literal (do not decode recursively). '+' stays '+'. Do not access filesystem
or mutate input. No requirement to reject malformed percent escapes themselves.
""", """
def solve(data):
    value = data['path']
    if value.startswith('/') or '..' in value: raise ValueError('path')
    return value.strip('/')
""", """
from urllib.parse import unquote
def solve(data):
    try: value = unquote(data['path'], errors='strict')
    except UnicodeError as e: raise ValueError('encoding') from e
    if not value or value.startswith('/') or '\\\\' in value or '\\0' in value:
        raise ValueError('path')
    parts = value.split('/')
    if '..' in parts: raise ValueError('traversal')
    result = '/'.join(p for p in parts if p not in ('','.'))
    if not result: raise ValueError('empty')
    return result
""", [example({"path":"docs/a.txt"},"docs/a.txt")], [
    example({"path":"a/%2e%2e/b"},error="ValueError"),
    example({"path":"%2fetc/passwd"},error="ValueError"),
    example({"path":"a%5cb"},error="ValueError"),
    example({"path":"a%00b"},error="ValueError"),
    example({"path":"a//./b/"},"a/b"),
    example({"path":"a/.../b+z"},"a/.../b+z"),
    example({"path":"%252e%252e/x"},"%2e%2e/x"),
    example({"path":"./"},error="ValueError"),
    example({"path":"%ff"},error="ValueError"),
    example({"path":""},error="ValueError")])

task("deep-merge", """
Implement solve(data), merging patch into base (both JSON objects). Object-valued
patches recursively merge into the corresponding object or into {} if the old
value is not an object. A null member in a patch object deletes that key if
present. Arrays replace in full, including null array elements; all other values
replace. Empty patch objects preserve an existing object, but replace a scalar
or array with {}. Return merged object. Do not mutate base or patch.
""", """
def solve(data):
    result = dict(data['base'])
    result.update(data['patch'])
    return result
""", """
from copy import deepcopy
def merge(base, patch):
    result = deepcopy(base) if isinstance(base, dict) else {}
    for key, value in patch.items():
        if value is None: result.pop(key, None)
        elif isinstance(value, dict): result[key] = merge(result.get(key),value)
        else: result[key] = deepcopy(value)
    return result
def solve(data):
    return merge(data['base'], data['patch'])
""", [example({"base":{"x":1},"patch":{"x":2}},{"x":2})], [
    example({"base":{"a":{"x":1,"y":2},"b":3},"patch":{"a":{"x":None,"z":4},"b":None}},{"a":{"y":2,"z":4}}),
    example({"base":{"a":[1,2],"b":1},"patch":{"a":[None],"b":{}}},{"a":[None],"b":{}}),
    example({"base":{"a":{"b":1}},"patch":{"a":{}}},{"a":{"b":1}}),
    example({"base":{},"patch":{"a":{"b":None,"c":2}}},{"a":{"c":2}}),
    example({"base":{"a":[1]},"patch":{"a":{"x":3}}},{"a":{"x":3}}),
    example({"base":{"a":{"b":{"c":1,"d":2}}},"patch":{"a":{"b":{"c":3}}}},{"a":{"b":{"c":3,"d":2}}})])

task("rate-limit", """
Implement solve(data), a per-key sliding-window limiter. positive integer window
and limit; events {t: nonnegative integer, key: string} in nondecreasing time
order (different keys may share timestamps). At time t discard accepted events
with timestamp <= t-window for that key. If fewer than limit remain, accept
and record t; otherwise reject WITHOUT recording. Return a list of
{allowed: bool, retry_after: integer}: accepted gives 0; rejected gives
oldest retained timestamp + window - t. No sleeping, no mutation.
""", """
def solve(data):
    times = []; out = []
    for e in data['events']:
        times = [t for t in times if t >= e['t'] - data['window']]
        allowed = len(times) < data['limit']
        out.append({'allowed':allowed,'retry_after':0 if allowed else data['window']})
        times.append(e['t'])
    return out
""", """
from collections import defaultdict, deque
def solve(data):
    seen = defaultdict(deque); out = []
    for event in data['events']:
        t = event['t']; q = seen[event['key']]
        while q and q[0] <= t - data['window']: q.popleft()
        allowed = len(q) < data['limit']
        out.append({'allowed':allowed,'retry_after':0 if allowed else q[0]+data['window']-t})
        if allowed: q.append(t)
    return out
""", [example({"window":10,"limit":1,"events":[]},[])], [
    example({"window":10,"limit":1,"events":[{"t":0,"key":"a"},{"t":9,"key":"a"},{"t":10,"key":"a"},{"t":11,"key":"a"}]},[{"allowed":True,"retry_after":0},{"allowed":False,"retry_after":1},{"allowed":True,"retry_after":0},{"allowed":False,"retry_after":9}]),
    example({"window":5,"limit":1,"events":[{"t":1,"key":"a"},{"t":1,"key":"b"},{"t":1,"key":"a"},{"t":6,"key":"b"}]},[{"allowed":True,"retry_after":0},{"allowed":True,"retry_after":0},{"allowed":False,"retry_after":5},{"allowed":True,"retry_after":0}]),
    example({"window":5,"limit":2,"events":[{"t":0,"key":"a"},{"t":1,"key":"a"},{"t":2,"key":"a"},{"t":5,"key":"a"},{"t":6,"key":"a"},{"t":7,"key":"a"}]},[{"allowed":True,"retry_after":0},{"allowed":True,"retry_after":0},{"allowed":False,"retry_after":3},{"allowed":True,"retry_after":0},{"allowed":True,"retry_after":0},{"allowed":False,"retry_after":3}])])


def export():
    return json.loads(json.dumps(TASKS, sort_keys=True))

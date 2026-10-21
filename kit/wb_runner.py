# Workbench runner (Oct 21, 2026). Exec AFTER bali_metrics.py, bali_cover.py, bali_show.py and bali_slack.py.
# Why: the workbench's background threads hang or lose Composio auth between cells, and each tool call times out
# after about 60 seconds. So every Close read goes through a cache: a pass of the scorecard code runs with no network,
# records the reads it is missing (MISSES) and gets [] for them; fetch() then pulls the missing reads in parallel, one
# page at a time, within a time budget; repeat until a pass has no misses. That last pass is the real result.
# Usage, one setter at a time, every cell under ~45 seconds:
#   use_setter('jose'); D = dt.date(2026, 10, 20)
#   m, left = drive(lambda: run_show(D, run_cover(D)))   # repeat this cell until left == 0, then use m
import time, threading
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

GA_ORIG = globals().get('GA_ORIG') or get_all
CACHE, MISSES, PARTIAL = {}, {}, {}

def _key(ep, params): return (ep, json.dumps(params, sort_keys=True))

def get_all(ep, params, maxn=20000, stop=None):
    k = _key(ep, params)
    if k in CACHE: return [dict(x) for x in CACHE[k]]
    MISSES[k] = (ep, dict(params), maxn, stop)
    return []

def _page(k):
    ep, p, mx, st = MISSES[k]
    items, skip = PARTIAL.get(k, ([], 0))
    q = dict(p); q['_skip'] = skip; q.setdefault('_limit', 100)
    r, e = _q(proxy_execute, 'GET', ep, 'close', query_params=q)
    if e: raise Exception(str(e)[:300])
    body = r.get('data')
    if isinstance(body, dict): got = body.get('data', []); more = body.get('has_more')
    else: got = body or []; more = r.get('has_more') if r.get('has_more') is not None else len(got) == q['_limit']
    items = items + got; skip += len(got)
    done = (not more) or (not got) or len(items) >= mx or bool(st and got and st(got[-1]))
    PARTIAL[k] = (items, skip)
    if done: CACHE[k] = items
    return done

def fetch(budget=40, workers=8):
    """Pull the missing reads (page by page, in parallel) for up to `budget` seconds. Returns how many are left."""
    t0 = time.time(); q = [k for k in MISSES if k not in CACHE]
    ex = ThreadPoolExecutor(workers); futs = {}
    def sub(k=None):
        k = k or (q.pop(0) if q else None)
        if k: futs[ex.submit(_page, k)] = k
    for _ in range(workers): sub()
    while futs and time.time() - t0 < budget:
        done, _ = wait(list(futs), timeout=max(1, budget - (time.time() - t0)), return_when=FIRST_COMPLETED)
        for f in done:
            k = futs.pop(f)
            try: fin = f.result()
            except Exception as e:
                if 'revoked or expired' in str(e).lower(): raise
                fin = False
            if time.time() - t0 < budget - 4: sub(None if fin else k)
    ex.shutdown(wait=False, cancel_futures=True)
    for k in list(MISSES):
        if k in CACHE: MISSES.pop(k)
    return len(MISSES)

def drive(fn, budget=40):
    """Run fn() from the cache, fetch what it missed, repeat, for up to `budget` seconds.
    Returns (result, misses_left); the result is final only when misses_left == 0."""
    t0 = time.time(); r, n = None, 1
    while time.time() - t0 < budget:
        MISSES.clear(); _SETS.clear()   # memoized closer sets from a pass with misses are incomplete
        r = fn(); n = len(MISSES)
        if not n: break
        fetch(budget=max(5, budget + 5 - (time.time() - t0)))
    return r, n

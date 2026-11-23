# Inbound setter scorecards straight from the Close API (Sheila, Nov 20, 2026), GET only, read only.
# Usage, from kit/:  python3 run_inbound.py 2026-11-19 [jose jordan dave] --flags ../flags --out ..
# Writes inbound-<key>.json for each setter; render with inbound_build.py. Same Close access as run_direct.py.
import sys, os, json, datetime as dt, argparse, time

ap = argparse.ArgumentParser()
ap.add_argument('date'); ap.add_argument('keys', nargs='*', default=['jose', 'jordan', 'dave'])
ap.add_argument('--flags', default=None); ap.add_argument('--out', default='..')
a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
G = {'__name__': 'kit', 'dt': dt, 'json': json, '__file__': os.path.join(here, 'inbound.py')}
exec(open(os.path.join(here, 'close_direct.py')).read(), G)
for f in ['bali_metrics.py', 'bali_cover.py', 'bali_show.py', 'inbound.py']:
    exec(compile(open(os.path.join(here, f)).read(), f, 'exec'), G)
D = dt.date.fromisoformat(a.date); res = {}
for key in a.keys:
    t0 = time.time()
    r = G['run_inbound'](D, key, a.flags)
    p = os.path.join(a.out, f'inbound-{key}.json')
    json.dump(r, open(p, 'w'), default=str, indent=1)
    res[key] = dict(sets_today=r['sets_today'], sets_week=r['sets_week'], calls=r['calls_taken'],
                    verdict=(r.get('today') or {}).get('verdict'), file=p, seconds=round(time.time() - t0))
print(json.dumps(res, indent=1))

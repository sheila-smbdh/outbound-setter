# Daily setter scorecards straight from the Close API (Sheila, Nov 4, 2026), no Composio workbench.
# Usage, from kit/:  python3 run_direct.py 2026-11-03 [jose jordan] --out ..
# Bali left the team (Sheila, Nov 11, 2026): no daily card for him; pass 'bali' by name only for an old day.
# Writes metrics-<key>.json for each setter (dialed False = no calls that day), then render with build.py.
import sys, os, json, datetime as dt, argparse, time

ap = argparse.ArgumentParser()
ap.add_argument('date'); ap.add_argument('keys', nargs='*', default=['jose', 'jordan'])
ap.add_argument('--out', default='..')
a = ap.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
G = {'__name__': 'kit', 'dt': dt, 'json': json}
exec(open(os.path.join(here, 'close_direct.py')).read(), G)
for f in ['bali_metrics.py', 'bali_cover.py', 'bali_show.py', 'bali_slack.py']:
    exec(compile(open(os.path.join(here, f)).read(), f, 'exec'), G)
D = dt.date.fromisoformat(a.date); res = {}
for key in a.keys:
    t0 = time.time()
    G['use_setter'](key)
    m = G['run_show'](D, G['run_cover'](D))
    m['slack_check'] = {'skipped': 'not sent'}
    p = os.path.join(a.out, f'metrics-{key}.json')
    json.dump(m, open(p, 'w'), default=str)
    res[key] = dict(dialed=m.get('dialed'), dials=m.get('dials'), people=m.get('people_dialed'),
                    file=p, seconds=round(time.time() - t0))
print(json.dumps(res, indent=1))

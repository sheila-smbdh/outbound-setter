# Objection check: collect the day's real conversations and start the transcription batch.
# Runs inside the Composio remote workbench (proxy_execute reaches Close through the `close` toolkit).
# Exec order: oc_collect.py, then call start_day(D). oc_tx.py and oc_batch.py are written to /home/user by write_helpers().
import os, sys, json, subprocess, datetime as dt
from zoneinfo import ZoneInfo
ET = ZoneInfo('America/New_York')
SETTERS = {
    'user_c0wPSKtEPsqkIh08OnjiGaj6XHeFBjGSp2jyVxAggDl': 'Bali (Jabali Dumas)',
    'user_3IrYZLUcCBZrg2mb49wCybrxGBFTCxa5eqTHhE1ApuC': 'Jordan Kempster',
    'user_msFtSHmZcoRAYvHX8aGrnygBzOy4u1GnLrRSFfIdcgk': 'Jose Rodriguez',
}
MIN_SEC = 60          # real conversations only: recordings of 60+ seconds (Sheila, Oct 25)
ROOT = '/mnt/files/objections'

def _page(ep, params):
    out, skip = [], 0
    while True:
        r, e = proxy_execute('GET', ep, 'close', query_params=dict(params, _limit=100, _skip=skip))
        if e: raise Exception(str(e)[:300])
        body = r.get('data')
        if isinstance(body, dict): items, more = body.get('data', []), body.get('has_more')
        else: items, more = body or [], r.get('has_more', len(body or []) == 100)
        out += items; skip += len(items)
        if not more or not items: return out

def day_calls(D):
    a = dt.datetime(D.year, D.month, D.day, tzinfo=ET); b = a + dt.timedelta(days=1)
    q = {'date_created__gte': a.astimezone(dt.timezone.utc).isoformat(), 'date_created__lt': b.astimezone(dt.timezone.utc).isoformat()}
    calls = []
    for uid in SETTERS: calls += _page('/activity/call/', dict(q, user_id=uid))
    return calls

def lead_names(ids):
    names = {}
    for lid in ids:
        r, e = proxy_execute('GET', f'/lead/{lid}/', 'close', query_params={'_fields': 'display_name'})
        if not e:
            body = r.get('data') if isinstance(r.get('data'), dict) else r
            names[lid] = (body or {}).get('display_name') or ''
    return names

def outcome_names():
    try: return {o['id']: o.get('name') or '' for o in _page('/outcome/', {})}
    except Exception: return {}

def write_helpers():
    here = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/mnt/files'
    for f in ('oc_tx.py', 'oc_batch.py'):
        src = os.path.join(here, f)
        if not os.path.exists(src): src = os.path.join('/mnt/files', f)
        open(f'/home/user/{f}', 'w').write(open(src).read())

def start_day(D):
    """Pull the three setters' calls on D (ET), keep recordings of 60+ sec, save the call list and start
    the background transcription. Returns a short summary. Poll with batch_status(D)."""
    calls = day_calls(D)
    keep = [c for c in calls if c.get('recording_url') and (c.get('recording_duration') or 0) >= MIN_SEC]
    names = lead_names({c['lead_id'] for c in keep})
    outs = outcome_names()
    rows = [{
        'id': c['id'], 'setter': SETTERS[c['user_id']], 'lead_id': c['lead_id'], 'lead': names.get(c['lead_id'], ''),
        'direction': c.get('direction'), 'duration': c.get('duration'), 'recording_duration': c.get('recording_duration'),
        'at_et': dt.datetime.fromisoformat(c['date_created'].replace('Z', '+00:00')).astimezone(ET).strftime('%H:%M'),
        'outcome': outs.get(c.get('outcome_id') or '', ''), 'note': (c.get('note') or '')[:300],
        'close_url': f"https://app.close.com/lead/{c['lead_id']}/#activityId={c['id']}", 'recording_url': c['recording_url'],
    } for c in sorted(keep, key=lambda c: -(c.get('recording_duration') or 0))]
    d = f'{ROOT}/{D.isoformat()}'; os.makedirs(d, exist_ok=True)
    json.dump(rows, open(f'{d}/calls.json', 'w'))
    dials = {n: sum(1 for c in calls if SETTERS[c['user_id']] == n) for n in SETTERS.values()}
    write_helpers()
    if rows:
        subprocess.Popen([sys.executable, '/home/user/oc_batch.py', f'{d}/calls.json', f'{d}/tx'],
                         stdout=open('/home/user/oc_batch.log', 'w'), stderr=subprocess.STDOUT, start_new_session=True)
    return {'date': D.isoformat(), 'calls_by_setter': dials, 'recordings_60s': len(rows),
            'audio_min': round(sum(r['recording_duration'] for r in rows) / 60, 1)}

def batch_status(D):
    d = f'{ROOT}/{D.isoformat()}'
    rows = json.load(open(f'{d}/calls.json'))
    done = [r['id'] for r in rows if os.path.exists(f"{d}/tx/{r['id']}.json")]
    return {'done': len(done), 'total': len(rows), 'finished': os.path.exists(f'{d}/tx/DONE')}

def bundle(D):
    """One JSON with every call row and its transcript (speaker-unlabeled segments), for grading in the Claude session."""
    d = f'{ROOT}/{D.isoformat()}'
    rows = json.load(open(f'{d}/calls.json'))
    for r in rows:
        p = f"{d}/tx/{r['id']}.json"
        t = json.load(open(p)) if os.path.exists(p) else {'error': 'missing'}
        r.pop('recording_url', None)
        r['error'] = t.get('error')
        r['transcript'] = '\n'.join(f"[{int(s['s'])//60}:{int(s['s'])%60:02d}] {s['t']}" for s in t.get('segments', []))
    json.dump(rows, open(f'{d}/bundle.json', 'w'), separators=(',', ':'))
    return f'{d}/bundle.json'

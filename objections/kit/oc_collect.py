# Objection check, workbench side: list the day's 60+ second calls and hand the Claude session signed links.
# Runs inside the Composio remote workbench (proxy_execute reaches Close through the `close` toolkit). The workbench
# (1 CPU, ~1 GB RAM) is too small to transcribe long calls (Oct 25: out-of-memory kills and two crashes), so it only
# collects: the Claude session downloads the audio and the model from the signed links and transcribes (oc_local.py).
import os, sys, json, subprocess, datetime as dt, contextlib, io, requests
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo
ET = ZoneInfo('America/New_York')
SETTERS = {
    'user_c0wPSKtEPsqkIh08OnjiGaj6XHeFBjGSp2jyVxAggDl': 'Bali (Jabali Dumas)',
    'user_3IrYZLUcCBZrg2mb49wCybrxGBFTCxa5eqTHhE1ApuC': 'Jordan Kempster',
    'user_msFtSHmZcoRAYvHX8aGrnygBzOy4u1GnLrRSFfIdcgk': 'Jose Rodriguez',
}
MIN_SEC = 60          # real conversations only: recordings of 60+ seconds (Sheila, Oct 25)
MODEL = 'small.en'    # faster-whisper model the Claude session runs
MODEL_FILES = ('config.json', 'tokenizer.json', 'vocabulary.txt', 'model.bin')

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
    def one(lid):
        r, e = proxy_execute('GET', f'/lead/{lid}/', 'close', query_params={'_fields': 'display_name'})
        body = (r.get('data') if isinstance(r.get('data'), dict) else r) if not e else {}
        return lid, (body or {}).get('display_name') or ''
    with ThreadPoolExecutor(8) as ex: return dict(ex.map(one, ids))

def outcome_names():
    try: return {o['id']: o.get('name') or '' for o in _page('/outcome/', {})}
    except Exception: return {}

def _signed(recording_url):
    """proxy_execute returns {} for binary, so call the raw endpoint it wraps; binary_data.url is signed for 1 hour."""
    base = os.environ.get('BACKEND_URL', '').rstrip('/')
    hdr = {'x-session-' + 'access-key': os.environ.get('COMPOSIO_' + 'WORKBENCH_ACCESS_KEY') or ''}
    r = requests.post(base + '/api/v3/tool_router/internal/proxy_execute', headers=hdr, timeout=60,
                      json={'toolkit_slug': 'close', 'endpoint': recording_url, 'method': 'GET'}).json()
    return (r.get('binary_data') or {}).get('url')

def _share(path):
    """Upload a workbench file and return the direct storage link (the Claude container can't reach the short link)."""
    with contextlib.redirect_stdout(io.StringIO()):
        up, e = upload_local_file(path)
    if e: raise Exception(str(e)[:300])
    r = requests.get(up['s3_url'], allow_redirects=False, timeout=60)
    return r.headers.get('location') or up['s3_url']

def _prepare(D):
    """Pull the three setters' calls on D (ET), keep recordings of 60+ sec, sign each recording link, and share the
    list as one JSON file. Returns a small summary with `calls_link` for the Claude session."""
    calls = day_calls(D)
    keep = [c for c in calls if c.get('recording_url') and (c.get('recording_duration') or 0) >= MIN_SEC]
    names = lead_names({c['lead_id'] for c in keep})
    outs = outcome_names()
    with ThreadPoolExecutor(6) as ex:
        signed = dict(zip([c['id'] for c in keep], ex.map(lambda c: _signed(c['recording_url']), keep)))
    rows = [{
        'id': c['id'], 'setter': SETTERS[c['user_id']], 'lead_id': c['lead_id'], 'lead': names.get(c['lead_id'], ''),
        'direction': c.get('direction'), 'duration': c.get('duration'), 'recording_duration': c.get('recording_duration'),
        'at_et': dt.datetime.fromisoformat(c['date_created'].replace('Z', '+00:00')).astimezone(ET).strftime('%H:%M'),
        'outcome': outs.get(c.get('outcome_id') or '', ''), 'note': (c.get('note') or '')[:300],
        'close_url': f"https://app.close.com/lead/{c['lead_id']}/#activityId={c['id']}", 'audio_url': signed.get(c['id']),
    } for c in sorted(keep, key=lambda c: -(c.get('recording_duration') or 0))]
    p = f'/home/user/oc-calls-{D.isoformat()}.json'
    by_setter = {n: sum(1 for c in calls if SETTERS[c['user_id']] == n) for n in SETTERS.values()}
    json.dump({'date': D.isoformat(), 'calls_by_setter': by_setter, 'rows': rows}, open(p, 'w'))
    return {'date': D.isoformat(), 'calls_by_setter': by_setter, 'recordings_60s': len(rows),
            'unsigned': sum(1 for r in rows if not r['audio_url']),
            'audio_min': round(sum(r['recording_duration'] for r in rows) / 60, 1), 'calls_link': _share(p)}

DL = """import requests, os, sys
d = sys.argv[1]; os.makedirs(d, exist_ok=True)
for f in %r:
    with requests.get('https://huggingface.co/Systran/faster-whisper-%s/resolve/main/' + f, stream=True, timeout=120) as r:
        with open(d + '/' + f, 'wb') as fh:
            for ch in r.iter_content(1 << 22): fh.write(ch)
open(d + '/OK', 'w').write('ok')
"""

def _model_links(name=MODEL):
    """Signed links to the faster-whisper model files (huggingface.co is blocked from the Claude container).
    A fresh workbench downloads the model first, in the background (about a minute for small.en): this returns
    'downloading' until it's there; call again."""
    d = f'/home/user/whisper-{name}'
    if not os.path.exists(d + '/OK'):
        if not os.path.exists(d + '.started'):
            open(d + '.started', 'w').write('1'); open('/home/user/oc_dl.py', 'w').write(DL % (MODEL_FILES, name))
            subprocess.Popen([sys.executable, '/home/user/oc_dl.py', d], start_new_session=True,
                             stdout=open('/home/user/oc_dl.log', 'w'), stderr=subprocess.STDOUT)
        return 'downloading'
    return {f: _share(f'{d}/{f}') for f in MODEL_FILES}

# Both jobs can take longer than one cell may run (the MCP client gives up at 60 seconds, Oct 25), so they run in a
# kernel thread. Call prepare(D) / model_links() again until the answer is not 'working'.
JOBS = {}
def _bg(key, fn, *a):
    import threading
    j = JOBS.get(key)
    if j is None:
        j = JOBS[key] = {'done': False}
        def go():
            try: j['result'] = fn(*a)
            except Exception as e: j['result'] = {'error': str(e)[:300]}
            j['done'] = True
        threading.Thread(target=go, daemon=True).start()
    if not j['done']: return 'working'
    r = j['result']
    if r == 'downloading': JOBS.pop(key)   # model still downloading: start over on the next call
    return r

def prepare(D): return _bg(('prepare', D.isoformat()), _prepare, D)
def model_links(name=MODEL): return _bg(('model', name), _model_links, name)

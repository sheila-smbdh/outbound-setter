# Objection check, Claude-container side: fetch the model and the day's recordings from the signed links that
# oc_collect.py hands over, transcribe every call, and write one bundle for grading.
#   python3 oc_local.py model LINKS.json MODEL_DIR        (LINKS.json = the dict model_links() returned)
#   python3 oc_local.py run CALLS_LINK WORKDIR MODEL_DIR   (CALLS_LINK = prepare()['calls_link'], or a local path)
import os, sys, json, subprocess, urllib.request
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
JOBS = max(1, (os.cpu_count() or 2) // 2)   # transcriptions at once; 2 threads each

def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return path
    with urllib.request.urlopen(url, timeout=300) as r, open(path + '.part', 'wb') as f:
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b)
    os.rename(path + '.part', path); return path

def model(links_json, d):
    os.makedirs(d, exist_ok=True)
    for f, u in json.load(open(links_json)).items(): fetch(u, os.path.join(d, f))
    print({f: os.path.getsize(os.path.join(d, f)) for f in os.listdir(d)})

def run(calls_link, work, model_dir):
    os.makedirs(f'{work}/audio', exist_ok=True); os.makedirs(f'{work}/tx', exist_ok=True)
    src = calls_link if os.path.exists(calls_link) else fetch(calls_link, f'{work}/calls.json')
    day = json.load(open(src)); rows = day['rows']
    def one(r):
        out = f"{work}/tx/{r['id']}.json"
        if os.path.exists(out): return
        try:
            mp = fetch(r['audio_url'], f"{work}/audio/{r['id']}.mp3")
            p = subprocess.run([sys.executable, f'{HERE}/oc_tx.py', mp, out, model_dir, '2'], capture_output=True, text=True, timeout=3600)
            if not os.path.exists(out): json.dump({'error': f'rc={p.returncode} {p.stderr[-300:]}'}, open(out, 'w'))
        except Exception as e:
            json.dump({'error': str(e)[:300]}, open(out, 'w'))
    with ThreadPoolExecutor(JOBS) as ex: list(ex.map(one, rows))
    for r in rows:
        t = json.load(open(f"{work}/tx/{r['id']}.json"))
        r.pop('audio_url', None); r['error'] = t.get('error')
        r['transcript'] = '\n'.join(f"[{int(s['s'])//60}:{int(s['s'])%60:02d}] {s['t']}" for s in t.get('segments', []))
    json.dump(dict(day, rows=rows), open(f'{work}/bundle.json', 'w'), indent=1)
    print(json.dumps({'date': day['date'], 'calls_by_setter': day['calls_by_setter'], 'transcribed': sum(1 for r in rows if not r['error']),
                      'failed': [r['id'] for r in rows if r['error']], 'bundle': f'{work}/bundle.json'}))

if __name__ == '__main__':
    {'model': model, 'run': run}[sys.argv[1]](*sys.argv[2:])

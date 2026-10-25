# Background driver: python oc_batch.py calls.json outdir. Downloads each recording through the Composio close
# toolkit's raw proxy (binary_data.url, signed for 1 hour) and transcribes it in its own process. Resumable.
import os, sys, json, subprocess, requests, time
Q = json.load(open(sys.argv[1])); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
base = os.environ.get('BACKEND_URL', '').rstrip('/'); hk = 'x-session-' + 'access-key'; kv = os.environ.get('COMPOSIO_' + 'WORKBENCH_ACCESS_KEY') or ''
for c in Q:
    o = f"{OUT}/{c['id']}.json"
    if os.path.exists(o): continue
    try:
        r = requests.post(base + '/api/v3/tool_router/internal/proxy_execute', json={'toolkit_slug': 'close', 'endpoint': c['recording_url'], 'method': 'GET'}, headers={hk: kv}, timeout=90).json()
        u = (r.get('binary_data') or {}).get('url')
        mp = f"/home/user/{c['id']}.mp3"; open(mp, 'wb').write(requests.get(u, timeout=120).content)
        subprocess.run([sys.executable, '/home/user/oc_tx.py', mp, o], timeout=1800, capture_output=True)
        os.remove(mp)
        if not os.path.exists(o): json.dump({'error': 'transcribe failed'}, open(o, 'w'))
    except Exception as e:
        json.dump({'error': str(e)[:300]}, open(o, 'w'))
open(OUT + '/DONE', 'w').write(str(time.time()))

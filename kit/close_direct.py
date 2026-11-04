# Direct Close API for the scorecard kit (Sheila, Nov 4, 2026): GET only, read only.
# Replaces the Composio workbench's proxy_execute so the kit runs in the routine's own session. The cloud
# proxy adds the Close login to every request to api.close.com, so no key is needed here; CLOSE_API_KEY
# is used when set (a local machine). Anything but GET is refused before it is sent.
import os, time, requests

BASE = 'https://api.close.com/api/v1'
_S = requests.Session()
_S.auth = (os.environ.get('CLOSE_API_KEY') or 'proxy-injected', '')

def proxy_execute(method, endpoint, toolkit='close', query_params=None, body=None, headers=None):
    """Same call shape and return shape as the Composio helper: (dict(data=<json>), None) or (None, error)."""
    if (method or '').upper() != 'GET' or body is not None:
        return None, f'refused: only GET reads are allowed on Close ({method} {endpoint})'
    if toolkit != 'close':
        return None, f'refused: toolkit {toolkit}'
    url = BASE + '/' + endpoint.lstrip('/')
    for attempt in range(6):
        try:
            r = _S.get(url, params=query_params or {}, timeout=60)
        except requests.RequestException as e:
            if attempt == 5: return None, f'network error: {e}'
            time.sleep(2 ** attempt); continue
        if r.status_code == 429 or r.status_code >= 500:
            if attempt == 5: return None, f'HTTP {r.status_code}: {r.text[:200]}'
            time.sleep(float(r.headers.get('Retry-After') or 2 ** attempt)); continue
        if r.status_code != 200:
            return None, f'HTTP {r.status_code}: {r.text[:200]}'
        return dict(data=r.json()), None

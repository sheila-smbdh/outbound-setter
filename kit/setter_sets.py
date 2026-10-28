# Setter sets report (Sheila, Oct 28, 2026): every setter's inbound and outbound sets by month and week, from Close
# and from the self-reported tracker, plus where the closers bucketed each set lead. Feeds the "Setter Sets" dashboard.
# Runbook: docs/SETTER-SETS.md.
# Runs in the Composio workbench on its own (it needs none of the bali_*.py files). The workbench is shared, so every
# global is prefixed SS_ / _ss_. Each step saves to /home/user/setter_sets_state.pkl, so a restart resumes.
# Read only on Close and on the tracker sheet. Writes nothing anywhere.
# Usage, every cell under ~45 seconds:
#   ss_start(dt.date(2026, 8, 1), dt.date(2026, 10, 28))
#   ss_step()                          # repeat until it returns '... done'
#   out = ss_result()                  # {'monthly': csv text, 'weekly': ..., 'buckets': ..., 'leads': ...}
# The container can't download workbench files, so print each csv and copy it into data/setter-sets/<end date>/.
import collections, csv, datetime as dt, io, json, os, pickle, re, time
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

SS_ET = ZoneInfo('America/New_York')
SS_SETTERS = {'user_c0wPSKtEPsqkIh08OnjiGaj6XHeFBjGSp2jyVxAggDl': 'Bali',
              'user_TH3XzqxRNb7WhZ5taaJ9v3df27VAaU6KvCnFlCUbq9v': 'Yobani',
              'user_sByZkVjk2If3ioL4CC26O5JmTWuzzKzDEjr9fzZHJ26': 'Dave (David Martin)',   # dave@ (David Rendon) has no setter activity
              'user_fXLAvRIRIJxMAgcaYa2hH14SuwQphwF5aC9vtvouHob': 'Quinn',
              'user_3IrYZLUcCBZrg2mb49wCybrxGBFTCxa5eqTHhE1ApuC': 'Jordan Kempster',
              'user_msFtSHmZcoRAYvHX8aGrnygBzOy4u1GnLrRSFfIdcgk': 'Jose'}
SS_ORDER = ['Bali', 'Yobani', 'Dave (David Martin)', 'Quinn', 'Jordan Kempster', 'Jose']
# The 13 closers in bali_metrics.py CLOSERS, plus Ezra Isla, Chris Cha and Kameron Bryant, who also take discovery calls
SS_CLOSERS = {'user_6MNsV5izSPoZXcJP2YIpFugEBfZ4vFHSvKEpcwDqdGw', 'user_bWKARGZE8EbHRdVAwb1X7PKedIgSpk36pQqCNedoFux',
              'user_KljJRbJ4KU5gr2vYuVcQOXr2fwDrBRWF77rHsqIvmTP', 'user_e5ftkzIEvfPsrJiQL5iDkECWGn6zvgVRNNPP7736d75',
              'user_6WoeSFWodzS6EVPUlyUiEv1pplLvDiUokB28Cr72tSO', 'user_6MGs8qirvfVYunzojwPX9vxrGjYIxwW5caVU40i0V5l',
              'user_eE1A7LS7qtadfjtL4lWfnts3x6RBYBToJNRb5pT1Z23', 'user_f3vkQZe4xJvRsPV9L6cU1UOHk7nwxStq94aMqJYLqzm',
              'user_pjOhfDFMYSNFDKwgLEMHYOP1a9h8HjfwjSWekJnhx7j', 'user_2AigaoH78jJdTRUkOZYx4GGiefiBWKiRtR9m9T9LbTA',
              'user_FscBL0yyfYEgqQWD8ZBxvNkyrVfmIl2D6dKuLP2TPoi', 'user_GTts5Wcmueh0bn5bIMYXgF2TuvZ9qwKXu1kk9s0oLaT',
              'user_G5MW8qwDBNVPFYs9zFGoGUt834xgUxqbHSnCMD8t19U', 'user_IZsgcW3rxd1herqkr9P2OIkDvzekDImciId3Ni6nh4e',
              'user_rWfa75vFfzRRAVWIaixyDbaQDY9QQqq77htyXUNEcR1', 'user_Fg0PoYbm1Vcb0zZzY3NQW9hzFjBvoMuPq5s4L7S7lnc'}
SS_PRE = 'actitype_7eSCr8m78jZ35sh13poUg8'     # "001) Pre-Discovery Call", the setter's form
SS_DISC = 'actitype_4mIZqROw9obY6LQWDvGdtn'    # "002) Discovery Call", the closer's form
SS_PRE_TYPE = 'custom.cf_VzsnDPdz3FhFctUXEECIUUwCSBaG13JBiHLoboZHJwI'   # Inbound / Scheduled Intro, Inbound/ Scheduled Discovery, Outbound
SS_PRE_OUT = 'custom.cf_C6vBfqMyPQKFPCdDoVi2VxXD8yQhYo2Svnu8TrstKaz'    # "Pre-Strategy Call Outcome"
SS_SET_OUTCOME = '03. Discovery Call Scheduled'
SS_DISC_OUT = 'custom.cf_d6Xh2R1rxhHkMoo76I3O19HJCVbdrmeSczYD1bpV1IK'   # closer's "Call Outcome"
SS_TOUCH = dt.timedelta(hours=24)              # closer meeting created within 24h of the setter's call or intro call
SS_EXCLUDE = {('Bali', 'mattweiss'), ('Bali', 'danhousley')}   # Sheila, Oct 6: not Bali's sets (Oct 5)
SS_TRACKER_ID = '1TCO-KbUxwTs4qfLdmv2Dlt1BFipkdvfMRxW3Srwc_XI'   # "Sales Tracker 2026 - Setting team", tab Inputs
SS_TRACKER_NAMES = {'Bali': 'Bali', 'Yobani': 'Yobani', 'Dave': 'Dave (David Martin)', 'Quinn': 'Quinn',
                    'Jordan K.': 'Jordan Kempster', 'Jose': 'Jose'}
SS_STATE_PATH = '/home/user/setter_sets_state.pkl'   # /mnt/files fails on files this size (Errno 5)
SS_BUDGET = 25                                 # seconds of fetching per step (a workbench call is cut off at ~60)

# Closer buckets, most advanced first (a lead with duplicate records keeps its most advanced bucket)
SS_OPP_BUCKET = {'WON': 'Won', 'Next 7 Days': 'Short term: next 7 days', 'In Month Closing': 'Short term: in month closing',
                 'Split Pay/Deposit': 'Short term: split pay or deposit', 'Long Term w/ Intention': 'Long term: with intention',
                 'Long Term No Timeline': 'Long term: no timeline', 'Long Term Farm': 'Long term: farming',
                 'Offer Not Presented': 'Bad: offer not presented'}
SS_OUT_BUCKET = {'10. Sale': 'Won', 'Next 7 days': 'Short term: next 7 days', 'In Month Closing': 'Short term: in month closing',
                 '09. Deposit': 'Short term: split pay or deposit', 'Long Term w/ Intention': 'Long term: with intention',
                 'Long Term No Timeline': 'Long term: no timeline', 'Offer Not Presented': 'Bad: offer not presented',
                 'Bad Fit': 'Bad: bad fit'}
SS_BUCKETS = ['Won', 'Short term: next 7 days', 'Short term: in month closing', 'Short term: split pay or deposit',
              'Long term: with intention', 'Long term: no timeline', 'Long term: farming', 'Bad: bad fit',
              'Bad: offer not presented', 'Lost, other reason', 'No show or canceled', 'Reschedule pending',
              'Call still ahead', 'Call passed, closer has not updated']
SS_ST = {}


def _ss_get(ep, params):
    r, e = proxy_execute('GET', ep, 'close', query_params=params)
    if e: raise Exception(str(e)[:300])
    if isinstance(r, dict) and isinstance(r.get('data'), dict): return r['data']   # wrapped: {'data': {'data': [...], 'has_more': ...}}
    return r if isinstance(r, dict) else {'data': r}                              # raw Close body

def _ss_pages(ep, params):
    out, skip = [], 0
    while True:
        p = dict(params); p['_skip'] = skip; p['_limit'] = 100
        d = _ss_get(ep, p); out += d.get('data', [])
        if not d.get('has_more'): return out
        skip += 100

def _ss_t(s): return dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
def _ss_day(t): return t.astimezone(SS_ET).date()
def _ss_iso(d): return d.isoformat() + 'T00:00:00Z'
def _ss_name_key(s): return re.sub(r'[^a-z]', '', (s or '').lower())
def _ss_save():
    try:
        with open(SS_STATE_PATH, 'wb') as f: pickle.dump(SS_ST, f)
    except OSError: pass   # the run still works from memory; only a workbench restart loses progress

def _ss_windows(a, b, days):
    out, s = [], a
    while s < b:
        out.append((s, min(s + dt.timedelta(days=days), b))); s += dt.timedelta(days=days)
    return out


def ss_start(start, end):
    """Plan the pulls for sets booked start..end (ET days, both included)."""
    global SS_ST
    pull_from, pull_to = start - dt.timedelta(days=5), end + dt.timedelta(days=1)
    jobs = [('ca', '/activity/custom/', '', a, b) for a, b in _ss_windows(pull_from, pull_to, 7)]
    jobs += [('meet', '/activity/meeting/', '', a, b) for a, b in _ss_windows(pull_from, pull_to, 3)]
    jobs += [('call', '/activity/call/', u, a, b) for u in SS_SETTERS for a, b in _ss_windows(pull_from, pull_to, 7)]
    SS_ST = {'start': start, 'end': end, 'jobs': jobs, 'done': {}, 'tracker': None, 'opps': {}, 'names': {},
             'run_at': dt.datetime.now(dt.timezone.utc)}
    _ss_save()
    return f'{len(jobs)} pulls planned'


def _ss_job(j):
    kind, ep, user, a, b = j
    p = {'date_created__gte': _ss_iso(a), 'date_created__lt': _ss_iso(b)}
    if user: p['user_id'] = user
    return _ss_pages(ep, p)

def _ss_fetch(keys, fn, store):
    t0 = time.time()
    ex = ThreadPoolExecutor(8)          # not a with-block: its exit would wait for slow pulls past the time limit
    futs = {k: ex.submit(fn, k) for k in keys}
    try:
        for k, f in futs.items():
            try: store[k] = f.result(timeout=max(0.1, SS_BUDGET - (time.time() - t0)))
            except Exception as ex_:
                if 'revoked or expired' in str(ex_): raise
    finally:
        ex.shutdown(wait=False, cancel_futures=True)   # unfinished pulls are retried next step
        _ss_save()


def ss_step():
    global SS_ST
    if not SS_ST and os.path.exists(SS_STATE_PATH): SS_ST = pickle.load(open(SS_STATE_PATH, 'rb'))
    todo = [j for j in SS_ST['jobs'] if j not in SS_ST['done']]
    if todo:
        _ss_fetch(todo[:16], _ss_job, SS_ST['done'])
        return f'Close pulls: {len(SS_ST["done"])} of {len(SS_ST["jobs"])}'
    if SS_ST['tracker'] is None:
        SS_ST['tracker'] = _ss_tracker(); _ss_save()
        return f'tracker: {len(SS_ST["tracker"])} rows'
    if 'sets' not in SS_ST:
        SS_ST['sets'] = _ss_find_sets(); _ss_save()
        return f'sets found: {len(SS_ST["sets"])}'
    leads = sorted({r['lead'] for r in SS_ST['sets']})
    need = [l for l in leads if l not in SS_ST['opps']]
    if need:
        _ss_fetch(need[:120], lambda l: _ss_get('/opportunity/', {'lead_id': l, '_limit': 50}).get('data', []), SS_ST['opps'])
        return f'opportunities: {len(SS_ST["opps"])} of {len(leads)} leads'
    need = [l for l in leads if l not in SS_ST['names']]
    if need:
        _ss_fetch(need[:120], lambda l: _ss_get(f'/lead/{l}/', {'_fields': 'id,display_name'}).get('display_name'), SS_ST['names'])
        return f'lead names: {len(SS_ST["names"])} of {len(leads)} leads'
    return 'Setter sets ... done'


def _ss_tracker():
    r, e = run_composio_tool('GOOGLESHEETS_VALUES_GET', {'spreadsheet_id': SS_TRACKER_ID, 'range': 'Inputs!A1:Y5000',
                                                          'value_render_option': 'UNFORMATTED_VALUE'})
    if e: raise Exception(str(e)[:300])
    vals = r['data'].get('values') or []
    base, out = dt.date(1899, 12, 30), []
    num = lambda x: float(x) if isinstance(x, (int, float)) else (float(x) if str(x).strip().replace('.', '', 1).isdigit() else 0.0)
    for v in vals[1:]:
        v = list(v) + [''] * (25 - len(v))
        s = SS_TRACKER_NAMES.get(v[0])
        if not s or not isinstance(v[1], (int, float)): continue
        d = base + dt.timedelta(days=int(v[1]))
        if SS_ST['start'] <= d <= SS_ST['end']:
            out.append({'setter': s, 'day': d, 'in_sets': num(v[4]), 'ob_sets': num(v[7])})
    return out


def _ss_find_sets():
    """One row per (setter, lead): the setter's form, a closer meeting after a setter touch, or both."""
    start, end = SS_ST['start'], SS_ST['end']
    got = collections.defaultdict(list)
    for (kind, *_), rows in SS_ST['done'].items(): got[kind] += rows
    ca, meets, calls = got['ca'], got['meet'], got['call']
    SS_ST['disc'] = collections.defaultdict(list)
    for x in ca:
        if x.get('custom_activity_type_id') == SS_DISC and x.get('status') == 'published' and x.get(SS_DISC_OUT):
            SS_ST['disc'][x['lead_id']].append((_ss_t(x['date_created']), x[SS_DISC_OUT]))
    form = {}
    for x in ca:
        if x.get('custom_activity_type_id') != SS_PRE or x.get('status') != 'published': continue
        if x.get('user_id') not in SS_SETTERS or x.get(SS_PRE_OUT) != SS_SET_OUTCOME: continue
        d = _ss_day(_ss_t(x.get('activity_at') or x['date_created']))
        if start <= d <= end:
            k = (SS_SETTERS[x['user_id']], x['lead_id'])
            if k not in form or d < form[k]['day']: form[k] = {'day': d, 'type': x.get(SS_PRE_TYPE)}
    touches = collections.defaultdict(list)
    for c in calls:
        if c.get('call_method') == 'external' or not (c.get('duration') or 0) > 0 or not c.get('lead_id'): continue
        touches[c['lead_id']].append((_ss_t(c['date_created']), c['user_id']))
    smeet, cmeet = collections.defaultdict(list), collections.defaultdict(list)
    for m in meets:
        if not m.get('lead_id'): continue
        if m.get('user_id') in SS_SETTERS: smeet[m['lead_id']].append(m)
        elif m.get('user_id') in SS_CLOSERS: cmeet[m['lead_id']].append(m)
    SS_ST['cmeet'] = cmeet
    cal = {}
    for l, ms in cmeet.items():
        for m in sorted(ms, key=lambda x: x['date_created']):
            t = _ss_t(m['date_created']); d = _ss_day(t)
            if not start <= d <= end: continue
            tt = [(ct, u, 'call') for ct, u in touches.get(l, []) if t - SS_TOUCH <= ct <= t + dt.timedelta(minutes=5)]
            tt += [(_ss_t(s['starts_at']), s['user_id'], 'intro') for s in smeet.get(l, []) if s.get('starts_at')
                   and t - SS_TOUCH <= _ss_t(s['starts_at']) <= t + dt.timedelta(minutes=15)
                   and not (s.get('title') or '').startswith('Canceled')]
            if not tt: continue
            _, u, _ = max(tt)
            intro = any(k == 'intro' and uu == u for _, uu, k in tt) or any(
                s['user_id'] == u and s.get('starts_at') and _ss_t(s['date_created']) < t
                and t - dt.timedelta(days=3) <= _ss_t(s['starts_at']) <= t + dt.timedelta(minutes=15) for s in smeet.get(l, []))
            k = (SS_SETTERS[u], l)
            if k not in cal:
                cal[k] = {'day': d, 'type': 'Inbound' if intro else 'Outbound', 'closer': m.get('user_name') or m.get('user_id')}
    out = []
    for k in set(form) | set(cal):
        f, c = form.get(k), cal.get(k)
        if f:
            ty = 'Outbound' if f['type'] == 'Outbound' else ('Inbound' if f['type'] else (c['type'] if c else 'Inbound'))
            out.append({'setter': k[0], 'lead': k[1], 'day': f['day'], 'type': ty,
                        'found_by': 'form and calendar' if c else 'form only', 'closer': c['closer'] if c else ''})
        else:
            out.append({'setter': k[0], 'lead': k[1], 'day': c['day'], 'type': c['type'], 'found_by': 'calendar only', 'closer': c['closer']})
    return out


def _ss_bucket(r):
    l = r['lead']; st = dt.datetime.combine(r['day'], dt.time(0), tzinfo=SS_ET)
    sales = [o for o in SS_ST['opps'].get(l) or [] if o.get('pipeline_name') == 'Sales']
    after = [o for o in sales if _ss_t(o['date_created']) >= st - dt.timedelta(days=3)]
    o = max(after or sales, key=lambda o: o['date_created']) if sales else None
    s = o['status_label'] if o else None
    dl = [x for x in SS_ST['disc'].get(l, []) if x[0] >= st]
    last = max(dl)[1] if dl else None
    if s in SS_OPP_BUCKET: return SS_OPP_BUCKET[s], s, last
    if s == 'LOST': return ('Bad: bad fit' if last == 'Bad Fit' else 'Lost, other reason'), s, last
    if last in SS_OUT_BUCKET: return SS_OUT_BUCKET[last], s, last
    now = SS_ST['run_at']
    if any(m.get('starts_at') and _ss_t(m['starts_at']) > now and not (m.get('title') or '').startswith('Canceled')
           for m in SS_ST['cmeet'].get(l, [])):
        return 'Call still ahead', s, last
    if s == 'No Show/Cancel' or last in ('No Show', 'Cancel'): return 'No show or canceled', s, last
    if s == 'Reschedule Request' or last == 'Reschedule Request': return 'Reschedule pending', s, last
    return 'Call passed, closer has not updated', s, last


def _ss_week(d):
    """Monday to Sunday, cut at month ends, so each month adds up on its own."""
    a = max(d - dt.timedelta(days=d.weekday()), d.replace(day=1))
    month_end = (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
    b = min(a + dt.timedelta(days=6 - a.weekday()), month_end, SS_ST['end'])
    return a, b

def _ss_csv(header, rows):
    f = io.StringIO(); w = csv.writer(f, lineterminator='\n'); w.writerow(header); w.writerows(rows); return f.getvalue()


def ss_result():
    start, end = SS_ST['start'], SS_ST['end']
    groups = collections.defaultdict(list)
    for r in SS_ST['sets']:
        r = dict(r); r['name'] = SS_ST['names'].get(r['lead']) or ''
        r['bucket'], r['opp'], r['disc'] = _ss_bucket(r)
        groups[(r['setter'], _ss_name_key(r['name']) or r['lead'])].append(r)
    sets = []
    for (setter, nk), rs in groups.items():   # duplicate lead records with the same name count once
        if (setter, nk) in SS_EXCLUDE: continue
        rs.sort(key=lambda r: (r['day'], r['found_by']))
        first = dict(rs[0]); first['bucket'] = min((r['bucket'] for r in rs), key=SS_BUCKETS.index); first['dups'] = len(rs)
        sets.append(first)
    sets.sort(key=lambda r: (SS_ORDER.index(r['setter']), r['day'], r['name']))
    months = sorted({(start + dt.timedelta(days=i)).strftime('%Y-%m') for i in range((end - start).days + 1)})
    weeks, d = [], start
    while d <= end:
        a, b = _ss_week(d); weeks.append((a, b)); d = b + dt.timedelta(days=1)
    wlabel = lambda a, b: f'{a:%b} {a.day}-{b.day}'
    mon, wk = collections.defaultdict(lambda: [0, 0, 0, 0]), collections.defaultdict(lambda: [0, 0, 0, 0])
    for r in sets:
        i = 0 if r['type'] == 'Inbound' else 1
        mon[(r['setter'], r['day'].strftime('%Y-%m'))][i] += 1; wk[(r['setter'], _ss_week(r['day']))][i] += 1
    for t in SS_ST['tracker']:
        for key, agg in (((t['setter'], t['day'].strftime('%Y-%m')), mon), ((t['setter'], _ss_week(t['day'])), wk)):
            agg[key][2] += t['in_sets']; agg[key][3] += t['ob_sets']
    n = lambda v: [int(x) for x in v]
    monthly = _ss_csv(['setter', 'month', 'close_inbound', 'close_outbound', 'tracker_inbound', 'tracker_outbound'],
                      [[s, m] + n(mon[(s, m)]) for s in SS_ORDER for m in months])
    weekly = _ss_csv(['setter', 'month', 'week', 'close_inbound', 'close_outbound', 'tracker_inbound', 'tracker_outbound'],
                     [[s, f'{a:%Y-%m}', wlabel(a, b)] + n(wk[(s, (a, b))]) for s in SS_ORDER for a, b in weeks])
    bk = collections.Counter((r['setter'], r['day'].strftime('%Y-%m'), r['type'], r['bucket']) for r in sets)
    buckets = _ss_csv(['setter', 'month', 'set_type', 'bucket', 'sets'],
                      [list(k) + [v] for k, v in sorted(bk.items(), key=lambda x: (SS_ORDER.index(x[0][0]), x[0][1], x[0][2], SS_BUCKETS.index(x[0][3])))])
    leads = _ss_csv(['setter', 'set_date', 'set_type', 'found_by', 'closer_bucket', 'pipeline_status', 'discovery_outcome',
                     'lead_name', 'closer', 'duplicate_records', 'lead_id'],
                    [[r['setter'], r['day'].isoformat(), r['type'], r['found_by'], r['bucket'], r['opp'] or '', r['disc'] or '',
                      r['name'], r['closer'], r['dups'], r['lead']] for r in sets])
    return {'monthly': monthly, 'weekly': weekly, 'buckets': buckets, 'leads': leads}

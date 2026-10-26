# Setter follow-up tracker (Sheila, Oct 25-26, 2026): every lead on each setter's list, grouped by the next step
# their SOP asks for, written once a day to the Google Sheet "Setter Follow-up Tracker" (one tab per setter).
#   Welcome Series leads: docs/SOP-Setter-Welcome-Series-Outbound.md, sections 3 to 4C (three tries over two days).
#   Bali's Abandoned Typeform leads: "Setter Abandoned Typeform Outbound SOP" (docs/ABANDONED-TYPEFORM.md):
#   Day 1, 3, 5, 7 (business days), then one call a month.
# Runs in the Composio workbench, which other sessions share: every global here is prefixed TRK_ / _trk_ so another
# script can't overwrite it, and it keeps its own copy of the Close pager (wb_runner.py swaps get_all for a cache).
# Exec right AFTER bali_metrics.py (it uses classify, no_vm_option, load_outcomes, OUTCOMES, CLOSERS, SEQ, pt, _q, ET).
# Read only on Close. Writes only to the tracker sheet.
# Usage, every cell under ~45 seconds: tracker_start(); then tracker_step() until it returns '... done'.
import collections, datetime as dt, re, json, pickle, os, time
from concurrent.futures import ThreadPoolExecutor
TRK_SETTERS = {'Bali': 'user_c0wPSKtEPsqkIh08OnjiGaj6XHeFBjGSp2jyVxAggDl',
               'Jose': 'user_msFtSHmZcoRAYvHX8aGrnygBzOy4u1GnLrRSFfIdcgk',
               'Jordan': 'user_3IrYZLUcCBZrg2mb49wCybrxGBFTCxa5eqTHhE1ApuC'}
TRK_SEQ = SEQ                     # "Welcome Series - Bali Test": every setter's Welcome Series sign-ups come in here
TRK_ICU_FIELD = 'cf_C6fOIXKxCBrG5PhlmEhcO6Rzu20G8XV6aA7wnADkH3P'   # "Initial Contact User": whose list a lead is on
TRK_AB_FIELD = 'cf_qiVzsFQUYHM2vmDeUg0mbfIrWgvU3ZJmhujqNtWiAhJ'    # "Incomplete Typeform User" (Abandoned Typeform list)
TRK_AB_FOR = ('Bali',)            # only Bali works the Abandoned Typeform list so far
TRK_AB_SEQ = 'seq_0i6NE63SCuSdwb4E7kXQc3'   # "001- Incomplete Typeform Lead Distribution": when a lead entered the bucket
TRK_AB_SCAN_FROM = dt.datetime(2026, 10, 1, tzinfo=ET)
TRK_AB_STEPS = (('Day 3', 2), ('Day 5', 4), ('Day 7', 6))   # business days after Day 1
TRK_AB_MONTHLY = 30
TRK_WINDOW_DAYS = 14              # Welcome Series sign-ups from the last 14 days
TRK_TRY2_GAP = dt.timedelta(minutes=60)   # SOP 4C try 2: "same day, a few hours later"; 60+ min after try 1 counts
TRK_DD_GAP = dt.timedelta(seconds=120)    # double dial: redial within 2 min of the no-answer ending (same as the scorecard)
TRK_CLOSED_OUTCOME = re.compile(r'not a fit|disqualified|do not contact')
TRK_CLOSED_STATUS = re.compile(r'do not contact|disqualif|not a fit|won|lost|bad (lead|number)')
TRK_SHEET_ID = '1R9G94XcDYBViugBPW0OEMBkueU1hHanedyyxaBn_lSU'   # Google Sheet "Setter Follow-up Tracker" (Sheila's Drive)
TRK_STATE_PATH = '/mnt/files/tracker_state.pkl'
TRK_CALL_SLICES = 3               # the call pull is split by date so each step stays well under a minute
TRK_MEET_DAYS, TRK_MEET_SLICES = 30, 6   # meetings booked in the last 30 days (all reps), 5 days per step
TRK_KEEP = {'call': ('id', 'lead_id', 'user_id', 'direction', 'call_method', 'outcome_id', 'note', 'disposition', 'duration', 'date_created'),
            'sms': ('lead_id', 'direction', 'date_created'), 'email': ('lead_id', 'direction', 'subject', 'date_created'),
            'task': ('lead_id', 'text', 'due_date', 'date'), 'sub': ('lead_id', 'date_created'),
            'meeting': ('lead_id', 'user_id', 'user_name', 'title', 'status', 'activity_at', 'date_created')}
TRK_ST = {}

def _trk_slim(rows, kind): return [{k: r.get(k) for k in TRK_KEEP[kind]} for r in rows]   # keeps the saved state small
def _trk_iso(t): return t.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
def _trk_canceled(m):
    return (m.get('title') or '').lower().startswith('canceled') or m.get('status') in ('canceled', 'declined-by-lead', 'declined-by-org')
def _trk_get_all(ep, params, stop=None):
    out = []; skip = 0
    while True:
        p = dict(params); p['_skip'] = skip; p.setdefault('_limit', 100)
        r, e = _q(proxy_execute, 'GET', ep, 'close', query_params=p)
        if e: raise Exception(str(e)[:300])
        body = r.get('data')
        if isinstance(body, dict): items = body.get('data', []); more = body.get('has_more')
        else: items = body or []; more = r.get('has_more') if r.get('has_more') is not None else len(items) == p['_limit']
        out += items; skip += len(items)
        if stop and items and stop(items[-1]): break
        if not more or not items: break
    return out
def _trk_search(queries, fields=('id', 'display_name', 'status_label', 'date_created')):
    """Close data search (read only), every page."""
    body = {'query': {'type': 'and', 'queries': [{'type': 'object_type', 'object_type': 'lead'}] + queries},
            '_fields': {'lead': list(fields)}, '_limit': 200}
    out = []; cur = None
    while True:
        b = dict(body)
        if cur: b['cursor'] = cur
        for i in range(5):   # Close's search allows only a few requests a second: back off on 429
            r, e = _q(proxy_execute, 'POST', '/data/search/', 'close', body=b)
            if not (e and '429' in str(e)): break
            time.sleep(1 + 2 * i)
        if e: raise Exception(str(e)[:300])
        d = r.get('data') if isinstance(r.get('data'), dict) else r
        out += d.get('data') or []; cur = d.get('cursor')
        if not cur: break
    return out
def _trk_field_is(field, uid):
    return {'type': 'field_condition', 'field': {'type': 'custom_field', 'custom_field_id': field},
            'condition': {'type': 'reference', 'reference_type': 'user_or_group', 'object_ids': [uid]}}
def _trk_leads_info(ids):
    """Name and status for each lead id, 100 per search request (an "or" of id queries)."""
    ids = list(ids)
    def chunk(part): return _trk_search([{'type': 'or', 'queries': [{'type': 'id', 'value': i} for i in part]}])
    with ThreadPoolExecutor(2) as ex:
        return {x['id']: x for rows in ex.map(chunk, [ids[i:i + 100] for i in range(0, len(ids), 100)]) for x in rows}

def _trk_save(): pickle.dump(TRK_ST, open(TRK_STATE_PATH, 'wb'))
def tracker_start(now=None):
    TRK_ST.clear(); TRK_ST['now'] = now or dt.datetime.now(ET)
    TRK_ST['todo'] = ['subs', 'absubs'] + [f'meetings:{h}' for h in range(TRK_MEET_SLICES)] + \
        [f'list:{n}' for n in TRK_SETTERS] + [f'calls:{n}:{h}' for n in TRK_SETTERS for h in range(TRK_CALL_SLICES)] + \
        [f'{k}:{n}' for n in TRK_SETTERS for k in ('sms', 'other')] + ['universe', 'leads', 'build'] + \
        [f'sheet:{n}' for n in TRK_SETTERS] + ['sheet:How it works']
    if not OUTCOMES: load_outcomes()
    _trk_save(); return 'started'
def _trk_pull_calls(uid, start, end=None):
    q = {'user_id': uid, 'date_created__gte': _trk_iso(start)}
    if end: q['date_created__lt'] = _trk_iso(end)
    allc = _trk_slim(_trk_get_all('/activity/call/', q), 'call')
    calls = [c for c in allc if c.get('direction') == 'outbound' and c.get('call_method') != 'external' and c.get('lead_id')]
    inbound = [c for c in allc if c.get('direction') == 'inbound' and c.get('call_method') != 'external' and c.get('lead_id')
               and c.get('disposition') in (None, '', 'answered') and (classify(c) == 'talk' or (c.get('duration') or 0) >= 45)]
    for c in calls: c['_t'] = pt(c['date_created']); c['_k'] = classify(c)
    for c in inbound: c['_t'] = pt(c['date_created']); c['_k'] = 'talk'
    return calls, inbound

def tracker_step():
    """Do the next piece (each well under a minute). Returns what it did; the last one ends with 'done'."""
    if not TRK_ST:
        if not os.path.exists(TRK_STATE_PATH): return 'not started: call tracker_start()'
        TRK_ST.update(pickle.load(open(TRK_STATE_PATH, 'rb')))
    if not OUTCOMES: load_outcomes()
    if not TRK_ST['todo']: return 'done'
    job = TRK_ST['todo'][0]; now = TRK_ST['now']; start = now - dt.timedelta(days=TRK_WINDOW_DAYS + 1)
    per = TRK_ST.setdefault('per', {}); n = job.split(':')[1] if ':' in job else None
    if job == 'subs':
        TRK_ST['subs'] = _trk_slim(_trk_get_all('/sequence_subscription/', {'sequence_id': TRK_SEQ},
                                                stop=lambda x: pt(x['date_created']) < start), 'sub')
    elif job == 'absubs':
        TRK_ST['absubs'] = _trk_slim(_trk_get_all('/sequence_subscription/', {'sequence_id': TRK_AB_SEQ},
                                                  stop=lambda x: pt(x['date_created']) < TRK_AB_SCAN_FROM), 'sub')
    elif job.startswith('meetings:'):
        h = int(n); span = dt.timedelta(days=TRK_MEET_DAYS / TRK_MEET_SLICES); a = now - dt.timedelta(days=TRK_MEET_DAYS) + span * h
        q = {'date_created__gte': _trk_iso(a)}
        if h < TRK_MEET_SLICES - 1: q['date_created__lt'] = _trk_iso(a + span)
        ms = _trk_slim(_trk_get_all('/activity/meeting/', q), 'meeting')
        for m in ms: m['_t'] = pt(m['date_created']); m['_at'] = pt(m['activity_at']) if m.get('activity_at') else None
        TRK_ST['meetings'] = (TRK_ST.get('meetings', []) if h else []) + ms
    elif job.startswith('list:'):
        p = per.setdefault(n, {})
        p['list'] = {x['id'] for x in _trk_search([_trk_field_is(TRK_ICU_FIELD, TRK_SETTERS[n])], fields=('id',))}
        p['ab'] = _trk_search([_trk_field_is(TRK_AB_FIELD, TRK_SETTERS[n])]) if n in TRK_AB_FOR else []
    elif job.startswith('calls:'):
        h = int(job.split(':')[2]); p = per.setdefault(n, {}); span = (now - start) / TRK_CALL_SLICES
        c, i = _trk_pull_calls(TRK_SETTERS[n], start + span * h, None if h == TRK_CALL_SLICES - 1 else start + span * (h + 1))
        p['calls'] = (p.get('calls', []) if h else []) + c; p['inbound'] = (p.get('inbound', []) if h else []) + i
    elif job.startswith('sms:'):
        q = {'user_id': TRK_SETTERS[n], 'date_created__gte': _trk_iso(start)}
        sms = [s for s in _trk_slim(_trk_get_all('/activity/sms/', q), 'sms') if s.get('direction') == 'outbound' and s.get('lead_id')]
        for x in sms: x['_t'] = pt(x['date_created'])
        per.setdefault(n, {})['sms'] = sms
    elif job.startswith('other:'):
        q = {'user_id': TRK_SETTERS[n], 'date_created__gte': _trk_iso(start)}
        em = [m for m in _trk_slim(_trk_get_all('/activity/email/', q), 'email') if m.get('direction') == 'outgoing' and m.get('lead_id')]
        for x in em: x['_t'] = pt(x['date_created'])
        per.setdefault(n, {}).update(email=em, tasks=_trk_slim(_trk_get_all('/task/', {'assigned_to': TRK_SETTERS[n], 'is_complete': 'false', '_type': 'lead'}), 'task'))
    elif job == 'universe':
        TRK_ST['universe'] = _trk_universe(TRK_ST, now)
        TRK_ST['info'] = {x['id']: x for p in per.values() for x in p.get('ab', [])}
    elif job == 'leads':
        need = sorted({l for mine in TRK_ST['universe'].values() for l in mine if l not in TRK_ST['info']})
        TRK_ST['info'].update(_trk_leads_info(need))
    elif job == 'build':
        TRK_ST['result'] = _trk_build(TRK_ST, now)
    elif job.startswith('sheet:'):
        _trk_write_tab(n, TRK_ST['result'])
    TRK_ST['todo'].pop(0); _trk_save()
    return f'{job} ok' + ('' if TRK_ST['todo'] else '; done')
def tracker_result(): return TRK_ST.get('result')

def _trk_when(t): return t.astimezone(ET).strftime('%-I:%M%p').replace('AM', 'am').replace('PM', 'pm')
def _trk_day(d, today):
    if d == today: return 'today'
    if d == today + dt.timedelta(days=1): return 'tomorrow'
    if d == today - dt.timedelta(days=1): return 'yesterday'
    return d.strftime('%a %b ') + str(d.day)
def _trk_bday_add(d, k):
    while k > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5: k -= 1
    return d
def _trk_next_bday(d):
    while d.weekday() >= 5: d += dt.timedelta(days=1)
    return d
def _trk_try1(cl, sms, d1):
    """SOP try 1 / Day 1 parts that are missing on day d1: double dial, voicemail, text."""
    day = [c for c in cl if c['_t'].astimezone(ET).date() == d1]
    first = day[0]; end = first['_t'] + dt.timedelta(seconds=first.get('duration') or 0)
    dd = any(c is not first and first['_t'] <= c['_t'] <= end + TRK_DD_GAP for c in day)
    vm = any(c['_k'] == 'vm' for c in day) or all(no_vm_option(c) for c in day)
    txt = any(s['_t'].astimezone(ET).date() == d1 for s in sms)
    return [k for k, ok in (('double dial', dd), ('voicemail', vm), ('text', txt)) if not ok]

def _trk_ws_no_pickup(cl, sms, today):
    """Welcome Series SOP 4C: try 1 right away (double dial, voicemail, text), try 2 the same day a few hours later
    (dial only), try 3 the next day. After try 3 the Value Series takes over."""
    d1 = cl[0]['_t'].astimezone(ET).date()
    day1 = [c for c in cl if c['_t'].astimezone(ET).date() == d1]
    try2 = any(c['_t'] - day1[0]['_t'] >= TRK_TRY2_GAP for c in day1)
    later = [c for c in cl if c['_t'].astimezone(ET).date() > d1]
    if later:
        return 'done', f'3 tries done (last {_trk_day(later[-1]["_t"].astimezone(ET).date(), today)}). The Value Series takes it from here.', None
    if d1 == today:
        miss = _trk_try1(cl, sms, d1)
        fix = (' Finish try 1: ' + ', '.join(miss) + '.') if miss else ''
        if try2: return 'later', 'Try 3 tomorrow: dial, mention yesterday\'s email. Voicemail OK.' + fix, today + dt.timedelta(days=1)
        return 'today', 'Try 2 later today, a few hours after try 1: dial only, no second voicemail or text.' + fix, today
    if d1 == today - dt.timedelta(days=1):
        return 'today', 'Try 3 today: dial, mention yesterday\'s email. Voicemail OK.', today
    return 'overdue', f'Try 3 missed (was due {_trk_day(d1 + dt.timedelta(days=1), today)}). Dial once more; voicemail OK.', d1 + dt.timedelta(days=1)

def _trk_ab_no_pickup(cl, sms, today):
    """Abandoned Typeform SOP: Day 1, then Day 3, 5, 7 (business days after Day 1), each a call and, if no answer,
    double dial, voicemail, text. Then one call a month."""
    days = sorted({c['_t'].astimezone(ET).date() for c in cl}); d1 = days[0]; last = days[-1]
    sched = [(lbl, _trk_bday_add(d1, k)) for lbl, k in TRK_AB_STEPS]
    m = sched[-1][1]
    for i in range(1, 13):
        m = _trk_next_bday(m + dt.timedelta(days=TRK_AB_MONTHLY)); sched.append((f'Monthly call {i}', m))
    lbl, due = next((x for x in sched if x[1] > last), sched[-1])
    if last == today:
        miss = _trk_try1(cl, sms, today)
        if miss: return 'today', 'Finish today\'s no-answer steps: ' + ', '.join(miss) + f'. Next: {lbl} call {_trk_day(due, today)}.', today
    what = 'one call' if lbl.startswith('Monthly') else 'call; if no answer, double dial, voicemail, text'
    if due == today: return 'today', f'{lbl} today: {what}.', today
    if due < today: return 'overdue', f'{lbl} missed (was due {_trk_day(due, today)}): {what}.', due
    return 'later', f'{lbl} on {_trk_day(due, today)}: {what}.', due

def _trk_lead_row(name, lid, src, signup, info, d, mt, now, today):
    uid = TRK_SETTERS[name]
    cl = sorted([c for c in d['calls'] if c['lead_id'] == lid], key=lambda c: c['_t'])
    inb = [c for c in d['inbound'] if c['lead_id'] == lid]
    sms = [s for s in d['sms'] if s['lead_id'] == lid]
    em = [m for m in d['email'] if m['lead_id'] == lid]
    talks = sorted([c for c in cl if c['_k'] == 'talk'] + inb, key=lambda c: c['_t'])
    status = info.get('status_label') or ''
    last_out = OUTCOMES.get((talks[-1] if talks else (cl[-1] if cl else {})).get('outcome_id') or '', '')
    row = dict(lead=info.get('display_name') or lid, lead_id=lid, source=src, signup=signup.isoformat() if signup else None,
               calls=len(cl), last_call=cl[-1]['_t'].isoformat() if cl else None, last_outcome=last_out)
    def out(bucket, step, due=None, sort=None):
        row.update(bucket=bucket, step=step, due=due.isoformat() if due else None,
                   sort=(sort or (cl[-1]['_t'] if cl else signup or now)).isoformat())
        return row
    lm = [m for m in mt.get(lid, []) if not _trk_canceled(m) and m['_at']]
    ahead = sorted([m for m in lm if m['_at'] >= dt.datetime(today.year, today.month, today.day, tzinfo=ET)], key=lambda m: m['_at'])
    if TRK_CLOSED_STATUS.search(status.lower()) or (talks and TRK_CLOSED_OUTCOME.search(last_out)):
        why = status if TRK_CLOSED_STATUS.search(status.lower()) else last_out.capitalize()
        return out('done', f'Closed out ({why}). No next step.')
    if ahead:
        m = ahead[0]; md = m['_at'].astimezone(ET).date(); who = m.get('user_name') or 'someone'; at = _trk_when(m['_at'])
        if m.get('user_id') == uid:
            return out('today' if md == today else 'later', f'Your own call with them {_trk_day(md, today)} at {at} ET.', md, m['_at'])
        if m.get('user_id') in CLOSERS:
            bd = m['_t'].astimezone(ET).date()
            if bd == today:
                sent = any(x['_t'] >= m['_t'] - dt.timedelta(minutes=10) and 'discovery call' in (x.get('subject') or '').lower() for x in em)
                return out('today', ('Handoff email sent. ' if sent else 'Send the Setter to Closer Handoff email now. ') +
                           f'Setter notes in Close by end of day. Call with {who} {_trk_day(md, today)} at {at} ET.', today, m['_t'])
            if md == today + dt.timedelta(days=1):
                return out('today', f'Day-before reminder today: their call with {who} is tomorrow at {at} ET.', today, m['_at'])
            if md == today:
                return out('today', f'Morning-of reminder if they haven\'t replied: call with {who} today at {at} ET.', today, m['_at'])
            rd = md - dt.timedelta(days=1)
            return out('later', f'Set to {who} for {_trk_day(md, today)} at {at} ET. Day-before reminder {_trk_day(rd, today)}.', rd, m['_at'])
        return out('later', f'Booked with {who} {_trk_day(md, today)} at {at} ET.', md, m['_at'])
    if talks and any(m['_at'] < now for m in lm):
        return out('done', f'Their call was held {_trk_day(max(m["_at"] for m in lm if m["_at"] < now).astimezone(ET).date(), today)}. The closer has it from here.')
    if talks:
        tk = sorted([t for t in d['tasks'] if t.get('lead_id') == lid and 'welcome series' not in (t.get('text') or '').lower()
                     and (t.get('due_date') or t.get('date'))], key=lambda t: t.get('due_date') or t.get('date'))
        if tk:
            t = tk[0]; td = pt(t.get('due_date') or t.get('date')).astimezone(UTC).date()
            note = (t.get('text') or 'Call back').strip()[:90]
            if td < today: return out('overdue', f'Callback missed (was due {_trk_day(td, today)}): {note}', td)
            return out('today' if td == today else 'later', f'Callback {_trk_day(td, today)}: {note}', td)
        return out('attention', f'Talked {_trk_day(talks[-1]["_t"].astimezone(ET).date(), today)}'
                   + (f' ({last_out})' if last_out else '') + ', but no callback task or booking in Close. Set the next step.')
    if not cl:
        sd = signup.astimezone(ET).date() if signup else today
        if sd >= today - dt.timedelta(days=1):
            return out('now', f'Not called yet. Signed up {_trk_day(sd, today)} at {_trk_when(signup)} ET.' if signup else 'Not called yet.', None, signup or now)
        return out('overdue', f'Never called. Signed up {_trk_day(sd, today)}.', None, signup)
    bucket, step, due = (_trk_ab_no_pickup if src == 'Abandoned Typeform' else _trk_ws_no_pickup)(cl, sms, today)
    return out(bucket, step, due)

def _trk_universe(st, now):
    """Each setter's leads: Welcome Series sign-ups on their list (Initial Contact User) from the window, and for Bali
    the Abandoned Typeform list (Incomplete Typeform User). Returns {setter: {lead_id: (list name, signed up)}}."""
    cut = now - dt.timedelta(days=TRK_WINDOW_DAYS)
    enr = {}
    for s in st['subs']:
        t = pt(s['date_created'])
        if s['lead_id'] not in enr or t < enr[s['lead_id']]: enr[s['lead_id']] = t
    ab_in = {}
    for s in st.get('absubs', []):
        t = pt(s['date_created'])
        if s['lead_id'] not in ab_in or t < ab_in[s['lead_id']]: ab_in[s['lead_id']] = t
    out = {}
    for name in TRK_SETTERS:
        p = st['per'][name]
        mine = {l: ('Welcome Series', t) for l, t in enr.items() if l in p['list'] and t >= cut}
        for x in p.get('ab', []):
            mine[x['id']] = ('Abandoned Typeform', ab_in.get(x['id']) or (pt(x['date_created']) if x.get('date_created') else None))
        out[name] = mine
    return out

def _trk_build(st, now):
    today = now.astimezone(ET).date()
    mt = collections.defaultdict(list)
    for m in st['meetings']:
        if m.get('lead_id'): mt[m['lead_id']].append(m)
    out = dict(generated=now.isoformat(), today=today.isoformat(), window_days=TRK_WINDOW_DAYS, setters={})
    for name, mine in st['universe'].items():
        out['setters'][name] = [_trk_lead_row(name, l, src, su, st['info'].get(l) or {}, st['per'][name], mt, now, today)
                                for l, (src, su) in mine.items()]
    return out

# ---- Google Sheet ----
TRK_SECTIONS = [
    ('now', 'NEW: not called yet', 'Signed up yesterday or today. Call these first, newest first.', '#fde2d2'),
    ('today', 'DUE TODAY', 'Follow-up calls, callbacks and handoff steps due today.', '#d6e4ff'),
    ('attention', 'TALKED, NO NEXT STEP IN CLOSE', 'Book them, set a callback task, or log the outcome.', '#fff1c2'),
    ('overdue', 'OVERDUE', 'Missed follow-ups and older sign-ups never called. Work these after today\'s list, newest first.', '#f9d4d4'),
    ('later', 'COMING UP', 'Already scheduled for a later day.', '#e6e8eb'),
    ('done', 'NOTHING LEFT TO DO', 'Closed out, call held, or every SOP try done.', '#dcf2e1'),
]
TRK_COLS = ['Lead', 'Next step', 'Due', 'List', 'Signed up', 'Calls', 'Last call', 'Last outcome']
TRK_NCOLS = len(TRK_COLS)

def _trk_fmt_t(iso):
    if not iso: return ''
    t = dt.datetime.fromisoformat(iso).astimezone(ET)
    return t.strftime('%b ') + str(t.day) + ' ' + _trk_when(t)
def _trk_fmt_d(iso):
    if not iso: return ''
    d = dt.date.fromisoformat(iso[:10]); return d.strftime('%a %b ') + str(d.day)
def _trk_sheet_call(path, body):
    r, e = _q(proxy_execute, 'POST', f'https://sheets.googleapis.com/v4/spreadsheets/{TRK_SHEET_ID}{path}', 'googlesheets', body=body)
    if e: raise Exception(f'Sheets {path}: {str(e)[:300]}')
    return r
def _trk_tab_rows(name, res):
    rows = res['setters'][name]; gen = dt.datetime.fromisoformat(res['generated']).astimezone(ET)
    by = {b: [r for r in rows if r['bucket'] == b] for b, *_ in TRK_SECTIONS}
    out = [[f'{name}: Welcome Series' + (' and Abandoned Typeform' if name in TRK_AB_FOR else '') + ' follow-ups',
            '', '', '', '', '', '', f'Updated {gen.strftime("%a %b ")}{gen.day}, {_trk_when(gen)} ET'],
           [' · '.join(f'{len(by[b])} {lbl.split(":")[0].lower()}' for b, lbl, *_ in TRK_SECTIONS)] + [''] * (TRK_NCOLS - 1), [''] * TRK_NCOLS]
    marks = {'title': [0], 'section': [], 'cols': []}
    for b, lbl, sub, color in TRK_SECTIONS:
        items = by[b]
        key = (lambda r: (r.get('due') or '9', r['sort'])) if b in ('today', 'later') else (lambda r: r['sort'])
        items = sorted(items, key=key, reverse=b not in ('today', 'later'))
        marks['section'].append((len(out), color)); out.append([f'{lbl} ({len(items)})', sub] + [''] * (TRK_NCOLS - 2))
        if items:
            marks['cols'].append(len(out)); out.append(list(TRK_COLS))
        for r in items:
            nm = (r['lead'] or '').replace('"', "'")
            out.append([f'=HYPERLINK("https://app.close.com/lead/{r["lead_id"]}/","{nm}")', r['step'], _trk_fmt_d(r.get('due')),
                        r['source'], _trk_fmt_t(r.get('signup')), r['calls'], _trk_fmt_t(r.get('last_call')), r.get('last_outcome') or ''])
        if not items: out.append(['Nothing here right now.'] + [''] * (TRK_NCOLS - 1))
        out.append([''] * TRK_NCOLS)
    return out, marks
def _trk_sheet_ids():
    r, e = _q(proxy_execute, 'GET', f'https://sheets.googleapis.com/v4/spreadsheets/{TRK_SHEET_ID}', 'googlesheets',
              query_params={'fields': 'sheets.properties(sheetId,title,gridProperties)'})
    if e: raise Exception(str(e)[:300])
    d = r.get('data', r) if isinstance(r, dict) else r
    return {s['properties']['title']: s['properties'] for s in d.get('sheets', [])}
def _trk_rgb(h): return {'red': int(h[1:3], 16) / 255, 'green': int(h[3:5], 16) / 255, 'blue': int(h[5:7], 16) / 255}
def _trk_write_tab(name, res):
    """Rewrite one tab from scratch: values, then formatting (section bands, bold headers, frozen title)."""
    tabs = _trk_sheet_ids()
    if name not in tabs:
        _trk_sheet_call(':batchUpdate', {'requests': [{'addSheet': {'properties': {'title': name}}}]}); tabs = _trk_sheet_ids()
    sid = tabs[name]['sheetId']
    if name == 'How it works':
        rows = [[x] for x in TRK_HOW]; marks = {'title': [0], 'section': [], 'cols': []}
    else:
        rows, marks = _trk_tab_rows(name, res)
    need = len(rows) + 50
    reqs = [{'updateSheetProperties': {'properties': {'sheetId': sid, 'gridProperties': {'rowCount': max(need, 200), 'columnCount': TRK_NCOLS, 'frozenRowCount': 2}},
                                       'fields': 'gridProperties(rowCount,columnCount,frozenRowCount)'}},
            {'updateCells': {'range': {'sheetId': sid}, 'fields': 'userEnteredValue,userEnteredFormat'}}]
    _trk_sheet_call(':batchUpdate', {'requests': reqs})
    r, e = _q(proxy_execute, 'PUT', f"https://sheets.googleapis.com/v4/spreadsheets/{TRK_SHEET_ID}/values/'{name}'!A1:H{len(rows)}",
              'googlesheets', query_params={'valueInputOption': 'USER_ENTERED'}, body={'values': rows})
    if e: raise Exception(f'Sheets values {name}: {str(e)[:300]}')
    def band(row, color=None, bold=True, size=None):
        f = {'textFormat': {'bold': bold, **({'fontSize': size} if size else {})}}
        if color: f['backgroundColor'] = _trk_rgb(color)
        return {'repeatCell': {'range': {'sheetId': sid, 'startRowIndex': row, 'endRowIndex': row + 1, 'startColumnIndex': 0, 'endColumnIndex': TRK_NCOLS},
                               'cell': {'userEnteredFormat': f}, 'fields': 'userEnteredFormat(textFormat,backgroundColor)'}}
    reqs = [band(r, size=14) for r in marks['title']] + [band(r, c) for r, c in marks['section']] + [band(r, '#f3f4f6') for r in marks['cols']]
    widths = [200, 520, 100, 140, 120, 60, 120, 200] if name != 'How it works' else [900]
    reqs += [{'updateDimensionProperties': {'range': {'sheetId': sid, 'dimension': 'COLUMNS', 'startIndex': i, 'endIndex': i + 1},
                                            'properties': {'pixelSize': w}, 'fields': 'pixelSize'}} for i, w in enumerate(widths)]
    reqs.append({'repeatCell': {'range': {'sheetId': sid, 'startColumnIndex': 1, 'endColumnIndex': 2},
                                'cell': {'userEnteredFormat': {'wrapStrategy': 'WRAP', 'verticalAlignment': 'TOP'}}, 'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment)'}})
    _trk_sheet_call(':batchUpdate', {'requests': reqs})

TRK_HOW = [
    'How this tracker works',
    '',
    'One tab per setter. Rebuilt from Close every morning; nothing here needs typing in. To change a lead\'s next step, update the lead in Close (log the call, book the meeting, or set a callback task) and the next refresh picks it up.',
    'Click a lead name to open it in Close.',
    '',
    'Which leads: Welcome Series sign-ups from the last 14 days on your list (Close field "Initial Contact User" = you). Bali also gets his Abandoned Typeform list (Close field "Incomplete Typeform User" = Bali); for those, "Signed up" is when they entered the abandoned bucket.',
    '',
    'Welcome Series, no answer (SOP 4C): try 1 right away (double dial, voicemail, text); try 2 the same day a few hours later (dial only); try 3 the next day (voicemail OK). After try 3 the Value Series takes over.',
    'Abandoned Typeform, no answer: Day 1 double dial, voicemail, text; Day 3, 5 and 7 (business days after Day 1) a call and, if no answer, double dial, voicemail, text; then one call a month.',
    'Picked up: a booking or a callback task in Close sets the next step. Talked with neither shows under "Talked, no next step in Close".',
    'Set to a closer (SOP 4A): handoff email and setter notes on the booking day, a reminder the day before the call, a morning-of reminder if they haven\'t replied.',
    'Closed out: Do Not Contact, Disqualified or not a fit, Won or Lost.',
]

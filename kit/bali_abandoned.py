
# Abandoned Typeform card for Bali's daily scorecard (Sheila, Oct 21, 2026). A third image, separate from the
# Welcome Series cards; see docs/ABANDONED-TYPEFORM.md for the rules.
# Runs in the Composio workbench AFTER bali_metrics.py, bali_cover.py and bali_show.py (uses their helpers).
# Entry point: run_abandoned(D) returns the metrics dict that kit/abandoned_build.py renders.
#
# Bali's list: leads enrolled in the "001- Incomplete Typeform Lead Distribution" workflow (the #partial-submit
# bucket) whose "Incomplete Typeform User" field is Bali. Enrollment time = when the lead landed in the bucket.
# Every number on the card counts only these leads. Same call rules as Welcome Series (classify, is_real_call,
# no_vm_option, bad_number, double_dial, _bookings, run_show).
from concurrent.futures import ThreadPoolExecutor
AB_SEQ = 'seq_0i6NE63SCuSdwb4E7kXQc3'                              # 001- Incomplete Typeform Lead Distribution
AB_FIELD = 'custom.cf_qiVzsFQUYHM2vmDeUg0mbfIrWgvU3ZJmhujqNtWiAhJ'  # "Incomplete Typeform User"
AB_START = dt.date(2026, 10, 21)    # test start
AB_SCAN_FROM = dt.date(2026, 10, 1)  # enrollments checked for Bali's field (older bucket leads he may be given)
AB_TARGETS = dict(speed=60, vm=85, text=85, dd=85, pickup=25, connect=10, show=90, followup=90)  # Sheila, Oct 21
FU_STEPS = (('Day 3', 2), ('Day 5', 4), ('Day 7', 6))   # business days after Day 1 (Sheila, Oct 21: business days)
MONTHLY_DAYS = 30                   # then one call a month after Day 7
_AB = {}

def bday_add(d, n):
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5: n -= 1
    return d

def next_bday(d):
    while d.weekday() >= 5: d += dt.timedelta(days=1)
    return d

def bdays_between(a, b):
    """Business days from a to b (a < b): 1 for the next business day."""
    n = 0; d = a
    while d < b:
        d += dt.timedelta(days=1)
        if d.weekday() < 5: n += 1
    return n

def ab_leads(D):
    """{lead_id: (enrolled_at, name)} for Bali's Abandoned Typeform leads enrolled up to the end of D."""
    if D in _AB: return _AB[D]
    lo = day_bounds(AB_SCAN_FROM)[0]; hi = day_bounds(D)[1]
    subs = get_all('/sequence_subscription/', {'sequence_id': AB_SEQ}, stop=lambda x: pt(x['date_created']) < lo)
    enr = {}
    for s in subs:
        t = pt(s['date_created'])
        if lo <= t < hi and (s['lead_id'] not in enr or t < enr[s['lead_id']]): enr[s['lead_id']] = t
    def one(l):
        r, e = _q(proxy_execute, 'GET', f'/lead/{l}/', 'close', query_params={'_fields': f'id,display_name,{AB_FIELD}'})
        if e: raise Exception(str(e)[:300])
        return l, dict(r)
    with ThreadPoolExecutor(8) as ex: got = list(ex.map(one, list(enr)))
    out = {l: (enr[l], x.get('display_name') or l) for l, x in got if x.get(AB_FIELD) == BALI}
    _AB[D] = out
    return out

def _result(cs, sms_today, booked):
    """What happened on a follow-up lead's calls that day, in a few words."""
    if not cs: return 'Not called'
    if any(c['_k'] == 'talk' for c in cs):
        on = [OUTCOMES.get(c.get('outcome_id') or '', '') for c in cs if c['_k'] == 'talk']
        on = [o for o in on if o]
        if booked: return 'Picked up, set to a closer' if booked == 'closer' else 'Picked up, booked on your calendar'
        if on: return 'Picked up, ' + on[-1].replace('conversation: ', '')
        return 'Picked up'
    if any(c['_k'] == 'screen' for c in cs) and not any(c['_k'] == 'vm' for c in cs): head = 'Screener'
    else: head = 'No answer'
    done = []
    if double_dial(cs)[1]: done.append('double dial')
    if any(c['_k'] == 'vm' for c in cs): done.append('voicemail')
    if sms_today: done.append('text')
    return head + (': ' + ', '.join(done) if done else ', no voicemail or text')

def run_abandoned(D):
    """Metrics for the Abandoned Typeform card for dialing day D."""
    AB = ab_leads(D); ids = set(AB)
    data = load(D, back=max(16, (D - AB_START).days + 1))
    data = dict(calls=[c for c in data['calls'] if c['lead_id'] in ids],
                inbound=[c for c in data['inbound'] if c['lead_id'] in ids],
                sms=[s for s in data['sms'] if s.get('lead_id') in ids],
                meetings=[x for x in data['meetings'] if x.get('lead_id') in ids],
                dnc=data['dnc'], enr={l: AB[l][0] for l in AB})
    a, b = day_bounds(D); byl = _byl(data['calls']); dnc = data['dnc']
    nm = lambda l: AB[l][1] if l in AB else l
    dc = [c for c in data['calls'] if a <= c['_t'] < b]
    m = dict(date=D.isoformat(), list_size=len(AB), dials=len(dc), people_dialed=len({c['lead_id'] for c in dc}),
             new_leads=sum(1 for l in AB if a <= AB[l][0] < b), targets=AB_TARGETS)
    if dc:
        m['first_call'] = min(c['_t'] for c in dc).astimezone(ET).strftime('%-I:%M%p').lower()
        m['last_call'] = max(c['_t'] for c in dc).astimezone(ET).strftime('%-I:%M%p').lower()
    # 1. first call: speed to lead from the bucket entry (9am to 9pm ET), then the no-answer touches that day
    sp = speed_work(D, data); w = [x['w'] for x in sp if x['w'] is not None]
    m['new_in_hours'] = len(sp); m['within15'] = sum(1 for x in w if x <= 15)
    closer, selfs, _ = _bookings(D, data, byl); booked = closer | selfs
    pick = {c['lead_id'] for c in dc if c['_k'] == 'talk'}
    m['pickups'] = len(pick)
    m['real_conversations'] = len({c['lead_id'] for c in dc if is_real_call(c, booked)})
    smsl = collections.defaultdict(list)
    for s in data['sms']: smsl[s['lead_id']].append(s['_t'])
    na = sorted({c['lead_id'] for c in dc} - pick)
    m['dnc_left_out'] = sum(1 for l in na if l in dnc and dnc[l] < b)
    na = [l for l in na if not (l in dnc and dnc[l] < b)]
    vm = vp = tx = tp = 0
    for l in na:
        cs = [c for c in byl[l] if a <= c['_t'] < b]
        vm += any(c['_k'] == 'vm' for c in cs); vp += any(not no_vm_option(c) for c in cs)
        bad = any(bad_number(c) for c in cs); tp += not bad
        tx += (not bad) and any(a <= t < b for t in smsl.get(l, []))
    m.update(no_answers=len(na), vm_left=vm, vm_possible=vp, text_sent=tx, text_possible=tp)
    m['dd_noans'], m['dd_done'] = double_dial([c for c in dc if c['lead_id'] in set(na)])
    # 2. closers: sets since the test started, show rate and handoff steps (bali_show.py, limited to this list)
    day1 = {}
    for c in sorted(data['calls'], key=lambda c: c['_t']):
        if etd(c['_t']) >= AB_START: day1.setdefault(c['lead_id'], etd(c['_t']))
    sets = []; d = AB_START
    while d <= D:
        da, db = day_bounds(d)
        cl, _, _ = _bookings(d, data, byl)
        for l in cl:
            x = sorted([y for y in data['meetings'] if y.get('lead_id') == l and da <= y['_t'] < db
                        and y.get('user_id') in CLOSERS], key=lambda y: y['_t'])
            sets.append((d, l, nm(l), x[0] if x else None))
        d += dt.timedelta(days=1)
    def step_of(l, d):
        d1 = day1.get(l)
        return 'Day 1' if not d1 or d1 >= d else f'Day {bdays_between(d1, d) + 1}'
    m['closer_calls'] = len(closer)
    m['closer_split'] = dict(day1=[nm(l) for l in closer if step_of(l, D) == 'Day 1'],
                             followup=[[nm(l), step_of(l, D)] for l in closer if step_of(l, D) != 'Day 1'])
    seen = set(); uniq = [s for s in sets if not (s[1] in seen or seen.add(s[1]))]
    m['sets_to_date'] = len(uniq)
    _SETS[D] = sets
    m['show'] = run_show(D, {'dialed': True})['show']
    _SETS.pop(D, None)
    names = {AB[l][1] for l in AB}
    m['closes'] = [r for r in closes_to_date(D) if r['lead'] in names and r['date_won'] >= AB_START.isoformat()]
    # 3. follow-up calls on time: Day 3, 5, 7 (business days after Day 1, his first call) and monthly after that,
    # owed only while the lead hasn't picked up, booked or gone Do Not Contact
    talked = collections.defaultdict(list)
    for c in data['calls'] + data['inbound']:
        if c['_k'] == 'talk': talked[c['lead_id']].append(c['_t'])
    rows = []
    for l, d1 in day1.items():
        if d1 >= D or any(t < a for t in talked.get(l, [])) or (l in dnc and dnc[l] < a): continue
        if any(x['_t'] < a and not _dead(x) for x in data['meetings'] if x.get('lead_id') == l): continue
        due = [lab for lab, n in FU_STEPS if bday_add(d1, n) == D]
        d7 = bday_add(d1, 6); k = 1
        while not due and d7 + dt.timedelta(days=MONTHLY_DAYS * k) <= D:
            if next_bday(d7 + dt.timedelta(days=MONTHLY_DAYS * k)) == D: due = ['Monthly']
            k += 1
        if not due: continue
        cs = [c for c in byl.get(l, []) if a <= c['_t'] < b]
        bk = 'closer' if l in closer else 'self' if l in selfs else None
        rows.append(dict(lead=nm(l), step=due[0], called=bool(cs),
                         result=_result(cs, any(a <= t < b for t in smsl.get(l, [])), bk)))
    order = {'Day 3': 0, 'Day 5': 1, 'Day 7': 2, 'Monthly': 3}
    rows.sort(key=lambda r: (order[r['step']], not r['called'], r['lead']))
    m['followups'] = dict(due=len(rows), done=sum(r['called'] for r in rows), rows=rows)
    m['dialed'] = bool(dc) or bool(rows)
    return m

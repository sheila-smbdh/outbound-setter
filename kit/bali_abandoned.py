
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
# Bali's work hours for this list (Sheila, Oct 22): his 8 busiest dialing hours inside the 7am to 5pm PT he gave her,
# as ET hours [start, end). Speed to lead counts only leads that enter the bucket in these hours, and the card splits
# the day's leads into in hours and outside them. The Welcome Series WORK window in bali_cover.py is not changed.
AB_HOURS = (11, 19)   # 11am to 7pm ET = 8am to 4pm PT (provisional, from his Oct 16 and Oct 21 dialing)
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

def in_hours(t): return AB_HOURS[0] <= t.astimezone(ET).hour < AB_HOURS[1]

def ab_speed(D, data):
    """Minutes to Bali's first call that day for each lead that entered the bucket on D during AB_HOURS (None = not called)."""
    a, b = day_bounds(D); byl = _byl(data['calls']); out = []
    for l, e in data['enr'].items():
        if not (a <= e < b and in_hours(e)): continue
        cs = [c for c in byl.get(l, []) if c['_t'] >= e - dt.timedelta(minutes=1) and c['_t'] < b]
        out.append(max((cs[0]['_t'] - e).total_seconds() / 60, 0) if cs else None)
    return out

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
    if subs: _AB[D] = out   # not memoized on an empty pull (a wb_runner pass that hasn't fetched yet)
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
    sp = ab_speed(D, data); w = [x for x in sp if x is not None]
    m['new_in_hours'] = len(sp); m['within15'] = sum(1 for x in w if x <= 15); m['hours'] = list(AB_HOURS)
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
        rows.append(dict(lead=nm(l), lead_id=l, step=due[0], called=bool(cs),
                         result=_result(cs, any(a <= t < b for t in smsl.get(l, [])), bk)))
    order = {'Day 3': 0, 'Day 5': 1, 'Day 7': 2, 'Monthly': 3}
    rows.sort(key=lambda r: (order[r['step']], not r['called'], r['lead']))
    m['followups'] = dict(due=len(rows), done=sum(r['called'] for r in rows), rows=rows)
    # 4. per-lead card (Sheila, Oct 22): every lead that entered the bucket on D, in four groups, and the closer
    # calls that happened on D (leads set on earlier days)
    m['leads'] = lead_rows(D, AB, data, byl, closer, selfs, smsl, day1)
    rowsD = {r['lead_id']: r for r in m['show']['rows'] if r['date'] == D.isoformat()}
    m['closer_today'] = []
    for d, l, n, x in uniq:
        if l not in rowsD: continue
        st = handoff_marks(l, n, x['_t'] if x else day_bounds(d)[0], D)
        m['closer_today'].append(dict(lead=n, lead_id=l, set=d.isoformat(), closer=user_name(x.get('user_id') if x else None),
                                      status=rowsD[l]['status'], steps=st['marks']))
    m['dialed'] = bool(dc) or bool(rows) or bool(m['leads'])
    return m

# ---- per-lead rows (Sheila, Oct 22, 2026) -------------------------------------------------------------------------
STEP_KEYS = ('email', 'note', 'day_before', 'morning_of')
_USERS = {}

def user_name(uid):
    if not uid: return ''
    if not _USERS:
        for u in get_all('/user/', {}): _USERS[u['id']] = ' '.join(x for x in (u.get('first_name'), u.get('last_name')) if x)
    return _USERS.get(uid, '')

def when(t):
    """ET time like 'Thu 2pm' or 'Thu 2:30pm'."""
    t = t.astimezone(ET); h = t.strftime('%-I:%M%p').lower().replace(':00', '')
    return t.strftime('%a ') + h

def day_name(d): return d.strftime('%a, %b ') + str(d.day)

def handoff_marks(l, nm, set_t, D):
    """The four handoff steps for one closer set, as marks: y = done, n = missed, later = due after D, na = not owed.
    Same rules as lead_steps in bali_show.py; 'later' steps carry the date they are due."""
    r = lead_show(l, set_t, D, dt.datetime.now(UTC))
    got = {s['step']: s for s in lead_steps(l, nm, set_t, r['meetings'], D)}
    live = [x for x in r['meetings'] if not _dead(x)]
    x = sorted(live, key=_start)[-1] if live else None
    marks = {}; due = {}
    for k in ('email', 'note'):
        marks[k] = ('y' if got[k]['done'] else 'n') if k in got else 'na'
    S = etd(_start(x)) if x else None; booked = etd(x['_t']) if x else None
    for k, owed, dd in (('day_before', x is not None and booked < S - dt.timedelta(days=1), S - dt.timedelta(days=1) if S else None),
                        ('morning_of', x is not None and booked < S, S)):
        if k in got: marks[k] = 'y' if got[k]['done'] else 'n'
        elif owed and dd > D: marks[k] = 'later'; due[k] = dd
        else: marks[k] = 'na'
    return dict(marks=marks, due=due, meeting=x)

def _task(l):
    """Bali's earliest open task on the lead, as a date, or None."""
    ts = [t for t in get_all('/task/', {'lead_id': l, 'is_complete': 'false'}) if t.get('assigned_to') == BALI]
    ds = sorted((t.get('date') or t.get('due_date') or '')[:10] for t in ts if (t.get('date') or t.get('due_date')))
    return dt.date.fromisoformat(ds[0]) if ds else None

def lead_rows(D, AB, data, byl, closer, selfs, smsl, day1):
    """One row per lead that entered the bucket on D: name, speed, group, what happened, the no-answer touches or the
    handoff steps, and the next step from the Abandoned Typeform SOP (Day 1, 3, 5, 7, then monthly)."""
    a, b = day_bounds(D); dnc = data['dnc']; booked = closer | selfs; out = []
    inb = _byl(data['inbound'])
    for l, (e, nm) in sorted(AB.items(), key=lambda kv: kv[1][0]):
        if not (a <= e < b): continue
        cs = [c for c in byl.get(l, []) if e - dt.timedelta(minutes=1) <= c['_t'] < b]
        talk = [c for c in cs + [c for c in inb.get(l, []) if e <= c['_t'] < b] if c['_k'] == 'talk']
        sms_d = any(a <= t < b for t in smsl.get(l, []))
        row = dict(lead=nm, lead_id=l, entered=e.astimezone(ET).strftime('%-I:%M%p').lower(), in_hours=in_hours(e),
                   speed=round(max((cs[0]['_t'] - e).total_seconds() / 60, 0)) if cs else None)
        is_dnc = l in dnc and dnc[l] < b
        tk = None
        if any(is_real_call(c, booked) for c in cs) or (talk and l in booked):
            row['group'] = 'real'
            if l in closer:
                x = sorted([y for y in data['meetings'] if y.get('lead_id') == l and a <= y['_t'] < b
                            and y.get('user_id') in CLOSERS], key=lambda y: y['_t'])
                hm = handoff_marks(l, nm, x[0]['_t'] if x else a, D); mt = hm['meeting'] or (x[0] if x else None)
                row['result'] = 'Set to ' + (user_name(mt.get('user_id')) or 'a closer') + (', ' + when(_start(mt)) if mt else '')
                row['steps'] = hm['marks']
                mk = hm['marks']
                if mk['email'] == 'n': nxt = ('Send the handoff email now', True)
                elif mk['note'] == 'n': nxt = ('Write the closer note in Close now', True)
                elif mk['day_before'] == 'later': nxt = ('Reminder the day before: ' + day_name(hm['due']['day_before']), False)
                elif mk['morning_of'] == 'later': nxt = ('Morning-of reminder ' + day_name(hm['due']['morning_of']) + ' if no reply', False)
                else: nxt = (('Closer call ' + when(_start(mt))) if mt else 'Closer call booked', False)
            elif l in selfs:
                x = sorted([y for y in data['meetings'] if y.get('lead_id') == l and y.get('user_id') == BALI and not _dead(y)], key=_start)
                row['result'] = 'Booked on your calendar' + (', ' + when(_start(x[-1])) if x else '')
                nxt = (('Your call ' + when(_start(x[-1]))) if x else 'Your call is booked', False)
            else:
                on = [OUTCOMES.get(c.get('outcome_id') or '', '') for c in talk]; on = [o for o in on if o]
                o = on[-1] if on else ''
                if o.startswith('disqualified'):
                    row['result'] = 'Disqualified'; nxt = ('None, disqualified', False)
                else:
                    row['result'] = o.replace('conversation: ', '').capitalize() if o else 'Real conversation, no outcome logged'
                    tk = _task(l)
                    nxt = (('Call back ' + day_name(tk)) if tk else 'Set a callback task in Close', not tk)
        elif talk:
            row['group'] = 'short'
            c = max(talk, key=lambda c: c.get('duration') or 0); o = OUTCOMES.get(c.get('outcome_id') or '', '')
            row['result'] = (o.replace('conversation: ', '').capitalize() + ', ' if o else 'Picked up, ') + f"{c.get('duration') or 0} sec"
            tk = _task(l)
            nxt = (('Call back ' + day_name(tk)) if tk else 'Set a next step in Close', not tk)
        elif cs:
            row['group'] = 'nopick'
            elig, done = double_dial(cs)
            row['dd'] = 'na' if not elig else ('y' if done >= elig else 'n')
            row['vm'] = 'y' if any(c['_k'] == 'vm' for c in cs) else ('na' if all(no_vm_option(c) for c in cs) else 'n')
            row['tx'] = 'na' if any(bad_number(c) for c in cs) else ('y' if sms_d else 'n')
            d1 = day1.get(l, D)
            gaps = [lab for k, lab in (('dd', None), ('vm', None), ('tx', 'Text now')) if row[k] == 'n' and lab]
            nxt = ('. '.join(gaps + ['Day 3 call: ' + day_name(bday_add(d1, 2))]), bool(gaps))
            row['result'] = 'No answer' if not any(c['_k'] == 'screen' for c in cs) else 'Screener'
        else:
            row['group'] = 'notcalled'; row['result'] = 'Not called'
            nxt = ('Day 1 call now (entered ' + row['entered'] + ')', True)
        if is_dnc: nxt = ('None, Do Not Contact', False)
        row['next'], row['urgent'] = nxt
        out.append(row)
    return out

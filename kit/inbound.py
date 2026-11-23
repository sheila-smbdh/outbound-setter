# Inbound setter scorecards (Sheila, Nov 20, 2026): Jose, Jordan and Dave. See docs/INBOUND-SCORECARD.md.
# Runs after bali_metrics.py, bali_cover.py and bali_show.py in the same namespace (run_inbound.py does that), GET only.
# Entry point: run_inbound(D, key, flags_dir) -> dict for inbound_build.py.
#
# An inbound set (Sheila, Nov 20, 2026): the lead booked the setter's intro call (a meeting on the setter's own calendar),
# joined the Zoom (Close's Zoom integration shows someone besides the setter in the room, _zoom() in bali_cover.py), and
# a closer meeting was booked within 24 hours after that Zoom started (or later, when the setter sent the lead a text or
# email of their own after the Zoom and within 14 days before the booking). Not an inbound set: a lead the setter dialed
# in the 14 days before the intro call was booked, or a lead on the setter's Incomplete Typeform list (both are outbound
# sets), a lead who already had a closer meeting with the same person before the intro call (a reschedule), or a canceled
# closer meeting. One set per lead. The closer note and handoff email are checked as handoff steps: a set missing either
# still counts, and the missing step shows red.
#
# Price and direct-to-closer bookings come from Messi in Slack. The routine reads them and writes flags/<D>.json:
#   {"date": "YYYY-MM-DD",
#    "price":   {"checked": true, "hits": [{"setter": "dave", "lead": "...", "time": "3:15pm", "quote": "..."}]},
#    "booking": {"checked": true, "hits": [{"setter": "jose", "lead": "...", "lead_id": "lead_...", "closer": "...", "time": "..."}]}}
# A booking hit goes in the file of the day Messi posted it; _booking_by_day moves it to the day the set was made.
# checked false (or no file) means the check didn't run for that day: the card shows "not checked", never green.

import os

IN_SETTERS = dict(
    jose=dict(name='Jose', user='user_msFtSHmZcoRAYvHX8aGrnygBzOy4u1GnLrRSFfIdcgk', draw=True, outbound=True),
    jordan=dict(name='Jordan', user='user_3IrYZLUcCBZrg2mb49wCybrxGBFTCxa5eqTHhE1ApuC', draw=True, outbound=True),
    dave=dict(name='Dave', user='user_sByZkVjk2If3ioL4CC26O5JmTWuzzKzDEjr9fzZHJ26', draw=False, outbound=False))
IN_FROM = dt.date(2026, 11, 16)    # inbound handoff steps count from this week (Mon Nov 16, 2026)
IN_LOOK = 21                       # days back for sets whose reminders fall in the week
IN_DIAL_BACK = dt.timedelta(days=14)
IN_WINDOW = dt.timedelta(hours=24)


def _monday(d): return d - dt.timedelta(days=d.weekday())


def _flags(flags_dir, d):
    p = os.path.join(flags_dir, f'{d.isoformat()}.json') if flags_dir else None
    f = json.load(open(p)) if p and os.path.exists(p) else {}
    out = {}
    for k in ('price', 'booking'):
        x = f.get(k) or {}
        out[k] = dict(checked=bool(x.get('checked')), hits=list(x.get('hits') or []))
    return out


def _mine(hits, key):
    nm = IN_SETTERS[key]['name'].lower()
    return [h for h in hits if (h.get('setter') or '').strip().lower() in (key, nm) or
            (h.get('setter') or '').strip().lower().startswith(nm + ' ')]


def _ln(s): return re.sub(r'[^a-z ]', '', (s or '').lower()).strip()


def _match(h, lead_id, name):
    """A Messi hit is about this lead: same Close lead id (booking alerts carry the Close link), or the same name."""
    if h.get('lead_id'): return h['lead_id'] == lead_id
    a, b = _ln(h.get('lead')), _ln(name)
    return bool(a) and (a in b or b in a)


def _booking_by_day(flags_dir, key, first, D, ledger):
    """Messi's direct-booking alerts for this setter, by the day they count on (Sheila, Nov 23, 2026). An alert lands
    in the thread of the day Messi found it, which can be days after the booking (Nov 21's thread held Jose's Nov 19
    bookings), so an alert about one of the setter's sets counts on the day that set was made; any other alert counts
    on its thread's day."""
    out = collections.defaultdict(list); seen = set()
    last = max(D, dt.datetime.now(ET).date())   # alerts found after D (up to the run day) can be about D's sets
    for i in range((last - first).days + 1):
        d = first + dt.timedelta(days=i)
        for h in _mine(_flags(flags_dir, d)['booking']['hits'], key):
            k = (h.get('lead_id') or _ln(h.get('lead')), h.get('time') or '', h.get('closer') or '')
            if k in seen: continue
            seen.add(k)
            s = next((s for s in ledger if _match(h, s['lead_id'], s['name'])), None)
            out[etd(s['set_t']) if s else (_booked_day(h, d) or d)].append(h)
    return out


def _booked_day(h, d):
    """The ET day the flagged closer meeting was booked, from Close, for an alert that isn't one of the setter's sets
    (Sheila, Nov 23, 2026: Drew Davis, Jose, Nov 19: booked on Kevin Manuel's own link, flagged in Nov 21's thread, and
    the meeting was canceled afterwards, so it is no set; the booking still counts on Nov 19). Canceled meetings count.
    The meeting with the named closer booked on or before the alert's day, the latest one; None when Close has none."""
    if not h.get('lead_id'): return None
    first = _ln(h.get('closer')).split(' ')[0] if h.get('closer') else ''
    ms = [x for x in _q(get_all, '/activity/meeting/', {'lead_id': h['lead_id']}) if x.get('user_id') in CLOSERS
          and pt(x['date_created']) < day_bounds(d)[1] and (not first or first in _ln(x.get('user_name')))]
    return etd(max(pt(x['date_created']) for x in ms)) if ms else None


def inbound_sets(D, U, start, it_leads):
    """Inbound sets whose closer meeting was booked from day `start` through D, for setter user U.
    Returns [dict(lead_id, name, set_t, closer, intro_t)] sorted by set time."""
    a0 = day_bounds(start - dt.timedelta(days=2))[0]; b = day_bounds(D)[1]
    utc = lambda t: t.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    intro = get_all('/activity/meeting/', {'user_id': U, 'date_created__gte': utc(a0 - dt.timedelta(days=14)),
                                           'date_created__lt': utc(b)})
    joined = collections.defaultdict(list)          # lead -> [(zoom start, intro meeting created)]
    for y in intro:
        if y.get('user_id') != U or not y.get('lead_id') or _dead_meeting(y): continue
        z = _zoom(y)
        if z and z[2] and z[0] < b: joined[y['lead_id']].append((z[0], pt(y['date_created'])))
    out = []
    for l, zs in joined.items():
        if l in it_leads: continue                  # Incomplete Typeform lead: an outbound set (Jose's outbound card)
        lm = _q(get_all, '/activity/meeting/', {'lead_id': l})
        for y in lm: y['_t'] = pt(y['date_created'])
        cl = sorted([x for x in lm if x.get('user_id') in CLOSERS and not (x.get('title') or '').lower().startswith('canceled')],
                    key=lambda x: x['_t'])
        if not cl: continue
        oc = _q(get_all, '/activity/call/', {'lead_id': l, '_fields': 'id,date_created,direction,user_id,call_method'})
        msgs = None
        for x in cl:
            if not (day_bounds(start)[0] <= x['_t'] < b): continue
            ok = [(zt, it) for zt, it in zs if zt <= x['_t'] + dt.timedelta(minutes=5)]
            if not ok: continue
            zt, it = max(ok)
            if x['_t'] - zt > IN_WINDOW:            # booked later: needs the setter's own text or email after the Zoom
                if msgs is None:
                    msgs = [pt(m.get('date_sent') or m['date_created']) for m in
                            _q(get_all, '/activity/sms/', {'lead_id': l, '_fields': 'id,date_created,date_sent,direction,user_id,sequence_id,status'}) +
                            _q(get_all, '/activity/email/', {'lead_id': l, '_fields': 'id,date_created,date_sent,direction,user_id,sequence_id,status'})
                            if m.get('user_id') == U and m.get('direction') in ('outbound', 'outgoing') and not m.get('sequence_id')
                            and m.get('status') in ('sent', 'delivered', 'inbox')]
                if not any(zt < t < x['_t'] and x['_t'] - t <= HANDOFF for t in msgs): continue
            first_intro = min(i for _, i in zs)
            if any(o.get('user_id') == U and o.get('direction') == 'outbound' and o.get('call_method') != 'external'
                   and first_intro - IN_DIAL_BACK <= pt(o['date_created']) < first_intro for o in oc):
                break                               # the setter dialed the lead first: an outbound set, not inbound
            if any(y.get('user_id') in CLOSERS and y['_t'] < first_intro and same_person(y, x) for y in lm):
                break                               # already had a closer meeting with this person: a reschedule
            out.append(dict(lead_id=l, name=(x.get('title') or '').split(' and ')[0].strip() or l, set_t=x['_t'],
                            closer=x.get('user_name') or '', intro_t=zt, meeting=x))
            break                                   # one set per lead
    return sorted(out, key=lambda s: s['set_t'])


def run_inbound(D, key, flags_dir=None, now=None):
    global BALI, STEPS_FROM, HANDOFF_MIN, SETTER, CLOSES_FROM
    cfg = IN_SETTERS[key]; U = cfg['user']; now = now or dt.datetime.now(UTC)
    res = dict(key=key, name=cfg['name'], date=D.isoformat(), draw=cfg['draw'])
    # outbound tile (Jose and Jordan): closes / outbound sets since they started outbound (Oct 20), every list
    if cfg['outbound']:
        use_setter(key)
        sd = closer_sets_to_date(D); cl = closes_to_date(D)
        res['outbound'] = dict(sets=sd['count'], closes=len(cl), since=sd['since'],
                               closes_names=[r.get('lead') for r in cl])
    it_leads = list_leads(U, AB_USER_FIELD) if key == 'jose' else set()
    BALI = U; SETTER = dict(key=key, name=cfg['name']); STEPS_FROM = IN_FROM
    mon = _monday(D); start = max(min(mon, D) - dt.timedelta(days=IN_LOOK), IN_FROM - dt.timedelta(days=IN_LOOK))
    sets = inbound_sets(D, U, start, it_leads)
    # handoff steps for every set: email and note on the set day; reminders on their due days (lead_steps in bali_show.py).
    # Inbound: the handoff email counts when it goes out by the end of the set day (Sheila, Nov 19, 2026), not within an hour.
    ledger = []
    for s in sets:
        r = lead_show(s['lead_id'], s['set_t'], D, now)
        HANDOFF_MIN = max(60, int((day_bounds(etd(s['set_t']))[1] - s['set_t']).total_seconds() // 60))
        st = lead_steps(s['lead_id'], s['name'], s['set_t'], r['meetings'], D, r.get('showed_at'))
        s['steps'] = st; s['call'] = None
        live = [x for x in r['meetings'] if not _dead(x) and _start(x) >= s['set_t']]
        if live: s['call'] = _start(live[0])
        ledger.append(s)
    HANDOFF_MIN = 60
    # intro calls taken per day this week: Zooms on the setter's calendar that a lead joined
    a, b = day_bounds(D); zoom_by_day = collections.defaultdict(list)
    for y in get_all('/activity/meeting/', {'user_id': U, 'date_created__gte': (day_bounds(mon)[0] - dt.timedelta(days=IN_LOOK)).astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
                                             'date_created__lt': b.astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}):
        if y.get('user_id') != U or _dead_meeting(y): continue
        z = _zoom(y)
        if z and z[2] and day_bounds(mon)[0] <= z[0] < b: zoom_by_day[etd(z[0])].append(z)
    # each weekday Mon..D: sets, handoff steps due, price and booking flags, verdict.
    # A weekday with no intro calls, no sets and no steps due is not compliant (Sheila, Nov 20: compliant Monday to
    # Friday for the weekly draw); Sheila or Jay override days off in the tracker.
    days = []
    book_by_day = _booking_by_day(flags_dir, key, start, D, ledger)
    for i in range((D - mon).days + 1):
        d = mon + dt.timedelta(days=i)
        if d.weekday() > 4: continue
        due = [x for s in ledger for x in s['steps'] if x['due'] == d]
        fl = _flags(flags_dir, d)
        ph = _mine(fl['price']['hits'], key); bh = book_by_day.get(d, [])
        n_sets = sum(1 for s in ledger if etd(s['set_t']) == d)
        hand_ok = all(x['done'] for x in due)
        calls = len(zoom_by_day.get(d, []))
        idle = not calls and not n_sets and not due
        if d < IN_FROM: v = 'off'
        elif ph or bh or not hand_ok or idle: v = 'no'
        elif not fl['price']['checked'] or not fl['booking']['checked']: v = 'unchecked'
        else: v = 'yes'
        days.append(dict(date=d.isoformat(), dow=d.strftime('%a'), verdict=v, sets=n_sets, steps_due=len(due), calls=calls, idle=idle,
                         steps_done=sum(x['done'] for x in due), price=ph, booking=bh,
                         price_checked=fl['price']['checked'], booking_checked=fl['booking']['checked'],
                         missed=[f"{STEP_SHORT_IN[x['step']]} for {x['lead']}" for x in due if not x['done']]))
    today = days[-1] if days and days[-1]['date'] == D.isoformat() else None
    res['days'] = days; res['today'] = today
    res['sets_today'] = sum(1 for s in ledger if etd(s['set_t']) == D)
    res['sets_week'] = sum(1 for s in ledger if mon <= etd(s['set_t']) <= D)
    # table rows: sets made on D, then earlier sets with a reminder due on D
    flags = _flags(flags_dir, D)
    ph = _mine(flags['price']['hits'], key); bh = book_by_day.get(D, [])
    rows = []
    for s in ledger:
        sd_ = etd(s['set_t'])
        due_d = [x for x in s['steps'] if x['due'] == D]
        if sd_ != D and not any(x['step'] in ('day_before', 'morning_of') for x in due_d): continue
        cell = {}
        for k in ('email', 'note', 'day_before', 'morning_of'):
            xs = [x for x in s['steps'] if x['step'] == k]
            x = next((y for y in xs if y['due'] == D), None) or (xs[0] if xs else None)
            if x is None: cell[k] = 'later' if k in ('day_before', 'morning_of') else 'na'
            elif x['due'] > D: cell[k] = 'later'
            elif x['due'] == D: cell[k] = 'ok' if x['done'] else 'miss'
            else: cell[k] = 'ok_prev' if x['done'] else 'miss_prev'
        row = dict(lead=s['name'], lead_id=s['lead_id'], group='today' if sd_ == D else 'earlier',
                   call=_when(s['call']) if s['call'] else '', cells=cell)
        if sd_ == D:
            p = [h for h in ph if _match(h, s['lead_id'], s['name'])]
            b_ = [h for h in bh if _match(h, s['lead_id'], s['name'])]
            row['price'] = 'miss' if p else ('ok' if flags['price']['checked'] else 'unchecked')
            row['price_time'] = (p[0].get('time') or '') if p else ''
            row['booking'] = 'miss' if b_ else ('ok' if flags['booking']['checked'] else 'unchecked')
        rows.append(row)
    rows.sort(key=lambda r: (r['group'] != 'today', r['lead']))
    res['rows'] = rows
    # leads Messi flagged that aren't sets on the table (price came up on a call that didn't book)
    today_rows = [r for r in rows if r['group'] == 'today']
    res['price_other'] = [h for h in ph if not any(_match(h, r['lead_id'], r['lead']) for r in today_rows)]
    res['booking_other'] = [h for h in bh if not any(_match(h, r['lead_id'], r['lead']) for r in today_rows)]
    res['price'] = dict(checked=flags['price']['checked'], hits=ph)
    res['booking'] = dict(checked=flags['booking']['checked'], hits=bh)
    zz = zoom_by_day.get(D, [])
    res['calls_taken'] = len(zz)
    clk = lambda t: t.astimezone(ET).strftime('%-I:%M%p').lower()
    res['span'] = f"{clk(min(z[0] for z in zz))} to {clk(max(z[1] for z in zz))} ET" if zz else ''
    BALI = SETTERS['bali']['user'] if 'bali' in SETTERS else BALI
    return res


def _when(t):
    t = t.astimezone(ET); h = t.strftime('%-I') + (t.strftime(':%M') if t.minute else '') + t.strftime('%p').lower()
    return t.strftime('%a ') + h


STEP_SHORT_IN = dict(email='handoff email', note='closer note', day_before='day-before text', morning_of='day-of text')

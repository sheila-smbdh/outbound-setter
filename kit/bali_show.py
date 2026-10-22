
# Show rate and the three handoff steps for Bali's daily scorecard (Sheila, Oct 13, 2026).
# Runs in the Composio workbench AFTER bali_metrics.py and bali_cover.py (uses their helpers).
# Entry point: run_show(D, m) adds m['show'] and returns m. The daily run calls m = run_show(D, run_cover(D)).
#
# Show rate (strict, Sheila Oct 13): leads who showed / leads Bali set to a closer, one per lead (a closer's later
# meeting with the same lead is the same set). Reschedules wait: a lead with a closer meeting still ahead is pending
# and counts on the date of that meeting. No-shows, cancels (lead or closer side) and reschedule requests with no
# new meeting booked count as not showed. A past meeting with no outcome logged yet is left out and listed.
# Main number: leads whose meeting fell in the 7 days ending D. Under it: every lead set since Sep 16.
# Handoff steps (from Oct 13, 2026): 1) the "Setter to Closer Handoff" email right after booking; 2) a reminder the
# day before the call; 3) a personal reminder the morning of the call when the lead hasn't responded.
# Step 4 (Sheila, Oct 15, 2026): a closer note in Close with the lead's background, written by the end of the booking day.
DISC_TYPE = 'actitype_4mIZqROw9obY6LQWDvGdtn'                   # closer's "002) Discovery Call" activity
DISC_OUT = 'custom.cf_d6Xh2R1rxhHkMoo76I3O19HJCVbdrmeSczYD1bpV1IK'  # its Call Outcome field
NOT_SHOWED = ('no show', 'cancel', 'reschedule request')
SHOWED_OPP = ('next 7 days', 'in month closing', 'long term', 'split pay', 'offer not presented', 'won')
NOSHOW_OPP = ('no show/cancel', 'reschedule request')
HANDOFF_TMPL = 'tmpl_GfFgB6tt3nD6WaAsfgT3R8ZyuRvR8x9PtryCNr2oDN2'   # "Setter to Closer Handoff"
HANDOFF_SUBJ = 'your smb deal hunter discovery call with'
HANDOFF_MIN = 60          # step 1 counts when the handoff email goes out within 60 min of the booking
STEPS_FROM = dt.date(2026, 10, 13)   # Sheila introduced the three steps on Oct 13, 2026
SHOW_TARGET = 90
PRE_DISC_TYPE = 'actitype_7eSCr8m78jZ35sh13poUg8'      # Bali's "001) Pre-Discovery Call" form
PRE_DISC_NOTES = 'custom.cf_Pu5ktC6m2Ad9Gu0UEpe3UtfXOvg9RoZmojurmx7G5GJ'   # its "Pre-Discov Call Notes" field
NOTE_MIN_CHARS = 40       # step 4: a closer note needs at least this much text (HTML tags stripped)
_SETS = {}
# Oct 21, 2026 (Sheila): one card per setter. 'since' = first day their Welcome Series dials count (sets so far, closes,
# show rate); handoff steps count from max(Oct 13, since).
# Work hours for speed to lead (Sheila, Oct 22, 2026): 8 hours each, in the setter's own time zone. A list of
# (from date, time zone, start, end, label); the last entry whose date is on or before D applies.
# Bali said 7am-5pm PT (10 hours), so his 8 come from when he actually dials (Sep 28 to Oct 21: 89% of his calls fell
# in 9am-5pm PT). Jose gave no hours, so his come from his dialing too (91% in 10:30am-6:30pm ET).
# Jordan: 9am-4:30pm MT plus his extra hour, counted to 5pm MT; from Nov 1 he works Central time, same hours.
SETTERS = dict(
    bali=dict(name='Bali', user='user_c0wPSKtEPsqkIh08OnjiGaj6XHeFBjGSp2jyVxAggDl', since=dt.date(2026, 9, 16),
              hours=[(dt.date(2026, 9, 16), 'America/Los_Angeles', '09:00', '17:00', 'PT')]),
    jose=dict(name='Jose', user='user_msFtSHmZcoRAYvHX8aGrnygBzOy4u1GnLrRSFfIdcgk', since=dt.date(2026, 10, 20),
              hours=[(dt.date(2026, 10, 20), 'America/New_York', '10:30', '18:30', 'ET')]),
    jordan=dict(name='Jordan', user='user_3IrYZLUcCBZrg2mb49wCybrxGBFTCxa5eqTHhE1ApuC', since=dt.date(2026, 10, 20),
                hours=[(dt.date(2026, 10, 20), 'America/Denver', '09:00', '17:00', 'MT'),
                       (dt.date(2026, 11, 1), 'America/Chicago', '09:00', '17:00', 'CT')]))
SETTER = dict(key='bali', **SETTERS['bali'])

def use_setter(key):
    """Point every helper at one setter: their Close user (BALI), their list (LIST) and their start dates.
    Call before run_cover / run_show / week, and again before switching setters."""
    global BALI, LIST, CLOSES_FROM, STEPS_FROM, SETTER
    s = SETTERS[key]
    BALI = s['user']; LIST = list_leads(s['user']); CLOSES_FROM = s['since']
    STEPS_FROM = max(dt.date(2026, 10, 13), s['since']); SETTER = dict(key=key, **s)
    _SETS.clear()

def closer_sets(D):
    """Every closer call from Bali's pickups, Sep 16 through D, per day: [(date, lead_id, name, meeting)].
    Same rule as _bookings in bali_metrics.py (memoized: closer_sets_to_date below uses it too)."""
    if D in _SETS: return _SETS[D]
    data = load(D, back=(D - CLOSES_FROM).days)
    byl = _byl(data['calls']); out = []
    for i in range((D - CLOSES_FROM).days + 1):
        d = CLOSES_FROM + dt.timedelta(days=i); a, b = day_bounds(d)
        cl, _, names = _bookings(d, data, byl)
        for l in cl:
            x = sorted([y for y in data['meetings'] if y.get('lead_id') == l and a <= y['_t'] < b
                        and y.get('user_id') in CLOSERS], key=lambda y: y['_t'])
            nm = (x[0].get('title') or '').split(' and ')[0].strip() if x else l
            out.append((d, l, nm, x[0] if x else None))
    _SETS[D] = out
    return out

def closer_sets_to_date(D):
    """Replaces the bali_cover.py version with the same output, built from closer_sets (no second Close pull)."""
    out = [dict(date=d.isoformat(), name=nm) for d, l, nm, x in closer_sets(D)]
    return dict(count=len(out), since=CLOSES_FROM.isoformat(), list=out)

def _start(x): return pt(x['starts_at']) if x.get('starts_at') else x['_t']
def _dead(x): return (x.get('status') or '') in ('canceled', 'declined-by-lead', 'declined-by-org') or \
    (x.get('title') or '').lower().startswith('canceled')

def lead_show(l, set_t, D, now):
    """One lead's show status as of now, for meetings up to the end of D.
    Returns dict(status=showed|missed|pending|unlogged, date=ET date it counts on, meetings=[...])."""
    endD = day_bounds(D)[1]
    ms = [x for x in _q(get_all, '/activity/meeting/', {'lead_id': l}) if x.get('user_id') in CLOSERS]
    for x in ms: x['_t'] = pt(x['date_created'])
    ms = sorted([x for x in ms if x['_t'] >= set_t - dt.timedelta(minutes=1)], key=_start)
    ca = [c for c in _q(get_all, '/activity/custom/', {'lead_id': l})
          if c.get('custom_activity_type_id') == DISC_TYPE and pt(c['date_created']) >= set_t]
    osc = [o for o in _q(get_all, '/activity/status_change/opportunity/', {'lead_id': l}) if pt(o['date_created']) >= set_t]
    ev_show = [pt(c['date_created']) for c in ca if (c.get(DISC_OUT) or '').strip().lower() not in NOT_SHOWED and c.get(DISC_OUT)]
    ev_show += [pt(o['date_created']) for o in osc if (o.get('new_status_label') or '').lower().startswith(SHOWED_OPP)]
    past = [x for x in ms if _start(x) < endD]
    if ev_show:
        t = min(ev_show)
        att = [x for x in ms if _start(x) <= t] or past or ms
        return dict(status='showed', date=etd(_start(att[-1])) if att else etd(t), meetings=ms)
    ahead = [x for x in ms if _start(x) >= endD and not _dead(x)]
    if ahead: return dict(status='pending', date=etd(_start(ahead[0])), meetings=ms)
    if not past: return dict(status='pending', date=None, meetings=ms)
    last = past[-1]
    ev_no = any((c.get(DISC_OUT) or '').strip().lower() in NOT_SHOWED for c in ca) or \
        any((o.get('new_status_label') or '').lower().startswith(NOSHOW_OPP) for o in osc) or \
        (last.get('status') or '') in ('canceled', 'declined-by-lead') or (last.get('title') or '').lower().startswith('canceled')
    # 'declined-by-org' alone (the closer's calendar declined) is not proof the lead didn't show: it stays unlogged
    return dict(status='missed' if ev_no else 'unlogged', date=etd(_start(last)), meetings=ms)

def _touch(l):
    """Bali's outbound emails, texts and calls on a lead, and the lead's inbound emails and texts."""
    em = _q(get_all, '/activity/email/', {'lead_id': l, '_fields': 'id,date_created,direction,user_id,subject,template_id,status'})
    sm = _q(get_all, '/activity/sms/', {'lead_id': l, '_fields': 'id,date_created,direction,user_id,status'})
    ca = _q(get_all, '/activity/call/', {'lead_id': l, '_fields': 'id,date_created,direction,user_id,call_method'})
    sent = lambda s: s.get('status') not in ('draft', 'error', 'failed', 'scheduled', 'outbox')
    mine = [pt(x['date_created']) for x in em if x.get('user_id') == BALI and x.get('direction') == 'outgoing' and sent(x)]
    mine += [pt(x['date_created']) for x in sm if x.get('user_id') == BALI and x.get('direction') == 'outbound' and sent(x)]
    mine += [pt(x['date_created']) for x in ca if x.get('user_id') == BALI and x.get('direction') == 'outbound'
             and x.get('call_method') != 'external']
    handoff = [pt(x['date_created']) for x in em if x.get('user_id') == BALI and x.get('direction') == 'outgoing' and sent(x)
               and (x.get('template_id') == HANDOFF_TMPL or HANDOFF_SUBJ in (x.get('subject') or '').lower())]
    inbound = [pt(x['date_created']) for x in em if x.get('direction') == 'incoming'
               and not re.match(r'(new event|accepted|declined|updated|canceled|invitation)', (x.get('subject') or '').lower())]
    inbound += [pt(x['date_created']) for x in sm if x.get('direction') == 'inbound']
    return sorted(mine), sorted(handoff), sorted(inbound)

def _strip(s): return re.sub(r'<[^>]+>', ' ', s or '').strip()

def _closer_note(l, set_t):
    """Step 4 (Sheila, Oct 15, 2026): Bali wrote the lead's background in Close for the closer: a note, a call note or
    the notes field of his \"001) Pre-Discovery Call\" form, 40+ characters, from 24 hours before the booking to the
    end of the booking day (ET)."""
    lo = set_t - dt.timedelta(hours=24); hi = day_bounds(etd(set_t))[1]
    ok = lambda x: x.get('user_id') == BALI and lo <= pt(x['date_created']) < hi
    texts = [x.get('note') for x in _q(get_all, '/activity/note/', {'lead_id': l}) if ok(x)]
    texts += [x.get('note') for x in _q(get_all, '/activity/call/', {'lead_id': l, '_fields': 'id,date_created,user_id,note'}) if ok(x)]
    texts += [x.get(PRE_DISC_NOTES) for x in _q(get_all, '/activity/custom/', {'lead_id': l})
              if x.get('custom_activity_type_id') == PRE_DISC_TYPE and x.get('status') != 'draft' and ok(x)]
    return any(len(_strip(s)) >= NOTE_MIN_CHARS for s in texts)

def lead_steps(l, nm, set_t, meetings, D):
    """The three handoff steps for one set lead, each with the ET date it was due. Only steps due Oct 13 or later,
    and through D. A step that isn't owed (call booked for the next day or the same day) is left out."""
    mine, handoff, inbound = _touch(l); out = []
    if STEPS_FROM <= etd(set_t) <= D:
        ok = any(set_t - dt.timedelta(minutes=10) <= t <= set_t + dt.timedelta(minutes=HANDOFF_MIN) for t in handoff)
        out.append(dict(step='email', due=etd(set_t), done=ok, lead=nm))
        out.append(dict(step='note', due=etd(set_t), done=_closer_note(l, set_t), lead=nm))   # Oct 15, 2026
    for x in meetings:
        if _dead(x): continue
        s = _start(x); S = etd(s); booked = etd(x['_t'])
        if booked < S - dt.timedelta(days=1):      # day-before reminder owed only if booked 2+ days ahead
            P = S - dt.timedelta(days=1); pa, pb = day_bounds(P)
            if STEPS_FROM <= P <= D:
                out.append(dict(step='day_before', due=P, done=any(pa <= t < pb for t in mine), lead=nm))
        if booked < S:                              # morning-of reminder owed if he hasn't responded
            sa = day_bounds(S)[0]
            last = max([t for t in mine if t < sa] or [x['_t']])
            replied = any(last <= t < sa for t in inbound)
            if not replied and STEPS_FROM <= S <= D:
                out.append(dict(step='morning_of', due=S, done=any(sa <= t < s for t in mine), lead=nm))
    return out

def run_show(D, m, now=None):
    if not m.get('dialed'): return m
    now = now or dt.datetime.now(UTC)
    sets = closer_sets(D); seen = {}; rows = []; steps = []
    for d, l, nm, x in sets:
        if l in seen: continue                      # one set per lead: a later closer meeting is the same set
        seen[l] = 1
        set_t = x['_t'] if x else day_bounds(d)[0]
        r = lead_show(l, set_t, D, now)
        if r['status'] in ('showed', 'missed') and r['date'] and r['date'] > D:
            r['status'] = 'pending'                 # the meeting falls after D: not counted yet on this card
        rows.append(dict(lead=nm, lead_id=l, set=d.isoformat(), status=r['status'],
                         date=r['date'].isoformat() if r['date'] else None))
        steps += lead_steps(l, nm, set_t, r['meetings'], D)
    lo = (D - dt.timedelta(days=6)).isoformat(); hi = D.isoformat()
    win = [r for r in rows if r['date'] and lo <= r['date'] <= hi and r['status'] in ('showed', 'missed')]
    alln = [r for r in rows if r['status'] in ('showed', 'missed')]
    st = {}
    for k in ('email', 'note', 'day_before', 'morning_of'):
        s7 = [s for s in steps if s['step'] == k and lo <= s['due'].isoformat() <= hi]
        sd = [s for s in s7 if s['due'] == D]
        st[k] = dict(due=len(s7), done=sum(s['done'] for s in s7),
                     missed_on_day=[s['lead'] for s in sd if not s['done']],
                     missed_7d=[s['lead'] for s in s7 if not s['done']])
    m['show'] = dict(
        target=SHOW_TARGET, window=[lo, hi],
        n7=len(win), showed7=sum(r['status'] == 'showed' for r in win),
        missed7=[r['lead'] for r in win if r['status'] == 'missed'],
        n_all=len(alln), showed_all=sum(r['status'] == 'showed' for r in alln),
        pending=[r['lead'] for r in rows if r['status'] == 'pending'],
        unlogged=[r['lead'] for r in rows if r['status'] == 'unlogged'],
        steps=st, steps_from=STEPS_FROM.isoformat(), rows=rows)
    m['setter'] = dict(key=SETTER['key'], name=SETTER['name'], since=CLOSES_FROM.isoformat())
    return m

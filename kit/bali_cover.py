
# Cover-page metrics for Bali's daily scorecard (added Sep 30, 2026, per Sheila).
# Runs in the Composio workbench AFTER bali_metrics.py has been exec'd (uses its helpers).
# Entry point: run_cover(D) = run(D) plus m['cover'] (double dial, closes to date).
DD_GAP_SEC = 120          # a double dial = another call to the same number within ~2 min of a no-answer
CLOSES_FROM = dt.date(2026, 9, 16)   # Welcome Series outbound dials started Sep 16

def _num(c):
    return (c.get('remote_phone') or c.get('phone') or '').strip() or c['lead_id']

def double_dial(dc):
    """dc = Bali's real calls on one day. A no-answer is a call where he didn't reach a person
    (no answer or voicemail; screeners don't count). Each no-answer should be followed by another
    call to the same number within DD_GAP_SEC of it ending. The redial itself doesn't need its own redial."""
    g = collections.defaultdict(list)
    for c in sorted(dc, key=lambda c: c['_t']): g[_num(c)].append(c)
    elig = done = 0
    for cs in g.values():
        skip_next = False
        for i, c in enumerate(cs):
            if skip_next: skip_next = False; continue
            if c['_k'] not in ('miss', 'vm'): continue
            elig += 1
            if i + 1 < len(cs):
                end = c['_t'] + dt.timedelta(seconds=c.get('duration') or 0)
                if (cs[i+1]['_t'] - end).total_seconds() <= DD_GAP_SEC:
                    done += 1; skip_next = True
    return elig, done

def closes_to_date(D):
    """Won deals (date_won from Sep 16 through D) on leads whose closer call came from a Bali pickup:
    closer meeting within 24h after a Bali pickup, no other rep's call in between, and no meeting on the
    lead created before Bali's first real call. From Oct 13 a callback Bali answered counts as a pickup too."""
    opps = get_all('/opportunity/', {'status_type': 'won', 'date_won__gte': CLOSES_FROM.isoformat()})
    opps = [o for o in opps if o.get('date_won') and CLOSES_FROM.isoformat() <= o['date_won'][:10] <= D.isoformat()]
    if not opps: return []
    a0 = day_bounds(CLOSES_FROM)[0].astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    b0 = day_bounds(D)[1].astimezone(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
    bc = get_all('/activity/call/', {'user_id': BALI, 'date_created__gte': a0, 'date_created__lt': b0})
    bc = [c for c in bc if (c.get('direction') == 'outbound' and c.get('call_method') != 'external' and c.get('lead_id'))
          or inbound_talk(c)]
    dialed = {c['lead_id'] for c in bc}
    out = []
    for o in opps:
        L = o.get('lead_id')
        if L not in dialed or (EXCLUDE and L in EXCLUDE): continue   # Oct 28: Abandoned Typeform closes are on their own card
        lc = get_all('/activity/call/', {'lead_id': L})
        for c in lc: c['_t'] = pt(c['date_created']); c['_k'] = classify(c)
        mine = sorted([c for c in lc if c.get('user_id') == BALI and c.get('call_method') != 'external'
                       and (c.get('direction') == 'outbound' or inbound_talk(c))], key=lambda c: c['_t'])
        for c in mine:
            if c.get('direction') == 'inbound': c['_k'] = 'talk'   # callbacks he answered (Oct 13)
        if not mine: continue
        ms = get_all('/activity/meeting/', {'lead_id': L})
        for x in ms: x['_t'] = pt(x['date_created'])
        ms = [x for x in ms if not (x.get('title') or '').lower().startswith('canceled')]
        if any(x['_t'] < mine[0]['_t'] for x in ms): continue      # already booked before Bali dialed
        ok = None
        for x in sorted(ms, key=lambda x: x['_t']):
            if x.get('user_id') not in CLOSERS: continue
            lcs = [c for c in mine if c['_k'] == 'talk' and c['_t'] <= x['_t'] and x['_t'] - c['_t'] <= dt.timedelta(hours=24)]
            if not lcs: continue
            # Oct 8, 2026 (Sheila): an earlier Bali-owned meeting (set to self, two-step) no longer blocks the credit
            # other_rep_call (bali_metrics.py, Oct 6): 0-second 'external' duplicates by other users don't count
            if any(other_rep_call(c) and lcs[-1]['_t'] < c['_t'] < x['_t'] for c in lc): continue
            ok = x; break
        if ok:
            out.append(dict(lead=o.get('lead_name'), closer=o.get('user_name'), value=(o.get('value') or 0) / 100,
                            date_won=o['date_won'][:10], booked=ok['_t'].astimezone(ET).strftime('%b %-d')))
    best = {}
    for r in out:   # one close per lead (a lead can carry a duplicate $0 Won opportunity)
        if r['lead'] not in best or r['value'] > best[r['lead']]['value']: best[r['lead']] = r
    return sorted(best.values(), key=lambda r: r['date_won'])

WORK = (9, 21)   # 9am to 9pm ET: the speed window when no setter is selected (use_setter in bali_show.py), the old rule

def _clock(t):
    h, mi = t.hour, t.minute
    return f"{h % 12 or 12}{':%02d' % mi if mi else ''}{'am' if h < 12 else 'pm'}"

def work_window(D):
    """The setter's speed-to-lead hours on day D as (start, end) aware datetimes and a label for the card,
    e.g. '9am-5pm PT (12pm-8pm ET)'. Hours live in SETTERS (bali_show.py, Sheila, Oct 22, 2026)."""
    hrs = (globals().get('SETTER') or {}).get('hours')
    if not hrs: hrs = [(dt.date(2000, 1, 1), 'America/New_York', f'{WORK[0]:02d}:00', f'{WORK[1]:02d}:00', 'ET')]
    _, tz, s, e, ab = [h for h in hrs if h[0] <= D][-1] if any(h[0] <= D for h in hrs) else hrs[0]
    z = ZoneInfo(tz); mk = lambda x: dt.datetime.combine(D, dt.time.fromisoformat(x), tzinfo=z)
    a, b = mk(s), mk(e)
    lab = f"{_clock(a)}-{_clock(b)} {ab}"
    if ab != 'ET': lab += f" ({_clock(a.astimezone(ET))}-{_clock(b.astimezone(ET))} ET)"
    return a, b, lab

def speed_work(D, data):
    """Speed to lead for day D: new sign-ups (enrolled on D during the setter's work hours, work_window), first
    call after sign-up that same day. A lead never called that day counts as a miss."""
    a, b = day_bounds(D); wa, wb, _ = work_window(D); byl = _byl(data['calls']); out = []
    for l, e in data['enr'].items():
        if not (a <= e < b and wa <= e < wb): continue
        cs = [c for c in byl.get(l, []) if c['_t'] >= e - dt.timedelta(minutes=1) and c['_t'] < b]
        if not cs: out.append(dict(w=None, pick=False, real=False)); continue
        out.append(dict(w=max((cs[0]['_t'] - e).total_seconds() / 60, 0), pick=cs[0]['_k'] == 'talk',
                        real=any(is_real_call(c) for c in cs)))
    return out

def apply_work_speed(D, data, m):
    """Replace the dialing-window speed fields in m with the work-hours version (cover and detail card)."""
    sp = speed_work(D, data); w = [x['w'] for x in sp if x['w'] is not None]
    m['new_in_hours'] = len(sp); m['within15'] = sum(1 for x in w if x <= 15); m['in_hours_called'] = len(w)
    m['median_wait_min'] = round(statistics.median(w)) if w else None
    bk = collections.Counter(_bucket(x['w']) for x in sp)
    m['speed'] = dict(n=len(sp), **{k: bk.get(k, 0) for k in ['le15', 'm15_60', 'h1_3', 'h3p', 'none']})
    m['speed_window'] = m['work_hours'] = work_window(D)[2]
    agg = {'fast': [0, 0, 0], 'slow': [0, 0, 0]}
    for t in m.get('trend', []):
        d = dt.date.fromisoformat(t['date']); sd = speed_work(d, data)
        t['new_in_hours'] = len(sd); t['within15'] = sum(1 for x in sd if x['w'] is not None and x['w'] <= 15)
        for x in sd:
            if x['w'] is None: continue
            g = 'fast' if x['w'] <= 15 else 'slow'; agg[g][0] += 1; agg[g][1] += x['pick']; agg[g][2] += x['real']
    if 'speed7' in m:
        m['speed7'].update({g: dict(n=v[0], picked=v[1], real=v[2]) for g, v in agg.items()})
    return m

def run_cover(D):
    cache = {}
    g = globals(); orig = g['load']
    def load_once(DD, back=16):
        if (DD, back) not in cache: cache[(DD, back)] = orig(DD, back)
        return cache[(DD, back)]
    g['load'] = load_once
    try:
        m = run(D)
        if not m.get('dialed'): return m
        data = load_once(D, 16)
    finally:
        g['load'] = orig
    apply_work_speed(D, data, m)
    a, b = day_bounds(D)
    dc = [c for c in data['calls'] if a <= c['_t'] < b]
    dnc = data.get('dnc', {})   # Oct 8 (Sheila): leads set to Do Not Contact by the end of D are left out of double dial
    e, d = double_dial([c for c in dc if not (c['lead_id'] in dnc and dnc[c['lead_id']] < b)])
    cl = closes_to_date(D)
    m['cover'] = dict(dd_noans=e, dd_done=d, closes=len(cl), closes_list=cl,
                      closes_today=sum(1 for r in cl if r['date_won'] == D.isoformat()))
    m['cover']['closer_split'] = closer_split(D, data)   # Oct 8, 2026 (Sheila)
    m['duplicates'] = dup_check(D, data)   # Oct 8, 2026 (Sheila): duplicate sign-ups, for Sheila only, changes no count
    m['cover']['sets_to_date'] = closer_sets_to_date(D)   # Oct 8, 2026 (Sheila): cumulative sets to a closer
    # US caller ID on the previous dialing day, so the win can call out the day he switched
    isus = lambda c: (c.get('local_phone') or '').startswith('+1') and not (c.get('local_phone') or '').startswith('+1807')
    prev = sorted({etd(c['_t']) for c in data['calls'] if etd(c['_t']) < D})
    if prev:
        pa, pb = day_bounds(prev[-1]); pc = [c for c in data['calls'] if pa <= c['_t'] < pb]
        m['cover'].update(us_prev_day=prev[-1].isoformat(), us_prev_calls=sum(1 for c in pc if isus(c)), dials_prev=len(pc))
    return m

def closer_split(D, data):
    """Closer calls on D split by when Bali first called the lead (Sheila, Oct 8, 2026):
    'today' = his first call to the lead (or their first callback he answered) was on D; 'earlier' = before D."""
    a, b = day_bounds(D); byl = _byl(data['calls'])
    closer, _, _ = _bookings(D, data, byl)
    out = dict(today=[], earlier=[])
    for l in closer:
        nm = next(((x.get('title') or '').split(' and ')[0].strip() for x in data['meetings']
                   if x.get('lead_id') == l and a <= x['_t'] < b and x.get('user_id') in CLOSERS), l)
        lc = get_all('/activity/call/', {'lead_id': l})
        mine = [pt(c['date_created']) for c in lc if c.get('user_id') == BALI and c.get('call_method') != 'external'
                and (c.get('direction') == 'outbound' or inbound_talk(c))]
        out['today' if mine and min(mine) >= a else 'earlier'].append(nm)
    return out

def _digits(p):
    d = re.sub(r'\D', '', p or '')
    return d[-10:] if len(d) >= 10 else ''

def dup_check(D, data, days=14):
    """Duplicate sign-ups (Sheila, Oct 8, 2026): leads Bali dialed on D, or that signed up on D, that share a phone
    number or an email with another lead created in the last `days` days. For Sheila only; it changes no count."""
    a, b = day_bounds(D)
    lo = (D - dt.timedelta(days=days)).isoformat(); hi = (D + dt.timedelta(days=1)).isoformat()
    leads = get_all('/lead/', {'query': f'date_created >= "{lo}" date_created < "{hi}"',
                               '_fields': 'id,display_name,date_created,status_label,contacts', '_limit': 200})
    info = {}
    for L in leads:
        keys = set()
        for c in L.get('contacts') or []:
            keys |= {'phone:' + _digits(p.get('phone')) for p in c.get('phones') or [] if _digits(p.get('phone'))}
            keys |= {'email:' + (e.get('email') or '').strip().lower() for e in c.get('emails') or [] if e.get('email')}
        info[L['id']] = dict(name=L.get('display_name'), created=pt(L['date_created']), status=L.get('status_label'), keys=keys)
    dc = [c for c in data['calls'] if a <= c['_t'] < b]
    dialed = collections.Counter(c['lead_id'] for c in dc)
    for c in dc:
        if _digits(c.get('remote_phone')):
            info.setdefault(c['lead_id'], dict(name=None, created=None, status=None, keys=set()))['keys'].add('phone:' + _digits(c.get('remote_phone')))
    new = {l for l, t in data['enr'].items() if a <= t < b}
    bykey = collections.defaultdict(set)
    for l, x in info.items():
        for k in x['keys']: bykey[k].add(l)
    groups = {}
    for k, ls in bykey.items():
        if len(ls) < 2 or not (ls & (set(dialed) | new)): continue
        groups.setdefault(frozenset(ls), set()).add(k.split(':')[0])
    out = []
    for ls, how in groups.items():
        rows = []
        for l in ls:
            x = info[l]
            if x['name'] is None:
                try:
                    r, e = _q(proxy_execute, 'GET', f'/lead/{l}/', 'close', query_params={'_fields': 'display_name,date_created,status_label'})
                    d = r.get('data') if isinstance(r.get('data'), dict) else r
                    x.update(name=d.get('display_name'), status=d.get('status_label'),
                             created=pt(d['date_created']) if d.get('date_created') else None)
                except Exception: pass
            rows.append(dict(lead_id=l, name=x['name'] or l, status=x['status'], calls_on_day=dialed.get(l, 0),
                             signed_up_on_day=l in new,
                             created=x['created'].astimezone(ET).strftime('%b %-d %-I:%M%p').lower() if x['created'] else ''))
        rows.sort(key=lambda r: r['created'])
        out.append(dict(match=sorted(how), leads=rows, dialed_on_day=sum(1 for r in rows if r['calls_on_day'])))
    return dict(count=len(out), counted_twice=sum(max(0, g['dialed_on_day'] - 1) for g in out), groups=out)

def closer_sets_to_date(D):
    """Sets to a closer from Bali's dials since the test started (Sep 16) through D, one per day under the
    current closer-call rule (_bookings in bali_metrics.py). Sheila, Oct 8, 2026.
    (bali_show.py redefines this with the same output, built from its memoized closer_sets.)"""
    data = load(D, back=(D - CLOSES_FROM).days)
    byl = _byl(data['calls'])
    out = []
    for i in range((D - CLOSES_FROM).days + 1):
        d = CLOSES_FROM + dt.timedelta(days=i)
        _, _, names = _bookings(d, data, byl)
        out += [dict(date=d.isoformat(), name=n.strip()) for n in names]
    return dict(count=len(out), since=CLOSES_FROM.isoformat(), list=out)

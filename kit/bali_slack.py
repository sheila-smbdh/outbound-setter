
# Slack cross-check of Bali's real-conversation notes (Sheila, Oct 6, 2026).
# Bali posts a short note in the Slack group DM C0C11LAF4DB after each real conversation:
#   "<Name> - <liquidity> - <outcome>. <notes>" + a Close lead link.
# Sheila's decision (Oct 6): CROSS-CHECK ONLY. His notes never change any count on the cards or in the weekly report.
# They are used to (1) flag notes that don't match Close and (2) add names, liquidity and his notes to
# Sheila's caption and the weekly doc.
# Runs in the Composio workbench AFTER bali_metrics.py (and bali_cover.py) have been exec'd; uses their helpers.
# Entry points: slack_check(D, msgs) for one day; slack_week(days, msgs) for the weekly report.
# msgs = Slack messages from the channel as read by the Slack connector: dicts with 'user' (Slack user id or name),
# 'ts' (Slack ts string) and 'text'. Messages from others and from other days are ignored here.
SLACK_CHANNEL = 'C0C11LAF4DB'
SLACK_BALI = 'U0BP10N2WSU'
LEAD_RE = re.compile(r'lead_[A-Za-z0-9]{20,}')

def _reported(t):
    """What Bali says happened, from his note text."""
    t = (t or '').lower()
    if re.search(r'set to (closer|broker)', t): return 'set to closer'
    if re.search(r'set to self|booked (on|with) me|my calendar', t): return 'set to self'
    if re.search(r'\bf?dq\b|disqualif', t): return 'disqualified'
    if re.search(r'call ?back|two.?step', t): return 'call back later'
    if re.search(r'nurture|think it over|backed out', t): return 'nurture'
    return 'other'

def _note_name(t):
    t = re.sub(r'<[^>]*>', '', t or '').strip()
    return re.split(r'\s+-\s+|\s+\$|\s+\d', t, maxsplit=1)[0].strip()[:60]

def _liq(t):
    m = re.search(r'\$?\s?\d[\d.,]*\s?[kKmM]\+?', t or '')
    return m.group(0).strip() if m else ''

def _lead_name(l):
    try:
        r, e = _q(proxy_execute, 'GET', f'/lead/{l}/', 'close', query_params={'_fields': 'display_name'})
        d = r.get('data') if isinstance(r.get('data'), dict) else r   # proxy_execute may return the lead itself
        return d.get('display_name') or l
    except Exception:
        return l

def notes_for_day(D, msgs):
    a, b = day_bounds(D); out = []
    for x in msgs or []:
        u = str(x.get('user') or x.get('user_id') or '')
        if u != SLACK_BALI and 'bali' not in u.lower(): continue
        try: t = dt.datetime.fromtimestamp(float(x['ts']), tz=UTC)
        except Exception: continue
        if not (a <= t < b): continue
        txt = x.get('text') or ''
        ids = LEAD_RE.findall(txt)
        if not ids: continue
        for l in dict.fromkeys(ids):
            out.append(dict(lead_id=l, name=_note_name(txt), liquidity=_liq(txt), reported=_reported(txt),
                            text=re.sub(r'<[^>]*>', '', txt).strip()[:200], posted=t.astimezone(ET).strftime('%-I:%M%p').lower()))
    return out

def slack_check(D, msgs, data=None):
    """Cross-check Bali's Slack notes posted on D against Close. Counts are NOT changed (Sheila, Oct 6)."""
    notes = notes_for_day(D, msgs)
    if data is None: data = load(D, back=3)
    a, b = day_bounds(D); byl = _byl(data['calls'])
    dc = [c for c in data['calls'] if a <= c['_t'] < b]
    closer, selfs, cnames = _bookings(D, data, byl); booked = closer | selfs
    real = {c['lead_id'] for c in dc if is_real_call(c, booked)}
    pick = {c['lead_id'] for c in dc if c['_k'] == 'talk'}
    rows = []; seen = set()
    for n in notes:
        l = n['lead_id']
        if l in seen: continue
        seen.add(l)
        cs = [c for c in byl.get(l, []) if a <= c['_t'] < b]
        top = max(cs, key=lambda c: c.get('duration') or 0) if cs else None
        r = dict(n, calls=len(cs), longest_sec=(top or {}).get('duration') or 0,
                 outcome=OUTCOMES.get((top or {}).get('outcome_id') or '', '') or 'none',
                 picked_up=l in pick, real=l in real, closer_call=l in closer, self_set=l in selfs, flags=[])
        if not cs: r['flags'].append('no call from Bali to this lead on this day in Close')
        elif l not in real:
            r['flags'].append('not a real conversation under the scorecard rule (longest call %ss, outcome %s)'
                              % (r['longest_sec'], r['outcome']))
        if n['reported'] == 'set to closer' and l not in closer:
            r['flags'].append('he says set to closer, but no closer call was found under the booking rule')
        if n['reported'] == 'set to self' and l not in selfs and l not in closer:
            r['flags'].append('he says set to self, but no meeting was booked')
        r['status'] = 'flag' if r['flags'] else 'match'
        rows.append(r)
    posted = {r['lead_id'] for r in rows}
    unposted_real = sorted(real - posted)
    names = {l: _lead_name(l) for l in unposted_real}
    return dict(date=D.isoformat(), posted=len(rows), matched=sum(1 for r in rows if r['status'] == 'match'),
                flagged=sum(1 for r in rows if r['status'] == 'flag'), real_conversations=len(real),
                real_posted=len(real & posted), not_posted=[names[l] for l in unposted_real],
                closer_not_posted=[_lead_name(l) for l in sorted(closer - posted)], rows=rows)

def slack_week(days, msgs):
    """slack_check for each dialing day in the week (dates). Load once to save time."""
    days = sorted(days)
    data = load(days[-1], back=(days[-1] - days[0]).days + 3)
    per = [slack_check(d, msgs, data) for d in days]
    tot = {k: sum(p[k] for p in per) for k in ['posted', 'matched', 'flagged', 'real_conversations', 'real_posted']}
    tot['days'] = per
    return tot

# Setter draw (Sheila, Nov 16, 2026): Jose and Jordan earn a $1,000 draw for a week (Mon to Sun) when they are fully
# compliant on 5 of its 7 days. Runs Mon Nov 16 to Sun Nov 29, 2026. A day is compliant when all three hold:
#   1. Leads dialed: at least 60 leads (people dialed, not dials) that day.
#   2. Speed to lead: 60% or more of the new sign-ups during their work hours called within 20 minutes.
#   3. Handoff: 100% of the handoff steps due that day done (handoff email right after booking, closer note, day-before
#      reminder, morning-of reminder when the lead hasn't replied), the same four steps as the card's show rate tile.
# A KPI with nothing owed that day (no new sign-ups in work hours, no handoff steps due) counts as met. A day with no
# outbound calls is not a draw day. Weekends count only when the setter dialed (they can make up a missed weekday).
# Plain Python, no Close calls: reads the metrics JSON that run_direct.py (or the workbench) wrote.
#
# Usage, from kit/:
#   python3 setter_draw.py merge <days_values.json> <metrics-*.json ...> --out <dir>
#     days_values.json: the Days tab as read from the sheet ({"values": [[...], ...]} from the Sheets API, or {} when empty)
#     writes <dir>/draw-sheet.json (the Sheets values:batchUpdate body) and <dir>/draw-week-<key>-<date>.json
#     per card (pass it to build.py with --draw)
import json, sys, os, argparse, datetime as dt

DRAW = dict(start='2026-11-16', end='2026-11-29', amount=1000, days_needed=5,
            leads_min=60, speed_pct=60, speed_min=20)
STEPS = [('email', 'handoff email'), ('note', 'closer note'), ('day_before', 'day-before reminder'),
         ('morning_of', 'morning-of reminder')]
COLS = ['Week of', 'Date', 'Day', 'Setter', 'Leads dialed', 'Leads 60+', 'New sign-ups in hours',
        'Called within 20 min', 'Speed %', 'Speed 60%+', 'Handoff steps due', 'Handoff steps done',
        'Handoff 100%', 'Missed handoff steps', 'Draw day', 'Why not met', 'Checked at (ET)',
        "Sheila's override", 'Counts as']   # R is Sheila's to type in; S is a formula (override if set, else O)
SETTER_NAMES = dict(jose='Jose', jordan='Jordan')

def in_draw(d): return DRAW['start'] <= d <= DRAW['end']
def week_of(d):
    x = dt.date.fromisoformat(d); return (x - dt.timedelta(days=x.weekday())).isoformat()
def pct(a, b): return round(100 * a / b) if b else None

def draw_day(m):
    """The draw verdict for one setter-day from a metrics dict. checks: leads, speed, handoff, each with met
    (True, False) and a short reason; misses: the plain-English reasons the day was not met."""
    d = m['date']; key = (m.get('setter') or {}).get('key', '')
    if not m.get('dialed'):
        return dict(date=d, key=key, dialed=False, met=False, checks=[], misses=['No outbound calls'])
    pdl = m.get('people_dialed', 0) or 0
    ih = m.get('new_in_hours', 0) or 0; wm = m.get('within_min', m.get('within15', 0)) or 0
    sm = m.get('speed_min', 15); sp = pct(wm, ih)
    st = (m.get('show') or {}).get('steps') or {}
    due = sum((st.get(k) or {}).get('due_on_day', 0) for k, _ in STEPS)
    done = sum((st.get(k) or {}).get('done_on_day', 0) for k, _ in STEPS)
    missed = [(nm, (st.get(k) or {}).get('missed_on_day') or []) for k, nm in STEPS]
    missed = [(nm, who) for nm, who in missed if who]
    leads = dict(key='leads', name='Leads dialed', value=pdl, target=DRAW['leads_min'], met=pdl >= DRAW['leads_min'],
                 shown=f"{pdl} of {DRAW['leads_min']}",
                 why=f"Dialed {pdl} leads; the draw needs {DRAW['leads_min']}. {DRAW['leads_min'] - pdl} short.")
    speed = dict(key='speed', name=f'Speed to lead ({sm} min)', value=sp, target=DRAW['speed_pct'], owed=ih > 0,
                 met=(not ih) or sp >= DRAW['speed_pct'],
                 shown=(f"{sp}% ({wm} of {ih})" if ih else "No new sign-ups in your hours"),
                 why=f"Called {wm} of {ih} new sign-ups within {sm} minutes ({sp}%); the draw needs {DRAW['speed_pct']}%.")
    hand = dict(key='handoff', name='Handoff steps', value=done, target=due, owed=due > 0, met=done >= due,
                shown=(f"{done} of {due} done" if due else "None due"),
                why="Handoff steps missed: " + "; ".join(f"{nm} for {', '.join(who)}" for nm, who in missed) + ".")
    checks = [leads, speed, hand]
    return dict(date=d, key=key, dialed=True, met=all(c['met'] for c in checks), checks=checks,
                misses=[c['why'] for c in checks if not c['met']],
                leads=pdl, new_in_hours=ih, within_min=wm, speed_pct=sp, steps_due=due, steps_done=done,
                missed_steps="; ".join(f"{nm}: {', '.join(who)}" for nm, who in missed))

def row(v, now):
    """One Days-tab row (columns A to Q) for a draw_day verdict."""
    x = dt.date.fromisoformat(v['date']); nm = SETTER_NAMES.get(v['key'], v['key'])
    if not v['dialed']:
        return [week_of(v['date']), v['date'], x.strftime('%a'), nm, 0, 'Missed', '', '', '', '', '', '', '', '',
                'Not met', 'No outbound calls', now]
    c = {k['key']: k for k in v['checks']}
    ok = lambda k, owed=True: ('Met' if c[k]['met'] else 'Missed') if owed else 'None owed'
    return [week_of(v['date']), v['date'], x.strftime('%a'), nm, v['leads'], ok('leads'),
            v['new_in_hours'], v['within_min'], '' if v['speed_pct'] is None else v['speed_pct'] / 100,
            ok('speed', c['speed']['owed']), v['steps_due'], v['steps_done'], ok('handoff', c['handoff']['owed']),
            v['missed_steps'], 'Met' if v['met'] else 'Not met', ' '.join(v['misses']), now]

def merge(existing, verdicts, now):
    """Upsert verdict rows into the existing Days values by (date, setter). Rows keep their place (so Sheila's
    override in column R stays on its row); new rows go at the end. Returns the full A:Q values with the header."""
    vals = [list(r) for r in (existing.get('values') or [])][1:]
    ov = [r[17] if len(r) > 17 else '' for r in vals]   # Sheila's overrides, kept by row
    idx = {(r[1], r[3]): i for i, r in enumerate(vals) if len(r) > 3}
    for v in verdicts:
        r = row(v, now); k = (r[1], r[3])
        if k in idx: vals[idx[k]] = r
        else: idx[k] = len(vals); vals.append(r); ov.append('')
    return [COLS[:17]] + [(r + [''] * 17)[:17] for r in vals], ov

def week_status(rows, overrides, key, d):
    """The week (Mon to Sun) holding day d for one setter, from the merged rows: one entry per day so far."""
    wk = week_of(d); nm = SETTER_NAMES.get(key, key); days = {}
    for r, o in zip(rows[1:], overrides):
        if r[0] == wk and r[3] == nm and r[1] <= d:
            days[r[1]] = (o or r[14]) == 'Met'
    met = sum(days.values()); start = dt.date.fromisoformat(wk)
    left = [(start + dt.timedelta(days=i)).isoformat() for i in range(7)]
    left = [x for x in left if x > d]
    return dict(week=wk, end=(start + dt.timedelta(days=6)).isoformat(), needed=DRAW['days_needed'], met=met,
                days=[dict(date=x, met=days[x]) for x in sorted(days)], days_left=len(left),
                amount=DRAW['amount'])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['merge']); ap.add_argument('days'); ap.add_argument('metrics', nargs='+')
    ap.add_argument('--out', default='.')
    a = ap.parse_args()
    ex = json.load(open(a.days)) if os.path.exists(a.days) and os.path.getsize(a.days) else {}
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))).strftime('%Y-%m-%d %H:%M')
    ms = [json.load(open(p)) for p in a.metrics]
    vs = [draw_day(m) for m in ms if in_draw(m['date'])]
    # a weekend day with no outbound calls is not a row: they aren't expected to work weekends (Sheila, Nov 16)
    vs = [v for v in vs if v['dialed'] or dt.date.fromisoformat(v['date']).weekday() < 5]
    rows, ov = merge(ex, vs, now)
    n = len(rows)
    body = dict(valueInputOption='USER_ENTERED', data=[
        dict(range=f'Days!A1:Q{n}', majorDimension='ROWS', values=rows),
        dict(range=f'Days!S1:S{n}', majorDimension='ROWS',
             values=[[COLS[18]]] + [[f'=IF(R{i}<>"",R{i},O{i})'] for i in range(2, n + 1)])])
    os.makedirs(a.out, exist_ok=True)
    json.dump(body, open(os.path.join(a.out, 'draw-sheet.json'), 'w'))
    out = {}
    for m in ms:   # one file per card: the week as it stood on that card's day
        key = (m.get('setter') or {}).get('key')
        if not key or not in_draw(m['date']): continue
        w = week_status(rows, ov, key, m['date'])
        json.dump(w, open(os.path.join(a.out, f"draw-week-{key}-{m['date']}.json"), 'w'))
        out[f"{key} {m['date']}"] = w
    print(json.dumps(dict(rows=n - 1, verdicts=[dict(date=v['date'], key=v['key'], met=v['met'], misses=v['misses'])
                                                for v in vs], weeks=out), indent=1))

if __name__ == '__main__':
    main()

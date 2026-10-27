# Objection check, publishing side: turn one day's grades into rows for the two dashboards and merge them into the
# files already on the dashboards. Runs in the Claude container after grading.
#   python3 oc_publish.py build BUNDLE.json GRADES.json EXISTING_DIR OUT_DIR
# BUNDLE.json is oc_local.py's bundle for day D; GRADES.json is the session's grades for D (format in RUNBOOK.md,
# "Grades file"). EXISTING_DIR holds the current oc-<dataset>.json files downloaded from the dashboards (a missing
# file counts as empty). OUT_DIR gets the merged oc-calls/objections/coaching/flags/days.json plus headline.txt.
# Rerunning a day replaces that day's rows, so a corrected run never doubles up.
import os, sys, json

SETTERS = {'Bali (Jabali Dumas)': 'Bali', 'Jordan Kempster': 'Jordan Kempster', 'Jose Rodriguez': 'Jose Rodriguez'}
SHORT = list(SETTERS.values())
TYPES = ('conversation', 'voicemail', 'screener', 'logistics', 'unclear', 'cut off')
OBJECTIONS = ('Price', 'Send me info', 'Not right now', 'Is this legit', 'I can do this myself', 'Quick answer', 'Other')
GRADES = ('Hit', 'Partial', 'Miss')
DATASETS = ('calls', 'objections', 'coaching', 'flags', 'days')

def fail(msg): sys.exit(f'grades file problem: {msg}')

def clean(s, where):
    s = (s or '').strip()
    if '—' in s: fail(f'em dash in {where}; rewrite it without one')
    return s

def build(bundle_p, grades_p, existing, out):
    bundle, grades = json.load(open(bundle_p)), json.load(open(grades_p))
    day = bundle['date']
    if grades.get('day') != day: fail(f"day {grades.get('day')!r} does not match the bundle's {day!r}")
    by_id = {r['id']: r for r in bundle['rows']}
    graded = {c['call_id']: c for c in grades.get('calls', [])}
    missing = sorted(set(by_id) - set(graded))
    extra = sorted(set(graded) - set(by_id))
    if missing: fail(f'{len(missing)} calls in the bundle have no grade: {missing[:5]}')
    if extra: fail(f'calls not in the bundle: {extra[:5]}')

    calls, objections = [], []
    for cid, b in by_id.items():
        g = graded[cid]
        setter = SETTERS[b['setter']]
        if g.get('type') not in TYPES: fail(f"{cid}: type {g.get('type')!r} not one of {TYPES}")
        conv = g['type'] == 'conversation'
        booked = ('yes' if g.get('booked_live') else 'no') if conv else ''
        base = {'day': day, 'setter': setter, 'call_id': cid, 'lead': b['lead'], 'time_et': b['at_et'],
                'length_sec': b['recording_duration'], 'booked_live': booked, 'close_url': b['close_url']}
        calls.append(dict(base, type=g['type']))
        if not conv:
            if g.get('objections'): fail(f'{cid}: objections on a {g["type"]} call')
            continue
        objs = g.get('objections') or []
        if not objs:
            objections.append(dict(base, row_id=f'{day}-{cid[-10:]}-0', objection='None', lead_words='', grade='',
                                   decided_by='', instead=''))
        for i, o in enumerate(objs):
            if o.get('objection') not in OBJECTIONS: fail(f"{cid}: objection {o.get('objection')!r} not one of {OBJECTIONS}")
            if o.get('grade') not in GRADES: fail(f"{cid}: grade {o.get('grade')!r} not one of {GRADES}")
            instead = clean(o.get('instead'), f'{cid} instead') or ('Handled per script.' if o['grade'] == 'Hit' else '')
            if o['grade'] != 'Hit' and not instead: fail(f'{cid}: a {o["grade"]} needs "instead"')
            objections.append(dict(base, row_id=f'{day}-{cid[-10:]}-{i}', objection=o['objection'],
                                   lead_words=clean(o.get('lead_words'), f'{cid} lead_words'), grade=o['grade'],
                                   decided_by=clean(o.get('decided_by'), f'{cid} decided_by'), instead=instead))

    coaching = []
    for c in grades.get('coaching', []):
        if c.get('setter') not in SHORT: fail(f"coaching setter {c.get('setter')!r} not one of {SHORT}")
        coaching.append({'day': day, 'setter': c['setter'], **{k: clean(c.get(k), f'coaching {k}') for k in
                         ('focus', 'lead_said', 'setter_said', 'script_says', 'best_moment')}})
    flags = []
    for f in grades.get('flags', []):
        if f.get('setter') not in SHORT: fail(f"flag setter {f.get('setter')!r} not one of {SHORT}")
        flags.append({'day': day, 'setter': f['setter'], 'flag': clean(f.get('flag'), 'flag'), 'detail': clean(f.get('detail'), 'flag detail')})
    dials = bundle.get('calls_by_setter', {})
    days = [{'day': day, 'setter': SETTERS[k], 'dials': dials.get(k, 0)} for k in SETTERS]

    new = {'calls': calls, 'objections': objections, 'coaching': coaching, 'flags': flags, 'days': days}
    os.makedirs(out, exist_ok=True)
    for ds in DATASETS:
        p = os.path.join(existing, f'oc-{ds}.json')
        old = json.load(open(p)) if os.path.exists(p) else []
        rows = [r for r in old if r.get('day') != day] + new[ds]
        rows.sort(key=lambda r: (r['day'], r.get('setter', ''), r.get('time_et', '')))
        json.dump(rows, open(os.path.join(out, f'oc-{ds}.json'), 'w'), indent=1)

    lines = []
    for s in SHORT:
        g = [o for o in objections if o['setter'] == s and o['grade']]
        conv = sum(1 for c in calls if c['setter'] == s and c['type'] == 'conversation')
        booked = sum(1 for c in calls if c['setter'] == s and c['booked_live'] == 'yes')
        if not conv:
            n = dials.get(next(k for k, v in SETTERS.items() if v == s), 0)
            lines.append(f'{s}: no real conversations ({n} call{"" if n == 1 else "s"}).')
            continue
        h = sum(1 for o in g if o['grade'] == 'Hit') + sum(1 for o in g if o['grade'] == 'Partial') / 2
        pct = f'{round(100 * h / len(g))}% handled per script' if g else 'no objections'
        lines.append(f'{s}: {pct} ({len(g)} objections, {conv} conversations), {booked} set live.')
    open(os.path.join(out, 'headline.txt'), 'w').write('\n'.join(lines) + '\n')
    print(json.dumps({'day': day, 'calls': len(calls), 'objections': len(objections), 'coaching': len(coaching),
                      'flags': len(flags), 'out': out}))
    print('\n'.join(lines))

if __name__ == '__main__':
    if len(sys.argv) != 6 or sys.argv[1] != 'build': sys.exit(__doc__ or 'usage: oc_publish.py build BUNDLE GRADES EXISTING_DIR OUT_DIR')
    build(*sys.argv[2:])

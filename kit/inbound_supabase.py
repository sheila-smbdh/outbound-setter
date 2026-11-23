# Supabase rows for one inbound scorecards run (Sheila, Nov 23, 2026). Plain Python, no network calls: it writes one
# JSON file per table, and the routine sends each file with ONE inline curl upsert (Sheila's Supabase rules: inline
# curl only, one request per command, never a script that calls Supabase). Tables: supabase/inbound_scorecards.sql.
#
# Usage, from kit/:
#   python3 inbound_supabase.py <run_id> <D> <inbound-*.json ...> [--outbound <metrics-jose_it.json>] --out <dir>
# Writes <dir>/days.json, sets.json, calls.json, run.json and (with --outbound) outbound.json, and prints the curl
# command for each (table, on_conflict columns).
import json, os, argparse, datetime as dt
from inbound_draw import day_row   # same 'why' text as the tracker

BASE = 'https://suoblmuvrmyfmuvlhqce.supabase.co/rest/v1'
TABLES = dict(days=('inbound_sc_days', 'day,setter'), sets=('inbound_sc_sets', 'setter,lead_id,set_day'),
              calls=('inbound_sc_calls', 'day,setter,lead_id'), outbound=('outbound_sc_days', 'day,setter'),
              run=('inbound_sc_runs', 'run_id'))
DRAW = ('jose', 'jordan')


def status(x, k):
    hits, chk = x[k], x[k + '_checked']
    return 'Missed' if hits else ('Met' if chk else 'Not checked')


def pct(a, b): return round(100 * a / b) if b else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run_id'); ap.add_argument('date'); ap.add_argument('inbound', nargs='+')
    ap.add_argument('--outbound'); ap.add_argument('--out', default='.')
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    days, sets, calls, summ = [], [], [], {}
    for p in a.inbound:
        r = json.load(open(p)); key = r['key']; ob = r.get('outbound') or {}
        for x in r['days']:
            if x['verdict'] == 'off': continue
            hand = 'None due' if not x['steps_due'] else ('Met' if x['steps_done'] >= x['steps_due'] else 'Missed')
            days.append(dict(day=x['date'], setter=key, intro_calls=x.get('calls'), inbound_sets=x['sets'],
                             inbound_sets_week=r['sets_week'] if x['date'] == r['date'] else None,
                             booked_calls=x.get('booked'), scheduled_calls=x.get('scheduled'), live_calls=x.get('live'),
                             steps_due=x['steps_due'], steps_done=x['steps_done'], handoff=hand,
                             price=status(x, 'price'), booking=status(x, 'booking'),
                             verdict=dict(yes='Compliant', no='Not compliant', unchecked='Not checked').get(x['verdict'], x['verdict']),
                             why=day_row(key, x, '')[12] or None, price_hits=x['price'], booking_hits=x['booking'], missed_steps=x.get('missed') or [],
                             outbound_sets_total=ob.get('sets') if x['date'] == r['date'] else None,
                             outbound_closes_total=ob.get('closes') if x['date'] == r['date'] else None,
                             draw=key in DRAW, last_run_id=a.run_id, updated_at=now))
            for c in x.get('call_rows') or []:
                calls.append(dict(day=x['date'], setter=key, lead_id=c['lead_id'], lead_name=c['lead'], starts_at=c['start'],
                                  booked=c['booked'], scheduled=c['scheduled'], live=c['live'], removed_reason=c['removed'],
                                  last_run_id=a.run_id, updated_at=now))
        rows = {x['lead_id']: x for x in r.get('rows') or [] if x['group'] == 'today'}
        for s in r.get('ledger') or []:
            st = {y['step']: y for y in s['steps']}
            cell = lambda k: ('ok' if st[k]['done'] else 'miss') if k in st else ('later' if k in ('day_before', 'morning_of') else 'na')
            rw = rows.get(s['lead_id']) if s['set_day'] == r['date'] else None
            sets.append(dict(setter=key, lead_id=s['lead_id'], set_day=s['set_day'], lead_name=s['name'], closer=s['closer'],
                             set_at=s['set_at'], call_at=s['call_at'], email=cell('email'), note=cell('note'),
                             day_before=cell('day_before'), day_of=cell('morning_of'),
                             price=rw.get('price') if rw else None, booking=rw.get('booking') if rw else None,
                             last_run_id=a.run_id, updated_at=now))
        t = r.get('today') or {}
        summ[key] = dict(verdict=t.get('verdict'), sets=r['sets_today'], booked=(r.get('calls') or {}).get('booked'),
                         scheduled=(r.get('calls') or {}).get('scheduled'), live=(r.get('calls') or {}).get('live'))
    # one row per key: a later file for the same day and setter wins
    dedupe = lambda xs, ks: list({tuple(x[k] for k in ks): x for x in xs}.values())
    out = dict(days=dedupe(days, ('day', 'setter')), sets=dedupe(sets, ('setter', 'lead_id', 'set_day')),
               calls=dedupe(calls, ('day', 'setter', 'lead_id')))
    if a.outbound:
        m = json.load(open(a.outbound)); c = m.get('cover') or {}; st = (m.get('show') or {}).get('steps') or {}
        if m.get('dialed'):
            out['outbound'] = [dict(day=m['date'], setter='jose_it', dials=m.get('dials'), leads_dialed=m.get('people_dialed'),
                                    speed_pct=pct(m.get('within_min', 0) or 0, m.get('new_in_hours', 0)),
                                    pickup_pct=pct(m.get('pickups', 0), m.get('people_dialed', 0)),
                                    connect_pct=pct(m.get('real_conversations', 0), m.get('people_dialed', 0)),
                                    vm_pct=None, text_pct=None, dd_pct=pct(c.get('dd_done', 0), c.get('dd_noans', 0)),
                                    handoff_due=sum((st.get(k) or {}).get('due_on_day', 0) for k in st),
                                    handoff_done=sum((st.get(k) or {}).get('done_on_day', 0) for k in st),
                                    sets_to_closer=m.get('closer_calls'), sets_since_start=(c.get('sets_to_date') or {}).get('count'),
                                    closes_since_start=len(c.get('closes_list') or []), metrics=m, last_run_id=a.run_id, updated_at=now)]
            summ['jose_it'] = dict(dials=m.get('dials'), sets=m.get('closer_calls'))
    out['run'] = [dict(run_id=a.run_id, card_day=a.date, status='ok', summary=summ)]
    os.makedirs(a.out, exist_ok=True)
    for k, rows in out.items():
        p = os.path.join(a.out, f'{k}.json'); json.dump(rows, open(p, 'w'), default=str)
        tbl, oc = TABLES[k]
        print(f'{len(rows):4d} rows  curl -s -X POST "{BASE}/{tbl}?on_conflict={oc}" -H "Content-Type: application/json" '
              f'-H "Prefer: resolution=merge-duplicates,return=minimal" --data-binary @{os.path.abspath(p)} -w "%{{http_code}}\\n"')


if __name__ == '__main__':
    main()

# Inbound draw tracker (Sheila, Nov 20, 2026): Jose and Jordan are eligible for a week's draw when every weekday,
# Monday to Friday, is compliant on all 3 inbound KPIs (handoff steps 100%, no price on calls, no direct-to-closer
# bookings). Draw weeks start Mon Nov 23, 2026. Sheila and Jay can override any day or week in the sheet.
# Plain Python, no Close calls: reads the inbound-<key>.json files run_inbound.py wrote (each carries Mon..D of its week,
# so every run refreshes the earlier days of the week with Messi's latest results).
#
# Usage, from kit/:
#   python3 inbound_draw.py <days_values.json> <weeks_values.json> <inbound-*.json ...> --out <dir>
#     *_values.json: the tab as read from the sheet ({"values": [[...], ...]} from the Sheets API, or {} when empty)
#     writes <dir>/inbound-draw-sheet.json, the Sheets values:batchUpdate body (USER_ENTERED)
# Sheet: "Setter Draw Tracker" (1hvHFzqlPJzOq2ght4Ld4iZopX_9RgfYnMbWRuGScOzE), tabs "Inbound Days" and "Inbound Weeks".
# The routine writes Inbound Days A:O and R, and Inbound Weeks A:I and L. Never P:Q (Days) or J:K (Weeks): those are
# Sheila's and Jay's overrides. Both tabs are protected so only Sheila and Jay can edit them.
import json, os, argparse, datetime as dt

DRAW_FROM = '2026-11-23'
NAMES = dict(jose='Jose', jordan='Jordan')
DAYS_TAB, WEEKS_TAB = 'Inbound Days', 'Inbound Weeks'
DAY_COLS = ['Week of', 'Date', 'Day', 'Setter', 'Intro calls', 'Inbound sets', 'Handoff steps due',
            'Handoff steps done', 'Handoff 100%', 'No price on calls', 'No direct bookings', 'Day verdict',
            'Why', 'Missed handoff steps', 'Checked at (ET)',
            'Override (Sheila/Jay)', 'Override note', 'Counts as']          # P:Q typed by Sheila/Jay; R formula
WEEK_COLS = ['Week of', 'Setter', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Compliant days (of 5)', 'Auto result',
             'Override (Sheila/Jay)', 'Override note', 'Eligible for the draw']   # J:K typed by Sheila/Jay; L formula
VERDICT = dict(yes='Compliant', no='Not compliant', unchecked='Not checked')


def week_of(d):
    x = dt.date.fromisoformat(d); return (x - dt.timedelta(days=x.weekday())).isoformat()


def day_row(key, x, now):
    hand = 'None due' if not x['steps_due'] else ('Met' if x['steps_done'] >= x['steps_due'] else 'Missed')
    price = 'Missed' if x['price'] else ('Met' if x['price_checked'] else 'Not checked')
    book = 'Missed' if x['booking'] else ('Met' if x['booking_checked'] else 'Not checked')
    why = []
    if x.get('idle'): why.append('No intro calls, sets or steps due')
    if hand == 'Missed': why.append(f"{x['steps_due'] - x['steps_done']} of {x['steps_due']} handoff steps missed")
    for h in x['price']:
        why.append(f"Price on a call with {h.get('lead') or 'a lead'}" + (f" at {h['time']}" if h.get('time') else '') +
                   (f': "{h["quote"]}"' if h.get('quote') else ''))
    for h in x['booking']:
        why.append(f"Direct booking: {h.get('lead') or 'a lead'}" + (f" with {h['closer']}" if h.get('closer') else ''))
    if price == 'Not checked': why.append("Messi's price check didn't come in")
    if book == 'Not checked': why.append("Messi's booking check didn't come in")
    return [week_of(x['date']), x['date'], x['dow'], NAMES[key], x.get('calls', ''), x['sets'], x['steps_due'],
            x['steps_done'], hand, price, book, VERDICT.get(x['verdict'], x['verdict']), '. '.join(why),
            '; '.join(x.get('missed') or []), now]


def upsert(existing, new_rows, keyf, width):
    """Rows keep their place (so the override columns typed beside them stay on the right row); new rows go at the end."""
    vals = [list(r) for r in (existing.get('values') or [])][1:]
    idx = {keyf(r): i for i, r in enumerate(vals) if len(r) >= 2}
    for r in new_rows:
        k = keyf(r)
        if k in idx: vals[idx[k]] = r
        else: idx[k] = len(vals); vals.append(r)
    return [(r + [''] * width)[:width] for r in vals]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('days'); ap.add_argument('weeks'); ap.add_argument('inbound', nargs='+')
    ap.add_argument('--out', default='.')
    a = ap.parse_args()
    load = lambda p: json.load(open(p)) if os.path.exists(p) and os.path.getsize(p) else {}
    ex_d, ex_w = load(a.days), load(a.weeks)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))).strftime('%Y-%m-%d %H:%M')
    new_days, weeks = [], set()
    for p in a.inbound:
        r = json.load(open(p)); key = r['key']
        if key not in NAMES: continue                       # Dave has no draw
        for x in r['days']:
            if x['date'] < DRAW_FROM: continue
            new_days.append(day_row(key, x, now)); weeks.add((week_of(x['date']), NAMES[key]))
    # Week of and Date as text keys: the sheet stores them as dates, read back as YYYY-MM-DD (FORMATTED_VALUE with
    # the tab's yyyy-mm-dd format)
    days = upsert(ex_d, new_days, lambda r: (str(r[1]), str(r[3])), 15)
    n = len(days) + 1
    new_weeks = [[w, s] for w, s in sorted(weeks)]
    wk = upsert(ex_w, new_weeks, lambda r: (str(r[0]), str(r[1])), 2)
    m = len(wk) + 1
    D = f"'{DAYS_TAB}'"
    look = lambda i, off: (f'=IFERROR(INDEX(FILTER({D}!$R$2:$R,{D}!$B$2:$B=$A{i}+{off},{D}!$D$2:$D=$B{i}),1),"")')
    wrows = [[look(i, o) for o in range(5)] + [f'=COUNTIF(C{i}:G{i},"Compliant")',
             f'=IF(H{i}=5,"Eligible",IF(COUNTIF(C{i}:G{i},"Not compliant")>0,"Not eligible","In progress"))']
             for i in range(2, m + 1)]
    body = dict(valueInputOption='USER_ENTERED', data=[
        dict(range=f"{D}!A1:O{n}", majorDimension='ROWS', values=[DAY_COLS[:15]] + days),
        dict(range=f"{D}!R1:R{n}", majorDimension='ROWS',
             values=[[DAY_COLS[17]]] + [[f'=IF(P{i}<>"",P{i},L{i})'] for i in range(2, n + 1)]),
        dict(range=f"'{WEEKS_TAB}'!A1:I{m}", majorDimension='ROWS',
             values=[WEEK_COLS[:9]] + [r + w for r, w in zip(wk, wrows)]),
        dict(range=f"'{WEEKS_TAB}'!L1:L{m}", majorDimension='ROWS',
             values=[[WEEK_COLS[11]]] + [[f'=IF(J{i}<>"",J{i},I{i})'] for i in range(2, m + 1)])])
    os.makedirs(a.out, exist_ok=True)
    json.dump(body, open(os.path.join(a.out, 'inbound-draw-sheet.json'), 'w'))
    print(json.dumps(dict(day_rows=n - 1, week_rows=m - 1,
                          days=[dict(date=r[1], setter=r[3], verdict=r[11]) for r in new_days]), indent=1))


if __name__ == '__main__':
    main()

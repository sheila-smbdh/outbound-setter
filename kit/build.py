"""Build Bali's daily scorecard (v3: cover page + summary card + detail card) from a metrics JSON
(output of bali_cover.py run_cover(), which is run() from bali_metrics.py plus m['cover'], then bali_show.py run_show()).
usage: python3 build.py metrics.json out_dir
writes out_dir/bali-daily-scorecard.html (artifact body), out_dir/scorecard-YYYY-MM-DD-0-cover.png,
out_dir/scorecard-YYYY-MM-DD-1-summary.png, out_dir/scorecard-YYYY-MM-DD-2-detail.png
and out_dir/daily-YYYY-MM-DD.json (the record saved to the project)
The summary and detail cards come from template.html; the cover comes from cover.html.
v3.1 (Oct 5, 2026): cover shows 7 KPI tiles; Connect rate (real conversations per person dialed, target 10%)
added next to Pickup rate so the two aren't confused.
v3.2 (Oct 5, 2026): voicemail KPI counts only no-pickups who gave Bali a chance to leave a voicemail
(metrics 'vm_possible'); people who hung up, declined, or whose call never went through are left out.
v3.3 (Oct 5, 2026): real conversation = a 60+ sec call tagged Set to closer, Call back later or Disqualified,
or Set to self only when a meeting was actually booked (is_real_call in bali_metrics.py). The Connect tile
carries a small note saying Set to self counts only when booked (kpi 'note').
v3.4 (Oct 6, 2026): a blue "Set to a closer" tile after the 7 KPI tiles (metrics 'closer_calls'). It is tracked
only: no target, not counted in the targets hit, no win or fix line of its own (cover 'track').
Oct 8, 2026: Set to a closer tile split by first call (cover closer_split); text KPI counted out of text_possible
(first-call no-pickups minus blocked or invalid numbers).
v4 (Oct 13, 2026, Sheila): three priorities on top: speed to lead, dials and show rate (metrics 'show' from
bali_show.py: rolling 7 days, target 90%, with all calls set since Sep 16 and the three handoff steps under it).
Pickup, connect, voicemail, text and double dial move to a compliance section at the bottom (kpi group 'comp')
with the blue Set to a closer tile. "You hit X of 3 priority targets" counts only the priorities. Fixes: handoff
steps missed that day, then priority misses (worst first), then any compliance number in red.
Oct 14, 2026 (Sheila): two images only (cover and summary/funnel card); the detail card is hidden (#card2 in
cover.html) and the cover has no footnote.
Oct 15, 2026 (Sheila): a fourth handoff step under show rate, "Closer note attached" (metrics show.steps.note from
bali_show.py): Bali writes the lead's background in Close for the closer by the end of the booking day.
"""
import json, sys, os, asyncio, pathlib, datetime

HERE = pathlib.Path(__file__).parent
BASE = dict(within15_pct=7, target_within15_pct=60, median_wait="about 1.5 hrs",
            conv_rate_pct=26, closer_per_day="0.75")
# Cover-page targets (Sheila, Sep 30, 2026; connect added Oct 5, 2026; show rate added Oct 13, 2026)
TARGETS = dict(speed=60, dials=200, show=90, pickup=25, connect=10, vm=85, text=85, dd=85)  # vm/text/dd lowered from 100 to 85 (Sheila, Oct 14)  # dials raised from 150 to 200 on Sep 30
PRIORITY = ('speed', 'dials', 'show')                   # Sheila, Oct 13: what Bali focuses on now
COMPLIANCE = ('pickup', 'connect', 'vm', 'text', 'dd')  # still tracked, at the bottom of the cover
WIN_GROUPS = (('pickup', 'connect'), ('vm', 'text', 'dd'))   # compliance hits share a win line (Sheila, Oct 14)
CLOSE_PCT = 75   # yellow ('almost') when the number is at least 75% of its target
US_OK = 0.95     # share of calls on a US caller ID that counts as switched
ROUND_TWO = "2026-09-30"   # round two start, for the cumulative sets line
# small print under a tile's big number (Sheila, Oct 5)
NOTES = dict(connect="Set to self counts only when a meeting is actually booked.",
             show="Last 7 days. A rescheduled call counts on its new date.")
STEP_NAMES = [("email", "Handoff email right after booking"), ("note", "Closer note attached"),
              ("day_before", "Reminder the day before"), ("morning_of", "Morning-of reminder (no reply)")]
STEP_FIX = dict(
    email=("Handoff email", "Not sent within an hour of booking for {n}. Send the Setter to Closer Handoff email from Close right after you book."),
    note=("Closer note", "No closer note in Close for {n}. Write the lead's background in Close the day you book, so the closer can read it before the call."),
    day_before=("Day-before reminder", "{n} got no reminder from you the day before the call. Send one the day before every closer call."),
    morning_of=("Morning-of reminder", "{n} hadn't replied and got no reminder from you the morning of the call. Send a personal reminder that morning."))
FOOT = ("From Close, times in ET. Picked up: talked to a real person (TALK code or 45+ sec; screeners and voicemails don't count). "
        "Real conversation: a call of 60+ sec tagged set to closer, call back later or disqualified, or set to self when a meeting was actually booked (untagged calls: 3+ min or led to a booking). "
        "Voicemail: voicemail drop, the left-voicemail outcome or a note starting with VM; "
        "it counts only people who gave you a chance to leave one (not those who hung up, declined, or whose call didn't go through). "
        "Within 15 min: new sign-ups during your work hours (9am to 9pm ET), called within 15 minutes.")
COVER_FOOT = ("From Close, times in ET. Speed to lead: new sign-ups during 9am-9pm ET, called within 15 minutes. "
              "Dials: every call. "
              "Show rate: leads you set to a closer whose call was in the last 7 days, and how many showed (from the closer's Discovery Call outcome). "
              "No-shows, cancels and reschedule requests with no new time booked count as not showed; a rescheduled call counts on its new date. "
              "Under it: every lead you've set to a closer since Sep 16, one per lead. "
              "Handoff steps (from Oct 13): the Setter to Closer Handoff email within an hour of booking; a text, email or call the day before the call "
              "(when it was booked 2+ days out); and, when the lead hasn't replied, a personal reminder the morning of the call before it starts. "
              "Pickup rate: people who picked up the phone (a real person answered; screeners and voicemails don't count), out of people dialed. "
              "Connect rate: people you had a real conversation with, out of people dialed. A real conversation is a call of 60+ seconds "
              "you tagged set to closer, call back later or disqualified, or a call tagged set to self when a meeting was actually booked "
              "(sending your link alone doesn't count). Calls you didn't tag count if they lasted 3+ minutes or led to a booking. "
              "Voicemail: people who didn't pick up on your first call that day and gave you a chance to leave a voicemail. "
              "People who hung up on you, declined the call, or whose call didn't go through (busy, blocked, automated message, wrong number) aren't counted. "
              "Text: everyone who didn't pick up on your first call that day, except numbers Close blocked or you noted as invalid. "
              "Double dial: another call to the same number within 2 minutes of a no-answer or voicemail. "
              "Leads marked Do Not Contact that day are left out of voicemail, text and double dial. "
              "Set to a closer: leads booked on a closer's calendar that day, within 24 hours of a call where you reached them (tracked, no target), split into leads you first called that day and leads you first called on an earlier day. "
              "Sets to a closer so far: every closer call booked off your pickups since Sep 16, under the same rule. "
              "Closes: Won deals from closer calls booked off your pickups, since Sep 16.")

def pct(a, b): return round(100 * a / b) if b else 0

def names(xs, k=3):
    xs = list(xs)
    return ", ".join(xs) if len(xs) <= k else ", ".join(xs[:k]) + f" and {len(xs) - k} more"

def vm_base(m):
    """People the voicemail KPI is counted out of: no-pickups who gave Bali a chance to leave one."""
    v = m.get("vm_possible")
    return m.get("missed_first", 0) if v is None else v

def text_base(m):
    """People the text KPI is counted out of: first-call no-pickups minus blocked or invalid numbers (Oct 8, 2026)."""
    v = m.get("text_possible")
    return m.get("missed_first", 0) if v is None else v

def us_switched(m):
    """True on the first dialing day his calls go out on a US number (previous day mostly 807)."""
    c = m.get("cover") or {}; d = m.get("dials", 0)
    if not d or m.get("us_number_calls", 0) / d < US_OK: return False
    dp = c.get("dials_prev", 0)
    return bool(dp) and c.get("us_prev_calls", 0) / dp < 0.5

def pick_win(m):
    c = m.get("cover") or {}
    today = [r for r in c.get("closes_list", []) if r["date_won"] == m["date"]]
    parts = []
    if today:
        r = today[0]
        more = f" and {len(today)-1} more" if len(today) > 1 else ""
        parts.append(f"{r['lead']}{more} closed with {r['closer']}, from a closer call you booked on {r['booked']}.")
    if us_switched(m):
        parts.append(f"You switched to your US number: {m['us_number_calls']} of {m['dials']} calls went out on it.")
    if parts: return " ".join(parts)
    n = m.get("missed_first", 0)
    if m.get("closer_calls"): return f"You booked {m['closer_calls']} closer call{'s' if m['closer_calls']>1 else ''}. Keep booking them live, while the lead is on the phone."
    sp = pct(m.get("within15", 0), m.get("new_in_hours", 0))
    if m.get("new_in_hours") and sp > BASE["within15_pct"]:
        return f"{m['within15']} of {m['new_in_hours']} new leads got a call within 15 minutes ({sp}%), up from {BASE['within15_pct']}% in round one."
    if m.get("vm_left"): return f"You left {m['vm_left']} voicemails on first-call misses. That's the touch that lands when they don't pick up."
    if m.get("dials") and m.get("us_number_calls") == m.get("dials"): return "Every call went out on your US number."
    if m.get("self_sets"): return f"You booked {m['self_sets']} call{'s' if m['self_sets']>1 else ''} to your own calendar."
    if m.get("try2_same_day") and n and pct(m["try2_same_day"], n) >= 30: return f"{m['try2_same_day']} no-answers got a second call later the same day."
    return f"You put in the volume: {m.get('dials',0)} calls to {m.get('people_dialed',0)} people."

def pick_fix(m):
    n = m.get("missed_first", 0); d = m.get("dials", 0); vb = vm_base(m)
    if d and m.get("us_number_calls", 0) / d < US_OK:
        return f"{d - m.get('us_number_calls',0)} of {d} calls still showed the Canadian 807 number. Switch your caller ID to the US number before your first call."
    if m.get("power_dialer_calls"):
        return f"{m['power_dialer_calls']} calls went through the Power Dialer. Call one lead at a time so you can dial twice and leave the voicemail."
    if vb >= 5 and pct(m.get("vm_left", 0), vb) < 50:
        return f"{vb} people didn't pick up on your first call and gave you a chance to leave a voicemail; you left {m.get('vm_left',0)}. Leave the SOP voicemail every time, then text."
    ih = m.get("new_in_hours", 0)
    if ih and pct(m.get("within15", 0), ih) < BASE["target_within15_pct"]:
        late = ih - m.get("within15", 0)
        return f"{late} of {ih} new leads waited more than 15 minutes. Keep your list sorted newest first and call new sign-ups before anything else."
    if n >= 5 and pct(m.get("try2_same_day", 0), n) < 50:
        return f"Only {m.get('try2_same_day',0)} of {n} no-answers got a second call later that day. Keep the call task and dial again in a few hours."
    tb = text_base(m)
    if tb >= 5 and pct(m.get("text_sent", 0), tb) < 50:
        return f"You texted {m.get('text_sent',0)} of {tb} people who didn't pick up. Send the SOP text right after each voicemail."
    pm = m.get("prev_missed", 0)
    if pm >= 5 and pct(m.get("try3_next_day", 0), pm) < 50:
        return f"{m.get('try3_next_day',0)} of {pm} misses from the day before got their third try. Work the next-day call tasks first thing."
    return "Keep it up: same plan tomorrow."

def track_tiles(m):
    """Blue tiles after the KPI tiles: numbers we track with no target (Sheila, Oct 6, 2026)."""
    cc = m.get("closer_calls", 0) or 0
    nms = m.get("closer_names") or []
    sp = closer_split(m)
    if cc and sp:
        # split by when Bali first called the lead (Sheila, Oct 8, 2026): first called that day vs on an earlier day
        parts = []
        if sp["today"]: parts.append(f"<b>{len(sp['today'])} first called that day:</b> " + ", ".join(sp["today"]))
        if sp["earlier"]: parts.append(f"<b>{len(sp['earlier'])} first called on an earlier day:</b> " + ", ".join(sp["earlier"]))
        det = "<br>".join(parts)
    else:
        det = (f"{'lead' if cc == 1 else 'leads'} booked with a closer" + (": " + ", ".join(nms) if nms else "")) if cc else "No closer calls booked"
    return [dict(key="closer", name="Set to a closer", value=cc, detail=det, note="")]

def closer_split(m):
    """cover.closer_split from bali_cover.py (Oct 8, 2026), names ordered as in closer_names. None on older metrics."""
    s = (m.get("cover") or {}).get("closer_split")
    if not s: return None
    order = {n.strip(): i for i, n in enumerate(m.get("closer_names") or [])}
    key = lambda n: order.get(n.strip(), 99)
    return dict(today=sorted(s.get("today", []), key=key), earlier=sorted(s.get("earlier", []), key=key))

def show_row(m):
    """Show rate tile (Sheila, Oct 13, 2026) from m['show'] (bali_show.py). None on older metrics."""
    sh = m.get("show")
    if not sh: return None
    n7, s7 = sh["n7"], sh["showed7"]
    val = pct(s7, n7) if n7 else None
    det = (f"{s7} of {n7} closer calls showed" if n7 else "No closer calls were due in the last 7 days")
    nall, sall = sh["n_all"], sh["showed_all"]
    # all-time show rate as its own stat under the 7-day number (made bigger, Sheila Oct 14)
    extra = dict(all=(f'<div class="al">All calls you\'ve set since Sep 16</div>'
                      f'<div class="av">{pct(sall, nall)}%<span>{sall} of {nall} showed</span></div>') if nall else "",
                 steps_head="Handoff steps, last 7 days",
                 steps=[dict(name=nm, done=sh["steps"][k]["done"], due=sh["steps"][k]["due"]) for k, nm in STEP_NAMES
                        if k in sh["steps"]])   # 'note' (closer note) exists from the Oct 15, 2026 run on
    miss = sh.get("missed7") or []
    fx = (f"{n7 - s7} of {n7} closer calls in the last 7 days didn't show" + (f" ({names(miss)})" if miss else "") +
          ". Do all four handoff steps on every booking.")
    return ("show", "Show rate", val, "%", det, fx, extra)

def cover(m, win):
    c = m.get("cover") or {}
    T = TARGETS; n = m.get("missed_first", 0); ih = m.get("new_in_hours", 0); pd = m.get("people_dialed", 0)
    dn, dd = c.get("dd_noans", 0), c.get("dd_done", 0)
    rc = m.get("real_conversations", 0)
    vb = vm_base(m); vl = m.get("vm_left", 0); nov = n - vb
    vm_det = f"{vl} of {vb} no-answers who let you leave one" + (f" ({nov} hung up or didn't go through, not counted)" if nov else "")
    tb = text_base(m); ts = m.get("text_sent", 0); notx = n - tb
    tx_det = f"{ts} of {tb} no-answers got one" + (f" ({notx} blocked or invalid {'number' if notx == 1 else 'numbers'}, not counted)" if notx else "")
    rows = [  # key, name, value, unit, detail, fix text when missed, extra
        ("speed", "Speed to lead", pct(m.get("within15", 0), ih), "%", f"{m.get('within15',0)} of {ih} new leads in 15 min",
         f"{ih - m.get('within15',0)} of {ih} new sign-ups waited 15+ minutes" + (f" ({(m.get('speed') or {}).get('none',0)} never got a call that day)" if (m.get('speed') or {}).get('none') else "") + ". Call new sign-ups first, the moment they come in.", None),
        ("dials", "Dials", m.get("dials", 0), "", f"{m.get('dials',0)} calls",
         f"{T['dials'] - m.get('dials',0)} short of {T['dials']}. Add a dialing block.", None),
        show_row(m),
        ("pickup", "Pickup rate", pct(m.get("pickups", 0), pd), "%", f"{m.get('pickups',0)} of {pd} people picked up",
         f"{m.get('pickups',0)} of {pd} people picked up. Faster first calls and double dials lift this.", None),
        ("connect", "Connect rate", pct(rc, pd), "%", f"{rc} of {pd} people had a real conversation",
         f"{rc} of {pd} people had a real conversation. Use the new opener to keep pickups on the line.", None),
        ("vm", "Voicemail", pct(vl, vb), "%", vm_det,
         f"{vb - vl} of {vb} no-answers who let you leave a voicemail didn't get one. Leave one every time you hear the beep.", None),
        ("text", "Text", pct(ts, tb), "%", tx_det,
         f"{tb - ts} of {tb} no-answers got no text. Text right after the voicemail.", None),
        ("dd", "Double dial", pct(dd, dn), "%", f"{dd} of {dn} no-answers redialed",
         f"{dn - dd} of {dn} no-answers weren't redialed. Hang up and dial again right away.", None),
    ]
    kpis, pmiss, cmiss = [], [], []
    for r in rows:
        if r is None: continue
        key, name, val, unit, det, fx, extra = r
        if val is None:
            hit, status = False, "none"
        else:
            hit = val >= T[key]
            status = "hit" if hit else ("close" if val >= T[key] * CLOSE_PCT / 100 else "miss")
        k = dict(key=key, name=name, value=val, unit=unit, detail=det, target=T[key], hit=hit, status=status,
                 note=NOTES.get(key, ""), group="comp" if key in COMPLIANCE else "priority")
        if extra: k["extra"] = extra
        kpis.append(k)
        if status in ("close", "miss") and key in PRIORITY: pmiss.append(((T[key] - val) / T[key], name, fx))
        if status == "miss" and key in COMPLIANCE: cmiss.append(((T[key] - val) / T[key], name, fx))
    # fixes: handoff steps he missed that day (by lead), then priority misses worst first, then compliance in red
    fixes = []
    st = (m.get("show") or {}).get("steps") or {}
    for k, _ in STEP_NAMES:
        miss = (st.get(k) or {}).get("missed_on_day") or []
        if miss:
            nm, txt = STEP_FIX[k]
            fixes.append([nm, txt.format(n=names(miss))])
    fixes += [[nm, fx] for _, nm, fx in sorted(pmiss, key=lambda x: -x[0])]
    fixes += [[nm, fx] for _, nm, fx in sorted(cmiss, key=lambda x: -x[0])]
    if not fixes: fixes = [["Keep it up", "Every priority on target and compliance is holding. Same plan tomorrow."]]
    cl = c.get("closes_list", [])
    closes_text = ("close from your dials so far" if len(cl) == 1 else "closes from your dials so far") + \
                  (": " + ", ".join(r["lead"] for r in cl) if cl else "")
    # wins, as a numbered list like the fixes: closes that day, US number switch, closer calls booked,
    # leads who showed for their closer call that day, targets hit
    wins = []
    today = [r for r in cl if r["date_won"] == m["date"]]
    for r in today:
        wins.append(["Close", f"{r['lead']} closed with {r['closer']}, from a closer call you booked on {r['booked']}."])
    if us_switched(m):
        wins.append(["US number", f"You switched: {m['us_number_calls']} of {m['dials']} calls went out on your US number."])
    if m.get("closer_calls"):
        sp = closer_split(m); extra = ""
        if sp and sp["today"] and sp["earlier"]:
            nt, ne = len(sp['today']), len(sp['earlier'])
            extra = (f" ({nt} {'lead' if nt == 1 else 'leads'} you first called that day, "
                     f"{ne} {'lead' if ne == 1 else 'leads'} you first called on an earlier day)")
        wins.append(["Closer calls", f"You booked {m['closer_calls']} closer call{'s' if m['closer_calls'] > 1 else ''}{extra}."])
    showed = [r["lead"] for r in (m.get("show") or {}).get("rows", []) if r["status"] == "showed" and r["date"] == m["date"]]
    if showed:
        wins.append(["Showed up", f"{names(showed)} {'was' if len(showed) == 1 else 'were'} on their closer call."])
    # targets hit: priorities one line each; compliance hits grouped so the list stays short (Sheila, Oct 14):
    # pickup + connect on one line, voicemail + text + double dial on one line
    for k in kpis:
        if k["hit"] and k["group"] != "comp":
            wins.append([k["name"], f"{k['value']}{k['unit']} vs a target of {k['target']}{k['unit']}. You hit it."])
    for keys in WIN_GROUPS:
        hits = [k for key in keys for k in kpis if k["key"] == key and k["hit"]]
        if not hits: continue
        if len(hits) == 1:
            k = hits[0]
            wins.append([k["name"], f"{k['value']}{k['unit']} vs a target of {k['target']}{k['unit']}. You hit it."])
            continue
        nm = [k["name"] if i == 0 else k["name"].lower() for i, k in enumerate(hits)]
        title = (", ".join(nm[:-1]) + " and " + nm[-1]).replace(" rate and ", " and ")
        vals = ", ".join(f"{k['value']}%" for k in hits[:-1]) + f" and {hits[-1]['value']}%"
        tg = {k["target"] for k in hits}
        tgt = (f"a target of {hits[0]['target']}%" if len(tg) == 1 else
               "targets of " + ", ".join(f"{k['target']}%" for k in hits[:-1]) + f" and {hits[-1]['target']}%")
        wins.append([title, f"{vals} vs {tgt}. You hit {'both' if len(hits) == 2 else 'all three'}."])
    if not wins: wins = [["Win", win]]
    # cumulative sets to a closer since the test started Sep 16 (Sheila, Oct 8, 2026); cover.sets_to_date from bali_cover.py
    sd = c.get("sets_to_date")
    sets = sd["count"] if sd else None
    r2 = sum(1 for x in sd["list"] if x["date"] >= ROUND_TWO) if sd else 0
    sets_text = ("set to a closer" if sets == 1 else "sets to a closer") + f" from your dials so far ({r2} in round two)" if sd else ""
    return dict(win=win, wins=wins, fixes=fixes, kpis=kpis, track=track_tiles(m), closes=len(cl), closes_text=closes_text,
                sets=sets, sets_text=sets_text, footnote=COVER_FOOT)

def build(metrics, out_dir):
    tpl = (HERE / "template.html").read_text()
    cov = (HERE / "cover.html").read_text()
    font = (HERE / "manrope.b64").read_text().strip()
    win = pick_win(metrics)
    data = dict(metrics=metrics, baseline=BASE, win=win, fix=pick_fix(metrics), footnote=FOOT, cover=cover(metrics, win))
    # cover markup goes before the summary card; its script goes after the data block
    i = cov.index("<script>"); cov_html, cov_js = cov[:i], cov[i:]
    tpl = tpl.replace('<div class="card" id="card1">', cov_html + '\n<div class="card" id="card1">', 1)
    tpl = tpl.rstrip() + "\n" + cov_js
    body = tpl.replace("__FONT__", font).replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
    os.makedirs(out_dir, exist_ok=True)
    art = pathlib.Path(out_dir) / "bali-daily-scorecard.html"; art.write_text(body)
    full = (pathlib.Path(out_dir) / "_render.html").resolve()
    full.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                    '<style>html,body{margin:0}</style></head><body>' + body + "</body></html>")
    od = pathlib.Path(out_dir).resolve()
    rec = dict(date=metrics['date'], saved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
               win=data['win'], wins=data['cover']['wins'], fix=data['fix'], fixes=data['cover']['fixes'], kpis=data['cover']['kpis'],
               track=data['cover']['track'], closes=data['cover']['closes'], baseline=BASE, targets=TARGETS, metrics=metrics)
    (od / f"daily-{metrics['date']}.json").write_text(json.dumps(rec, indent=1, default=str))
    d = metrics['date']
    # two images since Oct 14 (Sheila): the cover and the summary (funnel) card; the detail card is hidden
    pngs = [str(od / f"scorecard-{d}-0-cover.png"), str(od / f"scorecard-{d}-1-summary.png")]
    asyncio.run(_shot(str(full), pngs))
    return data, str(art), pngs

async def _shot(src, outs):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 780, "height": 900}, device_scale_factor=2, color_scheme="light")
        await pg.goto("file://" + src); await pg.wait_for_timeout(400)
        for sel, out in zip(["#card0", "#card1"], outs):
            await pg.locator(sel).screenshot(path=out)
        await b.close()

if __name__ == "__main__":
    m = json.load(open(sys.argv[1]))
    d, a, p = build(m, sys.argv[2])
    print(json.dumps({"win": d["win"], "fix": d["fix"], "fixes": d["cover"]["fixes"], "artifact_file": a, "pngs": p,
                      "daily_file": str(pathlib.Path(sys.argv[2]).resolve() / f"daily-{m['date']}.json")}))

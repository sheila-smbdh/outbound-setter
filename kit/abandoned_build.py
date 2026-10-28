"""Build Bali's Abandoned Typeform card (a third image, separate from the Welcome Series cards) from the metrics JSON
written by run_abandoned(D) in bali_abandoned.py. Per-lead layout approved by Sheila on Oct 22, 2026
(mockups/abandoned-typeform-mockup.png): four rate tiles, a bar of where the day's leads landed, one table per group
(real conversation, picked up without one, didn't pick up, not called) with each lead's next step, and the closer
calls that happened that day (the follow-up calls section was dropped Oct 28, 2026). Talks to Bali as "you".
usage: python3 abandoned_build.py metrics.json out_dir
writes out_dir/abandoned-YYYY-MM-DD.html, out_dir/scorecard-YYYY-MM-DD-3-abandoned.png and
out_dir/abandoned-links-YYYY-MM-DD.txt (the lead names as Slack links, since the PNG can't hold links).
Chromium: set CHROMIUM_PATH to a local Chromium if Playwright's own browser isn't installed.
"""
import json, sys, os, asyncio, pathlib, datetime, html

HERE = pathlib.Path(__file__).parent
CLOSE_URL = "https://app.close.com/lead/{}/"
CLOSE_PCT = 75   # yellow ('almost') at 75% of the target or more, same as the Welcome Series cover
STEPS = (("email", "Email"), ("note", "Note"), ("day_before", "Day before"), ("morning_of", "Morning of"))
GROUPS = (("real", "Real conversations"), ("short", "Picked up, no real conversation"),
          ("nopick", "Didn't pick up"), ("notcalled", "Not called yet"))
CSS = """
:root{--bg:#f1f0ec;--card:#fbfbf9;--ink:#15171a;--ink2:#55585e;--ink3:#86888d;--line:#e2e1db;--accent:#2256b8;--good:#1a7f37;--good-soft:#e2f2e6;--bad:#c23a32;--bad-soft:#f8e3e1;--yel:#e3a800;--yel-ink:#946c00;--yel-soft:#f8efcf;--track:#e9e8e3;--short:#6aa77b;--f:"Manrope",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#141517;--card:#1c1d20;--ink:#f2f2f0;--ink2:#b4b5b8;--ink3:#8a8b8f;--line:#2d2e32;--accent:#6f9cf0;--good:#4cc26a;--good-soft:#17301f;--bad:#f07068;--bad-soft:#3a1d1b;--yel-ink:#f2c94c;--yel-soft:#3a3115;--track:#2a2b2f;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#141517;--card:#1c1d20;--ink:#f2f2f0;--ink2:#b4b5b8;--ink3:#8a8b8f;--line:#2d2e32;--accent:#6f9cf0;--good:#4cc26a;--good-soft:#17301f;--bad:#f07068;--bad-soft:#3a1d1b;--yel-ink:#f2c94c;--yel-soft:#3a3115;--track:#2a2b2f;color-scheme:dark}
@font-face{font-family:"Manrope";src:url(data:font/woff2;base64,__FONT__) format("woff2");font-weight:200 800}
body{background:var(--bg);color:var(--ink);font-family:var(--f);font-size:14px;line-height:1.4;margin:0;padding:20px 16px}
.card{max-width:760px;margin:0 auto;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px clamp(16px,4vw,28px);display:flex;flex-direction:column;gap:22px}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3)}
h1{font-size:28px;margin:4px 0 4px;letter-spacing:-.02em} .meta{color:var(--ink2)}
h2{font-size:13px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:var(--accent);margin:0 0 4px;display:flex;justify-content:space-between;align-items:baseline;gap:10px}
h2 span{font-size:22px;letter-spacing:0;color:var(--ink);text-transform:none}
h2 span.sm{font-size:14px;font-weight:700;color:var(--ink2)}
.lead{color:var(--ink2);margin:0 0 10px;font-size:13px}
.tiles{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.tile{border:1px solid var(--line);border-left:6px solid var(--ink3);border-radius:10px;padding:10px}
.tile.hit{border-left-color:var(--good);background:var(--good-soft)} .tile.miss{border-left-color:var(--bad);background:var(--bad-soft)}
.tile.close{border-left-color:var(--yel);background:var(--yel-soft)} .tile.track{border-left-color:var(--accent)}
.tile .k{font-size:11px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--ink2)}
.tile .v{font-size:28px;font-weight:800;line-height:1.1} .tile.hit .v{color:var(--good)} .tile.miss .v{color:var(--bad)}
.tile.close .v{color:var(--yel-ink)} .tile.track .v{color:var(--accent)} .tile.none .v{color:var(--ink3)}
.tile .d{font-size:12px;color:var(--ink2)}
.segbar{display:flex;height:28px;border-radius:8px;overflow:hidden;gap:2px}
.segbar i{display:flex;align-items:center;padding-left:8px;font-style:normal;color:#fff;font-size:13px;font-weight:800}
.segbar .real{background:var(--good)} .segbar .short{background:var(--short)} .segbar .nopick{background:var(--accent)} .segbar .notcalled{background:var(--ink3)}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12.5px;color:var(--ink2);margin-top:6px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{font-size:10.5px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--ink3);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
td{padding:7px 6px;border-bottom:1px solid var(--line);vertical-align:top}
td.c,th.c{text-align:center}
a{color:var(--accent);font-weight:700;text-decoration:none}
.sp{font-weight:800;font-variant-numeric:tabular-nums;white-space:nowrap} .sp.ok{color:var(--good)} .sp.no{color:var(--bad)} .sp.na{color:var(--ink3)}
.mk{display:inline-flex;width:20px;height:20px;border-radius:50%;align-items:center;justify-content:center;font-weight:800;font-size:12px}
.mk.y{background:var(--good-soft);color:var(--good)} .mk.n{background:var(--bad-soft);color:var(--bad)} .mk.na{color:var(--ink3)}
.mk.later{border:1.5px dashed var(--ink3);width:17px;height:17px}
.hd{display:flex;gap:6px} .hs{display:flex;flex-direction:column;align-items:center;gap:1px} .hs em{font-style:normal;font-size:9.5px;color:var(--ink3);white-space:nowrap}
.muted{color:var(--ink3)} .nx{font-weight:600} .nx.urg{color:var(--bad)}
.chips{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:0 0 10px}
.chip{min-height:52px}
.chip{border-radius:8px;padding:6px 10px;display:flex;flex-direction:column;font-size:12px;color:var(--ink2);border-left:4px solid var(--ink3)}
.chip b{font-size:16px;color:var(--ink)} .chip.hit{background:var(--good-soft);border-color:var(--good)} .chip.miss{background:var(--bad-soft);border-color:var(--bad)} .chip.close{background:var(--yel-soft);border-color:var(--yel)}
.st{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:2px 7px;border-radius:999px;white-space:nowrap}
.st.showed{background:var(--good-soft);color:var(--good)} .st.missed{background:var(--bad-soft);color:var(--bad)} .st.other{background:var(--track);color:var(--ink2)}
.grp{display:flex;flex-direction:column;gap:6px;margin-top:18px}
.grp h3{margin:0;font-size:13px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--ink2);display:flex;justify-content:space-between}
.grp h3 span{font-size:18px;color:var(--ink);letter-spacing:0}
section.part{border-top:2px solid var(--line);padding-top:16px}
.hchart{display:flex;align-items:flex-end;gap:2px;height:52px;border-bottom:1px solid var(--line);padding-top:4px}
.hc{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;min-width:0;height:100%;position:relative}
.hc.gap{margin-left:14px} .hc.gap::before{content:"";position:absolute;left:-9px;top:8px;bottom:0;border-left:1px dashed var(--line)}
.hc b{font-size:11px;font-weight:800;color:var(--ink);font-variant-numeric:tabular-nums;min-height:14px;line-height:14px}
.hc i{display:block;width:70%;max-width:36px;background:var(--ink3);border-radius:4px 4px 0 0}
.hc em{position:absolute;bottom:-18px;font-style:normal;font-size:10.5px;color:var(--ink3)}
.grp .hchart{margin-bottom:18px}
.wrap{overflow-x:auto} .none{color:var(--ink3);font-weight:600}
@media (max-width:560px){.tiles,.chips{grid-template-columns:1fr 1fr}}
"""

def e(s): return html.escape(str(s))
def pct(a, b): return round(100 * a / b) if b else 0

def status(v, target, base):
    if not base: return "none"
    if v >= target: return "hit"
    return "close" if v >= target * CLOSE_PCT / 100 else "miss"

def tile(name, num, base, target, detail):
    v = pct(num, base); st = status(v, target, base)
    return (f'<div class="tile {st}"><div class="k">{e(name)}</div><div class="v">{f"{v}%" if base else "–"}</div>'
            f'<div class="d">{detail} · target {target}%</div></div>'), st

def chip(name, a, b, target):
    st = status(pct(a, b), target, b)
    return f'<div class="chip {st}"><b>{a} of {b}</b><span>{e(name)}</span></div>'

def link(r): return f'<a href="{CLOSE_URL.format(e(r["lead_id"]))}">{e(r["lead"])}</a>'

def speed(m):
    if m is None: return '<span class="sp na">not called</span>'
    t = f"{m} min" if m < 60 else f"{m // 60}h {m % 60}m"
    return f'<span class="sp {"ok" if m <= 15 else "no"}">{t}</span>'

def mark(v):
    return {"y": '<span class="mk y">✓</span>', "n": '<span class="mk n">✗</span>',
            "later": '<span class="mk later"></span>'}.get(v, '<span class="mk na">–</span>')

def hand(st):
    if not st: return '<span class="muted">n/a</span>'
    return '<span class="hd">' + "".join(f'<span class="hs">{mark(st.get(k))}<em>{n}</em></span>' for k, n in STEPS) + "</span>"

def nxt(r): return f'<td class="nx{" urg" if r.get("urgent") else ""}">{e(r["next"])}</td>'

def hour_of(r):
    return datetime.datetime.strptime(r["entered"], "%I:%M%p").hour

def hour_chart(rows, hours):
    """Vertical bars: how many not-called leads came in each hour of the block, with the count on each bar."""
    c = {h: 0 for h in hours}
    for r in rows: c[hour_of(r)] = c.get(hour_of(r), 0) + 1
    top = max(c.values()) or 1; cols = []
    for i, h in enumerate(hours):
        gap = ' gap' if i and h != hours[i - 1] + 1 else ''
        n = c[h]; lab = f"{h % 12 or 12}{'a' if h < 12 else 'p'}"
        cols.append(f'<div class="hc{gap}"><b>{n or ""}</b><i style="height:{round(30 * n / top)}px"></i><em>{lab}</em></div>')
    return f'<div class="hchart">{"".join(cols)}</div>'

def group_tables(L, T, speed_chip=True, hours=range(24)):
    """The where-they-landed bar and one table per group, for one set of leads."""
    G = {k: [r for r in L if r["group"] == k] for k, _ in GROUPS}
    sets = [r for r in G["real"] if r.get("steps") is not None]
    bar = "".join(f'<i class="{k}" style="flex:{len(G[k])}">{len(G[k])}</i>' for k, _ in GROUPS if G[k])
    legend = "".join(f'<span><i style="background:var(--{c})"></i>{n} {len(G[k])}</span>'
                     for (k, n), c in zip(GROUPS, ("good", "short", "accent", "ink3")))
    out = [f'<div class="segbar">{bar}</div><div class="legend">{legend}</div>']
    if G["real"]:
        rows = "".join(f'<tr><td>{link(r)}</td><td>{speed(r["speed"])}</td><td>{e(r["result"])}</td><td>{hand(r.get("steps"))}</td>{nxt(r)}</tr>'
                       for r in G["real"])
        out.append(f'<div class="grp"><h3>Real conversations <span>{len(G["real"])}</span></h3>'
                   f'<p class="lead">{len(sets)} of {len(G["real"])} set to a closer. Handoff: email right after booking, closer note, '
                   f'reminder the day before, morning-of reminder. A dashed circle is a step still ahead.</p>'
                   f'<div class="wrap"><table><tr><th>Lead</th><th>Speed</th><th>Result</th><th>Handoff</th><th>Next step</th></tr>{rows}</table></div></div>')
    if G["short"]:
        rows = "".join(f'<tr><td>{link(r)}</td><td>{speed(r["speed"])}</td><td>{e(r["result"])}</td>{nxt(r)}</tr>' for r in G["short"])
        out.append(f'<div class="grp"><h3>Picked up, no real conversation <span>{len(G["short"])}</span></h3>'
                   f'<div class="wrap"><table><tr><th>Lead</th><th>Speed</th><th>What happened</th><th>Next step</th></tr>{rows}</table></div></div>')
    if G["nopick"]:
        np_ = G["nopick"]
        cnt = lambda k: (sum(r[k] == "y" for r in np_), sum(r[k] != "na" for r in np_))
        chips = (chip("double dialed", *cnt("dd"), T["dd"]) + chip("voicemail (when you could)", *cnt("vm"), T["vm"])
                 + chip("texted", *cnt("tx"), T["text"])
                 + (chip("called in 15 min", sum(r["speed"] <= 15 for r in np_), len(np_), T["speed"]) if speed_chip else ""))
        rows = "".join(f'<tr><td>{link(r)}</td><td>{speed(r["speed"])}</td><td class="c">{mark(r["dd"])}</td><td class="c">{mark(r["vm"])}</td>'
                       f'<td class="c">{mark(r["tx"])}</td>{nxt(r)}</tr>' for r in np_)
        out.append(f'<div class="grp"><h3>Didn\'t pick up <span>{len(np_)}</span></h3><div class="chips">{chips}</div>'
                   f'<div class="wrap"><table><tr><th>Lead</th><th>Speed</th><th class="c">Double dial</th><th class="c">Voicemail</th>'
                   f'<th class="c">Text</th><th>Next step</th></tr>{rows}</table></div>'
                   f'<p class="lead" style="margin-top:6px">– on voicemail or text = the call never reached a mailbox or the number '
                   f"can't take a text, so it doesn't count against you. SOP: Day 1, 3, 5 and 7 (business days), then once a month.</p></div>")
    if G["notcalled"]:
        out.append(f'<div class="grp"><h3>Not called yet <span>{len(G["notcalled"])}</span></h3>'
                   f'<p class="lead">When they came in, by hour (ET). Their names and Close links are in the message under this card.</p>'
                   + hour_chart(G["notcalled"], hours) + "</div>")
    return "".join(out)

def build_html(m):
    T = m["targets"]; d = datetime.date.fromisoformat(m["date"]); day = f"{d.strftime('%a, %b')} {d.day}"
    L = m.get("leads") or []; G = {k: [r for r in L if r["group"] == k] for k, _ in GROUPS}
    tot = len(L); called = [r for r in L if r["speed"] is not None]; picked = len(G["real"]) + len(G["short"])
    sets = [r for r in G["real"] if (r.get("steps") is not None)]
    on_track = sum(1 for r in sets if "n" not in r["steps"].values())
    tiles = [
        tile("Speed to lead", m["within15"], m["new_in_hours"], T["speed"],
             f'{m["within15"]} of {m["new_in_hours"]} in your hours called in 15 min'),
        tile("Pickup rate", picked, len(called), T["pickup"], f"{picked} of {len(called)} you called picked up"),
        tile("Connect rate", len(G["real"]), len(called), T["connect"], f'{len(G["real"])} of {len(called)} real conversations'),
    ]
    # Set to a closer counts every abandoned lead set that day (Sheila, Oct 28, 2026); the small print says how many
    # came from earlier days' leads, which the tables below don't list
    n_set = m["closer_calls"]; n_old = n_set - len(sets)
    if not n_set: sub = "none today"
    elif not n_old: sub = f"all from today's leads · handoff on track for {on_track} of {len(sets)}"
    elif not sets: sub = "all from earlier days' leads" if n_set > 1 else "from an earlier day's leads"
    else: sub = f"{len(sets)} from today's leads, {n_old} from earlier days' leads"
    settile = (f'<div class="tile track"><div class="k">Set to a closer</div><div class="v">{n_set}</div>'
               f'<div class="d">{e(sub)}</div></div>')
    H = m.get("hours") or [10, 18]
    def hr(h, off=0):
        h = (h - off) % 24; return f"{h % 12 or 12}{'am' if h < 12 else 'pm'}"
    hours_et = f"{hr(H[0])} to {hr(H[1])} ET"; hours_pt = f"{hr(H[0], 3)} to {hr(H[1], 3)} PT"
    sec = []
    for part, title, note in ((True, "During your hours", f"{hours_et} ({hours_pt}). Speed to lead counts these leads."),
                              (False, "Outside your hours", "Came in before or after your hours. Call them first thing in your next block.")):
        P = [r for r in L if bool(r.get("in_hours", True)) == part]
        sec.append(f'<section class="part"><h2>{title} <span>{len(P)}</span></h2><p class="lead">{e(note)}</p>'
                   + (group_tables(P, T, speed_chip=part, hours=[h for h in range(24) if (H[0] <= h < H[1]) == part]) if P else '<p class="none">No leads.</p>') + "</section>")
    # the "Follow-up calls due" section was taken off the card (Sheila, Oct 28, 2026: too long); m["followups"] is still computed
    # closer calls that happened on D (sets from earlier days)
    sh = m["show"]; ct = m.get("closer_today") or []
    s7 = f'{sh["showed7"]} of {sh["n7"]} showed, last 7 days' if sh["n7"] else "no closer calls due in the last 7 days"
    if ct:
        lab = {"showed": "showed", "missed": "no show", "unlogged": "not logged", "pending": "rescheduled"}
        rows = "".join(f'<tr><td>{link(r)}</td><td>{e(datetime.date.fromisoformat(r["set"]).strftime("%b ") + str(int(r["set"][8:])))}</td>'
                       f'<td>{e(r["closer"])}</td><td><span class="st {r["status"] if r["status"] in ("showed", "missed") else "other"}">{lab.get(r["status"], r["status"])}</span></td>'
                       f'<td>{hand(r["steps"])}</td></tr>' for r in ct)
        body = f'<div class="wrap"><table><tr><th>Lead</th><th>Set on</th><th>Closer</th><th>Showed?</th><th>Handoff</th></tr>{rows}</table></div>'
    else:
        body = f'<p class="none">No closer calls from abandoned leads were on {e(day)}.</p>'
    sec.append(f'<section><h2>Closer calls that happened {e(day)} <span class="sm">{e(s7)}</span></h2>'
               f'<p class="lead">Leads you set on earlier days. Separate from the {tot} above.</p>{body}</section>')
    cl = m.get("closes") or []
    meta = (f'{tot} abandoned Typeform {"lead" if tot == 1 else "leads"} · {len(called)} called · {picked} picked up · {n_set} set to a closer'
            f' · {m["sets_to_date"]} {"set" if m["sets_to_date"] == 1 else "sets"} and {len(cl)} {"close" if len(cl) == 1 else "closes"} since Oct 21')
    return f"""<div class="card" id="card3">
<header><div class="eyebrow">Abandoned Typeform test · separate from Welcome Series</div>
<h1>Bali's leads: {e(day)}</h1><div class="meta">{e(meta)}</div></header>
<div class="tiles">{"".join(t for t, _ in tiles)}{settile}</div>
{"".join(sec)}
</div>"""

def slack_links(m):
    """The day's leads as Slack links, one line per group, for the message under the PNG."""
    d = datetime.date.fromisoformat(m["date"]); L = m.get("leads") or []; out = [f"Close links, {d.strftime('%a, %b')} {d.day}:"]
    for k, n in GROUPS:
        rs = [r for r in L if r["group"] == k]
        if rs: out.append(f"{n}: " + ", ".join(f"<{CLOSE_URL.format(r['lead_id'])}|{r['lead']}>" for r in rs))
    fu = [r for r in m["followups"]["rows"] if r.get("lead_id")]
    if fu: out.append("Follow-ups due: " + ", ".join(f"<{CLOSE_URL.format(r['lead_id'])}|{r['lead']}>" for r in fu))
    return "\n".join(out)

def build(m, out_dir):
    font = (HERE / "manrope.b64").read_text().strip()
    od = pathlib.Path(out_dir).resolve(); od.mkdir(parents=True, exist_ok=True)
    page = od / f"abandoned-{m['date']}.html"
    page.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                    f"<title>Bali Abandoned Typeform</title><style>{CSS.replace('__FONT__', font)}</style></head><body>"
                    + build_html(m) + "</body></html>")
    (od / f"abandoned-links-{m['date']}.txt").write_text(slack_links(m) + "\n")
    png = od / f"scorecard-{m['date']}-3-abandoned.png"
    asyncio.run(_shot(str(page), str(png)))
    return str(page), str(png)

async def _shot(src, png):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        pg = await b.new_page(viewport={"width": 800, "height": 900}, device_scale_factor=2, color_scheme="light")
        await pg.goto("file://" + src); await pg.wait_for_timeout(400)
        await pg.locator("#card3").screenshot(path=png)
        await b.close()

if __name__ == "__main__":
    m = json.load(open(sys.argv[1]))
    page, png = build(m, sys.argv[2])
    print(json.dumps({"html": page, "png": png}))

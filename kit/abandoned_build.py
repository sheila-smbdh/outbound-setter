"""Build Bali's Abandoned Typeform card (a third image, separate from the Welcome Series cards) from the metrics JSON
written by run_abandoned(D) in bali_abandoned.py. Layout approved by Sheila on Oct 21, 2026
(mockups/abandoned-typeform/): the running sets and closes on top, then one section in three groups:
1. First call, 2. Closers, 3. Follow-up calls on time (with every lead due that day listed). No wins or fixes.
usage: python3 abandoned_build.py metrics.json out_dir
writes out_dir/abandoned-YYYY-MM-DD.html and out_dir/scorecard-YYYY-MM-DD-3-abandoned.png.
Chromium: set CHROMIUM_PATH to a local Chromium if Playwright's own browser isn't installed.
"""
import json, sys, os, re, asyncio, pathlib, datetime, html

HERE = pathlib.Path(__file__).parent
CLOSE_PCT = 75   # yellow ('almost') at 75% of the target or more, same as the Welcome Series cover
PILL = dict(hit="Hit", close="Almost", miss="Missed", none="None today")
STEP_NAMES = [("email", "Handoff email right after booking"), ("note", "Closer note attached"),
              ("day_before", "Reminder the day before"), ("morning_of", "Morning-of reminder (no reply)")]
CSS = """
#card3 .eyebrow{color:var(--older)}
.tot2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tot2 .callout{display:flex;align-items:baseline;gap:12px}
.tot2 .n{font-size:40px;font-weight:800;color:var(--good);line-height:1;font-variant-numeric:tabular-nums}
.tot2 .t{font-size:14px;font-weight:600;color:var(--ink2)}
.pri .grp > .kpis{grid-template-columns:repeat(3,minmax(0,1fr))}
.grp{display:flex;flex-direction:column;gap:8px}
.grp + .grp{margin-top:18px}
.grp h3{margin:0;font-size:13px;font-weight:800;color:var(--ink);display:flex;gap:8px;align-items:baseline}
.grp h3 span{font-size:12.5px;font-weight:600;color:var(--ink3)}
.closers{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.6fr);gap:8px}
.fu{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2.2fr);gap:8px;align-items:start}
.due{width:100%;border-collapse:collapse;font-size:13px}
.due th{font-size:11px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--ink3);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}
.due td{padding:6px;border-bottom:1px solid var(--line);vertical-align:top}
.due td:first-child{font-weight:700;white-space:nowrap}
.due td.st{white-space:nowrap;font-weight:800}
.due .ok{color:var(--good)} .due .no{color:var(--bad)}
.due tr.miss td{background:var(--bad-soft)}
.due td.r{color:var(--ink2)}
.due td.none{color:var(--ink3);font-weight:600}
@media (max-width:560px){.tot2,.closers,.fu,.pri .grp > .kpis{grid-template-columns:1fr}}
"""

def pct(a, b): return round(100 * a / b) if b else 0
def e(s): return html.escape(str(s))

def status(value, target, base):
    if not base: return "none"
    if value >= target: return "hit"
    return "close" if value >= target * CLOSE_PCT / 100 else "miss"

def tile(key, name, num, base, target, detail, note="", extra="", cls=""):
    """A KPI tile in the Welcome Series cover style (cover.html tile())."""
    v = pct(num, base); st = status(v, target, base)
    val = f"{v}%" if base else "–"
    return (f'<div class="kpi k-{key} {st} {cls}"><div class="nm">{e(name)}</div><div class="v">{val}</div>'
            + (f'<div class="nt">{e(note)}</div>' if note else "") + f'<div class="of">{detail}</div>' + extra
            + f'<div class="tbar"><i style="width:{min(v, 100) if base else 0}%"></i><b style="left:calc({target}% - 1px)"></b></div>'
            + f'<div class="st"><span>Target {target}%</span><span class="pill">{PILL[st]}</span></div></div>'), st

def build_html(m):
    T = m["targets"]; d = datetime.date.fromisoformat(m["date"])
    nov = m["no_answers"] - m["vm_possible"]; notx = m["no_answers"] - m["text_possible"]
    first = [
        tile("speed", "Speed to lead", m["within15"], m["new_in_hours"], T["speed"],
             f'{m["within15"]} of {m["new_in_hours"]} new abandoned leads in 15 min', "From the #partial-submit ping, 9am to 9pm ET."),
        tile("vm", "Voicemail", m["vm_left"], m["vm_possible"], T["vm"],
             f'{m["vm_left"]} of {m["vm_possible"]} no-answers who let you leave one'
             + (f" ({nov} hung up or didn't go through, not counted)" if nov else "")),
        tile("text", "Text", m["text_sent"], m["text_possible"], T["text"],
             f'{m["text_sent"]} of {m["text_possible"]} no-answers got one'
             + (f" ({notx} blocked or invalid {'number' if notx == 1 else 'numbers'}, not counted)" if notx else "")),
        tile("dd", "Double dial", m["dd_done"], m["dd_noans"], T["dd"], f'{m["dd_done"]} of {m["dd_noans"]} no-answers redialed'),
        tile("pickup", "Pickup rate", m["pickups"], m["people_dialed"], T["pickup"], f'{m["pickups"]} of {m["people_dialed"]} people picked up'),
        tile("connect", "Connect rate", m["real_conversations"], m["people_dialed"], T["connect"],
             f'{m["real_conversations"]} of {m["people_dialed"]} people had a real conversation',
             "Set to self counts only when a meeting is actually booked."),
    ]
    sp = m["closer_split"]; parts = []
    if sp["day1"]: parts.append(f'<b>{len(sp["day1"])} on Day 1:</b> ' + e(", ".join(sp["day1"])))
    if sp["followup"]: parts.append(f'<b>{len(sp["followup"])} on a follow-up day:</b> ' + e(", ".join(f"{n} ({s})" for n, s in sp["followup"])))
    setdet = "<br>".join(parts) if parts else "No closer calls booked"
    settile = (f'<div class="kpi track"><div class="nm">Set to a closer</div><div class="v">{m["closer_calls"]}</div>'
               f'<div class="of">{setdet}</div><div class="st"><span>No target</span><span class="pill">Tracking</span></div></div>')
    sh = m["show"]; miss = sh.get("missed7") or []
    def step_row(nm, s):
        cls = ("ok" if s["done"] == s["due"] else "no") if s["due"] else "na"
        val = f'{s["done"]} of {s["due"]}' if s["due"] else "none due yet"
        return f'<div class="r"><span>{nm}</span><span class="{cls}">{val}</span></div>'
    steps = "".join(step_row(nm, sh["steps"][k]) for k, nm in STEP_NAMES)
    extra = ((f'<div class="all"><div class="al">All abandoned leads set since Oct 21</div>'
              f'<div class="av">{pct(sh["showed_all"], sh["n_all"])}%<span>{sh["showed_all"]} of {sh["n_all"]} showed</span></div></div>'
              if sh["n_all"] else "")
             + f'<div class="steps"><div class="sh">Handoff steps, last 7 days</div>{steps}</div>')
    showdet = (f'{sh["showed7"]} of {sh["n7"]} closer calls showed' + (f" ({e(', '.join(miss))} didn't)" if miss else "")
               if sh["n7"] else "No closer calls were due in the last 7 days")
    show = tile("show", "Show rate", sh["showed7"], sh["n7"], T["show"], showdet,
                "Last 7 days. A rescheduled call counts on its new date.", extra)
    fu = m["followups"]
    futile = tile("fu", "Follow-up calls on time", fu["done"], fu["due"], T["followup"], f'{fu["done"]} of {fu["due"]} calls due today made')
    rows = "".join(
        f'<tr class="{"" if r["called"] else "miss"}"><td>{e(r["lead"])}</td><td>{e(r["step"])}</td>'
        f'<td class="st {"ok" if r["called"] else "no"}">{"Yes" if r["called"] else "No"}</td><td class="r">{e(r["result"])}</td></tr>'
        for r in fu["rows"]) or '<tr><td class="none" colspan="4">No follow-up calls were due today.</td></tr>'
    scored = [s for _, s in first + [show, futile] if s != "none"]
    hit = scored.count("hit"); near = scored.count("close")
    meta = (((f'You hit {hit} of {len(scored)} targets' + (f", {near} almost" if near else "")) if scored else "No targets to score yet")
            + f' · {m["dials"]} dials to {m["people_dialed"]} abandoned {"lead" if m["people_dialed"] == 1 else "leads"}'
            + f' · {m["new_leads"]} new in #partial-submit')
    cl = m["closes"]
    closes_t = ("close from abandoned leads so far" if len(cl) == 1 else "closes from abandoned leads so far") + (": " + ", ".join(r["lead"] for r in cl) if cl else "")
    sets_t = ("set to a closer" if m["sets_to_date"] == 1 else "sets to a closer") + " from abandoned leads since Oct 21"
    return f"""<style>{CSS}</style>
<div class="card" id="card3">
  <header>
    <div class="eyebrow">Abandoned Typeform test · separate from Welcome Series</div>
    <h1>Bali's Abandoned Typeform day: {d.strftime('%A, %b')} {d.day}</h1>
    <div class="meta">{e(meta)}</div>
  </header>
  <div class="tot2">
    <div class="callout win"><div class="n">{m["sets_to_date"]}</div><div class="t">{e(sets_t)}</div></div>
    <div class="callout win"><div class="n">{len(cl)}</div><div class="t">{e(closes_t)}</div></div>
  </div>
  <section class="pri">
    <h2>Your numbers on this list</h2>
    <p class="lead">Green: you hit the target. Yellow: almost there (75% of the target or more). Red: you missed it. Blue: a number we track, with no target. The black line on each bar is the target.</p>
    <div class="grp">
      <h3>1. First call <span>new abandoned leads, the moment the #partial-submit ping lands</span></h3>
      <div class="kpis">{"".join(t for t, _ in first)}</div>
    </div>
    <div class="grp">
      <h3>2. Closers <span>sets, and getting them to show</span></h3>
      <div class="closers">{settile}{show[0]}</div>
    </div>
    <div class="grp">
      <h3>3. Follow-up calls on time <span>Day 3, 5, 7 and monthly calls due today</span></h3>
      <div class="fu">{futile[0]}
        <table class="due"><tr><th>Lead</th><th>Due</th><th>Called</th><th>What happened</th></tr>{rows}</table>
      </div>
    </div>
  </section>
</div>"""

def styles(path):
    return "".join(re.findall(r"<style>.*?</style>", path.read_text(), re.S))

def build(m, out_dir):
    font = (HERE / "manrope.b64").read_text().strip()
    css = (styles(HERE / "template.html") + styles(HERE / "cover.html")).replace("__FONT__", font)
    body = css + build_html(m)
    od = pathlib.Path(out_dir).resolve(); od.mkdir(parents=True, exist_ok=True)
    page = od / f"abandoned-{m['date']}.html"
    page.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                    "<title>Bali Abandoned Typeform</title><style>html,body{margin:0}</style></head><body>" + body + "</body></html>")
    png = od / f"scorecard-{m['date']}-3-abandoned.png"
    asyncio.run(_shot(str(page), str(png)))
    return str(page), str(png)

async def _shot(src, png):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        pg = await b.new_page(viewport={"width": 780, "height": 900}, device_scale_factor=2, color_scheme="light")
        await pg.goto("file://" + src); await pg.wait_for_timeout(400)
        await pg.locator("#card3").screenshot(path=png)
        await b.close()

if __name__ == "__main__":
    m = json.load(open(sys.argv[1]))
    page, png = build(m, sys.argv[2])
    print(json.dumps({"html": page, "png": png}))

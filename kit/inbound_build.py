# Render an inbound setter scorecard (Sheila, Nov 20, 2026; layout: mockups/inbound-scorecards v7).
# usage, from kit/:  python3 inbound_build.py ../d/<D>/inbound-<key>.json ../out
# Writes inbound-<key>-<D>.html and inbound-<key>-<D>.png. Styles come from template.html, cover.html and inbound.css.
import sys, os, json, re, html, asyncio, pathlib, datetime as dt

HERE = pathlib.Path(__file__).parent
E = html.escape


def styles():
    css = "".join(re.findall(r"<style>.*?</style>", (HERE / "template.html").read_text(), re.S) +
                  re.findall(r"<style>.*?</style>", (HERE / "cover.html").read_text(), re.S))
    return css.replace("__FONT__", (HERE / "manrope.b64").read_text().strip()) + "<style>" + (HERE / "inbound.css").read_text() + "</style>"


def _day(d): return dt.date.fromisoformat(d).strftime("%A, %b ") + str(dt.date.fromisoformat(d).day)


def _short(d): return dt.date.fromisoformat(d).strftime("%b ") + str(dt.date.fromisoformat(d).day)


def verdict_box(r):
    t = r.get("today") or {}
    v = t.get("verdict")
    why = []
    if t.get("idle"): why.append("no intro calls")
    if t.get("steps_due") and t["steps_done"] < t["steps_due"]:
        n = t["steps_due"] - t["steps_done"]; why.append(f"{n} handoff step{'s' if n != 1 else ''} missed")
    if t.get("price"):
        n = len(t["price"]); why.append(f"price came up on {n} call{'s' if n != 1 else ''}")
    if t.get("booking"):
        n = len(t["booking"]); why.append(f"{n} direct-to-closer booking{'s' if n != 1 else ''}")
    if v == "yes": head, cls = "Compliant day: all 3 KPIs hit", "verdict met"
    elif v == "no": head, cls = "Not a compliant day: " + ", ".join(why), "verdict"
    else:
        miss = [k for k, c in (("price", t.get("price_checked")), ("booking", t.get("booking_checked"))) if not c]
        head, cls = "Not checked yet: the " + " and ".join(miss) + " check" + ("s" if len(miss) > 1 else "") + " didn't come in", "verdict unc"
    dots = "".join(f'<span class="{dict(yes="y", no="n", unchecked="u").get(d["verdict"], "")}">{d["dow"]}</span>' for d in r["days"])
    # the rest of the week, not reached yet
    seen = {d["dow"] for d in r["days"]}
    dots += "".join(f"<span>{w}</span>" for w in ("Mon", "Tue", "Wed", "Thu", "Fri") if w not in seen)
    return f'<div class="{cls}"><div class="dt">{E(head)}</div><div class="days">This week {dots}</div></div>'


def cell(c, txt_ok="✓"):
    if c in ("ok", "ok_prev"): return f'<td class="ok">{txt_ok}</td>'
    if c == "miss": return '<td class="no">✗</td>'
    if c == "miss_prev": return '<td class="na">missed</td>'
    if c == "unchecked": return '<td class="nd">not checked</td>'
    return '<td class="na"></td>'


def table(r):
    rows = r["rows"]; out = []
    out.append('<table class="tbl"><tr><th rowspan="2" class="l">Lead</th><th rowspan="2" class="l">Closer call</th>'
               '<th colspan="4" class="kg">1. Handoff steps</th><th class="kg">2. Price</th><th class="kg">3. Booking</th></tr>'
               '<tr><th>Email to closer</th><th>Closer note</th><th>Day-before text</th><th>Day-of text</th><th>No price said</th><th>Team link</th></tr>')
    for grp, label in (("today", "Set today"), ("earlier", "Set earlier, reminder due today")):
        g = [x for x in rows if x["group"] == grp]
        if not g: continue
        out.append(f'<tr class="grp"><td colspan="8">{label}</td></tr>')
        # one gray "not due yet" block over runs of rows whose two reminders are both still ahead (Sheila, Nov 20)
        both = [x["cells"]["day_before"] == "later" and x["cells"]["morning_of"] == "later" for x in g]
        i = 0
        while i < len(g):
            x = g[i]; c = x["cells"]
            tds = f'<td>{E(x["lead"])}</td><td class="r">{E(x["call"])}</td>' + cell(c["email"]) + cell(c["note"])
            if both[i]:
                j = i
                if i == 0 or not both[i - 1]:
                    while j + 1 < len(g) and both[j + 1]: j += 1
                    tds += f'<td class="nd" colspan="2" rowspan="{j - i + 1}">not due yet</td>'
            else:
                for k in ("day_before", "morning_of"):
                    tds += '<td class="nd">not due yet</td>' if c[k] == "later" else cell(c[k])
            if grp == "today":
                tds += (f'<td class="no">✗ {E(x.get("price_time") or "")}</td>' if x["price"] == "miss" else cell(x["price"]))
                tds += cell(x["booking"])
            else:
                tds += '<td class="na"></td><td class="na"></td>'
            out.append(f"<tr>{tds}</tr>"); i += 1
    if not rows:
        out.append('<tr><td colspan="8" class="r">No inbound sets today and no reminders due.</td></tr>')
    t = r.get("today") or {}
    due, done = t.get("steps_due", 0), t.get("steps_done", 0)
    hcls = "ok" if done == due else "no"
    htxt = f"{round(100 * done / due)}% · {done} of {due} steps" if due else "No steps due"
    p, b = r["price"], r["booking"]
    ptd = (f'<td class="no">{len(p["hits"])} call{"s" if len(p["hits"]) != 1 else ""}</td>' if p["hits"] else
           ('<td class="ok">0 calls</td>' if p["checked"] else '<td class="nd">not checked</td>'))
    btd = (f'<td class="no">{len(b["hits"])} direct</td>' if b["hits"] else
           ('<td class="ok">0 direct</td>' if b["checked"] else '<td class="nd">not checked</td>'))
    out.append(f'<tr class="tot"><td class="lab" colspan="2">Total</td><td colspan="4" class="{hcls}">{htxt}</td>{ptd}{btd}</tr>')
    out.append('<tr class="tgt"><td colspan="2"></td><td colspan="4">Target 100%</td><td>Target 0</td><td>Target 0</td></tr></table>')
    extra = []
    for h in r.get("price_other") or []:
        extra.append(f'<li>Price on a call with {E(h.get("lead") or "a lead")}' + (f' at {E(h["time"])}' if h.get("time") else "") +
                     (f': <i>"{E(h["quote"])}"</i>' if h.get("quote") else "") + "</li>")
    for h in r.get("booking_other") or []:
        # lead name, closer and call time, so the booking can be traced (Sheila, Nov 23, 2026)
        extra.append(f'<li>Direct booking: <b>{E(h.get("lead") or "a lead")}</b>' + (f' with {E(h["closer"])}' if h.get("closer") else "") +
                     (f', call {E(h["time"])}' if h.get("time") else "") +
                     (f' (not a set: {E(h["not_a_set"])})' if h.get("not_a_set") else "") + "</li>")
    if extra: out.append('<ul class="xtra">' + "".join(extra) + "</ul>")
    return "".join(out)


def card(r):
    name = r["name"]; draw = r.get("draw")
    meta = f'{r["calls_taken"]} intro call{"s" if r["calls_taken"] != 1 else ""} taken · {r["sets_today"]} inbound set{"s" if r["sets_today"] != 1 else ""} to a closer' + (f' · {r["span"]}' if r.get("span") else "")
    tiles = (f'<div class="t3"><div class="n">{r["sets_today"]}</div><div class="t"><b>inbound</b> sets to a closer today</div></div>'
             f'<div class="t3"><div class="n">{r["sets_week"]}</div><div class="t"><b>inbound</b> sets to a closer this week</div></div>')
    ob = r.get("outbound")
    if ob:
        tiles += (f'<div class="t3"><div class="n">{ob["closes"]}<span> / {ob["sets"]}</span></div><div class="t"><b>{ob["closes"]} closed</b> of the '
                  f'<b>{ob["sets"]} outbound sets</b> you\'ve made since you started outbound on {_short(ob["since"])}</div></div>')
    head = "Every set, every step: all of it, every day" + (", for the draw" if draw else "")
    todo = ('<ol class="todo"><li><b>Handoff steps, 100%:</b> email the closer and attach the closer note on every set, text the day before, '
            "and text the morning of the call if they haven't replied. All done by the end of your workday.</li>"
            "<li><b>Never mention price</b> on a call.</li><li><b>Book through the team link</b>, never straight onto one closer's calendar.</li></ol>")
    return (f'<div class="card inb" id="card0"><header><div class="eyebrow">Inbound Setter</div>'
            f'<h1>{E(name)}\'s Day: {_day(r["date"])}</h1><div class="meta">{E(meta)}</div></header>'
            f'<div class="top3{"" if ob else " two"}">{tiles}</div>{verdict_box(r)}'
            f'<section><h2>{head}</h2>{todo}{table(r)}</section></div>')


def build(path, out_dir):
    r = json.load(open(path))
    od = pathlib.Path(out_dir).resolve(); od.mkdir(parents=True, exist_ok=True)
    stem = f'inbound-{r["key"]}-{r["date"]}'
    page = od / f"{stem}.html"
    page.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                    f'<title>{E(r["name"])} Inbound Scorecard</title><style>html,body{{margin:0}}</style></head><body>'
                    + styles() + card(r) + "</body></html>")
    png = od / f"{stem}.png"
    asyncio.run(_shot(str(page), str(png)))
    return str(page), str(png)


async def _shot(src, png):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try: b = await p.chromium.launch()
        except Exception: b = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
        pg = await b.new_page(viewport={"width": 780, "height": 900}, device_scale_factor=2, color_scheme="light")
        await pg.goto("file://" + src); await pg.wait_for_timeout(400)
        await pg.locator("#card0").screenshot(path=png)
        await b.close()


if __name__ == "__main__":
    print(*build(sys.argv[1], sys.argv[2]))

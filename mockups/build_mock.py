"""Mockup of the per-lead abandoned Typeform card. Sample data only; not wired to Close yet."""
import json, pathlib, sys
H = pathlib.Path(__file__).parent
CLOSE = 'https://app.close.com/lead/'
Y, N, NA = 'y', 'n', '-'
D = {
 'date': 'Wed, Oct 21',
 'talked': [  # real conversations
  dict(n='Alex R.', s=3, res='Set to Adam Larkins, Thu 2pm', hand=[Y, Y, NA, NA], nxt='Day-before reminder today (Wed)'),
  dict(n='Priya S.', s=6, res='Set to Nick Vaughan, Fri 11am', hand=[N, Y, NA, NA], nxt='Send the handoff email now (missed)'),
  dict(n='Marcus T.', s=22, res='Set to Owen Henderson, today 4pm', hand=[Y, Y, NA, NA], nxt='Morning-of text if no reply'),
  dict(n='Dana W.', s=9, res='Call back later', hand=None, nxt='Call back Thu 10am (his ask)'),
  dict(n='Leo M.', s=41, res='Call back later', hand=None, nxt='Call back Mon, send materials'),
  dict(n='Rita K.', s=12, res='Disqualified (low liquidity)', hand=None, nxt='None, nurture'),
 ],
 'short': [  # picked up, no real conversation
  dict(n='Sam P.', s=5, res='Hung up after 20 sec', nxt='Dial again today, then text'),
  dict(n='Jordan F.', s=14, res='Screener, got through, 40 sec', nxt='Dial again tomorrow morning'),
 ],
 'nopick': [  # [double dial, voicemail, text]; '-' = no chance to leave one
  dict(n='Chris B.', s=2, dd=Y, vm=Y, tx=Y, nxt='Try 2 today, try 3 tomorrow'),
  dict(n='Nina O.', s=8, dd=Y, vm=Y, tx=Y, nxt='Try 2 today, try 3 tomorrow'),
  dict(n='Tom G.', s=11, dd=N, vm=Y, tx=Y, nxt='Try 2 today (double dial missed)'),
  dict(n='Ivy L.', s=27, dd=Y, vm=NA, tx=Y, nxt='Try 2 today, try 3 tomorrow'),
  dict(n='Ben H.', s=64, dd=Y, vm=N, tx=N, nxt='Text now, try 2 today'),
  dict(n='Omar Z.', s=95, dd=Y, vm=Y, tx=Y, nxt='Try 2 today, try 3 tomorrow'),
 ],
 'notcalled': [dict(n='Kate V.', s=None, nxt='Call first thing (signed up 8:52pm)')],
 'shows': [
  dict(n='Ravi D.', set='Oct 19', closer='Julien Breteau', st='showed', hand=[Y, Y, Y, NA]),
  dict(n='Grace N.', set='Oct 20', closer='Kevin Manuel', st='showed', hand=[Y, Y, NA, Y]),
  dict(n='Paul E.', set='Oct 16', closer='Harry Whyte', st='no show', hand=[Y, Y, N, N]),
  dict(n='Mia C.', set='Oct 20', closer='Owen Henderson', st='not logged', hand=[Y, N, NA, Y]),
 ],
 'show7': (8, 10),
}

def link(r): return f'<a href="{CLOSE}">{r["n"]}</a>'
def speed(s):
    if s is None: return '<span class="sp na">not called</span>'
    c = 'ok' if s <= 15 else 'no'
    t = f'{s} min' if s < 60 else f'{s//60}h {s%60}m'
    return f'<span class="sp {c}">{t}</span>'
def mark(v, label=''):
    cls = {Y: 'ok', N: 'no', NA: 'na'}[v]; sym = {Y: '✓', N: '✗', NA: '–'}[v]
    return f'<span class="mk {cls}" title="{label}">{sym}</span>'
STEPS = ['Email', 'Note', 'Day before', 'Morning of']
def hand(h):
    if not h: return '<span class="muted">n/a</span>'
    return '<span class="hd">' + ''.join(f'<span class="hs">{mark(v)}<em>{s}</em></span>' for v, s in zip(h, STEPS)) + '</span>'
def cnt(rows, k): 
    due = [r for r in rows if r[k] != NA]; return sum(r[k] == Y for r in due), len(due)
def chip(name, a, b, tgt=85):
    p = round(100 * a / b) if b else 0
    cls = 'ok' if p >= tgt else 'mid' if p >= .75 * tgt else 'no'
    return f'<div class="chip {cls}"><b>{a} of {b}</b><span>{name}</span></div>'

t, s, np_, nc = D['talked'], D['short'], D['nopick'], D['notcalled']
allr = t + s + np_ + nc; tot = len(allr)
called = [r for r in allr if r['s'] is not None]
w15 = sum(1 for r in called if r['s'] <= 15)
picked = len(t) + len(s); sets = [r for r in t if r['res'].startswith('Set')]
full = sum(1 for r in sets if all(v != N for v in r['hand']))
seg = lambda k, n, lab: f'<i class="{k}" style="flex:{n}"><b>{n}</b></i>' if n else ''

html = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Abandoned Typeform Card</title><style>
:root{{--bg:#f1f0ec;--card:#fbfbf9;--ink:#15171a;--ink2:#55585e;--ink3:#86888d;--line:#e2e1db;--accent:#2256b8;--good:#1a7f37;--good-soft:#e2f2e6;--bad:#c23a32;--bad-soft:#f8e3e1;--yel:#e3a800;--yel-ink:#946c00;--yel-soft:#f8efcf;--track:#e9e8e3;--f:"Manrope",system-ui,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#141517;--card:#1c1d20;--ink:#f2f2f0;--ink2:#b4b5b8;--ink3:#8a8b8f;--line:#2d2e32;--accent:#6f9cf0;--good:#4cc26a;--good-soft:#17301f;--bad:#f07068;--bad-soft:#3a1d1b;--yel-ink:#f2c94c;--yel-soft:#3a3115;--track:#2a2b2f;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141517;--card:#1c1d20;--ink:#f2f2f0;--ink2:#b4b5b8;--ink3:#8a8b8f;--line:#2d2e32;--accent:#6f9cf0;--good:#4cc26a;--good-soft:#17301f;--bad:#f07068;--bad-soft:#3a1d1b;--yel-ink:#f2c94c;--yel-soft:#3a3115;--track:#2a2b2f;color-scheme:dark}}
@font-face{{font-family:"Manrope";src:url(data:font/woff2;base64,__FONT__) format("woff2");font-weight:200 800}}
body{{background:var(--bg);color:var(--ink);font-family:var(--f);font-size:14px;line-height:1.4;margin:0;padding:20px 16px}}
.card{{max-width:760px;margin:0 auto;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px clamp(16px,4vw,28px);display:flex;flex-direction:column;gap:22px}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3)}} .eyebrow b{{color:var(--bad)}}
h1{{font-size:28px;margin:4px 0 4px;letter-spacing:-.02em}} .meta{{color:var(--ink2)}}
h2{{font-size:13px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:var(--accent);margin:0 0 4px;display:flex;justify-content:space-between;align-items:baseline}}
h2 span{{font-size:22px;letter-spacing:0;color:var(--ink);text-transform:none}}
h2 span.sm{{font-size:14px;font-weight:700;color:var(--ink2)}}
.lead{{color:var(--ink2);margin:0 0 10px;font-size:13px}}
.tiles{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}}
.tile{{border:1px solid var(--line);border-left:6px solid var(--ink3);border-radius:10px;padding:10px}}
.tile.ok{{border-left-color:var(--good);background:var(--good-soft)}} .tile.no{{border-left-color:var(--bad);background:var(--bad-soft)}} .tile.tr{{border-left-color:var(--accent)}}
.tile .k{{font-size:11px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--ink2)}}
.tile .v{{font-size:28px;font-weight:800;line-height:1.1}} .tile.ok .v{{color:var(--good)}} .tile.no .v{{color:var(--bad)}} .tile.tr .v{{color:var(--accent)}}
.tile .d{{font-size:12px;color:var(--ink2)}}
.segbar{{display:flex;height:28px;border-radius:8px;overflow:hidden;gap:2px}}
.segbar i{{display:flex;align-items:center;padding-left:8px;font-style:normal;color:#fff;font-size:13px}}
.segbar .t{{background:var(--good)}} .segbar .s{{background:#6aa77b}} .segbar .p{{background:var(--accent)}} .segbar .c{{background:var(--ink3)}}
.legend{{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:12.5px;color:var(--ink2);margin-top:6px}}
.legend i{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{font-size:10.5px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;color:var(--ink3);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}}
td{{padding:7px 6px;border-bottom:1px solid var(--line);vertical-align:top}}
td.c,th.c{{text-align:center}}
a{{color:var(--accent);font-weight:700;text-decoration:none}}
.sp{{font-weight:800;font-variant-numeric:tabular-nums;white-space:nowrap}} .sp.ok{{color:var(--good)}} .sp.no{{color:var(--bad)}} .sp.na{{color:var(--ink3)}}
.mk{{display:inline-flex;width:20px;height:20px;border-radius:50%;align-items:center;justify-content:center;font-weight:800;font-size:12px}}
.mk.ok{{background:var(--good-soft);color:var(--good)}} .mk.no{{background:var(--bad-soft);color:var(--bad)}} .mk.na{{color:var(--ink3)}}
.hd{{display:flex;gap:6px}} .hs{{display:flex;flex-direction:column;align-items:center;gap:1px}} .hs em{{font-style:normal;font-size:9.5px;color:var(--ink3);white-space:nowrap}}
.muted{{color:var(--ink3)}} .nx{{font-weight:600}} .nx.urg{{color:var(--bad)}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 10px}}
.chip{{border-radius:8px;padding:6px 10px;display:flex;flex-direction:column;font-size:12px;color:var(--ink2);border-left:4px solid}}
.chip b{{font-size:16px;color:var(--ink)}} .chip.ok{{background:var(--good-soft);border-color:var(--good)}} .chip.no{{background:var(--bad-soft);border-color:var(--bad)}} .chip.mid{{background:var(--yel-soft);border-color:var(--yel)}}
.st{{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;padding:2px 7px;border-radius:999px;white-space:nowrap}}
.st.showed{{background:var(--good-soft);color:var(--good)}} .st.no{{background:var(--bad-soft);color:var(--bad)}} .st.nl{{background:var(--track);color:var(--ink2)}}
.wrap{{overflow-x:auto}}
@media (max-width:560px){{.tiles{{grid-template-columns:1fr 1fr}}}}
</style></head><body><div class="card">
<header><div class="eyebrow">Welcome Series · abandoned Typeform · <b>mockup, sample data</b></div>
<h1>Bali's leads: {D['date']}</h1>
<div class="meta">{tot} abandoned Typeform leads · {len(called)} called · {picked} picked up · {len(sets)} set to a closer</div></header>

<div class="tiles">
<div class="tile {'ok' if w15/tot>=.6 else 'no'}"><div class="k">Speed to lead</div><div class="v">{round(100*w15/tot)}%</div><div class="d">{w15} of {tot} called in 15 min · target 60%</div></div>
<div class="tile {'ok' if picked/tot>=.25 else 'no'}"><div class="k">Pickup rate</div><div class="v">{round(100*picked/tot)}%</div><div class="d">{picked} of {tot} picked up · target 25%</div></div>
<div class="tile {'ok' if len(t)/tot>=.10 else 'no'}"><div class="k">Connect rate</div><div class="v">{round(100*len(t)/tot)}%</div><div class="d">{len(t)} of {tot} real conversations · target 10%</div></div>
<div class="tile tr"><div class="k">Set to a closer</div><div class="v">{len(sets)}</div><div class="d">handoff on track for {full} of {len(sets)}</div></div>
</div>

<section><h2>Where all {tot} landed</h2>
<div class="segbar">{seg('t',len(t),'')}{seg('s',len(s),'')}{seg('p',len(np_),'')}{seg('c',len(nc),'')}</div>
<div class="legend"><span><i style="background:var(--good)"></i>Real conversation {len(t)}</span><span><i style="background:#6aa77b"></i>Picked up, no real conversation {len(s)}</span><span><i style="background:var(--accent)"></i>Didn't pick up {len(np_)}</span><span><i style="background:var(--ink3)"></i>Not called yet {len(nc)}</span></div></section>

<section><h2>Real conversations <span>{len(t)}</span></h2>
<p class="lead">{len(sets)} of {len(t)} set to a closer. Handoff: email right after booking, closer note, reminder the day before, morning-of reminder.</p>
<div class="wrap"><table><tr><th>Lead</th><th>Speed</th><th>Result</th><th>Handoff</th><th>Next step</th></tr>
{''.join(f"<tr><td>{link(r)}</td><td>{speed(r['s'])}</td><td>{r['res']}</td><td>{hand(r['hand'])}</td><td class='nx{' urg' if 'missed' in r['nxt'] else ''}'>{r['nxt']}</td></tr>" for r in t)}
</table></div></section>

<section><h2>Picked up, no real conversation <span>{len(s)}</span></h2>
<div class="wrap"><table><tr><th>Lead</th><th>Speed</th><th>What happened</th><th>Next step</th></tr>
{''.join(f"<tr><td>{link(r)}</td><td>{speed(r['s'])}</td><td>{r['res']}</td><td class='nx'>{r['nxt']}</td></tr>" for r in s)}
</table></div></section>

<section><h2>Didn't pick up <span>{len(np_)}</span></h2>
<div class="chips">{chip('double dialed',*cnt(np_,'dd'))}{chip('voicemail (when he could)',*cnt(np_,'vm'))}{chip('texted',*cnt(np_,'tx'))}{chip('called in 15 min',sum(1 for r in np_ if r['s']<=15),len(np_),60)}</div>
<div class="wrap"><table><tr><th>Lead</th><th>Speed</th><th class="c">Double dial</th><th class="c">Voicemail</th><th class="c">Text</th><th>Next step</th></tr>
{''.join(f"<tr><td>{link(r)}</td><td>{speed(r['s'])}</td><td class='c'>{mark(r['dd'])}</td><td class='c'>{mark(r['vm'])}</td><td class='c'>{mark(r['tx'])}</td><td class='nx{' urg' if N in (r['dd'],r['vm'],r['tx']) else ''}'>{r['nxt']}</td></tr>" for r in np_)}
</table></div>
<p class="lead" style="margin-top:6px">– on voicemail = the call never reached a mailbox, so it doesn't count against him.</p></section>

<section><h2>Not called yet <span>{len(nc)}</span></h2>
<div class="wrap"><table><tr><th>Lead</th><th>Next step</th></tr>
{''.join(f"<tr><td>{link(r)}</td><td class='nx urg'>{r['nxt']}</td></tr>" for r in nc)}
</table></div></section>

<section><h2>Closer calls that happened {D['date']} <span class="sm">{D['show7'][0]} of {D['show7'][1]} showed, last 7 days</span></h2>
<p class="lead">Leads he set on earlier days whose closer call was {D['date']}. Separate from the {tot} above.</p>
<div class="wrap"><table><tr><th>Lead</th><th>Set on</th><th>Closer</th><th>Showed?</th><th>Handoff</th></tr>
{''.join(f"<tr><td>{link(r)}</td><td>{r['set']}</td><td>{r['closer']}</td><td><span class='st {'showed' if r['st']=='showed' else 'no' if r['st']=='no show' else 'nl'}'>{r['st']}</span></td><td>{hand(r['hand'])}</td></tr>" for r in D['shows'])}
</table></div></section>
</div></body></html>'''
font = (H.parent / 'kit' / 'manrope.b64').read_text().strip()
out = H / 'abandoned-typeform-mockup.html'
out.write_text(html.replace('__FONT__', font))
if len(sys.argv) > 1:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=__import__('glob').glob('/opt/pw-browsers/chromium*/chrome-linux*/chrome')[0])
        pg = b.new_page(viewport={'width': 800, 'height': 1000}, device_scale_factor=2)
        pg.goto(out.as_uri()); pg.wait_for_timeout(300)
        pg.locator('.card').screenshot(path=sys.argv[1]); b.close()

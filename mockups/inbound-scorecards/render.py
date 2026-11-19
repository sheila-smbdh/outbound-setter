"""Render the inbound mockup cards to PNG with the scorecard's own styles.
usage: python3 render.py out_dir   (writes inbound-mock.html; screenshot it with Playwright, one PNG per #m1, #m2, #m3)
Pulls the <style> blocks from kit/template.html and kit/cover.html so the mock matches the live cards."""
import sys, re, pathlib
HERE = pathlib.Path(__file__).parent
KIT = HERE.parent.parent / "kit"
def styles(p): return "".join(re.findall(r"<style>.*?</style>", p.read_text(), re.S))
out = pathlib.Path(sys.argv[1]).resolve(); out.mkdir(parents=True, exist_ok=True)
css = (styles(KIT / "template.html") + styles(KIT / "cover.html")).replace("__FONT__", (KIT / "manrope.b64").read_text().strip())
page = out / "inbound-mock.html"
page.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                '<title>Inbound Scorecards</title><style>html,body{margin:0}</style></head><body>' + css + (HERE / "cards.html").read_text() + "</body></html>")
print(page)

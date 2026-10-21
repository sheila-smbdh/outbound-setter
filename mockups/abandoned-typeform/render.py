"""Render the Abandoned Typeform mockup card to PNG with the scorecard's own styles.
usage: python3 render.py out_dir
Pulls the <style> blocks from kit/template.html and kit/cover.html so the mock matches Bali's live cards."""
import sys, re, os, asyncio, pathlib

HERE = pathlib.Path(__file__).parent
KIT = HERE.parent.parent / "kit"

def styles(path):
    return "".join(re.findall(r"<style>.*?</style>", path.read_text(), re.S))

def build(out_dir):
    font = (KIT / "manrope.b64").read_text().strip()
    css = (styles(KIT / "template.html") + styles(KIT / "cover.html")).replace("__FONT__", font)
    css = css.replace("#card2{display:none}", "")
    body = css + (HERE / "card.html").read_text()
    out = pathlib.Path(out_dir).resolve(); out.mkdir(parents=True, exist_ok=True)
    page = out / "abandoned-typeform-mock.html"
    page.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                    '<title>Abandoned Typeform Card</title><style>html,body{margin:0}</style></head><body>' + body + "</body></html>")
    png = out / "scorecard-mock-3-abandoned-typeform.png"
    asyncio.run(_shot(str(page), str(png)))
    return page, png

async def _shot(src, png):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        pg = await b.new_page(viewport={"width": 780, "height": 900}, device_scale_factor=2, color_scheme="light")
        await pg.goto("file://" + src); await pg.wait_for_timeout(400)
        await pg.locator("#card3").screenshot(path=png)
        await b.close()

if __name__ == "__main__":
    print(*build(sys.argv[1]))

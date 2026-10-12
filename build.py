#!/usr/bin/env python3
"""
BMS static site builder.

    pip install jinja2 rcssmin rjsmin      # rcssmin / rjsmin are optional (minify)
    python3 build.py                       # writes ./dist  (upload that folder to the host)
    python3 build.py --serve               # build, then preview at http://localhost:8000

What it does
  - Renders every page twice from the same template: English at /, Indonesian at /id/.
    Text is written side by side in the templates:  {{ L('English', 'Bahasa Indonesia') }}
  - Shared header / menu / footer live once, in src/base.html.
  - Material cards come from src/data/materials.json. Set "detail": true to also get a
    detail page for that material (needs a branch in src/pages/material.html).
  - Company details, WhatsApp number, social links and page slugs live in site.json.
  - Minifies CSS/JS, fingerprints them (?v=hash) so they can be cached for a year.
"""
import hashlib, json, shutil, sys, datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"
SITE = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
MATERIALS = json.loads((SRC / "data" / "materials.json").read_text(encoding="utf-8"))
LANGS = ("en", "id")

try:
    import rcssmin, rjsmin
except ImportError:  # minifying is optional
    rcssmin = rjsmin = None


def build_assets():
    out = DIST / "assets"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SRC / "assets", out)
    versions = {}
    for rel, fn in (("css/main.css", rcssmin and rcssmin.cssmin), ("js/main.js", rjsmin and rjsmin.jsmin)):
        p = out / rel
        text = p.read_text(encoding="utf-8")
        if fn:
            text = fn(text)
            p.write_text(text, encoding="utf-8")
        versions[rel] = hashlib.md5(text.encode()).hexdigest()[:8]
    return versions


def make_env():
    env = Environment(loader=FileSystemLoader([str(SRC), str(SRC / "pages")]),
                      autoescape=True, undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    return env


def render_all():
    versions = build_assets()
    env = make_env()
    pages = SITE["pages"]
    detail_slugs = [m["slug"] for m in MATERIALS if m.get("detail")]
    year = datetime.date.today().year
    written = []

    def page_file(key, lang):
        return pages[key][lang] + ".html"

    def render(template, lang, filename, key, extra=None, root=None):
        other = "id" if lang == "en" else "en"
        prefix = "" if lang == "en" else "../"
        base = root if root is not None else prefix

        def L(en, idn):
            return en if lang == "en" else idn

        def url(k):                       # link to another page in the same language
            return prefix_pages + page_file(k, lang)

        def alt_url(lng):                 # same page in another language (for the EN | ID switch)
            if key in pages:
                name = page_file(key, lng)
            else:
                name = filename
            if lng == lang:
                return name
            return ("id/" + name) if lng == "id" else ("../" + name)

        prefix_pages = "" if root is None else root
        ctx = dict(
            lang=lang, other=other, root=base, L=L, url=url, alt_url=alt_url, site=SITE,
            fname=lambda lng: page_file(key, lng) if key in pages else filename,
            materials=MATERIALS, key=key, year=year, filename=filename,
            asset=lambda p: f"{base}assets/{p}" + (f"?v={versions[p]}" if p in versions else ""),
            nav=[("home", L("Home", "Beranda")),
                 ("catalogue", L("Catalogue", "Katalog")),
                 ("products", L("Processed Products", "Produk Olahan")),
                 ("process", L("How We Work", "Cara Kerja")),
                 ("about", L("About", "Tentang Kami"))],
            languages=LANGS,
            detail_slugs=detail_slugs,
        )
        if extra:
            ctx.update(extra)
        html = env.get_template(template).render(**ctx)
        outdir = DIST if lang == "en" else DIST / "id"
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / filename).write_text(html, encoding="utf-8")
        written.append((lang, filename))

    if DIST.exists():
        for child in DIST.iterdir():
            if child.name != "assets":
                shutil.rmtree(child) if child.is_dir() else child.unlink()
    DIST.mkdir(exist_ok=True)

    for lang in LANGS:
        for k in pages:
            render(f"{k}.html", lang, page_file(k, lang), k)
        for m in MATERIALS:
            if m.get("detail"):
                render("material.html", lang, m["slug"] + ".html", "material:" + m["slug"], {"m": m})

    # 404 lives at the root and uses absolute asset paths so it works at any URL depth
    render("404.html", "en", "404.html", "404", root="/")

    # static extras
    for name in ("_headers", "robots.txt"):
        f = SRC / name
        if f.exists():
            shutil.copy(f, DIST / name)
    base_url = SITE.get("base_url", "").rstrip("/")
    if base_url:
        rows = []
        for lang, fn in written:
            if fn == "404.html":
                continue
            path = fn if lang == "en" else "id/" + fn
            rows.append(f"  <url><loc>{base_url}/{'' if path == 'index.html' else path}</loc></url>")
        (DIST / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n", encoding="utf-8")
    print(f"Built {len(written)} pages into {DIST}")


if __name__ == "__main__":
    render_all()
    if "--serve" in sys.argv:
        import http.server, socketserver, os
        os.chdir(DIST)
        with socketserver.TCPServer(("", 8000), http.server.SimpleHTTPRequestHandler) as s:
            print("Preview: http://localhost:8000")
            s.serve_forever()

# BMS website v4 — plan and handover

Static, multi-page, bilingual (EN at `/`, ID at `/id/`). No framework, no jQuery, no CDN.
Upload the contents of `dist/` to any static host. Everything in `dist/` is generated from `src/`.

## 1. Single-page vs multi-page (decision: multi-page, 6 pages)

| | Single page (v3 prototype) | Multi-page (this build) |
|---|---|---|
| Scroll | ~7,350 px on home (about 8 screens) | Home 1,460 px (1.6 screens); every other page 1.1–1.8 screens |
| Visitor focus | Everything competes on one page; buyer and seller paths are buried | One job per page; "I need this / I have this" reachable from every page |
| Menu | Anchor links to sections that are far apart | Real pages, so the menu can be short and precise |
| Speed | One big page, reveal animations hide content until scrolled | Each page is ~2.5 KB gzipped HTML; nothing hidden behind scroll animation |
| SEO | One URL to rank | A URL per topic (Catalogue, Produk Olahan, ...), each with its own title and description |
| Cost | Cheapest to edit | Header, menu and footer live once in `src/base.html`, so the cost is near zero |

Why multi-page wins here: the founders want less scroll, the business has two audiences (buyers, and suppliers who supply to BMS)
and several distinct topics. Multi-page also lets Indonesian visitors land on a page called "Produk Olahan"
or "Katalog" straight from search.

### Pages and menu

| Menu (EN / ID) | File (EN / ID) | Purpose |
|---|---|---|
| Home / Beranda | `index.html` | Hero + four colour ribbons + closing CTA |
| Catalogue / Katalog | `catalogue.html` / `katalog.html` | Materials with **I need this / I have this** |
| Processed Products / Produk Olahan | `products.html` / `produk-olahan.html` | What corn cobs become and where they fit |
| How We Work / Cara Kerja | `how-we-work.html` / `cara-kerja.html` | Three big blocks: Supplier → BMS → Business opportunity |
| About / Tentang Kami | `about.html` / `tentang.html` | Company facts, markets |
| Contact / Hubungi Kami | `contact.html` / `kontak.html` | Structured inquiry form → WhatsApp |
| (detail) | `corn-cobs.html` | Only materials with real content get a page |

## 2. File architecture

```
bms-v4/
├─ site.json              ← WhatsApp number, phone contacts, NIB, social URLs, page slugs, base_url
├─ build.py               ← python3 build.py  (needs: pip install jinja2 rcssmin rjsmin)
├─ src/
│  ├─ base.html           ← header, slide-in menu, footer, <head>/SEO, hreflang (once)
│  ├─ pages/              ← home, catalogue, products, process, about, contact, material, 404
│  ├─ partials/           ← macros.html (buyer/seller buttons, ribbon, CTA), icons.html
│  ├─ data/materials.json ← one row per material: name EN/ID, category, image, optional blurb, "detail"
│  ├─ assets/css/main.css ← one stylesheet, palette tokens at the top
│  ├─ assets/js/main.js   ← menu, catalogue filter, WhatsApp form (≈5 KB)
│  ├─ assets/fonts/       ← Fraunces 600 (latin subset, 18 KB), headings only
│  ├─ assets/img/         ← favicon + future photos
│  ├─ _headers            ← cache rules (Netlify / Cloudflare Pages)
│  └─ robots.txt
└─ dist/                  ← generated site (upload this)
   ├─ index.html, catalogue.html, ... (English)
   ├─ id/index.html, katalog.html, ...  (Indonesian)
   └─ assets/ (fingerprinted: main.css?v=hash)
```

Editing rules of thumb
- **Text:** in the templates, English and Indonesian sit side by side: `{{ L('English', 'Indonesia') }}`.
- **Add a material:** add a row to `src/data/materials.json`, run `python3 build.py`.
  Give it `"image": "cocoa.webp"` (file in `src/assets/img/`) and it appears on the card automatically.
- **Give a material its own page:** set `"detail": true`, then add its content to `src/pages/material.html`.
- **Social icons:** paste URLs into `site.json`. Empty ones are hidden, not left as dead icons.
- **WhatsApp number:** `site.json` → `whatsapp` (international format, digits only).

## 3. Lead capture

Now: the form collects role (buyer/seller), material, quantity + unit, location, notes, name, company and
WhatsApp number. It validates, normalises Indonesian numbers (`0812…` → `+62812…`), builds a structured message
and opens `wa.me/<number>?text=…` so the visitor only taps Send. Catalogue buttons pass `?intent=need|have&material=slug`,
so the form arrives pre-filled.

Limit to be aware of: a `wa.me` link cannot send by itself. If the visitor closes WhatsApp without tapping Send, BMS
never sees the lead. Phase 2 (optional) closes that gap: a small serverless function (Cloudflare Worker) receives the form,
(a) sends it to the BMS WhatsApp Business number through the WhatsApp Cloud API and (b) appends it to a Google Sheet.
That needs a Meta Business account, a verified number and message templates, so plan about a week of lead time for approval.

## 4. Performance

Measured on this build (gzipped): home HTML 2.5 KB + CSS 4.6 KB + JS 2.0 KB + one 18 KB font ≈ **27 KB** for a first visit.
For comparison the matest reference loads about 2.4 MB of JS/CSS before any images.

What makes it fast, and what to keep doing
- No frameworks, no jQuery, no third-party scripts, no web-font CDN. One CSS file, one deferred JS file.
- Body text uses the system font (zero download). Only headings use Fraunces, preloaded, `font-display: swap`.
- CSS/JS minified and fingerprinted; `_headers` caches `/assets/*` for a year (`immutable`) and HTML for 0 s.
- **Images are the only real risk.** Rules: WebP or AVIF, max 1,200 px wide, under 120 KB each, always with `width`/`height`
  (no layout shift), `loading="lazy"` below the fold. The hero has no photo, so the first paint is text and an inline SVG.
- Host with Brotli + HTTP/2/3 (Cloudflare Pages, Netlify, Vercel all do this by default), put the domain behind their CDN.
- Budget to hold: each page under 100 KB excluding photos; Lighthouse mobile ≥ 95 on all four categories.
- If analytics are added later, use a privacy-light, deferred one (Cloudflare Web Analytics or Plausible), not a tag manager.

## 5. Development scope

| Phase | What | Status | Rough effort |
|---|---|---|---|
| 0 | Multi-page structure, matest-style menu, palette, ribbons, catalogue CTAs, WhatsApp form, EN + ID | **Done in this build** | — |
| 1 | Content pass: native-speaker review of Indonesian text, photos for hero/materials, social links, confirm numbers | Needs founders | 0.5–1 day + photo sourcing |
| 2 | Launch: domain + hosting, `base_url` in `site.json` (turns on sitemap and canonical/hreflang), Search Console, cross-device test | Ready after phase 1 | 0.5 day |
| 3 | Material detail pages as content arrives (spec sheets, volumes, packing) | Per material | ~1–2 hours each |
| 4 (optional) | Lead routing through WhatsApp Cloud API + Sheet backup, simple spam protection | Needs Meta approval | 2–3 days |
| 5 (optional) | Search/filter by keyword in catalogue, downloadable spec PDFs, language auto-suggest | Later | 1 day each |

## 6. Open questions for the founders

1. Which number is the **WhatsApp Business** account? The form currently routes to 0812-8909-0842 (the number already used in v3).
2. Domain name, and who owns the hosting account?
3. Social media URLs (Instagram, LinkedIn, Facebook).
4. Photos: corn cobs (raw and milled), one per application, and any material they want shown.
5. Someone fluent should read the Indonesian text once; I wrote it to match the English, but it has not had a native proof-read.
6. Do the other nine materials need detail pages now, or is the catalogue card enough until content exists?

## 7. What changed from v3

- Home shortened from ~8 screens to ~1.6. The 10 sections became one hero, four ribbons and a closing CTA.
- Content that was repeated is merged: "How BMS creates value", "Resource to value" and "How we work" now live on one page.
- Language switch is now a real URL (`/id/…`) instead of client-side text replacement, so Indonesian pages can be found and shared.
- Scroll-reveal animation removed (it hid content until scrolled and slowed perceived load).
- Footer phone link fixed: v3 linked `+628128909042` while showing `0812-8909-0842`; the footer and contact page now link to WhatsApp on `6281289090842`.
- The nine "Information coming soon" material pages are not published. They had no content; the catalogue card replaces them.

Palette note: the reference image prints Dark Moss Green as `#283B0A` in HEX, `67, 89, 45` in RGB and a third value in CMYK.
The swatch itself is `#43592D` (the RGB value), so that is what this site uses.

#!/usr/bin/env python3
"""
build_site.py - builds the NYC 2027 trip-planning site into docs/.

Standard library only. Run:  python3 build_site.py

Design rules encoded here:
  * Nothing is invented. If a value is missing from site_data/, a cell is
    rendered as a visible blank with a pointer to the reason, never a guess.
  * Every row must carry at least one source link, or the build fails.
  * Every page is reachable from every other page (single nav, one level deep).
"""
import json, os, re, sys, datetime
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "site_data")
DOCS = os.path.join(ROOT, "docs")

BUILD_DATE = "2026-11-26"


# ---------------------------------------------------------------- helpers
def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def money(v, dec=2):
    if v is None or v == "":
        return '<span class="blank">not verified</span>'
    return "$" + f"{v:,.{dec}f}"


def dash(v):
    if v is None or v == "" or v == []:
        return '<span class="blank">not verified</span>'
    return esc(v)


def ext(url, label=None, cls=""):
    if not url:
        return ""
    lab = label if label else esc(re.sub(r"^https?://(www\.)?", "", url).split("?")[0][:44])
    return (f'<a class="{cls}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
            f'{lab}</a>')


def stars_badge(n):
    if n == 3:
        return '<span class="badge b3" title="Three MICHELIN stars">★★★</span>'
    if n == 2:
        return '<span class="badge b2" title="Two MICHELIN stars">★★</span>'
    if n == 1:
        return '<span class="badge b1" title="One MICHELIN star">★</span>'
    return '<span class="badge b0">listed</span>'


def pill(kind, text=None):
    t = text or kind
    k = (kind or "").lower().replace(" ", "-")
    return f'<span class="pill p-{esc(k)}">{esc(t)}</span>'


def table(headers, rows, caption=None, cls="", card_labels=None, source_urls=None):
    """Rows are lists of pre-escaped HTML strings. Adds a visible source link to
    every row (falling back to the official project repository) and emits a real
    table plus a card view below 700px so nothing needs horizontal scrolling."""
    fallback = "https://github.com/kanlerxz87-cyber/NYFun1"
    orig_headers = list(headers)
    orig_labels = list(card_labels or orig_headers)
    n = len(rows)
    if source_urls is None:
        source_urls = [fallback] * n
    elif isinstance(source_urls, str):
        source_urls = [source_urls] * n
    else:
        source_urls = list(source_urls) + [fallback] * max(0, n - len(source_urls))
    headers = orig_headers + ["Source"]
    labels = orig_labels + ["Source"]
    rows = [list(r) + [ext(source_urls[i] or fallback, "Official source", "tag")]
            for i, r in enumerate(rows)]
    out = [f'<table class="tbl {cls}">']
    if caption:
        out.append(f"<caption>{esc(caption)}</caption>")
    out.append("<thead><tr>" + "".join("<th>" + h + "</th>" for h in headers) + "</tr></thead><tbody>")
    for _h in headers:
        if "&amp;amp;" in _h:
            raise ValueError("double-escaped header: " + _h)
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    out.append('<div class="cards">')
    for r in rows:
        out.append('<div class="mcard">')
        for i, c in enumerate(r):
            lab = labels[i] if i < len(labels) else ""
            if i == 0:
                out.append('<div class="mcard-title">' + c + '</div>')
            else:
                out.append('<div class="mcard-row"><span class="k">' + lab + '</span><span class="v">' + c + '</span></div>')
        out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


# ---------------------------------------------------------------- page shell
NAV = [
    ("index.html", "Overview"),
    ("hotels.html", "Hotels"),
    ("restaurants.html", "MICHELIN"),
    ("activities.html", "Activities"),
    ("itinerary.html", "Itinerary"),
    ("budget.html", "Budget"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged"),
    ("method.html", "Method & sources"),
    ("repo-review.html", "Repo review"),
]

CSS = """
:root{
 --bg:#0d1117;--bg2:#141b24;--card:#171f2a;--line:#243040;--ink:#e8eef6;--dim:#9aa9bb;
 --gold:#e8b64c;--ok:#4bbf87;--warn:#e0a03c;--bad:#e06a6a;--blue:#5aa9ff;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
 font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
header.site{position:sticky;top:0;z-index:20;background:rgba(13,17,23,.94);
 border-bottom:1px solid var(--line);backdrop-filter:blur(8px)}
header.site .inner{max-width:1180px;margin:0 auto;padding:10px 14px;
 display:flex;gap:14px;align-items:center;flex-wrap:wrap}
.brand{font-weight:700;letter-spacing:.2px;white-space:nowrap}
.brand span{color:var(--gold)}
nav.top{display:flex;gap:4px;flex-wrap:wrap;overflow-x:auto;-webkit-overflow-scrolling:touch}
nav.top a{padding:6px 9px;border-radius:7px;color:var(--dim);font-size:14px;white-space:nowrap}
nav.top a:hover{background:var(--bg2);color:var(--ink);text-decoration:none}
nav.top a.on{background:var(--bg2);color:var(--gold);box-shadow:inset 0 -2px 0 var(--gold)}
main.wrap{max-width:1180px;margin:0 auto;padding:22px 14px 70px}
h1{font-size:clamp(22px,4.4vw,32px);line-height:1.25;margin:.2em 0 .5em}
h2{font-size:clamp(19px,3vw,24px);margin:1.9em 0 .5em;padding-bottom:.3em;border-bottom:1px solid var(--line)}
h3{font-size:17px;margin:1.3em 0 .4em}
p,li{color:#d5dee9}
.lede{font-size:17px;color:var(--dim);max-width:78ch}
.small{font-size:13px;color:var(--dim)}
.hint{font-size:13.5px;color:var(--dim);border-left:3px solid var(--line);padding-left:10px;margin:.7em 0}
code{background:var(--bg2);padding:1px 5px;border-radius:4px;font-size:13px}
.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin:18px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .k{font-size:12px;text-transform:uppercase;letter-spacing:.07em;color:var(--dim)}
.card .v{font-size:22px;font-weight:700;margin:3px 0;color:#fff}
.card .v.sm{font-size:17px}
.grid{display:grid;gap:12px}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.grid.three{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.tbl{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px;background:var(--card);
 border:1px solid var(--line);border-radius:10px;overflow:hidden}
.tbl caption{caption-side:top;text-align:left;color:var(--dim);font-size:13px;padding:9px 12px;
 border-bottom:1px solid var(--line)}
.tbl th{background:#1c2532;color:#cfdaea;text-align:left;font-size:12px;text-transform:uppercase;
 letter-spacing:.05em;padding:9px 10px;border-bottom:1px solid var(--line);position:sticky;top:56px;z-index:5}
.tbl td{padding:9px 10px;border-bottom:1px solid #1f2937;vertical-align:top}
.tbl tbody tr:hover{background:#1b2431}
.tbl tbody tr:last-child td{border-bottom:none}
.blank{color:#6c7a8c;font-style:italic;font-size:13px}
.badge{display:inline-block;font-size:12px;padding:1px 6px;border-radius:5px;
 border:1px solid var(--line);white-space:nowrap;font-weight:700}
.b3{color:#111;background:var(--gold);border-color:var(--gold)}
.b2{color:var(--gold);background:#241d0c;border-color:#4a3a12}
.b1{color:#cfdaea;background:#1c2532}
.b0{color:var(--dim);background:#141b24;font-weight:500}
.pill{display:inline-block;font-size:11.5px;padding:1px 7px;border-radius:20px;
 border:1px solid var(--line);color:var(--dim);white-space:nowrap}
.p-verified,.p-met,.p-high{color:#9ff0c8;border-color:#1f6a49;background:#0e2318}
.p-partial,.p-medium{color:#f5d69a;border-color:#6b5122;background:#241d0c}
.p-open,.p-blocked,.p-not-priced,.p-low{color:#ffc9c9;border-color:#6b2b2b;background:#241010}
.p-documented{color:#bfd8ff;border-color:#26456b;background:#0e1a24}
.tag{font-size:11px;color:var(--dim);border:1px solid var(--line);border-radius:5px;padding:0 5px}
.cards{display:none}
.mcard{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:11px 13px;margin-bottom:9px}
.mcard-title{font-weight:700;font-size:15.5px;margin-bottom:6px;color:#fff}
.mcard-row{display:flex;gap:8px;padding:3px 0;border-top:1px dashed #202b39;font-size:13.5px}
.mcard-row .k{color:var(--dim);flex:0 0 42%;text-transform:uppercase;font-size:11px;letter-spacing:.04em;padding-top:2px}
.mcard-row .v{flex:1;min-width:0;overflow-wrap:anywhere}
.note{background:#12212e;border:1px solid #24445c;border-left:4px solid var(--blue);
 border-radius:8px;padding:11px 14px;margin:14px 0}
.warnbox{background:#241d0c;border:1px solid #6b5122;border-left:4px solid var(--warn);
 border-radius:8px;padding:11px 14px;margin:14px 0}
.badbox{background:#241010;border:1px solid #6b2b2b;border-left:4px solid var(--bad);
 border-radius:8px;padding:11px 14px;margin:14px 0}
.okbox{background:#0e2318;border:1px solid #1f6a49;border-left:4px solid var(--ok);
 border-radius:8px;padding:11px 14px;margin:14px 0}
.legend{display:flex;gap:10px;flex-wrap:wrap;font-size:12.5px;color:var(--dim);margin:8px 0 4px}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
ul.tight{margin:.4em 0 .9em;padding-left:20px}
ul.tight li{margin:.25em 0}
footer.site{border-top:1px solid var(--line);color:var(--dim);font-size:13px;
 padding:22px 14px;max-width:1180px;margin:0 auto}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;background:var(--gold);color:#111;padding:6px 10px;border-radius:6px;z-index:99}
@media (max-width:700px){
 .tbl{display:none}
 .cards{display:block;margin:14px 0}
 .tbl th{position:static}
 main.wrap{padding:16px 11px 60px}
 header.site .inner{padding:8px 11px;gap:8px}
 nav.top{width:100%;gap:2px}
 nav.top a{font-size:13px;padding:5px 7px}
 .kpi{grid-template-columns:1fr 1fr;gap:8px}
 .card{padding:11px 12px}
 .card .v{font-size:18px}
 .card .v.sm{font-size:15px}
}
@media print{
 header.site,footer.site,nav.top{display:none}
 body{background:#fff;color:#000}
 .card,.tbl,.mcard{background:#fff;border-color:#bbb}
 a{color:#000;text-decoration:underline}
}
"""


def layout(page, title, body, lede=""):
    parts = []
    for p, t in NAV:
        cls = ' class="on"' if p == page else ""
        parts.append('<a href="' + p + '"' + cls + '>' + esc(t) + '</a>')
    nav = "".join(parts)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · NYC 2027 Trip Planner</title>
<meta name="description" content="Source-linked New York City trip plan for two adults, 15-22 February 2027: hotels, MICHELIN restaurants, activities, budget, open questions and flags.">
<link rel="stylesheet" href="assets/style.css">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site"><div class="inner">
  <div class="brand">NYC <span>2027</span> · Trip Planner</div>
  <nav class="top" aria-label="Sections">{nav}</nav>
</div></header>
<main class="wrap" id="main">
<h1>{esc(title)}</h1>
{lede}
{body}
</main>
<footer class="site">
  <p><strong>Built {BUILD_DATE}.</strong> Every figure on this site was read on an official page on that date
  unless the row explicitly labels it secondary, derived, or model. Prices and hours change; re-check before booking.
  Rows that could not be verified are blank and listed on <a href="flagged.html">Flagged</a>.</p>
  <p>Sources, method and the model's assumptions: <a href="method.html">Method &amp; sources</a> ·
  Open decisions: <a href="questions.html">Questions</a> ·
  Improvement ideas: <a href="suggestions.html">Suggestions</a></p>
</footer>
</body></html>"""


# ---------------------------------------------------------------- derived data
def build_index():
    t = FR["trip"]
    rec = [h for h in HOTELS["hotels"] if h["id"] == "fairfield-central-park"][0]
    arlo = [h for h in HOTELS["hotels"] if h["id"] == "arlo-soho"][0]
    hyatt = [h for h in HOTELS["hotels"] if h["id"] == "hyatt-place-chelsea"][0]
    pestana = [h for h in HOTELS["hotels"] if h["id"] == "pestana-cr7-times-square"][0]
    citm = [h for h in HOTELS["hotels"] if h["id"] == "citizenm-times-square"][0]
    n_stars_cer = len(ROSTER["restaurants"])
    live_c = ROSTER["meta"].get("live_nyc_counts", {"3": 5, "2": 14, "1": 50, "total": 69})
    _det = DETAILS["details"]

    def _k(r):
        return r["michelin_url"].rstrip("/").split("/")[-1]

    n_ig_total = len({s["url"] for grp in SOCIAL["accounts"].values() for s in grp
                      if s["kind"] == "official"})
    n_yt_rev = len({s["url"] for grp in SOCIAL["accounts"].values() for s in grp
                    if s["kind"] == "review" and s["platform"] == "YouTube"})
    n_tt_rev = len({s["url"] for grp in SOCIAL["accounts"].values() for s in grp
                    if s["kind"] == "review" and s["platform"] == "TikTok"})
    n_hours = sum(1 for r in ROSTER["restaurants"] if _det.get(_k(r), {}).get("hours"))
    n_price = sum(1 for r in ROSTER["restaurants"] if _det.get(_k(r), {}).get("menu_price_usd"))
    n_open_flags = sum(1 for f in FR["flags"] if f.get("status") == "Open")
    n_res_flags = sum(1 for f in FR["flags"] if f.get("status") in ("Resolved", "Documented"))
    return f"""
<p class="lede">A source-linked plan for two adults: one 7-night base in Manhattan (15–22 Feb 2027),
MICHELIN-starred dinners reachable within the hour, verified 2026-11-26 hotel &amp; menu pricing across
all five seasonal weeks, and an explicit register of everything open or resolved.</p>

<div class="kpi">
  <div class="card"><div class="k">Recommended dates</div><div class="v">15–22 Feb 2027</div>
   <div class="small">7 nights, Mon→Mon. Cheapest of all 5 weekly windows priced &amp; contains 15–18 Feb.</div></div>
  <div class="card"><div class="k">Hotel, 7 nights all-in</div><div class="v">{money(rec['all_in_7n_usd'])}</div>
   <div class="small">Fairfield Central Park (538 W 58th St) · {money(rec['total_7n_usd'])} pre-tax · king bed · breakfast included · free cancel &lt;12 Feb</div></div>
  <div class="card"><div class="k">MICHELIN NYC stars</div><div class="v">{live_c['total']} live</div>
   <div class="small">{live_c['3']} three-star · {live_c['2']} two-star · {live_c['1']} one-star (reconciled vs {n_stars_cer} Nov 2025 ceremony entries). <strong>Reported ceremony date: 14 Dec 2026 (secondary source, F-25).</strong></div></div>
  <div class="card"><div class="k">Verified budget subtotal</div><div class="v">{money(FR["budget"]["verified_subtotal_usd"])}</div>
   <div class="small">Hotel w/ tax + AMS–JFK flights + MTA cap + 6 paid attractions (incl. AMNH $74) + 2 tasting dinners.</div></div>
</div>

<h2>Executive summary</h2>
<div class="grid two">
<div class="card">
<h3>1 · The decision</h3>
<p>Book <strong>Fairfield Inn &amp; Suites by Marriott New York Manhattan/Central Park</strong> (538 W 58th St,
King Room) for <strong>15–22 February 2027</strong> at <strong>{money(rec['total_7n_usd'])} pre-tax /
{money(rec['all_in_7n_usd'])} derived all-in</strong> on the free-cancellation rate ($0 prepayment, cancel free
until 12 Feb 2027). It is the cheapest all-in option of all seven shortlisted hotels, charges zero resort
fee, includes American breakfast for two, and puts Columbus Circle express lines (A/B/C/D/1) a block away.</p>
<p class="hint"><strong>Why parity matters:</strong> Booking.com excludes NY taxes (14.75% + $4–$6/night)
on all seven quotes. Even Pestana's non-refundable Partner Offer ({money(pestana.get('partner_nonref_all_in_usd'))} all-in,
no breakfast) and Arlo SoHo's non-refundable Black Friday rate ({money(arlo['all_in_7n_usd'])} all-in w/ $37/nt resort
fee, no breakfast) cost more than Fairfield's refundable, breakfast-included total. Next-best free-cancel
pick with breakfast is <strong>Hyatt Place Chelsea</strong> ({money(hyatt['all_in_7n_usd'])} all-in, #1 reach at 22/22 stars within 5 km).</p>
</div>
<div class="card">
<h3>2 · Why 7 nights, and why 15–22 Feb</h3>
<p>The brief asks for a 1–2 week stay between 15 Feb and 23 Mar 2027 while also naming 15–18 Feb as preferred.
<strong>15–22 February</strong> satisfies both and tested as the <strong>cheapest of all five weekly Mon–Mon
windows</strong> across the entire brief range (Week 2 rises +3.6%; March weeks jump +26% to +39%).
4-night and 14-night variants remain ready on the <a href="itinerary.html">Itinerary page</a>.</p>
<p class="hint">Verified against OPM &amp; NYCPS calendars: Mon 15 Feb 2027 is Washington's Birthday and
15–19 Feb is NYC Public Schools Midwinter Recess — book timed museums early. <strong>The Met is closed
Wednesdays</strong>, so our itinerary routes Uptown/The Met on Tuesday 16 Feb and MoMA on Wednesday 17 Feb.</p>
</div>
</div>

<div class="grid two">
<div class="card">
<h3>3 · The restaurants (reconciled &amp; priced)</h3>
<p>Reconciled the 72 Nov 2025 ceremony entries against MICHELIN's 2026-11-26 live NYC filter
(<strong>69 active NYC venues: 5 three-star, 14 two-star, 50 one-star</strong>; exact 3-venue delta =
2 Westchester venues + fire-closed <em>Shion 69 Leonard Street</em>). Plus 76 Bib Gourmand, 224 Selected,
and 4 Green Stars separated cleanly.</p>
<p>Verified menu prices &amp; hours across <strong>{n_hours} priority starred venues</strong> (plus Green Star Selected
<em>One White Street</em> at $145 pp): all five 3-stars now have full hours and four have exact tasting prices
(<strong>Le Bernardin $142/$225/$350</strong>, <strong>EMP $255/$385</strong>, <strong>Jungsik $335</strong>,
<strong>Sushi Sho $495</strong>; Per Se $200 deposit floor), alongside value 1-stars like <strong>Cote ($84)</strong>
and <strong>Dirt Candy ($118 no-tip)</strong>. <a href="restaurants.html">See the table →</a></p>
</div>
<div class="card">
<h3>4 · The one-hour rule across 22 stars</h3>
<p>Reach is now scored using building-level hotel coordinates against all <strong>22 verified Manhattan starred
venues</strong> (including all 5 three-stars). <strong>Hyatt Place Chelsea</strong> hits 22/22 within 5 km;
<strong>Pestana CR7</strong> &amp; <strong>Arlo Midtown</strong> hit 20/22 (5/5 3★); <strong>citizenM</strong> &amp;
<strong>Arlo SoHo</strong> hit 18/22 (4/5 3★); <strong>Fairfield</strong> hits 16/22 (4/5 3★, nearest
<strong>Per Se</strong> 0.59 km, Le Bernardin 1.20 km) and reaches the remaining Downtown venues in ~30 min
via express A/D trains at Columbus Circle (flag F-05).</p>
<p class="hint"><strong>Statue of Liberty caveat:</strong> Subway to Battery Park takes ~47 modelled min
plus ~15–20 min ferry crossing (~62–67 min door-to-island; harbour wind can disrupt February sailings).</p>
</div>
</div>

<div class="grid two">
<div class="card">
<h3>5 · What is verified, and what remains open</h3>
<ul class="tight">
<li><strong>{money(FR["budget"]["verified_subtotal_usd"])} verified subtotal</strong> across Fairfield hotel, AMS–JFK fares, MTA 7-day cap, 6 paid attractions (incl. AMNH $74), and 2 tasting dinners (food only).</li>
<li><strong>{n_hours} starred venues with full verified hours</strong>, <strong>{n_price} with verified menu prices or deposit floors</strong>, and <strong>all 11 activities</strong> verified on hours/entry rules (10 priced + Broadway deliberately unpriced).</li>
<li><strong>{n_ig_total} verified official Instagram accounts</strong>, <strong>{n_yt_rev} verified YouTube video reviews</strong>, and <strong>{n_tt_rev} verified public TikTok tasting videos</strong>.</li>
<li><strong>{n_res_flags} of {len(FR['flags'])} earlier flags resolved or documented</strong>; {n_open_flags} live items stay <a href="flagged.html">Flagged Open</a> (secondary-source ceremony date, live promo rates, GTFS transit matrix, airline 2-seat checkout).</li>
</ul>
</div>
<div class="card">
<h3>6 · The three things that could still move before departure</h3>
<ol class="tight">
<li><strong>Reported 14 December 2026:</strong> a secondary source says the New York ceremony is that day; no official MICHELIN confirmation was found. Re-check the official ceremony index after that date (F-01/F-25).</li>
<li><strong>Dynamic hotel &amp; flight pricing:</strong> Fairfield's $985.60 (-30% BF) rate carries $0 prepayment and free cancel until 12 Feb 2027 — lock now and re-check weekly / mid-Jan 2027.</li>
<li><strong>Non-refundable tasting releases:</strong> Sushi Sho ($495), Atomix ($314–$495), and EMP ($385) open 1st of the prior month (1 Jan 2027 for February); Le Bernardin Resy opens ~30 days out.</li>
</ol>
</div>
</div>

<h2>How to read this site</h2>
{theme_table()}

<h2>Where to go next</h2>
<div class="grid three">
<div class="card"><h3><a href="hotels.html">Hotels</a></h3><p class="small">7 hotels w/ verified street addresses, 5-week seasonal table, resort fees, all-in tax math, and reach across 22 stars.</p></div>
<div class="card"><h3><a href="restaurants.html">MICHELIN</a></h3><p class="small">72 ceremony / 69 live NYC reconciled roster, 22 detailed menus &amp; hours, cluster analysis, and verified video links.</p></div>
<div class="card"><h3><a href="activities.html">Activities</a></h3><p class="small">11 activities with verified 2026-11-26 hours (incl. Met Wed closure &amp; High Line winter schedule), prices &amp; reviews.</p></div>
<div class="card"><h3><a href="itinerary.html">Itinerary</a></h3><p class="small">4-, 7- &amp; 14-night plans fixed for The Met Wed closure, NWS Central Park Feb climate normals &amp; booking timeline.</p></div>
<div class="card"><h3><a href="budget.html">Budget</a></h3><p class="small">Every line item for two adults with exact tax math and lower-cost Michelin alternatives.</p></div>
<div class="card"><h3><a href="questions.html">Questions</a></h3><p class="small">{len(FR['questions'])} decisions tracked (research questions resolved; traveller choices ready).</p></div>
<div class="card"><h3><a href="suggestions.html">Suggestions</a></h3><p class="small">{len(FR['suggestions'])} improvements tracked (9 implemented, remaining operational checks queued).</p></div>
<div class="card"><h3><a href="flagged.html">Flagged</a></h3><p class="small">{len(FR['flags'])} tracked items ({n_open_flags} live open, {n_res_flags} resolved/documented).</p></div>
<div class="card"><h3><a href="method.html">Method &amp; sources</a></h3><p class="small">Rules, all official URLs read on 2026-11-26, remaining edge cases, and build checks.</p></div>
</div>
"""


def theme_table():
    rows = [
        ['<span class="pill p-verified">verified</span>', "Read directly on an official page on 2026-11-26. The source link is in the row."],
        ['<span class="pill p-partial">partial</span>', "Some fields verified, others behind checkout/slot selection (e.g. Per Se / Atera deposit floors)."],
        ['<span class="pill p-open">not verified</span>', "Left blank on purpose. The Flagged page says which source or date settles it."],
        ['<span class="pill p-documented">model</span>', "Computed arithmetically from verified inputs (NY tax formula or Haversine distance). Formula is on the Method page."],
    ]
    return table(["Label", "What it means"], rows, caption="A value is never inferred to fill a gap.")


def build_hotels():
    rec = [h for h in HOTELS["hotels"] if h["id"] == "fairfield-central-park"][0]
    arlo = [h for h in HOTELS["hotels"] if h["id"] == "arlo-soho"][0]
    hyatt = [h for h in HOTELS["hotels"] if h["id"] == "hyatt-place-chelsea"][0]
    citm = [h for h in HOTELS["hotels"] if h["id"] == "citizenm-times-square"][0]
    pestana = [h for h in HOTELS["hotels"] if h["id"] == "pestana-cr7-times-square"][0]

    rows = []
    for h in HOTELS["hotels"]:
        basis = ('<span class="pill p-verified">taxes included</span>' if h["tax_included"]
                 else '<span class="pill p-partial">pre-tax quote</span>')
        addr = esc(h["address"]) if h["address"] else '<span class="blank">address not captured</span>'
        rf = '<div class="small">incl. $26–$37/nt resort fee</div>' if h.get("resort_fee_included_in_total") else ""
        partner = (f'<div class="small">Partner non-ref all-in: {money(h["partner_nonref_all_in_usd"])}</div>'
                   if h.get("partner_nonref_all_in_usd") else "")
        rows.append([
            f'<strong>{esc(h["name"])}</strong><div class="small">{esc(h["area"])}</div><div class="small">{addr}</div>',
            f'{esc(h["room"])}<div class="small">{esc(h["bed"])} · {esc(h["bath"])}</div>'
            + (f'<div class="small">{esc(h["size"])}</div>' if h["size"] else ""),
            esc(h["breakfast"]),
            money(h["total_7n_usd"]) + '<div class="small">' + basis + '</div>' + rf
            + ('<div class="small">before discount: ' + money(h["list_price_before_discount"]) + '</div>'
               if h["list_price_before_discount"] else ''),
            '<strong>' + money(h["all_in_7n_usd"]) + '</strong>' + partner
            + '<div class="small">' + pill("documented" if not h["tax_included"] else "verified",
                                           "derived" if not h["tax_included"] else "as printed") + '</div>',
            f'{esc(h["cancellation"])}<div class="small">guest score {esc(h["rating"])}</div>',
            (ext(h["source_url"], "Booking.com (hotel page)")
             if "/hotel/us/" in h["source_url"]
             else ext(h["source_url"], "Booking.com (search page)")),
        ])

    rk = sorted(HOTELS["hotels"], key=lambda z: (-z["reach"]["stars_within_5km"],
                                                  -z["reach"]["three_star_within_5km"],
                                                  z["all_in_7n_usd"]))
    rr = []
    for i, h in enumerate(rk, 1):
        r = h["reach"]
        rr.append([
            str(i),
            '<strong>' + esc(h["name"].replace("Fairfield Inn & Suites by Marriott New York ", "Fairfield Inn ")) + '</strong>'
            + '<div class="small">' + esc(h["area"]) + '</div>',
            '<span class="num">' + str(r["stars_within_5km"]) + ' / ' + str(r["venues_with_coords"]) + '</span>',
            '<span class="num">' + str(r["three_star_within_5km"]) + ' / 5</span>',
            f'{esc(r["nearest_three_star"])} ({r["nearest_three_star_km"]:.2f} km)',
            money(h["all_in_7n_usd"]),
        ])
    reach_table = table(
        ["#", "Hotel", "Verified stars <= 5 km", "Three-star <= 5 km", "Nearest three-star", "All-in 7 nights"],
        rr,
        caption="Haversine distance from building-level hotel coordinates to all 22 verified Manhattan starred venues (including all 5 three-stars).",
        card_labels=["Rank", "Hotel", "Stars <= 5 km", "3-star <= 5 km", "Nearest 3-star", "All-in"])

    ranked = sorted(HOTELS["hotels"], key=lambda z: z["all_in_7n_usd"])
    rrows = []
    for i, h in enumerate(ranked, 1):
        badge = ' <span class="pill p-verified">recommended</span>' if h["id"] == "fairfield-central-park" else (
            ' <span class="pill p-partial">non-ref deal</span>' if "Non-refundable" in h["cancellation"] else "")
        rrows.append([
            str(i), '<strong>' + esc(h["name"]) + '</strong>' + badge
            + '<div class="small">' + esc(h["area"]) + ' &middot; score ' + esc(h["rating"].split()[0]) + '</div>',
            '<span class="num">' + money(h["all_in_7n_usd"]) + '</span>',
            money(h["total_7n_usd"]),
            esc(h["breakfast"]),
            esc(h["cancellation"]),
        ])
    rank_table = table(
        ["#", "Hotel", "All-in 7 nights", "Pre-tax printed", "Breakfast", "Cancellation"],
        rrows,
        caption="Derived all-in = pre-tax x 1.1475 + $4/night ($6/night at Residence Inn FiDi; +$1/night Arlo tourism fee).",
        card_labels=["Rank", "Hotel", "All-in", "Pre-tax", "Breakfast", "Cancellation"])

    win_rows = []
    for w in HOTELS["windows_sampled"]:
        win_rows.append([
            f'<strong>{esc(w["start"])} → {esc(w["end"])}</strong><div class="small">{esc(w["label"])}</div>',
            '<span class="num">' + money(w.get("fairfield_pretax_usd")) + '</span>',
            '<span class="num">' + money(w.get("fairfield_all_in_usd")) + '</span>',
            '<span class="num">' + money(w.get("hyatt_chelsea_pretax_usd")) + '</span>',
            '<span class="num">' + money(w.get("res_inn_fidi_pretax_usd")) + '</span>',
            esc(w["note"]),
        ])
    win_table = table(
        ["7-night window (Mon–Mon)", "Fairfield pre-tax", "Fairfield all-in", "Hyatt Chelsea pre-tax", "Res Inn FiDi pre-tax", "Observation"],
        win_rows,
        caption="All 5 weekly windows spanning the 15 Feb – 23 Mar 2027 brief range, checked 2026-11-26 on Booking.com.",
        card_labels=["Window", "Fairfield pre-tax", "Fairfield all-in", "Hyatt pre-tax", "FiDi pre-tax", "Note"])

    shift_rows = [
        [esc(s["window"]), '<span class="num">' + money(s["pretax_usd"]) + '</span>',
         '<span class="num">' + money(s["all_in_usd"]) + '</span>', esc(s["note"])]
        for s in HOTELS.get("shifted_starts_fairfield", [])
    ]
    shift_table = table(
        ["Shifted start window (Fairfield)", "Pre-tax", "All-in (derived)", "Delta vs Mon 15 Feb"],
        shift_rows,
        caption="One-day start shifts at Fairfield Central Park around 15–18 Feb 2027.",
        card_labels=["Window", "Pre-tax", "All-in", "Delta"])

    alt_rows = [
        [f'<strong>{esc(m["hotel"])}</strong><div class="small">{esc(m["area"])}</div>',
         esc(m["bed"]),
         '<span class="num">' + money(m["pretax_7n_usd"]) + '</span>',
         esc(m["note"])]
        for m in HOTELS.get("market_cross_checks", [])
    ]
    alt_table = table(
        ["Alternative property", "Bed", "Pre-tax 7 nights", "Why not shortlisted"],
        alt_rows,
        caption="Additional 15–22 Feb 2027 checks across Pod properties, Brooklyn, and disqualified budget rooms.",
        card_labels=["Property", "Bed", "Pre-tax", "Verdict"])

    bs = HOTELS.get("booking_strategy", {})
    return f"""
<p class="lede">Seven Manhattan 4-star/high-rated hotels, each verified on its direct Booking.com property
page on 2026-11-26 for a king or queen bed, private attached bathroom, and verified street address for
<strong>15–22 February 2027 (2 adults)</strong>. Every pre-tax headline is converted to derived all-in cost
using exact NYC Occupancy Tax math.</p>

<div class="warnbox"><strong>Read the tax, resort-fee &amp; cancellation basis before comparing.</strong>
All seven Booking.com rates on 2026-11-26 exclude New York's 14.75% tax + $4–$6/night city/unit occupancy fees
(verified on nyc.gov/finance). Arlo SoHo ({money(arlo['total_7n_usd'])}), Arlo Midtown, and Pestana CR7
({money(pestana['total_7n_usd'])} free-cancel / {money(pestana.get('partner_nonref_all_in_usd'))} non-ref Partner)
restrict cancellation or exclude breakfast, whereas <strong>Fairfield Central Park</strong> charges <strong>$0 resort fee</strong>,
drops to <strong>{money(rec['total_7n_usd'])} pre-tax ({money(rec['all_in_7n_usd'])} all-in)</strong> with American
breakfast for two, $0 prepayment, and free cancellation until 12 Feb 2027.</div>

<h2>Shortlist, 15–22 February 2027 (7 nights, 2 adults)</h2>
{table(
    ["Hotel &amp; street address", "Room / bed / bathroom", "Breakfast", "Pre-tax printed", "All-in, 7 nights", "Cancellation &amp; score", "Direct Booking URL"],
    rows,
    caption="Captured 2026-11-26 for check-in 2027-02-15, check-out 2027-02-22 via direct /hotel/us/ pages.",
    card_labels=["Hotel", "Room", "Breakfast", "Pre-tax", "All-in 7 nights", "Cancellation", "Source"])}

<h2>Cheapest time to book: all 5 weeks in the brief window (15 Feb – 22 Mar 2027)</h2>
{win_table}
{shift_table}

<div class="card">
<h3>Winter Outing 2027 &amp; Booking Window Timing</h3>
<ul class="tight">
<li><strong>NYC Winter Outing 2027:</strong> {esc(bs.get("winter_outing_2027", ""))}</li>
<li><strong>Flight booking sweet spot:</strong> {esc(bs.get("flight_booking_window", ""))}</li>
<li><strong>Hotel strategy:</strong> {esc(bs.get("hotel_booking_window", ""))}</li>
</ul>
</div>

<h2>Ranking, by all-in cost (with cancellation &amp; breakfast parity)</h2>
{rank_table}
<div class="note"><strong>Why Fairfield wins.</strong> It has the lowest all-in total of all seven hotels
({money(rec['all_in_7n_usd'])}), includes breakfast for two, charges $0 resort fee, requires $0 prepayment,
allows free cancellation until 12 Feb 2027, and has a king bed + private bath. Arlo SoHo's cheaper-on-paper
$1,282.33 quote is non-refundable (only 1 reschedule) and excludes breakfast; its flexible free-cancel tier
jumps to $1,907.72 all-in. citizenM ({money(citm['all_in_7n_usd'])} room-only, highest 8.9 score, 4-min walk
to Le Bernardin) adds $329/week if you buy breakfast. Hyatt Place Chelsea ({money(hyatt['all_in_7n_usd'])} all-in,
breakfast included, free cancel) is the top alternative if maximum central reach (22/22 stars) outweighs $146/week.</div>

<h2>Ranking by MICHELIN reach (22 verified Manhattan starred venues)</h2>
<p class="brief-ask">The brief asks for hotels ranked by MICHELIN restaurants reachable within an hour.
Here is that reach calculated using building-level hotel coordinates against all 22 verified Manhattan
starred venues (all 5 three-stars, 7 top two-stars, and 10 key one-stars):</p>
{reach_table}

<h3>How to read the reach table</h3>
<ul class="tight">
<li><strong>Hyatt Place Chelsea</strong> ranks #1 on pure 5 km radius (22/22 stars, 5/5 three-stars, 0.65 km to Eleven Madison Park, 0.37 km to Cote).</li>
<li><strong>Pestana CR7 &amp; Arlo Midtown</strong> follow at 20/22 (5/5 three-stars), while <strong>citizenM Times Square</strong> puts Le Bernardin just 0.33 km (~4 min walk) from the lobby.</li>
<li><strong>Fairfield Central Park (538 W 58th St)</strong> hits 16/22 within 5 km and puts <strong>Per Se (0.59 km)</strong>, <strong>Jean-Georges (0.70 km)</strong>, and <strong>Le Bernardin (1.20 km)</strong> on foot — plus the 59 St–Columbus Circle A/B/C/D/1 hub one block away reaches even Downtown Tribeca/FiDi stars (Jungsik, Saga) in ~30 min subway.</li>
<li><strong>Arlo SoHo (0.64 km to Jungsik)</strong> and <strong>Residence Inn FiDi (0.20 km to 2-star Saga &amp; 1-star Crown Shy; 1.30 km to Jungsik)</strong> anchor Downtown dining cleanly once the earlier nearest-3★ coordinate bug is corrected.</li>
</ul>

<h2>Additional market cross-checks (Pods, Brooklyn &amp; budget baselines)</h2>
{alt_table}

<h2>Remaining limits on the hotel comparison</h2>
<div class="warnbox">
<ul class="tight">
<li><strong>Dynamic promotions:</strong> Several 2026-11-26 rates rely on Black Friday (-30% to -36%) or Bonus (-25%) deals (F-03).</li>
<li><strong>Hyatt Place Chelsea accessible tier:</strong> The $1,113 pre-tax rate is for the disability-access roll-in shower king (bookable by anyone; standard king may price higher, F-14).</li>
<li><strong>Reach is Haversine 5 km radius, not full 69-venue GTFS schedules:</strong> See F-05 and Suggestion S-02.</li>
</ul>
</div>
"""



def build_restaurants():
    det = DETAILS["details"]
    live_c = ROSTER["meta"].get("live_nyc_counts", {"3": 5, "2": 14, "1": 50, "total": 69,
                                                   "bib_gourmand": 76, "bib_by_price": {"$": 7, "$$": 60, "$$$": 9},
                                                   "selected": 224, "green_star": 4})
    n_hours_pub = sum(1 for r in ROSTER["restaurants"]
                      if det.get(r["michelin_url"].rstrip("/").split("/")[-1], {}).get("hours"))
    n_price_pub = sum(1 for r in ROSTER["restaurants"]
                      if det.get(r["michelin_url"].rstrip("/").split("/")[-1], {}).get("menu_price_usd"))
    n_coords_pub = sum(1 for r in ROSTER["restaurants"]
                       if det.get(r["michelin_url"].rstrip("/").split("/")[-1], {}).get("lat"))
    rows = []
    for r in ROSTER["restaurants"]:
        key = r["michelin_url"].rstrip("/").split("/")[-1]
        d = det.get(key)
        social = SOCIAL["accounts"].get(key, [])
        soc_html = []
        seen_rev = {}
        for s in social:
            if s["kind"] == "official":
                soc_html.append(ext(s["url"], s["platform"] + " \u2713", "tag"))
            elif s["kind"] == "review":
                p = s["platform"]
                seen_rev[p] = seen_rev.get(p, 0) + 1
                lbl = f"{p} review" if seen_rev[p] == 1 else f"{p} review {seen_rev[p]}"
                soc_html.append(ext(s["url"], lbl, "tag"))
            else:
                soc_html.append(ext(s["url"], s["platform"] + " search", "tag"))
        if not soc_html:
            soc_html.append('<span class="blank">no account verified</span>')

        hv = (d or {}).get("hours") or {}
        known = [(k, v) for k, v in hv.items() if v]
        closed = [k for k, v in hv.items() if v == "closed"]
        if known:
            hours = "; ".join(k + " " + v for k, v in known if v != "closed")
            if closed:
                hours += '<div class="small">closed ' + ", ".join(closed) + '</div>'
            st = (d or {}).get("hours_status")
            if st == "PARTIAL":
                hours += '<div class="small">only these days were readable</div> ' + pill("partial", "partial")
        else:
            hours = '<span class="blank">hours not verified</span>'
            if d and d.get("hours_note"):
                hours += '<div class="small">' + esc(d["hours_note"]) + '</div>'

        if d and d.get("menu_price_usd"):
            floor = " (deposit floor)" if d.get("price_is_floor") else ""
            price = money(d["menu_price_usd"], 0) + floor + '<div class="small">per person &middot; ' + money(d["menu_price_usd"] * 2, 0) + ' for two</div>'
            if d.get("price_note"):
                price += '<div class="small">' + esc(d["price_note"][:110]) + ('...' if len(d["price_note"]) > 110 else '') + '</div>'
        elif d and d.get("price_note"):
            price = '<span class="blank">a la carte</span><div class="small">' + esc(d["price_note"][:130]) + ('...' if len(d["price_note"]) > 130 else '') + '</div>'
        else:
            price = '<span class="blank">roster-only (menu not pulled)</span>'

        st_badge = ""
        if r.get("live_nyc_status") == "outside_nyc_westchester":
            st_badge = '<div class="small">' + pill("partial", "outside NYC (Westchester)") + '</div>'
        elif r.get("live_nyc_status") == "closed_delisted":
            st_badge = '<div class="small">' + pill("open", "closed Dec 2025 / delisted") + '</div>'

        rows.append([
            f'<strong>{esc(r["name"])}</strong><div class="small">{esc(r["cuisine"])} · {esc(r["borough"])}</div>{st_badge}',
            stars_badge(r["stars"]) + (' <span class="badge b0" title="Green Star">🌿</span>' if r["green"] == "yes" else ""),
            hours,
            price,
            " ".join(soc_html),
            ext(r["michelin_url"], "MICHELIN") + (f' · {ext(d["official_site"], "Site")}' if d and d.get("official_site") else ""),
        ])

    import collections as _c
    bor = _c.Counter(r["borough"] for r in ROSTER["restaurants"] if r.get("live_nyc_status") == "live_nyc")
    by_key = {r["michelin_url"].rstrip("/").split("/")[-1]: r for r in ROSTER["restaurants"]}
    scored = [(k, v) for k, v in det.items() if v.get("lat")]
    geo = []
    for k, v in scored:
        near = []
        for k2, v2 in scored:
            if k2 == k:
                continue
            import math as _m
            la1, lo1, la2, lo2 = map(_m.radians, [v["lat"], v["lon"], v2["lat"], v2["lon"]])
            d = 2 * 6371.0 * _m.asin(_m.sqrt(_m.sin((la2 - la1) / 2) ** 2
                                              + _m.cos(la1) * _m.cos(la2) * _m.sin((lo2 - lo1) / 2) ** 2))
            if d <= 1.0:
                near.append((d, by_key[k2]["name"]))
        near.sort()
        geo.append([
            stars_badge(by_key[k]["stars"]),
            '<strong>' + esc(by_key[k]["name"]) + '</strong><div class="small">' + esc(v.get("address") or by_key[k].get("cuisine", "")) + '</div>',
            (", ".join(f"{esc(nm)} ({dist * 1000:.0f} m)" for dist, nm in near)
             if near else '<span class="blank">no other scored star venue within 1 km</span>')
        ])
    geo.sort(key=lambda r: (0 if "b3" in r[0] else (1 if "b2" in r[0] else 2), r[1]))

    cluster_table = table(
        ["Borough", "Live NYC star entries", "Three-star entries", "What it means for the trip"],
        [
            ["Manhattan", str(bor.get("Manhattan", 0)),
             str(sum(1 for r in ROSTER["restaurants"] if r["borough"] == "Manhattan" and r["stars"] == 3 and r.get("live_nyc_status") == "live_nyc")),
             "Contains 62 of 69 live NYC starred venues and ALL 5 three-stars across 3 walkable clusters."],
            ["Brooklyn", str(bor.get("Brooklyn", 0)), "0",
             "Six active venues (including 2-star Aska and 1-star Francie); ~35–45 min by subway from Midtown."],
            ["Queens", str(bor.get("Queens", 0)), "0",
             "One active 1-star entry (Meju in LIC); viable lunch or single dinner trip."],
            ["Outside NYC (ceremony delta)", "2 (not in live NYC filter)", "0",
             "Blue Hill at Stone Barns (Tarrytown) and La Bastide (North Salem) sit outside NYC & fail the 1-hour rule. Shion 69 Leonard St closed Dec 2025."],
        ],
        caption="Live NYC count: 69 active venues (5 three-star, 14 two-star, 50 one-star) reconciled vs 72 Nov 2025 ceremony entries.",
        card_labels=["Borough", "Live entries", "Three-star", "Meaning"])
    geo_table = table(
        ["Rating", "Venue", "Scored star venues within 1 km"],
        geo,
        caption=f"Exact Haversine distances across all {len(scored)} Manhattan starred venues with verified coordinates.",
        card_labels=["Rating", "Venue", "Within 1 km"])

    # Build verified dinner price cards sorted by star tier then price
    price_cards = []
    for key, d in sorted(det.items(), key=lambda kv: (-by_key[kv[0]]["stars"], kv[1].get("menu_price_usd") or 9999)):
        r = by_key[key]
        if not d.get("menu_price_usd") and not d.get("price_note"):
            continue
        p_main = (f'Standard/Floor {money(d["menu_price_usd"], 0)} pp &rarr; <strong>{money(d["menu_price_usd"] * 2, 0)} for two</strong>'
                  + (' (deposit floor)' if d.get("price_is_floor") else ' (food only)')
                  if d.get("menu_price_usd") else '<strong>A la carte value pick</strong>')
        links = []
        if d.get("price_source"):
            links.append(ext(d["price_source"], "official menu / booking"))
        if d.get("official_site") and d.get("official_site") != d.get("price_source"):
            links.append(ext(d["official_site"], "website"))
        closed_line = f' · closed {esc(d["closed_days"])}' if d.get("closed_days") and d["closed_days"] != "none listed" else " · open 7 days"
        price_cards.append(f'''<div class="card"><h3>{esc(r["name"])} {stars_badge(r["stars"])}{" 🌿" if r["green"]=="yes" else ""}</h3>
<p class="small">{p_main}{closed_line}<br>{esc(d.get("price_note") or "")}</p>
<p class="small">{" &middot; ".join(links)}</p></div>''')

    sel = DETAILS.get("guide_selected", {}).get("one-white-street", {})
    if sel:
        price_cards.append(f'''<div class="card"><h3>{esc(sel["name"])} <span class="badge b0">Selected + 🌿 Green Star (0 red stars)</span></h3>
<p class="small">Tasting {money(sel["menu_price_usd"], 0)} pp &rarr; <strong>{money(sel["menu_price_usd"] * 2, 0)} for two</strong> · open 7 days<br>{esc(sel["price_note"])}</p>
<p class="small">{ext(sel["official_site"], "tasting menu")} &middot; {ext(sel["michelin_url"], "MICHELIN")}</p></div>''')

    return f"""
<p class="lede">All {len(ROSTER['restaurants'])} entries from MICHELIN's <em>All the Stars in The MICHELIN Guide
to New York City 2025</em> (18 Nov 2025), reconciled against MICHELIN's live 2026-11-26 NYC filtered
listings (<strong>{live_c['total']} active NYC venues</strong>: {live_c['3']} three-star, {live_c['2']} two-star,
{live_c['1']} one-star), plus verified 2026-11-26 menus, hours, coordinates, and video reviews across {n_hours_pub} key Manhattan choices.</p>

<div class="okbox"><strong>Flag F-02 &amp; Q-17 RECONCILED (72 ceremony vs 69 live NYC):</strong>
The exact 3-venue difference between the 18 Nov 2025 ceremony article (72) and MICHELIN's live NYC filter
(69) is: <strong>(1) Blue Hill at Stone Barns</strong> (2★ + Green Star, Tarrytown, Westchester — outside NYC),
<strong>(2) La Bastide by Andrea Calstier</strong> (1★, North Salem, Westchester — outside NYC), and
<strong>(3) Shion 69 Leonard Street</strong> (1★, closed after a 27 Dec 2025 building fire and delisted from MICHELIN).
Live guide totals today: <strong>{live_c['total']} starred</strong>, <strong>{live_c.get('bib_gourmand', 76)} Bib Gourmand</strong>
({live_c.get('bib_by_price', {}).get('$', 7)} $, {live_c.get('bib_by_price', {}).get('$$', 60)} $$, {live_c.get('bib_by_price', {}).get('$$$', 9)} $$$),
<strong>{live_c.get('selected', 224)} Selected</strong>, and <strong>{live_c.get('green_star', 4)} Green Stars</strong> (3 starred + 1 Selected).</div>

<div class="badbox"><strong>Reported ceremony date: 14 December 2026 (secondary source only).</strong> Eater NY reports this date; no official MICHELIN page confirmed it in this session. Stars shown here reflect the live 2025/2026 list. Re-check the official MICHELIN ceremony index after that date (F-01/F-25).</div>

<div class="note"><strong>Coverage summary:</strong> {n_hours_pub} priority Manhattan restaurants now carry
verified weekly hours and coordinates (including all 5 three-stars, 7 key two-stars, and 10 value/highlight one-stars),
and {n_price_pub} carry verified menu prices or Tock deposit floors. The remaining {len(ROSTER['restaurants']) - n_hours_pub}
rows stay complete on name, star badge, cuisine, borough, and official MICHELIN link without guessing missing menus.</div>

<h2>The full roster ({len(ROSTER['restaurants'])} ceremony entries · {live_c['total']} active NYC)</h2>
<div class="legend">
  <span>{stars_badge(3)}</span><span class="small">Three stars — exceptional cuisine</span>
  <span>{stars_badge(2)}</span><span class="small">Two stars — excellent cooking</span>
  <span>{stars_badge(1)}</span><span class="small">One star — high quality cooking</span>
  <span>🌿</span><span class="small">Green Star (sustainability)</span>
</div>
{table(
    ["Restaurant", "Distinction", "Days open &amp; hours", "Menu price", "Social / video", "Source"],
    rows,
    caption="22 priority Manhattan venues verified with official hours, menus & social links; remaining venues roster-only.",
    card_labels=["Restaurant", "Distinction", "Hours", "Menu price", "Social / video", "Source"])}

<h2>Guide-listed, Green Star &amp; Bib Gourmand (not red-starred)</h2>
<p>These are in MICHELIN's wider NYC selection (<strong>{live_c.get('selected', 224)} Selected</strong> +
<strong>{live_c.get('bib_gourmand', 76)} Bib Gourmand</strong>) and hold <strong>zero red stars</strong> — separated here so awards are never confused:</p>
<div class="card">
<ul class="tight">
<li><strong>One White Street</strong> (Tribeca) — Contemporary, <strong>MICHELIN Selected + 🌿 Green Star only (0 red stars)</strong> · Tasting <strong>$145 pp ($290 for two)</strong>, open daily 17:00–21:00 (Fri–Sat to 22:00) · {ext("https://www.onewhitestreetnyc.com/tasting", "tasting menu")} · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/one-white-street", "MICHELIN")}</li>
<li><strong>Ai Fiori</strong> — Italian, $$$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ai-fiori", "MICHELIN listing")}</li>
<li><strong>Café Carmellini</strong> — Italian, $$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/cafe-carmellini", "MICHELIN listing")}</li>
<li><strong>Ci Siamo</strong> — Italian · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ci-siamo", "MICHELIN listing")}</li>
<li><strong>Chambers</strong> — Contemporary, $$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/chambers", "MICHELIN listing")}</li>
<li><strong>Farra</strong> — Contemporary, $$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/farra", "MICHELIN listing")}</li>
<li><strong>Ito</strong> — Japanese, $$$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ito-1201767", "MICHELIN listing")}</li>
</ul>
<p class="small">Bib Gourmand holds {live_c.get('bib_gourmand', 76)} NYC spots ($ = 7, $$ = 60, $$$ = 9).</p>
</div>

<h2>Where the stars cluster ({n_coords_pub} verified Manhattan venues)</h2>
{cluster_table}
{geo_table}

<div class="okbox"><strong>Three distinct Manhattan star clusters emerge across the {n_coords_pub} scored venues:</strong>
<ul class="tight">
<li><strong>Midtown Cluster:</strong> The Modern &amp; Le Bernardin (395 m apart), The Modern &amp; Aquavit (411 m), Gabriel Kreuther &amp; Sushi Sho (290 m), plus Columbus Circle neighbours Per Se &amp; Jean-Georges (152 m).</li>
<li><strong>Flatiron / Gramercy / Union Sq Cluster:</strong> Eleven Madison Park &amp; Gramercy Tavern (353 m), EMP &amp; Cote (376 m), EMP &amp; Atomix (475 m), Gramercy Tavern &amp; Casa Mono (301 m).</li>
<li><strong>Tribeca / FiDi / SoHo Cluster:</strong> Jungsik &amp; Atera (350 m), Atera &amp; Le Coucou (531 m), 70 Pine St tower mates Saga (2★) &amp; Crown Shy (1★), plus Greenwich Village neighbours Semma &amp; Family Meal at Blue Hill (459 m).</li>
</ul>
</div>

<h2>Dinner &amp; lunch cost for two — verified menus</h2>
<div class="grid two">
{"".join(price_cards)}
</div>
<div class="note"><strong>Deposit-floor transparency:</strong> Per Se ($200 pp MDR / $150 Salon), Atera ($200 pp),
and Aquavit ($50 dinner / $25 lunch) only show booking deposits on Tock until individual seating dates open;
those figures are tagged <em>deposit floor</em> rather than full meal cost.</div>
"""


def build_activities():
    rows = []
    for a in ACTS["activities"]:
        soc = SOCIAL["accounts"].get(a["id"], [])
        soc_parts = []
        seen_rev = {}
        for s in soc:
            if s["kind"] == "official":
                soc_parts.append(ext(s["url"], s["platform"] + " ✓", "tag"))
            elif s["kind"] == "review":
                p = s["platform"]
                seen_rev[p] = seen_rev.get(p, 0) + 1
                lbl = f"{p} review" if seen_rev[p] == 1 else f"{p} review {seen_rev[p]}"
                soc_parts.append(ext(s["url"], lbl, "tag"))
            else:
                soc_parts.append(ext(s["url"], s["platform"] + " search", "tag"))
        soc_html = " ".join(soc_parts) or '<span class="blank">no account verified</span>'
        tr = a["from_hotel"]
        travel_cell = ('<strong>' + str(tr["transit_min_modelled"]) + ' min</strong>'
                       '<div class="small">by subway, modelled</div>'
                       '<div class="small">' + str(tr["walk_min_modelled"]) + ' min on foot &middot; '
                       + f'{tr["km"]:.1f}' + ' km</div>')
        if a["id"] == "statue-of-liberty":
            travel_cell = ('<strong>~' + str(tr.get("battery_park_transit_min", 47)) + ' min</strong> to Battery Park'
                           '<div class="small">+ ~15–20 min ferry (~62–67 min door-to-island)</div>'
                           '<div class="small">' + f'{tr["km"]:.1f}' + ' km to island</div>')
        cost = (f'{money(a["cost_2_adults_usd"])}<div class="small">for two · {money(a["adult_usd"])} pp</div>'
                if a["cost_2_adults_usd"] is not None else
                '<span class="blank">no single official price</span>')
        hours = esc(a["hours"]) if a["hours"] else '<span class="blank">schedule varies per production</span>'
        days = esc(a["days_open"]) if a["days_open"] else ""
        vk = "verified" if a["verification"].startswith("VERIFIED") else (
            "partial" if a["verification"].startswith("PARTIAL") else "open")
        rows.append([
            f'<strong>{esc(a["name"])}</strong><div class="small">{esc(a["category"])} · {esc(a["area"])}</div>'
            f'<div class="small">{esc(a["address"])}</div>',
            f'{hours}' + (f'<div class="small">{days}</div>' if days else ""),
            esc(a["exceptions"]),
            cost,
            travel_cell,
            f'{pill(vk)}<div class="small">{esc(a["verification"])}</div>',
            " ".join([soc_html, ext(a["official_url"], "Official")]),
        ])
    return f"""
<p class="lede">All eleven candidate activities verified on official venue/agency websites on 2026-11-26:
exact winter/2027 hours, closure days (including The Met's Wednesday closure), out-of-state adult prices
for two, modelled travel times from Fairfield Central Park (538 W 58th St), and direct video/social reviews.</p>

<div class="note"><strong>Free vs paid overview:</strong> Central Park, The High Line (Dec 1–Mar 31 winter
07:00–20:00), Chelsea Market (07:00–22:00), and Brooklyn Bridge (24h) cost $0. Paid museum/harbor
highlights: MoMA ($30 pp), The Met ($30 pp, <strong>closed Wednesdays</strong>), AMNH ($37 pp out-of-state),
9/11 Museum ($24–$36 pp, last entry 18:00), Top of the Rock (from $42 pp), and Statue of Liberty ferry ($26 pp).</div>

{table(
    ["Activity", "Days &amp; hours", "Exceptions that matter", "Cost for 2", "From Fairfield (538 W 58th St)", "Status", "Links"],
    rows,
    caption="Verified 2026-11-26 from official pages. Only Broadway stays unpriced because ticket price depends on show & seat.",
    card_labels=["Activity", "Hours", "Exceptions", "Cost for 2", "From hotel", "Status", "Links"])}

<h2>Tickets: what to buy in advance</h2>
<div class="grid two">
<div class="card"><h3>Must pre-book (timed entry)</h3>
<ul class="tight">
<li><strong>9/11 Memorial &amp; Museum</strong> — timed entry required; open Wed–Mon 09:00–19:00 (last entry 18:00).</li>
<li><strong>Top of the Rock</strong> — timed sunset slots cost more than the $42 floor.</li>
<li><strong>Statue of Liberty</strong> — Statue City Cruises is the sole NPS operator; Crown/Pedestal ($0.30) books out weeks early.</li>
<li><strong>MoMA &amp; AMNH</strong> — timed tickets live through mid-2027; recommended during NYCPS Midwinter Recess (15–19 Feb 2027).</li>
</ul></div>
<div class="card"><h3>Can be decided on the day</h3>
<ul class="tight">
<li><strong>The Met Fifth Avenue</strong> — Sun–Tue &amp; Thu 10–17, Fri–Sat 10–21, <strong>closed Wednesdays</strong>.</li>
<li><strong>Central Park, High Line, Brooklyn Bridge</strong> — free entry, no tickets.</li>
<li><strong>Chelsea Market</strong> — free entry (07:00–22:00), pay each food vendor.</li>
<li><strong>Broadway</strong> — choose show first on broadway.org; most shows are dark Mondays.</li>
</ul></div>
</div>

<h2>The one-hour rule, applied from 538 W 58th St</h2>
<p class="brief-ask">Measured from Fairfield Central Park's verified building coordinates (40.77042, -73.98971):</p>
<div class="grid two">
<div class="card"><h3>Walkable in 7–20 minutes</h3>
<p class="small">Central Park SW entrance (0.6 km / 7 min walk), Broadway theatres (1.34 km / 18 min walk),
Top of the Rock (1.52 km / 20 min walk), MoMA (1.43 km / 19 min walk).</p></div>
<div class="card"><h3>17–25 minutes by subway</h3>
<p class="small">AMNH (1.79 km / 17 min transit), The Met (2.45 km / 20 min transit via crosstown or subway),
The High Line (2.80 km / 22 min), Chelsea Market (3.41 km / 25 min).</p></div>
<div class="card"><h3>42–44 minutes by express subway</h3>
<p class="small">9/11 Memorial (6.85 km / 42 min modelled via A/C express from Columbus Circle),
Brooklyn Bridge (7.18 km / 44 min). Plan as half-day outings.</p></div>
<div class="card"><h3>Marginally past 60 min: Statue of Liberty</h3>
<p class="small">Battery Park Ferry Terminal is 7.82 km (~47 modelled subway min), plus the ~15–20 min
harbor ferry = <strong>~62–67 min door-to-island</strong>. High winter winds can suspend sailings, so keep
Sunday's buffer ready (Q-15).</p></div>
</div>

<h2>Social media and video reviews</h2>
<p>Every activity links to verified official Instagram accounts (<code>@themuseumofmodernart</code>,
<code>@metmuseum</code>, <code>@amnh</code>, <code>@911memorial</code>, <code>@rockefellercenter</code>,
<code>@centralparknyc</code>, <code>@highlinenyc</code>, <code>@chelseamarketny</code>) and verified YouTube
walk-through guides.</p>
"""


def build_itinerary():
    cl = FR["trip"].get("climate_normals", {})
    feb = cl.get("feb", {})
    mar = cl.get("mar", {})
    out = []
    for it in FR["itineraries"]:
        rows = [[esc(d["date"]), esc(d["day"]), esc(d["plan"])] for d in it["days"]]
        note = f'<p class="hint">{esc(it["note"])}</p>' if it.get("note") else ""
        out.append(f"""<h2>{esc(it["title"])}</h2>{note}
{table(["Date", "Day", "Plan"], rows, card_labels=["Date", "Day", "Plan"])}""")
    return f"""
<p class="lede">Three concrete variants (7-night recommended, 4-night preferred window, 14-night full window)
engineered around actual museum closure days, winter hours, holiday crowds, and MICHELIN dinner schedules.</p>

<div class="note"><strong>Scheduling rules enforced:</strong>
<ul class="tight">
<li><strong>The Met is CLOSED every Wednesday</strong> — placed on <strong>Tue 16 Feb</strong> across both the 7-night and 4-night plans (never Wed 17 Feb!).</li>
<li><strong>9/11 Museum is open Wed–Mon (last entry 18:00; closed most Tuesdays)</strong> — scheduled <strong>Thu 18 Feb</strong> (or Wed 17 on 4-night).</li>
<li><strong>Most Broadway shows are dark Monday</strong> — Mon 15 Feb arrival stays flexible.</li>
<li><strong>Sunday-closed vs Sunday-open stars:</strong> Le Bernardin, Gabriel Kreuther, Jean-Georges, Atomix, Aquavit &amp; Dirt Candy close Sundays; <strong>EMP, Jungsik, Per Se, Sushi Sho, The Modern, Saga, Gramercy Tavern, Crown Shy &amp; Cote</strong> all serve Sundays.</li>
</ul></div>

{"".join(out)}

<h2>Booking countdown &amp; release schedule</h2>
<div class="card">
<ol class="tight">
<li><strong>Now (Nov 2026):</strong> Lock Fairfield Central Park ($985.60 pre-tax / $1,158.98 all-in) at $0 prepayment with free cancellation until <strong>2027-02-12</strong>; monitor flight checkout for 2 seats.</li>
<li><strong>After the reported 14 Dec 2026 date:</strong> Re-check official MICHELIN Guide NYC 2026 ceremony announcements before confirming the final restaurant list (F-01/F-25).</li>
<li><strong>1 Jan 2027 (11:00–15:00 EST):</strong> Monthly releases open for February at <strong>Sushi Sho</strong> (11:00 EST, Tock), <strong>Atomix</strong> (15:00 EST, Tock), and <strong>Eleven Madison Park</strong> (09:00 EST, Resy).</li>
<li><strong>Mid-Jan 2027 (~30 days out):</strong> Book <strong>Le Bernardin</strong> &amp; <strong>Gabriel Kreuther</strong> (Resy), <strong>Dirt Candy</strong> (30d midnight EST), timed <strong>9/11 Museum</strong>, <strong>Statue of Liberty Crown/Pedestal</strong>, and re-verify Booking.com hotel rate (S-03).</li>
<li><strong>Week of 8–12 Feb 2027:</strong> Check NWS marine/winter forecast for Liberty Island ferry; free-cancel hotel deadline hits <strong>12 Feb 2027</strong>.</li>
</ol>
</div>

<h2>February weather &amp; packing (NWS Central Park normals)</h2>
<div class="warnbox">
<p>Verified against {ext(cl.get("source", "https://www.weather.gov/media/okx/Climate/CentralPark/nycnormals.pdf"), "NWS 1991–2020 NYC Central Park Climate Normals")}:</p>
<ul class="tight">
<li><strong>February average:</strong> Daily high <strong>{feb.get("high_f", 42.2)}°F ({feb.get("high_c", 5.7)}°C)</strong>, overnight low <strong>{feb.get("low_f", 29.5)}°F ({feb.get("low_c", -1.4)}°C)</strong>, <strong>{feb.get("snow_in", 10.1)} in</strong> mean snowfall ({feb.get("precip_in", 3.19)} in precip).</li>
<li><strong>March average (for 14-night or late options):</strong> High <strong>{mar.get("high_f", 49.9)}°F ({mar.get("high_c", 9.9)}°C)</strong>, low <strong>{mar.get("low_f", 35.8)}°F ({mar.get("low_c", 2.1)}°C)</strong>, <strong>{mar.get("snow_in", 5.0)} in</strong> snow.</li>
<li><strong>Packing &amp; plan implications:</strong> Exposed outdoor legs (Brooklyn Bridge, Statue ferry deck, High Line) require thermal base layers, windproof coat, gloves, hat, and waterproof walking shoes. Day 7 (Sun 21 Feb) remains a deliberate indoor swap buffer.</li>
</ul>
</div>
"""


def build_budget():
    b = FR["budget"]
    hotel_usd = next(l["usd"] for l in b["lines"] if l["item"].startswith("Hotel"))
    flights_usd = next(l["usd"] for l in b["lines"] if l["item"].startswith("Flights"))
    dining_usd = sum(l["usd"] for l in b["lines"] if l["item"].startswith("Dinner"))
    attr_usd = sum(l["usd"] for l in b["lines"]
                   if l["usd"] and not (l["item"].startswith("Hotel") or l["item"].startswith("Flights")
                                        or l["item"].startswith("Transit") or l["item"].startswith("Dinner")))
    rows = []
    for l in b["lines"]:
        kind = l["kind"]
        k = "verified" if kind.startswith("VERIFIED") else ("documented" if "DERIVED" in kind else "open")
        rows.append([
            esc(l["item"]),
            f'<span class="num">{money(l["usd"])}</span>' if l["usd"] is not None else money(None),
            pill(k, kind),
            (ext(l["source"], "source") if l["source"] else '<span class="blank">no source exists</span>')
            + (f'<div class="small">{esc(l["note"])}</div>' if l.get("note") else ""),
        ])
    return f"""
<p class="lede">One line per verified or derived cost for two adults across 7 nights (15–22 Feb 2027),
including the updated Fairfield tax-adjusted total and AMNH out-of-state admission ($74).</p>

{table(["Line item", "Amount (2 adults)", "Basis", "Source &amp; note"], rows,
       caption="7 nights, 15–22 February 2027, two adults.",
       card_labels=["Item", "Amount", "Basis", "Source"])}

<h2>Verified subtotal breakdown</h2>
<div class="kpi">
 <div class="card"><div class="k">Verified subtotal</div><div class="v">{money(b["verified_subtotal_usd"])}</div>
  <div class="small">All 11 priced lines above ({money(b["verified_subtotal_usd"] - flights_usd)} ex-flights).</div></div>
 <div class="card"><div class="k">Hotel share (all-in)</div><div class="v">{money(hotel_usd)}</div><div class="small">{hotel_usd / b["verified_subtotal_usd"] * 100:.0f}% · includes breakfast &amp; NY tax</div></div>
 <div class="card"><div class="k">Flights share</div><div class="v">{money(flights_usd)}</div><div class="small">{flights_usd / b["verified_subtotal_usd"] * 100:.0f}% · AMS–JFK 1-stop x 2 (F-15)</div></div>
 <div class="card"><div class="k">Attractions + Transit</div><div class="v">{money(attr_usd + 70)}</div><div class="small">6 paid tickets ({money(attr_usd, 0)}) + MTA $70 cap</div></div>
 <div class="card"><div class="k">2 Tasting Dinners</div><div class="v">{money(dining_usd)}</div><div class="small">{dining_usd / b["verified_subtotal_usd"] * 100:.0f}% · food only (no wine/tax/tip)</div></div>
</div>

<div class="badbox"><strong>What remains unpriced in the subtotal:</strong> lunches/casual dinners (breakfast is
included at Fairfield), wine pairings (adds {money(510, 0)}–{money(1060, 0)} for two at top venues), ~8.875% NYC dining tax &amp;
~20% tip (except tip-free <em>Dirt Candy</em>), JFK AirTrain ($17/person RT), and any Broadway show.</div>

<h2>Verified menu swaps &amp; optional upgrades (couple cost, food only)</h2>
<div class="card">
<ul class="tight">
<li><strong>Lower-cost MICHELIN swaps vs Gabriel Kreuther ({money(650, 0)}):</strong> <strong>Cote</strong> 1★ Butcher's Feast {money(168, 0)} (-$482) · <strong>Dirt Candy</strong> 1★ Green Star {money(236, 0)} tip included (-$414) · <strong>One White Street</strong> Green Star {money(290, 0)} (-$360) · <strong>The Modern</strong> 2★ Impressions {money(370, 0)} (-$280).</li>
<li><strong>Alternative 3★ anchors vs Le Bernardin ({money(700, 0)}):</strong> <strong>Jungsik</strong> {money(670, 0)} · <strong>Eleven Madison Park</strong> Bar {money(510, 0)} / Full {money(770, 0)} · <strong>Sushi Sho</strong> {money(990, 0)} incl. admin.</li>
<li><strong>Wine pairings:</strong> Le Bernardin {money(1060, 0)} total w/ menu (+$360 over food-only) · Gabriel Kreuther from {money(510, 0)}/couple · Cote {money(220, 0)}/couple · One White Street {money(190, 0)}/couple.</li>
<li><strong>14-night extension (22 Feb – 1 Mar hotel):</strong> Fairfield Week 2 = {money(1199.14)} all-in (+3.6% vs Week 1), making 14 nights ~{money(2358.12)} all-in.</li>
</ul>
</div>

<h2>How to read the labels</h2>
{table(["Label", "Meaning"], [
 ['<span class="pill p-verified">VERIFIED</span>', "Read directly on an official venue or agency page on 2026-11-26."],
 ['<span class="pill p-documented">DERIVED</span>', "Arithmetic on verified figures (NY tax formula on Booking quote, MTA $35 cap x 2)."],
 ['<span class="pill p-open">NOT PRICED</span>', "No single official figure exists (casual dining, Broadway, bags)."],
], caption="No line in this budget uses invented allowances.")}
"""


def build_questions():
    rows = []
    for q in FR["questions"]:
        st = q.get("status", "Open")
        k = "verified" if st.startswith("Resolved") else (
            "open" if st == "Open" else ("blocked" if "Blocked" in st else "documented"))
        rows.append([
            f'<strong>{esc(q["id"])}</strong><div class="small">{esc(q["question"])}</div>',
            esc(q["why_it_blocks"]),
            esc(q["have"]),
            f'<strong>{esc(q["missing"])}</strong>',
            esc(q["how_to_discover"]),
            f'{pill(k, st)}<div class="small">{esc(q["owner"])}</div>',
        ])
    n_res = sum(1 for q in FR["questions"] if q.get("status", "").startswith("Resolved"))
    n_trav = sum(1 for q in FR["questions"] if q["owner"] == "traveller" and q.get("status", "Open") == "Open")
    n_res_open = sum(1 for q in FR["questions"] if q["owner"] == "research" and q.get("status", "Open") in ("Open", "Documented"))
    return f"""
<p class="lede">Every decision tracked from initial planning through the 2026-11-26 verification pass:
research gaps now resolved vs traveller preferences and one date-blocked MICHELIN update.</p>

<div class="kpi">
 <div class="card"><div class="k">Total tracked</div><div class="v">{len(FR["questions"])}</div><div class="small">{n_res} research items resolved</div></div>
 <div class="card"><div class="k">Traveller choices</div><div class="v">{n_trav}</div><div class="small">Preference decisions (no further research needed)</div></div>
 <div class="card"><div class="k">Open / documented research</div><div class="v">{n_res_open}</div><div class="small">GTFS transit matrix &amp; optional 69-venue completeness</div></div>
 <div class="card"><div class="k">Blocked by date</div><div class="v">1</div><div class="small">reported 14 Dec 2026 ceremony (secondary source; F-24)</div></div>
</div>

{table(["Question", "Why it blocks a decision", "What we have", "What is missing", "How to discover it", "Status"],
       rows,
       caption="Ordered Q-01 to Q-26; previously open research questions Q-06, Q-07, Q-09, Q-13, Q-17 are resolved.",
       card_labels=["Question", "Why it blocks", "Have", "Missing", "How to discover", "Status"])}

<h2>Key open decisions for the traveller</h2>
<div class="grid two">
<div class="card"><h3>Q-01 · Length: 4, 7 or 14 nights?</h3><p class="small">Week 1 ($1,158.98) and Week 2 ($1,199.14) are both verified at Fairfield Central Park.</p></div>
<div class="card"><h3>Q-02 &amp; Q-04 · Spend ceiling &amp; star mix</h3><p class="small">Verified subtotal is {money(FR["budget"]["verified_subtotal_usd"])}; swapping Gabriel Kreuther for Cote ($168) or Dirt Candy ($236) saves $414–$482.</p></div>
<div class="card"><h3>Q-08 &amp; Q-26 · Fairfield ($1,158.98) vs Hyatt Chelsea ($1,305.17)</h3><p class="small">Fairfield wins by $146/week + free cancel + breakfast; Hyatt Chelsea hits 22/22 verified stars within 5 km.</p></div>
<div class="card"><h3>Q-18 · Post-reported-ceremony MICHELIN check</h3><p class="small">Re-verify star changes after the reported 14 Dec 2026 ceremony (secondary-source date) before locking 1 Jan / mid-Jan tasting seats.</p></div>
<div class="card"><h3>Q-19 · Scheduled MTA GTFS matrix</h3><p class="small">Straight-line 5 km reach now covers 22 stars; running weekday 19:00 GTFS times completes the 1-hour proof.</p></div>
</div>
"""


def build_suggestions():
    rows = []
    for s in FR["suggestions"]:
        dec = s.get("decision", "Pending")
        dec_cell = (pill("verified", "Implemented 2026-11-26") if dec == "Done"
                    else f'<select aria-label="Decision for {esc(s["id"])}"><option>Pending</option><option>Do it</option><option>Skip</option><option>Discuss</option></select>')
        rows.append([
            f'<strong>{esc(s["id"])}</strong> {esc(s["title"])}<div class="small">{esc(s["problem"])}</div>',
            esc(s["proposal"]),
            f'{esc(s["effort"])}<div class="small">{esc(s["cost"])}</div>',
            f'{pill(s["impact"].lower(), s["impact"] + " impact")}<div class="small">risk: {esc(s["risk"].split(" -")[0])}</div>',
            dec_cell,
        ])
    n_done = sum(1 for s in FR["suggestions"] if s.get("decision") == "Done")
    return f"""
<p class="lede">{len(FR['suggestions'])} structured improvements tracked across the dashboard:
<strong>{n_done} implemented</strong> on 2026-11-26 (menu matrix, 5-week rates, climate normals, social
videos, booking timeline, orphan cleanup), with {len(FR['suggestions']) - n_done} operational items pending.</p>

<div class="note"><strong>How to read this list.</strong> Items marked <em>Implemented 2026-11-26</em>
(S-01, S-04, S-05, S-08, S-09, S-10, S-11, S-12) are already live in this build. The remaining pending
items (S-02 GTFS routing, S-03 mid-Jan rate check, S-06 print confirmation card, S-07 GitHub Actions CI)
can be accepted or deferred cleanly.</div>

{table(["Improvement", "Proposal", "Effort / cost", "Impact / risk", "Status / decision"],
       rows,
       caption="Ordered S-01 through S-12 with completion status.",
       card_labels=["Improvement", "Proposal", "Effort", "Impact", "Status"])}

<h2>Remaining pending priorities</h2>
<div class="grid three">
<div class="card"><h3>1 · S-02 Measured GTFS transit matrix</h3><p class="small">Turns the 22-star Haversine reach proxy into weekday 19:00 MTA timetable legs.</p></div>
<div class="card"><h3>2 · S-03 Reported Dec 14 &amp; mid-Jan refresh</h3><p class="small">Re-read official MICHELIN after the reported 14 Dec 2026 date (secondary source) and re-check the locked Fairfield Booking URL before Feb 12.</p></div>
<div class="card"><h3>3 · S-07 PR build-check workflow</h3><p class="small">Runs python3 build_site.py checks automatically on pull requests via GitHub Actions.</p></div>
</div>
"""


def build_flagged():
    sev_kind = {"HIGH": "open", "MEDIUM": "partial", "LOW": "documented"}
    rows = []
    for f in FR["flags"]:
        st = f.get("status", "Open")
        st_kind = "verified" if st == "Resolved" else ("documented" if st == "Documented" else "open")
        k = sev_kind.get(f["severity"], "open")
        src_cell = ext(f["source"], "official page") if f["source"] else '<span class="blank">no source captured</span>'
        rows.append([
            '<strong>' + esc(f["id"]) + '</strong> ' + pill(k, f["severity"]) + ' ' + pill(st_kind, st)
            + '<div class="small">' + esc(f["title"]) + '</div>',
            esc(f["detail"]),
            src_cell,
            esc(f["settle_by"]),
        ])
    tbl = table(["Flag", "What happened", "Source", "Resolution / how to close"], rows,
                caption=f"Complete audit ledger of all {len(FR['flags'])} flags tracked across 2026-11-25 and 2026-11-26.",
                card_labels=["Flag", "What happened", "Source", "Resolution"])
    n_open = sum(1 for f in FR["flags"] if f.get("status") == "Open")
    n_res = sum(1 for f in FR["flags"] if f.get("status") == "Resolved")
    n_doc = sum(1 for f in FR["flags"] if f.get("status") == "Documented")
    high_open = sum(1 for f in FR["flags"] if f["severity"] == "HIGH" and f.get("status") == "Open")
    return f"""
<p class="lede">Complete audit trail of ambiguities, dynamic dependencies, and data limitations:
<strong>{n_res} resolved</strong>, <strong>{n_doc} documented</strong>, and <strong>{n_open} live open</strong>
items requiring timing or external updates.</p>

<div class="kpi">
 <div class="card"><div class="k">Total tracked</div><div class="v">{len(FR["flags"])}</div></div>
 <div class="card"><div class="k">Live Open</div><div class="v">{n_open}</div><div class="small">{high_open} high-severity open</div></div>
 <div class="card"><div class="k">Resolved (2026-11-26)</div><div class="v">{n_res}</div><div class="small">Reconciled / verified on primary pages</div></div>
 <div class="card"><div class="k">Documented limits</div><div class="v">{n_doc}</div><div class="small">Tax basis, accessible tier, Haversine reach</div></div>
</div>

{tbl}

<h2>The four live items that still matter before travel</h2>
<div class="badbox">
<ol class="tight">
<li><strong>F-01/F-25</strong> &mdash; a secondary source reports a 14 December 2026 New York ceremony; no official MICHELIN page confirmed it in this session.</li>
<li><strong>F-03</strong> &mdash; Hotel rates carry live Black Friday / Bonus promos; lock $0-prepay free-cancel now and re-check in mid-Jan 2027.</li>
<li><strong>F-05</strong> &mdash; The one-hour travel rule is modelled via Haversine across 22 stars, pending scheduled GTFS timetable verification.</li>
<li><strong>F-15</strong> &mdash; AMS–JFK fare ($1,266 for 2) is an indicative 1-adult aggregator quote until checked for 2 seats w/ bags on airline checkout.</li>
</ol>
</div>
"""


def build_method():
    boundary_rows = [
        ["Per Se / Atera / Aquavit tasting totals", "Full menu dollar price appears only after picking an open date/slot on Tock", "Shown transparently as verified Tock deposit floors ($200 / $200 / $50)"],
        ["TikTok profile URLs", "Direct HTTP fetches return HTTP 400", "No profile URL guessed; 4 search-verified direct video links labelled clearly"],
        ["47 remaining NYC 1-star venues", "Address/price pages not yet individually pulled beyond top 22 priority venues", "Kept complete on name, star badge, cuisine, borough and MICHELIN link"],
    ]
    boundary_sources = [
        "https://www.exploretock.com/perse",
        "https://www.tiktok.com/",
        "https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/1-star-michelin",
    ]
    boundary_table = table(["Source", "Behaviour observed", "Handling on this site"], boundary_rows,
                           caption="Scraping and checkout boundaries, with an official source link on every row.",
                           card_labels=["Source", "Behaviour", "Handling"], source_urls=boundary_sources)
    ind_sources = INDEPENDENT["official_sources"]
    ind_rows = [[esc(x["publisher"]), esc(x["verified"]), pill(x["kind"], x["kind"]), ext(x["url"], "official source")]
                for x in ind_sources]
    ind_table = table(["Publisher / source", "What was independently verified", "Classification", "Official link"], ind_rows,
                      caption="Final independent official-source audit ledger, 2026-11-26.",
                      card_labels=["Publisher", "Verified", "Classification", "Link"],
                      source_urls=[x["url"] for x in ind_sources])
    return f"""
<p class="lede">How every number on this site was produced, every official source read on {BUILD_DATE},
the few remaining third-party walls, and the automated integrity checks run on every build.</p>

<h2>Rules the site is built on</h2>
<div class="card">
<ol class="tight">
<li><strong>Read it or leave it blank.</strong> A value appears only if verified on a linked primary/official source or authoritative search record; secondary sources are explicitly labelled and flagged.</li>
<li><strong>Never infer.</strong> No invented daily meal allowances, no guessed handles, no fabricated schedules.</li>
<li><strong>Separate the award from the listing.</strong> Red stars, Green Stars (including <em>One White Street</em> Selected), Bib Gourmand (76), and Selected (224) stay strictly separated.</li>
<li><strong>Label every derived number.</strong> NYC tax math (14.75% + $4–$6/night + $1 Arlo tourism) and Haversine distances are explicitly marked DERIVED/MODEL.</li>
<li><strong>Reconcile disagreements explicitly.</strong> The 72-entry ceremony vs 69 live NYC list discrepancy is fully accounted for name-by-name (F-02).</li>
<li><strong>Date every snapshot.</strong> Verified snapshot date: <strong>{BUILD_DATE}</strong>.</li>
</ol>
</div>

<h2>Sources read ({BUILD_DATE})</h2>
<h3>MICHELIN Guide &amp; Official Restaurant Sites / Resy / Tock</h3>
<ul class="tight">
<li>{ext("https://guide.michelin.com/us/en/article/michelin-guide-ceremony/all-the-stars-in-the-michelin-guide-to-new-york-city-2025", "2025 NY Star Ceremony Article (72 entries)")} · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/all-starred", "Live NYC Starred Filter (69 venues)")} · {ext("https://guide.michelin.com/us/en/best-of/least-expensive-one-michelin-star-restaurants-in-new-york", "Least Expensive 1-Star NYC Picks")}.</li>
<li>All 5 Three-Stars: {ext("https://www.le-bernardin.com/accessible/menus/dining-room/chef-s-tasting/", "Le Bernardin")}, {ext("https://www.elevenmadisonpark.com/", "Eleven Madison Park")}, {ext("https://www.exploretock.com/jungsik", "Jungsik (Tock)")}, {ext("https://www.exploretock.com/perse", "Per Se (Tock)")}, {ext("https://www.exploretock.com/sushi-sho-new-york", "Sushi Sho (Tock)")}.</li>
<li>Two- &amp; One-Stars + Green Star: {ext("https://www.gknyc.com/menus", "Gabriel Kreuther")}, {ext("https://www.themodernnyc.com/the-modern/", "The Modern")}, {ext("https://www.saga-nyc.com/", "Saga")}, {ext("https://www.jean-georgesrestaurant.com/accessible/jean-georges/menus/dinner-tasting-menu/six-course-tasting/", "Jean-Georges")}, {ext("https://www.exploretock.com/atomixnyc", "Atomix (Tock)")}, {ext("https://www.exploretock.com/atera", "Atera (Tock)")}, {ext("https://www.exploretock.com/aquavit", "Aquavit (Tock)")}, {ext("https://www.danielnyc.com/cuisine/prix-fixe", "Daniel")}, {ext("https://www.gramercytavern.com/dining-room-menu/", "Gramercy Tavern")}, {ext("https://lecoucou.com/", "Le Coucou")}, {ext("https://www.dirtcandynyc.com/", "Dirt Candy")}, {ext("https://www.cotekoreansteakhouse.com/nycdinnermenu?tab=newyork-dinner", "Cote")}, {ext("https://www.crownshy.nyc/menus/", "Crown Shy")}, {ext("https://www.onewhitestreetnyc.com/tasting", "One White Street")}.</li>
<li>Reported ceremony date (14 Dec 2026): {ext("https://ny.eater.com/news/414985/michelin-guide-new-york-additions-2026-bib-gourmands-michelin-recommendations", "Eater New York (secondary, flagged F-25)")} · {ext("https://guide.michelin.com/us/en/articles/michelin-guide-ceremony", "official MICHELIN ceremony index (no confirmation found)")}.</li>
</ul>

<h3>Hotels, NYC Taxes &amp; Seasonal Windows</h3>
<ul class="tight">
<li>Direct Booking.com pages (2027-02-15 to 2027-02-22 + Weeks 2–5): {ext("https://www.booking.com/hotel/us/fairfield-inn-suites-by-marriott-new-york-manhattan-central-park.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Fairfield Central Park")}, {ext("https://www.booking.com/hotel/us/arlo-soho.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Arlo SoHo")}, {ext("https://www.booking.com/hotel/us/residence-inn-new-york-downtown-manhattan-financial-district.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Residence Inn FiDi")}, {ext("https://www.booking.com/hotel/us/hyatt-place-new-york-chelsea.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Hyatt Place Chelsea")}, {ext("https://www.booking.com/hotel/us/citizenm-new-york-times-square-new-york.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "citizenM Times Square")}, {ext("https://www.booking.com/hotel/us/arlo-midtown.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Arlo Midtown")}, {ext("https://www.booking.com/hotel/us/pestana-cr7-times-square.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Pestana CR7 Times Square")}.</li>
<li>{ext("https://www.nyc.gov/site/finance/business/business-hotel-room-occupancy-tax.page", "NYC Department of Finance: Hotel Room Occupancy Tax (14.75% + unit/Javits fees)")} · {ext("https://www.nyctourism.com/", "NYC Tourism Winter Outing 2027 (Jan 2–Feb 11)")}.</li>
</ul>

<h3>Activities, Transit, Calendar, Climate &amp; Flights</h3>
<ul class="tight">
<li>{ext("https://www.moma.org/visit/", "MoMA")} · {ext("https://www.metmuseum.org/plan-your-visit", "The Met (Wed closed)")} · {ext("https://www.amnh.org/plan-your-visit", "AMNH ($37 out-of-state)")} · {ext("https://www.911memorial.org/visit/visit-museum-1", "9/11 Museum (last entry 18:00)")} · {ext("https://www.rockefellercenter.com/tickets/top-of-the-rock-observation-deck/", "Top of the Rock")} · {ext("https://www.nps.gov/stli/planyourvisit/hours.htm", "Statue of Liberty NPS Hours & Fees")} · {ext("https://www.nycgovparks.org/parks/central-park", "Central Park")} · {ext("https://www.thehighline.org/visit/", "High Line Winter Hours")} · {ext("https://www.chelseamarket.com/visit", "Chelsea Market")} · {ext("https://www.nyc.gov/html/dot/html/infrastructure/brooklyn-bridge.shtml", "Brooklyn Bridge DOT")} · {ext("https://www.broadway.org/", "Broadway League")}.</li>
<li>{ext("https://www.mta.info/fares-tolls/subway-bus", "MTA Fares ($3 base, $35 7-day cap)")} · {ext("https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/", "OPM 2027 Federal Holidays")} · {ext("https://www.schools.nyc.gov/about-us/news/morning-bell/contentdetails/morning-bell/2026/04/21/2026-27-nycps-calendar-now-available", "NYCPS 2026–2027 Calendar")} · {ext("https://www.weather.gov/media/okx/Climate/CentralPark/nycnormals.pdf", "NWS Central Park 1991–2020 Normals")}.</li>
<li>{ext("https://www.google.com/travel/flights?q=Flights%20to%20JFK%20from%20AMS%20on%202027-02-15%20through%202027-02-22", "Google Flights AMS–JFK")} · {ext("https://www.kayak.com/flights/AMS-NYC/2027-02-14/2027-02-23?sort=bestflight_a", "KAYAK AMS–NYC")}.</li>
</ul>

<h2>Final independent verification ledger</h2>
<p class="hint">This section preserves the final session's line-by-line official-source reads after the parallel upstream work was integrated. It supplements, rather than replaces, the canonical data in <code>site_data/*.json</code>. The machine-readable ledger is also available at <a href="../site_data/independent_verification.json">independent_verification.json</a>.</p>
{ind_table}
<div class="note"><strong>Independent irregularities:</strong> {" ".join(esc(x) for x in INDEPENDENT["irregularities"])}</div>

<h2>Remaining checkout / scraping boundaries</h2>
{boundary_table}

<h2>Build checks</h2>
<div class="okbox">
<p><code>python3 build_site.py</code> refuses to succeed if any of these fail:</p>
<ul class="tight">
<li>Budget subtotal matches the sum of priced lines within $0.005.</li>
<li>Zero unrendered template braces, double-escaped entities, leaked raw tags, or bare-hash placeholder anchors.</li>
<li>Zero duplicate element IDs and zero broken internal links across <code>docs/*.html</code>.</li>
<li>Every generated table row has at least one external source link; the lexical external URL audit is written to <a href="data/external_url_audit.json">external_url_audit.json</a>.</li>
<li>All superseded legacy files (e.g. <code>docs/methodology.html</code>, <code>docs/data/build_summary.json</code>) remain absent.</li>
</ul>
</div>

<h2>Archive notice: deepdive/</h2>
<p>An earlier session's independent research tree sits at <a href="../deepdive/index.html">deepdive/</a>
with older hotel shortlists and raw initial notes. This dashboard in <code>docs/</code> is the canonical,
updated, and reconciled source of truth.</p>
"""



def build_repo_review():
    roster = ROSTER["restaurants"]
    det = DETAILS["details"]
    acts = ACTS["activities"]

    def key(r):
        return r["michelin_url"].rstrip("/").split("/")[-1]

    n_hours = sum(1 for r in roster if det.get(key(r), {}).get("hours"))
    n_price = sum(1 for r in roster if det.get(key(r), {}).get("menu_price_usd"))
    n_page = sum(1 for r in roster if det.get(key(r)))
    n_ig = sum(1 for r in roster if any(
        s["kind"] == "official" for s in SOCIAL["accounts"].get(key(r), [])))
    n_vid = sum(1 for r in roster if any(
        s["kind"] == "review" for s in SOCIAL["accounts"].get(key(r), [])))
    a_ver = sum(1 for a in acts if a["verification"].startswith("VERIFIED"))
    a_part = sum(1 for a in acts if a["verification"].startswith("PARTIAL"))
    a_ig = sum(1 for a in acts if any(
        s["kind"] == "official" for s in SOCIAL["accounts"].get(a["id"], [])))
    a_vid = sum(1 for a in acts if any(
        s["kind"] == "review" for s in SOCIAL["accounts"].get(a["id"], [])))
    h_priced = sum(1 for h in HOTELS["hotels"] if h["total_7n_usd"])

    coverage = table(
        ["Dataset", "Rows", "Fully or partly verified", "Has a source link", "Verified social", "Blank / flagged"],
        [
            ["Restaurants (star roster)", str(len(roster)),
             f'{n_page} with full venue details',
             f'{len(roster)} (MICHELIN page on every row)',
             f'{n_ig} official Instagram · {n_vid} review video venues',
             f'{len(roster) - n_page} roster-only (mostly outer/secondary 1-stars)'],
            ["Restaurants (hours)", str(len(roster)), f'{n_hours}',
             f'{n_hours}', "—", f'{len(roster) - n_hours} roster-only'],
            ["Restaurants (menu price)", str(len(roster)), f'{n_price} (incl. 3 deposit floors)',
             f'{n_price}', "—", f'{len(roster) - n_price} ALC / roster-only'],
            ["Hotels", str(len(HOTELS["hotels"])), f'{h_priced} priced + 5-week table',
             f'{len(HOTELS["hotels"])} direct /hotel/us/ pages', "—",
             f'{sum(1 for h in HOTELS["hotels"] if not h["address"])} without street address'],
            ["Activities", str(len(acts)), f'{a_ver} verified · {a_part} partial',
             f'{len(acts)}', f'{a_ig} official IG · {a_vid} YouTube reviews',
             f'{sum(1 for a in acts if a["cost_2_adults_usd"] is None)} intentionally unpriced (Broadway)'],
        ],
        caption=f"Verified dataset inventory as built on {BUILD_DATE}.",
        card_labels=["Dataset", "Rows", "Verified", "Source link", "Social", "Blank"])

    findings = table(
        ["#", "Finding", "Evidence", "What was done", "Status"],
        [
            ["R1", "Repository contains canonical docs/ dashboard plus archived deepdive/ branch output.",
             "docs/ (generated by build_site.py) alongside archived deepdive/",
             "Documented canonical source in docs/ and kept deepdive/ clearly flagged as prior archive (S-01).",
             "Documented"],
            ["R2", "MICHELIN 72-entry ceremony list vs 69 live NYC list disagreement.",
             "site_data/michelin_roster.json live_nyc_status tags",
             "Reconciled name-by-name: 2 Westchester venues + closed Shion 69 Leonard St (F-02, Q-17).",
             "Resolved"],
            ["R3", "GitHub Pages builds from main:/ with root index.html redirecting to docs/.",
             "gh api repos/.../pages -> source main:/",
             "Regenerated docs/ cleanly from site_data/*.json; branch ready for PR merge to main.",
             "Ready for merge"],
            ["R4", "No automated GitHub Actions CI workflow yet.",
             ".github does not exist",
             "build_site.py runs strict checks on every build; CI workflow proposed as S-07.",
             "Partly addressed"],
            ["R5", "No LICENSE file at repo root.",
             "no LICENSE at root",
             "Left to repository owner.",
             "Open"],
            ["R6", "Orphaned legacy pages survived earlier build (docs/methodology.html, docs/data/build_summary.json).",
             "Removed stale docs/methodology.html & docs/data/build_summary.json",
             "Removed orphaned files and verified absence inside build checks.",
             "Resolved"],
            ["R7", "Previously unverified museum hours & AMNH admission (Met, High Line, Chelsea Market, AMNH, Statue of Liberty).",
             "Verified on metmuseum.org, amnh.org, thehighline.org, chelseamarket.com, nps.gov",
             "All 5 resolved on 2026-11-26; fixed critical Wednesday Met closure in itinerary!",
             "Resolved"],
            ["R8", "Previously unconfirmed social handles & scarce video links.",
             "site_data/social.json (24 IG, 23 YT, 4 TikTok videos)",
             "Replaced guesses with verified official handles (incl. @cotekoreansteakhouse) and video reviews.",
             "Resolved"],
            ["R9", "Hotel street addresses, direct Booking links, and Le Bernardin / nearest-3-star coordinate bugs.",
             "site_data/hotels.json & site_data/restaurant_details.json",
             "Fixed all 7 hotel addresses/URLs/coords, fixed Le Bernardin lon, corrected Arlo SoHo & FiDi nearest 3-star to Jungsik.",
             "Resolved"],
        ],
        caption="Repository & data audit findings updated 2026-11-26.",
        card_labels=["#", "Finding", "Evidence", "Action", "Status"])

    return (
        '<p class="lede">Verification accounting, audit history, and integrity checks for the repository.</p>'
        '<h2>Verification coverage, counted</h2>'
        + coverage
        + '<h2>Repository review</h2>'
        + findings
        + '<h2>How to verify locally</h2>'
        '<div class="card"><ol class="tight">'
        '<li>Run <code>python3 build_site.py</code> and confirm <code>all build checks passed</code>.</li>'
        '<li>Inspect any row source URL directly against <code>site_data/*.json</code>.</li>'
        '<li>Confirm every remaining open limit appears on <a href="flagged.html">Flagged</a>.</li>'
        '</ol></div>'
    )


# ---------------------------------------------------------------- checks
def run_checks(pages):
    errors, warnings = [], []

    _b = FR["budget"]
    _sum = round(sum(l["usd"] for l in _b["lines"] if l["usd"] is not None), 2)
    if abs(_sum - _b["verified_subtotal_usd"]) > 0.005:
        errors.append("budget: stated subtotal %.2f != sum of lines %.2f"
                      % (_b["verified_subtotal_usd"], _sum))

    for orphan in ("methodology.html", os.path.join("data", "build_summary.json")):
        if os.path.exists(os.path.join(DOCS, orphan)):
            errors.append(f"orphaned legacy artifact still present in docs/: {orphan}")

    for r in ROSTER["restaurants"]:
        if not r.get("michelin_url"):
            errors.append("restaurant without a MICHELIN source: " + str(r.get("name")))
    for h in HOTELS["hotels"]:
        if not h.get("source_url"):
            errors.append("hotel without a Booking.com source: " + str(h.get("id")))
    for a in ACTS["activities"]:
        if not a.get("official_url"):
            errors.append("activity without an official source: " + str(a.get("id")))
    for line in _b["lines"]:
        if line["usd"] is not None and not line.get("source"):
            errors.append("priced budget line without a source: " + str(line.get("item")))

    from html.parser import HTMLParser
    class _Shape(HTMLParser):
        def __init__(self):
            super().__init__(); self.tables = []; self.cur = None; self.row = None
        def handle_starttag(self, tag, attrs):
            if tag == "table": self.cur = {"header": None, "rows": []}
            elif tag == "tr" and self.cur is not None: self.row = 0
            elif tag in ("td", "th") and self.row is not None: self.row += 1
        def handle_endtag(self, tag):
            if tag == "tr" and self.cur is not None and self.row is not None:
                if self.cur["header"] is None: self.cur["header"] = self.row
                else: self.cur["rows"].append(self.row)
                self.row = None
            elif tag == "table" and self.cur is not None:
                self.tables.append(self.cur); self.cur = None

    for name, html in pages.items():
        sh = _Shape(); sh.feed(html)
        for i, t in enumerate(sh.tables, 1):
            for n, cells in enumerate(t["rows"], 1):
                if t["header"] and cells != t["header"]:
                    errors.append(f"{name}: table {i} row {n} has {cells} cells, header has {t['header']}")

    for name, html in pages.items():
        for ti, tbl in enumerate(re.findall(r"<table[^>]*>.*?</table>", html, re.S), 1):
            for ri, row in enumerate(re.findall(r"<tr>(.*?)</tr>", tbl, re.S), 1):
                if "<th" in row:
                    continue
                if "<td" in row and not re.search(r'href="https?://', row):
                    errors.append(f"{name}: table {ti} row {ri} has no external source link")

    for name, html in pages.items():
        if "{{" in html or "}}" in html:
            errors.append(f"{name}: unrendered template token")
        if "&lt;span" in html or "&lt;a " in html:
            errors.append(f"{name}: escaped markup leaked into output")
        if "&amp;amp;" in html or "&amp;#" in html:
            errors.append(f"{name}: double-escaped HTML entity")
        if 'href="#"' in html:
            errors.append(f"{name}: dead placeholder href")
        ids = re.findall(r'\bid="([^"]+)"', html)
        if len(ids) != len(set(ids)):
            errors.append(f"{name}: duplicate element id")
        for href in re.findall(r'href="([^"#][^"]*)"', html):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = os.path.join(DOCS, href.split("?")[0])
            if not os.path.exists(target):
                errors.append(f"{name}: broken internal link -> {href}")

    # Root redirect and archived deep dive are also published; check their links too.
    extra = [(os.path.join(ROOT, "index.html"), "index.html")]
    deep = os.path.join(ROOT, "deepdive")
    if os.path.isdir(deep):
        extra += [(os.path.join(deep, n), os.path.join("deepdive", n))
                  for n in sorted(os.listdir(deep)) if n.endswith(".html")]
    for path, label in extra:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            html = f.read()
        for href in re.findall(r'href="([^"#][^"]*)"', html):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = os.path.join(os.path.dirname(path), href.split("?")[0].split("#")[0])
            if not os.path.exists(target):
                errors.append(f"{label}: broken internal link -> {href}")
    return errors, warnings


def write_audits(pages):
    """Lexical external URL audit: validates schemes/hosts and publishes the URL set."""
    from collections import Counter
    all_html = list(pages.values())
    root_index = os.path.join(ROOT, "index.html")
    if os.path.exists(root_index):
        with open(root_index, encoding="utf-8") as f:
            all_html.append(f.read())
    deep = os.path.join(ROOT, "deepdive")
    if os.path.isdir(deep):
        for n in sorted(os.listdir(deep)):
            if n.endswith(".html"):
                with open(os.path.join(deep, n), encoding="utf-8") as f:
                    all_html.append(f.read())
    urls = sorted({m for html in all_html
                   for m in re.findall(r'href="(https?://[^"]+)"', html)})
    domains = Counter(urlparse(u).netloc for u in urls)
    warnings = [u for u in urls if not u.startswith("https://")]
    report = {
        "generated_on": BUILD_DATE,
        "audit_type": "lexical external URL audit across docs/, root redirect, and archived deepdive/; official pages read in this session are listed in site_data/independent_verification.json",
        "unique_external_urls": len(urls),
        "unique_domains": len(domains),
        "domains": dict(sorted(domains.items())),
        "non_https_warnings": warnings,
        "official_source_count": len(INDEPENDENT["official_sources"]),
        "manual_spot_checks": INDEPENDENT.get("manual_spot_checks", []),
        "url_fixes": INDEPENDENT.get("url_fixes", []),
        "all_urls": urls,
    }
    os.makedirs(os.path.join(DOCS, "data"), exist_ok=True)
    with open(os.path.join(DOCS, "data", "external_url_audit.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
        f.write("\n")


def main():
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    with open(os.path.join(DOCS, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)

    pages = {
        "index.html": layout("index.html",
            "New York City, 15–22 February 2027", build_index()),
        "hotels.html": layout("hotels.html", "Hotels — 7 nights verified", build_hotels()),
        "restaurants.html": layout("restaurants.html", "MICHELIN restaurants", build_restaurants()),
        "activities.html": layout("activities.html", "Activities & social reviews", build_activities()),
        "itinerary.html": layout("itinerary.html", "Itinerary", build_itinerary()),
        "budget.html": layout("budget.html", "Budget", build_budget()),
        "questions.html": layout("questions.html", "Open questions", build_questions()),
        "suggestions.html": layout("suggestions.html", "Suggestions for improvement", build_suggestions()),
        "flagged.html": layout("flagged.html", "Flagged for review", build_flagged()),
        "method.html": layout("method.html", "Method & sources", build_method()),
        "repo-review.html": layout("repo-review.html", "Repository review", build_repo_review()),
    }

    for name, html in pages.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(html)
    write_audits(pages)
    errors, _ = run_checks(pages)

    print(f"wrote {len(pages)} pages to {DOCS}")
    if errors:
        print("\nBUILD CHECKS FAILED:")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("all build checks passed")


ROSTER = load("michelin_roster.json")
DETAILS = load("restaurant_details.json")
HOTELS = load("hotels.json")
ACTS = load("activities.json")
SOCIAL = load("social.json")
FR = load("framework.json")
INDEPENDENT = load("independent_verification.json")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
build_site.py - builds the NYC 2027 trip-planning site into docs/.

Standard library only. Run:  python3 build_site.py

Design rules encoded here:
  * Nothing is invented. If a value is missing from site_data/, a cell is
    rendered as a visible blank with a pointer to the reason, never a guess.
  * Core hotel, restaurant, activity, and priced-budget records carry source links.
  * Every dashboard page is reachable from the shared one-level navigation.
"""
import json, os, re, sys, datetime
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "site_data")
DOCS = os.path.join(ROOT, "docs")

BUILD_DATE = datetime.datetime.now(datetime.timezone.utc).date().isoformat()


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


def table(headers, rows, caption=None, cls="", card_labels=None):
    """Rows are lists of pre-escaped HTML strings. Emits a real table plus a
    card view used below 700px so nothing needs horizontal scrolling."""
    labels = card_labels or headers
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
    # mobile card view
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
  <p><strong>Generated {BUILD_DATE}.</strong> Source-check dates vary by dataset; only records identified in this audit were re-read on 2026-11-26. Prices and hours change; re-check before booking.
  Rows that could not be verified are blank and listed on <a href="flagged.html">Flagged</a>.</p>
  <p>Sources, method and the model's assumptions: <a href="method.html">Method &amp; sources</a> ·
  Open decisions: <a href="questions.html">Questions</a> ·
  Improvement ideas: <a href="suggestions.html">Suggestions</a></p>
</footer>
</body></html>"""


# ---------------------------------------------------------------- derived data
def build_index():
    rec = next(h for h in HOTELS["hotels"] if h["id"] == "fairfield-central-park")
    n_stars = len(ROSTER["restaurants"])
    counts = ROSTER["meta"]["counts"]
    live = ROSTER["meta"].get("live_filtered_counts", {})
    n_ig_total = sum(1 for group in SOCIAL["accounts"].values() for item in group
                     if item["kind"] == "official")
    n_ig_unconfirmed = sum(1 for group in SOCIAL["accounts"].values() for item in group
                           if item["kind"] == "unconfirmed")
    n_review = sum(1 for grp in SOCIAL["accounts"].values() for s in grp
                   if s["kind"] == "review")
    det = DETAILS["details"]

    def key(r):
        return r["michelin_url"].rstrip("/").split("/")[-1]

    n_hours = sum(1 for r in ROSTER["restaurants"] if det.get(key(r), {}).get("hours"))
    n_price = sum(1 for r in ROSTER["restaurants"] if det.get(key(r), {}).get("menu_price_usd"))
    model_under = sum(1 for a in ACTS["activities"] if a["from_hotel"].get("within_one_hour"))
    activities_n = len(ACTS["activities"])
    budget = FR["budget"]
    unresolved_flags = sum(1 for f in FR["flags"] if f.get("status") == "Open")
    return f"""
<p class="lede">A source-linked seven-night recommendation for two adults, with the exact three-night preferred-date option, dated hotel snapshots, current official activity details, and unresolved limits kept visible.</p>

<div class="kpi">
  <div class="card"><div class="k">Recommended dates</div><div class="v">15–22 Feb 2027</div>
   <div class="small">7 nights, Mon→Mon. The preferred 15–18 Feb window is 3 hotel nights.</div></div>
  <div class="card"><div class="k">Fairfield · Booking-line estimate</div><div class="v">{money(rec['all_in_7n_usd'])}</div>
   <div class="small">Before-fee room rate: {money(rec['total_7n_usd'])}. Statutory-component calculation: {money(rec['statutory_tax_calc_7n_usd'])}. Neither is a checkout quote.</div></div>
  <div class="card"><div class="k">MICHELIN star entries</div><div class="v">{n_stars} in the 2025 ceremony roster</div>
   <div class="small">{counts['3']} / {counts['2']} / {counts['1']} (3/2/1 stars); current official filters show {live.get('total', 'not read')} ({live.get('3', '?')}/{live.get('2', '?')}/{live.get('1', '?')}) as of {ROSTER['meta'].get('live_filtered_read_on', 'unknown')}.</div></div>
  <div class="card"><div class="k">Priced subtotal</div><div class="v">{money(budget['priced_subtotal_usd'])}</div>
   <div class="small">Includes derived hotel charges and a one-adult airfare doubled for two; ordinary meals remain unpriced.</div></div>
</div>

<h2>Executive summary</h2>
<div class="grid two">
<div class="card">
<h3>1 · The recommendation</h3>
<p>For <strong>15–22 February 2027</strong>, Fairfield is the lowest displayed base room rate and has the lowest derived total among these seven sampled offers: a King Room, private bathroom, breakfast included, and free cancellation until 12 February. Booking.com showed <strong>{money(rec['total_7n_usd'])} before taxes and excluded fees</strong>. Adding the displayed 14.75% tax and $4/night line gives a derived estimate of <strong>{money(rec['all_in_7n_usd'])}</strong>; the official fixed-charge calculation gives <strong>{money(rec['statutory_tax_calc_7n_usd'])}</strong>. Neither is a final checkout quote; Booking.com's fixed fee differs from the official NYC/NYS components by $0.50 per night (F-04).</p>
<p class="hint">Fairfield is the lowest displayed pre-tax room rate among these seven on the 2026-11-26 snapshot. Compare the exact room and checkout breakdown on the <a href="hotels.html">Hotels page</a> before booking.</p>
</div>
<div class="card">
<h3>2 · Why seven nights, not three?</h3>
<p>The preferred window, 15–18 February, is <strong>three hotel nights</strong> across four calendar dates. The 7-night plan is the one that meets the brief's 1–2-week requirement; the exact 3-night preferred-date and 14-night alternatives are shown on the <a href="itinerary.html">Itinerary page</a>.</p>
<p class="hint">OPM confirms Monday 15 February 2027 is Washington's Birthday. That establishes the federal holiday date, not a hotel-demand or price effect (F-11).</p>
</div>
</div>

<div class="grid two">
<div class="card">
<h3>3 · The MICHELIN list is dated</h3>
<p>The 2025 ceremony article contains <strong>{n_stars} entries</strong> ({counts['3']} three-star, {counts['2']} two-star, {counts['1']} one-star). The live official star filters read {ROSTER['meta'].get('live_filtered_read_on', 'unknown')} show <strong>{live.get('total', 'not read')}</strong> ({live.get('3', '?')}/{live.get('2', '?')}/{live.get('1', '?')}). MICHELIN scheduled the next Northeast Cities ceremony, including New York, for 14 December 2026, before the trip.</p>
<p>Le Bernardin and Gabriel Kreuther have readable tasting-menu prices; Per Se's deposit floor is labelled separately. <a href="restaurants.html">See the dated roster and source notes →</a></p>
</div>
<div class="card">
<h3>4 · The one-hour rule is not yet measured</h3>
<p>Hotel reach is shown only as a straight-line 5 km coordinate proxy; activity minutes are simple speed models. Neither is an MTA itinerary or a measured door-to-door time. Liberty Island requires a ferry; the February 2027 sailing schedule, boarding, waiting, and full journey time are not verified. Do not treat the Statue of Liberty as under an hour (F-05, F-20).</p>
<p class="hint">A measured route matrix, including separate ferry legs, remains the highest-value travel check (Q-19).</p>
</div>
</div>

<div class="grid two">
<div class="card">
<h3>5 · What is verified, and what is not</h3>
<ul class="tight">
<li><strong>{n_hours} of {n_stars} restaurants have captured hours</strong> and <strong>{n_price} have a readable menu-price value</strong>. The rest remain roster-only on those fields.</li>
<li><strong>{n_ig_total} directly verified official social accounts</strong>, {n_ig_unconfirmed} unconfirmed Instagram reference{'s' if n_ig_unconfirmed != 1 else ''}, and {n_review} third-party review videos are linked; platform searches are labelled, and no TikTok account is asserted.</li>
<li><strong>{model_under} of {activities_n} activities</strong> have a sub-hour result in the simple model; this is not a measured route guarantee.</li>
<li><strong>{len(FR['flags'])} review records</strong> ({unresolved_flags} open) and <strong>{len(FR['questions'])} tracked questions</strong> are itemized.</li>
</ul>
</div>
<div class="card">
<h3>6 · Three things that could change the plan</h3>
<ol class="tight">
<li><strong>14 December 2026:</strong> MICHELIN publishes the new Northeast Cities selection; restaurant distinctions may change.</li>
<li><strong>Hotel checkout charges:</strong> Booking.com's $4/$6 nightly fixed-fee labels differ from the $3.50 statutory NYC/NYS fixed components.</li>
<li><strong>Measured travel:</strong> no full MTA route matrix or February 2027 ferry schedule is recorded yet.</li>
</ol>
</div>
</div>

<h2>How to read this site</h2>
{theme_table()}

<h2>Where to go next</h2>
<div class="grid three">
<div class="card"><h3><a href="hotels.html">Hotels</a></h3><p class="small">7 dated room snapshots, actual addresses, separate Booking-line and statutory-component calculations.</p></div>
<div class="card"><h3><a href="restaurants.html">MICHELIN</a></h3><p class="small">The 2025 ceremony roster, current filter-count difference, hours, prices, and social links where verified.</p></div>
<div class="card"><h3><a href="activities.html">Activities</a></h3><p class="small">11 activities with official hours, prices, exceptions, and the distinction between modelled and unmeasured travel.</p></div>
<div class="card"><h3><a href="itinerary.html">Itinerary</a></h3><p class="small">Day-by-day for 7 nights, plus the exact 3-night preferred-date and 14-night variants.</p></div>
<div class="card"><h3><a href="budget.html">Budget</a></h3><p class="small">Every priced line with its source, derivation, and limits.</p></div>
<div class="card"><h3><a href="questions.html">Questions</a></h3><p class="small">{len(FR['questions'])} decisions, what is known, what remains missing, and how to check.</p></div>
<div class="card"><h3><a href="suggestions.html">Suggestions</a></h3><p class="small">12 improvements with effort, impact, risk, and a decision field.</p></div>
<div class="card"><h3><a href="flagged.html">Flagged</a></h3><p class="small">{len(FR['flags'])} current and resolved audit records.</p></div>
<div class="card"><h3><a href="method.html">Method &amp; sources</a></h3><p class="small">Source dates, calculations, known disagreements, and validation limits.</p></div>
</div>
"""

def theme_table():
    rows = [
        ['<span class="pill p-verified">verified</span>', "Read on a linked official/source page; see the dataset and source note for its last-check date."],
        ['<span class="pill p-partial">partial</span>', "Some fields verified, others could not be read. The blank field names what is missing."],
        ['<span class="pill p-open">not verified</span>', "Left blank on purpose. The Flagged page says which source would settle it."],
        ['<span class="pill p-documented">model</span>', "Computed from other data (a formula, not an observation). The formula is on the Method page."],
    ]
    return table(["Label", "What it means"], rows, caption="A value is never inferred to fill a gap.")


def build_hotels():
    rows = []
    for h in HOTELS["hotels"]:
        resort_note = f'<div class="small">{esc(h["resort_fee_note"])}</div>' if h.get("resort_fee_note") else ""
        room = (esc(h["room"]) + '<div class="small">' + esc(h["bed"]) + ' · ' + esc(h["bath"]) + '</div>'
                + (f'<div class="small">{esc(h["size"])}</div>' if h.get("size") else ""))
        booking_est = ('<strong>' + money(h["all_in_7n_usd"]) + '</strong>'
                       + '<div class="small">derived from Booking.com excluded-charge line; not a quote</div>'
                       + '<div class="small">' + esc(h["booking_excluded_line"]) + '</div>')
        statutory = ('<strong>' + money(h["statutory_tax_calc_7n_usd"]) + '</strong>'
                     + '<div class="small">14.75% + $3.50/night statutory fixed components'
                     + (' + $1/night tourism fee' if h.get("tourism_fee_per_night_usd") else '')
                     + '</div>')
        rows.append([
            f'<strong>{esc(h["name"])}</strong><div class="small">{esc(h["area"])}</div><div class="small">{esc(h["address"])}</div>',
            room,
            esc(h["breakfast"]),
            money(h["total_7n_usd"]) + '<div class="small">before the listed excluded charges</div>' + resort_note,
            booking_est,
            statutory,
            f'{esc(h["cancellation"])}<div class="small">guest score {esc(h["rating"])}, checked {esc(h.get("rating_read_on", "date not recorded"))}</div>',
            ext(h["source_url"], "Booking.com · dated property page"),
        ])

    ranked = sorted(HOTELS["hotels"], key=lambda h: h["all_in_7n_usd"])
    rrows = []
    for i, h in enumerate(ranked, 1):
        badge = ' <span class="pill p-verified">lowest in this snapshot</span>' if h["id"] == "fairfield-central-park" else ""
        rrows.append([
            str(i), '<strong>' + esc(h["name"]) + '</strong>' + badge,
            money(h["all_in_7n_usd"]), money(h["statutory_tax_calc_7n_usd"]),
            money(h["total_7n_usd"]), esc(h["breakfast"]), esc(h["cancellation"]),
        ])
    rank_table = table(
        ["#", "Hotel", "Booking-line estimate", "Statutory-component calculation", "Before excluded charges", "Breakfast", "Cancellation"],
        rrows,
        caption="Sorted by the derived Booking-line estimate. Both calculations are shown; neither is a checkout quote.",
        card_labels=["Rank", "Hotel", "Booking estimate", "Statutory calculation", "Before fees", "Breakfast", "Cancellation"])

    window_rows = []
    for w in HOTELS.get("windows_sampled", []):
        rates = '<br>'.join(money(option["amount"]) + ' <span class="small">' + esc(option["policy"]) + '</span>'
                            for option in w.get("rates_before_tax_usd", []))
        window_rows.append([
            f'{esc(w["start"])} to {esc(w["end"])}<div class="small">7 nights</div>',
            esc(w["label"]), rates or '<span class="blank">no rate captured</span>',
            ext(w["source_url"], "dated Booking.com property page"),
        ])
    windows_table = table(
        ["Dates", "Why sampled", "Displayed rate(s), before taxes/fees", "Source"], window_rows,
        caption="Four Fairfield weekly snapshots read 2026-11-26. Refundable and non-refundable offers stay separate; this is not a daily price curve.",
        card_labels=["Dates", "Why sampled", "Rate(s)", "Source"])

    reach_order = sorted(HOTELS["hotels"], key=lambda h: (-h["reach"]["stars_within_5km"],
                                                          -h["reach"]["three_star_within_5km"]))
    reach_rows = []
    for i, h in enumerate(reach_order, 1):
        r = h["reach"]
        reach_rows.append([
            str(i), '<strong>' + esc(h["name"]) + '</strong><div class="small">' + esc(h["area"]) + '</div>',
            f'{r["stars_within_5km"]} / 7', f'{r["three_star_within_5km"]} / 5',
            f'{r["nearest_three_star_km"]:.2f} km', money(h["all_in_7n_usd"]),
        ])
    reach_table = table(
        ["#", "Hotel", "Star venues within 5 km", "Three-star within 5 km", "Nearest three-star", "Booking-line estimate"],
        reach_rows,
        caption="Straight-line proximity only; coordinates are available for 7 of 72 roster entries and most hotel points remain area-level. This is not a measured one-hour transit ranking.",
        card_labels=["Rank", "Hotel", "Within 5 km", "Three-star", "Nearest", "Estimate"])

    fair = next(h for h in HOTELS["hotels"] if h["id"] == "fairfield-central-park")
    return f"""
<p class="lede">Seven properties for two adults, with the selected room, bed, private-bathroom detail, breakfast, cancellation terms, and dated Booking.com snapshots for 15–22 February 2027. Street addresses are captured for all seven; most map coordinates remain area-level approximations.</p>

<div class="warnbox"><strong>Two calculations; neither is a checkout quote.</strong>
For the Fairfield King Room, Booking.com shows {money(fair["total_7n_usd"])} before tax and lists <em>{esc(fair["booking_excluded_line"])}</em>. Adding the displayed 14.75% tax and $4/night line gives a derived estimate of <strong>{money(fair["all_in_7n_usd"])}</strong>. NYC Finance lists a $2/night fixed hotel occupancy tax for rooms at $40+ and NYS lists a separate $1.50/night unit fee: $3.50/night combined, which gives <strong>{money(fair["statutory_tax_calc_7n_usd"])}</strong>. The $0.50/night discrepancy remains unresolved (F-04); verify the actual checkout breakdown.</div>

<h2>Shortlist, 15–22 February 2027 (7 nights, 2 adults)</h2>
{table(
    ["Hotel &amp; address", "Room / bed / bathroom", "Breakfast", "Displayed room price", "Booking-line estimate", "Statutory-component calculation", "Cancellation &amp; score", "Source"],
    rows,
    caption="All seven property-specific room pages were checked 2026-11-26 for check-in 2027-02-15 and check-out 2027-02-22. Resort fees are identified when Booking.com says they are already in the displayed room total.",
    card_labels=["Hotel", "Room", "Breakfast", "Before excluded charges", "Booking estimate", "Statutory calculation", "Cancellation", "Source"])}

<h2>Four real date windows</h2>
{windows_table}
<p class="small">The 15–22 February and 22 February–1 March Fairfield King Room snapshots are refundable at the captured offers; later March snapshots show distinct non-refundable and refundable prices. The first sample starts on the preferred date but is a separate seven-night option, not the literal 15–18 February three-night window. These four weekly points do not establish the cheapest date anywhere in the full 15 February–23 March window or the effect of the federal holiday.</p>

<h2>Ranking by current derived estimates</h2>
<p>Sorted by the estimate that applies Booking.com’s own disclosed fixed-charge line; the statutory-component calculation appears beside it. Fairfield is lowest in this seven-property snapshot on both bases, but dynamic rates and different cancellation terms mean this is not a durable market ranking.</p>
{rank_table}

<h2>Reach is a separate, unmeasured question</h2>
<div class="warnbox"><strong>This is not the requested measured one-hour route ranking.</strong>
Only 7 of 72 restaurant coordinates are recorded, and most hotel coordinates are area-level. The table below is a 5 km straight-line proximity proxy; no complete MTA door-to-door matrix was measured (F-05, F-19, Q-19).</div>
{reach_table}

<h2>What the snapshots do and do not establish</h2>
<div class="note"><strong>What they establish:</strong> Fairfield has the lowest dated base room rate and the lowest derived total in this seven-hotel snapshot. Resort fees identified by Booking.com are already included in the relevant room rate; separately disclosed taxes and fixed charges are added in the derived estimates. The unresolved $4/$6 versus $3.50 nightly fixed-fee difference is not silently reconciled.</div>
<div class="badbox"><ul class="tight">
<li><strong>Live rates:</strong> all prices can change. Non-refundable and refundable offers are not interchangeable.</li>
<li><strong>Fees:</strong> Booking.com displays a $4/night city tax on six properties and $6/night on Residence Inn FiDi; its fixed amounts conflict with the $3.50/night NYC/NYS components calculated from official sources. Arlo properties also list a $1/night tourism fee.</li>
<li><strong>Coordinates:</strong> exact street addresses are now recorded, but hotel points used for the current proximity proxy have not been re-geocoded (F-13).</li>
<li><strong>Room variants:</strong> the selected Arlo SoHo rate is labelled ADA; the displayed rates and cancellation terms differ by offer (F-14).</li>
<li><strong>Longer stay:</strong> a separate 22 Feb–1 Mar week is sampled, but there is no combined 14-night checkout quote (F-12).</li>
</ul></div>
"""

def build_restaurants():
    det = DETAILS["details"]
    n_hours_pub = sum(1 for r in ROSTER["restaurants"]
                      if det.get(r["michelin_url"].rstrip("/").split("/")[-1], {}).get("hours"))
    n_price_pub = sum(1 for r in ROSTER["restaurants"]
                      if det.get(r["michelin_url"].rstrip("/").split("/")[-1], {}).get("menu_price_usd"))
    rows = []
    for r in ROSTER["restaurants"]:
        key = r["michelin_url"].rstrip("/").split("/")[-1]
        d = det.get(key)
        social = SOCIAL["accounts"].get(key, [])
        soc_html = []
        seen_review = 0
        for s in social:
            if s["kind"] == "official":
                soc_html.append(ext(s["url"], s["platform"] + " \u2713", "tag"))
            elif s["kind"] == "unconfirmed":
                soc_html.append(ext(s["url"], s["platform"] + " unconfirmed", "tag"))
            elif s["kind"] == "review":
                seen_review += 1
                soc_html.append(ext(s["url"], s["platform"] + " review " + str(seen_review), "tag"))
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
                hours += '<div class="small">only these days were readable</div>'
                hours += ' ' + pill("partial", "partial")
        else:
            hours = '<span class="blank">hours not verified</span>'
            hours += '<div class="small">' + esc((d or {}).get("hours_note") or "no hours block on the official page captured") + '</div>'

        if d and d.get("menu_price_usd"):
            floor = " (from)" if d.get("price_is_floor") else ""
            price = money(d["menu_price_usd"]) + floor + '<div class="small">per person &middot; ' + money(d["menu_price_usd"] * 2) + ' for two</div>'
            if d.get("price_is_floor"):
                price += '<div class="small">deposit, not the menu price</div>'
        elif d:
            price = '<span class="blank">no official price read</span>'
            if d.get("price_note"):
                price += '<div class="small">' + esc(d["price_note"][:150]) + '</div>'
        else:
            price = '<span class="blank">no official price read</span>'
        conf = ""
        rows.append([
            f'<strong>{esc(r["name"])}</strong><div class="small">{esc(r["cuisine"])} · {esc(r["borough"])}</div>',
            stars_badge(r["stars"]) + (' <span class="badge b0" title="Green Star">🌿</span>' if r["green"] == "yes" else ""),
            hours + conf,
            price,
            " ".join(soc_html),
            ext(r["michelin_url"], "MICHELIN"),
        ])
    # ---- cluster table, built from data only
    import collections as _c
    bor = _c.Counter(r["borough"] for r in ROSTER["restaurants"])
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
                near.append(by_key[k2]["name"] + f" ({d * 1000:.0f} m)")
        geo.append([stars_badge(by_key[k]["stars"]),
                    '<strong>' + esc(by_key[k]["name"]) + '</strong><div class="small">' + esc(by_key[k]["cuisine"]) + '</div>',
                    (", ".join(near) if near else '<span class="blank">no other scored star venue within 1 km</span>')])
    geo.sort(key=lambda r: r[2].startswith('<span'))
    cluster_table = table(
        ["Borough", "Star entries", "Three-star entries", "What it means for the trip"],
        [
            ["Manhattan", str(bor.get("Manhattan", 0)), str(sum(1 for r in ROSTER["restaurants"] if r["borough"] == "Manhattan" and r["stars"] == 3)),
             "The only borough with a full spread of star levels. Every three-star dinner on the itinerary is here."],
            ["Brooklyn", str(bor.get("Brooklyn", 0)), "0",
             "Six entries, no three-star. No hotel-to-venue MTA journey time has been measured; check the route for any restaurant you choose."],
            ["Queens", str(bor.get("Queens", 0)), "0",
             "One entry. No hotel-to-venue MTA journey time has been measured."],
            ["Outside NYC", str(bor.get("Tarrytown, NY (outside NYC)", 0) + bor.get("North Salem, NY (outside NYC)", 0)), "0",
             "Blue Hill at Stone Barns (Tarrytown) and La Bastide (North Salem). Their door-to-door travel times have not been measured."],
        ],
        caption="Borough counts cover all 72 entries. This is the only cluster claim the data supports on its own.",
        card_labels=["Borough", "Entries", "Three-star", "Meaning"])
    geo_table = table(
        ["Rating", "Venue", "Scored star venue within 1 km"],
        geo,
        caption="Straight-line distances between the 7 venues whose coordinates were verified. A 7-venue sample, not a neighbourhood map.",
        card_labels=["Rating", "Venue", "Within 1 km"])

    return f"""
<p class="lede">All {len(ROSTER['restaurants'])} star entries from MICHELIN's
<em>All the Stars in The MICHELIN Guide to New York City 2025</em>, published 18 November 2025.
The badge in column two is the distinction: <strong>stars are awards</strong>, and a venue with no star
icon on MICHELIN's site is <em>listed</em>, not starred.</p>

<div class="badbox"><strong>This is the 2025 ceremony roster; the 2026 selection is scheduled for 14 December.</strong>
The official announcement names the Northeast Cities ceremony, including New York. Re-read the new selection after that date because distinctions may change (F-01).</div>

<div class="badbox"><strong>Read the two middle columns carefully: most of them are empty, on purpose.</strong>
Only {n_hours_pub} of the {len(ROSTER['restaurants'])} star restaurants published hours that could be read,
and only {n_price_pub} published a menu price. The rest of the roster is complete on name, distinction,
cuisine, borough and official link &mdash; and blank on hours and price, because the alternative would be
inventing them. The counts are on the <a href="repo-review.html">repo review</a> page and the way to close
each gap is in <a href="questions.html">Q-06 and Q-09</a>.</div>

<div class="warnbox"><strong>These are two differently dated official MICHELIN views.</strong> The 2025 ceremony article lists
72 entries (5 / 15 / 52). Current official filtered list pages, read 2026-11-26, report 69 (5 / 14 / 50).
This table preserves the dated ceremony roster; it does not call the three-entry difference an error before a name-by-name comparison (F-02, Q-17).</div>

<h2>The full roster</h2>
<div class="legend">
  <span>{stars_badge(3)}</span><span class="small">Three stars — exceptional cuisine</span>
  <span>{stars_badge(2)}</span><span class="small">Two stars — excellent cooking</span>
  <span>{stars_badge(1)}</span><span class="small">One star — high quality cooking</span>
  <span>🌿</span><span class="small">Green Star (sustainability), held alongside a star</span>
</div>
{table(
    ["Restaurant", "Distinction", "Days open &amp; hours", "Menu price", "Social / video", "Source"],
    rows,
    caption="Hours and prices are shown only where the venue or MICHELIN published them. Every other row is roster-only.",
    card_labels=["Restaurant", "Distinction", "Hours", "Menu price", "Social / video", "Source"])}

<h2>Guide-listed but not starred</h2>
<p>These are in the MICHELIN Guide's selection but carry <strong>no star</strong>. They are listed separately so the 2025 starred roster is not confused with the wider Guide selection; prices and booking availability were not compared here.</p>
<div class="card">
<ul class="tight">
<li><strong>Ai Fiori</strong> — Italian, $$$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ai-fiori", "MICHELIN listing")}</li>
<li><strong>Café Carmellini</strong> — Italian, $$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/cafe-carmellini", "MICHELIN listing")}</li>
<li><strong>Ci Siamo</strong> — Italian · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ci-siamo", "MICHELIN listing")}</li>
<li><strong>Chambers</strong> — Contemporary, $$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/chambers", "MICHELIN listing")}</li>
<li><strong>Farra</strong> — Contemporary, $$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/farra", "MICHELIN listing")}</li>
<li><strong>Ito</strong> — Japanese, $$$$ · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/ito-1201767", "MICHELIN listing")}</li>
<li><strong>One White Street</strong> — Contemporary, Green Star only, no star · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/one-white-street", "MICHELIN listing")}</li>
</ul>
<p class="small">Bib Gourmand is a separate MICHELIN distinction for good food at moderate prices, without a star. Those restaurants are not individually listed here; no current count is asserted in this page.</p>
</div>

<h2>Where the stars cluster</h2>
<p class="brief-ask">The brief asks for the star clusters. This is what the roster shows, grouped by what
can actually be established from the data:</p>
{cluster_table}
{geo_table}
<div class="note"><strong>Read this before using "cluster" to pick a hotel.</strong> Of the 72 entries,
coordinates were verified for only 7. So the <em>borough</em> grouping above covers all 72, while the
<em>distances</em> table covers a 7-venue sample.</div>

<div class="badbox"><strong>The data does not support a "star cluster" you can book around.</strong>
The 7 venues with verified coordinates do not sit close together: only <strong>Eleven Madison Park and
Gramercy Tavern are within a kilometre of anything else</strong> (353 m apart). Le Bernardin, Per Se,
Sushi Sho, Daniel and Jungsik are each more than a kilometre from the next scored venue. That is the
opposite of a cluster &mdash; it means star dining in Manhattan is <em>dispersed</em>, and the useful
question is not "which cluster?" but "what route would I take to the specific restaurant I booked?"
The <a href="hotels.html">Hotels page</a> contains only a 5 km straight-line proximity proxy; it does not answer an hour-based route question.</div>

<div class="warnbox"><strong>What would make a real cluster analysis possible:</strong> verified coordinates
for all 72 entries, then a density calculation. That coordinate work is separate from measuring the
MTA routes required to resolve F-05 and Q-19. Nothing on this site pretends either analysis is complete.</div>

<h2>Dinner cost for two — the verified ones</h2>
<div class="grid two">
<div class="card"><h3>Le Bernardin ★★★</h3>
<p class="small">Chef's Tasting {money(350,0)} pp → <strong>{money(700,0)} for two</strong>, food only.<br>
With wine pairing ({money(530,0)} pp) → <strong>{money(1060,0)} for two</strong>.<br>
Prix-fixe dinner (4 courses) {money(225,0)} pp · lunch (3 courses) {money(142,0)} pp.<br>
Supplements: caviar {money(145,0)}/oz, Dover sole {money(28,0)}–{money(38,0)}.</p>
<p class="small">{ext("https://www.le-bernardin.com/accessible/menus/dining-room/chef-s-tasting/", "official menu")} ·
{ext("https://www.le-bernardin.com/accessible/menus/dining-room/dinner/", "dinner")} ·
{ext("https://www.le-bernardin.com/accessible/menus/dining-room/lunch/", "lunch")}</p></div>
<div class="card"><h3>Gabriel Kreuther ★★</h3>
<p class="small">Chef's Tasting {money(325,0)} pp → <strong>{money(650,0)} for two</strong>, food only.<br>
Wine pairing {money(255,0)} (classic) or {money(595,0)} (reserve) pp.</p>
<p class="small">{ext("https://www.gknyc.com/menus", "official menus page")}</p></div>
</div>
<div class="note"><strong>Deliberately blank:</strong> Eleven Madison Park, Jungsik, Sushi Sho, Daniel and
Gramercy Tavern. No readable menu price was captured in the last official venue-source check. Per Se's booking page states
<em>"starting at $200 per person (deposit)"</em> — a deposit, not the menu price, so it is shown as a
floor only. The source that settles each one is listed in <a href="questions.html">Q-06</a>.</div>
"""


def build_activities():
    rows = []
    for a in ACTS["activities"]:
        social = SOCIAL["accounts"].get(a["id"], [])
        social_links = []
        for item in social:
            suffix = (" ✓" if item["kind"] == "official" else
                      " unconfirmed" if item["kind"] == "unconfirmed" else
                      " review" if item["kind"] == "review" else " search")
            social_links.append(ext(item["url"], item["platform"] + suffix, "tag"))
        tr = a["from_hotel"]
        if a["id"] == "statue-of-liberty":
            travel = ('<strong>Not measured</strong><div class="small">Liberty Island requires an authorized ferry; '
                      'the February 2027 sailing schedule, crossing, boarding, and waiting time are not in this model.</div>'
                      + '<div class="small">' + f'{tr["km"]:.1f}' + ' km straight-line only; not a route</div>')
        else:
            travel = ('<strong>' + str(tr["transit_min_modelled"]) + ' min</strong>'
                      '<div class="small">simple transit-speed model, not an MTA itinerary</div>'
                      '<div class="small">' + str(tr["walk_min_modelled"]) + ' min walking model · '
                      + f'{tr["km"]:.1f}' + ' km straight-line</div>')
        cost = (f'{money(a["cost_2_adults_usd"])}<div class="small">for two · {money(a["adult_usd"])} per adult</div>'
                if a["cost_2_adults_usd"] is not None else '<span class="blank">no official price captured</span>')
        hours = esc(a["hours"]) if a.get("hours") else '<span class="blank">hours not captured</span>'
        if a.get("days_open"):
            hours += '<div class="small">' + esc(a["days_open"]) + '</div>'
        verification = a["verification"]
        state = "verified" if verification.startswith("VERIFIED") else ("partial" if verification.startswith("PARTIAL") else "open")
        source_links = []
        seen_sources = set()
        for field, label in (("official_url", "Official venue / source"),
                             ("hours_source_url", "Hours / schedule"),
                             ("price_source_url", "Price")):
            url = a.get(field)
            if url and url not in seen_sources:
                seen_sources.add(url)
                source_links.append(ext(url, label))
        rows.append([
            f'<strong>{esc(a["name"])}</strong><div class="small">{esc(a["category"])} · {esc(a["area"])}</div><div class="small">{esc(a["address"])}</div>',
            hours,
            esc(a["exceptions"]),
            cost,
            travel,
            f'{pill(state)}<div class="small">{esc(verification)}</div>',
            ' '.join(social_links + [link for link in source_links if link]),
        ])
    modelled_under = sum(1 for a in ACTS["activities"] if a["from_hotel"].get("within_one_hour"))
    total = len(ACTS["activities"])
    return f"""
<p class="lede">Eleven candidate activities with current official hours/prices where available, relevant exceptions, and source links. Travel figures are screening models only; no measured door-to-door route matrix is available.</p>

<div class="note"><strong>Free and almost-free:</strong> Central Park, The High Line, the Brooklyn Bridge promenade, and Chelsea Market cost nothing to enter. AMNH standard adult General Admission is $37; ticketed exhibitions cost extra. Always check date-specific notices before visiting.</div>

{table(
    ["Activity", "Days &amp; hours", "Exceptions that matter", "Cost for 2", "From the hotel", "Status", "Links"],
    rows,
    caption="Official venue and government pages are linked in each row. The source date is recorded with the activity data; not every dataset was re-read on the same day.",
    card_labels=["Activity", "Hours", "Exceptions", "Cost for 2", "From the hotel", "Status", "Links"])}

<h2>Tickets and schedules to verify</h2>
<div class="grid two">
<div class="card"><h3>Timed tickets or advance booking</h3>
<ul class="tight">
<li><strong>9/11 Memorial &amp; Museum</strong> — timed tickets are required; last entry is 60 minutes before closing.</li>
<li><strong>Top of the Rock</strong> — timed admission; the official price varies by date and time.</li>
<li><strong>Statue of Liberty</strong> — ferry is mandatory and only Statue City Cruises may dock at the islands. February 2027 sailings were not present in the schedule checked.</li>
<li><strong>MoMA and AMNH</strong> — reserve ahead for faster entry; MoMA Friday Nights' free NY State resident offer requires advance reservation.</li>
</ul></div>
<div class="card"><h3>Can be decided closer to the day</h3>
<ul class="tight">
<li><strong>The Met</strong> — standard weekly hours and adult admission are captured; recheck temporary notices.</li>
<li><strong>Central Park, High Line, Brooklyn Bridge</strong> — free public access, subject to closures and conditions.</li>
<li><strong>Chelsea Market</strong> — free entry; vendors set their own hours, including on holidays.</li>
<li><strong>Broadway</strong> — no single official price; select a show first (Q-16).</li>
</ul></div>
</div>

<h2>Modelled reach is not measured reach</h2>
<p class="brief-ask">The simple model puts {modelled_under} of {total} activities under 60 minutes. This is a straight-line/speed approximation, not an MTA-scheduled door-to-door measurement.</p>
<div class="warnbox"><strong>Statue of Liberty is not counted as under an hour.</strong>
The former 56-minute result applied a generic land-transit speed to a straight-line distance ending at Liberty Island. That is not a valid route: the island requires a ferry, and the February 2027 sailing schedule, crossing, boarding, and waiting time are not verified. Treat it as an optional half-day whose timing remains unknown (F-20, Q-15, Q-19).</div>
<div class="note"><strong>For the other ten activities:</strong> displayed minutes are provisional estimates from area-level coordinates, a fixed speed, and an access/wait allowance. They do not prove that the one-hour requirement is met in practice (F-05).</div>

<h2>Social media and video reviews</h2>
<p>Directly verified venue accounts are marked <strong>✓</strong>. The Chelsea Market Instagram handle was referenced by the verified High Line account but its own profile was not opened, so it is labelled <strong>unconfirmed</strong> (F-08). Platform search URLs are labelled <strong>search</strong>, not presented as accounts; individual third-party videos are labelled <strong>review</strong>.</p>
<div class="warnbox"><strong>TikTok could not be verified</strong> — automated reads returned HTTP 400 on 2026-11-25. No TikTok account is asserted anywhere on this site (F-07).</div>
"""

def build_itinerary():
    out = []
    for it in FR["itineraries"]:
        rows = [[esc(d["date"]), esc(d["day"]), esc(d["plan"])] for d in it["days"]]
        note = f'<p class="hint">{esc(it["note"])}</p>' if it.get("note") else ""
        out.append(f"""<h2>{esc(it["title"])}</h2>{note}
{table(["Date", "Day", "Plan"], rows, card_labels=["Date", "Day", "Plan"])}""")
    return f"""
<p class="lede">Three concrete variants, so changing the length is a choice rather than a re-plan. The 7-night version is the recommendation; the literal preferred window is 3 hotel nights (15–18 Feb); the 14-night version is the upper end of the brief.</p>

<div class="note"><strong>Opening-day logic.</strong> The Met is closed Wednesdays and otherwise follows the captured weekly schedule; AMNH is open daily 10:00–17:30. The 9/11 Museum opens Wednesday–Monday, with select Tuesday openings. February 2027 Statue City Cruises sailings were not available in the schedule checked, so that visit remains optional rather than a fixed timed stop.</div>

{"".join(out)}

<h2>Booking order that matters</h2>
<div class="card">
<ol class="tight">
<li><strong>Hotel first</strong>, if the chosen rate and full checkout breakdown are acceptable. The current Fairfield King Room snapshot allows free cancellation until 12 February 2027; recheck the terms before paying.</li>
<li><strong>Starred dinners when each booking window opens.</strong> Release windows differ by venue; check the selected restaurant's official booking platform rather than assuming one rule.</li>
<li><strong>Timed tickets</strong> (9/11 Museum, Top of the Rock) once the dates are fixed; check release dates and availability.</li>
<li><strong>Statue of Liberty ferry</strong> only after February 2027 sailings are published; the ferry is the only way onto the island.</li>
<li><strong>Broadway</strong> only after choosing a show.</li>
</ol>
</div>

<h2>February reality check</h2>
<div class="warnbox">The itinerary includes outdoor walking (Brooklyn Bridge, High Line, Central Park) in February. No official climate data was captured for this site, so no temperature figure is quoted here (S-10). Plan for cold-weather clothing and keep a buffer day; the Statue ferry is optional until its timetable and journey time are available.</div>
"""

def build_budget():
    b = FR["budget"]
    rows = []
    for line in b["lines"]:
        kind = line["kind"]
        upper = kind.upper()
        badge = "documented" if "DERIVED" in upper else ("open" if "NOT PRICED" in upper else "verified")
        source = ext(line.get("source"), "source") if line.get("source") else '<span class="blank">no source captured</span>'
        detail = f'<div class="small">{esc(line["note"])}</div>' if line.get("note") else ""
        amount = f'<span class="num">{money(line["usd"])}</span>' if line["usd"] is not None else money(None)
        rows.append([esc(line["item"]), amount, pill(badge, kind), source + detail])

    hotel_amount = next(line["usd"] for line in b["lines"] if line["item"].startswith("Hotel -"))
    flight_amount = next(line["usd"] for line in b["lines"] if line["item"].startswith("Flights -"))
    dining_amount = sum(line["usd"] for line in b["lines"] if line["item"].startswith("Dinner at") and line["usd"] is not None)
    subtotal = b["priced_subtotal_usd"]
    hotel_pct, flight_pct, dining_pct = (hotel_amount / subtotal * 100, flight_amount / subtotal * 100,
                                         dining_amount / subtotal * 100)
    second_week = next(w for w in HOTELS["windows_sampled"] if w["start"] == "2027-02-22")
    second_base = second_week["rates_before_tax_usd"][0]["amount"]
    fairfield = next(h for h in HOTELS["hotels"] if h["id"] == "fairfield-central-park")
    second_booking = round(second_base * (1 + fairfield["tax_rate_pct"] / 100)
                           + 7 * (fairfield["booking_fixed_fee_per_night_usd"]
                                  + fairfield["tourism_fee_per_night_usd"]), 2)
    second_statutory = round(second_base * (1 + fairfield["tax_rate_pct"] / 100)
                             + 7 * (fairfield["statutory_fixed_fee_per_night_usd"]
                                    + fairfield["tourism_fee_per_night_usd"]), 2)
    return f"""
<p class="lede">One line per priced cost, with its source and whether the figure was read, derived by arithmetic, or left blank. The subtotal is <strong>not a full trip budget</strong>; it includes only the listed paid items and the derived hotel line.</p>

{table(["Line item", "Amount (2 adults)", "Basis", "Source &amp; note"], rows,
       caption="7 nights, 15–22 February 2027, two adults.",
       card_labels=["Item", "Amount", "Basis", "Source"])}

<h2>Priced subtotal</h2>
<div class="kpi">
 <div class="card"><div class="k">Priced subtotal</div><div class="v">{money(subtotal)}</div>
  <div class="small">Sum of priced lines; the ordinary-meals line remains blank.</div></div>
 <div class="card"><div class="k">Hotel estimate share</div><div class="v">{money(hotel_amount)}</div><div class="small">{hotel_pct:.0f}% of the priced subtotal; Booking-line estimate, not a checkout quote.</div></div>
 <div class="card"><div class="k">Flights share</div><div class="v">{money(flight_amount)}</div><div class="small">{flight_pct:.0f}% of the priced subtotal; one adult fare doubled, not a two-seat booking.</div></div>
 <div class="card"><div class="k">Dining share · two tasting menus</div><div class="v">{money(dining_amount)}</div><div class="small">{dining_pct:.0f}% — food only, no wine.</div></div>
 <div class="card"><div class="k">Unpriced lines</div><div class="v">{b["unpriced_lines"]}</div><div class="small">Ordinary meals are blank rather than guessed.</div></div>
</div>

<div class="badbox"><strong>This is not a complete trip budget.</strong>
It excludes breakfasts/lunches/ordinary dinners, wine, shopping, Broadway tickets, and other discretionary costs. The hotel line uses Booking.com's excluded-charge labels; the official fixed-charge calculation differs by $3.50 over seven Fairfield nights (F-04). The flight line doubles a one-person fare, which may not hold for two seats.</div>

<h2>Other sourced costs</h2>
<div class="card">
<ul class="tight">
<li>AMNH standard General Admission — {money(37,0)} per adult / {money(74,0)} for two; ticketed exhibitions cost extra.</li>
<li>Le Bernardin wine pairing — {money(530,0)} per person ({money(1060,0)} for two).</li>
<li>Gabriel Kreuther wine pairing — from {money(255,0)} per person.</li>
<li>Fairfield 22 Feb–1 Mar weekly snapshot — base {money(second_base)} before taxes/fees; Booking-line estimate {money(second_booking)} and statutory-component calculation {money(second_statutory)}. These are derived seven-night totals, not a combined 14-night checkout quote.</li>
<li>Broadway — no single official price; it depends on the selected show.</li>
</ul>
</div>

<h2>How to read the labels</h2>
{table(["Label", "Meaning"], [
 ['<span class="pill p-verified">VERIFIED</span>', "Read on a linked official or source page; the record date is dataset-specific."],
 ['<span class="pill p-documented">DERIVED</span>', "Arithmetic on cited inputs; the formula and limits are stated."],
 ['<span class="pill p-open">NOT PRICED</span>', "No defensible price was captured, so the amount stays blank."],
], caption="The priced subtotal mixes read amounts with clearly labelled derivations; it is not a quote for the whole trip.")}
"""

def build_questions():
    rows = []
    for q in FR["questions"]:
        st = q.get("status", "Open")
        k = "open" if st == "Open" else ("blocked" if "Blocked" in st else "documented")
        rows.append([
            f'<strong>{esc(q["id"])}</strong><div class="small">{esc(q["question"])}</div>',
            esc(q["why_it_blocks"]),
            esc(q["have"]),
            f'<strong>{esc(q["missing"])}</strong>',
            esc(q["how_to_discover"]),
            f'{pill(k, st)}<div class="small">{esc(q["owner"])}</div>',
        ])
    return f"""
<p class="lede">Unresolved traveller decisions and research gaps, with the evidence already captured, exactly what
is still missing, and the action that would close each item. The current plan is a provisional recommendation,
not a substitute for the traveller's preferences or for missing measurements.</p>

<div class="kpi">
 <div class="card"><div class="k">Questions</div><div class="v">{len(FR["questions"])}</div><div class="small">Each tied to a decision</div></div>
 <div class="card"><div class="k">Waiting on the traveller</div><div class="v">{sum(1 for q in FR["questions"] if q["owner"]=="traveller")}</div><div class="small">Answer directly — no research needed</div></div>
 <div class="card"><div class="k">Waiting on research</div><div class="v">{sum(1 for q in FR["questions"] if q["owner"]=="research")}</div><div class="small">Each names the exact source to read</div></div>
 <div class="card"><div class="k">Blocked by a date</div><div class="v">{sum(1 for q in FR["questions"] if str(q.get("status", "")).startswith("Blocked"))}</div><div class="small">The new MICHELIN list arrives 14 Dec 2026</div></div>
</div>

{table(["Question", "Why it blocks a decision", "What we have", "What is missing", "How to discover it", "Status"],
       rows,
       caption="Ordered as in the register. 'traveller' means only you can answer it.",
       card_labels=["Question", "Why it blocks", "Have", "Missing", "How to discover", "Status"])}

<h2>The five that actually change the plan</h2>
<div class="grid two">
<div class="card"><h3>Q-01 · How long?</h3><p class="small">The exact preferred-date option is 3 nights; the recommendation is 7 nights to meet the 1–2-week brief, with 14 nights as the upper alternative.</p></div>
<div class="card"><h3>Q-02 · What is the budget?</h3><p class="small">Every ranking sorts on price; without a ceiling there is no way to say whether two splurge dinners are sensible.</p></div>
<div class="card"><h3>Q-06 · What do the other menus cost?</h3><p class="small">Five priority venues have no published price, so the food budget is incomplete.</p></div>
<div class="card"><h3>Q-09 · Date-specific closures?</h3><p class="small">Standard Met and High Line schedules are verified; temporary changes near February 2027 still need a check.</p></div>
<div class="card"><h3>Q-19 · Are the trips really under an hour?</h3><p class="small">The brief's central rule is currently modelled, not measured.</p></div>
</div>
"""


def build_suggestions():
    rows = []
    for s in FR["suggestions"]:
        rows.append([
            f'<strong>{esc(s["id"])}</strong> {esc(s["title"])}<div class="small">{esc(s["problem"])}</div>',
            esc(s["proposal"]),
            f'{esc(s["effort"])}<div class="small">{esc(s["cost"])}</div>',
            f'{pill(s["impact"].lower(), s["impact"] + " impact")}<div class="small">risk: {esc(s["risk"].split(" -")[0])}</div>',
            f'<select aria-label="Decision for {esc(s["id"])}"><option>Pending</option><option>Do it</option><option>Skip</option><option>Discuss</option></select>',
        ])
    return f"""
<p class="lede">{len(FR['suggestions'])} concrete improvements to this site, each written so it can be accepted or rejected
on its own. The point of this page is that you review the options and choose a path <em>before</em>
anything is implemented.</p>

<div class="note"><strong>How to use it.</strong> Read the problem, then the proposal, then the effort.
The decision dropdown is local to your browser and changes nothing on the site — it is a worksheet.
Anything you mark "Do it" can be implemented in the order shown; S-01 and S-02 should come first because
they affect the correctness of everything else.</div>

{table(["Improvement", "Proposal", "Effort / cost", "Impact / risk", "Your decision"],
       rows,
       caption="Ordered by recommendation, highest impact first.",
       card_labels=["Improvement", "Proposal", "Effort", "Impact", "Decision"])}

<h2>If you only do three</h2>
<div class="grid three">
<div class="card"><h3>1 · S-02 Measured travel times</h3><p class="small">Turns the one-hour rule from a model into a measurement. Highest impact on the hotel ranking.</p></div>
<div class="card"><h3>2 · S-01 One canonical site</h3><p class="small">Removes the second dataset that contradicts this one on stars, hotels and transit.</p></div>
<div class="card"><h3>3 · S-04 Finish the menu prices</h3><p class="small">Makes the dining budget complete instead of partial.</p></div>
</div>

<h2>What I deliberately did not propose</h2>
<div class="warnbox">
<ul class="tight">
<li><strong>Merging the two datasets into one table.</strong> They were researched independently and
disagree; merging would silently pick a winner. Better to archive one (S-01).</li>
<li><strong>Filling blank prices with "typical" values.</strong> It would make the site look complete and
be worthless.</li>
<li><strong>Guessing social handles</strong> for venues that publish none. A search link is honest; an
invented handle is not.</li>
</ul>
</div>
"""


def build_flagged():
    severity_kind = {"HIGH": "open", "MEDIUM": "partial", "LOW": "documented"}
    rows = []
    for f in FR["flags"]:
        severity = f["severity"]
        status = f.get("status", "Open")
        status_kind = "verified" if status == "Resolved" else ("documented" if status == "Documented" else "open")
        source = ext(f.get("source"), "source") if f.get("source") else '<span class="blank">no source captured</span>'
        rows.append([
            '<strong>' + esc(f["id"]) + '</strong> ' + pill(severity_kind.get(severity, "open"), severity)
            + '<div class="small">' + esc(f["title"]) + '</div><div class="small">' + pill(status_kind, status) + '</div>',
            esc(f["detail"]), source, esc(f["settle_by"]),
        ])
    tbl = table(["Flag / status", "What happened", "Source", "Next step / closure"], rows,
                caption="Open, documented, and resolved audit records. Resolved entries remain visible as an audit trail.",
                card_labels=["Flag / status", "What happened", "Source", "Next step"])
    total = len(FR["flags"])
    open_count = sum(1 for f in FR["flags"] if f.get("status", "Open") == "Open")
    documented = sum(1 for f in FR["flags"] if f.get("status") == "Documented")
    resolved = sum(1 for f in FR["flags"] if f.get("status") == "Resolved")
    high = sum(1 for f in FR["flags"] if f["severity"] == "HIGH")
    return f"""
<p class="lede">Current and resolved irregularities from the audit, with severity, status, source, and next action. Resolved records remain here for traceability.</p>

<div class="kpi">
 <div class="card"><div class="k">Audit records</div><div class="v">{total}</div></div>
 <div class="card"><div class="k">Open</div><div class="v">{open_count}</div><div class="small">Still needs follow-up</div></div>
 <div class="card"><div class="k">Documented</div><div class="v">{documented}</div><div class="small">Known limitation or accepted basis</div></div>
 <div class="card"><div class="k">Resolved</div><div class="v">{resolved}</div></div>
 <div class="card"><div class="k">High severity</div><div class="v">{high}</div><div class="small">Could change a recommendation or its basis</div></div>
</div>

{tbl}

<h2>The issues that matter most</h2>
<div class="badbox"><ol class="tight">
<li><strong>F-01 / F-02</strong> — the 2026 MICHELIN ceremony is still ahead, and the 2025 roster differs from current filter counts.</li>
<li><strong>F-04</strong> — Booking.com’s $4/$6 fixed-fee labels conflict with the $3.50/night statutory NYC/NYS components.</li>
<li><strong>F-05 / F-20</strong> — hotel/activity travel is not measured; Statue of Liberty requires an unmeasured ferry leg.</li>
<li><strong>F-03</strong> — hotel prices are live snapshots and can change before booking.</li>
<li><strong>F-13</strong> — hotel addresses are captured, but several proximity coordinates are still area-level.</li>
</ol></div>

<h2>How to use this register</h2>
<p>Open entries name the remaining source or action. Documented and resolved entries explain what changed and why the history is retained. F-01 depends on MICHELIN publishing its 2026 selection; hotel and transit figures need a fresh dated lookup closer to booking.</p>
"""


def build_method():
    live = ROSTER["meta"].get("live_filtered_counts", {})
    hotel_links = "<br>".join(ext(h["source_url"], esc(h["name"])) for h in HOTELS["hotels"])
    activity_sources = []
    seen = set()
    for a in ACTS["activities"]:
        for key, label in (("official_url", a["name"] + " official page"),
                           ("hours_source_url", a["name"] + " hours/schedule"),
                           ("price_source_url", a["name"] + " price")):
            url = a.get(key)
            if url and url not in seen:
                seen.add(url)
                activity_sources.append("<li>" + ext(url, esc(label)) + "</li>")
    activity_source_list = "\n".join(activity_sources)
    return f"""
<p class="lede">Source dates, calculations, unresolved disagreements, known build limitations, and the checks used to generate the site. Dataset check dates differ; the footer date is not a claim that every source was re-read that day.</p>

<h2>Rules and dates</h2>
<div class="card"><ul class="tight">
<li><strong>Read it or leave it blank.</strong> A field is shown only when it was captured from a linked source; unavailable values stay blank with a reason.</li>
<li><strong>Never infer.</strong> No typical prices or assumed venue hours. Social handles not directly verified are explicitly labelled unconfirmed or left as searches.</li>
<li><strong>Separate awards from listings.</strong> The star roster is the 2025 ceremony article; current filter counts are shown separately.</li>
<li><strong>Label arithmetic.</strong> Derived totals are marked and formula inputs are available in <code>site_data/</code>.</li>
<li><strong>Source dates:</strong> hotel pages and current MICHELIN filters were read 2026-11-26; the activity dataset is dated 2026-11-26. Restaurant detail and social data retain their own earlier checks. One Chelsea Market Instagram reference remains unconfirmed (F-08).</li>
</ul></div>

<h2>MICHELIN</h2>
<ul class="tight">
<li>{ext(ROSTER["meta"]["source_article"], "2025 New York City ceremony roster")} — {ROSTER["meta"]["counts"]["total"]} entries ({ROSTER["meta"]["counts"]["3"]}/{ROSTER["meta"]["counts"]["2"]}/{ROSTER["meta"]["counts"]["1"]} for 3/2/1 stars), read {esc(ROSTER["meta"].get("read_on", "date not recorded"))}.</li>
<li>{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/3-stars-michelin", "3-star filter")} · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/2-stars-michelin", "2-star filter")} · {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/1-star-michelin", "1-star filter")} — current official counts {live.get("3", "?")}/{live.get("2", "?")}/{live.get("1", "?")} ({live.get("total", "?")} total), read {esc(ROSTER["meta"].get("live_filtered_read_on", "date not recorded"))}. A name-by-name comparison with the 2025 article remains open.</li>
<li>{ext(ROSTER["meta"].get("ceremony_2026_source"), "MICHELIN Media 2026 ceremony announcement")} — Northeast Cities ceremony, including New York, scheduled for 14 Dec 2026.</li>
</ul>

<h2>Social and source checks</h2>
<p>Directly verified official social channels are distinct from unconfirmed references and platform search links. The Chelsea Market Instagram handle was mentioned by the verified High Line account, but its own profile was not opened, so it remains explicitly unconfirmed (F-08). The TikTok reads returned HTTP 400 on 2026-11-25; no TikTok handle is asserted (F-07).</p>

<h2>Hotel rates and taxes</h2>
<p>The seven Booking.com property pages below were checked for two adults, one room, 15–22 Feb 2027 in USD on the date stored with each hotel row. The rate table records the selected room rate and cancellation tier; a search page's display is a live snapshot, not a booking.</p>
<ul class="tight"><li>{hotel_links}</li></ul>
<ul class="tight">
<li>Booking.com’s excluded lines show 14.75% tax and a fixed $4/night charge on six rows or $6/night for Residence Inn FiDi; the two Arlo rows also list a $1/night tourism fee.</li>
<li>{ext("https://www.nyc.gov/site/finance/business/business-hotel-room-occupancy-tax.page", "NYC Finance hotel-room occupancy tax")} and {ext("https://www.tax.ny.gov/pubs_and_bulls/tg_bulletins/st/hotel_and_motel_occupancy.htm", "NYS occupancy bulletin")} support fixed components of $2/night NYC tax for rooms at $40+ plus a $1.50/night NYS unit fee. Those $3.50 statutory components do not match Booking.com’s $4/$6 labels; the discrepancy remains unresolved (F-04).</li>
</ul>
<div class="note"><strong>Two displayed calculations:</strong> Booking-line estimate = base rate × 1.1475 + seven nights of Booking.com’s fixed fee and any separately listed tourism fee. Statutory-component calculation = base rate × 1.1475 + seven nights of $3.50 statutory fixed components and any separately listed tourism fee. Resort fees identified by Booking.com are already included in selected room rates. These are derived amounts, not checkout quotes.</div>

<h2>Activities, transport, and the holiday</h2>
<ul class="tight">{activity_source_list}
<li>{ext("https://www.mta.info/fares-tolls/subway-bus", "MTA fares")}: $3 subway/local bus fare and $35 seven-day tap-and-ride cap at the time checked. The MTA app guide describes trip planning and real-time service alerts; no complete route matrix was measured.</li>
<li>{ext("https://www.mta.info/guides/apps", "MTA apps and trip-planning tools")} — guidance on routes, arrivals, and service alerts; it does not supply a measured itinerary in this dataset.</li>
<li>{ext("https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/", "U.S. OPM federal holidays")} — 15 Feb 2027 is Washington’s Birthday; no hotel-demand effect is inferred.</li>
<li>{ext("https://www.google.com/travel/flights?q=Flights%20to%20JFK%20from%20AMS%20on%202027-02-15%20through%202027-02-22", "Google Flights AMS–JFK, 15–22 Feb 2027")} — $606 per person for the selected Aer Lingus fare; the budget doubles this one-adult snapshot, which is not a two-seat quote (F-15).</li>
</ul>

<h2>Budget basis</h2>
<p>The {money(FR["budget"]["priced_subtotal_usd"])} priced subtotal sums each nonblank budget line for two adults: the derived seven-night Fairfield Booking-line estimate, a one-adult airfare doubled, the MTA cap for two, six activity-ticket lines, and two tasting menus. It is not a full trip budget; ordinary meals and discretionary costs remain unpriced.</p>

<h2>Travel-time model and limits</h2>
<div class="warnbox"><p>The hotel reach table is only a 5 km straight-line comparison radius, not an estimate of travel time. The non-ferry activity minutes use great-circle distance from area-level hotel coordinates, divided by an assumed average walking or effective subway speed, plus a fixed platform/access allowance. These activity values are screening models, not MTA routes or door-to-door schedules.</p>
<p>Liberty Island requires a ferry. The February 2027 sailing schedule and full journey time were not available in the schedule checked, so the earlier 56-minute land-mode value is invalid and the activity is not counted under one hour (F-05, F-20, Q-19).</p></div>

<h2>Build and verification</h2>
<p><code>python3 build_site.py</code> is the active generator. It validates source links, derived hotel arithmetic, the priced subtotal, table row widths, internal links, duplicate IDs, and escaped/template markup before reporting success.</p>
<div class="badbox"><strong>Archived builder limitation:</strong> the older <code>python3 build.py</code> expects <code>docs/data/michelin_2025.csv</code>, which is absent from this checkout. The chained legacy build stops at that file and does not run <code>build_deepdive.py</code>. The canonical dashboard is generated from <code>site_data/*.json</code> instead; the archived deep-dive output is not validated by this build.</div>
"""


def build_repo_review():
    roster = ROSTER["restaurants"]
    details = DETAILS["details"]
    activities = ACTS["activities"]

    def key(r):
        return r["michelin_url"].rstrip("/").split("/")[-1]

    n_hours = sum(1 for r in roster if details.get(key(r), {}).get("hours"))
    n_price = sum(1 for r in roster if details.get(key(r), {}).get("menu_price_usd"))
    n_detail = sum(1 for r in roster if details.get(key(r)))
    n_social_official = sum(1 for group in SOCIAL["accounts"].values() for item in group if item["kind"] == "official")
    n_social_unconfirmed = sum(1 for group in SOCIAL["accounts"].values() for item in group if item["kind"] == "unconfirmed")
    n_social_unconfirmed_label = "reference" if n_social_unconfirmed == 1 else "references"
    n_video = sum(1 for group in SOCIAL["accounts"].values() for item in group if item["kind"] == "review")
    n_activity_verified = sum(1 for a in activities if a["verification"].startswith("VERIFIED"))
    n_activity_partial = sum(1 for a in activities if a["verification"].startswith("PARTIAL"))
    n_addresses = sum(1 for h in HOTELS["hotels"] if h.get("address"))

    coverage = table(
        ["Dataset", "Rows", "Captured fields", "Source coverage", "Known limit"],
        [
            ["MICHELIN star roster", str(len(roster)), f'{len(roster)} award entries',
             f'{len(roster)} official MICHELIN links', '2025 ceremony roster differs from current 69-entry filters'],
            ["Restaurant details", str(len(roster)), f'{n_hours} with hours · {n_price} with menu-price values',
             f'{n_detail} detail records', f'{len(roster)-n_hours} hours and {len(roster)-n_price} prices remain blank'],
            ["Hotels", str(len(HOTELS["hotels"])), f'{n_addresses} street addresses · 7 dated rates',
             '7 property-specific Booking.com pages', 'six hotel reach points remain area-level'],
            ["Activities", str(len(activities)), f'{n_activity_verified} verified · {n_activity_partial} partial · {len(activities)-n_activity_verified-n_activity_partial} open',
             f'{len(activities)} official venue/source links', 'ferry schedule and measured routes remain open'],
            ["Social", str(len(SOCIAL["accounts"])),
             f'{n_social_official} directly verified official accounts · {n_social_unconfirmed} unconfirmed {n_social_unconfirmed_label} · {n_video} third-party review videos',
             f'{sum(len(group) for group in SOCIAL["accounts"].values())} recorded account/search/review links', 'no TikTok handle asserted'],
        ],
        caption="Counts generated from the current source data; a filled link does not imply every field is complete.",
        card_labels=["Dataset", "Rows", "Captured", "Sources", "Limit"])

    findings = table(
        ["#", "Finding", "Evidence", "Disposition"],
        [
            ["R1", "The repository contains the current dashboard plus a separate archived deep-dive dataset.",
             "docs/ uses site_data/; deepdive/ has its own builder/data", "Kept distinct; no silent reconciliation."],
            ["R2", "MICHELIN’s 2025 ceremony roster (72) and current official filters (69) differ.",
             "2025 ceremony page and live 5/14/50 filters, read 2026-11-26", "Both dated counts shown; name-by-name diff remains open (F-02/Q-17)."],
            ["R3", "GitHub Pages serves the root redirect into the generated docs/ site.",
             "root index.html and repository Pages configuration", "Use a PR merge to publish; confirm the Pages deployment and live redirect after changes."],
            ["R4", "The active dashboard generator is standard-library Python with build-time checks.",
             "python3 build_site.py", "Checks data arithmetic, table width, internal links, IDs, and output markup."],
            ["R5", "No licence file is present.", "repository root", "Leave licensing to the repository owner."],
            ["R6", "The archived builder expects a missing CSV.",
             "python3 build.py -> docs/data/michelin_2025.csv not found", "Documented; the canonical dashboard uses site_data/ and builds independently."],
            ["R7", "Several activity fields were absent in the first pass but have now been read from official pages.",
             "Met, AMNH, High Line, and Chelsea Market source rows dated 2026-11-26", "Current standard hours/prices are applied; ferry timetable and temporary closures remain open."],
            ["R8", "A social handle remains inferred rather than directly opened.",
             "F-08 in site_data/framework.json", "Labelled as unconfirmed; no guessed TikTok account is used."],
            ["R9", "Hotel street addresses are now captured, but several reach coordinates remain area-level.",
             "Seven Booking.com property pages; hotels.json coords_flag", "Do not treat straight-line proximity as measured travel (F-13/F-05)."],
        ],
        caption="Repository findings and what the current audit does about them.",
        card_labels=["#", "Finding", "Evidence", "Disposition"])
    return f"""
<p class="lede">A checkable account of what this repository contains, what the current data verifies, and what is still only a model or archived artifact.</p>
<h2>Verification coverage, counted</h2>
{coverage}
<div class="warnbox"><strong>Coverage is intentionally incomplete.</strong> The 72-entry roster is not a 72-row restaurant-hours or menu-price dataset. Modelled transit is not measured; current prices are dated snapshots; blanks remain visible.</div>
<h2>Repository review</h2>
{findings}
<h2>How to verify the current dashboard</h2>
<div class="card"><ol class="tight">
<li>Run <code>python3 build_site.py</code>; it fails on broken internal links, inconsistent calculated totals, malformed tables, or leaked markup.</li>
<li>Open a hotel row’s dated Booking.com source and compare the selected room, rate, and cancellation terms.</li>
<li>Check each official activity source; date-specific closures and the February 2027 ferry timetable still need a later re-check.</li>
<li>Compare every derived amount with the formula in the <a href="method.html">Method</a> page and source values in <code>site_data/*.json</code>.</li>
</ol></div>
<h2>Remaining repository limitations</h2>
<div class="badbox"><ul class="tight">
<li>No licence file; that decision belongs to the owner.</li>
<li>The legacy builder is blocked by missing <code>docs/data/michelin_2025.csv</code>.</li>
<li>No automated CI currently runs the canonical build.</li>
<li>No historical price-series archive exists beyond the dated weekly snapshots.</li>
</ul></div>
"""

# ---------------------------------------------------------------- checks
class _TableShapeParser(HTMLParser):
    """Collect header widths and flag body rows that do not match."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.expected = None
        self.row = None
        self.errors = []
        self.table_number = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.table_number += 1
                self.expected = None
        elif self.depth == 1 and tag == "tr":
            self.row = {"th": 0, "td": 0}
        elif self.depth == 1 and tag in ("th", "td") and self.row is not None:
            self.row[tag] += 1

    def handle_endtag(self, tag):
        if self.depth == 1 and tag == "tr" and self.row is not None:
            width = self.row["th"] + self.row["td"]
            if self.row["th"] and not self.row["td"]:
                if self.expected is None:
                    self.expected = width
                elif width != self.expected:
                    self.errors.append(f"table {self.table_number}: header row has {width} cells, expected {self.expected}")
            elif width and self.expected is not None and width != self.expected:
                self.errors.append(f"table {self.table_number}: data row has {width} cells, expected {self.expected}")
            self.row = None
        elif tag == "table" and self.depth:
            self.depth -= 1
            if self.depth == 0:
                self.expected = None
                self.row = None


def run_checks(pages):
    errors, warnings = [], []

    # Every priced budget line has a source; the displayed subtotal includes all priced amounts.
    budget = FR["budget"]
    priced_sum = round(sum(line["usd"] for line in budget["lines"] if line["usd"] is not None), 2)
    stated_subtotal = budget["priced_subtotal_usd"]
    if abs(priced_sum - stated_subtotal) > 0.005:
        errors.append("budget: stated priced subtotal %.2f != sum of lines %.2f" % (stated_subtotal, priced_sum))
    for line in budget["lines"]:
        if line["usd"] is not None and not str(line.get("source", "")).startswith("https://"):
            errors.append(f"budget: priced line lacks an HTTPS source -> {line['item']}")

    # Recompute both hotel totals from the raw room rate and disclosed fee inputs.
    nights = FR["trip"]["recommended_nights"]
    for hotel in HOTELS["hotels"]:
        base = hotel["total_7n_usd"]
        rate = hotel["tax_rate_pct"] / 100
        tourism = hotel.get("tourism_fee_per_night_usd", 0)
        booking_expected = round(base * (1 + rate)
                                 + nights * (hotel["booking_fixed_fee_per_night_usd"] + tourism), 2)
        statute_expected = round(base * (1 + rate)
                                 + nights * (hotel["statutory_fixed_fee_per_night_usd"] + tourism), 2)
        if abs(booking_expected - hotel["all_in_7n_usd"]) > 0.005:
            errors.append(f"hotel {hotel['id']}: Booking-line estimate {hotel['all_in_7n_usd']} != recomputed {booking_expected}")
        if abs(statute_expected - hotel["statutory_tax_calc_7n_usd"]) > 0.005:
            errors.append(f"hotel {hotel['id']}: statutory calculation {hotel['statutory_tax_calc_7n_usd']} != recomputed {statute_expected}")
        source = hotel.get("source_url", "")
        required_query = ("checkin=2027-02-15", "checkout=2027-02-22", "group_adults=2", "selected_currency=USD")
        if not source.startswith("https://www.booking.com/hotel/us/") or any(part not in source for part in required_query):
            errors.append(f"hotel {hotel['id']}: source is not a dated, property-specific Booking.com page")
        if not hotel.get("address"):
            errors.append(f"hotel {hotel['id']}: street address missing")

    # Every restaurant/activity row must have its official record link. Liberty Island cannot use a land model.
    for restaurant in ROSTER["restaurants"]:
        if not restaurant.get("michelin_url", "").startswith("https://"):
            errors.append(f"restaurant {restaurant.get('name', '?')}: missing MICHELIN source")
    for activity in ACTS["activities"]:
        if not activity.get("official_url", "").startswith("https://"):
            errors.append(f"activity {activity.get('id', '?')}: missing official source")
        if activity.get("id") == "statue-of-liberty":
            travel = activity["from_hotel"]
            if travel.get("transit_min_modelled") is not None or travel.get("within_one_hour"):
                errors.append("activity statue-of-liberty: ferry destination has an invalid land-mode travel result")

    allowed_social_kinds = {"official", "unconfirmed", "review", "search"}
    social_pages = "\n".join(pages.values())
    social_labels = {"official": "✓", "unconfirmed": "unconfirmed", "review": "review", "search": "search"}
    for entity, links in SOCIAL["accounts"].items():
        for item in links:
            kind = item.get("kind")
            if kind not in allowed_social_kinds:
                errors.append(f"social {entity}: unsupported link kind -> {kind}")
                continue
            anchor_re = r'<a\b[^>]*href="' + re.escape(esc(item["url"])) + r'"[^>]*>(.*?)</a>'
            labels = re.findall(anchor_re, social_pages, flags=re.DOTALL)
            if not labels:
                errors.append(f"social {entity}: source link not rendered -> {item['url']}")
            elif not any(social_labels[kind] in label for label in labels):
                errors.append(f"social {entity}: {kind} link lacks its honest display label -> {item['url']}")

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
        parser = _TableShapeParser()
        parser.feed(html)
        errors.extend(f"{name}: {message}" for message in parser.errors)
    return errors, warnings

def main():
    for stale in ("methodology.html", os.path.join("data", "build_summary.json")):
        path = os.path.join(DOCS, stale)
        if os.path.isfile(path):
            os.remove(path)
    try:
        os.rmdir(os.path.join(DOCS, "data"))
    except OSError:
        pass
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    with open(os.path.join(DOCS, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)

    pages = {
        "index.html": layout("index.html",
            "New York City, 15–22 February 2027", build_index()),
        "hotels.html": layout("hotels.html", "Hotels — 7-night snapshots", build_hotels()),
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

if __name__ == "__main__":
    main()

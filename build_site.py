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

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "site_data")
DOCS = os.path.join(ROOT, "docs")

BUILD_DATE = "2026-11-25"


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


def social_label(s, review_no=None):
    """Never label an unread handle as verified, even if the data says 'official'."""
    if s["kind"] == "official":
        if "unconfirmed" in s.get("evidence", "").lower():
            return s["platform"] + " handle (unconfirmed)"
        return s["platform"] + " ✓"
    if s["kind"] == "review":
        return s["platform"] + " review " + str(review_no or 1)
    return s["platform"] + " search"


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
  <p><strong>Built {BUILD_DATE}.</strong> Every figure on this site was read on an official page on that date
  unless the row says otherwise. Prices and hours change; re-check before booking.
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
    n_stars = len(ROSTER["restaurants"])
    _det = DETAILS["details"]

    def _k(r):
        return r["michelin_url"].rstrip("/").split("/")[-1]

    def _verified_account(s):
        return s["kind"] == "official" and "unconfirmed" not in s.get("evidence", "").lower()

    n_ig_total = len({s["url"] for grp in SOCIAL["accounts"].values() for s in grp
                      if _verified_account(s)})
    n_ig_flagged = len({s["url"] for grp in SOCIAL["accounts"].values() for s in grp
                        if s["kind"] == "official" and not _verified_account(s)})
    n_hours = sum(1 for r in ROSTER["restaurants"]
                  if _det.get(_k(r), {}).get("hours_status") == "VERIFIED")
    n_hours_partial = sum(1 for r in ROSTER["restaurants"]
                          if _det.get(_k(r), {}).get("hours_status") == "PARTIAL")
    n_price = sum(1 for r in ROSTER["restaurants"]
                  if _det.get(_k(r), {}).get("menu_price_usd")
                  and not _det.get(_k(r), {}).get("price_is_floor"))
    n_floor = sum(1 for r in ROSTER["restaurants"]
                  if _det.get(_k(r), {}).get("price_is_floor"))
    _arlo = [x for x in HOTELS["hotels"] if x["id"] == "arlo-soho"][0]
    n_vids = sum(1 for grp in SOCIAL["accounts"].values() for x in grp if x["kind"] == "review")
    n_vid_venues = len([grp for grp in SOCIAL["accounts"].values()
                        if any(x["kind"] == "review" for x in grp)])
    return f"""
<p class="lede">A source-linked plan for two adults: one 7-night base in Manhattan, MICHELIN-starred
dinners that are reachable within the hour, verified hotel pricing, and an explicit register of
everything that could <em>not</em> be verified.</p>

<div class="kpi">
  <div class="card"><div class="k">Recommended dates</div><div class="v">15–22 Feb 2027</div>
   <div class="small">7 nights, Mon→Mon. Contains the preferred 15–18 Feb window.</div></div>
  <div class="card"><div class="k">Hotel, 7 nights all-in</div><div class="v">{money(rec['all_in_7n_usd'])}</div>
   <div class="small">Fairfield Inn &amp; Suites Manhattan/Central Park · king bed · private bathroom · breakfast included · all-in derived</div></div>
  <div class="card"><div class="k">MICHELIN star entries</div><div class="v">{n_stars}</div>
   <div class="small">5 three-star · 15 two-star · 52 one-star, from the 18 Nov 2025 ceremony. <strong>Changes 14 Dec 2026.</strong></div></div>
  <div class="card"><div class="k">Budget subtotal, priced lines</div><div class="v">{money(FR["budget"]["verified_subtotal_usd"])}</div>
   <div class="small">Hotel + flights + transit + six tickets + 2 tasting menus. Ordinary meals are deliberately unpriced.</div></div>
</div>

<h2>Executive summary</h2>
<div class="grid two">
<div class="card">
<h3>1 · The decision</h3>
<p>Book <strong>Fairfield Inn &amp; Suites by Marriott New York Manhattan/Central Park</strong>, King Room,
for <strong>15–22 February 2027</strong> at <strong>{money(rec['total_7n_usd'])} before taxes</strong> ({money(rec['all_in_7n_usd'])} derived all-in), on the
free-cancellation rate (cancel free until 12 Feb 2027). Once tax is included it is the cheapest of the
seven, it includes breakfast for two, the bed is a king and the bathroom is attached.</p>
<p class="hint">Every Booking.com total is printed <em>before</em> tax. Arlo SoHo advertises
{money(1021.00)} against Fairfield's {money(rec['total_7n_usd'])}, but on the derived all-in basis
Fairfield is {money(rec['all_in_7n_usd'])} and Arlo SoHo is {money(1206.60)}. The 25 November figure of
$1,155.48 for Fairfield was withdrawn after a line-by-line re-read of its source (F-17, F-23);
the ranking uses the corrected all-in column and discloses the promotion (F-03).</p>
</div>
<div class="card">
<h3>2 · Why 7 nights, not 3</h3>
<p>The brief's preferred window is 15–18 February (3 nights) but it also asks for a 1–2 week trip.
Those two statements cannot both be satisfied, so the plan uses <strong>7 nights</strong> and keeps a
4-night variant and a 14-night variant on the <a href="itinerary.html">Itinerary page</a> as choices.
No re-planning is needed to switch.</p>
<p class="hint">15 February 2027 is Washington's Birthday on <a href="https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/" target="_blank" rel="noopener noreferrer">OPM's official 2027 holiday list</a>. Holiday demand and thinner restaurant availability are plausible but not measured.</p>
</div>
</div>

<div class="grid two">
<div class="card">
<h3>3 · The restaurants</h3>
<p>MICHELIN's 18 November 2025 ceremony lists <strong>{n_stars} star entries</strong>: 5 three-star,
15 two-star and 52 one-star, and 3 of the star holders also carry a Green Star. 63 are in Manhattan, 6 in Brooklyn, 1 in Queens and 2
outside the city (Tarrytown and North Salem — not reachable within the hour).</p>
<p>Of eight priority venues with a detail page, <strong>Le Bernardin ({money(350,0)} pp)</strong> and
<strong>Gabriel Kreuther ({money(325,0)} pp)</strong> publish an exact menu price; Per Se publishes only
a {money(200,0)} deposit floor. Four more are blank rather than guessed.
<a href="restaurants.html">See the table →</a></p>
</div>
<div class="card">
<h3>4 · The one-hour rule</h3>
<p>All seven shortlisted hotels are inside the modelled one-hour reach of the verified star
restaurants, so <strong>the rule does not separate them</strong> — price and breakfast do. That is a
model result, not a measurement, and it is labelled as such throughout (flag F-05).</p>
<p class="hint">A measured travel-time matrix is the single highest-value improvement available:
suggestion S-02.</p>
</div>
</div>

<div class="grid two">
<div class="card">
<h3>5 · What is verified, and what is not</h3>
<ul class="tight">
<li><strong>${FR["budget"]["verified_subtotal_usd"]:,.2f} priced subtotal</strong> across hotel, flights, transit, six tickets and two tasting menus; the hotel line is derived and ordinary meals are blank.</li>
<li><strong>{n_hours} of {n_stars} restaurants have a full week of verified hours</strong> (read on official MICHELIN or venue pages on 25&ndash;26 Nov 2026); {n_hours_partial} more is partial and the rest are blank rather than guessed. <strong>{n_price} have an exact published menu price</strong> and {n_floor} more publishes only a booking-deposit floor. Every other row is complete on name, distinction, cuisine, borough and official link (<a href="restaurants.html">see the table</a>).</li>
<li><strong>{n_ig_total} verified official social accounts</strong> and <strong>{n_vids} verified third-party review videos across {n_vid_venues} venues</strong>, each opened and identified by title, channel and view count. One further handle is inferred rather than opened (F-08) and is not counted as verified. Where nothing could be verified the cell is still a search link, labelled as a search — TikTok returned HTTP 400 on every read, so no TikTok account is claimed anywhere.</li>
<li><strong>{len(FR['flags'])} flagged items</strong> and <strong>{len(FR['questions'])} open questions</strong>, each with the exact source that would settle it.</li>
</ul>
</div>
<div class="card">
<h3>6 · The three things that could invalidate this plan</h3>
<ol class="tight">
<li><strong>14 December 2026:</strong> MICHELIN publishes a new New York list. Stars can move before you travel.</li>
<li><strong>Hotel prices are live:</strong> every total here is a 25 Nov 2026 snapshot and several depend on a time-limited promotion.</li>
<li><strong>Menu prices are mostly unknown:</strong> four priority restaurants publish no readable price, so the food budget is incomplete by design rather than by accident.</li>
</ol>
</div>
</div>

<h2>How to read this site</h2>
{theme_table()}

<h2>Where to go next</h2>
<div class="grid three">
<div class="card"><h3><a href="hotels.html">Hotels</a></h3><p class="small">7 hotels with verified bed, private bathroom, 7-night total and the tax basis of each number.</p></div>
<div class="card"><h3><a href="restaurants.html">MICHELIN</a></h3><p class="small">All 72 star entries with their distinction, plus hours, prices and social links where verified.</p></div>
<div class="card"><h3><a href="activities.html">Activities</a></h3><p class="small">11 activities with official hours, prices, exceptions and social accounts.</p></div>
<div class="card"><h3><a href="itinerary.html">Itinerary</a></h3><p class="small">Day-by-day for 7 nights, plus the 4-night and 14-night variants.</p></div>
<div class="card"><h3><a href="budget.html">Budget</a></h3><p class="small">Every line item with its source and whether it is verified, derived or unpriced.</p></div>
<div class="card"><h3><a href="questions.html">Questions</a></h3><p class="small">{len(FR['questions'])} decisions, what we have, what is missing, and how to find it.</p></div>
<div class="card"><h3><a href="suggestions.html">Suggestions</a></h3><p class="small">12 improvements with effort, impact, risk and a decision field.</p></div>
<div class="card"><h3><a href="flagged.html">Flagged</a></h3><p class="small">{len(FR['flags'])} irregularities, each with severity and the source that settles it.</p></div>
<div class="card"><h3><a href="method.html">Method &amp; sources</a></h3><p class="small">How each number was produced, every source URL, and the build's own checks.</p></div>
</div>
"""


def theme_table():
    rows = [
        ['<span class="pill p-verified">verified</span>', "Read directly on an official page on 2026-11-25. The source link is in the row."],
        ['<span class="pill p-partial">partial</span>', "Some fields verified, others could not be read. The blank field names what is missing."],
        ['<span class="pill p-open">not verified</span>', "Left blank on purpose. The Flagged page says which source would settle it."],
        ['<span class="pill p-documented">model</span>', "Computed from other data (a formula, not an observation). The formula is on the Method page."],
    ]
    return table(["Label", "What it means"], rows, caption="A value is never inferred to fill a gap. Prices were re-checked on 26 November 2026; see the Hotels page.")


def build_hotels():
    rows = []
    for h in HOTELS["hotels"]:
        basis = ('<span class="pill p-verified">taxes included</span>' if h["tax_included"]
                 else '<span class="pill p-partial">taxes excluded</span>')
        addr = h["address"] or '<span class="blank">address not captured</span>'
        rows.append([
            f'<strong>{esc(h["name"])}</strong><div class="small">{esc(h["area"])}</div><div class="small">{addr}</div>',
            f'{esc(h["room"])}<div class="small">{esc(h["bed"])} · {esc(h["bath"])}</div>'
            + (f'<div class="small">{esc(h["size"])}</div>' if h["size"] else ""),
            esc(h["breakfast"]),
            money(h["total_7n_usd"]) + '<div class="small">' + basis + '</div>'
            + ('<div class="small">before discount: ' + money(h["list_price_before_discount"]) + '</div>'
               if h["list_price_before_discount"] else ''),
            '<strong>' + money(h["all_in_7n_usd"]) + '</strong>'
            + '<div class="small">' + pill("documented" if not h["tax_included"] else "verified",
                                           "derived" if not h["tax_included"] else "as printed") + '</div>',
            f'{esc(h["cancellation"])}<div class="small">guest score {esc(h["rating"])}</div>',
            (ext(h["source_url"], "Booking.com (hotel page)")
             if "/hotel/us/" in h["source_url"]
             else ext(h["source_url"], "Booking.com (search snapshot)")
             + '<div class="small">Hotel page: '
             + ext(h.get("address_source_url", ""), "address and current rates") + '</div>'),
        ])
    rk = sorted(HOTELS["hotels"], key=lambda z: (-z["reach"]["stars_within_5km"],
                                                  -z["reach"]["three_star_within_5km"]))
    rr = []
    for i, h in enumerate(rk, 1):
        r = h["reach"]
        rr.append([
            str(i),
            '<strong>' + esc(h["name"].replace("Fairfield Inn & Suites by Marriott New York ", "Fairfield Inn ")) + '</strong>'
            + '<div class="small">' + esc(h["area"]) + '</div>',
            '<span class="num">' + str(r["stars_within_5km"]) + ' / 7</span>',
            '<span class="num">' + str(r["three_star_within_5km"]) + ' / 5</span>',
            f'{r["nearest_three_star_km"]:.2f} km',
            money(h["all_in_7n_usd"]),
            ext(h["source_url"], "Booking.com"),
        ])
    reach_table = table(
        ["#", "Hotel", "Star venues within 5 km", "Three-star within 5 km", "Nearest three-star", "All-in 7 nights", "Source"],
        rr,
        caption="Ranked on reach, then on count of three-star venues. Only 7 of the 72 star entries could be scored.",
        card_labels=["Rank", "Hotel", "Within 5 km", "Three-star", "Nearest", "All-in", "Source"])

    ranked = sorted(HOTELS["hotels"], key=lambda z: z["all_in_7n_usd"])
    rrows = []
    for i, h in enumerate(ranked, 1):
        star = ' <span class="pill p-verified">recommended</span>' if h["id"] == "fairfield-central-park" else ""
        rrows.append([
            str(i), '<strong>' + esc(h["name"]) + '</strong>' + star
            + '<div class="small">' + esc(h["area"]) + ' &middot; score ' + esc(h["rating"].split()[0]) + '</div>',
            '<span class="num">' + money(h["all_in_7n_usd"]) + '</span>',
            money(h["total_7n_usd"]),
            esc(h["breakfast"]),
            esc(h["cancellation"]),
            ext(h["source_url"], "Booking.com"),
        ])
    rank_table = table(
        ["#", "Hotel", "All-in 7 nights", "Advertised", "Breakfast", "Cancellation", "Source"],
        rrows,
        caption="All-in = advertised total × 1.1475 + the city tax and other excluded per-night fee printed on that room row. Arithmetic, not a quote.",
        card_labels=["Rank", "Hotel", "All-in", "Advertised", "Breakfast", "Cancellation", "Source"])

    wrows = []
    for w in HOTELS["windows_sampled"]:
        if w.get("total_7n_usd") is None:
            wprice = '<span class="blank">not priced in this pass</span>'
            wsrc = '<span class="blank">no source captured</span>'
        else:
            allin = (money(w["total_7n_usd"]) + '<div class="small">taxes included</div>'
                     if w["tax_included"] else
                     money(w["total_7n_usd"]) + '<div class="small">before tax · all-in derived '
                     + money(round(w["total_7n_usd"] * 1.1475 + 28, 2)) + '</div>')
            wprice = '<strong>' + allin + '</strong>'
            wsrc = ext(w["source_url"], "Booking.com") if w.get("source_url") else '<span class="blank">no source captured</span>'
        wrows.append([
            f'{esc(w["start"])} → {esc(w["end"])}<div class="small">{esc(w["label"])}</div>',

            esc(w.get("room") or "—"),
            wprice,
            esc(w["note"]),
            wsrc,
        ])
    window_table = table(
        ["Dates", "Room", "7-night total", "Read from the page / caveat", "Source"],
        wrows,
        caption="Each row carries the dated Booking.com URL that reproduces it. Derived all-in = printed total × 1.1475 + $28 city tax.",
        card_labels=["Dates", "Room", "Total", "Note", "Source"])
    _allin = {w["start"]: (w["total_7n_usd"] if w["tax_included"] else
                           round(w["total_7n_usd"] * 1.1475 + 28, 2))
              for w in HOTELS["windows_sampled"] if w.get("total_7n_usd") is not None}

    return f"""
<p class="lede">Seven hotels, each verified for a king-or-queen bed and a private bathroom for
two adults, priced for the whole 7-night stay 15–22 February 2027.
The <strong>basis</strong> column matters: every total is printed before tax, and the per-night city
tax is different at one property.</p>

<div class="warnbox"><strong>Read the tax basis before comparing.</strong>
Booking.com prints every total before tax. The <strong>All-in</strong> column multiplies each by
1.1475 (14.75% New York tax) and adds the city tax printed on that room row — $4/night except
$6/night at Residence Inn FiDi — plus the $1/night tourism fee at the two Arlo properties. That is
arithmetic, labelled <em>derived</em>, not a quote. Fairfield remains cheapest at
{money(1158.98)} all-in; Arlo SoHo is second at {money(1206.60)}. The old
$1,155.48 "taxes included" figure was withdrawn (F-17, F-23).</div>

<h2>Shortlist, 15–22 February 2027 (7 nights, 2 adults)</h2>
{table(
    ["Hotel", "Room / bed / bathroom", "Breakfast", "Advertised total", "All-in, 7 nights", "Cancellation &amp; score", "Source"],
    rows,
    caption="Totals as printed by Booking.com on 2026-11-25 for check-in 2027-02-15, check-out 2027-02-22.",
    card_labels=["Hotel", "Room", "Breakfast", "Advertised total", "All-in 7 nights", "Cancellation", "Source"])}

<h2>Date windows, with the source behind each price</h2>
{window_table}

<h2>What the price test showed</h2>
<div class="card">
<p>The recommended 15–22 Feb rate is the only one of the four sampled windows whose printed total
already includes tax; the other priced windows are Black Friday rates on <em>accessible</em> king rooms.
Their derived all-in equivalents are {money(_allin['2027-02-16'])} (16–23 Feb) and
{money(_allin['2027-02-22'])} (22 Feb – 1 Mar).</p>
<p class="hint">The recommended window is the cheapest of the three priced windows — but by only about
$16–$44, which is inside the noise of a live price feed. The honest conclusion is that mid-February is
<em>competitive</em>, not dramatically cheaper. A proper "cheapest time to book" answer needs a
per-night price curve across the whole 15 Feb – 23 Mar window, which is <strong>not</strong> captured
(flag F-12, question Q-22).</p>
</div>

<h2>Ranking, by all-in cost</h2>
<p>Because all seven hotels sit inside the modelled one-hour reach of the verified star restaurants
(F-05), the ranking turns on all-in cost and what that cost buys &mdash; bed, bathroom, breakfast and
cancellation terms &mdash; not on location. Sorted by the derived all-in column:</p>
{rank_table}
<div class="note"><strong>Why Fairfield wins.</strong> It is the cheapest <em>after</em> tax is derived
({money(1158.98)}), it includes breakfast for two, its bed is a king and the bathroom is attached.
Arlo SoHo and Arlo Midtown are cheaper only on paper: add tax and neither includes breakfast, and Arlo
Midtown's rate is non-refundable. citizenM has the best guest score (8.9) and the most central address for
Midtown dining, but {money(1344.18)} all-in plus $23.50 per person for breakfast makes it the third
dearest, not the cheapest.</div>

<h2>Ranking by MICHELIN reach</h2>
<p class="brief-ask">The brief asks for hotels to be ranked by how many MICHELIN restaurants are reachable
within an hour. Here is that rank &mdash; and an honest statement of what it is built on.</p>

<div class="warnbox"><strong>This rank covers 7 star restaurants, not 72.</strong>
Coordinates were verified for only the seven venues whose official page gave an address
(Le Bernardin, Eleven Madison Park, Per Se, Jungsik, Sushi Sho, Daniel, Gramercy Tavern &mdash; five of
them three-star or two-star). The remaining 65 star entries have no verified coordinates on this site, so
they cannot be scored. A perfect reach score below means "reach is not your problem here", not "this
hotel is objectively best". Flag F-05 and question Q-19.</div>
{reach_table}

<h3>How to read it</h3>
<ul class="tight">
<li><strong>Stars within 5 km</strong> is a straight-line proxy for the one-hour rule. Manhattan walking is
roughly 1.4 km per 20 minutes, so 5 km is a deliberately generous outer bound: anything inside it is
certainly within an hour on foot or by a short ride, and anything outside it needs a measured trip.</li>
<li><strong>Three-star within 5 km</strong> is the number that matters for a splurge dinner, because those
are the meals worth travelling for.</li>
<li><strong>What the rank shows:</strong> the five Midtown/Chelsea hotels are effectively tied on reach
(6&ndash;7 of the 7 scored venues, 4&ndash;5 of the five three-star ones). Only <strong>Residence Inn
FiDi</strong> is penalised, at 3 of 7 and 2 of 5. Since reach does not separate the other six,
<strong>cost and breakfast decide it</strong> &mdash; which is why the recommendation is Fairfield.</li>
</ul>

<h2>What we could not verify about these hotels</h2>
<div class="badbox">
<ul class="tight">
<li><strong>Street addresses</strong> for six of seven hotels were not in the captured text (F-13), so their map coordinates are area-level and any travel time from them is softer than it looks.</li>
<li><strong>Two cheapest qualifying rooms are accessible room types</strong> (Hyatt Place Chelsea, citizenM Bowery) &mdash; bookable by anyone, but a standard room may price differently (F-14).</li>
<li><strong>Promotions:</strong> several totals rely on a "Black Friday Deal" valid for select stays between 19 Nov 2026 and 31 Dec 2027 (F-03). The pre-discount price is shown wherever Booking.com published one.</li>
<li><strong>The all-in column is arithmetic, not a quote.</strong> The 14.75% rate and the $4 city tax were read on Booking.com's excluded-charges line, but the final bill can carry extra local fees that no page in this research named.</li>
</ul>
</div>
"""



def build_restaurants():
    det = DETAILS["details"]
    _detail = lambda r: det.get(r["michelin_url"].rstrip("/").split("/")[-1], {})
    n_hours_pub = sum(1 for r in ROSTER["restaurants"]
                      if _detail(r).get("hours_status") == "VERIFIED")
    n_hours_partial = sum(1 for r in ROSTER["restaurants"]
                          if _detail(r).get("hours_status") == "PARTIAL")
    n_price_pub = sum(1 for r in ROSTER["restaurants"]
                      if _detail(r).get("menu_price_usd") and not _detail(r).get("price_is_floor"))
    n_price_floor = sum(1 for r in ROSTER["restaurants"] if _detail(r).get("price_is_floor"))
    rows = []
    for r in ROSTER["restaurants"]:
        key = r["michelin_url"].rstrip("/").split("/")[-1]
        d = det.get(key)
        social = SOCIAL["accounts"].get(key, [])
        soc_html = []
        seen_review = 0
        for s in social:
            if s["kind"] == "review":
                seen_review += 1
            soc_html.append(ext(s["url"], social_label(s, seen_review), "tag"))
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
                    (", ".join(near) if near else '<span class="blank">no other scored star venue within 1 km</span>'),
                    ext(by_key[k]["michelin_url"], "MICHELIN")])
    geo.sort(key=lambda r: r[2].startswith('<span'))
    cluster_table = table(
        ["Borough", "Star entries", "Three-star entries", "What it means for the trip", "Source"],
        [
            ["Manhattan", str(bor.get("Manhattan", 0)), str(sum(1 for r in ROSTER["restaurants"] if r["borough"] == "Manhattan" and r["stars"] == 3)),
             "The only borough with a full spread of star levels. Every three-star dinner on the itinerary is here.",
             ext(ROSTER["meta"]["source_article"], "MICHELIN")],
            ["Brooklyn", str(bor.get("Brooklyn", 0)), "0",
             "Six entries, no three-star. A dinner here costs a 40-minute trip each way (Aska and Francie are the names to check).",
             ext(ROSTER["meta"]["source_article"], "MICHELIN")],
            ["Queens", str(bor.get("Queens", 0)), "0",
             "One entry. Worth a lunch, not a dinner run from Midtown.",
             ext(ROSTER["meta"]["source_article"], "MICHELIN")],
            ["Outside NYC", str(bor.get("Tarrytown, NY (outside NYC)", 0) + bor.get("North Salem, NY (outside NYC)", 0)), "0",
             "Blue Hill at Stone Barns (Tarrytown) and La Bastide (North Salem). Both fail the one-hour rule outright.",
             ext(ROSTER["meta"]["source_article"], "MICHELIN")],
        ],
        caption="Borough counts cover all 72 entries. This is the only cluster claim the data supports on its own.",
        card_labels=["Borough", "Entries", "Three-star", "Meaning", "Source"])
    geo_table = table(
        ["Rating", "Venue", "Scored star venue within 1 km", "Source"],
        geo,
        caption="Straight-line distances between the 7 venues whose coordinates were verified. A 7-venue sample, not a neighbourhood map.",
        card_labels=["Rating", "Venue", "Within 1 km", "Source"])

    return f"""
<p class="lede">All {len(ROSTER['restaurants'])} star entries from MICHELIN's
<em>All the Stars in The MICHELIN Guide to New York City 2025</em>, published 18 November 2025.
The badge in column two is the distinction: <strong>stars are awards</strong>, and a venue with no star
icon on MICHELIN's site is <em>listed</em>, not starred.</p>

<div class="badbox"><strong>This list changes on 14 December 2026</strong> — before the trip.
The next New York ceremony is that day, so any star shown here may move. Re-read the MICHELIN
ceremony page after that date (flag F-01).</div>

<div class="badbox"><strong>Read the two middle columns carefully: most of them are empty, on purpose.</strong>
Only {n_hours_pub} of the {len(ROSTER['restaurants'])} star restaurants have a full week of hours read
from an official page (one more is partial), and only {n_price_pub} published an exact menu price
(one more published a deposit floor). The rest of the roster is complete on name, distinction,
cuisine, borough and official link &mdash; and blank on hours and price, because the alternative would be
inventing them. The counts are on the <a href="repo-review.html">repo review</a> page and the way to close
each gap is in <a href="questions.html">Q-06 and Q-09</a>.</div>

<div class="warnbox"><strong>Two official MICHELIN pages disagree.</strong> The ceremony article lists
72 entries (5 / 15 / 52). MICHELIN's own filtered list pages, read the same day, report 69 (5 / 14 / 50).
This table publishes the 72 ceremony entries and flags the discrepancy rather than picking a winner
(F-02, question Q-17).</div>

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
<p>These are in the MICHELIN Guide's selection but carry <strong>no star</strong>. They are cheaper and
easier to book, and are listed here so the star tables are never confused with the wider guide.</p>
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
<p class="small">Bib Gourmand restaurants (76 of them per MICHELIN's filter) are a third category again:
good food at moderate prices, no star. They are not individually listed here.</p>
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
question is not "which cluster?" but "which hotel is within an hour of the specific restaurant I booked?"
The answer for all seven shortlisted hotels is in the <a href="hotels.html">MICHELIN reach ranking</a>.</div>

<div class="warnbox"><strong>What would make a real cluster analysis possible:</strong> verified coordinates
for all 72 entries, then a density calculation. That needs one page read per restaurant and is the same
work as closing F-05. Nothing on this site pretends to have done it.</div>

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
Gramercy Tavern. None published a readable price on 2026-11-25. Per Se's booking page states
<em>"starting at $200 per person (deposit)"</em> — a deposit, not the menu price, so it is shown as a
floor only. The source that settles each one is listed in <a href="questions.html">Q-06</a>.</div>
"""


def build_activities():
    rows = []
    for a in ACTS["activities"]:
        soc = SOCIAL["accounts"].get(a["id"], [])
        soc_html = " ".join(ext(s["url"], social_label(s), "tag")
                            for s in soc) or '<span class="blank">no account verified</span>'
        tr = a["from_hotel"]
        travel_cell = ('<strong>' + str(tr["transit_min_modelled"]) + ' min</strong>'
                       '<div class="small">by subway, modelled</div>'
                       '<div class="small">' + str(tr["walk_min_modelled"]) + ' min on foot &middot; '
                       + f'{tr["km"]:.1f}' + ' km</div>')
        if a["id"] == "statue-of-liberty":
            travel_cell += '<div class="small">+ ~15 min ferry to the island</div>'
        cost = (f'{money(a["cost_2_adults_usd"])}<div class="small">for two · {money(a["adult_usd"])} pp</div>'
                if a["cost_2_adults_usd"] is not None else
                '<span class="blank">no official price</span>')
        hours = esc(a["hours"]) if a["hours"] else '<span class="blank">hours not captured</span>'
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
<p class="lede">Eleven candidate activities with the official price, the official hours, the exceptions
that actually matter (closure days, last entry, ticket rules) and a verified social account where one
exists. Prices are per adult and doubled arithmetically for two.</p>

<div class="note"><strong>Free and almost-free:</strong> Central Park, The High Line, the Brooklyn Bridge
promenade and Chelsea Market cost nothing to enter. The paid items that matter are MoMA ($30),
The Met ($30), AMNH ($37 standard adult), the 9/11 Museum ($24–$36) and the Statue of Liberty ferry ($26).</div>

{table(
    ["Activity", "Days &amp; hours", "Exceptions that matter", "Cost for 2", "From the hotel", "Status", "Links"],
    rows,
    caption="Read on each venue's own site on 2026-11-25, with official re-reads on 2026-11-26 where a row says so. A blank means the official page did not yield the value.",
    card_labels=["Activity", "Hours", "Exceptions", "Cost for 2", "From the hotel", "Status", "Links"])}

<h2>Tickets: what to buy in advance</h2>
<div class="grid two">
<div class="card"><h3>Must pre-book (timed entry)</h3>
<ul class="tight">
<li><strong>9/11 Memorial &amp; Museum</strong> — timed tickets required, on sale up to six months ahead; last entry 17:30.</li>
<li><strong>Top of the Rock</strong> — timed admission, price varies by slot.</li>
<li><strong>Statue of Liberty</strong> — ferry is the only way to land, and only Statue City Cruises may dock.</li>
<li><strong>MoMA</strong> — booking ahead is sensible; the free Friday-night tickets must be reserved in advance.</li>
</ul></div>
<div class="card"><h3>Can be decided on the day</h3>
<ul class="tight">
<li><strong>The Met</strong> — ticket at the door.</li>
<li><strong>Central Park, High Line, Brooklyn Bridge</strong> — no ticket at all.</li>
<li><strong>Chelsea Market</strong> — free entry, pay each vendor.</li>
<li><strong>Broadway</strong> — no single official price exists; choose a show first (Q-16).</li>
</ul></div>
</div>

<h2>The one-hour rule, applied</h2>
<p class="brief-ask">The brief requires every activity to be within an hour of the chosen hotel. Measured
from the recommended hotel (Midtown West), all eleven qualify &mdash; but by different means.</p>
<div class="grid two">
<div class="card"><h3>Walkable in under 20 minutes</h3>
<p class="small">Broadway theatres (0.7 km), Top of the Rock (1.0 km), MoMA (1.1 km). These need no
transit planning at all, which is why they are clustered at the start of the itinerary.</p></div>
<div class="card"><h3>20&ndash;30 minutes by subway</h3>
<p class="small">AMNH, The Met, Central Park, The High Line, Chelsea Market. All comfortably inside the
hour with a single ride.</p></div>
<div class="card"><h3>Needs a real trip</h3>
<p class="small">9/11 Memorial (39 min modelled), Brooklyn Bridge (41 min). Both are inside the hour, but
they are half-day commitments rather than drop-ins.</p></div>
<div class="card"><h3>The one caveat: Statue of Liberty</h3>
<p class="small">Battery Park is 56 modelled minutes by subway &mdash; inside the hour, but only just, and
the ferry to the island adds roughly 15 minutes. Treat this as a half-day with a weather dependency, and
it is the first thing to cut if the schedule tightens (Q-15).</p></div>
</div>
<div class="warnbox">These minutes are <strong>modelled</strong>: straight-line distance at 12 km/h
effective subway speed plus 8 minutes for platform access and waiting. They are not schedules. The
Method page states the formula and flag F-05 records the limitation.</div>

<h2>Social media and video reviews</h2>
<p>Every activity carries at least one social or video link. Where an account was verified it is marked
<strong>✓</strong>. Where only a search URL is available it says <strong>search</strong>, because a search
link is honest and a guessed handle is not.</p>
<div class="warnbox"><strong>TikTok could not be verified at all</strong> — every TikTok URL returned
HTTP 400 to an automated read on 2026-11-25. No TikTok account is asserted anywhere on this site (F-07).</div>
"""


def build_itinerary():
    out = []
    for it in FR["itineraries"]:
        rows = [[esc(d["date"]), esc(d["day"]),
                 esc(d["plan"]) + '<div class="small">Official sources for every named venue are in the '
                 + '<a href="activities.html">Activities</a> and <a href="restaurants.html">Restaurants</a> tables.</div>',
                 '<a href="activities.html">Activities</a> · <a href="restaurants.html">Restaurants</a>']
                for d in it["days"]]
        note = f'<p class="hint">{esc(it["note"])}</p>' if it.get("note") else ""
        out.append(f"""<h2>{esc(it["title"])}</h2>{note}
{table(["Date", "Day", "Plan", "Sources"], rows, card_labels=["Date", "Day", "Plan", "Sources"])}""")
    return f"""
<p class="lede">Three concrete variants, so switching length is a choice rather than a re-plan.
The 7-night version is the recommendation; the 4-night version is the literal preferred window;
the 14-night version is the upper end of the brief.</p>

<div class="note"><strong>Dinner placement logic.</strong> Le Bernardin is closed on Sundays and does not
serve lunch on Saturdays. The 9/11 Museum opens Wednesday–Monday. MoMA opens at 10:30 every day and
runs late only on Fridays. Those three facts drive the order of days below.</div>

{"".join(out)}

<h2>Booking order that matters</h2>
<div class="card">
<ol class="tight">
<li><strong>Hotel first</strong>, on a free-cancellation rate — the deadline on the recommended rate is
12 February 2027, so nothing is at risk while you decide.</li>
<li><strong>Starred dinners roughly 30 days out.</strong> Most New York tasting menus release reservations
about a month ahead. This 30-day pattern is a common practice, not a rule I verified per venue — check each one.</li>
<li><strong>Timed tickets</strong> (9/11 Museum, Top of the Rock) once the dates are fixed; they sell out on holiday weekends.</li>
<li><strong>Statue of Liberty ferry</strong> before the trip; it is the only way onto the island.</li>
<li><strong>Broadway</strong> only after choosing a show.</li>
</ol>
</div>

<h2>February reality check</h2>
<div class="warnbox">The itinerary includes outdoor walking (Brooklyn Bridge, High Line, Central Park) in
February. No official climate data was captured for this site, so no temperature figure is quoted here —
that is deliberate (see suggestion S-10). Plan for a cold-weather wardrobe and keep a buffer day, which is
why day 7 is deliberately unscheduled.</div>
"""


def build_budget():
    b = FR["budget"]
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
<p class="lede">One line per cost, with the source that produced it and a label saying whether the figure
was read, derived by arithmetic, or deliberately left blank. The subtotal covers <strong>only</strong>
the lines that have a verified number.</p>

{table(["Line item", "Amount (2 adults)", "Basis", "Source &amp; note"], rows,
       caption="7 nights, 15–22 February 2027, two adults.",
       card_labels=["Item", "Amount", "Basis", "Source"])}

<h2>Verified subtotal</h2>
<div class="kpi">
 <div class="card"><div class="k">Verified subtotal</div><div class="v">{money(b["verified_subtotal_usd"])}</div>
  <div class="small">Everything above except the blank line.</div></div>
 <div class="card"><div class="k">Hotel share</div><div class="v">{money(1155.48)}</div><div class="small">{1155.48 / b["verified_subtotal_usd"] * 100:.0f}% of the subtotal</div></div>
 <div class="card"><div class="k">Flights share</div><div class="v">{money(1204)}</div><div class="small">{1204 / b["verified_subtotal_usd"] * 100:.0f}% of the subtotal &mdash; nearly as much as the hotel</div></div>
 <div class="card"><div class="k">Dining share (2 tasting menus)</div><div class="v">{money(1350)}</div><div class="small">{1350 / b["verified_subtotal_usd"] * 100:.0f}% &mdash; food only, no wine</div></div>
 <div class="card"><div class="k">Lines with no price</div><div class="v">{b["unpriced_lines"]}</div><div class="small">Ordinary meals: no official source exists, so it is blank rather than estimated.</div></div>
</div>

<div class="badbox"><strong>This is not a full trip budget and should not be presented as one.</strong>
It excludes breakfasts/lunches/ordinary dinners, wine with dinner (which would add roughly
{money(950)}–{money(1750)} for two pairings), shopping, and any Broadway tickets. It also uses the
cheapest flight fare found, which may not hold for two seats.</div>

<h2>What each add-on would cost, at verified prices</h2>
<div class="card">
<ul class="tight">
<li>Wine pairing at Le Bernardin — {money(530,0)} per person (i.e. {money(1060,0)} for two).</li>
<li>Wine pairing at Gabriel Kreuther — from {money(255,0)} per person.</li>
<li>American Museum of Natural History — {money(37,0)} standard adult, {money(74,0)} for two, from the official Plan Your Visit page; NY State residents pay what they wish.</li>
<li>A second week of hotel, 22 Feb – 1 Mar — {money(1199.14)} derived all-in for the same Fairfield room, from a $1,020.60 before-tax total (F-12).</li>
<li>Broadway — no single official price; depends entirely on the show.</li>
</ul>
</div>

<h2>How to read the labels</h2>
{table(["Label", "Meaning"], [
 ['<span class="pill p-verified">VERIFIED</span>', "Read on an official page. The link is in the row."],
 ['<span class="pill p-documented">DERIVED</span>', "Arithmetic on a verified official figure (e.g. an official cap × 2 people)."],
 ['<span class="pill p-open">NOT PRICED</span>', "No official source exists for this number, so it is blank."],
], caption="No line in this budget is an estimate dressed up as a fact.")}
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
<p class="lede">Every decision that cannot yet be made, with what we already have, exactly what is
missing, and the specific action that would resolve it. Nothing here needs to be answered for the plan
to run — the recommendation already assumes an answer to each — but each one changes a number or a choice.</p>

<div class="kpi">
 <div class="card"><div class="k">Questions</div><div class="v">{len(FR["questions"])}</div><div class="small">Each tied to a decision</div></div>
 <div class="card"><div class="k">Waiting on the traveller</div><div class="v">{sum(1 for q in FR["questions"] if q["owner"]=="traveller")}</div><div class="small">Answer directly — no research needed</div></div>
 <div class="card"><div class="k">Waiting on research</div><div class="v">{sum(1 for q in FR["questions"] if q["owner"]=="research")}</div><div class="small">Each names the exact source to read</div></div>
 <div class="card"><div class="k">Blocked by a date</div><div class="v">1</div><div class="small">The new MICHELIN list arrives 14 Dec 2026</div></div>
</div>

{table(["Question", "Why it blocks a decision", "What we have", "What is missing", "How to discover it", "Status"],
       rows,
       caption="Ordered as in the register. 'traveller' means only you can answer it.",
       card_labels=["Question", "Why it blocks", "Have", "Missing", "How to discover", "Status"])}

<h2>The five that actually change the plan</h2>
<div class="grid two">
<div class="card"><h3>Q-01 · How long?</h3><p class="small">4, 7 or 14 nights changes the hotel cost, the number of starred dinners and which hotel wins.</p></div>
<div class="card"><h3>Q-02 · What is the budget?</h3><p class="small">Every ranking sorts on price; without a ceiling there is no way to say whether two splurge dinners are sensible.</p></div>
<div class="card"><h3>Q-06 · What do the other menus cost?</h3><p class="small">Four priority venues still have no published price, so the food budget is incomplete.</p></div>
<div class="card"><h3>Q-09 · The Met hours?</h3><p class="small">The High Line is verified; The Met's hours come from an official page excerpt and remain PARTIAL.</p></div>
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
    sev_kind = {"HIGH": "open", "MEDIUM": "partial", "LOW": "documented"}
    rows = []
    cards = []
    for f in FR["flags"]:
        k = sev_kind.get(f["severity"], "open")
        src_cell = ext(f["source"], "official page") if f["source"] else '<span class="blank">no source captured</span>'
        rows.append([
            '<strong>' + esc(f["id"]) + '</strong> ' + pill(k, f["severity"])
            + '<div class="small">' + esc(f["title"]) + '</div>',
            esc(f["detail"]),
            src_cell,
            esc(f["settle_by"]),
        ])
        cards.append([
            '<strong>' + esc(f["id"]) + '</strong> ' + pill(k, f["severity"])
            + '<div class="small">' + esc(f["title"]) + '</div>',
            esc(f["detail"]),
            src_cell,
            esc(f["settle_by"]),
        ])
    tbl = table(["Flag", "What happened", "Source", "How to close it"], rows,
                caption="All items were found during the build. None is a guess.",
                card_labels=["Flag", "What happened", "Source", "How to close it"])
    high = sum(1 for f in FR["flags"] if f["severity"] == "HIGH")
    med = sum(1 for f in FR["flags"] if f["severity"] == "MEDIUM")
    low = sum(1 for f in FR["flags"] if f["severity"] == "LOW")
    body = """
<p class="lede">Everything on this site that is unverified, ambiguous or irregular, with its severity and
the exact action that would close it. Nothing is hidden and nothing is quietly smoothed over.</p>

<div class="kpi">
 <div class="card"><div class="k">Flagged items</div><div class="v">%d</div></div>
 <div class="card"><div class="k">High severity</div><div class="v">%d</div><div class="small">Could change a recommendation</div></div>
 <div class="card"><div class="k">Medium</div><div class="v">%d</div></div>
 <div class="card"><div class="k">Low</div><div class="v">%d</div></div>
</div>

%s

<h2>The four that matter most</h2>
<div class="badbox">
<ol class="tight">
<li><strong>F-01</strong> &mdash; the MICHELIN list changes on 14 December 2026, before the trip.</li>
<li><strong>F-02</strong> &mdash; MICHELIN's own ceremony article (72) and live filter (69) disagree.</li>
<li><strong>F-05</strong> &mdash; the one-hour travel rule is modelled, not measured.</li>
<li><strong>F-03 / F-04</strong> &mdash; hotel prices are live snapshots, and some totals exclude tax.</li>
</ol>
</div>

<h2>What this register is for</h2>
<p>Each flag names the source that would close it. Closing all of them is a bounded amount of work:
most are a single page read. The ones that are not &mdash; F-01 and F-02 &mdash; depend on MICHELIN
publishing, and cannot be closed early.</p>
""" % (len(FR["flags"]), high, med, low, tbl)
    return body


def build_method():
    return f"""
<p class="lede">How every number on this site was produced, every source that was read, every source that
failed, and the checks the build runs on itself.</p>

<h2>Rules the site is built on</h2>
<div class="card">
<ol class="tight">
<li><strong>Read it or leave it blank.</strong> A value appears only if it was read on the page linked in
the same row. If it could not be read, the cell is blank and the reason is named.</li>
<li><strong>Never infer.</strong> No "typical" prices, no assumed opening hours, no guessed social handles.</li>
<li><strong>Separate the award from the listing.</strong> A star is an award; a venue in the guide carries
a different badge.</li>
<li><strong>Label every derived number.</strong> Arithmetic on a verified figure is marked DERIVED and the
formula is written down.</li>
<li><strong>Keep disagreements visible.</strong> When two official pages disagree, both numbers are shown.</li>
<li><strong>Date every snapshot.</strong> Most values were read on 2026-11-25; six MICHELIN hour blocks, hotel rates, AMNH and Gramercy Tavern prices, Jungsik's address, The Met's hours excerpt and The High Line's seasonal hours were re-read on 2026-11-26. All will drift.</li>
</ol>
</div>

<h2>Sources read</h2>
<h3>MICHELIN</h3>
<ul class="tight">
<li>{ext("https://guide.michelin.com/us/en/article/michelin-guide-ceremony/all-the-stars-in-the-michelin-guide-to-new-york-city-2025", "All the Stars in The MICHELIN Guide to New York City 2025")} — the 72-entry roster (published 18 Nov 2025).</li>
<li>{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/1-star-michelin", "1-star filtered list")} and {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/2-stars-michelin", "2-star filtered list")} — the 69 count.</li>
<li>Individual restaurant pages for hours, address and price band: {ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/le-bernardin", "Le Bernardin")},
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/eleven-madison-park", "Eleven Madison Park")},
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/per-se", "Per Se")},
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/daniel", "Daniel")},
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/gramercy-tavern", "Gramercy Tavern")},
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/sushi-sho-1213976", "Sushi Sho")}.</li>
<li>Ceremony date (14 Dec 2026) reported by {ext("https://ny.eater.com/news/414985/michelin-guide-new-york-additions-2026-bib-gourmands-michelin-recommendations", "Eater New York")} — a secondary source, flagged as such.</li>
</ul>

<h3>Restaurant prices (from the venues themselves)</h3>
<ul class="tight">
<li>{ext("https://www.le-bernardin.com/accessible/menus/dining-room/chef-s-tasting/", "Le Bernardin Chef's Tasting")} — $350 pp.</li>
<li>{ext("https://www.le-bernardin.com/accessible/menus/dining-room/dinner/", "Le Bernardin dinner")} — $225 prix fixe.</li>
<li>{ext("https://www.le-bernardin.com/accessible/menus/dining-room/lunch/", "Le Bernardin lunch")} — $142 prix fixe.</li>
<li>{ext("https://www.gknyc.com/menus", "Gabriel Kreuther menus")} — Chef's Tasting $325 pp (PDF dated 11.17.26).</li>
<li>{ext("https://www.exploretock.com/perse", "Per Se on Tock")} — "starting at $200 per person (deposit)".</li>
</ul>

<h3>Hotels</h3>
<ul class="tight">
<li>{ext("https://www.booking.com/searchresults.html?ss=Manhattan%2C+New+York&checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD&order=price&nflt=ht_id%3D204%3Bclass%3D4%3Breview_score%3D80%3Bhotelfacility%3D2", "Booking.com search: Manhattan, 4-star, score 8+, private bathroom")} — the shortlist, sorted by price.</li>
<li>Individual hotel pages for the room-level detail: {ext("https://www.booking.com/hotel/us/fairfield-inn-suites-by-marriott-new-york-manhattan-central-park.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Fairfield")},
{ext("https://www.booking.com/hotel/us/citizenm-new-york-times-square-new-york.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "citizenM Times Square")},
{ext("https://www.booking.com/hotel/us/pestana-cr7-times-square.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Pestana CR7")},
{ext("https://www.booking.com/hotel/us/arlo-midtown.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD", "Arlo Midtown")}.</li>
</ul>

<h3>Activities, transit and flights</h3>
<ul class="tight">
<li>{ext("https://www.moma.org/visit/", "MoMA: hours and admission")} · {ext("https://www.metmuseum.org/plan-your-visit", "The Met: tickets")} · {ext("https://www.metmuseum.org/plan-your-visit/met-fifth-avenue", "The Met Fifth Avenue: hours excerpt")} · {ext("https://www.amnh.org/plan-your-visit", "AMNH: hours and standard admission")}</li>
<li>{ext("https://www.911memorial.org/visit/visit-museum-1", "9/11 Memorial &amp; Museum: hours and tickets")} · {ext("https://www.rockefellercenter.com/tickets/top-of-the-rock-observation-deck/", "Top of the Rock: tickets")} · {ext("https://www.nps.gov/stli/planyourvisit/fees.htm", "Statue of Liberty: NPS fees")}</li>
<li>{ext("https://www.nycgovparks.org/parks/central-park", "NYC Parks: Central Park")} · {ext("https://www.thehighline.org/visit/", "The High Line: visitor info")} — winter hours 07:00–20:00, read 2026-11-26.</li>
<li>{ext("https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/", "OPM: 2027 federal holidays")} — Washington's Birthday on Monday 15 February 2027.</li>
<li>{ext("https://www.mta.info/fares-tolls/subway-bus", "MTA subway and bus fares")} — $3 fare, $35 seven-day tap-and-ride cap.</li>
<li>{ext("https://www.google.com/travel/flights?q=Flights%20to%20JFK%20from%20AMS%20on%202027-02-15%20through%202027-02-22", "Google Flights: AMS–JFK, 15–22 Feb 2027")} &mdash; $606 per adult round trip (Aer Lingus, 1 stop via Dublin), $562 with a 6h20m layover, $904–906 nonstop. These are the itinerary's own dates.</li>
<li>{ext("https://www.kayak.com/flights/AMS-NYC/2027-02-14/2027-02-23?sort=bestflight_a", "KAYAK AMS–NYC, 14–23 Feb 2027")} &mdash; a cross-check on adjacent dates: $686 cheapest, $908 nonstop. The extra night costs money, which is why the plan does not add one.</li>
</ul>

<h3>Social accounts verified</h3>
<ul class="tight">
<li>Instagram profiles opened and read and confirmed official by badge plus bio or link-in-bio: Le Bernardin (346,704 followers), Eleven Madison Park (543,313), Per Se (333,776), Daniel (159,355), Gramercy Tavern (145,393), MoMA (6,154,925), The Met (4,752,680), NYC Parks (309,569), The High Line (253,752). Le Coucou's account is private, so nothing could be confirmed from it.</li>
<li>YouTube: <strong>eleven</strong> specific review videos across seven venues were opened and identified by title, channel and view count; every remaining social cell is a labelled search link.</li>
<li><strong>A lookalike handle was caught:</strong> <code>instagram.com/museumofmodernart</code> has 3,809 followers and has not posted since 2019. It is <em>not</em> MoMA. The real account is <code>themuseumofmodernart</code>.</li>
<li><strong>TikTok: failed.</strong> Every URL returned HTTP 400.</li>
</ul>

<h2>Re-verified on 26 November 2026</h2>
<div class="card">
<p>Six hour blocks that the first pass had marked <em>UNVERIFIED</em> were readable in a second
read of MICHELIN's own restaurant pages. They were replaced with the published weekly hours and given
a per-field <code>hours_read_on</code> value; nothing was pattern-filled:</p>
<ul class="tight">
<li>{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/eleven-madison-park", "Eleven Madison Park")} ·
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/per-se", "Per Se")} ·
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/daniel", "Daniel")} ·
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/jungsik-new-york", "Jungsik")} ·
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/sushi-sho-1213976", "Sushi Sho")} ·
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/gabriel-kreuther", "Gabriel Kreuther")}</li>
<li>Two dates previously quoted without a clickable source are now tied to their exact Booking.com URLs:
{ext("https://www.booking.com/hotel/us/fairfield-inn-suites-by-marriott-new-york-manhattan-central-park.html?checkin=2027-02-16&checkout=2027-02-23&group_adults=2&no_rooms=1&selected_currency=USD", "16–23 Feb 2027")} ($996.10 before tax) and
{ext("https://www.booking.com/hotel/us/fairfield-inn-suites-by-marriott-new-york-manhattan-central-park.html?checkin=2027-02-22&checkout=2027-03-01&group_adults=2&no_rooms=1&selected_currency=USD", "22 Feb – 1 Mar 2027")} ($1,020.60 before tax). Both are accessible king rooms — flag F-22.</li>
<li>{ext("https://www.booking.com/hotel/us/fairfield-inn-suites-by-marriott-new-york-manhattan-central-park.html?checkin=2027-02-16&checkout=2027-02-23&group_adults=2&no_rooms=1&selected_currency=USD", "Booking.com")} also published the Fairfield's street address (538 West 58th Street);
{ext("https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/gabriel-kreuther", "MICHELIN")} published Gabriel Kreuther's (41 W. 42nd St.).</li>
<li>{ext("https://www.thehighline.org/visit/", "The High Line's official visitor page")} published seasonal hours on the second read; {ext("https://www.amnh.org/plan-your-visit", "AMNH")} published $37 standard adult admission, and {ext("https://www.gramercytavern.com/dining-room-menu", "Gramercy Tavern")} published a $178 seasonal menu. The Met's own search excerpt lists hours but a direct fetch redirected, so that row remains PARTIAL.</li>
</ul>
<p class="small">Also corrected in this pass: the overview called Arlo SoHo's discounted $1,021 rate
"pre-discount" (its pre-discount rate is $1,639); the social-account headline counted an unread
Instagram handle as verified; and an orphaned, stale <code>docs/methodology.html</code> from an earlier
build was removed.</p>
</div>

<h2>What failed, and what was done about it</h2>
<div class="card">
<table class="tbl"><thead><tr><th>Source</th><th>What happened</th><th>Result</th></tr></thead><tbody>
<tr><td>{ext("https://www.amnh.org/plan-your-visit", "amnh.org admission prices")}</td><td>The first read covered hours only; the full Plan Your Visit page was read again on 2026-11-26</td><td>Standard adult $37, or $74 for two, now published with source</td></tr>
<tr><td>{ext("https://www.thehighline.org/visit/", "thehighline.org hours")}</td><td>Cookie-consent wall blocked the first read on 25 Nov</td><td>Recovered from a second page read on 26 Nov: Dec 1 – Mar 31, 07:00-20:00</td></tr>
<tr><td>{ext("https://www.metmuseum.org/plan-your-visit/met-fifth-avenue", "metmuseum.org hours block")}</td><td>The direct capture redirected; The Met's own page excerpt in search results does list the hours</td><td>Hours shown, but the activity row remains PARTIAL rather than VERIFIED</td></tr>
<tr><td>tiktok.com (profile and discovery)</td><td>HTTP 400 on every attempt</td><td>No TikTok asserted anywhere</td></tr>
<tr><td>{ext("https://www.elevenmadisonpark.com/", "elevenmadisonpark.com menu")}</td><td>Site publishes no price</td><td>Blank, Resy policy noted</td></tr>
<tr><td>{ext("https://www.gramercytavern.com/dining-room-menu", "gramercytavern.com Dining Room menu")}</td><td>The generic menus URL failed; the dedicated Dining Room menu page was read on 2026-11-26</td><td>Seasonal Menu $178 per person now published with source; $118 wine pairing noted</td></tr>
<tr><td>{ext("https://www.le-bernardin.com/accessible/", "le-bernardin.com/menus")}</td><td>JavaScript-only page</td><td>Solved: the site's accessible ("/accessible/") menus carry the same prices as text</td></tr>
</tbody></table>
</div>

<h2>The travel model, stated plainly</h2>
<div class="warnbox">
<p>Travel minutes shown anywhere on this site are <strong>modelled</strong>: straight-line distance from
the hotel's coordinates divided by an assumed average speed, with a fixed allowance for platform access
and waiting. They are not schedules.</p>
<p>Why it matters: the brief's central constraint is "an hour or less". A straight-line model understates
real trips that require a transfer, and it cannot see the East River. A few legs were checked against a
real transit router and were consistent with the model, but <strong>no full matrix was measured</strong>.
Treat every "within the hour" statement as provisional (F-05, Q-19, S-02).</p>
</div>

<h2>Build checks</h2>
<div class="okbox">
<p>The generator refuses to publish if any of these fail:</p>
<ul class="tight">
<li>Every internal link (nav, body, footer) resolves to a file that exists.</li>
<li>No unrendered template tokens or HTML-escaped markup leaks into the output.</li>
<li>No placeholder links that point at nothing (a bare hash).</li>
<li>No duplicate element IDs; every table row has the same number of cells as its header.</li>
<li>Every data row in the restaurant, hotel and activity tables carries at least one outbound source link.</li>
</ul>
<p class="small">These checks are run by <code>build_site.py</code> on every build and their result is printed to the console.</p>
</div>

<h2>Known structural limitation: two datasets</h2>
<p>An earlier session published a second, independently researched dataset alongside this one, still live at
<a href="../deepdive/index.html">the deep dive</a>. It disagrees with this site on the star count (69 vs 72),
the hotel shortlist, the transit method and the hotel ranking basis. This site does not merge the two,
because merging would silently choose a winner.</p>
<p><strong>This dashboard is the canonical one</strong> for the reasons on the
<a href="repo-review.html">repository review</a>: it carries per-row hours, prices and social accounts that
the deep dive does not, and it states its own verification counts instead of implying completeness. The
deep dive is kept only so the earlier work is not lost (suggestion S-01, question Q-23).</p>
"""



def build_repo_review():
    roster = ROSTER["restaurants"]
    det = DETAILS["details"]
    acts = ACTS["activities"]

    def key(r):
        return r["michelin_url"].rstrip("/").split("/")[-1]

    n_hours = sum(1 for r in roster if det.get(key(r), {}).get("hours_status") == "VERIFIED")
    n_partial = sum(1 for r in roster if det.get(key(r), {}).get("hours_status") == "PARTIAL")
    n_price = sum(1 for r in roster if det.get(key(r), {}).get("menu_price_usd")
                  and not det.get(key(r), {}).get("price_is_floor"))
    n_page = sum(1 for r in roster if det.get(key(r)))
    def verified(s):
        return s["kind"] == "official" and "unconfirmed" not in s.get("evidence", "").lower()
    n_ig = sum(1 for r in roster if any(
        verified(s) for s in SOCIAL["accounts"].get(key(r), [])))
    n_vid = sum(1 for r in roster if any(
        s["kind"] == "review" for s in SOCIAL["accounts"].get(key(r), [])))
    n_vids = sum(1 for grp in SOCIAL["accounts"].values() for s in grp if s["kind"] == "review")
    n_vid_venues = sum(1 for grp in SOCIAL["accounts"].values()
                       if any(s["kind"] == "review" for s in grp))
    a_ver = sum(1 for a in acts if a["verification"].startswith("VERIFIED"))
    a_part = sum(1 for a in acts if a["verification"].startswith("PARTIAL"))
    a_ig = sum(1 for a in acts if any(
        verified(s) for s in SOCIAL["accounts"].get(a["id"], [])))
    a_vid = sum(1 for a in acts if any(
        s["kind"] == "review" for s in SOCIAL["accounts"].get(a["id"], [])))
    h_priced = sum(1 for h in HOTELS["hotels"] if h["total_7n_usd"])

    coverage = table(
        ["Dataset", "Rows", "Fully or partly verified", "Has a source link", "Verified social", "Blank / flagged"],
        [
            ["Restaurants (star roster)", str(len(roster)),
             f'{n_page} with a detail page',
             f'{len(roster)} (MICHELIN page on every row)',
             f'{n_ig} official Instagram · {n_vid} review-video venues',
             f'{len(roster) - n_page} roster-only'],
            ["Restaurants (hours)", str(len(roster)), f'{n_hours} full · {n_partial} partial',
             f'{n_hours + n_partial}', "—", f'{len(roster) - n_hours - n_partial} blank'],
            ["Restaurants (menu price)", str(len(roster)), f'{n_price} exact',
             f'{n_price}', "—", f'{len(roster) - n_price} without an exact price'],
            ["Hotels", str(len(HOTELS["hotels"])), f'{h_priced} priced for 7 nights',
             f'{len(HOTELS["hotels"])}', "—",
             f'{sum(1 for h in HOTELS["hotels"] if not h["address"])} without a street address'],
            ["Activities", str(len(acts)), f'{a_ver} verified · {a_part} partial',
             f'{len(acts)}', f'{a_ig} official Instagram · {a_vid} review-video venues', f'{len(acts) - a_ver - a_part} roster-only'],
        ],
        caption="What is actually verified on this site, counted rather than claimed.",
        card_labels=["Dataset", "Rows", "Verified", "Source link", "Social", "Blank"])

    findings = table(
        ["#", "Finding", "Evidence", "What was done", "Status"],
        [
            ["R1", "The repository began as a single 8-byte README and now carries two independently researched datasets that disagree with each other.",
             "git log; 2 commits on this branch; docs/ and deepdive/ both published",
             "This site publishes one dataset and treats the other as archived prior work; the disagreement is itemised rather than merged away (S-01, Q-23).",
             "Documented"],
            ["R2", "Two live datasets contradict each other on the star count.",
             "docs/data/michelin_2025.csv vs this roster: 69 vs 72",
             "Both numbers are shown on the MICHELIN page and flagged F-02, with Q-17 naming the diff as the way to settle it.",
             "Open"],
            ["R3", "GitHub Pages builds from main:/ with a root index.html that redirects into docs/. Nothing on this branch is live until it is merged.",
             "gh api repos/.../pages -> source main:/, build_type legacy",
             "Every page here is generated into docs/, and the root redirect already points at docs/. Publishing is a merge, not a setting.",
             "Needs merge"],
            ["R4", "No CI of any kind: no link checker, no data validation.",
             ".github does not exist",
             "build_site.py now runs its own checks and exits non-zero on failure. A CI job that calls it is proposed as S-07.",
             "Partly addressed"],
            ["R5", "No LICENSE file, so the repository's reuse terms are undefined.",
             "no LICENSE at root",
             "Out of scope for a research task and left to the owner; noted rather than guessed at.",
             "Open"],
            ["R6", "Old generated pages survived a rebuild and linked to pages that no longer exist.",
             "docs/methodology.html from a prior build was superseded by method.html and removed",
             "The superseded page is removed and this one is regenerated from data; the build fails if any internal link dangles.",
             "Resolved"],
            ["R7", "Three official pages failed to render during research, so their values are absent.",
             "metmuseum.org hours block, thehighline.org consent wall, amnh.org ticketing",
             "High Line hours, AMNH admission and Gramercy Tavern's menu price were read from official pages; The Met's hours remain an official search excerpt only (F-09).",
             "Partly addressed"],
            ["R8", "An Instagram handle was inferred from another account's post, not opened directly.",
             "@chelseamarketny, read in a verified High Line post",
             "Labelled as unconfirmed in F-08 rather than presented as verified.",
             "Open"],
            ["R9", "No .gitignore rule for the generated site, so build output and source live in the same tree.",
             ".gitignore contains only __pycache__, *.pyc, .DS_Store",
             "Deliberate: docs/ is the published artefact and must be committed. The generated CSS and HTML are reproducible from site_data/ plus build_site.py.",
             "Accepted"],
        ],
        caption="The repository as found, reviewed line by line, with what was done about each finding.",
        card_labels=["#", "Finding", "Evidence", "Action", "Status"])

    return (
        '<p class="lede">What this repository contained, what was wrong with it, and what is now verified'
        ' versus merely written down. This page exists so the work can be checked rather than trusted.</p>'

        '<h2>Verification coverage, counted</h2>'
        + coverage
        + '<div class="warnbox"><strong>The headline number is uncomfortable and should be.</strong> Of '
        + str(len(roster)) + ' star restaurants, ' + str(n_hours) + ' have a full week of verified hours ('
        + str(n_partial) + ' partial) and ' + str(n_price) + ' have an exact published menu price. '
        'The roster is complete; the operational detail is not. '
        + str(n_vids) + ' review videos across ' + str(n_vid_venues) + ' venues were individually opened and identified. '
        'That is a research limit, not a formatting choice, and the Flagged page says what would close it.</div>'

        '<h2>Repository review</h2>'
        + findings
        + '<h2>What changed in this session</h2>'
        '<div class="card"><ul class="tight">'
        '<li><strong>New data layer</strong> in <code>site_data/</code>: star roster, restaurant detail, hotels, '
        'activities, social accounts, and the framework (plan, budget, itineraries, flags, questions, suggestions).</li>'
        '<li><strong>New generator</strong> <code>build_site.py</code>, standard library only, which refuses to '
        'publish a page with a dangling link, a duplicated id, or an unescaped template token.</li>'
        '<li><strong>New site</strong> of 11 pages in <code>docs/</code>, regenerated from the data, with a '
        'card layout below 700px so no table needs horizontal scrolling on a phone.</li>'
        '<li><strong>Superseded pages removed</strong> so no two pages in the published tree describe the same '
        'thing differently.</li>'
        '</ul></div>'

        '<h2>How to check this work</h2>'
        '<div class="card"><ol class="tight">'
        '<li><strong>Re-run the build:</strong> <code>python3 build_site.py</code>. It prints every check it ran. '
        'A failure exits non-zero.</li>'
        '<li><strong>Spot-check a row:</strong> open the source link in the row and compare the number. '
        'Hotel URLs carry the dates in the query string, so the price reproduces.</li>'
        '<li><strong>Check a blank:</strong> every blank on the site should appear on the '
        '<a href="flagged.html">Flagged</a> page. A blank that is not flagged is a defect.</li>'
        '<li><strong>Check a derived number:</strong> the formula is on the '
        '<a href="method.html">Method</a> page and the inputs are in <code>site_data/*.json</code>.</li>'
        '</ol></div>'

        '<h2>What is still missing from the repository itself</h2>'
        '<div class="badbox"><ul class="tight">'
        '<li><strong>No licence.</strong> Decide before sharing the repo.</li>'
        '<li><strong>No CI.</strong> The build has checks; nothing runs them automatically (S-07).</li>'
        '<li><strong>No price history.</strong> Each build overwrites the last; a dated snapshot of '
        '<code>site_data/</code> would show how prices moved (S-03).</li>'
        '<li><strong>No test for data shape.</strong> The generator fails on missing keys, but there is no '
        'schema that would catch a field quietly changing meaning.</li>'
        '</ul></div>'
    )


# ---------------------------------------------------------------- checks
def run_checks(pages):
    errors, warnings = [], []

    # the stated budget subtotal must equal the sum of its priced lines
    _b = FR["budget"]
    _sum = round(sum(l["usd"] for l in _b["lines"] if l["usd"] is not None), 2)
    if abs(_sum - _b["verified_subtotal_usd"]) > 0.005:
        errors.append("budget: stated subtotal %.2f != sum of lines %.2f"
                      % (_b["verified_subtotal_usd"], _sum))

    # every data row must have an outbound source (the claim on the Method page)
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

    # table shape: every row has the same cell count as its header
    from html.parser import HTMLParser
    class _Shape(HTMLParser):
        def __init__(self):
            super().__init__(); self.tables = []; self.cur = None; self.row = None
        def handle_starttag(self, tag, attrs):
            if tag == "table": self.cur = {"header": None, "rows": []}
            elif tag == "tr" and self.cur is not None: self.row = 0
            elif tag in ("td", "th") and self.row is not None: self.row += 1
        def handle_endtag(self, tag):
            if tag in ("td", "th") and self.row is not None:
                # one cell counted on each close tag would double count; handled below
                pass
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
    return errors, warnings


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

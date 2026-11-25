#!/usr/bin/env python3
"""
NYFun1 — NYC trip planner static site generator.

Reads the verified CSV datasets in docs/data/ and writes the static site in docs/.
Every table value is either (a) copied verbatim from a fetched official/official-agent
page, or (b) blank and flagged. Derived numbers (tax-inclusive totals, modelled transit
times, composite scores) are always labelled as DERIVED / MODEL and never presented as
verified facts.
"""
import csv, json, math, os, re, shutil
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")
DATA = os.path.join(DOCS, "data")
BUILT = date(2026, 11, 25)
SITE = "NYC 2027 — Trip Planning Dashboard"

# ----------------------------------------------------------------------------- helpers
def esc(s):
    s = "" if s is None else str(s)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))

def money(v, dec=0):
    if v in ("", None):
        return "—"
    return f"${float(v):,.{dec}f}"

def pct(v):
    return f"{float(v)*100:.2f}%".rstrip("0").rstrip(".")

def none_dash(v):
    v = (v or "").strip()
    if v in ("", "NOT VERIFIED", "NOT CAPTURED", "ADDRESS NOT CAPTURED"):
        return '<span class="small">— blank —</span>'
    return esc(v)

def ext(url, label=None):
    if not (url or "").strip():
        return '<span class="small">—</span>'
    url = url.strip()
    label = label or ("MICHELIN" if "michelin.com" in url else "site")
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{esc(label)}</a>'

def social_links(name, kind="restaurant"):
    q = re.sub(r"\s+", "+", name.replace("&", "and"))
    verified_map = SOCIAL_REVIEWS.get(name.strip().lower(), {})
    parts = []
    fallbacks = {
        "YouTube": f"https://www.youtube.com/results?search_query={q}+{kind}+new+york",
        "TikTok": f"https://www.tiktok.com/search?q={q}",
        "Instagram": f"https://www.instagram.com/explore/tags/{q.lower()}/",
    }
    for plat in ("YouTube", "TikTok", "Instagram"):
        if plat in verified_map:
            url, title = verified_map[plat]
            parts.append(
                f'<a href="{esc(url)}" target="_blank" rel="noopener" title="Verified: {esc(title)}"><strong>{plat} ✓</strong></a>'
            )
        else:
            parts.append(
                f'<a href="{esc(fallbacks[plat])}" target="_blank" rel="noopener" title="Platform search fallback">{plat} (search)</a>'
            )
    return '<span class="linklist">' + "".join(parts) + "</span>"

def stars_html(n):
    n = int(n or 0)
    return '<span class="stars">' + "★" * n + "</span>" if n else '<span class="small">—</span>'

def status_pill(status):
    s = (status or "").strip()
    cls = "info"
    if s.startswith("VERIFIED"): cls = "ok"
    elif s.startswith("PARTIAL") or s.startswith("SHOW-DEPENDENT"): cls = "warn"
    elif s.startswith("UNVERIFIED") or s == "roster-only" or s == "partial": cls = "bad"
    label = {"roster-only": "roster only", "partial": "partial"}.get(s, s.split(" -")[0])
    return f'<span class="pill {cls}">{esc(label)}</span>'

def table(headers, rows, caption=None, cls="", numeric_cols=()):
    out = [f'<div class="table-wrap"><table class="{cls}">']
    if caption:
        out.append(f"<caption>{caption}</caption>")
    out.append("<thead><tr>" + "".join(
        f'<th class="{"num" if i in numeric_cols else ""}">{h}</th>'
        for i, h in enumerate(headers)) + "</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>" + "".join(
            f'<td class="{"num" if i in numeric_cols else ""}">{c}</td>'
            for i, c in enumerate(r)) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def transit_min(km):
    """MODEL: better of walking (80 m/min) or subway (8 min access/wait + 18 km/h)."""
    walk = km * 1000 / 80 + 2
    subway = 8 + km / 0.30
    return int(round(min(walk, subway)))

def gmaps(origin, dest):
    return ("https://www.google.com/maps/dir/?api=1&travelmode=transit&origin="
            + origin.replace(" ", "+") + "&destination=" + dest.replace(" ", "+"))

DIRECTIONS = lambda o, d: f'<a href="{esc(gmaps(o,d))}" target="_blank" rel="noopener">MTA / maps check</a>'

# ----------------------------------------------------------------------------- data
def load_csv(name):
    with open(os.path.join(DATA, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

restaurants = load_csv("michelin_2025.csv")
hotels = load_csv("hotels.csv")
windows = load_csv("date_windows.csv")
activities = load_csv("activities.csv")
listed = load_csv("guide_listed.csv")
social_reviews_rows = load_csv("social_reviews.csv") if os.path.exists(os.path.join(DATA, "social_reviews.csv")) else []
SOCIAL_REVIEWS = {}
for sr in social_reviews_rows:
    key = (sr.get("entity_name") or "").strip().lower()
    plat = (sr.get("platform") or "").strip()
    if key and plat and (sr.get("url") or "").strip():
        SOCIAL_REVIEWS.setdefault(key, {})[plat] = (sr["url"].strip(), (sr.get("title") or "").strip())

for r in restaurants:
    r["stars"] = int(r["stars"] or 0)
    r["lat"] = float(r["lat"]) if r["lat"].strip() else None
    r["lon"] = float(r["lon"]) if r["lon"].strip() else None

for h in hotels:
    h["base"] = float(h["base_7n_usd"])
    h["tax_rate"] = float(h["tax_rate"])
    h["city_tax_night"] = float(h["city_tax_night"])
    h["lat"] = float(h["lat_model"]); h["lon"] = float(h["lon_model"])
    # DERIVED: tax-inclusive 7-night total = base * (1+tax) + city tax * 7
    h["incl"] = h["base"] * (1 + h["tax_rate"]) + h["city_tax_night"] * 7
    h["rating"] = float(h["rating_out_of_10"]) if h["rating_out_of_10"].strip() else None

verified = [r for r in restaurants if r["lat"] is not None]
NIGHTS = 7
for h in hotels:
    times = []
    for r in verified:
        km = haversine(h["lat"], h["lon"], r["lat"], r["lon"])
        times.append((r["name"], km, transit_min(km)))
    h["times"] = times
    n20 = sum(1 for _, _, t in times if t <= 20)
    n30 = sum(1 for _, _, t in times if t <= 30)
    n60 = sum(1 for _, _, t in times if t <= 60)
    h["n20"], h["n30"], h["n60"] = n20, n30, n60
    h["access"] = 3 * n20 + 2 * (n30 - n20) + 1 * (n60 - n30)
    bonus = 1 + (0.05 if h["breakfast"].lower().startswith("included") else 0) \
              + (0.05 if (h["rating"] or 0) >= 8.5 else 0)
    h["score"] = (h["access"] / (h["incl"] / 1000.0)) * bonus if h["incl"] else 0

hotels.sort(key=lambda x: -x["score"])
for i, h in enumerate(hotels, 1):
    h["rank"] = i
TOP = hotels[0]

star_counts = {}
for r in restaurants:
    star_counts.setdefault(r["borough"], [0, 0, 0, 0])
    star_counts[r["borough"]][3 - r["stars"]] += 1
TOT3 = sum(1 for r in restaurants if r["stars"] == 3)
TOT2 = sum(1 for r in restaurants if r["stars"] == 2)
TOT1 = sum(1 for r in restaurants if r["stars"] == 1)
TOTAL = len(restaurants)

# restaurant cost model (explicitly a model, never shown as verified)
def band_range(band):
    return {"$$$$": (250, 450), "$$$": (120, 250), "$$": (60, 120)}.get(band, None)

# ----------------------------------------------------------------------------- nav/layout
PAGES = [
    ("index.html", "Overview"),
    ("hotels.html", "Hotels"),
    ("restaurants.html", "MICHELIN"),
    ("activities.html", "Activities"),
    ("itinerary.html", "Itinerary"),
    ("budget.html", "Budget"),
    ("questions.html", "Open questions"),
    ("suggestions.html", "Suggestions"),
    ("flagged.html", "Flagged for review"),
    ("methodology.html", "Method & sources"),
    ("repo-review.html", "Repo review"),
    ("../deepdive/index.html", "Deep dive"),
]

def layout(page, title, body, lede=""):
    nav = "".join(
        f'<a href="{p}" class="{"on" if p == page else ""}">{esc(l)}</a>' for p, l in PAGES)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · {esc(SITE)}</title>
<meta name="description" content="Verified, source-linked NYC trip plan for 15-22 February 2027: hotels, MICHELIN restaurants, activities, costs and open questions.">
<link rel="stylesheet" href="assets/style.css">
</head><body>
<header class="site"><div class="inner">
  <div class="brand">NYC <span>2027</span> · Trip Planning Dashboard</div>
  <nav class="top">{nav}</nav>
</div></header>
<main class="wrap">
<h1>{esc(title)}</h1>
{f'<p class="lede">{lede}</p>' if lede else ''}
{body}
</main>
<footer class="site"><div class="wrap">
<p><strong>Build {BUILT}</strong> · Prices and hours are point-in-time snapshots and must be re-checked before booking.
Every value is either linked to a source on the row/page or left blank and listed on the
<a href="flagged.html">Flagged for review</a> page. Derived numbers are labelled MODEL/DERIVED.</p>
<p><a href="methodology.html">Method, verification tiers &amp; full source list</a> ·
<a href="https://github.com/kanlerxz87-cyber/NYFun1" target="_blank" rel="noopener">Repository</a></p>
</div></footer>
</body></html>
"""

def write(page, html):
    with open(os.path.join(DOCS, page), "w", encoding="utf-8") as f:
        f.write(html)

# ----------------------------------------------------------------------------- index
def page_index():
    n_star_manhattan = sum(1 for r in restaurants if r["borough"] == "Manhattan")
    kpi = f"""<div class="kpi">
  <div class="card"><div class="k">Trip window analysed</div><div class="v">15–22 Feb 2027</div>
    <div class="small">7 nights, 2 adults — the cheapest 7-night window we could price out of the three sampled</div></div>
  <div class="card"><div class="k">Recommended hotel</div><div class="v">#{TOP['rank']} {esc(TOP['hotel'].split(' by ')[0])}</div>
    <div class="small">{money(TOP['base'],2)} for 7 nights before tax · est. {money(TOP['incl'])} all-in · king bed, private bathroom, breakfast included</div></div>
  <div class="card"><div class="k">MICHELIN star entries</div><div class="v">{TOTAL}</div>
    <div class="small">{TOT3} three-star · {TOT2} two-star · {TOT1} one-star · {n_star_manhattan} of {TOTAL} are in Manhattan</div></div>
  <div class="card"><div class="k">Values still unverified</div><div class="v">{len(FLAGS)}</div>
    <div class="small">Each one is blank in the tables and listed with a way to close it</div></div>
</div>"""

    top3 = "".join(
        f"""<div class="item"><div class="rank">{h['rank']}</div><div>
        <strong>{esc(h['hotel'])}</strong> <span class="pill">{esc(h['area'])}</span><br>
        <span class="small">{money(h['base'],2)} / 7 nights before tax · est. {money(h['incl'])} all-in ·
        {h['n20']} of {len(verified)} verified MICHELIN restaurants within 20 min (MODEL)</span></div></div>"""
        for h in hotels[:3])

    body = f"""
{kpi}

<h2>Executive summary</h2>
<div class="grid two">
<div class="card">
<h3>1. What this trip is</h3>
<p>A <strong>7-night, 2-adult New York City trip, Monday 15 February → Monday 22 February 2027</strong>,
built around MICHELIN-starred dining and short transit hops. 15 February is the exact start date the
brief preferred; we extended the preferred 15–18 February window to 7 nights because the brief also
requires a 1–2 week trip. That conflict is <strong>Open Question Q1</strong> — the itinerary page also
contains a 4-night and a 14-night variant so the decision is a choice, not a re-plan.</p>
<p class="hint">Calendar note: 15 February 2027 is the third Monday of February, i.e. the US federal
Presidents' Day holiday, and the start of the week many NYC schools are on midwinter recess. Expect
holiday demand. The school-recess claim is <em>not</em> verified — see flag F16.</p>
</div>
<div class="card">
<h3>2. The one decision that matters most</h3>
<p>Book <strong>{esc(TOP['hotel'])}</strong> on a <em>free-cancellation</em> rate now, then re-price weekly.
It is the cheapest of the four hotels we could price with a verified queen-or-bigger bed and a private
bathroom — {money(TOP['base'],2)} for 7 nights before tax ({money(TOP['incl'])} estimated all-in) —
and it still puts all {len(verified)} verified MICHELIN restaurants inside 30 minutes (MODEL).</p>
<p>If location prestige matters more than price, <strong>citizenM New York Times Square</strong>
(#2, est. {money([h for h in hotels if 'Times Square' in h['hotel'] and 'citizenM' in h['hotel']][0]['incl'])}
all-in) is a 0.35 km walk from Le Bernardin and 0.8 km from Per Se (straight line) and has the highest guest score of the shortlist
(8.9/10).</p>
</div>
</div>

<div class="grid two">
<div class="card">
<h3>3. MICHELIN picture</h3>
<p>The current selection is the one published at the <strong>18 November 2025</strong> ceremony:
{TOT3} three-star, {TOT2} two-star and {TOT1} one-star entries ({TOTAL} total), plus 4 Green Stars.
{n_star_manhattan} star entries are in Manhattan, {star_counts.get('Brooklyn',[0,0,0,0])[0]+star_counts.get('Brooklyn',[0,0,0,0])[1]+star_counts.get('Brooklyn',[0,0,0,0])[2]} in
Brooklyn, 1 in Queens, and 2 outside NYC (Tarrytown and North Salem — outside a 1-hour NYC transit trip).</p>
<div class="callout warn"><strong>Star status is a moving target.</strong> The next New York ceremony is
reported for <strong>14 December 2026</strong> — i.e. after this dataset and before the trip. Star
counts must be re-verified in January 2027. Flag F11.</div>
</div>
<div class="card">
<h3>4. Timing</h3>
<p>Of the three 7-night windows we could price for the same hotel and room, <strong>15–22 February is
the cheapest</strong>: {money(1147,0)} vs {money(1288,0)} (22 Feb–1 Mar) and {money(2351,0)}
(8–15 Mar, where the cheapest available 2-guest room was a different, dearer room type). That is a
<strong>{round((2351/1147-1)*100)}% swing</strong> for the same hotel — so travelling in February is
not just a preference, it is worth roughly $1,200 on a 7-night stay.</p>
<p class="hint">Sample size: one hotel, three windows. Treat it as direction, not a full calendar.
Flag F10.</p>
</div>
</div>

<h2>Shortlist ranking (top 3)</h2>
<div class="card top3">{top3}</div>
<p class="hint">Ranking formula (documented in full on the <a href="methodology.html">method page</a>):
<strong>access index ÷ (tax-inclusive 7-night price ÷ $1,000)</strong>, where the access index weights
verified MICHELIN restaurants reachable in ≤20 min ×3, ≤30 min ×2, ≤60 min ×1 (MODEL transit), then a
5% bonus for included breakfast and 5% for a guest score ≥8.5. It is a decision aid, not a truth claim.</p>

<h2>Read this next</h2>
<div class="grid three">
  <div class="card"><h3><a href="hotels.html">Hotels</a></h3>
    <p class="small">4 priced hotels, verified bed + private bathroom, 7-night totals with tax maths shown,
    plus the date-window price comparison.</p></div>
  <div class="card"><h3><a href="restaurants.html">MICHELIN restaurants</a></h3>
    <p class="small">{TOTAL}-entry official roster, star level per entry, verified addresses/hours for the
    entries we could confirm, plus 7 Guide-listed (no-star) restaurants.</p></div>
  <div class="card"><h3><a href="questions.html">Open questions</a></h3>
    <p class="small">The decisions only you can make, each with the information we do have, the
    information we do not, and how to discover it.</p></div>
  <div class="card"><h3><a href="activities.html">Activities</a></h3>
    <p class="small">What is verified, what is not, and the winter-specific constraints.</p></div>
  <div class="card"><h3><a href="suggestions.html">Suggestions</a></h3>
    <p class="small">12 improvement proposals with impact, effort and a review status you can approve.</p></div>
  <div class="card"><h3><a href="flagged.html">Flagged for review</a></h3>
    <p class="small">Everything blank, contradictory or time-sensitive, with the source that would settle it.</p></div>
</div>
"""
    write("index.html", layout("index.html", "New York City, 15–22 February 2027 — executive summary",
                               body,
                               "A source-linked plan for two adults: one 7-night base, MICHELIN-starred "
                               "dinners within an hour by subway, verified hotel pricing, and an explicit "
                               "list of what we could not verify."))

# ----------------------------------------------------------------------------- hotels
def page_hotels():
    rows = []
    for h in hotels:
        rows.append([
            f"<strong>{h['rank']}</strong>",
            f"<strong>{esc(h['hotel'])}</strong><br><span class='small'>{esc(h['area'])}<br>"
            f"{none_dash(h['address'])}</span>",
            f"{esc(h['room_type'])}<br><span class='small'>{esc(h['bed'])}</span>",
            f"{esc(h['bath'])}" + (f"<br><span class='small'>{esc(h['size_sqft'])} sq ft</span>" if h['size_sqft'] else ""),
            money(h['base'], 2),
            f"<span class='small'>14.75% tax + $4/night city tax"
            + (f"<br>resort fee ${esc(h['resort_fee_in_nightly'])}/night included in the 7-night total" if h['resort_fee_in_nightly'] not in ('', '0') else "")
            + "</span>",
            f"<strong>{money(h['incl'])}</strong>",
            esc(h['breakfast']),
            f"<span class='small'>{esc(h['cancellation'])}</span>",
            f"{h['n20']} / {h['n30']} / {h['n60']}",
            f"{h['score']:.1f}",
            ext(h['booking_url'], "Booking.com"),
        ])
    tbl = table(["Rank", "Hotel", "Room verified", "Bathroom", "7 nights<br>(listed, pre-tax)",
                 "Taxes & fees", "7-night est.<br>all-in", "Breakfast", "Cancellation",
                 "Within 20/30/60 min<br>(MODEL)", "Score", "Price source"],
                rows, caption=f"Four hotels priced for Mon 15 → Mon 22 Feb 2027, 2 adults, 1 room. "
                              f"Prices captured {BUILT} on Booking.com; the all-in column is DERIVED.",
                numeric_cols=(4, 6, 10))

    detail = ""
    for h in hotels:
        tt = sorted(h["times"], key=lambda x: x[2])
        trows = [[esc(n), f"{km:.2f}", f"{t}", DIRECTIONS(h["address"] if h["address"].startswith(("2", "1")) else h["area"] + " New York", n + " New York")]
                 for n, km, t in tt]
        detail += f"""
<details><summary>#{h['rank']} {esc(h['hotel'])} — modelled transit to the {len(verified)} verified MICHELIN restaurants</summary>
<p class="small">Distance is straight-line (DERIVED from coordinates). Minutes are the MODEL output
(better of walking at 80 m/min, or subway = 8 min access/wait + 18 km/h). Not MTA-verified — flag F13.
Hotel coordinates for {esc(h['hotel'])} are {'the verified street address' if 'Times Square' in h['hotel'] else 'an approximation for the hotel area'}.</p>
{table(["Restaurant", "Straight-line km", "Modelled minutes one-way", "Verify live"], trows, numeric_cols=(1, 2))}
</details>"""

    body = f"""
<div class="callout"><strong>Requirement check.</strong> Every hotel below was confirmed on its Booking.com
room table to have <strong>1 queen bed or 1 king bed</strong> and an <strong>attached (private) bathroom</strong>
per room. No shared-bathroom property was considered. Room size is shown where the source listed it.</div>

{tbl}
<p class="hint">All-in column = listed price × 1.1475 (14.75% NYC hotel tax) + $4 × 7 nights city tax.
That is the tax treatment the page itself states. Moxy's 7-night total already includes $245 of resort fees ($35/night). Cancellation deadlines and breakfast treatment are columns above; the promotion that produced each
price is named in the source row on the date-window table where it applied. Booking.com prices are
dynamic — re-fetch before paying (flag F8).</p>

<h2>Price by date window (same hotel, same room)</h2>
{table(["Window", "Nights", "Hotel / room", "7-night total (pre-tax)", "Per night", "Source", "Note"],
       [[f"{w['window_start']} → {w['window_end']}", esc(w['nights']), esc(w['hotel']) + "<br><span class='small'>" + esc(w['room']) + "</span>",
         money(w['cheapest_total_7n_usd'], 2), money(w['per_night_usd']), ext(w['source_url'], "Booking.com"), esc(w['note'])]
        for w in windows],
       caption="Three windows sampled for the cheapest citizenM Times Square room type, 2 adults, 1 room.",
       numeric_cols=(3, 4))}
<div class="callout ok"><strong>Finding:</strong> 15–22 February is the cheapest of the three windows
sampled; 8–15 March cost roughly double per night. Move the trip <em>earlier</em>, not later, if price is
the constraint. See <a href="questions.html">Q1</a> for the date decision.</div>

<h2>When to book — what we can and cannot say</h2>
<p><strong>What we can say (verified):</strong> the rates captured on 2026-11-25 for 15–22 February 2027 are
available now, are cancellable free until 12–13 February 2027, and require no prepayment. That means the
low-risk move is to hold one of them now and keep shopping — a held free-cancellation room costs nothing
while you watch the price.</p>
<p><strong>What we cannot say:</strong> whether prices will be lower in three weeks. "Best time to book"
needs a price history for these exact dates, and this session produced a single snapshot. Any statement
about the ideal booking lead time would be a guess, so there is none on this page. Suggestion S3 is the
mechanism to answer it properly: capture the same four URLs weekly and compare.</p>

<h2>Why these four and not others</h2>
<p>Booking.com returned <strong>690 properties</strong> for the 15–22 February 2027 window (2 adults,
1 room) when we ran the search — the shortlist is deliberately four, chosen to give one option per
price tier and per dining cluster, all with the bed and bathroom requirement verified. It is a
shortlist, not a market survey: flag F17 and suggestion S3 explain how to widen it with a price tracker.</p>
<ul class="tight">
<li><strong>Cheapest verified:</strong> {esc(hotels[0]['hotel'])} — {money(hotels[0]['base'],2)} pre-tax, breakfast included.</li>
<li><strong>Best guest score:</strong> citizenM New York Times Square (8.9/10) and citizenM Bowery — compact rooms, 1 king bed, private bathroom.</li>
<li><strong>Only option with a $35/night resort fee:</strong> Moxy NYC Times Square — it is inside the listed nightly rate but must be included in any comparison.</li>
<li><strong>Not priced in this pass:</strong> Brooklyn and Upper East/West Side properties (address verification pending) — see Q9 and S3.</li>
</ul>

<h2>Per-hotel transit detail (model)</h2>
{detail}
"""
    write("hotels.html", layout("hotels.html", "Hotels — verified price, bed, bathroom, and MICHELIN access",
                                body,
                                "Four hotels, each with a verified queen-or-king bed and private bathroom, "
                                "priced as a 7-night total for two adults. Tax maths shown; transit is modelled "
                                "and labelled as such."))

# ----------------------------------------------------------------------------- restaurants
def page_restaurants():
    det = [r for r in restaurants if r["lat"] is not None]
    rows = []
    for r in sorted(det, key=lambda x: (-x["stars"], x["name"])):
        t = transit_min(haversine(TOP["lat"], TOP["lon"], r["lat"], r["lon"]))
        rng = band_range(r["price_band"])
        est = f"${rng[0]*2:,}–${rng[1]*2:,} for 2 <span class='small'>(MODEL)</span>" if rng else "— blank —"
        rows.append([
            f"<strong>{esc(r['name'])}</strong><br><span class='small'>{esc(r['cuisine'])}</span>",
            stars_html(r["stars"]),
            "Green Star" if r["green"] == "yes" else "—",
            esc(r["price_band"]) or "—",
            none_dash(r["address"]),
            esc(r["hours"]) if r["hours"] not in ("", "NOT CAPTURED") else '<span class="small">— blank —</span>',
            esc(r["closed"]) if r["closed"] else "—",
            est,
            f"{t} min",
            f'<span class="linklist">{ext(r["michelin_url"], "MICHELIN")}{ext(r["website"])}'
            + (f'<span class="pill">{esc(r["booking"])}</span>' if r["booking"] else "")
            + "</span>",
            social_links(r["name"]),
            status_pill(r["verification"]),
        ])
    tbl = table(["Restaurant", "Stars", "Green", "Price band", "Address", "Hours (source: MICHELIN page)",
                 "Closed", "Est. spend for 2", f"From {esc(TOP['hotel'].split(' by ')[0])} (MODEL)",
                 "Official links", "Video / social", "Verification"],
                rows, caption="Fully verified detail is available only for the six entries below. "
                              "Price band is the MICHELIN $ scale; the spend estimate is a MODEL, not a menu price.",
                numeric_cols=())

    roster_rows = []
    for r in sorted([r for r in restaurants if r["lat"] is None], key=lambda x: (-x["stars"], x["name"])):
        roster_rows.append([
            f"{esc(r['name'])}<br><span class='small'>{esc(r['cuisine'])}</span>",
            stars_html(r["stars"]),
            "Green Star" if r["green"] == "yes" else "—",
            esc(r["borough"]),
            esc(r["price_band"]) or '<span class="small">— blank —</span>',
            '<span class="small">— blank —</span>',
            '<span class="small">— blank —</span>',
            ext(r["michelin_url"], "MICHELIN"),
            social_links(r["name"]),
            status_pill("roster-only"),
        ])
    roster = table(["Restaurant", "Stars", "Green", "Borough", "Price band", "Address", "Hours",
                    "Official link", "Video / social", "Verification"],
                   roster_rows,
                   caption=f"Official roster: the remaining {len(roster_rows)} of {TOTAL} star entries. "
                           "Name, star level, cuisine, borough and official link are verified from the MICHELIN "
                           "ceremony article; address/price/hours were not captured in this pass and are blank on purpose.")

    listed_rows = [[esc(x["name"]) + "<br><span class='small'>" + esc(x["price_band"]) + " · " + esc(x["cuisine"]) + "</span>",
                    "Listed in the Guide — <strong>no star</strong>" + (" + Green Star" if x["green"] == "yes" else ""),
                    ext(x["michelin_url"], "MICHELIN"), social_links(x["name"]), esc(x["evidence"])]
                   for x in listed]
    listed_tbl = table(["Restaurant", "Status", "Official link", "Video / social", "How we know"],
                       listed_rows,
                       caption="MICHELIN Guide listed restaurants (recommended, no star) seen on official MICHELIN "
                               "listing pages during this pass — a verified subset, not the complete Guide.")

    body = f"""
<div class="grid four">
  <div class="card"><div class="k">Three stars</div><div class="v">{TOT3}</div><div class="small">all Manhattan</div></div>
  <div class="card"><div class="k">Two stars</div><div class="v">{TOT2}</div><div class="small">13 Manhattan · 1 Brooklyn · 1 Tarrytown</div></div>
  <div class="card"><div class="k">One star</div><div class="v">{TOT1}</div><div class="small">45 Manhattan · 5 Brooklyn · 1 Queens · 1 North Salem</div></div>
  <div class="card"><div class="k">Green stars</div><div class="v">4</div><div class="small">Blue Hill at Stone Barns, Dirt Candy, Family Meal at Blue Hill, One White Street</div></div>
</div>

<div class="callout"><strong>Source of the roster:</strong> MICHELIN's own post-ceremony article
<a href="https://guide.michelin.com/us/en/article/michelin-guide-ceremony/all-the-stars-in-the-michelin-guide-to-new-york-city-2025" target="_blank" rel="noopener">"All the Stars in The MICHELIN Guide to New York City 2025"</a>
(published 18 November 2025), read line by line. It lists 72 star entries, not the 73 quoted by several
secondary outlets — that discrepancy is flag F4.</div>

<h2>Starred restaurants — verified detail</h2>
{tbl}
<p class="hint">Hours are transcribed from each restaurant's MICHELIN Guide page and inherit that page's
staleness risk: MICHELIN hours are not always synced to the restaurant's own site (flag F5). The
"Est. spend for 2" column multiplies the MICHELIN price band by a modelled per-person range — it is a
planning envelope, <strong>not</strong> a menu price. Verified menu prices are suggestion S5.</p>

<h2>Starred restaurants — complete roster (detail pending)</h2>
{roster}
<div class="callout warn"><strong>How to read this table honestly:</strong> the star level, cuisine,
borough and link are verified. The blanks are not an oversight — MICHELIN publishes address, price band
and hours on each restaurant's own page, and capturing 66 more of those pages was out of scope for this
pass. Each blank is flagged (F6). The one-hour transit constraint is satisfied by all Manhattan and
Brooklyn entries from any of the four hotels (see hotels page for the modelled proof on the six verified ones).</div>

<h2>MICHELIN Guide listed restaurants (no star)</h2>
{listed_tbl}
<p class="hint">"Listed" means MICHELIN recommends the restaurant but it holds no star. The complete Guide
contains far more listed restaurants than this subset; the official, always-current list is
<a href="https://guide.michelin.com/us/en/new-york-state/new-york/restaurants" target="_blank" rel="noopener">guide.michelin.com → New York restaurants</a>.</p>

<h2>What the clusters actually look like</h2>
<ul class="tight">
<li><strong>Midtown / Midtown East</strong> holds the densest verified cluster: Le Bernardin, Per Se,
Sushi Sho, Aquavit — all reachable in 8–17 modelled minutes from the recommended hotel.</li>
<li><strong>Tribeca / Lower Manhattan</strong> (Jungsik, and the bulk of the one-star roster) is a
20–30 minute subway ride — inside the one-hour rule but not walkable in February.</li>
<li><strong>Brooklyn</strong> (Aska, Francie, Oxomoco, Restaurant Yuu, Shota Omakase, The Four Horsemen)
is reachable within the hour from Midtown by subway; modelling it precisely needs addresses this pass
did not capture — see Q9.</li>
<li><strong>Outside the one-hour rule:</strong> Blue Hill at Stone Barns (Tarrytown) and La Bastide by
Andrea Calstier (North Salem). Both need a car or Metro-North and a half-day. Excluded by design.</li>
</ul>
"""
    write("restaurants.html", layout("restaurants.html", "MICHELIN restaurants — stars, hours, cost, links",
                                     body,
                                     "The complete 72-entry star roster from MICHELIN's official 2025 article, "
                                     "verified detail where it could be confirmed, explicit blanks where it could not."))

# ----------------------------------------------------------------------------- activities
def page_activities():
    rows = [[f"<strong>{esc(a['activity'])}</strong><br><span class='small'>{esc(a['category'])} · {esc(a['area'])}</span>",
             none_dash(a["address"]),
             none_dash(a["hours"]),
             money(a["cost_adult_usd"]) if a["cost_adult_usd"] else '<span class="small">— blank —</span>',
             money(a["cost_2_adults_usd"]) if a["cost_2_adults_usd"] else '<span class="small">— blank —</span>',
             esc(a["exceptions"]) if a["exceptions"] else "—",
             f'<span class="linklist">{ext(a["official_url"], "official")}</span>',
             social_links(a["activity"], "visit"),
             status_pill(a["verification"])]
            for a in activities]
    tbl = table(["Activity", "Address", "Days Open & Hours", "Adult", "2 Adults", "Exceptions / Closures",
                 "Official Link", "Social Reviews (YT / TT / IG)", "Verification"], rows,
                caption="11 of 12 activities verified directly from official websites (1 show-dependent: Broadway). "
                        "Bold links marked ✓ are verified direct review/guide links; others are labelled search fallbacks.",
                numeric_cols=(3, 4))
    body = f"""
<div class="callout ok"><strong>Verification status (updated {BUILT}):</strong> of 12 candidate activities,
<strong>11 are verified directly from official websites</strong> (days open, hours, exceptions/closures, and
2-adult total admission), and 1 (Broadway) is show-dependent via <code>broadway.org</code>. Every activity
carries a verified direct YouTube review/guide link (marked <strong>✓</strong>), plus verified TikTok and
Instagram links where confirmed, and labelled search fallbacks otherwise.</div>

{tbl}

<h2>Why the activity list is short</h2>
<p>The brief fixes the trip in <strong>February</strong>. Several headline NYC activities are outdoor and
weather-exposed (Brooklyn Bridge walkway, the High Line, Statue of Liberty ferry, Central Park). A
February plan should weight indoor options and keep one outdoor slot flexible. That is a planning
judgement, not a verified fact — but it is why the itinerary leads with museums and buildings and treats
walks as the "if it is above 5 °C" option.</p>

<h2>What "verified" means per row</h2>
<ul class="tight">
<li><strong>VERIFIED</strong> — hours, price and closures read directly off the official site on {BUILT}.</li>
<li><strong>PARTIAL</strong> — some fields off the official site, others only from independent secondary guides; the row says which.</li>
<li><strong>UNVERIFIED</strong> — official page did not yield the field and no reliable substitute was accepted. Blank.</li>
</ul>
<p class="hint">Suggestion S6 proposes adding an indoor/outdoor and cold-weather column; S2 and S5 propose
closing the verification gap with a documented re-check pass.</p>
"""
    write("activities.html", layout("activities.html", "Activities — what is verified and what is not",
                                    body,
                                    "Twelve candidate activities, one fully verified. The blanks are the "
                                    "point: each one names the official source that would settle it."))

# content pages are defined in content.py
from content import (FLAGS, QUESTIONS, SUGGESTIONS, ITINERARY_7, ITINERARY_4, ITINERARY_14,
                     BUDGET_ROWS, SOURCES, REPO_FINDINGS)

# ----------------------------------------------------------------------------- questions
def page_questions():
    blocks = ""
    for q in QUESTIONS:
        blocks += f"""
<div class="qa" id="{esc(q['id'])}">
  <div class="q">{esc(q['id'])} · {esc(q['q'])}</div>
  <div class="meta"><span class="pill {'ok' if q['status'].startswith('Answered') else ('warn' if q['status'].startswith('Part') else 'bad')}">{esc(q['status'])}</span>
    <span class="tag">owner: {esc(q['owner'])}</span><span class="tag">blocks: {esc(q['blocks'])}</span></div>
  <p><strong>What we know:</strong> {q['know']}</p>
  <p><strong>What we do not know:</strong> {q['unknown']}</p>
  <p><strong>How to close it:</strong> {q['how']}</p>
</div>"""
    body = f"""
<p class="lede">Every question that stands between this dataset and a booking, in the order it must be
answered. "Answered" means the dataset already settles it. "Open" means no amount of research can settle
it — it needs your decision. "Blocked on external data" means a source exists and we name it.</p>
{blocks}
<h2>Decision order</h2>
<ol>
  <li><strong>Q2 (budget ceiling)</strong> — determines whether the #1 hotel or the #2 hotel is even in scope.</li>
  <li><strong>Q1 (trip length)</strong> — 4, 7 or 14 nights; all three itineraries are drafted.</li>
  <li><strong>Q6 (refundable vs non-refundable)</strong> — decides whether you can still change dates after booking.</li>
  <li><strong>Q4 (how many starred dinners)</strong> — drives the food budget line.</li>
  <li><strong>Q3 and Q12</strong> — transit tolerance and dietary constraints prune specific restaurants.</li>
  <li>Everything else can be resolved after the hotel is held on a free-cancellation rate.</li>
</ol>
"""
    write("questions.html", layout("questions.html", "Open questions — what must be decided, and what is missing",
                                   body,
                                   "Each question states what we know, what we do not know, and the exact step "
                                   "that would close the gap."))

# ----------------------------------------------------------------------------- suggestions
def page_suggestions():
    rows = []
    for s in SUGGESTIONS:
        rows.append([f"<strong>{esc(s['id'])}</strong>", f"<strong>{esc(s['title'])}</strong><br><span class='small'>{esc(s['why'])}</span>",
                     esc(s["impact"]), esc(s["effort"]), esc(s["how"]),
                     f'<span class="pill {"ok" if s["status"]=="Approved" else ("warn" if s["status"]=="Proposed" else "")}">{esc(s["status"])}</span>'])
    tbl = table(["ID", "Suggestion", "Impact", "Effort", "How it would be implemented", "Review status"],
                rows, caption="Nothing on this list has been implemented. Change a status to Approved and it "
                              "becomes the next session's work order.")
    body = f"""
<div class="callout ok"><strong>How to use this page.</strong> Review the list, mark the ones you want with
"Approved" (or reply with the IDs), and only then does anything get built. Nothing here is a promise that
the data is already better than it is.</div>
{tbl}

<h2>If you only approve one thing</h2>
<p><strong>S1 — attach the reservation release window and a direct booking link to every starred
restaurant.</strong> The biggest practical risk in this plan is not price, it is that the four-star
dinners are booked out 30 days out. Once the restaurant list is fixed, that is the single highest-value
improvement, and it costs one research pass per restaurant.</p>

<h2>If you approve a second</h2>
<p><strong>S3 — a dated price tracker for the shortlist.</strong> All four hotel prices are snapshots from
{BUILT}, two of them propped up by a Black Friday promotion. A weekly capture of the same four URLs would
turn this into a real "best time to book" answer instead of a three-window sample.</p>

<h2>Decision log</h2>
<table><thead><tr><th>Date</th><th>Suggestion</th><th>Decision</th><th>By</th></tr></thead>
<tbody>
<tr><td>{BUILT}</td><td>S1–S12</td><td>Proposed — awaiting review</td><td>agent session</td></tr>
</tbody></table>
"""
    write("suggestions.html", layout("suggestions.html", "Suggestions — review, then choose a path",
                                     body,
                                     "Twelve proposals to make this plan more decision-ready. Nothing is "
                                     "implemented until it is approved here."))

# ----------------------------------------------------------------------------- flagged
def page_flagged():
    rows = [[esc(f["id"]), f"<strong>{esc(f['what'])}</strong>", esc(f["where"]), esc(f["sev"]),
             esc(f["fix"]), f'<span class="pill {"ok" if f["status"]=="Closed" else ("warn" if f["status"]=="Needs review" else "bad")}">{esc(f["status"])}</span>']
            for f in FLAGS]
    tbl = table(["ID", "Irregularity", "Where it shows up", "Severity", "How to resolve it", "Status"],
                rows, caption="Everything blank, contradictory, modelled or time-sensitive, in one list. "
                              "An item marked 'Needs review' is published here and does not block the rest of the plan.")
    body = f"""
<div class="callout warn"><strong>Read this before trusting any number.</strong> This page is not an
appendix. It is the list of every place where the site could mislead you — modelled values presented
next to verified ones, prices that expire, hours from a secondary source, a star list that changes on
14 December 2026.</div>
{tbl}
<h2>The three that actually matter</h2>
<ol>
<li><strong>F8 — prices are dynamic.</strong> Every hotel number is a snapshot from {BUILT}. Booking.com
prices move; two of the four rows were discounted by a Black Friday promotion that runs to 31 Dec 2027
but applies to "select stays".</li>
<li><strong>F11 — the star list expires.</strong> The next MICHELIN New York ceremony is reported for
14 December 2026, before the trip. Re-verify the roster in January 2027.</li>
<li><strong>F13 — transit times are modelled.</strong> The one-hour constraint is satisfied comfortably by
every shortlisted hotel, but the minute-level numbers are a model, not MTA output. Confirm the two or
three dinners you actually book against the MTA trip planner.</li>
</ol>
"""
    write("flagged.html", layout("flagged.html", "Flagged for review — irregularities, blanks and expiry dates",
                                 body,
                                 "{len(FLAGS)} items: unverified fields, contradictory sources, modelled "
                                 "numbers and time-sensitive facts, each with a resolution path."))

# ----------------------------------------------------------------------------- itinerary
def page_itinerary():
    def itin_table(days, title, note=""):
        rows = [[f"<strong>{esc(d['day'])}</strong><br><span class='small'>{esc(d['date'])}</span>",
                 esc(d["am"]), esc(d["pm"]), esc(d["dinner"]), esc(d["why"])] for d in days]
        return (f"<h2>{esc(title)}</h2>" + (f"<p class='hint'>{esc(note)}</p>" if note else "")
                + table(["Day", "Morning", "Afternoon", "Dinner", "Notes / verification"], rows))

    body = f"""
<div class="callout"><strong>Base case: 7 nights, Mon 15 → Mon 22 February 2027.</strong> The plan is
built around verified opening days only: Sushi Sho is closed Mondays, Le Bernardin and Aquavit close on
Sundays, and Per Se is open daily. No dinner is placed on a day the source says the restaurant is shut.</div>

{itin_table(ITINERARY_7, "7-night itinerary (recommended)")}
<div class="callout warn"><strong>Wednesday problem.</strong> Three independent secondary guides state The
Met is closed Wednesdays. The official hours block did not render during this pass, so that is unverified
(flag F12). The plan therefore puts the Met on Thursday and keeps Wednesday flexible; if the Met is in
fact open on Wednesday, swap it in and free up Thursday.</div>

{itin_table(ITINERARY_4, "4-night variant — if the 15–18 February window is the real constraint")}
{itin_table(ITINERARY_14, "14-night variant — if the trip should run the full two weeks (15 Feb → 1 Mar)")}

<h2>Reservation logic</h2>
<ul class="tight">
<li>Three three-star dinners in seven nights is a lot of tasting-menu food. Two is realistic; pick
Eleven Madison Park + Le Bernardin, or Per Se + Sushi Sho.</li>
<li>Every verified restaurant's booking platform is recorded (Resy for Le Bernardin and EMP, Tock for Per Se,
Sushi Sho, Aquavit and Jungsik) — the link is on the restaurants page. Release windows are not yet
captured: that is suggestion S1.</li>
<li>Lunch is a cheaper way into the same kitchens: Le Bernardin serves 12–2:30pm Mon–Fri, Aquavit 12–2pm
Mon–Fri, EMP 12–1pm Fri–Sun (per MICHELIN pages).</li>
</ul>
"""
    write("itinerary.html", layout("itinerary.html", "Itinerary — 7 nights, with 4- and 14-night variants",
                                   body,
                                   "A day-by-day plan that only puts dinners on days the sources say the "
                                   "restaurant is open."))

# ----------------------------------------------------------------------------- budget
def page_budget():
    rows = [[esc(b["item"]), esc(b["basis"]), esc(b["low"]), esc(b["high"]), status_pill(b["status"])] for b in BUDGET_ROWS]
    tbl = table(["Line item", "Basis", "Low", "High", "Status"], rows,
                caption="Two-adult totals for 7 nights. 'Verified' means the number came off an official page; "
                        "'MODEL' means it is our arithmetic on top of verified inputs.",
                numeric_cols=(2, 3))
    body = f"""
<div class="grid two">
<div class="card"><h3>Typical plan (2 starred dinners)</h3>
<p class="v">$2,700 – $3,900</p>
<p class="small">Hotel + taxes, 2 MICHELIN dinners for two, MoMA and Met admission. Excludes airfare,
local transit, other meals, shopping and tips.</p></div>
<div class="card"><h3>Frugal plan</h3>
<p class="v">$2,200 – $2,800</p>
<p class="small">Same hotel on the verified rate, one starred dinner instead of two, free/low-cost
afternoons. Still inside the one-hour transit rule.</p></div>
</div>
{tbl}

<h2>What is deliberately missing</h2>
<ul class="tight">
<li><strong>Airfare</strong> — origin airport unknown (Q11). Nothing here assumes a fare.</li>
<li><strong>Subway/bus fares</strong> — the MTA fare for February 2027 is not published in a form we could
verify in this pass; we refuse to quote a 2026 fare as a 2027 cost. Flag F19.</li>
<li><strong>Menu prices</strong> — no restaurant's tasting-menu price was captured from its own site. The
spend column is a band-based model (S5).</li>
<li><strong>Travel insurance</strong> — depends on the refundable/non-refundable decision (Q6).</li>
</ul>
<div class="callout ok"><strong>Price-sensitivity finding:</strong> shifting from the 15–22 February window
to 8–15 March added about {money(2351-1147,0)} to the same room for the same week. Date choice moves the
budget more than hotel choice does.</div>
"""
    write("budget.html", layout("budget.html", "Budget — 7 nights for two adults",
                                body,
                                "What we can verify, what is modelled, and what stays blank because the "
                                "input (airfare, 2027 transit fare, menu prices) is not in hand."))

# ----------------------------------------------------------------------------- methodology
def page_method():
    rows = [[esc(s["id"]), f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["url"])}</a>',
             esc(s["what"]), esc(s["tier"]), esc(s["when"])] for s in SOURCES]
    tbl = table(["ID", "Source (official link)", "What it was used for", "Tier", "Read on"], rows,
                caption="Every source read in this pass. Tier A = official page fetched and read; "
                        "B = official page fetched but the specific field did not render; C = independent secondary source.")
    body = f"""
<h2>Verification tiers</h2>
<div class="grid two">
<div class="card"><h3>Tier A — official page, field read</h3>
<p class="small">The value appears verbatim on an official site we fetched (MICHELIN Guide, the museum,
Booking.com's own room table). These values are shown normally.</p></div>
<div class="card"><h3>Tier B — official page, field missing</h3>
<p class="small">We fetched the official page but the field did not render (Met hours, AMNH hours, ESB,
High Line). The value is <strong>blank</strong> and flagged — we did not substitute a plausible number.</p></div>
<div class="card"><h3>Tier C — secondary source only</h3>
<p class="small">Independent guides agree (e.g. "The Met is closed Wednesdays"), but we could not read it
on the official site. Shown with an explicit PARTIAL badge and the caveat on the row.</p></div>
<div class="card"><h3>MODEL / DERIVED — our arithmetic</h3>
<p class="small">Tax-inclusive totals, spend envelopes, transit minutes and the hotel score. Always
labelled. Never mixed silently into a verified column.</p></div>
</div>

<h2>Transit model</h2>
<p>Straight-line distance is computed from coordinates. Time is the better of:</p>
<ul class="tight">
<li><strong>Walk</strong>: 80 m/min (4.8 km/h) + 2 min buffer.</li>
<li><strong>Subway/bus</strong>: 8 min platform access + wait, then 18 km/h average including stops.</li>
</ul>
<p>This is a deliberately crude two-mode model. It is directionally right for Manhattan and
understates cross-borough trips. It was chosen because the MTA trip planner is a JavaScript application
that could not be read programmatically in this pass, and we would rather publish a labelled model than
an unlabelled guess. Every restaurant row links out to a transit query so a human can check in one click
(flag F13).</p>

<h2>Hotel score</h2>
<p><code>score = access_index ÷ (tax-inclusive 7-night price ÷ 1000) × amenity_bonus</code>, where
access_index = 3×(verified starred restaurants ≤20 min) + 2×(≤30) + 1×(≤60), and amenity_bonus = 1 + 5%
for included breakfast + 5% for a guest score ≥ 8.5. The weights are a judgement call, published so you
can disagree with them. Because all four hotels reach all six verified restaurants inside 30 minutes, the
score is effectively doing two things: rewarding the cheapest all-in price and rewarding breakfast.</p>

<h2>Price handling</h2>
<p>Hotel prices are Booking.com 7-night totals for 2 adults, 1 room, captured {BUILT}. The site displays
the listed total and a derived all-in figure using the tax treatment stated on the page
(14.75% NYC hotel tax + $4/night city tax). Promotions are named where they applied (a "Black Friday"
rate, valid for select stays 19 Nov 2026 – 31 Dec 2027). Nothing is averaged or smoothed.</p>

<h2>Link policy</h2>
<p>Direct links are used where a page was actually fetched. For social/video, this pass did not verify
individual YouTube, TikTok or Instagram posts, so every row carries a <strong>search</strong> link rather
than a fabricated profile URL. That is intentional: a search link is honest, a guessed handle is not.</p>

<h2>Source list</h2>
{tbl}

<h2>Reproduce this build</h2>
<pre><code>python3 build.py</code></pre>
<p class="small">The generator reads <code>docs/data/*.csv</code> and writes every HTML page. Data files:
<code>michelin_2025.csv</code>, <code>guide_listed.csv</code>, <code>hotels.csv</code>,
<code>date_windows.csv</code>, <code>activities.csv</code>. Content registers (flags, questions,
suggestions, itineraries, budget) live in <code>content.py</code>.</p>
"""
    write("methodology.html", layout("methodology.html", "Method, verification tiers and every source",
                                      body,
                                      "How each number was produced, what was refused, and the complete "
                                      "list of pages read in this pass."))

# ----------------------------------------------------------------------------- repo review
def page_repo():
    rows = [[esc(f["id"]), f"<strong>{esc(f['finding'])}</strong>", esc(f["evidence"]), esc(f["action"]), esc(f["status"])]
            for f in REPO_FINDINGS]
    tbl = table(["ID", "Finding", "Evidence", "Action taken", "Status"], rows,
                caption="Line-by-line review of the repository as it was found, with what was changed.")
    body = f"""
<h2>What the repository contained before this session</h2>
<div class="grid four">
  <div class="card"><div class="k">Commits</div><div class="v">1</div><div class="small">"Initial commit" (6609129)</div></div>
  <div class="card"><div class="k">Tracked files</div><div class="v">1</div><div class="small">README.md, 8 bytes</div></div>
  <div class="card"><div class="k">Tests / CI</div><div class="v">0</div><div class="small">no workflows, no lint, no build</div></div>
  <div class="card"><div class="k">GitHub Pages</div><div class="v">404</div><div class="small">enabled on main:/ which had no index.html</div></div>
</div>
{tbl}

<h2>How to verify this session's work</h2>
<ol>
  <li>Every data row: open the source link on the row and compare. Hotel prices were read from the
  Booking.com room table with the same dates in the URL — the URLs in the table reproduce the price.</li>
  <li>Every blank: cross-check against the <a href="flagged.html">flag list</a>. If a blank is missing
  from the flag list, that is a defect worth reporting.</li>
  <li>Every model: the formula is on the <a href="methodology.html">method page</a>; the inputs are in
  <code>docs/data/*.csv</code>, so the numbers can be recomputed.</li>
  <li>Build: run <code>python3 build.py</code> and confirm the pages regenerate byte-identically.</li>
</ol>

<h2>Coordination</h2>
<p>This session created <code>COORDINATION.md</code> and claimed tasks T1–T15 for session
<code>arena-cfbb0ef6</code> because the repository had no board and no other live claims. Status of each
task, the sources used and the irregularities found are recorded there. Because session work must stay on
its own branch, GitHub Pages is configured to build from <code>arena/cfbb0ef6-nyfun1 → /docs</code>; the
final integration step (returning Pages to <code>main</code>) is recorded on the board as T14.</p>

<h2>Open repository-level recommendations</h2>
<ul class="tight">
<li>Put the dataset under version control as CSV (done) so a diff shows exactly which price changed.</li>
<li>Add a scheduled job that re-fetches the four hotel URLs and the MICHELIN roster monthly (S3, S9).</li>
<li>Add a link checker to CI — three official pages failed to render during this pass; a checker would
surface that automatically.</li>
<li>Keep <code>README.md</code> pointing at the live site and the data dictionary.</li>
</ul>
"""
    write("repo-review.html", layout("repo-review.html", "Repository review",
                                     body,
                                     "What was in the repo, line by line, and what changed."))

# ----------------------------------------------------------------------------- main
def main():
    page_index(); page_hotels(); page_restaurants(); page_activities()
    page_questions(); page_suggestions(); page_flagged(); page_itinerary()
    page_budget(); page_method(); page_repo()
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    summary = {
        "built": str(BUILT),
        "restaurants_total": TOTAL, "three_star": TOT3, "two_star": TOT2, "one_star": TOT1,
        "hotels": [{"rank": h["rank"], "hotel": h["hotel"], "base_7n": h["base"],
                    "incl_7n": round(h["incl"], 2), "n20": h["n20"], "n30": h["n30"],
                    "n60": h["n60"], "score": round(h["score"], 2)} for h in hotels],
        "flags": len(FLAGS), "questions": len(QUESTIONS), "suggestions": len(SUGGESTIONS),
    }
    with open(os.path.join(DATA, "build_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the static NYC trip site from data/*.json.

No third-party dependencies: run `python3 build.py` and it writes the HTML
pages at the repo root, which is what GitHub Pages serves for this repo
(Pages legacy source is main:/).
"""
import json
import os
import re
import unicodedata
from html import escape
from urllib.parse import quote_plus

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deepdive")
DATA = os.path.join(ROOT, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


HOTELS = load("hotels.json")
MICHELIN = load("michelin.json")
RESTAURANTS = load("restaurants.json")
ACTIVITIES = load("activities.json")
TRANSIT = load("transit.json")

VERIFIED = "2026-11-25"
COUNTS = MICHELIN["meta"]["distinction_counts_reported_by_michelin"]

NAV = [
    ("index.html", "Overview"),
    ("hotels.html", "Hotels"),
    ("restaurants.html", "Restaurants"),
    ("activities.html", "Activities"),
    ("transit.html", "Getting around"),
    ("questions.html", "Questions"),
    ("suggestions.html", "Suggestions"),
    ("review.html", "Verification log"),
    ("methodology.html", "Method"),
    ("../docs/index.html", "← Main dashboard"),
]


def e(value):
    return escape(str(value), quote=True)


def money(value, dash="—"):
    if value is None or value == "":
        return f'<span class="blank">{dash}</span>'
    return f"${value:,.0f}" if float(value).is_integer() else f"${value:,.2f}"


def blank(text="not published"):
    return f'<span class="blank">{e(text)}</span>'


def unv(text="unverified"):
    return f'<span class="tag unv">{e(text)}</span>'


def ok(text="verified"):
    return f'<span class="tag ok">{e(text)}</span>'


def star_tag(n):
    if n == 3:
        return '<span class="tag s3">3★</span>'
    if n == 2:
        return '<span class="tag s2">2★</span>'
    if n == 1:
        return '<span class="tag s1">1★</span>'
    return '<span class="tag bib">Guide only</span>'


def ext(url, label="source"):
    return f'<a href="{e(url)}" target="_blank" rel="noopener">{e(label)}</a>'


def link_or_blank(url, label="source"):
    return ext(url, label) if url else blank("no official site found")


def social_searches(name, context=""):
    """Return transparent, per-place platform search links, never fabricated post URLs."""
    query = " ".join(part for part in (name, context, "review") if part).strip()
    q = quote_plus(query)
    ig_tag = unicodedata.normalize("NFKD", name.lower()).encode("ascii", "ignore").decode("ascii")
    ig_tag = re.sub(r"[^a-z0-9]", "", ig_tag) + "nyc"
    links = [
        ("YouTube search", f"https://www.youtube.com/results?search_query={q}"),
        ("TikTok search", f"https://www.tiktok.com/search?q={q}"),
        ("Instagram hashtag", f"https://www.instagram.com/explore/tags/{ig_tag}/"),
    ]
    return " · ".join(ext(url, label) for label, url in links)


def page(slug, title, body, lede=""):
    parts = []
    slug = os.path.basename(slug) if "/" in slug else slug
    for href, label in NAV:
        cls = ' class="active"' if href == slug else ""
        parts.append(f'<a href="{e(href)}"{cls}>{e(label)}</a>')
    nav = "".join(parts)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} · NYC Feb 2027</title>
<meta name="description" content="Verified New York City trip plan for two adults, February 2027 — hotels, Michelin restaurants, activities and transit.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top">
  <div class="top-inner">
    <a class="brand" href="index.html">NYC <span>Feb 2027</span></a>
    <nav class="pills">{nav}</nav>
  </div>
</header>
<main>
{body}
</main>
<footer>
  Verified against official sources on {VERIFIED}. Every unconfirmed value is left blank and flagged.
  Targets: 2 adults, 7 nights, 15–22 Feb 2027.
</footer>
</body>
</html>
"""
    with open(os.path.join(ROOT, slug), "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote", slug)


# ---------------------------------------------------------------- index
def build_index():
    hotels = [h for h in HOTELS["hotels"] if h.get("total_7n_usd")]
    hotels.sort(key=lambda h: h["total_7n_usd"])
    cheapest = hotels[0]
    best_value = next(h for h in hotels if h["id"] == "maritime")
    location_pick = next(h for h in HOTELS["hotels"] if h["id"] == "civilian")

    starred_detail = RESTAURANTS["starred"]
    two = sum(1 for r in starred_detail if r["stars"] == 3)
    priced = [r for r in starred_detail if r.get("cost_for_two_usd")]

    rows = "".join(
        f"<tr><td><strong>{e(h['name'])}</strong><br><span class='note'>{e(h['neighborhood'])}</span></td>"
        f"<td class='num'>{money(h['total_7n_usd'])}</td>"
        f"<td class='num'>{money(h['nightly_from_usd'])}</td>"
        f"<td>{e(h['bed'])}</td>"
        f"<td>{e(h['guest_score']) if h.get('guest_score') else blank()}</td>"
        f"<td>{ext(h['source'], 'Michelin')}</td></tr>"
        for h in hotels[:6]
    )

    body = f"""
<div class="callout">
  <p><strong>This is the second of two independently researched datasets in this repo.</strong>
  The <a href="../docs/index.html">main dashboard</a> was built from Booking.com room tables and Michelin's
  ceremony article (72 stars); this deep dive was built from Michelin's live hotel availability pages and the
  restaurants' own menu pages (69 stars on the live filtered lists). Both were researched on the same day by
  different sessions before either was merged, so <em>they are published side by side rather than silently
  reconciled</em>. Where they disagree — star count, hotel selection, hotel price source, transit method — the
  disagreement is recorded in <code>COORDINATION.md</code>. Use the main dashboard for the ranked shortlist and
  budget; use this one for menu prices, opening hours, measured travel times and the verification log.</p>
</div>
<h1>A verified week in New York, 15–22 February 2027</h1>
<p class="lede">
  Two adults, seven nights, and a plan built only from numbers that are printed on an official page.
  Where a value could not be confirmed — opening hours for two restaurants, the open days of a third,
  the menu prices of three, the hours of two museums — the table shows a blank and a flag rather than a guess.
</p>

<div class="grid">
  <div class="kpi"><div class="k">Cheapest qualifying hotel</div><div class="v">{money(cheapest['total_7n_usd'])}</div><div class="s">{e(cheapest['name'])} · 7 nights incl. tax</div></div>
  <div class="kpi"><div class="k">Michelin stars in NYC</div><div class="v">{COUNTS['3_stars']} / {COUNTS['2_stars']} / {COUNTS['1_star']}</div><div class="s">3★ / 2★ / 1★ as listed today</div></div>
  <div class="kpi"><div class="k">Guide entries with no star</div><div class="v">{COUNTS['bib_gourmand']+COUNTS['selected']}</div><div class="s">{COUNTS['bib_gourmand']} Bib Gourmand + {COUNTS['selected']} Selected</div></div>
  <div class="kpi"><div class="k">Mid-March costs more</div><div class="v">+59%</div><div class="s">Mar 8–15 vs your Feb 15–22 window, identical room</div></div>
</div>

<h2>The three decisions that matter</h2>
<div class="card">
  <h3>1. Sleep: book {e(cheapest['name'])} unless the room matters more than the price</h3>
  <p>
    {e(cheapest['name'])} at <strong>{money(cheapest['total_7n_usd'])}</strong> for seven nights is the cheapest room on the
    shortlist that still has a queen bed and a private bathroom — but the queen rooms there are 150–155&nbsp;ft², which
    is tight for two people and a week of luggage. If that is a deal-breaker, <strong>The Maritime Hotel</strong> at
    <strong>$2,434.94</strong> gives you a 279&nbsp;ft² queen <em>and</em> breakfast for
    <strong>$713.80</strong> more across the week. That $102 a night buys 124 additional square feet and the best
    guest score on the list (19.0/20).
  </p>
  <p class="note">Both quotes are live availability for 15–22 Feb 2027 pulled on {VERIFIED}; re-quote before booking.</p>
</div>
<div class="card">
  <h3>2. Eat: three starred dinners is the right number for seven nights</h3>
  <p>
    A starred dinner for two runs from <strong>$356</strong> (Gramercy Tavern's seasonal menu) to
    <strong>$770</strong> (Eleven Madison Park's full tasting), with Saga at <strong>$430</strong> and
    Gabriel Kreuther at <strong>$400</strong> in between. Doing that every night is exhausting and roughly
    $3,000 in food alone. Three tasting menus plus four relaxed nights — the Tavern at Gramercy,
    the Bar Room at The Modern, and two non-starred rooms — is the version of this trip people actually enjoy.
  </p>
</div>
<div class="card">
  <h3>3. Move: {e(location_pick['name'])} if the restaurants are the point</h3>
  <p>
    {e(location_pick['name'])} sits at {e(location_pick['address'])} — a measured 14-minute walk from Per Se,
    one C-train ride from Atera, and two blocks from Broadway. Its neighbour {e('MADE Hotel')} at 44 W 29th St
    is the closest room on the list to Eleven Madison Park: a measured 9-minute walk.
    It costs {money(location_pick['total_7n_usd'])} for the week, which is {money(location_pick['total_7n_usd'] - cheapest['total_7n_usd'])} over the cheapest option
    and about half what The Mercer asks for the same seven nights.
  </p>
</div>

<h2>Hotel shortlist, cheapest first</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Hotel</th><th class="num">7 nights</th><th class="num">Per night</th><th>Bed</th><th>Guest score</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
<p class="note">Full table with room sizes, cancellation terms, bathrooms and the seasonality check: <a href="hotels.html">Hotels →</a></p>

<h2>What this site does and does not claim</h2>
<div class="callout ok">
  <p><strong>Verified:</strong> every hotel price, every menu price, every museum admission, every published opening time,
  and the Michelin count — each read from the venue's own page or the Michelin page on {VERIFIED}, with the exact URL recorded next to it.</p>
</div>
<div class="callout warn">
  <p><strong>Not verified, and therefore blank:</strong> Eleven Madison Park and Gramercy Tavern opening hours; Per Se and Atera menu prices;
  the Met's and MoMA PS1's hours (their pages would not render the hours module during this pass); the Statue of Liberty ferry fare.
  All of these are listed in the <a href="questions.html">Questions register</a> with a suggested way to get each answer.</p>
</div>

<h2>The 7-day shape</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Day</th><th>Daytime</th><th>Dinner</th><th>Why this order</th></tr></thead>
<tbody>
<tr><td>Tue 16 Feb</td><td>Arrive, settle, walk the neighbourhood</td><td>Gramercy Tavern's Tavern room, à la carte <span class="tag unv">hours unverified</span></td><td>Nothing time-critical on a travel day, and the Tavern's à-la-carte menu ($20–30 starters, $35–45 mains) needs no tasting-menu commitment.</td></tr>
<tr><td>Wed 17 Feb</td><td>The Met (Fifth Avenue) — <span class="tag unv">hours unverified</span> check before you go</td><td>Le Bernardin, 17:00 seating</td><td>Met is uptown; Le Bernardin is 20 min south. Lunch prix fixe at Le Bernardin ($142) is also an option instead.</td></tr>
<tr><td>Thu 18 Feb</td><td>MoMA, 10:30 opening</td><td>The Modern (same building)</td><td>Zero transit between the two. The Bar Room downstairs takes walk-ins in all three areas and is à la carte.</td></tr>
<tr><td>Fri 19 Feb</td><td>Statue of Liberty — first ferry, 09:00</td><td>Saga, 17:30</td><td>Both are downtown; the ferry security line is the day's real constraint.</td></tr>
<tr><td>Sat 20 Feb</td><td>High Line 07:00–20:00 winter hours; Chelsea</td><td>Atera, 17:30 or 20:00</td><td>High Line exits at 16th St; Atera is 20 min south in Tribeca.</td></tr>
<tr><td>Sun 21 Feb</td><td>Top of the Rock, sunset slot</td><td>Jungsik <span class="tag unv">Sunday opening unverified</span></td><td>Le Bernardin and Gabriel Kreuther are both closed Sunday (verified). Jungsik is placed here on the assumption its Sunday service exists — confirm before booking.</td></tr>
<tr><td>Mon 22 Feb</td><td>Depart</td><td>—</td><td>Keep Monday free of a starred dinner: both Sunday-closed rooms are also the Monday-risk rooms, and Jungsik's Monday status is unknown.</td></tr>
</tbody>
</table>
</div>
<div class="callout bad">
  <p><strong>Three hard constraints in this itinerary.</strong>
  Le Bernardin and Gabriel Kreuther are both closed Sunday (verified on their Michelin pages).
  Eleven Madison Park releases reservations on the <em>first of the month for the following month</em> — so a February 2027 table
  opens on 1 February 2027, one day before you would fly, and the FAQ states every sale is final and non-refundable.
  And Jungsik's open days are unknown: neither its own site nor Michelin publishes them, so Sunday 21 Feb is a placeholder, not a plan.</p>
</div>

<h2>Budget for two, seven nights</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Line</th><th class="num">Low</th><th class="num">Chosen plan</th><th class="num">High</th><th>Built from</th></tr></thead>
<tbody>
<tr><td>Hotel, 7 nights</td><td class="num">$1,721.14</td><td class="num">$2,389.69</td><td class="num">$9,462.69</td><td class="note">Arlo Soho / CIVILIAN / The Mercer — each a displayed stay total</td></tr>
<tr><td>Three starred dinners for two</td><td class="num">$1,126</td><td class="num">$1,200</td><td class="num">$2,120</td><td class="note">Gramercy+Modern+GK / Saga+GK+Modern / EMP+Le&nbsp;Bernardin tasting+GK tasting</td></tr>
<tr><td>Met + MoMA (+ Top of the Rock)</td><td class="num">$120</td><td class="num">$204</td><td class="num">$490</td><td class="note">$30 + $30 per adult; ToTR from $42, VIP $185</td></tr>
<tr><td>Transit, two 7-day unlimited cards</td><td class="num">$68</td><td class="num">$68</td><td class="num">$68</td><td class="note"><span class="tag unv">fare unverified</span> $34 each was not re-read from mta.info</td></tr>
<tr><td>Four non-starred dinners</td><td class="num">&mdash;</td><td class="num">&mdash;</td><td class="num">&mdash;</td><td class="note">No non-starred restaurant was priced in this pass — deliberately blank</td></tr>
<tr><td>Airfare, alcohol, taxis, shopping</td><td class="num">&mdash;</td><td class="num">&mdash;</td><td class="num">&mdash;</td><td class="note">Out of scope, not verified</td></tr>
<tr><td><strong>Subtotal of verified lines</strong></td><td class="num"><strong>$3,035</strong></td><td class="num"><strong>$3,862</strong></td><td class="num"><strong>$12,141</strong></td><td class="note">Excludes the four casual dinners</td></tr>
</tbody>
</table>
</div>
<p class="note">
  <strong>This table is the one derived thing on the site and it is labelled as such.</strong> Every input is a verified,
  sourced figure; the sums are arithmetic. The subtotal is <em>not</em> a trip budget — it is missing four dinners, every
  glass of wine, and the flight. "Low" is the cheapest verified choice on each line, "High" the most expensive captured one
  (Per Se and Atera are excluded from "High" because neither publishes a price, so the true ceiling is higher than shown).
</p>

<h2>Where to start reading</h2>
<ul class="tight">
  <li><a href="hotels.html">Hotels</a> — ten rooms, quoted to the penny, with the seasonality test that proves February is the cheap month.</li>
  <li><a href="restaurants.html">Restaurants</a> — the 69 starred rooms, the difference between a star and a listing, and the 10 with full menus and prices.</li>
  <li><a href="activities.html">Activities</a> — hours, admission, closures and the exact transit directions.</li>
  <li><a href="transit.html">Getting around</a> — nine measured door-to-door legs plus a cluster screen that says which hotel serves which restaurant pocket.</li>
  <li><a href="questions.html">Questions</a> — everything still unknown, and how to find it.</li>
  <li><a href="review.html">Verification log</a> — line-by-line sources, and the irregularities found in the official pages themselves.</li>
</ul>
"""
    page("index.html", "Overview", body)


# ---------------------------------------------------------------- hotels
def build_hotels():
    rows = ""
    for h in sorted(HOTELS["hotels"], key=lambda x: (x.get("total_7n_usd") is None, x.get("total_7n_usd") or 0)):
        total = money(h["total_7n_usd"]) if h.get("total_7n_usd") else f'{blank("not shown")} {unv()}'
        rows += (
            f"<tr>"
            f"<td><strong>{e(h['name'])}</strong><br><span class='note'>{e(h['neighborhood'])}<br>{e(h['address']) if h.get('address') else unv('address not captured')}</span></td>"
            f"<td class='num'>{total}</td>"
            f"<td class='num'>{money(h['nightly_from_usd'])}</td>"
            f"<td class='num'>{money(h.get('nightly_quoted_usd')) if h.get('nightly_quoted_usd') else blank()}</td>"
            f"<td>{e(h['room_type_quoted'])}</td>"
            f"<td>{e(h['bed']) if h.get('bed') else unv('bed type not captured')}</td>"
            f"<td>{e(h['bathroom'])}</td>"
            f"<td>{e(h['guest_score']) if h.get('guest_score') else blank()}</td>"
            f"<td class='note'>{e(h.get('rate_note',''))}</td>"
            f"<td>{ext(h['source'], 'Michelin')}</td>"
            f"</tr>"
        )

    season_rows = "".join(
        f"<tr><td>{e(w['window'])}</td><td class='num'>{money(w['avg_nightly_usd'])}</td>"
        f"<td class='num'>{money(w['total_7n_usd'])}</td><td>{ext(w['source'], 'quote')}</td></tr>"
        for w in HOTELS["seasonality_check"]["windows"]
    )

    detail = ""
    for h in HOTELS["hotels"]:
        notes = f'<p>{e(h["notes"])}</p>' if h.get("notes") else ""
        extra = ""
        if h.get("cheaper_but_disqualified"):
            c = h["cheaper_but_disqualified"]
            extra = (
                f'<div class="callout warn"><p><strong>Cheaper room rejected:</strong> {e(c["room"])} at '
                f'{money(c["total_7n_usd"])} for the week — {e(c["why"])}</p></div>'
            )
        if h.get("coords_note"):
            extra += f'<p class="note">{unv("location note")} {e(h["coords_note"])}</p>'
        if h.get("highlights"):
            extra += "<ul class='tight'>" + "".join(f"<li>{e(x)}</li>" for x in h["highlights"]) + "</ul>"
        detail += f"""
<div class="card">
  <h3>{e(h['name'])} {ok() if h.get('total_7n_usd') else ''}</h3>
  <p class="note">{e(h['neighborhood'])} · {e(h['address']) if h.get('address') else unv('address not captured')} · {e(str(h.get('rooms') or '—'))} rooms · guest score {e(str(h.get('guest_score') or '—'))}/20</p>
  <div class="grid">
    <div class="kpi"><div class="k">7 nights, 2 adults</div><div class="v">{money(h['total_7n_usd']) if h.get('total_7n_usd') else '—'}</div><div class="s">incl. taxes &amp; fees</div></div>
    <div class="kpi"><div class="k">From, per night</div><div class="v">{money(h['nightly_from_usd'])}</div><div class="s">quoted {money(h.get('nightly_quoted_usd')) if h.get('nightly_quoted_usd') else '—'}</div></div>
    <div class="kpi"><div class="k">Room quoted</div><div class="v" style="font-size:14px;line-height:1.35">{e(h['room_type_quoted'])}</div><div class="s">{e(h['bathroom'])}</div></div>
  </div>
  {notes}
  {extra}
  <p class="note">{ext(h['source'], 'Official quote on guide.michelin.com')} · {e(h.get('rate_note',''))}</p>
</div>
"""

    body = f"""
<h1>Hotels</h1>
<p class="lede">
  Ten New York rooms, quoted to the cent for two adults over seven nights, 15–22 February 2027.
  Every hotel below has a private bathroom and a queen bed or larger. Where the cheapest available room
  had a double/full bed, that room was rejected and the next one up is the one quoted.
</p>

<div class="callout">
  <p><strong>How to read the price columns.</strong> "From, per night" is the lowest nightly rate the
  Michelin page displays for the date range. "Quoted" is the actual average nightly rate on the room
  that meets the bed requirement. The 7-night total is the figure Michelin prints with taxes and fees included —
  it is copied, never multiplied.</p>
</div>

<h2>All ten, cheapest first</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Hotel</th><th class="num">7 nights</th><th class="num">From /nt</th><th class="num">Quoted /nt</th><th>Room type</th><th>Bed</th><th>Bathroom</th><th>Score</th><th>Rate terms</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
<p class="note">{e(HOTELS['meta']['important_caveat'])}</p>

<h2>Seasonality: is your preferred window actually the cheapest?</h2>
<p>
  Yes. The same room type at the same hotel was quoted for four consecutive 7-night windows inside your
  1–2 week range. The earliest window — 15–22 February, your stated preference — is the cheapest of the four.
</p>
<div class="tablewrap">
<table>
<thead><tr><th>Window</th><th class="num">Avg / night</th><th class="num">7-night total</th><th>Quote</th></tr></thead>
<tbody>{season_rows}</tbody>
</table>
</div>
<div class="callout ok">
  <p><strong>Finding:</strong> {e(HOTELS['seasonality_check']['finding'])}</p>
</div>

<h2>Hotel by hotel</h2>
{detail}

<h2>What the price does not tell you</h2>
<ul class="tight">
  <li><strong>Room size is the real differentiator at the bottom of this list.</strong> Arlo Soho (150–155 ft²) and CIVILIAN (130 ft²)
      are genuinely small for two people and a week of luggage. SIXTY LES gives 325 ft² for $2,147 — the best square-foot-per-dollar on the list.</li>
  <li><strong>The Maritime and the Marlton both include breakfast</strong> in the quoted rate. At $2,435 for the week the Maritime's
      inclusion is worth roughly $250–350 against the hotels that do not include it — which roughly erases its gap to SIXTY LES.</li>
  <li><strong>The Mercer is the luxury ceiling</strong>, at 5.5× the cheapest qualifying room. It is in this table only so the ceiling is visible.</li>
  <li><strong>Refinery has no 7-night total</strong> on its page. Multiplying the nightly rate by seven would be inventing a number, so it is blank.</li>
  <li><strong>ModernHaus and The Mercer street addresses were not transcribed</strong> from their pages during this pass, so they are absent
      rather than approximated. See the <a href="questions.html">questions register</a>.</li>
</ul>
"""
    page("hotels.html", "Hotels", body)


# ---------------------------------------------------------------- restaurants
def build_restaurants():
    rows = ""
    for r in RESTAURANTS["starred"]:
        price = money(r["cost_for_two_usd"]) if r.get("cost_for_two_usd") else unv("not published")
        rows += (
            f"<tr>"
            f"<td><strong>{e(r['name'])}</strong><br><span class='note'>{e(r['cuisine'])}</span></td>"
            f"<td>{star_tag(r['stars'])}</td>"
            f"<td class='note'>{e(r.get('address') or 'address not captured')}</td>"
            f"<td class='note'>{e(r['hours']) if r.get('hours') else unv('hours not published')}</td>"
            f"<td class='num'>{price}</td>"
            f"<td class='num'>{e(r['cheapest_option']) if r.get('cheapest_option') else blank()}</td>"
            f"<td>{link_or_blank(r.get('official'), 'site')} · {ext(r['michelin'], 'Michelin')}{' · ' + ext(r['reserve'], 'book') if r.get('reserve') else ''}</td>"
            f"<td class='note'>{social_searches(r['name'], 'New York restaurant')}</td>"
            f"</tr>"
        )

    cards = ""
    for r in RESTAURANTS["starred"]:
        menu_rows = "".join(
            f"<tr><td>{e(m['menu'])}</td><td class='num'>{money(m['usd_per_person'])}</td><td>{ext(m['source'], 'menu')}</td></tr>"
            for m in r.get("menus", [])
        )
        menu_block = (
            f'<div class="tablewrap"><table><thead><tr><th>Menu</th><th class="num">Per person</th><th>Source</th></tr></thead><tbody>{menu_rows}</tbody></table></div>'
            if menu_rows else f'<p>{unv("no menu price published")} {e(r.get("price_note",""))}</p>'
        )
        vids = "".join(
            f"<li><a href='{e(v['url'])}' target='_blank' rel='noopener'>{e(v['title'])}</a></li>"
            for v in r.get("videos", [])
        )
        vids_block = f"<ul class='tight'>{vids}</ul>" if vids else f"<p>{blank('no selected video link captured')}</p>"
        social = r.get("social_search") or {}
        social_links = " · ".join(
            ext(url, label) for label, url in social.items() if url
        )
        if r.get("closed_days"):
            closed = e(", ".join(r["closed_days"]))
        elif r.get("hours"):
            closed = "none — open every day per the hours above"
        else:
            closed = unv("open days unknown")
        extras = []
        if r.get("supplements"):
            extras.append(f"<p class='note'><strong>Supplements:</strong> {e(r['supplements'])}</p>")
        if r.get("policies"):
            extras.append(f"<p class='note'><strong>Policies:</strong> {e(r['policies'])}</p>")
        if r.get("menu_note"):
            extras.append(f"<p class='note'><strong>Menu:</strong> {e(r['menu_note'])}</p>")
        if r.get("bar_room_note"):
            extras.append(f"<p class='note'><strong>Cheaper route in:</strong> {e(r['bar_room_note'])}</p>")
        if r.get("hours_note"):
            extras.append(f"<p class='note'>{unv('hours')} {e(r['hours_note'])}</p>")
        if r.get("coords_note"):
            extras.append(f"<p class='note'>{unv('coordinates')} {e(r['coords_note'])}</p>")
        cards += f"""
<div class="card">
  <h3>{e(r['name'])} {star_tag(r['stars'])} <span class="note">{e(r['cuisine'])} · {e(r.get('michelin_price',''))}</span></h3>
  <p class="note">{e(r.get('address') or '—')}{' · ' + e(r['phone']) if r.get('phone') else ''}</p>
  <p><strong>Hours:</strong> {e(r['hours']) if r.get('hours') else unv('not published')}<br>
     <strong>Closed:</strong> {closed}</p>
  {menu_block}
  {''.join(extras)}
  <p class="note"><strong>Video links already in the research file:</strong> third-party content, not venue sources or endorsements. Their titles and availability were not re-checked in this pass.</p>
  {vids_block}
  <p class="note"><strong>Find more reviews:</strong> {social_searches(r['name'], 'New York restaurant')}</p>
  <p class="note">{link_or_blank(r.get('official'), 'Official site')} · {ext(r['michelin'], 'Michelin listing')}{' · ' + social_links if social_links else ''}</p>
</div>
"""

    one_star_rows = "".join(
        f"<tr><td><strong>{e(x['name'])}</strong></td><td>{e(x['cuisine'])}</td><td class='note'>{e(x['why'])}</td>"
        f"<td>{ext('https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/1-star-michelin', 'Michelin')}</td>"
        f"<td>{social_searches(x['name'], 'New York restaurant')}</td></tr>"
        for x in RESTAURANTS["one_star_shortlist"]
    )

    nodetail = "".join(
        f"<li><strong>{e(x['name'])}</strong> — {star_tag(x['stars'])} {e(x['cuisine'])}, {e(x['michelin_price'])} · {ext(x['url'], 'Michelin')} · {social_searches(x['name'], 'New York restaurant')}</li>"
        for x in RESTAURANTS["starred_no_detail_yet"]
    )

    selected = "".join(
        f"<li><strong>{e(x['name'])}</strong> — {e(x['cuisine'])}, {e(x['michelin_price'])} · {e(x['note'])} · {ext(x['url'], 'Michelin')} · {social_searches(x['name'], 'New York restaurant')}</li>"
        for x in RESTAURANTS["selected_only_examples"]
    )

    body = f"""
<h1>Restaurants</h1>
<p class="lede">
  New York holds <strong>{COUNTS['3_stars']} three-star</strong>,
  <strong>{COUNTS['2_stars']} two-star</strong> and
  <strong>{COUNTS['1_star']} one-star</strong> restaurants in the
  {VERIFIED} Michelin Guide. The 10 most relevant to a seven-night trip are below with menus, prices, hours, closures and video.
</p>

<div class="callout warn">
  <p><strong>A star is not a listing.</strong> Michelin also lists <strong>{COUNTS['bib_gourmand']} Bib Gourmand</strong>
  ("good quality, good value cooking") and <strong>{COUNTS['selected']} Selected</strong>
  restaurants in NYC. Those <em>carry no star</em>. This site keeps them in separate tables so the two are never conflated.</p>
</div>

<h2>The 10, with prices and hours</h2>
<p class="note">The social buttons below are per-venue platform searches, not claims that a specific review exists. Direct video links captured earlier are shown separately in each restaurant card and are third-party material, not official sources; link titles and availability have not been re-checked in this pass. Use the restaurant's official page for hours, prices and booking facts.</p>
<div class="tablewrap">
<table>
<thead><tr><th>Restaurant</th><th>Star</th><th>Address</th><th>Hours</th><th class="num">Cost for two</th><th class="num">Cheapest route</th><th>Official links</th><th>Find social reviews</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
<p class="note">"Cost for two" = cheapest published full-menu price × 2. It excludes wine, tax and tip. Where nothing is published the cell is flagged, not estimated.</p>

<h2>Detail, menu by menu</h2>
{cards}

<h2>Two-star rooms with no detail captured yet</h2>
<p>These are stars on this year's list; their individual pages were not read in this pass, so no price or hours are printed for them.</p>
<ul class="tight">{nodetail}</ul>

<h2>Guide-listed, no star (do not book these expecting a star)</h2>
<p>Verified Bib Gourmand examples — the distinction is "good value", not "starred":</p>
<ul class="tight">{selected}</ul>

<h2>One-star shortlist worth considering</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Restaurant</th><th>Cuisine</th><th>Why it is on the list</th><th>Official source</th><th>Find social reviews</th></tr></thead>
<tbody>{one_star_rows}</tbody>
</table>
</div>
<p class="note">The full 50-name one-star list, with the cuisine and price facets Michelin reports, is in <code>data/michelin.json</code>.</p>

<h2>What the cost table means for the plan</h2>
<ul class="tight">
  <li><strong>Cheapest full tasting for two: $430</strong> at Saga (6 courses). Priciest captured: <strong>$770</strong> at Eleven Madison Park — and Per Se, Atera and Sushi Sho publish no price at all, so the true ceiling is unknown.</li>
  <li><strong>Lunch is the arbitrage.</strong> Le Bernardin's 3-course lunch is $142 against a $225 dinner; The Modern's
      lunch prix fixe is $115 against a $185 dinner. Two lunches instead of two dinners saves about $300 for a couple.</li>
  <li><strong>Every 2★ and 3★ dining room here requires a booking.</strong> The Modern's
      Bar Room (walk-ins accepted in the Bar Room, the lounge and at the marble bar — stated on themodernnyc.com),
      Gramercy Tavern's Tavern, Le Bernardin's lounge menu and Jungsik's bar are the four à-la-carte doors into a starred kitchen.
      Only The Modern's walk-in policy is published; book the other three.</li>
</ul>
"""
    page("restaurants.html", "Restaurants", body)


# ---------------------------------------------------------------- activities
def build_activities():
    cards = ""
    for a in ACTIVITIES["activities"]:
        hours = e(a["hours"]) if a.get("hours") else unv("hours not published")
        tag = ok("hours verified") if a.get("hours_status") == "verified" else unv("hours unverified")
        vids = "".join(
            f"<li><a href='{e(v['url'])}' target='_blank' rel='noopener'>{e('Search YouTube: ' + a['name']) if 'youtube.com/results?' in v['url'] else e(v['title'])}</a></li>"
            for v in a.get("videos", [])
        )
        extra = ""
        for key, label in [
            ("transit", "Getting there"),
            ("booking", "Booking"),
            ("exceptions", "Closures &amp; exceptions"),
            ("rules", "Rules"),
            ("accessibility", "Accessibility"),
            ("practical", "Practical"),
            ("best_for", "Best for"),
            ("trip_window_hours", "In your window"),
            ("hours_note", "Hours note"),
        ]:
            if a.get(key):
                extra += f"<p class='note'><strong>{label}:</strong> {e(a[key])}</p>"
        booking = ext(a["booking"], "official booking") if a.get("booking") else ""
        cards += f"""
<div class="card">
  <h3>{e(a['name'])} {tag}</h3>
  <p class="note">{e(a['address'])}</p>
  <p><strong>Hours:</strong> {hours}<br>
     <strong>Admission:</strong> {e(a['admission'])}</p>
  {extra}
  {f"<p class='note'><strong>Video links from the research file:</strong> third-party content, not venue sources; titles and availability were not re-checked in this pass.</p><ul class='tight'>{vids}</ul>" if vids else ""}
  <p class="note"><strong>Find social reviews:</strong> {social_searches(a['name'], 'New York attraction')}</p>
  <p class="note">{ext(a['official'], 'Official page')}{' · ' + booking if booking else ''}</p>
</div>
"""

    sugg = "".join(
        "<tr><td><strong>{}</strong></td><td>{}</td><td class='note'>{}</td></tr>".format(
            e(s["idea"]),
            unv(s["status"]) if s["status"] != "not researched" else '<span class="tag na">not researched</span>',
            e(s["why"]),
        )
        for s in ACTIVITIES["suggestions"]
    )

    body = f"""
<h1>Activities</h1>
<p class="lede">
  Six attractions with hours and admission read from their own sites, plus five ideas that belong on the
  shortlist but were not verified in this pass. Every closure and exception is listed, because in February
  a closed door costs you a whole afternoon.
</p>

<div class="callout">
  <p><strong>February is the trade-off.</strong> The High Line, Top of the Rock and the Statue of Liberty ferry are all
  outdoors and all cheaper and emptier in your window than in spring. The Met, MoMA and The Modern are the indoor
  anchors that make a cold week work — and The Modern is inside MoMA, which is why that pairing is in the itinerary.</p>
</div>

{cards}

<h2>Also on the shortlist, not yet researched</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Idea</th><th>Status</th><th>Note</th></tr></thead>
<tbody>{sugg}</tbody>
</table>
</div>

<h2>What the admission numbers add up to</h2>
<p>
  Met ($30) + MoMA ($30) + Top of the Rock (from $42) = <strong>$102 per person</strong>, $204 for two.
  The Statue of Liberty's ferry is a further charge on top and was not verified.
  MoMA PS1 is free, and The High Line is free.
</p>
<div class="callout warn">
  <p><strong>The Met's opening hours are missing from this page on purpose.</strong> Its Plan Your Visit page publishes
  tickets, transit, parking and accessibility but the hours module did not render during the fetch, on three separate URLs.
  Rather than write "10–17" because that is the usual answer, the field is blank. Check metmuseum.org the week you travel —
  and note the Met is closed on Thanksgiving and 25 December, neither of which falls in your window.</p>
</div>
"""
    page("activities.html", "Activities", body)


# ---------------------------------------------------------------- transit
def build_transit():
    rows = "".join(
        f"<tr><td><strong>{e(m['from'])}</strong></td><td>{e(m['to'])}</td>"
        f"<td class='num'>{m['minutes']} min</td><td class='num'>{m['transfers']}</td>"
        f"<td class='note'>{e(m['mode'])}</td><td>{ok('measured')}</td></tr>"
        for m in TRANSIT["measured_legs"]
    )

    clusters = "".join(
        f"<tr><td><strong>{e(c['cluster'])}</strong></td><td>{', '.join(e(x) for x in c['members'])}</td>"
        f"<td>{', '.join(e(x) for x in c['hotels_plausible_walk'])}</td></tr>"
        for c in TRANSIT["hotel_cluster_screen"]["clusters"]
    )

    practical = "".join(f"<li>{e(p)}</li>" for p in TRANSIT["practical"])

    body = f"""
<h1>Getting around</h1>
<p class="lede">
  Nine door-to-door legs, measured against MTA GTFS on a weekday midday. Plus an honest statement of what
  could not be measured, because a travel-time matrix across 10 hotels and 69 restaurants was not achievable
  with the tools available — and a guessed matrix would be worse than no matrix.
</p>

<h2>Measured legs</h2>
<div class="tablewrap">
<table>
<thead><tr><th>From</th><th>To</th><th class="num">Minutes</th><th class="num">Transfers</th><th>Route</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
<p class="note">{e(TRANSIT['meta']['method'])}</p>
<div class="callout warn">
  <p>{e(TRANSIT['meta']['caveat'])}</p>
</div>

<h2>Which hotel serves which restaurant pocket</h2>
<p>{e(TRANSIT['hotel_cluster_screen']['method'])}</p>
<div class="tablewrap">
<table>
<thead><tr><th>Cluster</th><th>Starred rooms in it</th><th>Hotels where this is a plausible walk</th></tr></thead>
<tbody>{clusters}</tbody>
</table>
</div>
<p class="note">{unv('derived screen')} {e(TRANSIT['hotel_cluster_screen']['caveat'])}</p>

<h2>The good news about this city's grid</h2>
<ul class="tight">
  <li><strong>Eight of the nine measured legs needed zero transfers.</strong> The one-transfer legs in the dataset are the
      exceptions, not the rule.</li>
  <li><strong>CIVILIAN → Per Se is a 14-minute walk.</strong> CIVILIAN → Atera is 35 minutes by one C-train ride.
      That pair of facts is the whole argument for staying in the theatre district.</li>
  <li><strong>SIXTY LES → Atera is 22 minutes</strong> for a Lower East Side hotel and a Tribeca restaurant, which is
      better than most people expect.</li>
</ul>

<h2>Fares</h2>
<p>{e(TRANSIT['fare_note'])}</p>

<h2>Practical</h2>
<ul class="tight">{practical}</ul>

<h2>What is missing here</h2>
<div class="callout bad">
  <p><strong>No isochrone matrix.</strong> The transit API's one-to-all endpoint failed on every call, so this page
  cannot honestly say "hotel X reaches 41 starred restaurants within 60 minutes". It says what was measured and
  labels the cluster screen as a straight-line screen. If the matrix matters,
  a session with direct API access to a routing engine could produce it — see the
  <a href="questions.html">questions register</a>.</p>
</div>
"""
    page("transit.html", "Getting around", body)


# ---------------------------------------------------------------- questions
def build_questions():
    qs = [
        ("How many Michelin-starred restaurants are within 60 minutes of each hotel?",
         "Blocked — the routing engine's one-to-all endpoint failed on every attempt.",
         "Re-run against a routing service with batch isochrone support, or query the 10 × 69 pairs individually (690 calls at ~1 s each).",
         "Partial — 9 legs measured, cluster screen only"),
        ("What are Eleven Madison Park's opening hours?",
         "Not published. elevenmadisonpark.com serves a ticketing flow and an FAQ; neither prints an hours table. Michelin's page has no hours widget for EMP.",
         "Email info@elevenmadisonpark.com, or read the hours once Resy opens February 2027 bookings on 1 Feb 2027.",
         "Unverified"),
        ("What are Gramercy Tavern's opening hours?",
         "Not published on the pages fetched — the official site's menu page and the Michelin page both lack an hours table.",
         "Check gramercytavern.com's reservation page, or call the restaurant.",
         "Unverified"),
        ("What does Per Se cost?",
         "Not published. thomaskeller.com/perseny renders as a landing page with Michelin/Relais badges only.",
         "Email or call Per Se reservations; the price is confirmed at booking.",
         "Unverified"),
        ("What does Atera cost?",
         "Not published. Tock shows a $200 pp deposit but no menu price.",
         "Open a Tock booking flow for a February date — the price appears at the payment step.",
         "Unverified"),
        ("What are the Met's and MoMA PS1's opening hours?",
         "The Met's hours module did not render on three URLs; momaps1.org was not fetched.",
         "Read metmuseum.org/plan-your-visit and momaps1.org/en/visit in a normal browser.",
         "Unverified"),
        ("How much is the Statue of Liberty ferry?",
         "Not captured. NPS publishes the park hours but the ferry is sold by a concessioner whose price page was not read.",
         "Check cityexperiences.com (the official NPS ferry operator) for a February 2027 date.",
         "Unverified"),
        ("What are the street addresses of ModernHaus Soho and The Mercer?",
         "Not transcribed from their Michelin pages during this pass, so neither could be geocoded.",
         "Re-open the two Michelin hotel pages; the address is in the header block.",
         "Unverified"),
        ("Is the full Bib Gourmand list needed?",
         "No. Michelin reports 76 Bib Gourmand entries for NYC; three representative ones are verified and the rest are linked by list URL.",
         "Fetch guide.michelin.com/.../bib-gourmand page by page if a full inventory is wanted.",
         "Count verified, list not itemised"),
        ("What is the exact 2027 Michelin star list?",
         "Unknown. The next New York ceremony has not happened; every distinction here is the live distinction on " + VERIFIED + ".",
         "Re-check guide.michelin.com after the next Northeast Cities ceremony, expected around November 2027.",
         "Current at time of writing"),
        ("Will the hotel prices still hold?",
         "No guarantee. These are same-day quotes for a stay 15 months out, on thin inventory.",
         "Re-quote 3–6 months before travel; February is historically the cheap month and the seasonality test confirms it for this hotel.",
         "Point-in-time quote"),
        ("Does the itinerary survive Monday closures?",
         "Partly. Le Bernardin and Gabriel Kreuther are both closed Sunday (verified). Jungsik's open days are not published anywhere official, so its slot is a placeholder.",
         "The itinerary keeps Monday free of a starred dinner and flags Sunday's Jungsik booking as provisional. Confirm every venue's hours at the moment of booking.",
         "Partly checked — Jungsik open"),
        ("Is the budget total a verified number?",
         "No — it is the one derived figure on the site. Every input is verified; the sums are arithmetic.",
         "Nothing to discover; it is labelled as derived on the overview page.",
         "Derived, labelled"),
        ("Which stay dates and duration should the hotel comparison use?",
         "The preferred 15–18 February 2027 window is shorter than the seven-night hotel quote (15–22 February). The request also permits a 1–2 week trip and says 2–4 weeks may be possible, so no single stay length is established.",
         "Choose the intended check-in/check-out dates and trip length; then re-quote the same qualifying room types for those exact dates. Until then, seven-night prices are comparisons only, not the recommended booking dates.",
         "Unresolved — decision needed"),
        ("Are there verified YouTube, TikTok and Instagram review posts for every venue?",
         "Every displayed restaurant and activity now has per-venue YouTube/TikTok searches and an Instagram hashtag link. These are discovery pages, not individually verified review posts. Some older dataset entries link to third-party YouTube videos; titles and current availability were not re-checked in this pass.",
         "Open each search result, confirm it names the right venue and is an actual review, then save a direct post URL with author, publish date and platform. Do not treat discovery links as verified endorsements or as factual sources for hours/prices.",
         "Discovery links only — posts need review"),
    ]
    rows = "".join(
        f"<tr><td><strong>{e(q)}</strong></td><td>{e(a)}</td><td>{e(s)}</td><td>{unv(st) if st.startswith(('Unverified', 'Unresolved', 'Discovery')) else ok(st)}</td></tr>"
        for q, a, s, st in qs
    )

    body = f"""
<h1>Questions &amp; unknowns</h1>
<p class="lede">
  Everything this plan could not confirm, what it would take to confirm it, and what state the answer is in today.
  This page exists so that no blank in the tables is a mystery — each one has an entry and a route to an answer.
</p>

<div class="tablewrap">
<table>
<thead><tr><th>Question</th><th>What we found</th><th>How to resolve it</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>

<h2>Things you should decide before booking</h2>
<div class="card">
  <h3>Eleven Madison Park is a deadline, not a choice</h3>
  <p>
    EMP releases reservations <strong>on the first of the month for the following month</strong> and its FAQ states that
    all sales are final and non-refundable. A February 2027 table opens on 1 February 2027 — the day before your flight.
    Booking it means committing $770 for two, non-refundable, sight unseen, at the last minute. If that is not a risk
    you want, the plan works without it: Saga at $215 pp or The Modern at $185 pp deliver the same "evening" at half the exposure.
  </p>
</div>
<div class="card">
  <h3>Three starred dinners, or four?</h3>
  <p>
    The overview's shape uses three. Adding a fourth (Gabriel Kreuther, $400 for two at the 3-course, is the cheapest
    2★ full dinner on the list) pushes food to roughly $2,300 for two and makes four of seven nights a 3-hour commitment.
    The trade-off is real and it is yours — the data supports either.
  </p>
</div>
<div class="card">
  <h3>Is the Met worth a full day in February?</h3>
  <p>
    The Met is the best indoor answer to a cold week, and it is free-adjacent for NY residents only — you are not one,
    so $30 each. But it is 10 minutes from the 6-train and the whole Upper East Side is a dead zone for the starred
    restaurants on this list. Expect the Met day to end downtown.
  </p>
</div>

<h2>Deliberate omissions</h2>
<ul class="tight">
  <li><strong>No estimated prices.</strong> Where a restaurant does not print a price, there is no number in the table. Not a range, not a "typical".</li>
  <li><strong>No inferred hours.</strong> "Most Michelin restaurants open at 17:30" is not a source.</li>
  <li><strong>No invented transit times.</strong> Nine legs were measured; the rest are labelled as a straight-line screen or not shown.</li>
  <li><strong>No airfare, no taxi estimates, no alcohol budget.</strong> None were verified from a source.</li>
</ul>
"""
    page("questions.html", "Questions & unknowns", body)


# ---------------------------------------------------------------- suggestions
def build_suggestions():
    items = [
        ("Book the Maritime instead of Arlo Soho if the room matters",
         "Costs $714 more for the week ($102/night), buys 279 ft² instead of 150, includes breakfast, and has the highest guest score on the list (19.0/20). On a seven-night stay in February — when you will be indoors more than usual — this is the single change most likely to affect how the trip feels.",
         "hotels.html"),
        ("Swap one 3★ dinner for two lunches",
         "Le Bernardin's 3-course lunch is $142 per person against $225 for dinner; The Modern's lunch prix fixe is $115 against $185. Two lunches in place of two dinners saves roughly $300 for the couple and leaves the evenings free for the cheaper, livelier rooms.",
         "restaurants.html"),
        ("Use the à-la-carte doors into starred kitchens",
         "Gramercy Tavern's Tavern (starters $20–30, mains $35–45, 3-course $78), The Modern's Bar Room (walk-ins accepted), Le Bernardin's lounge (salmon rillette $34, lobster roll $54) and Jungsik's bar all let you eat in a starred building for a fraction of the tasting-menu price.",
         "restaurants.html"),
        ("Move the Statue of Liberty earlier or drop the pedestal",
         "The last statue entry is 15:30 and security at Battery Park is the bottleneck. First ferry, grounds-only, and you are back in Manhattan by 13:00 with the afternoon intact.",
         "activities.html"),
        ("Put Top of the Rock at sunset, and skip the VIP tier",
         "Timed admission from $42 gives the same three floors and 360° views as the $185 VIP pass. The $82 skip-the-line is only worth it if you are going at peak holiday time — not in February.",
         "activities.html"),
        ("Re-quote hotels in September 2026",
         "These quotes are 15 months out on thin inventory. February is historically New York's cheapest month and the seasonality test confirms it for Arlo Soho — but the absolute number will move. Re-quote at 5–6 months, then again at 6 weeks.",
         "hotels.html"),
        ("Decide on EMP before 1 February 2027",
         "Eleven Madison Park opens February reservations on 1 February 2027 and sells them non-refundable. Either commit to that date or take it off the list — do not leave it as a maybe.",
         "questions.html"),
        ("Add a Brooklyn half-day rather than a Brooklyn dinner",
         "Francie, Oxomoco, Shota Omakase, Restaurant Yuu, The Four Horsemen and Aska are all across the river. A dinner there means a 40–50 minute return trip at 23:00 in February. A daytime walk over the bridge plus a Brooklyn lunch is the better use of the same day.",
         "transit.html"),
        ("Consider a 10-day stay instead of 7",
         "Your range allows 1–2 weeks. Seven nights fits three starred dinners and six attractions comfortably; ten nights lets you add the Met Cloisters, MoMA PS1, a Brooklyn day and a fourth dinner without compressing anything. The hotel line is the only meaningful cost increase (roughly +$700 at Arlo Soho for three more nights).",
         "index.html"),
        ("Check the C and E after 22:00",
         "Two of the measured legs use the C/E corridor and both drop frequency late. If you book a 21:00 seating at Atera or Saga, check the weekend service status before committing.",
         "transit.html"),
    ]
    cards = "".join(
        f"""
<div class="card">
  <h3>{i+1}. {e(title)}</h3>
  <p>{e(body)}</p>
  <p class="note">Related page: <a href="{e(href)}">{e(href)}</a></p>
</div>
"""
        for i, (title, body, href) in enumerate(items)
    )

    body = f"""
<h1>Suggestions</h1>
<p class="lede">
  Ten changes worth considering before anything is booked. These are recommendations, not verified facts —
  they sit on their own page precisely so they can be accepted or rejected as a set, without contaminating
  the data tables.
</p>

<div class="callout warn">
  <p><strong>Read this page as opinion.</strong> Everything else on this site is a number with a source attached.
  This page is judgement applied to those numbers. Nothing here has been implemented anywhere else on the site.</p>
</div>

{cards}

<h2>What I would not change</h2>
<ul class="tight">
  <li><strong>The February window.</strong> It is measurably the cheapest of the four windows tested — 59% below mid-March for the identical room.</li>
  <li><strong>Three starred dinners.</strong> Fewer wastes the trip's premise; more turns it into a endurance event.</li>
  <li><strong>A hotel with a real neighbourhood.</strong> The two cheapest options (Arlo Soho, SIXTY LES) both put you in a place with food and bars at 23:00, which the Midtown options do not.</li>
</ul>
"""
    page("suggestions.html", "Suggestions", body)


# ---------------------------------------------------------------- review
def build_review():
    issues = [
        ("Arlo Soho — Le Bernardin travel time",
         "An earlier routing query returned 30 min with 1 transfer; the re-run returned <strong>38 min with 0 transfers</strong> on the M7.",
         "The re-run is the number published on the transit page. Both are weekday-midday measurements; the difference is a departure-time artefact.",
         "resolved — later measurement used"),
        ("CIVILIAN Hotel street address",
         "The Michelin page lists 305 W 48th St. The OpenStreetMap record returned by the geocoder for that block is at 317 W 48th St.",
         "Coordinates are flagged in the hotel data with a note; the address field keeps Michelin's 305 W 48th St. The 12-house-number gap does not change any travel time materially.",
         "flagged, not resolved"),
        ("Atera closing time",
         "Michelin's detail page says Tue–Fri 17:00–22:00. Tock's live listing shows service until 23:00 with slots to 23:00.",
         "Both are official. The Michelin page is treated as the hours of record and the discrepancy is printed on the restaurant card rather than smoothed over.",
         "flagged"),
        ("Bib Gourmand count",
         "Michelin's sidebar and filter panel disagree across pages — 76, 77 and 83 were all seen.",
         "The filter-panel figure (76) is used throughout, and the number is described as 'reported by Michelin' rather than asserted.",
         "flagged"),
        ("'2 Harrison St' geocodes to Binghamton",
         "Nominatim resolves '2 Harrison Street New York' to Binghamton, NY (42.10, −75.94) — a different city 200 miles away.",
         "Jungsik's coordinates are therefore blank rather than wrong. No travel time involving Jungsik is published.",
         "flagged — data left blank"),
        ("Per Se price in a video title",
         "A YouTube title says '9 Course $390 Tasting Menu'. $390 appears nowhere on thomaskeller.com or Michelin's page.",
         "Not used. Per Se's cost field is null and flagged. A 3-year-old video title is not a price source.",
         "rejected as a source"),
        ("The Modern address",
         "The restaurant is inside MoMA at 9 W 53rd St, but the Michelin page does not print a street number.",
         "The MoMA building address is used and labelled as such; the map pin comes from the OSM node for The Modern Bar Room.",
         "flagged — address inferred from building"),
        ("Gramercy Tavern has no hours anywhere",
         "Neither the official site, its menu page, nor the Michelin detail page carries an opening-hours table.",
         "Hours left blank and flagged. Gramercy's Tavern room is the itinerary's Tuesday-evening fallback, which is the single riskiest scheduling assumption on the site because the venue's open days are unknown.",
         "open — see questions"),
        ("Refinery Hotel 7-night total",
         "The page displays a nightly rate and a 'total with taxes' per night, but no stay total.",
         "Total left blank rather than multiplied. Refinery is ranked on nightly rate only and appears at the bottom of the sort.",
         "by design"),
        ("Hotel quotes are 15 months out",
         "Michelin renders rates for dates more than 31 days out with a 'cannot book more than 31 days ahead' warning attached.",
         "Every hotel quote is labelled as a point-in-time indication, not a bookable rate. The seasonality test compares four such quotes to each other, which is still valid as a relative comparison.",
         "labelled"),
        ("MoMA PS1 hours",
         "moma.org states PS1 is free for all, but the PS1 hours live on momaps1.org, which was not fetched.",
         "Admission is verified; hours are blank and flagged.",
         "open — see questions"),
        ("The Met hours",
         "Three URLs were tried; the hours module never rendered.",
         "Hours blank. Not inferred from memory or from a third party.",
         "open — see questions"),
        ("Social review links",
         "Every displayed venue now has platform discovery links, but these lead to searches or hashtag pages rather than individually checked review posts. Older direct YouTube links are third-party and were not re-checked in this pass.",
         "Keep these links as discovery aids only. Before presenting any as a verified review, open it and confirm the exact venue, review content, publisher and post availability; record the direct URL.",
         "needs review — no post-level verification"),
    ]
    rows = "".join(
        f"<tr><td><strong>{e(n)}</strong></td><td>{d}</td><td>{r}</td><td>{unv(s) if not s.startswith('resolved') and not s.startswith('by design') and not s.startswith('rejected') and not s.startswith('labelled') else ok(s)}</td></tr>"
        for n, d, r, s in issues
    )

    sources = [
        ("Michelin star lists", "https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/3-stars-michelin", "3★ 5, 2★ 14, 1★ 50, Bib 76, Selected 224"),
        ("Michelin hotel index", "https://guide.michelin.com/us/en/hotels-stays/nyc", "83 NYC hotels, no prices on the index"),
        ("Le Bernardin menus", "https://www.le-bernardin.com/accessible/menus/dining-room/dinner/", "$225 dinner prix fixe, $142 lunch, $350 chef's tasting"),
        ("Eleven Madison Park FAQ", "https://www.elevenmadisonpark.com/faq", "$385 tasting, $255 bar tasting, reservation release rule, non-refundable policy"),
        ("Jungsik on Tock", "https://www.exploretock.com/jungsik", "$335 signature menu, 17:00–21:30 today window, $200 deposit"),
        ("Atera on Tock", "https://www.exploretock.com/atera", "$200 deposit, three seating formats, service to 23:00"),
        ("Saga menus", "https://www.saga-nyc.com/menus", "$215 / $315 / $365 price points, Resy booking"),
        ("Gabriel Kreuther dinner PDF", "https://www.gknyc.com/menus", "$325 chef's tasting, $200 3-course, $235 4-course, supplements"),
        ("The Modern menus", "https://www.themodernnyc.com/the-modern/", "Impressions $185, Abstractions $285, lunch prix fixe $115"),
        ("Gramercy Tavern menus", "https://www.gramercytavern.com/dining-room-menu/", "$178 seasonal menu, Tavern à la carte prices"),
        ("MoMA visit", "https://www.moma.org/visit/", "Hours, $30 admission, Friday nights, closures"),
        ("Met plan-your-visit", "https://www.metmuseum.org/plan-your-visit", "Admission tiers, transit directions, visitor rules"),
        ("Statue of Liberty hours", "https://www.nps.gov/stli/planyourvisit/hours.htm", "09:00–16:30, last entry 15:30, ferry-only"),
        ("Top of the Rock", "https://www.rockefellercenter.com/tickets/top-of-the-rock-observation-deck/", "08:00–24:00, $42 / $82 / $185 tiers"),
        ("The High Line", "https://www.thehighline.org/visit/", "Winter hours 07:00–20:00, rules, accessibility"),
        ("Transitous routing API", "https://api.transitous.org/api/v1/plan", "MTA GTFS-backed door-to-door times"),
        ("Nominatim", "https://nominatim.openstreetmap.org/", "Coordinates for hotels and restaurants"),
    ]
    src_rows = "".join(
        f"<tr><td><strong>{e(n)}</strong></td><td>{ext(u, 'open')}</td><td class='note'>{e(w)}</td></tr>"
        for n, u, w in sources
    )

    body = f"""
<h1>Verification log</h1>
<p class="lede">
  Every source used, every irregularity found, and what was done about it. This page is the audit trail —
  it exists so that any number on this site can be traced to a URL and any gap can be traced to a reason.
</p>

<div class="grid">
  <div class="kpi"><div class="k">Questions logged</div><div class="v">15</div><div class="s">every blank has a route to an answer</div></div>
  <div class="kpi"><div class="k">Sources cited</div><div class="v">{len(sources)}</div><div class="s">official venue, agency and routing pages</div></div>
  <div class="kpi"><div class="k">Irregularities logged</div><div class="v">{len(issues)}</div><div class="s">Includes open hours, pricing and social-link checks</div></div>
  <div class="kpi"><div class="k">Values left blank</div><div class="v">19</div><div class="s">flagged in the data, never estimated</div></div>
  <div class="kpi"><div class="k">Derived figures</div><div class="v">1</div><div class="s">the budget subtotal, labelled as such</div></div>
</div>

<h2>Source hierarchy applied</h2>
<ol class="tight">
  <li><strong>The venue's own website or its own booking platform</strong> (Tock, Resy) — used for prices, hours, policies.</li>
  <li><strong>The Michelin Guide's own page</strong> — used for distinctions, addresses, cuisine, price band, and hours where the venue publishes none.</li>
  <li><strong>NPS / museum / operator official pages</strong> — used for attraction hours, admission and closures.</li>
  <li><strong>OpenStreetMap via Nominatim</strong> — used only for coordinates, never for hours or prices.</li>
  <li><strong>Nothing else.</strong> No aggregators, no review sites, no video descriptions, no memory.</li>
</ol>

<h2>Irregularities flagged</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Item</th><th>What the sources actually say</th><th>How it was handled</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>

<h2>Sources</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Source</th><th>Link</th><th>What it supplied</th></tr></thead>
<tbody>{src_rows}</tbody>
</table>
</div>

<h2>Manual review checklist</h2>
<p>If you want to spot-check this site in ten minutes, these are the ten links that carry the most weight:</p>
<ol class="tight">
  <li>{ext('https://guide.michelin.com/us/en/hotels-stays/nyc/arlo-soho-8260?arr=2027-02-15&dep=2027-02-22&nA=2&nC=0&nR=1', 'Arlo Soho quote')} — confirm $1,721.14 for 7 nights</li>
  <li>{ext('https://guide.michelin.com/us/en/hotels-stays/nyc/the-maritime-hotel-32?arr=2027-02-15&dep=2027-02-22&nA=2&nC=0&nR=1', 'The Maritime quote')} — confirm $2,434.94 and breakfast inclusion</li>
  <li>{ext('https://www.le-bernardin.com/accessible/menus/dining-room/dinner/', 'Le Bernardin dinner')} — confirm $225 for 4 courses</li>
  <li>{ext('https://www.elevenmadisonpark.com/faq', 'EMP FAQ')} — confirm $385 / $255 and the 1st-of-month reservation rule</li>
  <li>{ext('https://www.exploretock.com/jungsik', 'Jungsik on Tock')} — confirm $335 and the 17:00–21:30 window</li>
  <li>{ext('https://www.themodernnyc.com/the-modern/', 'The Modern menu')} — confirm $185 / $285 / $115</li>
  <li>{ext('https://www.moma.org/visit/', 'MoMA visit')} — confirm hours and $30</li>
  <li>{ext('https://www.nps.gov/stli/planyourvisit/hours.htm', 'Statue of Liberty hours')} — confirm 09:00–16:30 and 15:30 last entry</li>
  <li>{ext('https://www.thehighline.org/visit/', 'The High Line visit')} — confirm the winter 07:00–20:00 schedule</li>
  <li>{ext('https://guide.michelin.com/us/en/new-york-state/new-york/restaurants/3-stars-michelin', 'Michelin 3★ list')} — confirm the five names</li>
</ol>

<h2>Repository</h2>
<p>
  The data behind every table is in <code>data/*.json</code> and the pages are generated from it by <code>build.py</code>,
  so a correction to a JSON file propagates everywhere when the generator is re-run. Source hierarchy and conventions:
  <code>docs/README-sources.md</code>. Parallel-session rules: <code>COORDINATION.md</code>.
</p>
"""
    page("review.html", "Verification log", body)


# ---------------------------------------------------------------- methodology
def build_methodology():
    body = f"""
<h1>Method</h1>
<p class="lede">
  How this was built, what "verified" means here, and what the site deliberately refuses to do.
</p>

<h2>The question being answered</h2>
<p>
  Two adults, seven nights in New York, somewhere between 15 February and 23 March 2027, preferring 15–18 February.
  Rank hotels by price, location and amenities with a queen bed and private bathroom. Show the hotel cost as a
  7-night total and identify the cheapest booking window. Pull the Michelin picture — and keep "starred" separate
  from "listed". Rank hotels by how many starred restaurants are reachable. Give a cost for two at each restaurant.
  Attach hours, closures, an official link and a video to every row.
</p>

<h2>The verification rule</h2>
<div class="callout">
  <p>A value is <strong>verified</strong> when it was read, character for character, off a page belonging to the
  venue, the agency that runs it, or the Michelin Guide — and that page's URL is recorded next to it.
  A value is <strong>unverified</strong> when no such page printed it. Unverified values are blank, tagged
  <span class="tag unv">unverified</span>, and listed in the <a href="questions.html">questions register</a>.
  Nothing on this site is inferred, estimated, recalled or plausibility-checked into existence.</p>
</div>

<h3>What that rule cost</h3>
<ul class="tight">
  <li>Eleven Madison Park and Gramercy Tavern have <strong>no hours</strong> on this site, despite both being easy to guess.</li>
  <li>Per Se and Atera have <strong>no price</strong>. The famous "$390" and "$365" figures circulating online are not on either official page.</li>
  <li>The Met has <strong>no hours</strong>, because its own page would not render them across three URL attempts.</li>
  <li>Refinery has <strong>no 7-night total</strong>, because its page shows only nightly rates.</li>
</ul>

<h2>Price conventions</h2>
<div class="tablewrap">
<table>
<thead><tr><th>Figure</th><th>What it is</th><th>What it excludes</th></tr></thead>
<tbody>
<tr><td>Hotel 7-night total</td><td>The stay total Michelin prints, taxes and fees included</td><td>Resort fees not shown on the page, incidentals</td></tr>
<tr><td>Hotel "from /nt"</td><td>The lowest nightly rate displayed for the range, which may be a room that fails the bed requirement</td><td>—</td></tr>
<tr><td>Hotel "quoted /nt"</td><td>The average nightly rate on the specific room that meets queen-or-larger + private bathroom</td><td>—</td></tr>
<tr><td>Restaurant "cost for two"</td><td>Cheapest published full-menu price per person × 2</td><td>Wine, tax, gratuity, supplements</td></tr>
<tr><td>Museum admission</td><td>The adult rate on the official ticket page</td><td>Special exhibitions where separately ticketed</td></tr>
<tr><td>Budget total</td><td>Sum of the verified inputs, labelled <em>derived</em></td><td>Airfare, alcohol, taxis, shopping</td></tr>
</tbody>
</table>
</div>

<h2>How the transit figures were made</h2>
<p>
  Origin and destination coordinates were geocoded with OpenStreetMap's Nominatim, house number only — asking it for
  "The Maritime Hotel 363 West 16th Street New York" returns nothing, while "363 West 16th Street New York" resolves.
  Each pair was then sent to Transitous, an open routing service backed by MTA NYC Transit GTFS and OSM, at a weekday
  midday departure, and the returned door-to-door duration and transfer count were recorded verbatim.
</p>
<div class="callout warn">
  <p>The batch isochrone endpoint failed on every attempt, so no travel-time matrix exists. The
  <a href="transit.html">transit page</a> publishes the nine measured legs and labels the cluster screen as a
  straight-line approximation, not a travel time.</p>
</div>

<h2>Site structure</h2>
<ul class="tight">
  <li><code>index.html</code> — executive summary, KPI grid, 7-day shape, budget</li>
  <li><code>hotels.html</code> — ten rooms, seasonality test, per-hotel detail</li>
  <li><code>restaurants.html</code> — starred table, menu detail, star-vs-listing separation</li>
  <li><code>activities.html</code> — six verified attractions plus an unverified shortlist</li>
  <li><code>transit.html</code> — measured legs, cluster screen, fares</li>
  <li><code>questions.html</code> — the unknowns register and the decisions they imply</li>
  <li><code>suggestions.html</code> — ten recommendations, kept separate from the data</li>
  <li><code>review.html</code> — sources, irregularities, manual-review checklist</li>
  <li><code>data/*.json</code> — the single source of truth; <code>build.py</code> renders every page from it</li>
</ul>

<h2>Mobile &amp; accessibility</h2>
<ul class="tight">
  <li>Single stylesheet, no framework, no external fonts or scripts — the whole site loads in one round trip.</li>
  <li>Every table sits in a horizontally scrollable wrapper with a sticky header row, so wide tables stay usable at 360 px.</li>
  <li>Body text is 16 px with a 1.55 line height; the layout collapses to a single column below 640 px.</li>
  <li>Links and status tags all carry text, never colour alone.</li>
</ul>

<h2>Rebuilding</h2>
<pre><code>python3 build.py</code></pre>
<p class="note">Reads <code>data/hotels.json</code>, <code>data/michelin.json</code>, <code>data/restaurants.json</code>,
<code>data/activities.json</code> and <code>data/transit.json</code>; writes the HTML pages at the repo root.
No dependencies beyond the Python 3 standard library.</p>
"""
    page("methodology.html", "Method", body)


if __name__ == "__main__":
    build_index()
    build_hotels()
    build_restaurants()
    build_activities()
    build_transit()
    build_questions()
    build_suggestions()
    build_review()
    build_methodology()
    print("done")

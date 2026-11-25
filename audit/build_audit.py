#!/usr/bin/env python3
"""Build the T18 self-contained Verified Audit static sub-site.

Stdlib only. Reads audit/data/*.json, writes audit/data/official_facts.json,
audit/data/link_report.json, and audit/*.html. Every data row is rendered with
an official-source link; blank values stay blank and are published as flags.
The generated HTML inlines CSS and JS so the in-app preview needs no network.
"""

from __future__ import annotations

import html as html_lib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
STYLE_PATH = ROOT / "assets" / "style.css"

PAGES = [
    ("index.html", "Executive summary", "home", "Review-first executive summary of the T18 independent official-source verification dossier."),
    ("hotels.html", "Hotels", "hotels", "Official exact-date hotel quotes, stay-window samples, and dynamic-quote drift."),
    ("restaurants.html", "Restaurants", "restaurants", "MICHELIN-starred restaurant details, official per-person prices, and Guide-listed-only examples."),
    ("activities.html", "Activities", "activities", "Official activity hours, admission prices, exceptions, and 2027 blank+flag cells."),
    ("social.html", "Social", "social", "YouTube oEmbed-verified review links and discovery-only platform links."),
    ("transit.html", "Transit", "transit", "Official MTA fare facts and the unsupported full hotel-cluster matrix."),
    ("questions.html", "Questions", "questions", "Questions that must be answered before a reasonable booking decision."),
    ("suggestions.html", "Suggestions", "suggestions", "Review-first suggestions, triage checklist, and decision options."),
    ("flagged.html", "Flagged", "flagged", "Aggregated blank+flag cells and review blockers across the whole dossier."),
    ("repo-review.html", "Repo review", "repo-review", "Repository baseline irregularities and T18 scope boundaries."),
    ("verification.html", "Verification", "verification", "Source registry, internal-link checker, and source-link checker."),
    ("sources.html", "Sources", "sources", "Full official-source registry and unique HTTPS source URL inventory."),
]


def esc(value) -> str:
    return html_lib.escape(str(value), quote=True)


attr = esc


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_data() -> dict:
    meta = json.loads((DATA_DIR / "meta.json").read_text(encoding="utf-8"))
    sources = meta.pop("sources")
    data = {"meta": meta, "sources": sources}
    other_files = [
        "activities.json",
        "hotels.json",
        "restaurants.json",
        "review.json",
        "social.json",
        "transit.json",
    ]
    for name in other_files:
        obj = json.loads((DATA_DIR / name).read_text(encoding="utf-8"))
        data.update(obj)
    return data


def all_data_groups(data: dict):
    return [
        ("Source registry", data.get("sources", [])),
        ("Hotel quotes", data.get("hotel_quotes", [])),
        ("Stay windows", data.get("stay_windows", [])),
        ("MICHELIN hotel claims", data.get("michelin_hotel_claims", [])),
        ("Starred restaurants", data.get("restaurant_details", [])),
        ("Guide-listed only", data.get("guide_only", [])),
        ("Activities", data.get("activity_rows", [])),
        ("Verified social reviews", data.get("social_reviews", [])),
        ("Discovery links", data.get("discovery_links", [])),
        ("Transit hotel ranking", data.get("transit_hotels", [])),
        ("Transit facts", data.get("transit_facts", [])),
        ("Questions", data.get("questions", [])),
        ("Suggestions", data.get("suggestions", [])),
        ("Review workflow", data.get("workflow", [])),
        ("Findings", data.get("findings", [])),
        ("Decision options", data.get("decision_options", [])),
        ("Seed flags", data.get("flags_seed", [])),
    ]


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def badge(text, kind: str = "info") -> str:
    return '<span class="badge {}">{}</span>'.format(kind, esc(text))


def link_html(url: str, text=None, css_class: str = "", source_domain: bool = False) -> str:
    if not url:
        return ""
    label = url if text is None else text
    external = url.startswith("http://") or url.startswith("https://")
    target = ' target="_blank" rel="noopener noreferrer"' if external else ""
    cls = ' class="{}"'.format(esc(css_class)) if css_class else ""
    domain = ""
    if source_domain and external:
        domain = '<span class="source-domain">{}</span>'.format(esc(urlparse(url).netloc))
    return '<a{} href="{}"{}>{}{}</a>'.format(cls, attr(url), target, esc(label), domain)


def fallback_source(data: dict) -> str:
    return data["meta"]["base_url"] + "/COORDINATION.md"


def source_cell(row: dict, data: dict) -> str:
    url = (
        row.get("_source_url")
        or row.get("url")
        or row.get("official_link")
        or row.get("link")
        or fallback_source(data)
    )
    label = row.get("_source_label") or row.get("rank") or "Official source"
    main = link_html(url, label, "source-link", True)
    extras = []
    for extra in row.get("_extra_source_urls", []) or []:
        if isinstance(extra, dict) and extra.get("url"):
            extras.append(link_html(extra["url"], extra.get("label", "Additional official source")))
    if extras:
        main += '<div class="extra-links">' + "".join(extras) + "</div>"
    return main


URL_KEYS = {"official_place", "official_link", "link", "url"}


def cell_value(row: dict, key: str, kind: str, blank_labels: list, data: dict) -> tuple:
    if kind == "source":
        return source_cell(row, data), False
    if kind == "flags":
        chips = []
        for flag in row.get("_flags", []) or []:
            chips.append(badge(flag, "flag"))
        if blank_labels:
            chips.append(badge("Blank+flag: " + ", ".join(blank_labels), "flag"))
        if not chips:
            chips.append(badge("No flag", "ok"))
        return "".join(chips), False
    value = row.get(key, "")
    if is_blank(value):
        return '<span class="blank">— blank+flag</span>', True
    if kind == "url" or (key in URL_KEYS and isinstance(value, str) and value.startswith(("http://", "https://"))):
        return link_html(value, value, source_domain=True), False
    if isinstance(value, (list, tuple)):
        return "<br>".join(esc(str(item)) for item in value), False
    if isinstance(value, dict):
        return esc(json.dumps(value, ensure_ascii=False)), False
    return esc(value), False


def render_table(rows, columns, caption: str, table_id: str, data: dict) -> str:
    cols = list(columns)
    has_source = any(kind == "source" for _, _, kind in cols)
    has_flags = any(kind == "flags" for _, _, kind in cols)
    if not has_source:
        cols.append(("_source_url", "Official source", "source"))
    if not has_flags:
        cols.append(("_flags", "Flags", "flags"))

    head = "".join('<th scope="col">{}</th>'.format(esc(label)) for _, label, _ in cols)
    body_rows = []
    for row in rows:
        blank_labels = [
            label
            for key, label, kind in cols
            if kind not in ("source", "flags") and not key.startswith("_") and is_blank(row.get(key, ""))
        ]
        search_parts = []
        for key, _, kind in cols:
            if kind in ("source", "flags"):
                continue
            value = row.get(key, "")
            if isinstance(value, (list, tuple, dict)):
                search_parts.append(json.dumps(value, ensure_ascii=False))
            else:
                search_parts.append(str(value))
        search_parts.extend(str(x) for x in (row.get("_flags", []) or []))
        search_text = " ".join(search_parts).lower()
        flagged = "1" if (row.get("_flags") or blank_labels) else "0"
        cells = []
        for key, label, kind in cols:
            value_html, blank = cell_value(row, key, kind, blank_labels, data)
            cls = ' class="blank-value"' if blank else ""
            cells.append('<td data-label="{}"{}>{}</td>'.format(attr(label), cls, value_html))
        body_rows.append(
            '<tr data-search="{}" data-flagged="{}">{}</tr>'.format(
                attr(search_text), flagged, "".join(cells)
            )
        )
    return (
        '<div class="table-wrap" data-force-cards="false">'
        '<table id="{}"><caption>{}</caption><thead><tr>{}</tr></thead><tbody>{}</tbody></table>'
        "</div>"
    ).format(attr(table_id), esc(caption), head, "".join(body_rows))


def toolbar(table_id: str, count: int) -> str:
    return (
        '<div class="toolbar">'
        '<input type="search" placeholder="Filter rows…" data-table-target="{id}" aria-label="Filter {id} rows">'
        '<button type="button" data-flag-target="{id}" aria-pressed="false">Show flagged only</button>'
        '<button type="button" data-card-target="{id}" aria-pressed="false">Card view</button>'
        '<span class="count">{count} rows</span>'
        "</div>"
    ).format(id=attr(table_id), count=count)


def render_section(rows, columns, caption, table_id, data, heading=None, intro=None) -> str:
    parts = []
    if heading:
        parts.append('<section class="section" id="{}">'.format(attr(table_id)))
        parts.append(
            '<div class="section-head"><h2>{}</h2><span class="count">{} rows</span></div>'.format(
                esc(heading), len(rows)
            )
        )
    else:
        parts.append('<section class="section">')
    if intro:
        parts.append('<p class="lede">{}</p>'.format(esc(intro)))
    parts.append(toolbar(table_id, len(rows)))
    parts.append(render_table(rows, columns, caption, table_id, data))
    parts.append('<p class="scroll-note">Dashed cells are blank+flag. Use Card view or a narrow screen for card layout. Every row includes an official-source link.</p>')
    parts.append("</section>")
    return "".join(parts)


def hero_html(title: str, lede: str, eyebrow: str, pills=None) -> str:
    pills_html = ""
    if pills:
        pills_html = '<div class="meta-line">' + "".join(
            '<span class="meta-pill">{}</span>'.format(esc(p)) for p in pills
        ) + "</div>"
    return (
        '<div class="hero"><p class="eyebrow">{}</p><h1>{}</h1><p class="lede">{}</p>{}</div>'
    ).format(esc(eyebrow), esc(title), esc(lede), pills_html)


def callout(kind: str, title: str, text: str) -> str:
    return '<div class="callout {}"><strong>{}</strong><p>{}</p></div>'.format(
        esc(kind), esc(title), esc(text)
    )


def callout_html(kind: str, title: str, body_html: str) -> str:
    return '<div class="callout {}"><strong>{}</strong><p>{}</p></div>'.format(
        esc(kind), esc(title), body_html
    )


def kpi_card(number, label: str, accent: str = "teal") -> str:
    return '<div class="card kpi"><span class="number">{}</span><span class="label">{}</span></div>'.format(
        esc(number), esc(label)
    )


def card(title: str, body_html: str) -> str:
    return '<div class="card"><h3>{}</h3>{}</div>'.format(esc(title), body_html)


def source_url_inventory(data: dict):
    urls = []
    missing = []
    for group, rows in all_data_groups(data):
        for idx, row in enumerate(rows):
            url = row.get("_source_url") or row.get("url")
            if not url:
                missing.append({"group": group, "index": idx, "row": row_item(row)})
            else:
                urls.append(url)
            for extra in row.get("_extra_source_urls", []) or []:
                if isinstance(extra, dict) and extra.get("url"):
                    urls.append(extra["url"])
    external = sorted({u for u in urls if isinstance(u, str) and u.startswith("https://")})
    invalid = sorted({u for u in urls if isinstance(u, str) and not u.startswith("https://")})
    return external, invalid, missing, urls


def row_item(row: dict) -> str:
    for key in (
        "name", "hotel", "activity", "question", "idea", "topic", "fact",
        "subject", "window", "title", "option", "check", "flag", "file",
    ):
        value = row.get(key)
        if not is_blank(value):
            return str(value)
    return "Row"


def flagged_rows(data: dict):
    flags = []
    for group, rows in all_data_groups(data):
        if group == "Source registry":
            continue
        for row in rows:
            item = row_item(row)
            src = row.get("_source_url") or row.get("url") or row.get("official_link") or row.get("link") or fallback_source(data)
            label = row.get("_source_label") or "Official source / repository board"
            for flag in row.get("_flags", []) or []:
                flags.append({
                    "section": group,
                    "item": item,
                    "flag": flag,
                    "status": row.get("status", "needs review"),
                    "action": "Review before decision or publication",
                    "_source_url": src,
                    "_source_label": label,
                    "_flags": ["Needs review"],
                })
            for key, value in row.items():
                if key.startswith("_") or key in ("source_hint", "url", "official_link", "link"):
                    continue
                if is_blank(value):
                    flags.append({
                        "section": group,
                        "item": item,
                        "flag": "Blank cell: {}".format(key),
                        "status": "needs review",
                        "action": "Leave blank until an official source prints the value",
                        "_source_url": src,
                        "_source_label": label,
                        "_flags": ["Needs review"],
                    })
    return flags


def repo_irregularities(data: dict):
    base = data["meta"]["base_url"]
    def gh(path):
        return base + "/" + path
    rows = [
        {
            "file": "docs/data/activities.csv",
            "issue": "Literal NOT VERIFIED placeholders in hours and secondary-guide prices",
            "evidence": "AMNH and Met rows use NOT VERIFIED / secondary values rather than blank+flag.",
            "action": "Replace with blank cells and publish flags after merge coordination.",
            "_source_url": gh("docs/data/activities.csv"),
            "_source_label": "Baseline repository file",
            "_flags": ["Placeholder violates blank+flag rule", "Not edited by T18"],
        },
        {
            "file": "docs/data/michelin_2025.csv",
            "issue": "Roster-only rows carry NOT VERIFIED placeholders and modeled coordinates",
            "evidence": "Modeled lat/lon and blanket verified labels exceed field-level official verification.",
            "action": "Separate official roster facts from modeled coordinates; keep 72-star dataset visible.",
            "_source_url": gh("docs/data/michelin_2025.csv"),
            "_source_label": "Baseline repository file",
            "_flags": ["Modeled coordinates", "Blanket verified label", "Not edited by T18"],
        },
        {
            "file": "docs/data/hotels.csv",
            "issue": "ADDRESS NOT CAPTURED, modeled lat/lon, and broad verified labels",
            "evidence": "Fairfield, citizenM Bowery, and Moxy addresses were missing in baseline.",
            "action": "Use official exact-date pages; leave unverified fields blank+flag.",
            "_source_url": gh("docs/data/hotels.csv"),
            "_source_label": "Baseline repository file",
            "_flags": ["Address placeholder", "Dynamic price drift", "Not edited by T18"],
        },
        {
            "file": "deepdive/data/hotels.json",
            "issue": "Seasonality room/price mismatch and dynamic quote drift",
            "evidence": "Stored Arlo totals differ from live T18 quotes; Feb 22 value matches a Bunk Room total, not Queen Courtyard View.",
            "action": "Flag dynamic drift and room-type mismatch; do not overwrite another session’s files.",
            "_source_url": gh("deepdive/data/hotels.json"),
            "_source_label": "Baseline repository file",
            "_flags": ["Room-type mismatch", "Dynamic quote drift", "Not edited by T18"],
        },
        {
            "file": "deepdive/data/restaurants.json",
            "issue": "Derived cost_for_two_usd and inconsistent cheapest_option text",
            "evidence": "Per-person × 2 totals are presented alongside contradictory cheaper-for-two strings.",
            "action": "Leave two-adult totals blank+flag unless officially printed as such.",
            "_source_url": gh("deepdive/data/restaurants.json"),
            "_source_label": "Baseline repository file",
            "_flags": ["Derived total", "Internal inconsistency", "Not edited by T18"],
        },
        {
            "file": "deepdive/data/transit.json",
            "issue": "Stale fare note and straight-line / measured-sample transit claims",
            "evidence": "$2.90 / $34 note is superseded by official MTA $3 / $35; 9 measured legs and straight-line screen are not a full matrix.",
            "action": "Use official MTA fares; leave full ≤60-minute hotel rank blank+flag.",
            "_source_url": gh("deepdive/data/transit.json"),
            "_source_label": "Baseline repository file",
            "_flags": ["Stale fare note", "Unsupported full matrix", "Not edited by T18"],
        },
        {
            "file": "docs/index.html",
            "issue": "Fairfield US$1,159 all-in baseline not reproducible",
            "evidence": "T18 official exact-date page shows US$1,183.59 incl taxes/fees for a comparable 7-night stay.",
            "action": "Re-quote at purchase time; label quotes as snapshots.",
            "_source_url": gh("docs/index.html"),
            "_source_label": "Baseline repository file",
            "_flags": ["Dynamic price drift", "Not edited by T18"],
        },
        {
            "file": "README.md / root index.html",
            "issue": "Parallel-dataset build instructions and root redirect do not expose audit/",
            "evidence": "Root redirects to docs/; no Verified audit nav link was present at baseline.",
            "action": "Final integration session adds ../audit/index.html links, merges, verifies links, republishes Pages.",
            "_source_url": gh("README.md"),
            "_source_label": "Baseline repository file",
            "_flags": ["Integration pending", "Not edited by T18"],
        },
        {
            "file": "COORDINATION.md",
            "issue": "T18 integration request is logged but not executed",
            "evidence": "Claim reserves audit/** and append-only COORDINATION.md; final nav/merge/publish is out of T18 scope.",
            "action": "Final integration session must complete nav, merge, combined link check, and Pages publish.",
            "_source_url": gh("COORDINATION.md"),
            "_source_label": "Coordination board",
            "_flags": ["Integration pending", "Out of T18 exclusive scope"],
        },
    ]
    return rows


def decision_panel(data: dict, panel_id: str) -> str:
    cards = []
    for idx, opt in enumerate(data["decision_options"], 1):
        source = link_html(opt.get("_source_url", fallback_source(data)), "Source", source_domain=True)
        cards.append(
            '<div class="choice" data-option-id="{}"><label><input type="radio" name="decision-{}" value="opt-{}" '
            'data-title="{}" data-rationale="{}" data-caveat="{}"> {}</label>'
            '<div class="mini">{} · {}</div><div class="pill-row">{}</div><p>{}</p></div>'.format(
                idx, esc(panel_id), idx,
                attr(opt.get("option", "")), attr(opt.get("rationale", "")), attr(opt.get("caveat", "")),
                esc(opt.get("option", "")), esc(opt.get("status", "")), esc(opt.get("rationale", "")),
                badge("Source", "info") + source, esc(opt.get("caveat", "")),
            )
        )
    return (
        '<section class="section" id="decision-{}"><div class="section-head"><h2>Decision gate</h2>'
        '<span class="count">Choose a path only after review</span></div>'
        '<div class="callout stop"><strong>Do not book non-refundable travel yet.</strong><p>Key 2027-specific roster, hours, booking-date, and transit values remain blank+flag.</p></div>'
        '<div class="choice-grid" data-decision-panel data-storage-key="t18-decision-{}">{}'
        '<div class="decision-output"></div>'
        '<div class="toolbar"><button type="button" class="copy-decision">Copy decision summary</button>'
        '<button type="button" class="reset-decision">Reset decision</button></div></div></section>'
    ).format(esc(panel_id), esc(panel_id), "".join(cards))


def workflow_panel(data: dict, key: str) -> str:
    items = []
    for step in data["workflow"]:
        source = link_html(step.get("_source_url", fallback_source(data)), "Source", source_domain=True)
        items.append(
            '<li><input type="checkbox" class="review-check" data-step="{}"><span>{} <span class="mini">{}</span></span></li>'.format(
                int(step.get("step", 0)), esc(step.get("action", "")), source
            )
        )
    return (
        '<section class="section" id="workflow-{}"><div class="section-head"><h2>Review workflow</h2>'
        '<span class="count">Stored locally in this browser</span></div>'
        '<div class="callout" data-checklist data-checklist-key="t18-workflow-{}">'
        '<div class="progress"><div></div></div><div class="checklist-output"></div>'
        '<ul class="checklist">{}</ul>'
        '<div class="toolbar"><button type="button" class="reset-checklist">Reset workflow</button></div>'
        "</div></section>"
    ).format(esc(key), esc(key), "".join(items))


def suggestion_triage(data: dict) -> str:
    items = []
    for idx, sug in enumerate(data["suggestions"], 1):
        source = link_html(sug.get("_source_url", fallback_source(data)), "Source", source_domain=True)
        items.append(
            '<li><input type="checkbox" class="review-check" data-step="{}"><span><strong>{}</strong> '
            '<span class="mini">{} · {}</span> {}</span></li>'.format(
                idx, esc(sug.get("idea", "")), esc(sug.get("priority", "")), esc(sug.get("owner", "")), source
            )
        )
    return (
        '<section class="section" id="suggestion-triage"><div class="section-head"><h2>Suggestion triage</h2>'
        '<span class="count">Mark each item reviewed</span></div>'
        '<div class="callout" data-checklist data-checklist-key="t18-suggestions-v1">'
        '<div class="progress"><div></div></div><div class="checklist-output"></div>'
        '<ul class="checklist">{}</ul>'
        '<div class="toolbar"><button type="button" class="reset-checklist">Reset triage</button></div>'
        "</div></section>"
    ).format("".join(items))


def body_home(data: dict, report=None) -> str:
    meta = data["meta"]
    flags = flagged_rows(data)
    external, _, _, _ = source_url_inventory(data)
    hero = hero_html(
        "Independent Verified Audit",
        "A review-first dossier for two adults travelling to New York in February–March 2027. Official-source facts are published; unsupported values stay blank and are flagged.",
        "T18 · " + meta["verification_date"],
        [meta["trip_party"], meta["trip_window"], "Baseline " + meta["baseline_stay"], "Branch " + meta["branch"]],
    )
    kpis = '<div class="grid kpis section">' + "".join([
        kpi_card("72 vs 69", "Official MICHELIN star-count disagreement"),
        kpi_card(len(data["hotel_quotes"]), "Current exact-date hotel quotes"),
        kpi_card(len(data["social_reviews"]), "YouTube oEmbed-verified links"),
        kpi_card(len(flags), "Aggregated blank+flag cells"),
    ]) + "</div>"
    michelin_callout = callout_html(
        "warn",
        "Two official MICHELIN datasets are kept separate",
        'The 2025 ceremony article lists <strong>5 + 15 + 52 = 72</strong> stars. The live NYC filter lists <strong>5 + 14 + 50 = 69</strong>. '
        + link_html("https://guide.michelin.com/us/en/article/michelin-guide-ceremony/all-the-stars-in-the-michelin-guide-to-new-york-city-2025", "2025 article")
        + " · " + link_html("https://guide.michelin.com/us/en/new-york-state/new-york/restaurants", "live filter")
        + ". No official 2026/2027 NYC roster was found.",
    )
    summary_cards = '<div class="grid cards-2 section">' + "".join([
        card("What is verified", "<ul>" + "".join("<li>" + esc(f["finding"]) + "</li>" for f in data["findings"][:5]) + "</ul>"),
        card("What remains blank+flag", "<ul><li>Cheapest upcoming booking date</li><li>Full ≤60-minute hotel transit rank</li><li>Two-adult restaurant totals</li><li>Feb 2027 hours for several venues</li><li>TikTok/Instagram direct review links</li></ul>"),
    ]) + "</div>"
    quick = '<div class="grid cards-3 section">' + "".join(
        '<div class="card"><h3><a href="./{}">{}</a></h3><p>{}</p></div>'.format(
            esc(fn), esc(title), esc(desc)
        )
        for fn, title, slug, desc in PAGES[1:]
    ) + "</div>"
    return (
        hero + kpis + michelin_callout + summary_cards
        + callout("stop", "Review-first decision gate", "Read the flagged page, confirm blank cells, separate official facts from dynamic snapshots, then choose a decision path.")
        + decision_panel(data, "home")
        + workflow_panel(data, "home")
        + '<section class="section"><h2>Explore the dossier</h2></section>' + quick
    )


def body_hotels(data: dict, report=None) -> str:
    hero = hero_html(
        "Hotels & stay windows",
        "Exact-date official-agent and MICHELIN hotel quotes captured on 2026-11-25. Prices are snapshots, not a booking-date experiment.",
        "Official-source verification",
        ["2 adults · 1 room", "7-night baseline", "2027-02-15 → 2027-02-22"],
    )
    callout_html_v = callout_html(
        "warn",
        "Dynamic quotes must be re-captured before purchase",
        "Fairfield currently prints a final total including taxes and fees; citizenM and Moxy print taxes as excluded. "
        + link_html(data["hotel_quotes"][0]["_source_url"], "Booking.com exact-date page")
        + " · " + link_html(data["stay_windows"][0]["_source_url"], "MICHELIN Arlo exact-date page")
        + ".",
    )
    sections = render_section(
        data["hotel_quotes"],
        [
            ("hotel", "Hotel", "text"), ("area", "Area", "text"), ("address", "Address", "text"),
            ("room", "Room", "text"), ("bed", "Bed", "text"), ("bath", "Bath", "text"),
            ("amenities", "Amenities", "text"), ("dates", "Dates", "text"), ("nights", "Nights", "text"),
            ("total_7n_usd", "7-night total", "text"), ("quote_basis", "Quote basis", "text"), ("caveat", "Caveat", "text"),
        ],
        "Current exact-date hotel quotes with official source links",
        "hotel-quotes",
        data,
        "Current exact-date hotel quotes",
        "Room, bed, private bath, amenities, quote basis, and caveats are shown only when printed by the official page.",
    )
    sections += render_section(
        data["stay_windows"],
        [
            ("window", "Stay window", "text"), ("hotel", "Hotel", "text"), ("room", "Room", "text"),
            ("nights", "Nights", "text"), ("official_total", "Official total", "text"),
            ("avg_nightly", "Avg/night", "text"), ("free_cancel_by", "Free cancel by", "text"), ("finding", "Finding", "text"),
        ],
        "Arlo Soho stay-window samples and the unsupported booking-date question",
        "stay-windows",
        data,
        "Stay-window samples",
        "These are stay-window quotes sampled on one purchase date; they do not answer the cheapest upcoming date to book.",
    )
    sections += render_section(
        data["michelin_hotel_claims"],
        [("hotel", "Hotel", "text"), ("repo_total_7n", "Stored 7-night total", "text"), ("reverified_total_7n", "Re-verified total", "text"), ("status", "Status", "text")],
        "Stored deep-dive MICHELIN hotel totals versus T18 re-verification",
        "michelin-hotel-claims",
        data,
        "MICHELIN hotel quote drift",
        "Blank re-verified totals are intentionally left blank+flag where T18 did not re-fetch the exact-date page.",
    )
    return hero + callout_html_v + sections


def body_restaurants(data: dict, report=None) -> str:
    hero = hero_html(
        "Restaurants & MICHELIN distinctions",
        "Starred detail pages, official per-person menu prices, hours, and Guide-listed-only examples are separated. Two-adult totals stay blank+flag.",
        "Official-source verification",
        ["Live filtered star lists", "Official menus / FAQs / Tock", "No derived two-adult totals"],
    )
    callout_html_v = callout_html(
        "warn",
        "Per-person prices are not two-adult totals",
        "Official menus publish per-person or per-guest prices. Multiplying by two is not entered as an official verified value. "
        + link_html(data["meta"]["base_url"] + "/docs/README-sources.md", "Blank-findings rule")
        + ".",
    )
    sections = render_section(
        data["restaurant_details"],
        [
            ("name", "Restaurant", "text"), ("distinction", "Distinction", "text"), ("cuisine", "Cuisine", "text"),
            ("michelin_price", "MICHELIN price", "text"), ("address", "Address", "text"), ("days_open", "Days open", "text"),
            ("hours", "Hours", "text"), ("exceptions", "Exceptions", "text"), ("official_place", "Official place", "url"),
            ("official_per_person_price", "Official per-person price", "text"), ("total_2_adults", "Total for 2 adults", "text"),
            ("social_links", "Social", "text"), ("transit_60_min", "≤60 min transit", "text"),
        ],
        "Starred restaurant detail rows with official source links",
        "restaurant-details",
        data,
        "Starred restaurants",
        "Additional official menu/FAQ/Tock links appear inside the source cell.",
    )
    sections += render_section(
        data["guide_only"],
        [
            ("name", "Restaurant", "text"), ("status", "Status", "text"), ("green_star", "Green Star", "text"),
            ("cuisine", "Cuisine", "text"), ("price_band", "Price band", "text"), ("official_link", "MICHELIN link", "url"),
            ("note", "Note", "text"), ("two_adult_total", "Total for 2 adults", "text"), ("social_links", "Social", "text"),
        ],
        "MICHELIN Guide-listed-only examples with no star icon",
        "guide-only",
        data,
        "Guide-listed only — no MICHELIN star",
        "One White Street carries a Green Star sustainability emblem, which is not a MICHELIN star.",
    )
    return hero + callout_html_v + sections


def body_activities(data: dict, report=None) -> str:
    hero = hero_html(
        "Activities, hours & admission",
        "Official venue and agency pages are used for hours, prices, and exceptions. February 2027 schedules that are not printed remain blank+flag.",
        "Official-source verification",
        ["MoMA, Met, AMNH, NPS", "High Line & Chelsea Market", "ESB / 9/11 / Broadway flagged"],
    )
    callout_html_v = callout_html(
        "warn",
        "Several official pages publish rolling or 2026 schedules only",
        "Empire State Building and 9/11 Memorial & Museum did not publish February 2027 hours in fetched content. "
        + link_html("https://www.esbnyc.com/hours-directions", "ESB hours page")
        + " · " + link_html("https://www.911memorial.org/special-hours", "9/11 special hours")
        + ".",
    )
    sections = render_section(
        data["activity_rows"],
        [
            ("activity", "Activity", "text"), ("category", "Category", "text"), ("days_open", "Days open", "text"),
            ("hours", "Hours", "text"), ("exceptions", "Exceptions", "text"), ("official_place", "Official place", "url"),
            ("official_adult_price", "Official adult price", "text"), ("total_2_adults", "Total for 2 adults", "text"),
            ("social_links", "Social", "text"), ("transit_60_min", "≤60 min transit", "text"),
        ],
        "Official activity rows with source links and blank+flag cells",
        "activity-rows",
        data,
        "Activity verification table",
        "Additional official ticket / special-hours links appear inside the source cell.",
    )
    return hero + callout_html_v + sections


def body_social(data: dict, report=None) -> str:
    hero = hero_html(
        "Social review links",
        "Direct YouTube pages were verified through official oEmbed metadata. Search and profile links are labelled discovery-only, not verified reviews.",
        "Platform metadata verification",
        ["27 YouTube oEmbed checks", "TikTok / Instagram discovery only", "No venue endorsement implied"],
    )
    callout_html_v = callout_html(
        "warn",
        "oEmbed verifies platform metadata, not review quality",
        "YouTube oEmbed confirms title and channel for each watch URL. "
        + link_html(data["social_reviews"][0]["_source_url"], "Example oEmbed endpoint")
        + ". TikTok/Instagram direct review links remain blank+flag.",
    )
    sections = render_section(
        data["social_reviews"],
        [
            ("subject", "Subject", "text"), ("platform", "Platform", "text"), ("title", "Verified title", "text"),
            ("channel", "Channel", "text"), ("link", "Watch link", "url"), ("verification", "Verification", "text"),
            ("tiktok", "TikTok review", "text"), ("instagram", "Instagram review", "text"),
        ],
        "YouTube oEmbed-verified review / feature links",
        "social-reviews",
        data,
        "Verified YouTube links",
        "These are platform-metadata links, not official venue endorsements.",
    )
    sections += render_section(
        data["discovery_links"],
        [
            ("subject", "Subject", "text"), ("platform", "Platform", "text"), ("link", "Discovery link", "url"),
            ("label", "Label", "text"), ("note", "Note", "text"), ("verified_review", "Verified review", "text"),
        ],
        "Discovery-only platform links — not verified reviews",
        "discovery-links",
        data,
        "Discovery links only",
        "Do not use search or profile links as official place-fact sources.",
    )
    return hero + callout_html_v + sections


def body_transit(data: dict, report=None) -> str:
    hero = hero_html(
        "Transit & hotel cluster",
        "Official MTA fare facts are verified. The full ≤60-minute subway/bus hotel ranking remains unsupported and blank+flag.",
        "Official-source verification",
        ["MTA $3 base fare", "$35 seven-day cap", "No official door-to-door matrix"],
    )
    callout_html_v = callout_html(
        "stop",
        "Full hotel ranking is not verified",
        "Transitous / MOTIS samples are derived community-router data, not an official MTA trip-planner publication. "
        + link_html("https://raw.githubusercontent.com/motis-project/motis/master/openapi.yaml", "MOTIS OpenAPI")
        + ". The 10-destination sample is not a 10-hotel × live-star matrix.",
    )
    sections = render_section(
        data["transit_hotels"],
        [
            ("hotel", "Hotel", "text"), ("starred_within_60_min", "Starred venues ≤60 min", "text"),
            ("rank", "Rank", "text"), ("method", "Method", "text"), ("result", "Result", "text"),
        ],
        "Hotel cluster ranking — all verified values blank+flag",
        "transit-hotels",
        data,
        "Hotel cluster matrix",
        "No hotel is chosen and no official MTA door-to-door matrix was produced.",
    )
    sections += render_section(
        data["transit_facts"],
        [("fact", "Fact", "text"), ("value", "Official value", "text"), ("note", "Note", "text")],
        "Official MTA fare facts and derived-sample caveats",
        "transit-facts",
        data,
        "Official fare facts",
        "The MTA fares page is the source for fare values; the community-router row is labelled derived.",
    )
    return hero + callout_html_v + sections


def body_questions(data: dict, report=None) -> str:
    hero = hero_html(
        "Questions before a decision",
        "Answers that are not printed by an official source are intentionally blank. Each question links to an official source or repository board.",
        "Review gate",
        ["18 questions", "Blank answers are flagged", "2027 re-check required"],
    )
    sections = render_section(
        data["questions"],
        [
            ("question", "Question", "text"), ("known_official", "Known official fact", "text"),
            ("answer", "Answer", "text"), ("why_or_next", "Why / next step", "text"), ("source_hint", "Source hint", "text"),
        ],
        "Questions and blank+flag answers",
        "questions-table",
        data,
        "Unresolved questions",
        "A reasonable final booking decision is not supported until these blanks are resolved or consciously accepted.",
    )
    return (
        hero
        + callout("stop", "No final booking decision yet", "Key 2027-specific price, roster, hours, booking-date, and transit values remain blank+flag.")
        + sections
        + workflow_panel(data, "questions")
    )


def body_suggestions(data: dict, report=None) -> str:
    hero = hero_html(
        "Suggestions & review-first workflow",
        "Suggestions need review before implementation. T18 does not edit shared docs/**, deepdive/**, build scripts, README, or root index.html files.",
        "Review gate",
        ["12 suggestions", "Needs-review status", "Final integration pending"],
    )
    sections = render_section(
        data["suggestions"],
        [
            ("idea", "Suggestion", "text"), ("priority", "Priority", "text"), ("owner", "Owner", "text"),
            ("workflow", "Workflow", "text"), ("status", "Status", "text"), ("source_hint", "Source hint", "text"),
        ],
        "Suggestions with official source / coordination links",
        "suggestions-table",
        data,
        "Suggestions awaiting review",
        "Status remains needs review until the reviewer chooses a path.",
    )
    return (
        hero
        + callout("warn", "Scope boundary", "T18 exclusive scope is audit/** plus append-only COORDINATION.md.")
        + sections
        + suggestion_triage(data)
        + decision_panel(data, "suggestions")
    )


def body_flagged(data: dict, report=None) -> str:
    rows = flagged_rows(data)
    hero = hero_html(
        "Flagged for review",
        "Every blank+flag cell and explicit review blocker across the dossier is published here with an official source link.",
        "Aggregated verification flags",
        [str(len(rows)) + " flags", "Needs review", "No inferred values"],
    )
    sections = render_section(
        rows,
        [
            ("section", "Section", "text"), ("item", "Item", "text"), ("flag", "Flag", "text"),
            ("status", "Status", "text"), ("action", "Action", "text"),
        ],
        "All aggregated flags and blank cells",
        "flagged-table",
        data,
        "All flagged rows",
        "Use the filter box to find a venue, field, or blocker. Every row retains its official source link.",
    )
    return hero + callout("stop", "Review blockers", "Resolve or consciously accept these flags before a final booking decision or Pages publication.") + sections


def body_repo_review(data: dict, report=None) -> str:
    hero = hero_html(
        "Repository review",
        "Line-by-line baseline irregularities are documented without editing another active session’s claimed files.",
        "T18 scope boundary",
        ["audit/** only", "Append-only COORDINATION.md", "No shared-file edits"],
    )
    findings_section = render_section(
        data["findings"],
        [("topic", "Topic", "text"), ("finding", "Finding", "text"), ("implication", "Implication", "text"), ("source_hint", "Source hint", "text")],
        "Independent findings from official-source comparison",
        "repo-findings",
        data,
        "Findings",
        "Official-source disagreements and unsupported claims are kept visible.",
    )
    irregularities_section = render_section(
        repo_irregularities(data),
        [("file", "File", "text"), ("issue", "Issue", "text"), ("evidence", "Evidence", "text"), ("action", "Action", "text")],
        "Baseline repository irregularities with source links",
        "repo-irregularities",
        data,
        "Baseline irregularities",
        "These rows are review findings; T18 did not modify the linked baseline files.",
    )
    integration = callout_html(
        "warn",
        "Final integration request is logged but not executed",
        "Add a “Verified audit” nav link from docs/index.html and deepdive/index.html to ../audit/index.html, merge this branch, verify combined internal links, and republish GitHub Pages. "
        + link_html(data["meta"]["base_url"] + "/COORDINATION.md", "COORDINATION.md T18"),
    )
    return hero + integration + findings_section + irregularities_section


def link_report_rows(report, data: dict):
    if not report:
        return [{
            "check": "Link check",
            "result": "Pending first build pass",
            "status": "info",
            "note": "The generator runs the checker after writing the first pass of pages.",
            "_source_url": "sources.html",
            "_source_label": "Source registry",
            "_flags": ["Pending"],
        }]
    rows = [
        {
            "check": "Internal links",
            "result": "{} unique local links checked; {} broken".format(report["internal_links_checked"], len(report["internal_broken"])),
            "status": "pass" if not report["internal_broken"] else "fail",
            "note": report["internal_check_note"],
            "_source_url": "sources.html",
            "_source_label": "Source registry",
            "_flags": [] if not report["internal_broken"] else ["Broken internal link"],
        },
        {
            "check": "Source URL syntax",
            "result": "{} unique HTTPS source URLs; {} missing; {} non-HTTPS".format(
                report["source_links_checked"], len(report["source_links_missing"]), len(report["source_links_invalid"])
            ),
            "status": "pass" if not report["source_links_missing"] and not report["source_links_invalid"] else "fail",
            "note": report["source_check_note"],
            "_source_url": "sources.html",
            "_source_label": "Source registry",
            "_flags": [],
        },
        {
            "check": "Row source-link coverage",
            "result": "{} of {} rendered rows include a source link".format(
                report["row_source_links"]["rows_with_source_link"], report["row_source_links"]["rows_checked"]
            ),
            "status": "pass" if not report["row_source_links"]["rows_missing_source_link"] else "fail",
            "note": "Every generated table row is checked for a class=\"source-link\" anchor.",
            "_source_url": "sources.html",
            "_source_label": "Source registry",
            "_flags": [],
        },
        {
            "check": "External live HTTP status",
            "result": "Not re-fetched from static build",
            "status": "info",
            "note": report["external_fetch_note"],
            "_source_url": "sources.html",
            "_source_label": "Source registry",
            "_flags": ["Live HTTP 200 not claimed"],
        },
        {
            "check": "Overall status",
            "result": report["status"].upper(),
            "status": report["status"],
            "note": "Pass means no broken internal links, no missing row source links, no missing row source URLs, and no non-HTTPS source URLs.",
            "_source_url": "sources.html",
            "_source_label": "Source registry",
            "_flags": [],
        },
    ]
    return rows


def body_verification(data: dict, report=None) -> str:
    r = report or {}
    hero = hero_html(
        "Verification & link checker",
        "The static build checks relative internal links on disk, validates HTTPS source URL syntax, and confirms every rendered table row has a source link.",
        "Build-time checks",
        [data["meta"]["verification_date"], "Stdlib-only generator", "No browser-side network calls"],
    )
    kpis = '<div class="grid kpis section">' + "".join([
        kpi_card(r.get("status", "pending").upper(), "Overall checker status"),
        kpi_card(r.get("internal_links_checked", 0), "Unique internal links"),
        kpi_card(r.get("source_links_checked", 0), "Unique HTTPS source URLs"),
        kpi_card("{} / {}".format(r.get("row_source_links", {}).get("rows_with_source_link", 0), r.get("row_source_links", {}).get("rows_checked", 0)), "Rows with source link"),
    ]) + "</div>"
    callout_html_v = callout_html(
        "warn",
        "External pages are not re-fetched by the generator",
        "T18 fetched official pages during verification and recorded the capture log. The static build validates URL syntax and source-link presence; it does not claim live HTTP 200 for external pages. "
        + link_html("https://www.mta.info/fares-tolls/subway-bus", "Example official source")
        + ".",
    )
    sections = render_section(
        link_report_rows(report, data),
        [("check", "Check", "text"), ("result", "Result", "text"), ("status", "Status", "text"), ("note", "Note", "text")],
        "Build-time link and source-link checker summary",
        "link-report",
        data,
        "Checker summary",
        "Full machine-readable output is in data/link_report.json.",
    )
    sections += render_section(
        data["sources"],
        [
            ("rank", "Rank", "text"), ("title", "Title", "text"), ("used_for", "Used for", "text"),
            ("verification", "Verification log", "text"), ("url", "Official source", "source"),
        ],
        "Official source registry and T18 fetch log",
        "verification-sources",
        data,
        "Source registry / verification log",
        "Each row records what was fetched and what the source was used for.",
    )
    policy = '<section class="section"><h2>Source policy</h2><div class="grid cards-2">' + "".join(
        card("Rule " + str(i), "<p>" + esc(rule) + "</p>") for i, rule in enumerate(data["meta"]["source_policy"], 1)
    ) + "</div></section>"
    return hero + kpis + callout_html_v + sections + policy


def body_sources(data: dict, report=None) -> str:
    external, invalid, missing, _ = source_url_inventory(data)
    hero = hero_html(
        "Official sources",
        "The registry below outranks search snippets, secondary guides, and platform discovery links. All unique HTTPS source URLs are listed with their domains.",
        "Source hierarchy",
        [str(len(data["sources"])) + " registry entries", str(len(external)) + " unique HTTPS URLs", "No inferred values"],
    )
    registry = render_section(
        data["sources"],
        [
            ("rank", "Rank", "text"), ("title", "Title", "text"), ("used_for", "Used for", "text"),
            ("verification", "Verification", "text"), ("url", "Official source", "source"),
        ],
        "Official-source registry",
        "sources-registry",
        data,
        "Registry",
        "Official place/agency pages and the repository’s own baseline files are distinguished.",
    )
    url_rows = []
    for url in external:
        url_rows.append({
            "domain": urlparse(url).netloc,
            "url": url,
            "used_by": "T18 verification log / row source link",
            "_source_url": url,
            "_source_label": "Official source",
            "_flags": [],
        })
    inventory = render_section(
        url_rows,
        [("domain", "Domain", "text"), ("url", "Official source URL", "url"), ("used_by", "Recorded in", "text")],
        "Unique HTTPS source URLs recorded in the dossier",
        "source-url-inventory",
        data,
        "Unique source URL inventory",
        "Duplicates are collapsed. Live HTTP status is not re-fetched by the static generator.",
    )
    policy = '<section class="section"><h2>Source policy</h2><div class="grid cards-2">' + "".join(
        card("Rule " + str(i), "<p>" + esc(rule) + "</p>") for i, rule in enumerate(data["meta"]["source_policy"], 1)
    ) + "</div></section>"
    return hero + registry + inventory + policy


BODIES = {
    "home": body_home,
    "hotels": body_hotels,
    "restaurants": body_restaurants,
    "activities": body_activities,
    "social": body_social,
    "transit": body_transit,
    "questions": body_questions,
    "suggestions": body_suggestions,
    "flagged": body_flagged,
    "repo-review": body_repo_review,
    "verification": body_verification,
    "sources": body_sources,
}


JS = r"""
(function () {
  const filterState = new Map();

  function stateFor(id) {
    if (!filterState.has(id)) filterState.set(id, { q: "", flagged: false });
    return filterState.get(id);
  }

  function applyFilters(table) {
    const state = stateFor(table.id);
    table.querySelectorAll("tbody tr").forEach(function (row) {
      const matchQ = !state.q || (row.dataset.search || "").indexOf(state.q) !== -1;
      const matchF = !state.flagged || row.dataset.flagged === "1";
      row.classList.toggle("hidden", !(matchQ && matchF));
    });
  }

  document.addEventListener("input", function (event) {
    const input = event.target.closest("[data-table-target]");
    if (!input) return;
    const table = document.getElementById(input.dataset.tableTarget);
    if (!table) return;
    const state = stateFor(table.id);
    state.q = input.value.toLowerCase();
    applyFilters(table);
  });

  document.addEventListener("click", function (event) {
    const flagBtn = event.target.closest("[data-flag-target]");
    if (flagBtn) {
      const table = document.getElementById(flagBtn.dataset.flagTarget);
      if (table) {
        const state = stateFor(table.id);
        state.flagged = flagBtn.getAttribute("aria-pressed") !== "true";
        flagBtn.setAttribute("aria-pressed", state.flagged ? "true" : "false");
        flagBtn.textContent = state.flagged ? "Show all rows" : "Show flagged only";
        applyFilters(table);
      }
      return;
    }
    const cardBtn = event.target.closest("[data-card-target]");
    if (cardBtn) {
      const table = document.getElementById(cardBtn.dataset.cardTarget);
      if (table) {
        const wrap = table.closest(".table-wrap");
        const on = cardBtn.getAttribute("aria-pressed") !== "true";
        cardBtn.setAttribute("aria-pressed", on ? "true" : "false");
        cardBtn.textContent = on ? "Table view" : "Card view";
        if (wrap) wrap.dataset.forceCards = on ? "true" : "false";
      }
      return;
    }
  });

  function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  document.querySelectorAll("[data-decision-panel]").forEach(function (panel) {
    const key = panel.dataset.storageKey || "t18-decision-v1";
    const radios = Array.prototype.slice.call(panel.querySelectorAll("input[type=radio]"));
    const output = panel.querySelector(".decision-output");
    function render() {
      const selectedValue = localStorage.getItem(key) || "";
      radios.forEach(function (radio) {
        radio.checked = radio.value === selectedValue;
        const choice = radio.closest(".choice");
        if (choice) choice.classList.toggle("selected", radio.checked);
      });
      const selected = radios.find(function (radio) { return radio.checked; });
      if (!selected) {
        output.innerHTML = "<strong>No decision path selected yet.</strong> Complete the review workflow before choosing Hold, Re-verify, Book refundable, or Integrate.";
      } else {
        output.innerHTML = "<strong>Selected:</strong> " + escapeHTML(selected.dataset.title) +
          "<br><strong>Rationale:</strong> " + escapeHTML(selected.dataset.rationale) +
          "<br><strong>Caveat:</strong> " + escapeHTML(selected.dataset.caveat);
      }
    }
    radios.forEach(function (radio) {
      radio.addEventListener("change", function () {
        localStorage.setItem(key, radio.value);
        render();
      });
    });
    const copy = panel.querySelector(".copy-decision");
    if (copy) {
      copy.addEventListener("click", function () {
        const selected = radios.find(function (radio) { return radio.checked; });
        const text = selected
          ? "T18 decision: " + selected.dataset.title + "\nRationale: " + selected.dataset.rationale + "\nCaveat: " + selected.dataset.caveat
          : "T18 decision: none selected";
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(function () {
            copy.textContent = "Copied";
            setTimeout(function () { copy.textContent = "Copy decision summary"; }, 1200);
          }).catch(function () { copy.textContent = "Copy unavailable"; });
        } else {
          copy.textContent = "Copy unavailable";
        }
      });
    }
    const reset = panel.querySelector(".reset-decision");
    if (reset) {
      reset.addEventListener("click", function () {
        localStorage.removeItem(key);
        render();
      });
    }
    render();
  });

  document.querySelectorAll("[data-checklist]").forEach(function (root) {
    const key = root.dataset.checklistKey;
    const checks = Array.prototype.slice.call(root.querySelectorAll(".review-check"));
    const bar = root.querySelector(".progress > div");
    const output = root.querySelector(".checklist-output");
    function load() {
      try { return JSON.parse(localStorage.getItem(key) || "[]"); } catch (e) { return []; }
    }
    function save(values) { localStorage.setItem(key, JSON.stringify(values)); }
    function render() {
      const done = load();
      checks.forEach(function (check) {
        check.checked = done.indexOf(Number(check.dataset.step)) !== -1;
      });
      const count = checks.filter(function (check) { return check.checked; }).length;
      const total = checks.length || 1;
      if (bar) bar.style.width = (count / total * 100) + "%";
      if (output) output.innerHTML = "<strong>" + count + " of " + checks.length + " review steps complete.</strong>";
    }
    checks.forEach(function (check) {
      check.addEventListener("change", function () {
        const step = Number(check.dataset.step);
        let done = load().filter(function (item) { return item !== step; });
        if (check.checked) done.push(step);
        save(done);
        render();
      });
    });
    const reset = root.querySelector(".reset-checklist");
    if (reset) {
      reset.addEventListener("click", function () {
        localStorage.removeItem(key);
        render();
      });
    }
    render();
  });
})();
"""


def nav_html(active: str) -> str:
    links = []
    for fn, title, slug, _ in PAGES:
        current = ' aria-current="page"' if slug == active else ""
        links.append('<a href="./{}"{}>{}</a>'.format(esc(fn), current, esc(title)))
    return '<nav class="nav" aria-label="Audit sections">' + "".join(links) + "</nav>"


def page_shell(title: str, active: str, body: str, description: str, data: dict, css: str) -> str:
    meta = data["meta"]
    coord = meta["base_url"] + "/COORDINATION.md"
    generated = utc_now()
    footer = (
        '<footer class="footer">Generated {} · T18 {} · '
        '<a href="./data/official_facts.json">Machine-readable facts</a> · '
        '<a href="./data/link_report.json">Link report</a> · '
        '<a href="./assets/style.css">Stylesheet</a> · '
        '<a href="./build_audit.py">Generator</a> · '
        '<a href="{}" target="_blank" rel="noopener noreferrer">Coordination board</a>'
        "</footer>"
    ).format(esc(generated), esc(meta["verification_date"]), attr(coord))
    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<meta name=\"color-scheme\" content=\"light\">\n"
        "<meta name=\"description\" content=\"{}\">\n"
        "<title>{} · T18 Verified Audit</title>\n"
        "<style>\n{}\n</style>\n"
        "</head>\n<body>\n"
        "<a class=\"skip\" href=\"#main\">Skip to content</a>\n"
        "<header class=\"site-header\"><div class=\"header-inner\">"
        "<a class=\"brand\" href=\"./index.html\">Verified <span>Audit</span></a>\n{}\n"
        "</div></header>\n"
        "<main id=\"main\">\n{}\n</main>\n"
        "{}\n"
        "<script>\n{}\n</script>\n"
        "</body>\n</html>\n"
    ).format(
        attr(description), esc(title), css, nav_html(active), body, footer, JS
    )


def build_pages(data: dict, css: str, report):
    pages = {}
    for fn, title, slug, desc in PAGES:
        body_fn = BODIES[slug]
        body = body_fn(data, report)
        pages[fn] = page_shell(title, slug, body, desc, data, css)
    return pages


def build_verification_page(data: dict, css: str, report):
    return page_shell(
        "Verification & link checker",
        "verification",
        body_verification(data, report),
        "Source registry, internal-link checker, and source-link checker.",
        data,
        css,
    )


class HrefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def run_link_check(data: dict, pages: dict) -> dict:
    internal = {}
    for page_name, doc in pages.items():
        parser = HrefParser()
        parser.feed(doc)
        for href in parser.hrefs:
            if href.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            clean = href.split("#", 1)[0].split("?", 1)[0]
            if not clean:
                continue
            target = (ROOT / clean).resolve()
            try:
                resolved = str(target.relative_to(ROOT))
            except ValueError:
                resolved = str(target)
            exists = target.exists()
            key = clean
            if key not in internal:
                internal[key] = {
                    "href": clean,
                    "resolved": resolved,
                    "exists": exists,
                    "pages": [],
                }
            if page_name not in internal[key]["pages"]:
                internal[key]["pages"].append(page_name)
    internal_links = sorted(internal.values(), key=lambda x: x["href"])
    internal_broken = [row for row in internal_links if not row["exists"]]

    external, invalid, missing, _ = source_url_inventory(data)
    source_links = [{
        "url": url,
        "status": "HTTPS syntax verified",
        "note": "Recorded in T18 official-source fetch log; live HTTP 200 not claimed by static build.",
        "_source_url": url,
        "_source_label": "Official source",
        "_flags": [],
    } for url in external]

    row_total = 0
    row_with = 0
    row_missing = []
    for page_name, doc in pages.items():
        for match in re.finditer(r"<tr\b[^>]*>(.*?)</tr>", doc, re.S | re.I):
            inner = match.group(1)
            if "<td" not in inner.lower():
                continue
            row_total += 1
            if 'class="source-link"' in inner or "class='source-link'" in inner:
                row_with += 1
            else:
                row_missing.append({"page": page_name, "row_number": row_total})
    row_coverage = {
        "rows_checked": row_total,
        "rows_with_source_link": row_with,
        "rows_missing_source_link": row_missing,
    }

    status = "pass"
    if internal_broken or missing or invalid or row_missing:
        status = "fail"
    return {
        "generated_at": utc_now(),
        "status": status,
        "pages_checked": len(pages),
        "internal_links_checked": len(internal_links),
        "internal_links": internal_links,
        "internal_broken": internal_broken,
        "internal_check_note": "Relative hrefs were resolved against audit/ and checked on disk; external and anchor links were skipped.",
        "source_links_checked": len(external),
        "source_links": source_links,
        "source_links_missing": missing,
        "source_links_invalid": invalid,
        "source_check_note": "Row source URLs and extra official-source URLs must be unique HTTPS links; internal source-registry links are handled as internal links.",
        "row_source_links": row_coverage,
        "external_fetch_note": "External official pages were fetched during T18 verification and recorded in the source registry. The static generator does not re-fetch them and does not claim live HTTP 200 status.",
        "method": "stdlib HTMLParser + regex row scan; no network access",
    }


def stable_key(report: dict) -> str:
    copy = {k: v for k, v in report.items() if k != "generated_at"}
    return json.dumps(copy, ensure_ascii=False, sort_keys=True)


def main() -> None:
    data = load_data()
    css = STYLE_PATH.read_text(encoding="utf-8")

    write_json(DATA_DIR / "official_facts.json", data)
    write_json(DATA_DIR / "link_report.json", {"status": "pending", "generated_at": utc_now(), "note": "Placeholder before first build pass."})

    report = None
    last_key = None
    for _ in range(8):
        pages = build_pages(data, css, report)
        for fn, doc in pages.items():
            write_text(ROOT / fn, doc)
        new_report = run_link_check(data, pages)
        key = stable_key(new_report)
        report = new_report
        if key == last_key:
            break
        last_key = key

    final_pages = build_pages(data, css, report)
    for fn, doc in final_pages.items():
        write_text(ROOT / fn, doc)
    final_report = run_link_check(data, final_pages)
    write_json(DATA_DIR / "link_report.json", final_report)
    data["link_report"] = final_report
    write_json(DATA_DIR / "official_facts.json", data)
    # Make the verification page display the final report values.
    final_pages["verification.html"] = build_verification_page(data, css, final_report)
    write_text(ROOT / "verification.html", final_pages["verification.html"])

    print("Generated {} pages".format(len(final_pages)))
    print("Link checker status: {}".format(final_report["status"]))
    print("Internal links: {} checked, {} broken".format(final_report["internal_links_checked"], len(final_report["internal_broken"])))
    print("Source URLs: {} unique HTTPS, {} missing, {} non-HTTPS".format(final_report["source_links_checked"], len(final_report["source_links_missing"]), len(final_report["source_links_invalid"])))
    print("Row source links: {}/{}".format(final_report["row_source_links"]["rows_with_source_link"], final_report["row_source_links"]["rows_checked"]))
    if final_report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

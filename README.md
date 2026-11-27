# NYC 2027 — trip planning dashboard

A source-linked plan for **two adults, 15–22 February 2027** in New York City: hotels priced for the
whole 7-night stay, MICHELIN-starred restaurants reachable within the hour, activities with official
hours and prices, a budget that says which numbers are real, and an explicit register of everything that
could **not** be verified.

**Live site:** https://kanlerxz87-cyber.github.io/NYFun1/

---

## The rules this repository is built on

1. **Read it or leave it blank.** A value appears only if it was read on the official page linked in the
   same row. If it could not be read, the cell is blank and the reason is named — never filled in from
   plausibility.
2. **Never infer.** No "typical" prices, no assumed opening hours, no guessed social handles.
3. **Separate the award from the listing.** A star is an award; a venue in the guide carries a different
   badge and is shown separately.
4. **Label every derived number.** Arithmetic on a verified figure is marked *derived*, with the formula
   written down on the Method page.
5. **Keep disagreements visible.** When two official pages disagree — and they do, on the star count —
   both numbers are shown and the conflict is flagged.
6. **Date every snapshot.** All prices, hours, coordinates, and calendars were verified on **2026-11-25/26** and will drift. A **2026-11-27** re-read of official URLs corrected the Met pay-what-you-wish rule, the 9/11 Tuesday wording, the MetroCard citation, every Booking hotel room table (all-in totals are now Booking-stated incl. tax, fee model corrected to the official $3.50/night — F-44), the Met hours (F-31), and the Fairfield score/price (F-38); what could not be re-confirmed stays flagged (F-30, F-41, F-43, F-45).

Anything unverified is on [the Flagged page](docs/flagged.html). Anything undecided is on
[the Questions page](docs/questions.html).

---

## What the site contains

| Page | What it answers |
|---|---|
| [Overview](docs/index.html) | The decision, in six numbered points: hotel ($1,155.48 all-in as printed by Booking, 2026-11-27), dates (15–22 Feb 2027), reconciled stars (69 live vs 72 ceremony), priced subtotal ($2,977.48; airfare excluded), what is open |
| [Requirements](docs/requirements.html) | Every requirement from the brief: MET or PARTIAL, the reason, the official source and the related flag or question (checked 2026-11-27) |
| [Hotels](docs/hotels.html) | 7 hotels × 7 nights with verified street addresses, direct Booking URLs, Booking-stated all-in totals (read 2026-11-27), tax/resort-fee parity, 5-week seasonal table, shifted Feb starts & 22-star reach |
| [MICHELIN](docs/restaurants.html) | 72 Nov 2025 ceremony entries reconciled to 69 live NYC stars (5/14/50), 22 verified Manhattan menus/hours/coordinates, 3 spatial clusters, Green Star / Bib separation |
| [Activities](docs/activities.html) | 12 activity candidates; The Met hours re-confirmed 2026-11-27 (F-31 resolved), AMNH/High Line hours re-confirmed (F-41 narrowed to pay-what-you-wish wording), Broadway schedule still blank (F-33); dated values are flagged where the latest official read was incomplete |
| [Itinerary](docs/itinerary.html) | Day-by-day for 7 nights, plus 4-night and 14-night variants (routed around Met Wed & 9/11 Museum hours), booking countdown, NWS Feb/Mar climate normals |
| [Budget](docs/budget.html) | $2,977.48 priced subtotal across 10 priced lines; airfare, casual dining, tax/tip and other costs remain unpriced, verified dinner swaps & wine pairings |
| [Questions](docs/questions.html) | 27 decisions: research items resolved vs traveller preferences & date-blocked official 14 Dec 2026 check (MICHELIN press site; ceremony flag resolved 2026-11-26) |
| [Suggestions](docs/suggestions.html) | 12 structured improvements (8 implemented on 2026-11-26, 4 operational checks pending) |
| [Flagged](docs/flagged.html) | 38 tracked items (resolved, documented, and live open flags) with primary sources; F-38 to F-43 added 2026-11-27 |
| [Method & sources](docs/method.html) | Every primary source URL, final independent audit ledger, lexical external URL audit, scraping limits, travel model formula, and build assertions |
| [Repo review](docs/repo-review.html) | Verification inventory, audit findings, orphan cleanup, and reproduction guide |

`deepdive/` holds an **earlier, independent dataset** from a previous session. It is kept so that work is
not lost but is **not** canonical: it disagrees with this site on the star count, the hotel shortlist and
the transit method. See suggestion S-01.

---

## Build

Standard library only. No dependencies, no network access needed at build time.

```bash
python3 build_site.py
```

Writes `docs/*.html`, `docs/assets/style.css`, and `docs/data/external_url_audit.json`. The generator **fails the build** (non-zero exit) if:

- any internal link points at a file that does not exist,
- a template token or escaped markup leaks into the output,
- a page contains a placeholder link that goes nowhere,
- two elements share an id,
- a table row has a different number of cells than its header, or
- the budget's stated subtotal does not equal the sum of its priced lines,
- any generated table row lacks an external source link,
- any internal link in `docs/`, the root redirect, or archived `deepdive/` is broken, or
- the lexical external URL audit finds a non-HTTPS external URL.

`build.py`, `build_deepdive.py` and `content.py` belong to the earlier dataset and are left untouched. The external URL audit is lexical and is accompanied by manual `fetch_page` spot checks recorded in `site_data/independent_verification.json`; broken official URLs found during the audit were replaced and the fixes are published in `docs/data/external_url_audit.json`.

---

## Data

Everything the site renders lives in `site_data/`, one file per concern. Edit the JSON, re-run the build.

| File | Contents |
|---|---|
| `michelin_roster.json` | 72 Nov 2025 ceremony entries reconciled with `live_nyc_status` to 69 active NYC stars (`5` 3★ / `14` 2★ / `50` 1★), plus 76 Bib Gourmand, 224 Selected, 4 Green Stars |
| `restaurant_details.json` | 22 verified Manhattan starred venues + Selected Green Star `One White Street`: full Mon–Sun hours, menu prices or Tock deposit floors, official URLs, verified building coordinates |
| `hotels.json` | 7 hotels: verified street addresses, direct Booking `/hotel/us/...` URLs, 2026-11-27 Booking-stated all-in 7-night totals + 2026-11-26 pre-tax snapshots, resort-fee parity, 5-week seasonal comparison, shifted Feb starts, 22-star reach |
| `activities.json` | 12 activity candidates; The Met hours re-confirmed from metmuseum.org (2026-11-27), AMNH/High Line hours re-confirmed (2026-11-27), Broadway schedule blank (F-33), AMNH pay-what-you-wish wording open (F-41), with dated prices and modelled distances from `538 W 58th St` |
| `social.json` | Social & video links across 28 venue/activity keys: 24 official Instagram handles (incl. `@cotekoreansteakhouse`), 23 YouTube reviews, 4 TikTok tasting videos, honest search fallbacks |
| `framework.json` | Trip dates, OPM/NYCPS holidays, NWS Central Park climate normals, $2,977.48 priced subtotal (airfare excluded), 7/4/14-night itineraries, 40 flags, 27 questions, 12 suggestions |
| `independent_verification.json` | 89 source-ledger entries (87 official, one trusted aggregator, one secondary/flagged), with per-entry classifications and read dates; rendered on the Method page |

### Two fields to understand before editing

- **`hours_status`** — `VERIFIED`, `PARTIAL` or `UNVERIFIED`. All 22 priority Manhattan starred venues and `One White Street` now carry verified hours; remaining roster-only rows stay clean without guessed hours.
- **`all_in_7n_usd`** — Booking.com's own tax-inclusive total ("Gesamt / Includes taxes and charges") re-read live on **2026-11-27** for every hotel; the official NYC rate behind it is `14.75%` + `$3.50/night` fixed fees (`$2.00` room fee + `$1.50` NYS unit fee, nyc.gov). Fairfield Central Park (`$985.60` pre-tax -> **`$1,155.48`** stated all-in) wins on all-in parity, breakfast included, `$0` resort fee, and free cancellation until `2027-02-12`. Where a 2026-11-26 pre-tax snapshot no longer composes with the 2026-11-27 total (Arlo SoHo, Arlo Midtown, Residence Inn moved overnight), the stated total governs — flag F-31.

---

## Known limits, stated plainly

| Limit | Where it is recorded |
|---|---|
| MICHELIN Media confirms the **14 December 2026** ceremony date; the 2026 selection/star changes remain pending until the event | F-01 / F-25 |
| 72 ceremony vs 69 live NYC discrepancy reconciled (`Blue Hill at Stone Barns`, `La Bastide`, fire-closed `Shion 69 Leonard St`) | F-02 (Resolved) |
| Hotel prices carry live Black Friday / Bonus promos (`-30%` to `-36%`); lock $0-prepay free-cancel and re-check in Jan 2027 | F-03 |
| Reach across 22 verified Manhattan stars uses Haversine 5 km radius pending full 69-venue weekday GTFS routing | F-05, Q-19, S-02 |
| Direct unauthenticated TikTok profile fetches return HTTP 400; only 4 verified video URLs + search links used | F-07 |
| Per Se, Atera & Aquavit show Tock deposit floors ($200 / $200 / $50) behind checkout date selection | `restaurant_details.json` |
| Airfare is excluded: departure airport is unknown and the saved AMS–JFK one-adult aggregator snapshot does not verify a two-seat checkout | F-15 |
| Broadway days/hours and two-seat ticket price remain blank until a specific show/performance is selected | F-33 / Q-16 |

---

## Licence and attribution

No licence file is present; that decision belongs to the repository owner. Star data is attributed to the
MICHELIN Guide, hotel prices to Booking.com, fares to KAYAK and Google Flights, transit to the MTA, and
each venue's hours and prices to the venue itself. Every page footer repeats that prices are
point-in-time snapshots that must be re-checked before booking.

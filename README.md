# NYFun1 — New York City trip plan, 15–22 February 2027

A source-linked trip-planning dataset and static dashboard for two adults: hotel price/value,
MICHELIN-starred restaurant access within one hour by subway, verified activities, costs, and an
explicit register of everything that could not be verified.

**Live site:** https://kanlerxz87-cyber.github.io/NYFun1/

## What is in here

| Path | Purpose |
|---|---|
| `docs/` | The published static site (GitHub Pages serves this folder) |
| `docs/data/michelin_2025.csv` | 72 star entries from MICHELIN's official 18 Nov 2025 New York article |
| `docs/data/guide_listed.csv` | MICHELIN Guide *listed* (no star) restaurants verified on official listing pages |
| `docs/data/hotels.csv` | 4 hotels, verified queen/king bed + private bathroom, 7-night price for 2 adults |
| `docs/data/date_windows.csv` | 7-night price across three date windows (15 Feb / 22 Feb / 8 Mar 2027) |
| `docs/data/activities.csv` | 12 candidate activities with verification status |
| `content.py` | Registers: 22 flags, 18 open questions, 12 suggestions, itineraries, budget, sources |
| `build.py` | Stdlib-only generator: reads the CSVs, writes every HTML page |
| `COORDINATION.md` | Shared task board, claims, file ownership and verification log |
| `deepdive/` | **Second, independently researched site — the "verified deep dive"** |

## Build

```bash
python3 build.py           # main dashboard: docs/*.html from docs/data/*.csv + content.py
python3 build_deepdive.py  # deep dive: deepdive/*.html from deepdive/data/*.json
python3 -m http.server 8000   # preview both at http://localhost:8000
```

No third-party dependencies.

## Verification rules used

1. A value is shown only if it was read on an official page (MICHELIN, the museum, Booking.com's own
   room table) or, where noted, on an independent secondary source.
2. If a field could not be read, it is **blank** and listed on `docs/flagged.html` with the source that
   would settle it. No plausible-looking values are substituted.
3. Every derived number (tax-inclusive totals, spend envelopes, transit minutes, hotel score) is labelled
   MODEL/DERIVED and its formula is on `docs/methodology.html`.
4. Prices and hours are point-in-time snapshots (2026-11-25) and must be re-checked before booking.

## Data dictionary (CSV columns)

- `michelin_2025.csv`: `name, stars, green, cuisine, borough, price_band, address, hours, closed,
  michelin_url, website, booking, lat, lon, verification` — `verification` is `verified`, `partial`, or
  `roster-only` (roster-only rows have name/star/cuisine/borough/link only).
- `hotels.csv`: `hotel, area, address, room_type, bed, bath, size_sqft, base_7n_usd, tax_rate,
  city_tax_night, resort_fee_in_nightly, breakfast, cancellation, booking_url, rating_out_of_10,
  lat_model, lon_model, verification`.
- `date_windows.csv`: one row per hotel/date window with the 7-night total and the exact source URL.
- `activities.csv`: `activity, category, area, address, hours, cost_adult_usd, cost_2_adults_usd,
  official_url, verification, exceptions, notes`.

## Two datasets, deliberately

Two research sessions worked this repo in parallel before either was merged, from different official
sources. Rather than merge the numbers and quietly pick a winner wherever they disagree, both are
published and cross-linked; the disagreements are itemised in `COORDINATION.md`.

| | `docs/` (main dashboard) | `deepdive/` |
|---|---|---|
| Stars | 72 (5/15/52) — Michelin's ceremony article | 69 (5/14/50) — Michelin's live filtered lists |
| Hotels | 4, quoted from Booking.com room tables | 10, quoted from Michelin's own availability pages |
| Hotel price basis | room rate + separately itemised taxes/fees | the stay total Michelin prints, taxes & fees included |
| Transit | distance/18 km/h model, labelled MODEL | 9 legs measured against MTA GTFS via Transitous |
| Restaurant depth | roster + price band; social links are search links only | menu prices from the venues' own pages, hours, closures, verified video |
| Best for | the ranked shortlist and the budget envelope | menu prices, hours, measured travel times, the audit trail |

`deepdive/` also carries the **verification log** (`deepdive/review.html`) with a 10-link manual review
checklist, and a **suggestions** page kept separate from the data.

### What the deep dive adds over the dashboard

- Restaurant prices read from each venue's own menu page (Le Bernardin $225 dinner / $142 lunch,
  EMP $385, Saga $215, Gabriel Kreuther $200, The Modern $185, Jungsik $335, Gramercy $178).
- Per-venue opening hours and closures, straight from the Michelin detail pages.
- Nine door-to-door transit legs measured against MTA GTFS — not modelled.
- A four-window seasonality test proving the 15–22 Feb window is the cheapest of the four tested.
- Nineteen values left deliberately blank, each with a row in the questions register.

## Known limitations

See `docs/flagged.html` (22 items) and `docs/questions.html` (18 items). The three that matter most:
hotel prices are dynamic snapshots, the MICHELIN star list is expected to change on 14 December 2026
(before the trip), and all transit minutes are modelled, not MTA-verified.

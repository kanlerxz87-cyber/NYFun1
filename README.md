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

## Build

```bash
python3 build.py     # regenerates docs/*.html from docs/data/*.csv + content.py
python3 -m http.server -d docs 8000   # preview at http://localhost:8000
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

## Known limitations

See `docs/flagged.html` (22 items) and `docs/questions.html` (18 items). The three that matter most:
hotel prices are dynamic snapshots, the MICHELIN star list is expected to change on 14 December 2026
(before the trip), and all transit minutes are modelled, not MTA-verified.

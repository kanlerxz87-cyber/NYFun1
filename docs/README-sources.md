# Source hierarchy, conventions and how to extend this dataset

## 1. Source hierarchy

| Rank | Source | Used for | Not used for |
|---|---|---|---|
| 1 | The venue's own website | prices, menus, hours, policies, closures, dress code | Michelin distinctions |
| 1 | The venue's own booking platform (Tock / Resy page run by the venue) | prices, deposit amounts, released seating windows | — |
| 2 | guide.michelin.com | star/Bib/Selected distinction, address, cuisine, price band, hours where the venue publishes none | prices (Michelin shows only a `$$$$` band) |
| 3 | The agency that runs an attraction (NPS, MTA, museum, operator) | hours, admission, closures, access rules | anything else |
| 4 | OpenStreetMap via Nominatim | coordinates only | hours, prices, names |
| — | Anything else | **nothing** | — |

No aggregators, no review sites, no Wikipedia, no video descriptions, no memory, no inference.
A `$$$$` band from Michelin is a price *band*, not a price — it never becomes a dollar figure.

## 2. How "unverified" works

If a field cannot be filled from rank 1–4, it is `null` in the JSON, rendered as a blank with a
`unverified` tag on the page, and given a row in `questions.html` with a suggested way to close it.
The site currently carries 19 such blanks; the list is in the "Known gaps" section of `README.md`.

Two special cases:

- **Derived values.** Only one exists: the budget subtotal on `index.html`. It is a sum of verified
  inputs, and it is labelled derived on the page itself. The generator never computes a price.
- **Point-in-time values.** Hotel quotes are live availability read on 2026-11-25 for a stay 15 months
  out. They are labelled as indicative everywhere they appear. The seasonality comparison between four
  such quotes is still valid as a *relative* comparison and is presented that way.

## 3. Data file schemas

### `data/hotels.json`
`meta` (quote basis, caveats) · `hotels[]` — `id, name, neighborhood, address, lat, lon, guest_score,
rooms, source, room_type_quoted, bed, bathroom, nightly_from_usd, nightly_quoted_usd, rate_note,
total_7n_usd, total_is_displayed_by_source, notes` · `seasonality_check` (four windows, same room type).

`total_is_displayed_by_source` is the guard against accidental arithmetic: if Michelin did not print a
stay total, the field is `false` and the page shows a blank rather than a product.

### `data/michelin.json`
`meta` (counts as reported by Michelin, award-year caveat) · `three_stars[]`, `two_stars[]` (objects
with address/hours where known) · `one_star[]` (50 names) · `one_star_url_slugs` (per-name slugs, since
Michelin's slugs are inconsistent) · `one_star_brooklyn`, `one_star_queens` (borough-qualified URLs) ·
`bib_gourmand_*`. Starred and listed are never mixed in one array.

### `data/restaurants.json`
`starred[]` — the 10 rooms with detail: `stars, cuisine, michelin_price, address, lat, lon, official,
michelin, reserve, phone, hours, closed_days, menus[{menu, usd_per_person, source}], cost_for_two_usd,
cheapest_option, supplements, policies, videos[{platform,title,url}], social_search`.
`cost_for_two_usd = cheapest published full-menu price × 2`; `null` when nothing is published.
Also `starred_no_detail_yet[]`, `selected_only_examples[]`, `one_star_shortlist[]`.

### `data/activities.json`
`activities[]` — `name, address, official, hours, hours_status (verified|unverified), admission,
booking, transit, exceptions, rules, accessibility, practical, best_for, videos`. `suggestions[]` for
attractions that are on the shortlist but were not verifiable in this pass (status-tagged).

### `data/transit.json`
`measured_legs[]` — `from, to, minutes, transfers, mode, status: measured`. `hotel_cluster_screen` —
straight-line screen, explicitly **not** a travel time, with the caveat written into the file.
`fare_note`, `practical[]`.

## 4. Conventions

- **ISO dates** in JSON (`2027-02-15`); human dates on the page (`15–22 Feb 2027`).
- **USD, no currency symbol** in JSON; the renderer adds `$` and thousands separators.
- **Times as `HH:MM–HH:MM`** in 24 h, in local New York time, matching the source's own wording even
  where the source used 12 h.
- **URLs verbatim**, including query strings (`?arr=…&dep=…&nA=2&nC=0&nR=1`), because those parameters
  are what make a hotel quote reproducible.
- **Never overwrite a blank with a guess to make a page look complete.** A blank is a finding.

## 5. Extending it

1. Add or correct the record in the relevant `data/*.json`.
2. Run `python3 build.py`.
3. If you blanked a value, add a row to the `questions` list in `build.py::build_questions` and to the
   relevant `README.md` gap list.
4. If you found a contradiction between two official sources, add it to
   `build.py::build_review`'s `issues` list — do not silently pick a winner.
5. Commit the JSON **and** the regenerated HTML together, or the site will disagree with its data.

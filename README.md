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
6. **Date every snapshot.** The core data was read on **2026-11-25**; hotel pages were re-read on **2026-11-26** and both reads are published. Prices and hours will keep drifting.

Anything unverified is on [the Flagged page](docs/flagged.html). Anything undecided is on
[the Questions page](docs/questions.html).

---

## What the site contains

| Page | What it answers |
|---|---|
| [Overview](docs/index.html) | The decision, in six numbered points: hotel, dates, why 7 nights, what is verified, what could invalidate the plan |
| [Hotels](docs/hotels.html) | 7 hotels × 7 nights with bed, private bathroom, breakfast, advertised vs all-in cost, cancellation terms; ranked by all-in cost and by MICHELIN reach |
| [MICHELIN](docs/restaurants.html) | All 72 star entries with their distinction (★★★ / ★★ / ★), hours, menu prices and social links where verified; guide-listed venues separately |
| [Activities](docs/activities.html) | 11 activities with official hours, exceptions, prices for two, and social/video links |
| [Itinerary](docs/itinerary.html) | Day-by-day for 7 nights, plus 4-night and 14-night variants |
| [Budget](docs/budget.html) | Every line with its source and whether it is verified, derived or deliberately blank |
| [Questions](docs/questions.html) | 26 decisions: what we have, what is missing, how to discover it |
| [Suggestions](docs/suggestions.html) | 12 proposed improvements with effort, impact, risk and a decision field |
| [Flagged](docs/flagged.html) | 21 irregularities with severity and the source that would close each |
| [Method & sources](docs/method.html) | Every source URL, what failed, the travel model's assumptions, the build's own checks |
| [Repo review](docs/repo-review.html) | What this repository contained, what was wrong with it, and verification counted rather than claimed |

`deepdive/` holds an **earlier, independent dataset** from a previous session. It is kept so that work is
not lost but is **not** canonical: it disagrees with this site on the star count, the hotel shortlist and
the transit method. See suggestion S-01.

---

## Build

Standard library only. No dependencies, no network access needed at build time.

```bash
python3 build_site.py
```

Writes `docs/*.html` and `docs/assets/style.css`. The generator **fails the build** (non-zero exit) if:

- any internal link points at a file that does not exist,
- a template token or escaped markup leaks into the output,
- a page contains a placeholder link that goes nowhere,
- two elements share an id,
- a table row has a different number of cells than its header, or
- the budget's stated subtotal does not equal the sum of its priced lines.

`build.py`, `build_deepdive.py` and `content.py` belong to the earlier dataset and are left untouched.

---

## Data

Everything the site renders lives in `site_data/`, one file per concern. Edit the JSON, re-run the build.

| File | Contents |
|---|---|
| `michelin_roster.json` | 72 star entries: name, stars, Green Star, cuisine, borough, MICHELIN URL. Counts: 5 three-star, 15 two-star, 52 one-star |
| `restaurant_details.json` | Per-venue detail keyed by MICHELIN URL slug: hours (+ `hours_status`), address, price band, menu price (+ `price_source`, `price_note`), coordinates |
| `hotels.json` | 7 hotels: room, bed, bathroom, breakfast, `total_7n_usd` (before tax), `city_tax_per_night`, `all_in_7n_usd` (derived), cancellation, `reach`, `address`, source URL; plus `price_windows` and `recheck_2026_11_26` with dated source links |
| `activities.json` | 11 activities: hours, days, exceptions, price per adult and for two, official URL, verification level |
| `social.json` | Social accounts keyed by venue/activity id. Each entry has `kind`: `official`, `review` or `search`. **Only `official` and `review` may be rendered as an account** |
| `framework.json` | The plan itself: trip dates, requirement checklist, budget lines, three itineraries, flags, questions, suggestions |

### Two fields to understand before editing

- **`hours_status`** — `VERIFIED`, `PARTIAL` (only some days could be read) or `UNVERIFIED`. A block that
  was not read from a page must not be filled in. Six venues carry `UNVERIFIED` deliberately.
- **`all_in_7n_usd`** — the printed total times 1.1475 plus the city tax printed on that room row
  ($4/night except $6 at Residence Inn FiDi) and any other excluded per-night fee. **Every** advertised
  total is before tax. This column is derived arithmetic, not a quote.

---

## Known limits, stated plainly

| Limit | Where it is recorded |
|---|---|
| MICHELIN publishes a new New York list on **14 December 2026**, before the trip | F-01 |
| MICHELIN's ceremony article (72 entries) and its own live filter (69) disagree | F-02, Q-17 |
| Hotel prices are live snapshots; four cheapest qualifying rates changed between 25 and 26 Nov 2026 | F-03, F-22 |
| Gramercy Tavern ($178 seasonal menu), AMNH ($37 standard adult) and Jungsik's address were added from official pages on 26 Nov 2026 | Budget, Restaurants, Activities |
| The one-hour travel rule is **modelled from straight-line distance, not measured** | F-05, Q-19 |
| 70 of 72 restaurants have no verified hours; 68 have no verified menu price | `repo-review.html` counts them |
| TikTok returned HTTP 400 on every read, so no TikTok account is asserted anywhere | F-07 |
| The Met's hours come from an official page excerpt only (row stays PARTIAL); The High Line's winter hours are verified | F-09 |
| Flights are a fare, not a quote for two seats | F-15 |
| The published $1,155.48 Fairfield total was withdrawn: the dated source says "Total before taxes $985.60" | F-17, F-23 |

---

## Licence and attribution

No licence file is present; that decision belongs to the repository owner. Star data is attributed to the
MICHELIN Guide, hotel prices to Booking.com, fares to KAYAK and Google Flights, transit to the MTA, and
each venue's hours and prices to the venue itself. Every page footer repeats that prices are
point-in-time snapshots that must be re-checked before booking.

---

## Verification addendum — 26 November 2026

A second line-by-line read of the dated Booking.com property pages changed one recommendation figure
and exposed pricing drift. Both are recorded on the site; nothing was silently overwritten.

| Check | What the official page said | Change made |
|---|---|---|
| [Fairfield, 15–22 Feb](https://www.booking.com/hotel/us/fairfield-inn-suites-by-marriott-new-york-manhattan-central-park.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD) | "Total before taxes $985.60"; "Excluded: 14.75 % TAX, $4 City tax per night" | Withdrawn $1,155.48 "taxes included" figure. Advertised $985.60, derived all-in $1,158.98. Budget subtotal $4,110.98. |
| [Residence Inn FiDi](https://www.booking.com/hotel/us/residence-inn-new-york-downtown-manhattan-financial-district.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD) | "Total before taxes $1,097.25"; "Excluded: 14.75 % TAX, $6 City tax per night" | Rounded $1,097.00 corrected to $1,097.25; city tax is $6/night here, not $4. All-in $1,301.09. |
| [Arlo SoHo](https://www.booking.com/hotel/us/arlo-soho.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD), [Arlo Midtown](https://www.booking.com/hotel/us/arlo-midtown.html?checkin=2027-02-15&checkout=2027-02-22&group_adults=2&no_rooms=1&selected_currency=USD) | $1 tourism fee per night excluded, $37 resort fee per night included | All-in columns now include the tourism fee and state that the resort fee is included on the hotel page. |
| [The High Line](https://www.thehighline.org/visit/) | "December 1 – March 31: 7am to 8pm"; Rail Yard Preserve closes at dusk | Winter hours and exception published, source linked. |
| [OPM federal holidays](https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/) | 2027 table lists Monday 15 February as Washington's Birthday | The holiday claim is now sourced, not derived from a calendar. |
| Four hotel pages re-read | Cheapest qualifying rates differ from the 25 Nov snapshot | Published in the *Price re-check: 26 November 2026* table on the Hotels page; ranking still uses the consistent 25 Nov snapshot. |

`docs/methodology.html` and `docs/data/build_summary.json` were left over from an earlier build and
contradicted the current data; they were removed. The repo review page already recorded their removal.

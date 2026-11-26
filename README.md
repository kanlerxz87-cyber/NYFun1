# NYC 2027 — trip-planning dashboard

A source-linked plan for **two adults visiting New York City in February 2027**. The preferred date window, **15–18 February**, is three hotel nights; the recommended **15–22 February** plan is seven nights so it satisfies the brief’s 1–2-week duration. The site keeps those options distinct, shows dated hotel rates and activity details, and records what remains unmeasured or unresolved.

**Live site:** https://kanlerxz87-cyber.github.io/NYFun1/

---

## Research rules

1. **Read it or leave it blank.** A value appears only when a linked source supports it; unavailable fields remain blank with the reason stated.
2. **Never infer.** No typical prices or assumed opening hours. Any indirectly referenced social handle is labelled unconfirmed rather than marked as verified.
3. **Separate awards from listings.** A MICHELIN star is an award; a Guide-listed venue without a star is a different category.
4. **Label arithmetic.** Derived amounts show their inputs and are not presented as quotes.
5. **Keep disagreements visible.** The 2025 MICHELIN ceremony roster and current filtered lists have different totals; both dated views are shown.
6. **Date each snapshot.** The hotel rates, current MICHELIN filter counts, and refreshed activity records are dated 2026-11-26. Restaurant detail and social records retain their own earlier source dates; the site-generation date does not imply every source was reread that day.

Anything unresolved is recorded on [Flagged](docs/flagged.html); open decisions are on [Questions](docs/questions.html).

---

## Pages

| Page | What it answers |
|---|---|
| [Overview](docs/index.html) | Seven-night recommendation, three-night preferred-date option, hotel fee comparison, MICHELIN snapshot, and remaining limits |
| [Hotels](docs/hotels.html) | Seven dated room offers, addresses, cancellation terms, Booking-line and statutory-component calculations, weekly snapshots, and a clearly labelled proximity proxy |
| [MICHELIN](docs/restaurants.html) | The 72-entry 2025 ceremony roster, current-filter count difference, hours, menu-price values, and social links where verified |
| [Activities](docs/activities.html) | Eleven activities with official details where captured and a clear distinction between modelled and unmeasured travel |
| [Itinerary](docs/itinerary.html) | Day-by-day 7-night plan, exact 3-night preferred-date option, and 14-night alternative |
| [Budget](docs/budget.html) | Priced items for two adults; the subtotal is incomplete and explicitly excludes ordinary meals and other discretionary spending |
| [Questions](docs/questions.html) | Twenty-six decisions, current information, missing evidence, and how to check it |
| [Suggestions](docs/suggestions.html) | Twelve possible improvements with effort, impact, risk, and a decision field |
| [Flagged](docs/flagged.html) | Open, documented, and resolved audit records with status and next steps |
| [Method & sources](docs/method.html) | Source dates, fee formulas, travel-model limits, and legacy-build caveat |
| [Repo review](docs/repo-review.html) | Counted coverage, current repository findings, and verification steps |

`deepdive/` is a separate, earlier dataset with its own builder and sources; it is not merged into this dashboard. The active dashboard uses `site_data/` and `build_site.py`.

---

## Build

Standard-library Python only; no network access is required to generate the dashboard.

```bash
python3 build_site.py
```

The generator writes the 11 canonical pages into `docs/` and checks:

- hotel Booking-line and statutory-component calculations against the raw rate/fee inputs;
- that the priced budget subtotal equals the sum of its priced lines and each priced line has a source;
- property-specific, date-specific Booking.com hotel URLs and official restaurant/activity source links;
- the special ferry constraint for Liberty Island (no invalid land-mode journey);
- internal links, duplicate element IDs, leaked template/escaped markup, and table row widths.

The older `python3 build.py` is not the dashboard build. It currently stops because `docs/data/michelin_2025.csv` is absent; when invoked in the old chained command, `build_deepdive.py` does not run after that failure.

---

## Source data

All active dashboard source data is in `site_data/`:

| File | Contents |
|---|---|
| `michelin_roster.json` | 72 star entries from the 2025 ceremony article, plus dated current filter counts of 5 three-star, 14 two-star, and 50 one-star |
| `restaurant_details.json` | Restaurant details keyed by MICHELIN URL slug; blank hours/prices are not guessed |
| `hotels.json` | Seven rooms, current Booking.com rate snapshots, street addresses, fee inputs, two derived seven-night calculations, and four Fairfield weekly date windows |
| `activities.json` | Eleven activities, official hours/prices where captured, source URLs, and modelled or explicitly unmeasured travel fields |
| `social.json` | Directly verified official accounts, one explicitly unconfirmed social reference, individual reviews, and labelled platform-search links; searches are never presented as accounts |
| `framework.json` | Trip dates, requirements, budget lines, itineraries, flags, questions, and suggestions |

### Hotel calculations

For a base room total `B`, seven nights, a 14.75% displayed tax, Booking fixed fee `F`, and any separately listed tourism fee `T` per night:

- **Booking-line estimate:** `round(B × 1.1475 + 7 × (F + T), 2)`
- **Statutory-component calculation:** `round(B × 1.1475 + 7 × ($3.50 + T), 2)`

NYC Finance’s fixed hotel-occupancy component is $2/night for rooms at $40+, and NYS lists a separate $1.50/night unit fee. Booking.com displays $4/night on six rows and $6/night for Residence Inn FiDi. The discrepancy is unresolved; both calculations are shown, and neither is a final checkout quote. Resort fees that Booking.com says are already included remain in the selected room rate.

### Travel-time limitation

Activity times (except the Statue of Liberty) are rough straight-line/speed models, not MTA itineraries. The hotel table's 5 km reach column is a straight-line comparison radius only; it does not estimate journey time or establish a one-hour route. Only seven of the 72 restaurant entries have captured coordinates, and six hotel points remain area-level. Liberty Island requires an authorized ferry; its February 2027 sailing schedule and complete journey time were not verified. **No complete measured one-hour route matrix is available.**

---

## Known limits

| Limit | Record |
|---|---|
| The 2026 Northeast Cities MICHELIN ceremony, including New York, is scheduled for **14 December 2026**, before the trip | F-01 |
| The 2025 ceremony article has 72 entries; current MICHELIN filters show 69 (5/14/50). A name-by-name comparison remains open | F-02, Q-17 |
| Hotel prices are live snapshots; cancellation terms and promotional rates vary | F-03 |
| Booking.com’s fixed nightly fee labels differ from the $3.50/night NYC/NYS statutory components | F-04 |
| The one-hour rule is not measured; activity minutes are estimates and the Liberty Island ferry is not timed | F-05, F-20, Q-19 |
| Restaurant menu-price coverage is incomplete; blanks are intentional | F-06 |
| Standard Met, AMNH, High Line, and Chelsea Market details were refreshed; temporary February 2027 notices still need a later check | F-09, Q-09 |
| Four weekly Fairfield samples do not establish a daily price curve or combined 14-night checkout total | F-12 |
| Six hotel proximity coordinates remain area-level even though all seven street addresses are now captured | F-13 |
| The fare snapshot is one adult; doubling it is not a two-seat booking | F-15 |
| TikTok could not be verified; no TikTok account is asserted | F-07 |
| The Chelsea Market Instagram handle was referenced by the verified High Line account, but its own profile was not opened; the link is labelled unconfirmed | F-08 |

---

## Attribution

No licence file is present; that decision belongs to the repository owner. MICHELIN data is attributed to the MICHELIN Guide, hotel rates to Booking.com, activity hours and prices to the linked venues or government pages, MTA fares to the MTA, and the federal-holiday date to OPM. All prices and schedules are point-in-time records and should be rechecked before booking or travel.

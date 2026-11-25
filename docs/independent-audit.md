# Independent static integrity audit

**Audit date:** 25 November 2026 (UTC)  
**Scope:** local repository only — generated HTML and checked-in CSV/JSON.  
**Important limit:** this pass did **not** fetch external pages or re-confirm prices, hours, opening days, Michelin distinctions, or social-video content. The existing source URLs are preserved for manual review; a URL in a cell is not proof that its current content was re-read.

## Executive result

The build is reproducible and the local site is structurally sound, but the strict requirement that every dining, hotel, and activity table row be supported by a meaningful source link is **not met**. In particular, the main Michelin roster has 66 star rows without a restaurant/MICHELIN source link, and the main hotels page includes a 24-row modelled travel screen whose map links are not verification sources. Social coverage is mostly discovery searches and hashtags, not individual review content.

| Check | Result | Meaning |
|---|---:|---|
| Generated HTML pages | 21 | Root + `docs/` + `deepdive/` |
| Broken local links or missing local anchors | 0 | Static link check only; no external URL status check |
| Pages with mobile viewport metadata | 21 / 21 | Presence check, not device/browser testing |
| `docs/activities.html` rows with non-social external link | 12 / 12 | Presence only; the activity row is not independently reverified by this audit |
| `docs/restaurants.html` rows with non-social external link | 13 / 79 | **66 rows have only discovery links/no restaurant or MICHELIN source link** |
| `docs/hotels.html` rows with a source other than a social/map utility | 7 / 31 | Four hotel quotes + three date-window quotes are linked; 24 modelled route rows are not backed by an official transit source |
| `deepdive/restaurants.html` rows with non-social external link | 42 / 42 | Presence only; links and data still need live source re-check |
| `deepdive/hotels.html` rows with non-social external link | 14 / 14 | Presence only; links and data still need live source re-check |
| Platform URLs rendered across the site | 321 | URL count, not a count of independently verified reviews |
| YouTube search / TikTok search / Instagram hashtag links | 97 / 101 / 91 | **289 discovery links**, not direct reviews |
| Direct social post/video/profile URLs | 32 | 27 YouTube video URLs + 5 Instagram post/profile URLs; content and relevance were not checked in this pass |

The main restaurant table covers the 72-entry Michelin roster and seven guide-listed examples; it has 79 data rows. Only 13 rows have a non-social external link (the six detailed starred entries plus the seven guide-listed examples). The remaining 66 are roster-only. Their verification column says “roster only,” but the rendered “Official link” cell is blank. Do not treat the generated YouTube/TikTok searches or Instagram hashtags as a restaurant source.

## Specific issues for the integration/research owner

### A. Add per-row Michelin evidence or leave the row out of a verified directory

- `docs/data/michelin_2025.csv`: 66 of 72 rows have an empty `michelin_url` value; the names still render in `docs/restaurants.html` with a blank official-link cell.
- Relevant official citation currently recorded in the board: [MICHELIN 2025 New York star roster](https://guide.michelin.com/us/en/article/michelin-guide-ceremony/all-the-stars-in-the-michelin-guide-to-new-york-city-2025).
- Next action: re-read each Michelin listing and enter its exact detail URL, or visibly cite the shared official roster article on each row while making clear it is a roster citation (not an individual venue page). Do not synthesize URL slugs.
- While editing, re-check whether the 2025 star awards are still current for February 2027. The board already notes that a 2026 edition may be released before travel.

### B. Separate social discovery links from actual social reviews

- The current generated links provide broad YouTube and TikTok searches and Instagram tag pages for many entries. They are useful for discovery but are not the requested “social media that are reviewing” links.
- The 32 direct links are a mix of videos and account/post URLs; this audit did not watch or read them, so it cannot establish that any is a review of the named venue/activity.
- Next action: keep an entry only after opening it and confirming the venue/activity match; record platform, creator/title, URL, and date checked. If no qualifying content is found, say “no verified review link found” rather than implying the search page is a review.

### C. Distinguish real transit evidence from travel-time models

- The main hotel page contains 24 modelled hotel-to-restaurant route rows. Their “MTA / maps check” links point to Google Maps; they are route-planning utilities, not official MTA sources or evidence that the printed model minutes are correct.
- The deep dive has nine measured legs, but `deepdive/data/transit.json` stores no per-leg source URL. Its general router/GTFS method is not an independently checkable itinerary citation for each row.
- The primary dashboard already labels its minutes as MODEL; retain that warning. For the ≤60-minute decision, replace or supplement the model with a dated route from an official MTA trip-planning source, including the date/time tested and any walk/wait/transfer components. Otherwise leave the journey-time cell blank and flagged.

### D. Treat hotel prices as dated quotes, not a booking-time forecast

- The main hotel data provides four quoted properties and three date windows, sourced to Booking.com URLs captured 25 November 2026. The deep-dive data uses Michelin hotel pages and a different shortlist/price basis. These are separate samples and cannot be merged as though comparable.
- The evidence supports “lowest price among the sampled stay windows on the capture date,” not “cheapest time to book” or the cheapest stay across every eligible date through 23 March 2027.
- Before a booking decision, re-quote identical room requirements (2 adults, queen/king, private bathroom, same 7-night dates, same cancellation terms) across the eligible date range and compare a displayed **tax/fee-inclusive** stay total. Preserve the exact date, time, currency and room/rate details.

### E. Maintain separate Michelin counts until reconciled against the same official release

- `docs/` reports 72 entries from the 2025 ceremony article (5/15/52); `deepdive/` reports 69 from live filter counts (5/14/50). The discrepancy is already disclosed in `COORDINATION.md` and must not be silently reconciled.
- Before publishing a single “current” count, capture the same official edition/listing, date, filters and borough scope. Keep the 2025 ceremony roster distinct from live distinctions and from Guide-listed/no-star entries.

## Reproduction

From the repository root:

```sh
python3 build.py
python3 build_deepdive.py
python3 tools/audit_site.py
```

The audit script checks local HTML references/anchors, viewport metadata, source-link presence in the selected listing tables, and whether checked-in data rows carry URL fields. It exits `0` only when structural checks pass **and** source coverage is complete; it exits `2` for the current known source gaps (or `1` for local structural failures). It intentionally **does not** claim that an external page is reachable, official, or consistent with a value in the table.

## Files reviewed

- Main source tables: `docs/data/activities.csv`, `docs/data/hotels.csv`, `docs/data/date_windows.csv`, `docs/data/michelin_2025.csv`, `docs/data/guide_listed.csv`.
- Deep-dive evidence: `deepdive/data/activities.json`, `deepdive/data/hotels.json`, `deepdive/data/restaurants.json`, `deepdive/data/transit.json`, `deepdive/data/michelin.json`.
- Generated pages: root `index.html`, `docs/*.html`, and `deepdive/*.html`.

See the on-site [Flagged for review](flagged.html), [Open questions](questions.html), [Methodology](methodology.html), and [Deep dive verification log](../deepdive/review.html) for the source registers and existing caveats.

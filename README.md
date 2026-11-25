# NYFun1 - NYC Trip Planning (Feb-Mar 2027)

Planning repository for a 1-2 week New York City vacation for 2 adults, with preferred dates **2027-02-15 to 2027-02-18** (window: 2027-02-15 to 2027-03-23).

## Live Site
GitHub Pages site (after publish): `docs/` directory contains the static site.

## What’s in this repo
- `docs/` - GitHub Pages static site (landing page + subpages)
- `data/` - structured data used by the site (CSV/JSON)
- `COORDINATION.md` - shared task board for parallel agent sessions
- `VERIFICATION.md` - verification log, sources, and irregularities

## Key constraints (from request)
- 2 adults, 1-2 weeks, window 2027-02-15 to 2027-03-23; preferred 2027-02-15 to 2027-02-18.
- Hotels: private bathroom, queen bed or equivalent/bigger. Rank by Michelin-star/guide restaurant density within ~1 hour subway/bus.
- Michelin restaurants: distinguish Michelin-starred vs Michelin Guide listed/selected; include hours/days/exceptions where verifiable; include cost for 2 adults; include official/social links.
- Activities/restaurants: include YouTube/TikTok/Instagram links where found; include official link.
- No hallucinations. Every table row must have official source link; unverifiable values left blank and flagged.
- Work on current branch; coordinate via `COORDINATION.md`.

## Status
In progress - research, verification, and site build underway on branch `arena/0558efa5-nyfun1`.

# NYFun1 — NYC Trip Planner (Feb–Mar 2027)

Planning workspace for a 2-adult New York City trip (preferred **2027-02-15 to 2027-02-18**, within **2027-02-15 to 2027-03-23**). The repo contains a static GitHub Pages site in [`docs/`](docs/) with hotels, Michelin restaurants, activities, executive summary, questions/gaps, suggestions, and verification logs.

## Live Site (GitHub Pages)

After enabling GitHub Pages for this repository:
1. Go to **Settings → Pages**.
2. Set **Source** to “Deploy from a branch”.
3. Select branch `main` (or the active integration branch) and folder `/docs`.
4. Save. The site will be served from `https://<owner>.github.io/NYFun1/`.

Local preview:

```bash
python3 -m http.server 8000 --directory docs
# open http://localhost:8000
```

## What’s Included

- **[Dashboard](docs/index.html)** — scope, caveats, navigation.
- **[Hotels](docs/hotels.html)** — candidate hotels evaluated for private bathroom, queen+ bed, 2 adults, Midtown/Michelin access, and 7-night pricing (pricing flagged where unverified).
- **[Michelin Restaurants](docs/restaurants.html)** — starred restaurants with Michelin status, hours, address, website, estimated cost for 2 adults, social/video links, and source links.
- **[Activities](docs/activities.html)** — activities with official links, hours/pricing verification placeholders, and social/video links.
- **[Executive Summary](docs/summary.html)** — key findings and decision rule.
- **[Questions & Gaps](docs/questions.html)** — blocking questions, missing info, and discovery methods.
- **[Suggestions](docs/suggestions.html)** — review-before-implement improvements.
- **[Verification & Flags](docs/verification.html)** — verification log, irregularities, and unresolved blockers.

## Verification Policy

- Every table row should have an official source link. If a value cannot be confirmed from an official source, it is left blank/marked **Unverified**.
- No hallucinated prices, hours, or availability. Transit times are estimates unless backed by dated route evidence.
- Michelin star status was checked against [Michelin Guide NYC restaurant pages](https://guide.michelin.com/us/en/new-york-state/new-york/restaurants) on 2026-11-25; re-verify before booking.

## Coordination

See [`COORDINATION.md`](COORDINATION.md) for task ownership, status, file scopes, and handoff log. Multiple agent sessions should claim tasks before editing.

## Key Blocking Gaps (as of 2026-11-25)

- **Hotel 7-night totals for Feb 15–Mar 23, 2027:** not verified from official booking sources.
- **Cheapest upcoming time to book:** not verified; requires dated price tracking.
- **Transit pairwise durations:** estimates only; need dated MTA/Google Maps captures.
- **Restaurant 2-adult totals:** estimates only; need official menu pricing.

## Repo Structure

```text
NYFun1/
  COORDINATION.md
  README.md
  docs/
    index.html
    hotels.html
    restaurants.html
    activities.html
    summary.html
    questions.html
    suggestions.html
    verification.html
    css/style.css
    js/main.js
    .nojekyll
```

# NYC trip plan — 15–22 February 2027

A verified seven-night New York plan for two adults: hotels priced to the cent, the Michelin picture
separated into starred versus merely listed, six attractions with real hours and admission, and
measured door-to-door transit times.

**Read it at:** `index.html` (the site is served from the repo root by GitHub Pages).

## The rule this repo is built on

> A value is **verified** when it was read off a page belonging to the venue, the agency that runs it,
> or the Michelin Guide, and that page's URL is recorded next to it. Otherwise the value is **blank**
> and tagged `unverified`.

No estimates, no inferred hours, no "typical" prices, no recalled facts. The
[questions register](questions.html) lists every gap and how to close it; the
[verification log](review.html) lists every irregularity found in the official sources themselves.

## Pages

| Page | What is in it |
|---|---|
| `index.html` | Executive summary, KPI grid, the three decisions that matter, 7-day shape, budget |
| `hotels.html` | 10 rooms quoted for 7 nights, seasonality test across four 2027 windows |
| `restaurants.html` | 69 starred rooms, 10 with menus and prices, star-vs-listing separation |
| `activities.html` | Met, Cloisters, MoMA, PS1, Statue of Liberty, Top of the Rock, The High Line |
| `transit.html` | 9 measured legs, cluster screen, fares |
| `questions.html` | 14 unknowns, each with a route to an answer |
| `suggestions.html` | 10 recommendations, deliberately kept apart from the data |
| `review.html` | Sources, 12 irregularities, 10-link manual review checklist |
| `methodology.html` | Conventions, verification rule, how to rebuild |

## Repo layout

```
index.html … methodology.html   generated pages (do not hand-edit; regenerate)
assets/style.css                the only stylesheet, no framework, no external requests
data/hotels.json                hotel quotes + seasonality test
data/michelin.json              star / Bib / Selected inventory
data/restaurants.json           per-restaurant menus, prices, hours, links, videos
data/activities.json            attraction hours, admission, closures, rules
data/transit.json               measured legs, cluster screen, fares
build.py                        stdlib-only generator: data/*.json → *.html
docs/README-sources.md          source hierarchy and conventions
COORDINATION.md                 parallel-session task board and handoff rules
```

## Rebuilding

```
python3 build.py
```

Standard library only — no `pip install`, no build step, no lockfile. Editing a JSON file and re-running
propagates the change to every page that uses it.

## Known gaps (deliberate)

- Eleven Madison Park and Gramercy Tavern opening hours — not published on any official page read.
- Jungsik's open days — not published anywhere official.
- Per Se, Atera and Sushi Sho menu prices — not published.
- The Met's and MoMA PS1's hours — the Met's hours module would not render across three URL attempts.
- Statue of Liberty ferry fare — NPS publishes park hours, the concessioner publishes the fare; only the former was read.
- No travel-time matrix — the routing API's batch endpoint failed, so only 9 legs are measured.

Each of these has an entry in `questions.html`.

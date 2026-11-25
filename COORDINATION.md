# COORDINATION.md — Shared Task Board

Repo: kanlerxz87-cyber/NYFun1 · Trip Planning New York (Feb 15 – Mar 23, 2027 window)

Sessions must read this file before starting work, claim a task by writing their session ID +
file scope below, commit and push the claim immediately, and never start a task another
session has claimed. Status values: `unclaimed`, `in progress`, `needs review`, `done`.

## Session log

| Session ID | Branch | Role | Started (UTC) |
|---|---|---|---|
| arena-11af0476 | `arena/11af0476-nyfun1` | Bootstrap, research, site build and publish | 2026-11-25 |

> Note on branch naming: this session is bound to `arena/11af0476-nyfun1` by the Arena
> harness and may not create or switch branches. That branch is this session's exclusive
> scope; the convention `session-<id>/<task>` is satisfied in spirit (one session = one
> branch = one file scope).
>
> **Publishing note.** GitHub Pages for this repo uses the legacy source `main:/` (the repo
> root of `main`). Work happens on `arena/11af0476-nyfun1`; the site only goes live when that
> branch is merged into `main`. The pages were generated at the repo root deliberately so
> that the merge is the whole publish step — no `docs/` prefix, no `gh-pages` branch.

## Task board

| ID | Task | Status | Owner | File scope |
|---|---|---|---|---|
| T1 | Repo review + irregularities log | done | arena-11af0476 | `review.html`, `build.py` |
| T2 | Michelin star / Bib / Selected dataset (official Michelin pages) | done | arena-11af0476 | `data/michelin.json` |
| T3 | Hotel shortlist + verified 7-night pricing (Feb 15–22, 2027) + seasonality | done | arena-11af0476 | `data/hotels.json` |
| T4 | Cluster ranking (stars reachable per hotel) | **needs review** — measured legs + labelled straight-line screen only; the routing API's one-to-all endpoint failed, so no ≤60 min matrix | arena-11af0476 | `data/transit.json` |
| T5 | Activities dataset + hours + social links | done | arena-11af0476 | `data/activities.json` |
| T6 | Open questions / information-gap register | done | arena-11af0476 | `questions.html`, `build.py` |
| T7 | Suggestions register (decision paths, not implemented) | done | arena-11af0476 | `suggestions.html`, `build.py` |
| T8 | Static site (landing + category subpages, mobile-first) | done | arena-11af0476 | `*.html`, `assets/style.css`, `build.py` |
| T9 | Verification pass + publish to GitHub Pages | in progress — needs the merge to `main` | arena-11af0476 | `README.md`, `data/**` |

## Session log of changes

- 2026-11-25 · arena-11af0476 · Bootstrapped the board, wrote the source hierarchy doc.
- 2026-11-25 · arena-11af0476 · Built `data/*.json` (hotels, Michelin, restaurants, activities, transit)
  and `build.py`, which generates all nine pages at the repo root.
- 2026-11-25 · arena-11af0476 · **Scope change:** the site moved from `site/**` to the repo root, because
  Pages serves `main:/` and a root build makes the merge the entire publish step. Any session that
  claimed `site/**` must use the root paths instead.

## Claim / handoff rules in force

- One session owns this branch. Any second session must announce itself here first and
  take a task ID above; do not edit files outside the scope you claim.
- **Generated files are not hand-edited.** `index.html` … `methodology.html` are outputs of
  `build.py`; correct the JSON in `data/` and re-run the generator, or the next build will
  discard the edit.
- Shared outputs (the pages, the nav in `build.py`, `COORDINATION.md`) are integration-owned.
- If a claim is >60 min old with no commits, another session may take over and must log the handoff.

## Open requests to any future session

| Request | Why | Suggested scope |
|---|---|---|
| R1 | Produce the ≤60 min travel-time matrix (T4) | 10 hotels × 69 starred rooms against a routing engine with batch isochrone support; write `data/clusters.json` |
| R2 | Fill the four missing hours tables | EMP, Gramercy Tavern, Jungsik open days, the Met, MoMA PS1 — all need a browser that renders client-side widgets |
| R3 | Price Per Se, Atera and Sushi Sho | Open a live booking flow for a February date; the price appears at the payment step |
| R4 | Add the remaining 1★ detail rows | 40 of the 50 one-star rooms have no price/hours/video yet; `data/michelin.json` has the names and slugs |
| R5 | 9/11 Memorial & Museum | `911memorial.org` failed to load repeatedly; needs its own session before it can join `activities.json` |

# COORDINATION.md — Shared Task Board

Repo: kanlerxz87-cyber/NYFun1 · Trip Planning New York (Feb 15 – Mar 23, 2027 window)

Sessions must read this file before starting work, claim a task by writing their session ID +
file scope below, commit and push the claim immediately, and never start a task another
session has claimed. Status values: `unclaimed`, `in progress`, `needs review`, `done`.
`needs review` items are published on the site's Flagged for Review page and block nothing.

## Session log

| Session ID | Branch | Role | Started (UTC) |
|---|---|---|---|
| arena-11af0476 | `arena/11af0476-nyfun1` | Bootstrap + research + site build (all tasks below) | 2026-11-25 |

> Note on branch naming: this session is bound to `arena/11af0476-nyfun1` by the Arena
> harness and may not create or switch branches. That branch is this session's exclusive
> scope; the convention `session-<id>/<task>` is satisfied in spirit (one session = one
> branch = one file scope).

## Task board

| ID | Task | Status | Owner session | File scope |
|---|---|---|---|---|
| T1 | Repo review + irregularities log | in progress | arena-11af0476 | `docs/repo-review.md` |
| T2 | Michelin star / Bib / Selected dataset (official Michelin pages) | in progress | arena-11af0476 | `data/michelin.json`, `docs/sources-michelin.md` |
| T3 | Hotel shortlist + verified 7-night pricing (Feb 15–22, 2027) | in progress | arena-11af0476 | `data/hotels.json`, `docs/sources-hotels.md` |
| T4 | Cluster ranking (stars within ≤60 min transit of each hotel) | in progress | arena-11af0476 | `data/clusters.json` |
| T5 | Activities dataset + social links + hours | in progress | arena-11af0476 | `data/activities.json` |
| T6 | Open questions / information-gap register | in progress | arena-11af0476 | `docs/questions.md` |
| T7 | Suggestions register (decision paths, not implemented) | in progress | arena-11af0476 | `docs/suggestions.md` |
| T8 | Static site (landing + category subpages, mobile-first) | in progress | arena-11af0476 | `site/**` |
| T9 | Verification pass + publish to GitHub Pages | in progress | arena-11af0476 | `site/**`, `.github/workflows/**`, `README.md` |

## Claim / handoff rules in force

- One session owns this branch. Any second session must announce itself here first and
  take a task ID above; do not edit files outside the scope you claim.
- Shared outputs (`site/index.html`, nav, `COORDINATION.md`) are integration-owned.
- If a claim is >60 min old with no commits, another session may take over and must log the handoff.

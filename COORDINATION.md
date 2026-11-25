# COORDINATION.md — Shared Task Board

**Repo:** kanlerxz87-cyber/NYFun1  
**Current integration branch:** `arena/a095530f-nyfun1` (this Arena session branch)  
**Last updated:** 2026-11-25T00:00:00Z (ses-a095530f)

## Rules
- Claim a task by writing your session ID and file scope, then commit and push the claim immediately. Never start a task another session has claimed.
- Keep scopes non-overlapping. If you need a file owned by another session, log a request here.
- Status values: `unclaimed | in-progress | done | needs-review | blocked`.
- `needs-review` means published on Flagged for Review page; does not block other tasks.
- Never mark anything verified without checking it against an official source and linking that source.
- Shared outputs (site index/navigation/data merge) changed only by final integration session after all tasks done.
- Stale claim takeover: if claim >60 min old with no commits, another session may take over and note handoff.

## Session Registry
| Session ID | Branch | Started (UTC) | Last heartbeat (UTC) | Notes |
|---|---|---|---|---|
| ses-a095530f | arena/a095530f-nyfun1 | 2026-11-25T00:00:00Z | 2026-11-25T00:00:00Z | Primary session; full scope claim below (repo currently empty/single session). |

## Task Board

| Task ID | Task | Status | Owner | Files/Scope | Depends On | Notes |
|---|---|---|---|---|---|---|
| T1 | Repo audit & coordination setup | in-progress | ses-a095530f | `COORDINATION.md`, `README.md` | - | Initial audit complete; repo had only README.md. |
| T2 | Research: NYC hotels (price/location/amenities, private bath, queen+ bed, 2 adults) | in-progress | ses-a095530f | `data/hotels.*`, `docs/data/*`, research notes in `research/` | T1 | Verify real pricing & availability for Feb 15-Mar 23 2027 window; identify cheapest 7-night bookable window. |
| T3 | Research: Michelin Guide NYC restaurants (stars vs listed), clusters, costs for 2 | in-progress | ses-a095530f | `data/restaurants.*`, `docs/data/*`, `research/` | T1 | Must distinguish Michelin-starred vs Michelin-selected/listed. Include hours/days, links, social links. |
| T4 | Map restaurants to hotels by <=60 min subway/bus; rank hotels | in-progress | ses-a095530f | `data/hotel_rankings.*`, `docs/data/*`, `analysis/` | T2,T3 | Use verifiable transit estimates; flag assumptions. |
| T5 | Activities research with links, hours, social | in-progress | ses-a095530f | `data/activities.*`, `docs/data/*` | T1 | Within ~1h travel of candidate hotel areas where possible. |
| T6 | Executive summary, questions/missing info, suggestions | in-progress | ses-a095530f | `docs/summary.*`, `analysis/summary.md`, `docs/suggestions.*` | T2-T5 | Must clearly separate confirmed vs unverified. |
| T7 | GitHub Pages site (landing + subpages, mobile-friendly, tables) | in-progress | ses-a095530f | `docs/**`, `.github/workflows/pages.yml` (if needed), site assets | T2-T6 | Clean dashboard UI; all entries in tables; source links per row. |
| T8 | Verification pass, flagged irregularities, final integration/publish | in-progress | ses-a095530f | All files (integration owner) | T1-T7 | Line-by-line verification; no unverified values presented as confirmed. |

## File Scope Claims (active)
| Session | Scope (exclusive write) |
|---|---|
| ses-a095530f | Entire repo (sole active session at claim time). Will respect any future claims logged before its next pull. |

## Requests / Cross-session Notes
| Time (UTC) | From | To | Request | Status |
|---|---|---|---|---|

## Log
| Time (UTC) | Session | Action | Details |
|---|---|---|---|
| 2026-11-25T00:00:00Z | ses-a095530f | claim | Claimed T1-T8; repo audit shows only README.md at 6609129. Working on current branch `arena/a095530f-nyfun1` per system instruction. |

# COORDINATION.md — Shared Task Board

**Repo:** kanlerxz87-cyber/NYFun1  
**Current integration branch:** `arena/a095530f-nyfun1` (this Arena session branch)  
**Last updated:** 2026-11-25T00:30:00Z (ses-a095530f)

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
| ses-a095530f | arena/a095530f-nyfun1 | 2026-11-25T00:00:00Z | 2026-11-25T00:30:00Z | Primary session; created initial site, research tables, verification log. |

## Task Board

| Task ID | Task | Status | Owner | Files/Scope | Depends On | Notes |
|---|---|---|---|---|---|---|
| T1 | Repo audit & coordination setup | done | ses-a095530f | `COORDINATION.md`, `README.md` | - | Repo audited; coordination created; README updated with Pages instructions. |
| T2 | Research: NYC hotels (price/location/amenities, private bath, queen+ bed, 2 adults) | needs-review | ses-a095530f | `docs/hotels.html`, `research/` | T1 | Amenities partially verified (Pod Times Square Queen Pod verified on official rooms page). 7-night totals and cheapest booking window NOT verifiable from official booking sources; flagged as blocking in verification. |
| T3 | Research: Michelin Guide NYC restaurants (stars vs listed), clusters, costs for 2 | needs-review | ses-a095530f | `docs/restaurants.html`, `research/` | T1 | 12 starred restaurants included; 7 fully verified on Michelin pages (status/address/hours/website). Remaining 5 partial. Costs are estimates, flagged. Michelin Selected/Bib not exhaustively cataloged. |
| T4 | Map restaurants to hotels by <=60 min subway/bus; rank hotels | needs-review | ses-a095530f | `docs/hotels.html`, `analysis/` | T2,T3 | Ranking provisional; transit times are estimates only. Needs dated MTA/Google Maps evidence per pair. |
| T5 | Activities research with links, hours, social | needs-review | ses-a095530f | `docs/activities.html` | T1 | 8 activities with official links and social links; hours/pricing require date-specific verification. |
| T6 | Executive summary, questions/missing info, suggestions | done | ses-a095530f | `docs/summary.html`, `docs/questions.html`, `docs/suggestions.html` | T2-T5 | Includes blocking questions, missing-info discovery plan, and review-gated suggestions. |
| T7 | GitHub Pages site (landing + subpages, mobile-friendly, tables) | done | ses-a095530f | `docs/**` | T2-T6 | Static HTML/CSS site in `docs/` with `.nojekyll`. Enable Pages from branch/folder in repo settings. |
| T8 | Verification pass, flagged irregularities, final integration/publish | needs-review | ses-a095530f | `docs/verification.html`, all files | T1-T7 | Verification log created; critical blockers flagged (hotel pricing, booking timing, transit evidence, menu-cost totals). No unverified pricing presented as confirmed. |

## File Scope Claims (active)
| Session | Scope (exclusive write) |
|---|---|
| ses-a095530f | Entire repo (sole active session at claim time). Will respect any future claims logged before its next pull. |

## Requests / Cross-session Notes
| Time (UTC) | From | To | Request | Status |
|---|---|---|---|---|

## Verification / Evidence Notes
| Item | Source | Checked (UTC) | Result | Notes |
|---|---|---|---|---|
| Le Bernardin | https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/le-bernardin | 2026-11-25 | Verified | 3★, address, hours, website captured. |
| The Modern | https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/the-modern | 2026-11-25 | Verified | 2★, address, hours, website captured. |
| Le Coucou | https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/le-coucou | 2026-11-25 | Verified | 1★, address, hours, website captured. |
| Gabriel Kreuther | https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/gabriel-kreuther | 2026-11-25 | Verified | 2★, address, hours, website captured. |
| Per Se | https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/per-se | 2026-11-25 | Verified | 3★, address, hours, website captured. |
| Masa | https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/masa | 2026-11-25 | Verified | 2★, address, hours, website captured. |
| Aquavit | https://guide.michelin.com/us/en/new-york-state/new-york/restaurant/aquavit | 2026-11-25 | Verified | 2★, address, hours, website captured. |
| Pod Times Square Queen Pod amenities | https://www.thepodhotel.com/pod-times-square/rooms | 2026-11-25 | Verified | Queen bed, private bathroom with rain showerhead, sleeps 2. Pricing not verified. |
| Hotel 7-night 2027 pricing | Official hotel booking pages (attempted) | 2026-11-25 | Unverified | Blocking gap; no static official quote captured. |

## Log
| Time (UTC) | Session | Action | Details |
|---|---|---|---|
| 2026-11-25T00:00:00Z | ses-a095530f | claim | Claimed T1-T8; repo audit shows only README.md at 6609129. Working on current branch `arena/a095530f-nyfun1` per system instruction. |
| 2026-11-25T00:10:00Z | ses-a095530f | research | Fetched Michelin Guide NYC starred/restaurant detail pages via web tools; verified 7 restaurant detail pages. |
| 2026-11-25T00:25:00Z | ses-a095530f | build | Created static GitHub Pages site in `docs/` with hotels, restaurants, activities, summary, questions, suggestions, verification pages. |
| 2026-11-25T00:30:00Z | ses-a095530f | verify/publish | Logged verification gaps; marked pricing/transit/cost estimates as unverified. Ready for commit/push. |

# COORDINATION.md

Shared task board for parallel agent sessions.  
**Rule:** Claim a task by writing your session ID and file scope here, commit and push the claim immediately, and never start a task another session has claimed. Keep scopes non-overlapping.

## Session Info
- **Session ID:** `0558efa5`
- **Branch:** `arena/0558efa5-nyfun1` (current/fixed for this session)
- **Base:** `6609129e727bc4a5abd876a2bdf57f1a37b0dd4e` (`main`)
- **Started:** 2026-11-25
- **Last heartbeat:** 2026-11-25 (active)

## Task Board

| Task | Status | Owner | Scope (files/dirs) | Notes |
|------|--------|-------|--------------------|-------|
| Repo review & coordination setup | done | 0558efa5 | `COORDINATION.md`, repo-wide read | Repo was minimal (README only). |
| Requirements/questions/suggestions docs | in progress | 0558efa5 | `docs/planning.html`, `docs/suggestions.html`, `VERIFICATION.md` | Building executive summary, open questions, suggestions. |
| Michelin NYC research & verification | in progress | 0558efa5 | `data/michelin/*`, `docs/restaurants.html` | Using official Michelin Guide 2025 ceremony/listing as primary source. |
| Hotel research & verification | in progress | 0558efa5 | `data/hotels/*`, `docs/hotels.html` | Real 2027 pricing is difficult to verify via static fetch; will flag unverifiable values. |
| Activities/transit clustering analysis | in progress | 0558efa5 | `data/analysis/*`, `docs/analysis.html` | 1-hour subway/bus constraint; will use official transit sources where possible. |
| GitHub Pages site build | in progress | 0558efa5 | `docs/*`, `assets/*`, `.nojekyll` | Static site, mobile-friendly. |
| Final verification & publish | unclaimed | 0558efa5 | repo-wide | Pending data completion; line-by-line verification required. |

## Log

| Timestamp (UTC) | Session | Action | Details |
|-----------------|---------|--------|---------|
| 2026-11-25 | 0558efa5 | Claimed repo review | Created COORDINATION.md; audited repo (README.md only). |
| 2026-11-25 | 0558efa5 | Research started | Fetched Michelin Guide official 2025 NYC ceremony article and starred listing pages. Began hotel/cluster research. |
| 2026-11-25 | 0558efa5 | Site scaffold | Creating docs/data structure and initial pages. |

## Requests / Cross-scope Notes
- None. Single session completing requested scope on fixed current branch.

## Verification / Irregularities
- Michelin starred list source: https://guide.michelin.com/us/en/article/michelin-guide-ceremony/all-the-stars-in-the-michelin-guide-to-new-york-city-2025 (fetched 2026-11-25). Lists 2025 NYC stars; confirms 5 three-star, 15 two-star, 50 one-star (total 70 named in article including Green Stars section? Article lists 5+15+50 starred = 70 starred entries; Michelin all-starred page shows 69 total - discrepancy to be flagged/reconciled during verification).
- Michelin all-starred listing: https://guide.michelin.com/en/us/new-york-state/new-york/restaurants/all-starred (fetched 2026-11-25) shows "NYC and surroundings: 1-48 of 69 restaurants" and counts 5/14/50. Ceremony article lists 15 two-star entries (includes Joo Ok NEW). All-starred page filter shows 14 two-star - potential count inconsistency; flag for manual review.
- Hotel pricing for Feb-Mar 2027: dynamic booking inventory/prices may not be statically verifiable; any unverified price will be left blank and flagged.

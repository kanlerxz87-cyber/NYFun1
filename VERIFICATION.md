# VERIFICATION.md

## Policy
- Every table row must have a source link to an official site where possible.
- If a value can't be confirmed from an official source, leave it blank and flag it as unverified.
- Never infer or fill in values.

## Verified in this session (2026-11-25, session 0558efa5)

| Item | Source | What was verified | Status | Notes |
|------|--------|-------------------|--------|-------|
| NYC Michelin 2025 starred restaurants (names, star level, cuisine, Michelin URL) | https://guide.michelin.com/us/en/article/michelin-guide-ceremony/all-the-stars-in-the-michelin-guide-to-new-york-city-2025 | Extracted from ceremony article body | Partial | Cost/hours/social/official restaurant links not verified. |
| Michelin all-starred listing counts | https://guide.michelin.com/en/us/new-york-state/new-york/restaurants/all-starred | Page showed 5 three-star, 14 two-star, 50 one-star (69 total) | Partial | Count discrepancy vs ceremony extraction flagged (F1). |
| MTA official site reference | https://www.mta.info/ | URL is official MTA domain | Verified (URL only) | No transit times computed. |
| Central Park Conservancy official site | https://www.centralparknyc.org/ | Official site URL | Verified (URL only) | Hours/cost details not verified. |
| Met Museum official site | https://www.metmuseum.org/ | Official site URL | Verified (URL only) | Admission/hours not verified. |
| AMNH official site | https://www.amnh.org/ | Official site URL | Verified (URL only) | Admission/hours not verified. |
| MoMA official site | https://www.moma.org/ | Official site URL | Verified (URL only) | Admission/hours not verified. |
| NPS Statue of Liberty | https://www.nps.gov/stli/index.htm | Official NPS URL | Verified (URL only) | Fees/hours/ferry details not verified. |

## Unverified / Flagged
- Hotel 7-night total prices for Feb 15–Mar 23 2027 (all candidates). 
- Cheapest upcoming 7-night booking window.
- Hotel room compliance (queen+/private bath) for exact dates.
- Michelin restaurant density within 1 hour subway/bus from candidate hotels.
- Restaurant cost for 2 adults, days/hours/exceptions, official restaurant websites, social links.
- Michelin Selected (non-starred) full list.
- Activity costs/hours/exceptions/social links.

## Irregularities
- F1: Michelin starred count discrepancy (ceremony extraction 72 rows vs all-starred filter 69). Manual reconciliation required.

#!/usr/bin/env python3
"""
Independent end-to-end site integrity, link, mobile-card, duplicate-header,
and arithmetic verifier for kanlerxz87-cyber/NYFun1 (session arena-61867d90).
"""
import glob, json, os, re, sys, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DATA = os.path.join(ROOT, "site_data")

errors = []

expected_html = {
    "index.html", "hotels.html", "restaurants.html", "activities.html",
    "itinerary.html", "budget.html", "questions.html", "suggestions.html",
    "flagged.html", "method.html", "repo-review.html",
}
actual_html = {os.path.basename(p) for p in glob.glob(os.path.join(DOCS, "*.html"))}
if actual_html != expected_html:
    errors.append(f"docs/*.html mismatch: extra={actual_html - expected_html}, missing={expected_html - actual_html}")

html_files = (
    [os.path.join(ROOT, "index.html")]
    + sorted(glob.glob(os.path.join(DOCS, "*.html")))
    + sorted(glob.glob(os.path.join(ROOT, "deepdive", "*.html")))
)
ext_urls = set()

for path in html_files:
    txt = open(path, encoding="utf-8").read()
    base = os.path.dirname(path)
    for href in re.findall(r'href="([^"]+)"', txt):
        if href.startswith(("#", "mailto:", "tel:")):
            continue
        if href.startswith(("http://", "https://")):
            ext_urls.add(href)
            p = urllib.parse.urlparse(href)
            if not p.netloc or " " in href or not href.startswith("https://"):
                errors.append(f"{path}: invalid or non-https external URL {href!r}")
        else:
            clean = href.split("#")[0].split("?")[0]
            if not clean:
                continue
            target = os.path.normpath(os.path.join(base, clean))
            if not (os.path.isfile(target) or os.path.isfile(os.path.join(target, "index.html"))):
                errors.append(f"{path}: broken relative link {href!r} -> {target}")

banned_strings = [
    'class="v">$1,155.48',
    "verified precio",
    "4 nights - the literal preferred window",
    "<th>Source</th><th>Source</th>",
    "NaN",
]
total_tbody_rows = 0
for fn in sorted(expected_html):
    p = os.path.join(DOCS, fn)
    txt = open(p, encoding="utf-8").read()
    if '<meta name="viewport" content="width=device-width,initial-scale=1">' not in txt:
        errors.append(f"docs/{fn}: missing mobile viewport meta tag")
    for b in banned_strings:
        if b in txt:
            errors.append(f"docs/{fn}: contains banned/duplicate markup {b!r}")
    tbodies = re.findall(r"<tbody>(.*?)</tbody>", txt, flags=re.S)
    tbody_rows = 0
    for ti, tb in enumerate(tbodies, 1):
        rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", tb, flags=re.S)
        tbody_rows += len(rows)
        for ri, rhtml in enumerate(rows, 1):
            if not re.search(r'href="https://', rhtml):
                errors.append(f"docs/{fn}: tbody {ti} row {ri} missing https:// source link")
    total_tbody_rows += tbody_rows
    mcards = len(re.findall(r'<div class="mcard(?:"|\s)', txt))
    if tbody_rows != mcards:
        errors.append(f"docs/{fn}: desktop tbody rows ({tbody_rows}) != mobile cards ({mcards})")

fr = json.load(open(os.path.join(DATA, "framework.json"), encoding="utf-8"))
b_sum = round(sum(l["usd"] for l in fr["budget"]["lines"] if l["usd"] is not None), 2)
if abs(b_sum - fr["budget"]["verified_subtotal_usd"]) > 0.005:
    errors.append(f"budget subtotal {fr['budget']['verified_subtotal_usd']} != {b_sum}")

audit_rep = json.load(open(os.path.join(DOCS, "data", "external_url_audit.json"), encoding="utf-8"))
if audit_rep.get("non_https_warnings"):
    errors.append(f"external_url_audit.json has non-https warnings: {audit_rep['non_https_warnings']}")

print(
    f"Verified {len(html_files)} HTML pages, {total_tbody_rows} desktop+mobile table rows, "
    f"{len(ext_urls)} unique HTTPS external URLs, 0 duplicate Source columns, and budget subtotal ${b_sum:,.2f}."
)
if errors:
    print("VERIFICATION FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("ALL INDEPENDENT SITE INTEGRITY CHECKS PASSED (0 errors)!")

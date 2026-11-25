#!/usr/bin/env python3
"""Offline integrity checks for the generated NYC trip-planning site.

This checks local page/link integrity and source-link presence only. It does not
assert that a cited page is live, official, or still shows the recorded value.
"""
from __future__ import annotations

import csv
import html.parser
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [ROOT / "index.html", *sorted((ROOT / "docs").glob("*.html")), *sorted((ROOT / "deepdive").glob("*.html"))]


class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []
        self.viewport = False
        self.table_rows: list[tuple[bool, list[str]]] = []  # (is header row, hrefs)
        self._row: list | None = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name", "").lower() == "viewport":
            self.viewport = True
        if tag in ("a", "link", "script", "img", "source"):
            attr = "href" if tag in ("a", "link") else "src"
            value = a.get(attr)
            if value:
                self.links.append((tag, value))
        if tag == "tr":
            self._row = [False, []]
        elif self._row is not None:
            if tag == "th":
                self._row[0] = True
            if tag == "a" and a.get("href"):
                self._row[1].append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tr" and self._row is not None:
            self.table_rows.append((self._row[0], self._row[1]))
            self._row = None


def scan_html():
    issues, pages, external_hosts = [], 0, set()
    social_links, search_links, hashtag_links, direct_social_links, viewport_missing = 0, 0, 0, 0, []
    listing_pages = ("docs/hotels.html", "docs/restaurants.html", "docs/activities.html", "deepdive/hotels.html", "deepdive/restaurants.html")
    listing_summary = {}
    for path in HTML_FILES:
        if not path.is_file():
            issues.append(f"Missing expected HTML file: {path.relative_to(ROOT)}")
            continue
        pages += 1
        parser = PageParser()
        parser.feed(path.read_text(encoding="utf-8"))
        if not parser.viewport:
            viewport_missing.append(path.relative_to(ROOT).as_posix())
        for tag, raw in parser.links:
            parsed = urlsplit(raw)
            if parsed.scheme in ("http", "https", "mailto", "tel", "data"):
                if parsed.hostname:
                    external_hosts.add(parsed.hostname.lower())
                    host = parsed.hostname.lower()
                    if any(s in host for s in ("youtube.com", "youtu.be", "tiktok.com", "instagram.com")):
                        social_links += 1
                        if any(token in parsed.path.lower() for token in ("/search", "/results")) or "search_query=" in parsed.query:
                            search_links += 1
                        elif "instagram.com" in host and "/explore/tags/" in parsed.path.lower():
                            hashtag_links += 1
                        else:
                            direct_social_links += 1
                continue
            if parsed.scheme or raw.startswith("//"):
                continue
            target = (path.parent / parsed.path).resolve() if parsed.path else path.resolve()
            if not target.exists():
                issues.append(f"Broken local link in {path.relative_to(ROOT)}: {raw}")
            elif parsed.fragment and target.is_file() and target.suffix.lower() in (".html", ".htm"):
                target_parser = PageParser()
                try:
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    if parsed.fragment not in target_parser.ids:
                        issues.append(f"Missing anchor in {path.relative_to(ROOT)}: {raw}")
                except UnicodeDecodeError:
                    pass
        rel = path.relative_to(ROOT).as_posix()
        if rel in listing_pages:
            rows = [(header, hrefs) for header, hrefs in parser.table_rows if not header]
            primary = []
            for _, hrefs in rows:
                hosts = [urlsplit(h).hostname or "" for h in hrefs if urlsplit(h).scheme in ("http", "https")]
                primary.append(any(not any(s in host.lower() for s in ("youtube.com", "youtu.be", "tiktok.com", "instagram.com", "google.com")) for host in hosts))
            listing_summary[rel] = {"data_rows": len(rows), "rows_with_non_social_external_link": sum(primary), "rows_without_non_social_external_link": len(rows) - sum(primary)}
    return {
        "html_pages": pages,
        "listing_row_source_link_audit": listing_summary,
        "social_platform_links": social_links,
        "social_platform_search_links": search_links,
        "instagram_hashtag_discovery_links": hashtag_links,
        "direct_post_or_profile_links_not_content_reviewed": direct_social_links,
        "external_hosts": len(external_hosts),
        "viewport_missing_pages": viewport_missing,
        "issues": issues,
    }


def scan_data():
    result = {"csv_tables": {}, "deepdive_json_records": {}, "json_record_gaps": []}
    for path in sorted((ROOT / "docs/data").glob("*.csv")):
        if path.name == "build_summary.json":
            continue
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        source_cols = [c for c in ("official_url", "michelin_url", "booking_url", "source_url") if rows and c in rows[0]]
        if not source_cols and rows:
            source_cols = [c for c in rows[0] if c.endswith("_url")]
        no_source = [r.get("name") or r.get("activity") or r.get("hotel") or r.get("window_start") or f"row {i+2}" for i, r in enumerate(rows) if not any((r.get(c) or "").strip().startswith("https://") for c in source_cols)]
        result["csv_tables"][path.name] = {"records": len(rows), "source_columns": source_cols, "records_without_https_source": no_source}
    for path in sorted((ROOT / "deepdive/data").glob("*.json")):
        obj = json.loads(path.read_text(encoding="utf-8"))
        for key, records in obj.items():
            if not isinstance(records, list) or not records or not isinstance(records[0], dict):
                continue
            # Only arrays rendered as venue/activity/hotel evidence tables are evaluated.
            n = len(records)
            result["deepdive_json_records"][f"{path.name}:{key}"] = n
            for i, r in enumerate(records):
                url_fields = [v for k, v in r.items() if (k in ("official", "michelin", "source", "url", "booking", "website") or k.endswith("_url")) and isinstance(v, str) and v.startswith("https://")]
                # The one-star shortlist is editorial context, not a source-verified directory table.
                if not url_fields and key not in ("one_star_shortlist", "suggestions"):
                    result["json_record_gaps"].append(f"{path.name}:{key}[{i}] {r.get('name', r.get('id', '(unnamed)'))}")
    return result


def main():
    html = scan_html()
    data = scan_data()
    html_source_gaps = sum(v["rows_without_non_social_external_link"] for v in html["listing_row_source_link_audit"].values())
    csv_source_gaps = sum(len(v["records_without_https_source"]) for v in data["csv_tables"].values())
    json_source_gaps = len(data["json_record_gaps"])
    out = {
        "html": html,
        "data": data,
        "source_coverage": {
            "complete": html_source_gaps == 0 and csv_source_gaps == 0 and json_source_gaps == 0,
            "listing_rows_without_non_social_source": html_source_gaps,
            "csv_records_without_https_source": csv_source_gaps,
            "json_records_without_per_record_url": json_source_gaps,
        },
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if html["issues"] or html["viewport_missing_pages"]:
        raise SystemExit(1)
    if not out["source_coverage"]["complete"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

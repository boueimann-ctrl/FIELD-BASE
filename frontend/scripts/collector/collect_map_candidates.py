
#!/usr/bin/env python3
"""Collect map coordinate candidates from official field websites."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, unquote, urljoin, urlparse
from urllib.request import Request

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "monitor"),
)

from monitor import (
    OPENER,
    TIMEOUT,
    USER_AGENT,
    fetch_robots,
    load_fields,
    valid_url,
)

ROOT = Path(__file__).resolve().parents[2]

OUTPUT = ROOT / "src/data/generated/mapCandidates.json"
LOCATIONS = ROOT / "src/data/fieldLocations.ts"

MAX_BYTES = 3_000_000
REQUEST_DELAY = 2.0


class MapLinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = set()

    def handle_starttag(self, tag, attrs):
        if tag not in {"iframe", "a"}:
            return

        attributes = dict(attrs)
        key = "src" if tag == "iframe" else "href"
        value = attributes.get(key)

        if isinstance(value, str) and value.strip():
            self.links.add(unescape(value.strip()))


def load_json(path):
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    return data if isinstance(data, dict) else {}


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(".json.tmp")

    temporary.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    temporary.replace(path)


def load_registered_location_ids():
    if not LOCATIONS.exists():
        return set()

    source = LOCATIONS.read_text(encoding="utf-8")

    return set(
        re.findall(
            r"""['"]([^'"]+)['"]\s*:\s*\{\s*latitude\s*:""",
            source,
        )
    )


def valid_coordinates(latitude, longitude):
    return (
        20.0 <= latitude <= 46.0
        and 122.0 <= longitude <= 154.0
    )


def parse_coordinate_pair(latitude, longitude):
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return None

    if not valid_coordinates(lat, lon):
        return None

    return {
        "latitude": lat,
        "longitude": lon,
    }


def is_google_maps_url(url):
    host = (urlparse(url).hostname or "").lower()

    return (
        host == "google.com"
        or host.endswith(".google.com")
        or host == "maps.app.goo.gl"
        or host == "goo.gl"
    )


def extract_google_coordinates(url):
    if not is_google_maps_url(url):
        return None

    decoded = unquote(url)

    patterns = [
        (
            r"!2d(-?\d+(?:\.\d+)?)!3d(-?\d+(?:\.\d+)?)",
            "embedded_map_center",
            True,
        ),
        (
            r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)",
            "map_view_center",
            False,
        ),
    ]

    for pattern, kind, reversed_order in patterns:
        match = re.search(pattern, decoded)

        if not match:
            continue

        first, second = match.groups()

        if reversed_order:
            coordinates = parse_coordinate_pair(second, first)
        else:
            coordinates = parse_coordinate_pair(first, second)

        if coordinates:
            return {
                **coordinates,
                "coordinateType": kind,
            }

    parsed = urlparse(decoded)
    params = parse_qs(parsed.query)

    for key in ("q", "query", "ll"):
        for value in params.get(key, []):
            match = re.fullmatch(
                r"\s*(-?\d+(?:\.\d+)?)\s*,\s*"
                r"(-?\d+(?:\.\d+)?)\s*",
                value,
            )

            if not match:
                continue

            coordinates = parse_coordinate_pair(
                match.group(1),
                match.group(2),
            )

            if coordinates:
                return {
                    **coordinates,
                    "coordinateType": "coordinate_query",
                }

    return None


def extract_map_links(html, base_url):
    parser = MapLinkParser()
    parser.feed(html)

    links = set()

    for link in parser.links:
        absolute = urljoin(base_url, link)

        if is_google_maps_url(absolute):
            links.add(absolute)

    url_pattern = re.compile(
        r"https?://(?:www\.)?google\.[^\"'<>\s]+"
    )

    for match in url_pattern.findall(html):
        link = unescape(match)

        if is_google_maps_url(link):
            links.add(link)

    return sorted(links)


def fetch_html(url, robots_cache):
    robots = fetch_robots(url, robots_cache)

    if robots.get("status") != "ok":
        return None

    if not robots["parser"].can_fetch(USER_AGENT, url):
        return None

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html",
        },
    )

    try:
        with OPENER.open(request, timeout=TIMEOUT) as response:
            content_type = response.headers.get(
                "Content-Type",
                "",
            ).lower()

            if "text/html" not in content_type:
                return None

            raw = response.read(MAX_BYTES + 1)

            if len(raw) > MAX_BYTES:
                return None

            charset = (
                response.headers.get_content_charset()
                or "utf-8"
            )

            try:
                return raw.decode(charset, errors="replace")
            except LookupError:
                return raw.decode("utf-8", errors="replace")

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        ValueError,
    ):
        return None


def collect_candidates(field, html):
    url = field["website"]
    links = extract_map_links(html, url)

    candidates = []
    seen = set()

    for link in links:
        coordinates = extract_google_coordinates(link)

        if coordinates is None:
            continue

        key = (
            coordinates["latitude"],
            coordinates["longitude"],
        )

        if key in seen:
            continue

        seen.add(key)

        candidates.append(
            {
                **coordinates,
                "mapUrl": link,
                "status": "pending_manual_review",
            }
        )

    return {
        "fieldName": field["name"],
        "officialUrl": url,
        "checkedAt": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "pending_manual_review",
        "candidates": candidates,
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    fields = load_fields()
    registered_ids = load_registered_location_ids()
    existing = load_json(OUTPUT)

    output = dict(existing)
    robots_cache = {}

    checked = 0
    found = 0

    for field in fields:
        field_id = field["id"]
        url = field["website"].strip()

        if field_id in registered_ids:
            continue

        if not valid_url(url):
            continue

        if args.limit and checked >= args.limit:
            break

        checked += 1

        print(
            f"[{checked}] {field['name']}",
            flush=True,
        )

        html = fetch_html(url, robots_cache)

        if html is None:
            print("  HTML取得不可・既存候補を維持")
            time.sleep(REQUEST_DELAY)
            continue

        result = collect_candidates(field, html)

        if result["candidates"]:
            output[field_id] = result
            found += 1

            print(
                f"  座標候補: {len(result['candidates'])}件"
            )

            for candidate in result["candidates"]:
                print(
                    "  ",
                    candidate["latitude"],
                    candidate["longitude"],
                    candidate["coordinateType"],
                )
        else:
            print("  座標候補なし")

        time.sleep(REQUEST_DELAY)

    output = dict(sorted(output.items()))

    print()
    print(f"調査施設数: {checked}")
    print(f"今回候補が見つかった施設数: {found}")
    print(f"保存対象施設数: {len(output)}")

    if args.dry_run:
        print()
        print(
            json.dumps(
                output,
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    save_json(OUTPUT, output)

    print()
    print(f"保存完了: {OUTPUT}")
    print("公開用の座標データは変更していません")

    return 0


if __name__ == "__main__":
    sys.exit(main())

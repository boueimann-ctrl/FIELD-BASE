
#!/usr/bin/env python3
"""FIELD//BASE Data Monitor: free, read-only website monitoring."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)
from urllib.robotparser import RobotFileParser


ROOT = Path(__file__).resolve().parents[2]
FIELDS_FILE = ROOT / "src/data/fields.ts"
VERIFICATION_FILE = ROOT / "src/data/fieldVerification.ts"

STATE_DIR = ROOT / "data-monitor"
SNAPSHOT_FILE = STATE_DIR / "snapshots.json"
REPORT_FILE = STATE_DIR / "report.md"
JSON_REPORT_FILE = STATE_DIR / "report.json"

USER_AGENT = "FIELD-BASE-Monitor/1.0 (+public website monitoring)"
TIMEOUT = 12
MAX_BYTES = 3_000_000
MAX_ROBOTS_BYTES = 256_000
REQUEST_DELAY = 2.0

DIRECTORY_URL = "https://sightin.jp/field/map/?area=kanto"

FIELD_PATTERN = re.compile(
    r"createField\s*\(\s*\{(.*?)\}\s*\)",
    re.S,
)

PROPERTY_PATTERN = re.compile(
    r"(\w+)\s*:\s*(['\"])(.*?)\2",
    re.S,
)

VERIFIED_PATTERN = re.compile(
    r"['\"]([^'\"]+)['\"]\s*:\s*\{(.*?)\}",
    re.S,
)


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(
        self, request, fp, code, msg, headers, newurl
    ):
        return None


OPENER = build_opener(NoRedirectHandler)


class TextExtractor(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg"}
    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr",
        "img", "input", "link", "meta", "param",
        "source", "track", "wbr",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and tag in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            self.stack = self.stack[:index]

    def handle_data(self, data):
        if not self.stack:
            self.parts.append(data)

    def text(self):
        return re.sub(
            r"\s+", " ", " ".join(self.parts)
        ).strip()


def parse_properties(block):
    return {
        match.group(1): match.group(3)
        for match in PROPERTY_PATTERN.finditer(block)
    }


def load_fields():
    source = FIELDS_FILE.read_text(encoding="utf-8")
    fields = []

    for match in FIELD_PATTERN.finditer(source):
        props = parse_properties(match.group(1))

        if "id" in props and "name" in props:
            fields.append({
                "id": props["id"],
                "name": props["name"],
                "website": props.get("website", ""),
            })

    verified_source = VERIFICATION_FILE.read_text(
        encoding="utf-8"
    )

    verified_section = verified_source.split(
        "const verifiedFields:", 1
    )[-1].split("export function", 1)[0]

    verified = {}

    for match in VERIFIED_PATTERN.finditer(verified_section):
        verified[match.group(1)] = parse_properties(
            match.group(2)
        )

    for field in fields:
        override = verified.get(field["id"], {})

        if override.get("website"):
            field["website"] = override["website"]

    return fields


def valid_url(value):
    try:
        parts = urlsplit(value)

        return (
            parts.scheme in ("http", "https")
            and bool(parts.hostname)
            and not parts.username
            and not parts.password
        )
    except ValueError:
        return False


def origin_of(url):
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def redirect_result(exc, original_url):
    from urllib.parse import urljoin

    location = exc.headers.get("Location")

    if not location:
        return {
            "status": "redirect_review",
            "http_status": exc.code,
        }

    final_url = urljoin(original_url, location)

    if not valid_url(final_url):
        return {
            "status": "invalid_redirect",
            "final_url": final_url,
        }

    return {
        "status": "redirect_review",
        "http_status": exc.code,
        "final_url": final_url,
    }


def fetch_robots(url, cache):
    origin = origin_of(url)

    if origin in cache:
        return cache[origin]

    robots_url = origin + "/robots.txt"
    parser = RobotFileParser()
    parser.set_url(robots_url)

    request = Request(
        robots_url,
        headers={"User-Agent": USER_AGENT},
    )

    try:
        with OPENER.open(request, timeout=TIMEOUT) as response:
            data = response.read(MAX_ROBOTS_BYTES + 1)

            if len(data) > MAX_ROBOTS_BYTES:
                cache[origin] = None
                return None

            content = data.decode(
                "utf-8", errors="replace"
            )
            parser.parse(content.splitlines())
            cache[origin] = parser

    except HTTPError as exc:
        if exc.code in (404, 410):
            parser.parse([])
            cache[origin] = parser
        else:
            cache[origin] = None

    except (URLError, TimeoutError, OSError, ValueError):
        cache[origin] = None

    return cache[origin]


def check_page(url, robots_cache):
    parser = fetch_robots(url, robots_cache)

    if parser is None:
        return {"status": "robots_unknown"}

    if not parser.can_fetch(USER_AGENT, url):
        return {"status": "robots_disallowed"}

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
                "Content-Type", ""
            ).lower()

            if "text/html" not in content_type:
                return {"status": "not_html"}

            content = response.read(MAX_BYTES + 1)

            if len(content) > MAX_BYTES:
                return {
                    "status": "too_large",
                    "max_bytes": MAX_BYTES,
                }

            charset = (
                response.headers.get_content_charset()
                or "utf-8"
            )

            try:
                html = content.decode(
                    charset, errors="replace"
                )
            except LookupError:
                html = content.decode(
                    "utf-8", errors="replace"
                )

        extractor = TextExtractor()
        extractor.feed(html)
        text = extractor.text()

        if not text:
            return {"status": "empty_content"}

        digest = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

        return {
            "status": "ok",
            "hash": digest,
            "text_length": len(text),
        }

    except HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308):
            return redirect_result(exc, url)

        return {
            "status": "http_error",
            "http_status": exc.code,
        }

    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "status": "request_error",
            "error_type": type(exc).__name__,
        }

    except Exception as exc:
        return {
            "status": "parse_error",
            "error_type": type(exc).__name__,
        }


def load_snapshots():
    if not SNAPSHOT_FILE.exists():
        return {}

    try:
        data = json.loads(
            SNAPSHOT_FILE.read_text(encoding="utf-8")
        )

        if isinstance(data, dict):
            return data

    except (ValueError, OSError):
        pass

    return {}


def write_json(path, value):
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def markdown_report(report):
    lines = [
        "# FIELD//BASE Data Monitor",
        "",
        f"実行日時（UTC）: {report['checked_at']}",
        "",
        f"- 登録施設: {report['total_fields']}件",
        f"- 監視対象: {report['monitored']}件",
        f"- 公式URL未登録: {report['missing_url']}件",
        f"- 初回基準作成: {report['baseline']}件",
        f"- ページ変更検出: {report['changed']}件",
        f"- 取得成功・変更なし: {report['unchanged']}件",
        f"- 要確認: {report['needs_review']}件",
        "",
        "## 施設別結果",
        "",
        "| 施設 | 状態 | URL |",
        "|---|---|---|",
    ]

    for item in report["results"]:
        name = item["name"].replace("|", "\\|")
        url = item["url"].replace("|", "%7C")

        lines.append(
            f"| {name} | {item['status']} | {url} |"
        )

    lines.extend([
        "",
        "## 注意事項",
        "",
        "- ページ変更は料金・営業状況の変更を意味しません。",
        "- URLへのアクセス成功は営業中の証明ではありません。",
        "- 取得失敗やアクセス制限は閉業の証明ではありません。",
        "- 監視対象は登録済みの公式URLのみです。",
        "- JavaScript生成部分は取得できない場合があります。",
        "- 施設データは自動変更しません。",
        "- リダイレクト先は自動取得せず、確認対象とします。",
        "",
    ])

    return "\n".join(lines)


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    fields = load_fields()
    previous = load_snapshots()
    updated = dict(previous)
    robots_cache = {}
    results = []

    for index, field in enumerate(fields, start=1):
        field_id = field["id"]
        url = field["website"].strip()

        print(
            f"[{index}/{len(fields)}] {field['name']}",
            flush=True,
        )

        if not url or url == DIRECTORY_URL:
            results.append({
                "id": field_id,
                "name": field["name"],
                "url": "",
                "status": "missing_url",
            })
            continue

        if not valid_url(url):
            results.append({
                "id": field_id,
                "name": field["name"],
                "url": url,
                "status": "invalid_url",
            })
            continue

        current = check_page(url, robots_cache)
        status = current["status"]

        if status == "ok":
            old = previous.get(field_id)

            if not isinstance(old, dict):
                old = {}

            if old.get("url") != url or not old.get("hash"):
                status = "baseline"
            elif old["hash"] != current["hash"]:
                status = "changed"
            else:
                status = "unchanged"

            updated[field_id] = {
                "url": url,
                "hash": current["hash"],
                "checked_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

        results.append({
            "id": field_id,
            "name": field["name"],
            "url": url,
            "status": status,
            **{
                key: value
                for key, value in current.items()
                if key not in ("status", "hash")
            },
        })

        time.sleep(REQUEST_DELAY)

    statuses = [
        item["status"]
        for item in results
    ]

    normal = {
        "missing_url",
        "baseline",
        "unchanged",
    }

    report = {
        "checked_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_fields": len(fields),
        "monitored": sum(
            status != "missing_url"
            for status in statuses
        ),
        "missing_url": statuses.count("missing_url"),
        "baseline": statuses.count("baseline"),
        "changed": statuses.count("changed"),
        "unchanged": statuses.count("unchanged"),
        "needs_review": sum(
            status not in normal
            for status in statuses
        ),
        "results": results,
    }

    write_json(SNAPSHOT_FILE, updated)
    write_json(JSON_REPORT_FILE, report)

    REPORT_FILE.write_text(
        markdown_report(report),
        encoding="utf-8",
    )

    print("\n=== FIELD//BASE DATA MONITOR ===")
    print(f"登録施設: {report['total_fields']}")
    print(f"公式URL未登録: {report['missing_url']}")
    print(f"初回基準: {report['baseline']}")
    print(f"変更検出: {report['changed']}")
    print(f"要確認: {report['needs_review']}")
    print(f"レポート: {REPORT_FILE}")

    if not fields:
        print("ERROR: フィールドを読み込めませんでした。")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

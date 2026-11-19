
#!/usr/bin/env python3
"""FIELD//BASE official structured-data collector.

Collect conservative facility information from official JSON-LD.

Safety rules:
- Respect robots.txt.
- Require matching facility name and municipality.
- Preserve existing data when collection fails.
- Hold conflicting address changes for review.
- Never publish unreviewed coordinates.
- Avoid updating verifiedAt when data is unchanged.
- Write output atomically.

Diagnostics:
- Report robots.txt restrictions.
- Report HTTP response and content type.
- Report missing or invalid JSON-LD.
- Report facility name and address validation failures.
- Never weaken verification rules to improve collection rates.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import tempfile
import time

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
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
GENERATED = ROOT / "src" / "data" / "generated"

OUTPUT = GENERATED / "fieldAutoData.json"
RESEARCH_CSV = GENERATED / "fieldResearch.csv"

FIELDS_FILE = ROOT / "src" / "data" / "fields.ts"
VERIFICATION_FILE = ROOT / "src" / "data" / "fieldVerification.ts"

MAX_BYTES = 3_000_000
REQUEST_DELAY = 2.0

JAPAN_BOUNDS = (
    20.0,
    46.0,
    122.0,
    154.0,
)

FIELD_PATTERN = re.compile(
    r"createField\s*\(\s*\{(.*?)\}\s*\)",
    re.S,
)

PROPERTY_PATTERN = re.compile(
    r"(\w+)\s*:\s*(['\"])(.*?)\2",
    re.S,
)


class StructuredDataParser(HTMLParser):
    """Extract JSON-LD documents from HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)

        self.inside = False
        self.buffer = []
        self.documents = []

        self.script_count = 0
        self.invalid_count = 0

    def handle_starttag(self, tag, attrs):
        if tag != "script":
            return

        attributes = dict(attrs)

        script_type = (
            attributes.get("type") or ""
        ).lower()

        if "application/ld+json" in script_type:
            self.inside = True
            self.buffer = []
            self.script_count += 1

    def handle_data(self, data):
        if self.inside:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if tag != "script" or not self.inside:
            return

        self.inside = False

        try:
            document = json.loads(
                "".join(self.buffer)
            )

            self.documents.append(document)

        except json.JSONDecodeError:
            self.invalid_count += 1

        self.buffer = []


def properties(block):
    return {
        match.group(1): match.group(3)
        for match in PROPERTY_PATTERN.finditer(block)
    }


def load_metadata():
    source = FIELDS_FILE.read_text(
        encoding="utf-8"
    )

    result = {}

    for match in FIELD_PATTERN.finditer(source):
        item = properties(match.group(1))

        field_id = item.get("id")

        if field_id:
            result[field_id] = {
                "prefecture": item.get(
                    "prefecture",
                    "",
                ),
                "city": item.get(
                    "city",
                    "",
                ),
            }

    return result


def load_manual_ids():
    """Identify manually maintained facility records."""

    source = VERIFICATION_FILE.read_text(
        encoding="utf-8"
    )

    section = source.split(
        "const verifiedFields:",
        1,
    )

    if len(section) < 2:
        return set()

    body = section[1].split(
        "export function",
        1,
    )[0]

    return set(
        re.findall(
            r"['\"]([^'\"]+)['\"]\s*:\s*\{",
            body,
        )
    )


def normalize(value):
    return re.sub(
        r"[\s\u3000・／/（）()\[\]【】\-_.]+",
        "",
        str(value).casefold(),
    )


def get_candidate_names(node):
    names = []

    name = node.get("name")

    if isinstance(name, str):
        names.append(name)

    alternate_name = node.get(
        "alternateName",
        [],
    )

    if isinstance(alternate_name, str):
        names.append(alternate_name)

    elif isinstance(alternate_name, list):
        names.extend(
            value
            for value in alternate_name
            if isinstance(value, str)
        )

    return names


def matches_field_name(node, field_name):
    target = normalize(field_name)

    if not target:
        return False

    return any(
        normalize(candidate) == target
        for candidate in get_candidate_names(node)
    )


def iter_nodes(document):
    if isinstance(document, list):
        for item in document:
            yield from iter_nodes(item)

    elif isinstance(document, dict):
        yield document

        graph = document.get("@graph")

        if isinstance(graph, (list, dict)):
            yield from iter_nodes(graph)


def is_place(node):
    types = node.get("@type", [])

    if isinstance(types, str):
        types = [types]

    accepted = {
        "Place",
        "LocalBusiness",
        "SportsActivityLocation",
        "SportsClub",
        "EntertainmentBusiness",
    }

    return any(
        str(value).rsplit("/", 1)[-1]
        in accepted
        for value in types
    )


def parse_address(value):
    if not isinstance(value, dict):
        return None

    street = value.get("streetAddress")
    locality = value.get(
        "addressLocality",
        "",
    )
    region = value.get(
        "addressRegion",
        "",
    )
    country = value.get(
        "addressCountry",
        "",
    )

    if isinstance(country, dict):
        country = country.get(
            "name",
            "",
        )

    if country and str(country).upper() not in {
        "JP",
        "JPN",
        "JAPAN",
        "日本",
    }:
        return None

    if (
        not isinstance(street, str)
        or not street.strip()
    ):
        return None

    if not isinstance(locality, str):
        return None

    if not isinstance(region, str):
        return None

    address = (
        f"{region}{locality}{street}"
    ).strip()

    if not address or len(address) > 180:
        return None

    return address


def parse_coordinates(value):
    if not isinstance(value, dict):
        return None

    try:
        latitude = float(
            value["latitude"]
        )

        longitude = float(
            value["longitude"]
        )

    except (KeyError, TypeError, ValueError):
        return None

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
    ):
        return None

    south, north, west, east = JAPAN_BOUNDS

    if not (
        south <= latitude <= north
        and west <= longitude <= east
    ):
        return None

    return {
        "latitude": latitude,
        "longitude": longitude,
    }


def extract_verified(
    html,
    field,
    metadata,
    diagnostics=None,
):
    """Extract verified JSON-LD and explain rejection reasons."""

    if diagnostics is None:
        diagnostics = {}

    parser = StructuredDataParser()
    parser.feed(html)

    diagnostics["jsonld_scripts"] = (
        parser.script_count
    )

    diagnostics["jsonld_documents"] = (
        len(parser.documents)
    )

    diagnostics["jsonld_invalid"] = (
        parser.invalid_count
    )

    if parser.script_count == 0:
        diagnostics["reason"] = (
            "JSON-LDなし"
        )
        return None

    if not parser.documents:
        diagnostics["reason"] = (
            "有効なJSON-LDなし"
        )
        return None

    counters = {
        "nodes": 0,
        "places": 0,
        "names": 0,
        "addresses": 0,
        "prefectures": 0,
        "cities": 0,
    }

    candidates = []

    for document in parser.documents:
        for node in iter_nodes(document):
            counters["nodes"] += 1

            if not is_place(node):
                continue

            counters["places"] += 1

            if not matches_field_name(
                node,
                field["name"],
            ):
                continue

            counters["names"] += 1

            address = parse_address(
                node.get("address")
            )

            if not address:
                continue

            counters["addresses"] += 1

            prefecture = metadata.get(
                "prefecture",
                "",
            )

            city = metadata.get(
                "city",
                "",
            )

            if not prefecture or not city:
                continue

            if not address.startswith(
                prefecture
            ):
                continue

            counters["prefectures"] += 1

            if (
                normalize(city)
                not in normalize(address)
            ):
                continue

            counters["cities"] += 1

            candidate = {
                "address": address,
            }

            coordinates = parse_coordinates(
                node.get("geo")
            )

            if coordinates:
                candidate.update(
                    coordinates
                )

            candidates.append(candidate)

    diagnostics["validation"] = counters

    if not candidates:
        if counters["places"] == 0:
            reason = (
                "対応する施設タイプのJSON-LDなし"
            )

        elif counters["names"] == 0:
            reason = (
                "施設名不一致"
            )

        elif counters["addresses"] == 0:
            reason = (
                "住所データなし・住所形式不正"
            )

        elif not metadata.get("prefecture") or not metadata.get("city"):
            reason = (
                "登録施設の都道府県・市区町村情報不足"
            )

        elif counters["prefectures"] == 0:
            reason = (
                "都道府県不一致"
            )

        elif counters["cities"] == 0:
            reason = (
                "市区町村不一致"
            )

        else:
            reason = (
                "検証条件に一致する情報なし"
            )

        diagnostics["reason"] = reason
        return None

    addresses = {
        item["address"]
        for item in candidates
    }

    if len(addresses) != 1:
        diagnostics["reason"] = (
            "JSON-LD内に異なる住所が複数存在"
        )
        return None

    result = {
        "address": candidates[0]["address"],
    }

    coordinate_pairs = {
        (
            item["latitude"],
            item["longitude"],
        )
        for item in candidates
        if (
            "latitude" in item
            and "longitude" in item
        )
    }

    if len(coordinate_pairs) == 1:
        latitude, longitude = next(
            iter(coordinate_pairs)
        )

        result["latitude"] = latitude
        result["longitude"] = longitude

    elif len(coordinate_pairs) > 1:
        diagnostics["coordinate_warning"] = (
            "座標候補が複数あり不一致。座標は採用しません"
        )

    diagnostics["reason"] = (
        "検証済み情報を取得"
    )

    return result


def fetch_html(
    url,
    robots_cache,
    diagnostics=None,
):
    """Fetch HTML while recording non-sensitive diagnostics."""

    if diagnostics is None:
        diagnostics = {}

    diagnostics["url"] = url

    scheme = urlsplit(url).scheme.lower()

    diagnostics["scheme"] = scheme.upper()

    if scheme == "http":
        diagnostics["security_warning"] = (
            "HTTP通信は暗号化されません"
        )

    try:
        robots = fetch_robots(
            url,
            robots_cache,
        )

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        ValueError,
    ) as error:
        diagnostics["reason"] = (
            "robots.txt確認エラー: "
            + type(error).__name__
        )
        return None

    robots_status = robots.get(
        "status",
        "unknown",
    )

    diagnostics["robots_status"] = (
        robots_status
    )

    if robots_status != "ok":
        diagnostics["reason"] = (
            "robots.txtを確認できないため取得中止"
            + f"（status={robots_status}）"
        )
        return None

    try:
        allowed = robots["parser"].can_fetch(
            USER_AGENT,
            url,
        )

    except (
        KeyError,
        AttributeError,
        ValueError,
    ):
        diagnostics["reason"] = (
            "robots.txtの判定に失敗"
        )
        return None

    if not allowed:
        diagnostics["reason"] = (
            "robots.txtにより取得不可"
        )
        return None

    diagnostics["robots_allowed"] = True

    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html",
        },
    )

    try:
        with OPENER.open(
            request,
            timeout=TIMEOUT,
        ) as response:

            diagnostics["http_status"] = (
                response.status
            )

            diagnostics["final_url"] = (
                response.geturl()
            )

            content_type = (
                response.headers.get(
                    "Content-Type",
                    "",
                )
            ).lower()

            diagnostics["content_type"] = (
                content_type
            )

            if "text/html" not in content_type:
                diagnostics["reason"] = (
                    "HTML以外のContent-Type"
                )
                return None

            content = response.read(
                MAX_BYTES + 1
            )

            diagnostics["bytes"] = (
                len(content)
            )

            if len(content) > MAX_BYTES:
                diagnostics["reason"] = (
                    "ページサイズ上限超過"
                )
                return None

            charset = (
                response.headers.get_content_charset()
                or "utf-8"
            )

            try:
                html = content.decode(
                    charset,
                    errors="replace",
                )

            except LookupError:
                diagnostics["charset_warning"] = (
                    "未知の文字コード。UTF-8で代替"
                )

                html = content.decode(
                    "utf-8",
                    errors="replace",
                )

            diagnostics["reason"] = (
                "HTML取得成功"
            )

            return html

    except HTTPError as error:
        diagnostics["http_status"] = (
            error.code
        )

        diagnostics["reason"] = (
            f"HTTPエラー: {error.code}"
        )

    except URLError as error:
        diagnostics["reason"] = (
            "接続エラー: "
            + type(error.reason).__name__
        )

    except TimeoutError:
        diagnostics["reason"] = (
            "接続タイムアウト"
        )

    except (
        OSError,
        ValueError,
    ) as error:
        diagnostics["reason"] = (
            "取得エラー: "
            + type(error).__name__
        )

    return None


def print_diagnostics(diagnostics):
    """Print compact diagnostics for GitHub Actions."""

    scheme = diagnostics.get(
        "scheme",
        "UNKNOWN",
    )

    status = diagnostics.get(
        "http_status",
    )

    if status is not None:
        print(
            f"  通信: {scheme} / HTTP {status}"
        )
    else:
        print(
            f"  通信方式: {scheme}"
        )

    final_url = diagnostics.get(
        "final_url",
    )

    if final_url:
        print(
            f"  最終URL: {final_url}"
        )

    security_warning = diagnostics.get(
        "security_warning",
    )

    if security_warning:
        print(
            f"  注意: {security_warning}"
        )

    robots_status = diagnostics.get(
        "robots_status",
    )

    if robots_status:
        print(
            f"  robots.txt: {robots_status}"
        )

    if diagnostics.get("robots_allowed"):
        print(
            "  robots.txt: 取得許可"
        )

    content_type = diagnostics.get(
        "content_type",
    )

    if content_type:
        print(
            f"  Content-Type: {content_type}"
        )

    if "bytes" in diagnostics:
        print(
            f"  取得サイズ: {diagnostics['bytes']} bytes"
        )

    if "jsonld_scripts" in diagnostics:
        print(
            "  JSON-LD: "
            f"{diagnostics['jsonld_scripts']}スクリプト / "
            f"{diagnostics['jsonld_documents']}文書"
        )

    if diagnostics.get("jsonld_invalid"):
        print(
            "  JSON-LD解析失敗: "
            f"{diagnostics['jsonld_invalid']}件"
        )

    validation = diagnostics.get(
        "validation",
    )

    if validation:
        print(
            "  検証件数: "
            f"施設タイプ={validation['places']} / "
            f"施設名一致={validation['names']} / "
            f"住所あり={validation['addresses']} / "
            f"都道府県一致={validation['prefectures']} / "
            f"市区町村一致={validation['cities']}"
        )

    charset_warning = diagnostics.get(
        "charset_warning",
    )

    if charset_warning:
        print(
            f"  注意: {charset_warning}"
        )

    coordinate_warning = diagnostics.get(
        "coordinate_warning",
    )

    if coordinate_warning:
        print(
            f"  注意: {coordinate_warning}"
        )

    print(
        "  判定: "
        + diagnostics.get(
            "reason",
            "不明",
        )
    )


def load_existing():
    if not OUTPUT.exists():
        return {}

    data = json.loads(
        OUTPUT.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(data, dict):
        raise ValueError(
            "fieldAutoData.json must contain an object"
        )

    return data


def published_record(item):
    """Remove coordinates that have not been manually reviewed."""

    if not isinstance(item, dict):
        return {}

    return {
        key: value
        for key, value in item.items()
        if key not in {
            "latitude",
            "longitude",
        }
    }


def write_json_atomic(path, data):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".field_auto_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(
                file.name
            )

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )

            file.write("\n")
            file.flush()

            os.fsync(
                file.fileno()
            )

        os.replace(
            temporary_path,
            path,
        )

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()


def load_confirmed_official_urls():
    """Read human-confirmed official URLs from research CSV."""

    if not RESEARCH_CSV.exists():
        print(
            "調査CSVがありません。"
            "fields.ts のURLのみ使用します"
        )
        return {}

    with RESEARCH_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        columns = set(
            reader.fieldnames or []
        )

        required = {
            "field_id",
            "confirmed_official_url",
        }

        if not required.issubset(columns):
            raise ValueError(
                "調査CSVに必要な列がありません: "
                + ", ".join(
                    sorted(
                        required - columns
                    )
                )
            )

        confirmed = {}

        for row in reader:
            field_id = (
                row.get("field_id")
                or ""
            ).strip()

            url = (
                row.get("confirmed_official_url")
                or ""
            ).strip()

            if not field_id or not url:
                continue

            if field_id in confirmed:
                raise ValueError(
                    "確認済みURLの施設IDが重複: "
                    + field_id
                )

            confirmed[field_id] = url

    return confirmed


def select_official_url(
    field,
    confirmed_urls,
):
    """Prefer a human-confirmed URL over the registered URL."""

    field_id = field["id"]

    if field_id in confirmed_urls:
        url = confirmed_urls[
            field_id
        ]

        if not valid_url(url):
            print(
                "  確認済み公式URLが不正: "
                + field_id
            )
            return None

        return url

    url = field["website"].strip()

    if not valid_url(url):
        return None

    return url


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

    if args.limit < 0:
        parser.error(
            "--limit must be zero or greater"
        )

    fields = load_fields()

    confirmed_urls = (
        load_confirmed_official_urls()
    )

    metadata = load_metadata()
    manual_ids = load_manual_ids()
    existing = load_existing()

    output = {
        field_id: published_record(item)
        for field_id, item in existing.items()
        if isinstance(item, dict)
    }

    robots_cache = {}

    checked = 0
    accepted = 0
    unchanged = 0
    review_needed = 0

    fetch_failed = 0
    verification_failed = 0
    verified = 0

    today = datetime.now(
        timezone.utc
    ).date().isoformat()

    for field in fields:
        field_id = field["id"]

        url = select_official_url(
            field,
            confirmed_urls,
        )

        if field_id in manual_ids:
            continue

        if url is None:
            continue

        if args.limit and checked >= args.limit:
            break

        checked += 1

        print(
            f"\n[{checked}] {field['name']}",
            flush=True,
        )

        diagnostics = {}

        html = fetch_html(
            url,
            robots_cache,
            diagnostics,
        )

        time.sleep(
            REQUEST_DELAY
        )

        if html is None:
            fetch_failed += 1

            print_diagnostics(
                diagnostics
            )

            print(
                "  既存データを保持"
            )

            continue

        result = extract_verified(
            html,
            field,
            metadata.get(
                field_id,
                {},
            ),
            diagnostics,
        )

        print_diagnostics(
            diagnostics
        )

        if result is None:
            verification_failed += 1

            print(
                "  検証失敗のため公開データは変更しません"
            )

            continue

        verified += 1

        result["sourceUrl"] = url

        candidate_address = (
            result["address"]
        )

        old = output.get(
            field_id,
            {},
        )

        old_address = old.get(
            "address"
        )

        if (
            old_address
            and old_address != candidate_address
        ):
            review_needed += 1

            print(
                "  住所変更を検出。手動確認待ち"
            )

            continue

        candidate = {
            "address": candidate_address,
            "sourceUrl": url,
        }

        old_content = {
            "address": old.get(
                "address"
            ),
            "sourceUrl": old.get(
                "sourceUrl"
            ),
        }

        if candidate == old_content:
            unchanged += 1

            print(
                "  既存データと一致。変更なし"
            )

            continue

        candidate["verifiedAt"] = today

        output[field_id] = candidate

        accepted += 1

        print(
            "  検証済みデータを更新候補に追加"
        )

        if "latitude" in result:
            print(
                "  座標候補を検出。"
                "手動確認まで公開しません"
            )

    output = dict(
        sorted(
            output.items()
        )
    )

    print()
    print("=" * 45)
    print("FIELD//BASE 収集結果")
    print("=" * 45)

    print(
        f"取得対象: {checked}施設"
    )

    print(
        f"HTML取得失敗: {fetch_failed}施設"
    )

    print(
        f"JSON-LD検証失敗: {verification_failed}施設"
    )

    print(
        f"情報検証成功: {verified}施設"
    )

    print(
        f"新規・更新: {accepted}施設"
    )

    print(
        f"変更なし: {unchanged}施設"
    )

    print(
        f"要確認: {review_needed}施設"
    )

    print(
        f"保存対象: {len(output)}施設"
    )

    if args.dry_run:
        print()

        print(
            json.dumps(
                output,
                ensure_ascii=False,
                indent=2,
            )
        )

        print(
            "プレビューのみ。"
            "JSONは変更していません"
        )

        return 0

    if output == existing:
        print(
            "変更なし。"
            "JSONの書き換えを省略"
        )

        return 0

    write_json_atomic(
        OUTPUT,
        output,
    )

    print(
        f"保存完了: {OUTPUT}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )


#!/usr/bin/env python3
"""Prepare FIELD//BASE research CSV without losing review progress."""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "src" / "data"
GENERATED = DATA / "generated"

FIELDS_TS = DATA / "fields.ts"
LOCATIONS_TS = DATA / "fieldLocations.ts"
VERIFIED_JSON = GENERATED / "verifiedFieldLocations.json"
OUTPUT = GENERATED / "fieldResearch.csv"

COLUMNS = [
    "field_id",
    "field_name",
    "prefecture",
    "city",
    "address",
    "address_quality",
    "website",
    "website_status",
    "maps_search_url",
    "official_site_search_url",
    "confirmed_official_url",
    "latitude",
    "longitude",
    "business_status",
    "review_status",
    "notes",
    "candidate_latitude",
    "candidate_longitude",
    "candidate_source",
    "candidate_status",
    "candidate_map_url",
]

PRESERVED_COLUMNS = [
    "confirmed_official_url",
    "latitude",
    "longitude",
    "business_status",
    "review_status",
    "notes",
    "candidate_latitude",
    "candidate_longitude",
    "candidate_source",
    "candidate_status",
    "candidate_map_url",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(f"JSON形式が不正です: {path}")

    return data


def extract_field_blocks(source: str) -> list[str]:
    blocks = []
    pattern = re.compile(r"\bcreateField\s*\(\s*\{")

    for match in pattern.finditer(source):
        start = match.end()
        depth = 1
        index = start
        quote_char = None
        escaped = False

        while index < len(source):
            char = source[index]

            if quote_char is not None:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote_char:
                    quote_char = None

            elif char in ("'", '"', "`"):
                quote_char = char

            elif char == "{":
                depth += 1

            elif char == "}":
                depth -= 1

                if depth == 0:
                    blocks.append(source[start:index])
                    break

            index += 1

    return blocks


def extract_string(block: str, key: str) -> str:
    pattern = re.compile(
        rf"\b{re.escape(key)}\s*:\s*"
        r"(['\"])((?:\\.|(?!\1).)*)\1",
        re.DOTALL,
    )

    match = pattern.search(block)

    if match is None:
        return ""

    return (
        match.group(2)
        .replace("\\'", "'")
        .replace('\\"', '"')
        .strip()
    )


def load_react_fields() -> list[dict]:
    source = FIELDS_TS.read_text(encoding="utf-8")
    fields = []
    seen_ids = set()

    for block in extract_field_blocks(source):
        field_id = extract_string(block, "id")

        if not field_id:
            continue

        if field_id in seen_ids:
            raise ValueError(
                f"施設IDが重複しています: {field_id}"
            )

        seen_ids.add(field_id)

        field = {
            "id": field_id,
            "name": extract_string(block, "name"),
            "prefecture": extract_string(
                block, "prefecture"
            ),
            "city": extract_string(block, "city"),
            "address": extract_string(block, "address"),
            "website": extract_string(block, "website"),
        }

        if not field["address"]:
            field["address"] = (
                field["prefecture"]
                + field["city"]
                + "（詳細住所未確認）"
            )

        fields.append(field)

    return fields


def load_registered_locations() -> set[str]:
    registered = set(read_json(VERIFIED_JSON).keys())

    if LOCATIONS_TS.exists():
        source = LOCATIONS_TS.read_text(encoding="utf-8")

        registered.update(
            re.findall(
                r"""['"]([^'"]+)['"]\s*:\s*\{\s*latitude\s*:""",
                source,
            )
        )

    return registered


def address_quality(address: str) -> str:
    if not address:
        return "missing"

    if "詳細住所未確認" in address:
        return "needs_review"

    if re.search(r"\d+", address):
        return "detailed"

    return "coarse"


def maps_url(query: str) -> str:
    return (
        "https://www.google.com/maps/search/"
        "?api=1&query=" + quote(query)
    )


def search_url(query: str) -> str:
    return (
        "https://www.google.com/search?q="
        + quote(query)
    )


def read_previous_progress() -> dict[str, dict]:
    if not OUTPUT.exists():
        return {}

    with OUTPUT.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if "field_id" not in (reader.fieldnames or []):
            raise ValueError(
                "既存CSVにfield_id列がありません"
            )

        previous = {}

        for row in reader:
            field_id = (row.get("field_id") or "").strip()

            if not field_id:
                continue

            if field_id in previous:
                raise ValueError(
                    f"既存CSVに施設IDの重複があります: {field_id}"
                )

            previous[field_id] = row

        return previous


def preserve_progress(
    rows: list[dict],
    previous: dict[str, dict],
) -> int:
    preserved = 0

    for row in rows:
        old = previous.get(row["field_id"])

        if old is None:
            continue

        for column in PRESERVED_COLUMNS:
            value = old.get(column)

            if value is None or value == "":
                continue

            row[column] = value
            preserved += 1

    return preserved


def backup_existing_csv() -> Path | None:
    if not OUTPUT.exists():
        return None

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup = OUTPUT.with_name(
        f"fieldResearch.backup.{timestamp}.csv"
    )

    shutil.copy2(OUTPUT, backup)

    return backup


def save_csv(rows: list[dict]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=OUTPUT.parent,
            prefix=".fieldResearch_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)

            writer = csv.DictWriter(
                file,
                fieldnames=COLUMNS,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(rows)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, OUTPUT)

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()


def build_rows(
    fields: list[dict],
    registered: set[str],
) -> list[dict]:
    rows = []

    for field in fields:
        field_id = field["id"]

        if field_id in registered:
            continue

        name = field["name"]
        address = field["address"]
        website = field["website"]

        rows.append(
            {
                "field_id": field_id,
                "field_name": name,
                "prefecture": field["prefecture"],
                "city": field["city"],
                "address": address,
                "address_quality": address_quality(
                    address
                ),
                "website": website,
                "website_status": (
                    "registered"
                    if website.startswith(
                        ("https://", "http://")
                    )
                    else "missing"
                ),
                "maps_search_url": maps_url(
                    name + " " + address
                ),
                "official_site_search_url": (
                    search_url(
                        name + " サバゲー 公式サイト"
                    )
                ),
                "confirmed_official_url": "",
                "latitude": "",
                "longitude": "",
                "business_status": "unverified",
                "review_status": "pending",
                "notes": "",
                "candidate_latitude": "",
                "candidate_longitude": "",
                "candidate_source": "",
                "candidate_status": "",
                "candidate_map_url": "",
            }
        )

    rows.sort(
        key=lambda row: (
            row["website_status"] != "missing",
            row["address_quality"] != "detailed",
            row["prefecture"],
            row["field_name"],
        )
    )

    return rows


def main() -> None:
    fields = load_react_fields()
    registered = load_registered_locations()

    rows = build_rows(fields, registered)
    previous = read_previous_progress()

    preserved = preserve_progress(rows, previous)
    backup = backup_existing_csv()

    save_csv(rows)

    detailed = sum(
        row["address_quality"] == "detailed"
        for row in rows
    )

    needs_review = sum(
        row["address_quality"] == "needs_review"
        for row in rows
    )

    missing_urls = sum(
        row["website_status"] == "missing"
        for row in rows
    )

    verified_pending = sum(
        row["review_status"].strip().lower()
        == "verified"
        for row in rows
    )

    candidates = sum(
        bool(row["candidate_latitude"])
        and bool(row["candidate_longitude"])
        for row in rows
    )

    print()
    print("FIELD//BASE 施設調査CSV")
    print("=" * 40)
    print(f"React登録施設数: {len(fields)}")
    print(f"座標登録済み: {len(registered)}")
    print(f"調査対象: {len(rows)}")
    print(f"詳細住所あり: {detailed}")
    print(f"詳細住所未確認: {needs_review}")
    print(f"公式URL未登録: {missing_urls}")
    print(f"引き継いだ調査項目数: {preserved}")
    print(f"座標候補あり: {candidates}")
    print(f"座標確認済み・反映待ち: {verified_pending}")
    print(f"CSV出力: {OUTPUT}")

    if backup is not None:
        print(f"バックアップ: {backup}")

    print()
    print("先頭10施設:")

    for row in rows[:10]:
        print(
            f"{row['field_name']} "
            f"| {row['address']} "
            f"| {row['review_status']}"
        )


if __name__ == "__main__":
    main()

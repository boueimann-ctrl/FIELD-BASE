
#!/usr/bin/env python3
"""Geocode one FIELD//BASE research field at a time."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "src" / "data" / "generated"

CSV_PATH = GENERATED / "fieldResearch.csv"
CACHE_PATH = GENERATED / "geocodeResearchCache.json"

ENDPOINT = "https://nominatim.openstreetmap.org/search"

CANDIDATE_COLUMNS = [
    "candidate_latitude",
    "candidate_longitude",
    "candidate_source",
    "candidate_status",
    "candidate_map_url",
]

REQUIRED_COLUMNS = {
    "field_id",
    "field_name",
    "address",
    "address_quality",
    "review_status",
    "latitude",
    "longitude",
}

PROTECTED_STATUSES = {"verified", "rejected"}


def load_csv() -> tuple[list[str], list[dict]]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"調査CSVがありません: {CSV_PATH}"
        )

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        columns = list(reader.fieldnames or [])
        rows = list(reader)

    missing = REQUIRED_COLUMNS - set(columns)

    if missing:
        raise ValueError(
            "CSVに必要な列がありません: "
            + ", ".join(sorted(missing))
        )

    ids = [row["field_id"] for row in rows]

    if len(ids) != len(set(ids)):
        raise ValueError("施設IDが重複しています")

    for column in CANDIDATE_COLUMNS:
        if column not in columns:
            columns.append(column)

    return columns, rows


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {}

    data = json.loads(
        CACHE_PATH.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        raise ValueError("キャッシュJSONの形式が不正です")

    return data


def atomic_json_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".geocode_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary = Path(file.name)

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary, path)

    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def atomic_csv_write(
    columns: list[str],
    rows: list[dict],
) -> None:
    temporary = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=CSV_PATH.parent,
            prefix=".fieldResearch_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary = Path(file.name)

            writer = csv.DictWriter(
                file,
                fieldnames=columns,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(rows)

            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary, CSV_PATH)

    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def backup_csv() -> Path:
    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup = CSV_PATH.with_name(
        f"fieldResearch.backup.{timestamp}.csv"
    )

    shutil.copy2(CSV_PATH, backup)

    return backup


def has_coordinate(value: str) -> bool:
    return bool((value or "").strip())


def is_eligible(row: dict) -> bool:
    status = (
        row.get("review_status") or ""
    ).strip().lower()

    if status in PROTECTED_STATUSES:
        return False

    if row.get("address_quality") != "detailed":
        return False

    if has_coordinate(row.get("latitude", "")):
        return False

    if has_coordinate(row.get("longitude", "")):
        return False

    if has_coordinate(row.get("candidate_latitude", "")):
        return False

    if has_coordinate(row.get("candidate_longitude", "")):
        return False

    return True


def valid_coordinates(lat: object, lon: object) -> bool:
    try:
        latitude = float(lat)
        longitude = float(lon)
    except (TypeError, ValueError):
        return False

    return (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and 20 <= latitude <= 46
        and 122 <= longitude <= 154
    )


def geocode(address: str, user_agent: str) -> dict:
    parameters = urllib.parse.urlencode(
        {
            "q": address,
            "format": "jsonv2",
            "limit": 3,
            "countrycodes": "jp",
            "addressdetails": 1,
        }
    )

    url = ENDPOINT + "?" + parameters

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=20,
    ) as response:
        results = json.load(response)

    if not isinstance(results, list):
        raise ValueError("APIの応答形式が不正です")

    valid_results = [
        result
        for result in results
        if isinstance(result, dict)
        and valid_coordinates(
            result.get("lat"),
            result.get("lon"),
        )
    ]

    if not valid_results:
        return {
            "status": "no_match",
            "query": address,
            "checked_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "results": [],
        }

    return {
        "status": "candidate",
        "query": address,
        "checked_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "results": [
            {
                "latitude": result["lat"],
                "longitude": result["lon"],
                "display_name": result.get(
                    "display_name", ""
                ),
                "type": result.get("type", ""),
                "category": result.get(
                    "category", ""
                ),
                "place_rank": result.get(
                    "place_rank"
                ),
            }
            for result in valid_results
        ],
    }


def apply_candidate(row: dict, entry: dict) -> bool:
    if entry.get("status") != "candidate":
        return False

    results = entry.get("results", [])

    if not results:
        return False

    result = results[0]

    lat = result["latitude"]
    lon = result["longitude"]

    if not valid_coordinates(lat, lon):
        return False

    row["candidate_latitude"] = str(lat)
    row["candidate_longitude"] = str(lon)
    row["candidate_source"] = "nominatim_osm"
    row["candidate_status"] = "pending_manual_review"
    row["candidate_map_url"] = (
        "https://www.openstreetmap.org/"
        f"?mlat={lat}&mlon={lon}"
        f"#map=17/{lat}/{lon}"
    )

    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Geocode a single FIELD//BASE facility"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Show eligible facilities",
    )

    parser.add_argument(
        "--field",
        help="Field ID to geocode",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write candidate to research CSV",
    )

    args = parser.parse_args()

    columns, rows = load_csv()
    cache = load_cache()

    if args.list:
        print()
        print("座標候補を取得できる施設")
        print("=" * 45)

        count = 0

        for row in rows:
            if not is_eligible(row):
                continue

            count += 1

            print(
                f"{row['field_id']} | "
                f"{row['field_name']} | "
                f"{row['address']}"
            )

        print()
        print(f"対象施設: {count}件")
        return 0

    if not args.field:
        parser.error(
            "--list または --field を指定してください"
        )

    matches = [
        row
        for row in rows
        if row["field_id"] == args.field
    ]

    if not matches:
        print(f"施設が見つかりません: {args.field}")
        return 1

    row = matches[0]

    if not is_eligible(row):
        print(
            "対象外です。既存座標、候補座標、"
            "住所品質、確認状態を確認してください。"
        )
        return 1

    field_id = row["field_id"]
    address = row["address"]

    print()
    print(f"施設名: {row['field_name']}")
    print(f"住所: {address}")

    cache_entry = cache.get(field_id)

    if (
        isinstance(cache_entry, dict)
        and cache_entry.get("query") == address
        and cache_entry.get("status")
        in {"candidate", "no_match"}
    ):
        print("保存済みキャッシュを使用")
        entry = cache_entry

    else:
        user_agent = os.environ.get(
            "FIELD_BASE_GEOCODE_USER_AGENT", ""
        ).strip()

        if not user_agent:
            print()
            print(
                "環境変数 FIELD_BASE_GEOCODE_USER_AGENT "
                "を設定してください。"
            )
            print(
                "アプリ名と連絡可能なメールアドレス等を"
                "含む識別子が必要です。"
            )
            return 1

        print("Nominatimへ1件問い合わせます")

        try:
            entry = geocode(address, user_agent)

        except urllib.error.HTTPError as error:
            print(f"HTTPエラー: {error.code}")

            if error.code in (403, 429):
                print(
                    "アクセス制限の可能性があります。"
                    "再試行せず利用規約を確認してください。"
                )

            return 1

        except (
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            print(f"取得エラー: {error}")
            return 1

        cache[field_id] = entry
        atomic_json_write(CACHE_PATH, cache)

    if entry["status"] == "no_match":
        print()
        print("一致する住所が見つかりませんでした")
        print("結果はキャッシュに保存されています")
        return 0

    print()
    print("取得した座標候補")
    print("=" * 45)

    for index, result in enumerate(
        entry["results"],
        start=1,
    ):
        print(
            f"{index}. "
            f"{result['latitude']}, "
            f"{result['longitude']}"
        )
        print(
            f"   {result['display_name']}"
        )

    print()
    print(
        "注意: 最初の検索結果は施設位置として"
        "確認されていません。"
    )

    if not args.apply:
        print(
            "プレビューのみ。CSVへ保存するには"
            " --apply を指定してください。"
        )
        return 0

    if not apply_candidate(row, entry):
        print("候補を保存できませんでした")
        return 1

    backup = backup_csv()
    atomic_csv_write(columns, rows)

    print()
    print("CSVへの候補保存が完了しました")
    print(f"バックアップ: {backup}")
    print(
        "review_statusはpendingのままです。"
        "地図上で位置を確認してください。"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""FIELD//BASE: one-field geocoding candidate lookup."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]

AUTO_DATA = ROOT / "src/data/generated/fieldAutoData.json"
CACHE_FILE = ROOT / "src/data/generated/geocodeCache.json"
CANDIDATE_FILE = (
    ROOT / "src/data/generated/geocodeCandidates.json"
)

API_URL = "https://nominatim.openstreetmap.org/search"

USER_AGENT = (
    "FIELD-BASE/0.1 "
    "(https://github.com/boueimann-ctrl/FIELD-BASE)"
)


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(f"JSON形式が不正です: {path}")

    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        file.write("\n")

    temporary.replace(path)


def valid_coordinates(latitude: float, longitude: float) -> bool:
    return (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and 20 <= latitude <= 46
        and 122 <= longitude <= 154
    )


def lookup_address(address: str) -> list:
    params = urlencode(
        {
            "q": address,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 5,
            "countrycodes": "jp",
            "accept-language": "ja",
        }
    )

    request = Request(
        f"{API_URL}?{params}",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=20) as response:
        raw = response.read(200_000)

    result = json.loads(raw.decode("utf-8"))

    if not isinstance(result, list):
        raise ValueError("API応答が配列ではありません")

    return result


def normalize_candidates(results: list) -> list:
    candidates = []

    for item in results:
        if not isinstance(item, dict):
            continue

        try:
            latitude = float(item["lat"])
            longitude = float(item["lon"])
        except (KeyError, TypeError, ValueError):
            continue

        if not valid_coordinates(latitude, longitude):
            continue

        address_details = item.get("address", {})

        if not isinstance(address_details, dict):
            address_details = {}

        country_code = str(
            address_details.get("country_code", "")
        ).lower()

        if country_code != "jp":
            continue

        candidates.append(
            {
                "latitude": latitude,
                "longitude": longitude,
                "displayName": str(
                    item.get("display_name", "")
                ),
                "placeId": item.get("place_id"),
                "osmType": item.get("osm_type"),
                "osmId": item.get("osm_id"),
                "addressDetails": address_details,
                "status": "pending_manual_review",
            }
        )

    return candidates


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--field",
        required=True,
        help="FIELD//BASE facility ID",
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh a previously cached lookup",
    )

    args = parser.parse_args()

    auto_data = read_json(AUTO_DATA)
    field = auto_data.get(args.field)

    if not isinstance(field, dict):
        print("指定施設の自動収集データがありません")
        return 1

    address = field.get("address")

    if not isinstance(address, str) or not address.strip():
        print("検証済み住所がありません")
        return 1

    address = address.strip()

    cache = read_json(CACHE_FILE)
    candidates_data = read_json(CANDIDATE_FILE)

    cached = cache.get(address)

    if (
        isinstance(cached, dict)
        and not args.refresh
        and isinstance(cached.get("results"), list)
    ):
        print("キャッシュを使用します")
        results = cached["results"]
    else:
        if os.environ.get("FIELD_BASE_GEOCODE_ONLINE") != "1":
            print(
                "オンライン照会には "
                "FIELD_BASE_GEOCODE_ONLINE=1 が必要です"
            )
            return 1

        print("住所を検索しています:", address)

        try:
            results = lookup_address(address)
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            print("通信エラー:", error)
            return 1
        except (ValueError, json.JSONDecodeError) as error:
            print("データ解析エラー:", error)
            return 1

        cache[address] = {
            "provider": "OpenStreetMap Nominatim",
            "retrievedAt": datetime.now(
                timezone.utc
            ).isoformat(),
            "results": results,
        }

        write_json(CACHE_FILE, cache)

    candidates = normalize_candidates(results)

    candidates_data[args.field] = {
        "address": address,
        "sourceUrl": field.get("sourceUrl"),
        "provider": "OpenStreetMap Nominatim",
        "attribution": "© OpenStreetMap contributors",
        "status": "pending_manual_review",
        "candidates": candidates,
    }

    write_json(CANDIDATE_FILE, candidates_data)

    print()
    print("施設ID:", args.field)
    print("住所:", address)
    print("候補数:", len(candidates))

    for index, candidate in enumerate(candidates, start=1):
        print()
        print(f"候補 {index}")
        print("緯度:", candidate["latitude"])
        print("経度:", candidate["longitude"])
        print("検索結果:", candidate["displayName"])

    print()
    print("候補は確認待ちです。地図には反映していません。")
    print("出典: © OpenStreetMap contributors")

    return 0


if __name__ == "__main__":
    sys.exit(main())

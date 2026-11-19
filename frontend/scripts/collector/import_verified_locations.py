
#!/usr/bin/env python3
"""Import manually verified field coordinates into FIELD//BASE.

Features:
- Import newly verified locations.
- Skip already registered locations when coordinates match.
- Reject conflicting coordinates.
- Reject duplicate coordinates across different facilities.
- Preview changes by default.
- Write JSON atomically with --apply.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "src" / "data" / "generated"

CSV_PATH = GENERATED / "fieldResearch.csv"
JSON_PATH = GENERATED / "verifiedFieldLocations.json"

VALID_LATITUDE = (20.0, 46.0)
VALID_LONGITUDE = (122.0, 154.0)

COORDINATE_TOLERANCE = 1e-7


def read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"座標データが見つかりません: {path}"
        )

    data = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        raise ValueError(
            "座標JSONのルートはオブジェクトである必要があります"
        )

    return data


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"調査CSVが見つかりません: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        required = {
            "field_id",
            "field_name",
            "latitude",
            "longitude",
            "review_status",
        }

        headers = set(reader.fieldnames or [])
        missing = required - headers

        if missing:
            raise ValueError(
                "CSVに必要な列がありません: "
                + ", ".join(sorted(missing))
            )

        return list(reader)


def validate_coordinates(
    latitude_text: object,
    longitude_text: object,
) -> tuple[float, float]:
    try:
        latitude = float(latitude_text)
        longitude = float(longitude_text)
    except (ValueError, TypeError) as error:
        raise ValueError(
            "緯度・経度は数値で入力してください"
        ) from error

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
    ):
        raise ValueError(
            "緯度・経度は有限の数値である必要があります"
        )

    if not (
        VALID_LATITUDE[0]
        <= latitude
        <= VALID_LATITUDE[1]
    ):
        raise ValueError(
            f"日本国内の想定緯度範囲外: {latitude}"
        )

    if not (
        VALID_LONGITUDE[0]
        <= longitude
        <= VALID_LONGITUDE[1]
    ):
        raise ValueError(
            f"日本国内の想定経度範囲外: {longitude}"
        )

    return latitude, longitude


def coordinates_match(
    first: tuple[float, float],
    second: tuple[float, float],
) -> bool:
    return (
        abs(first[0] - second[0])
        <= COORDINATE_TOLERANCE
        and abs(first[1] - second[1])
        <= COORDINATE_TOLERANCE
    )


def get_existing_coordinates(
    field_id: str,
    item: object,
) -> tuple[float, float]:
    if not isinstance(item, dict):
        raise ValueError(
            f"既存JSONのデータ形式が不正です: {field_id}"
        )

    try:
        return validate_coordinates(
            item.get("latitude"),
            item.get("longitude"),
        )
    except ValueError as error:
        raise ValueError(
            f"既存JSONの座標が不正です: "
            f"{field_id}: {error}"
        ) from error


def find_duplicate_coordinate(
    field_id: str,
    coordinates: tuple[float, float],
    registered: dict[str, tuple[float, float]],
) -> str | None:
    for other_id, other_coordinates in registered.items():
        if other_id == field_id:
            continue

        if coordinates_match(
            coordinates,
            other_coordinates,
        ):
            return other_id

    return None


def write_json_atomic(
    path: Path,
    data: dict,
) -> None:
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
            prefix=".verified_locations_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)

            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )

            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

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


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Import verified coordinates "
            "from fieldResearch.csv"
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Update verifiedFieldLocations.json",
    )

    args = parser.parse_args()

    rows = read_csv(CSV_PATH)
    existing = read_json(JSON_PATH)

    updates: dict[str, dict] = {}
    errors: list[str] = []

    skipped_unverified = 0
    skipped_existing = 0
    seen_ids: set[str] = set()

    registered_coordinates: dict[
        str, tuple[float, float]
    ] = {}

    for field_id, item in existing.items():
        try:
            registered_coordinates[field_id] = (
                get_existing_coordinates(
                    field_id,
                    item,
                )
            )
        except ValueError as error:
            errors.append(str(error))

    for row_number, row in enumerate(
        rows,
        start=2,
    ):
        field_id = (
            row.get("field_id") or ""
        ).strip()

        field_name = (
            row.get("field_name") or ""
        ).strip()

        status = (
            row.get("review_status") or ""
        ).strip().lower()

        if status != "verified":
            skipped_unverified += 1
            continue

        if not field_id:
            errors.append(
                f"{row_number}行目: "
                "施設IDがありません"
            )
            continue

        if field_id in seen_ids:
            errors.append(
                f"{row_number}行目: "
                f"施設IDが重複しています: {field_id}"
            )
            continue

        seen_ids.add(field_id)

        try:
            coordinates = validate_coordinates(
                row.get("latitude"),
                row.get("longitude"),
            )
        except ValueError as error:
            errors.append(
                f"{row_number}行目: "
                f"{field_name}: {error}"
            )
            continue

        latitude, longitude = coordinates

        if field_id in registered_coordinates:
            existing_coordinates = (
                registered_coordinates[field_id]
            )

            if coordinates_match(
                coordinates,
                existing_coordinates,
            ):
                skipped_existing += 1
                continue

            errors.append(
                f"{row_number}行目: "
                f"{field_name} は登録済みですが、"
                "座標が一致しません。"
                f" JSON={existing_coordinates},"
                f" CSV={coordinates}"
            )
            continue

        duplicate_id = find_duplicate_coordinate(
            field_id,
            coordinates,
            registered_coordinates,
        )

        if duplicate_id is not None:
            errors.append(
                f"{row_number}行目: "
                f"{field_name} の座標は "
                f"{duplicate_id} と重複しています"
            )
            continue

        updates[field_id] = {
            "latitude": latitude,
            "longitude": longitude,
        }

        registered_coordinates[field_id] = coordinates

    print()
    print("FIELD//BASE 座標インポート")
    print("=" * 40)
    print(f"CSV調査対象: {len(rows)}")
    print(f"既存JSON登録数: {len(existing)}")
    print(f"今回の新規登録候補: {len(updates)}")
    print(f"登録済み・一致スキップ: {skipped_existing}")
    print(f"未確認・スキップ: {skipped_unverified}")
    print(f"エラー: {len(errors)}")
    print()

    for field_id, coordinates in updates.items():
        print(
            f"[追加候補] {field_id}: "
            f"{coordinates['latitude']}, "
            f"{coordinates['longitude']}"
        )

    if errors:
        print()
        print("検証エラー:")

        for error in errors:
            print(f"- {error}")

        print()
        print(
            "エラーがあるためJSONは更新しません"
        )
        return 1

    if not updates:
        print(
            "新規登録する座標はありません。"
            "既存データはそのまま保持します。"
        )
        return 0

    if not args.apply:
        print()
        print(
            "プレビューのみです。"
            "JSONは変更していません"
        )
        print(
            "反映するには --apply を指定してください"
        )
        return 0

    merged = {
        **existing,
        **updates,
    }

    write_json_atomic(
        JSON_PATH,
        merged,
    )

    print()
    print(f"登録完了: {JSON_PATH}")
    print(f"JSON登録数: {len(merged)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

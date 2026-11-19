
#!/usr/bin/env python3
"""Merge existing map candidates into the FIELD//BASE research CSV."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "src" / "data" / "generated"

CSV_PATH = GENERATED / "fieldResearch.csv"
CANDIDATES_PATH = GENERATED / "mapCandidates.json"

REQUIRED_COLUMNS = {
    "field_id",
    "field_name",
    "latitude",
    "longitude",
    "review_status",
    "notes",
}

CANDIDATE_COLUMNS = [
    "candidate_latitude",
    "candidate_longitude",
    "candidate_source",
    "candidate_status",
    "candidate_map_url",
]

PROTECTED_STATUSES = {"verified", "rejected"}


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"候補JSONが見つかりません: {path}"
        )

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("候補JSONはオブジェクト形式が必要です")

    return data


def load_csv(path: Path) -> tuple[list[str], list[dict]]:
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
        columns = list(reader.fieldnames or [])
        rows = list(reader)

    missing = REQUIRED_COLUMNS - set(columns)

    if missing:
        raise ValueError(
            "必要なCSV列がありません: "
            + ", ".join(sorted(missing))
        )

    ids = [row["field_id"] for row in rows]

    if len(ids) != len(set(ids)):
        raise ValueError("CSVに施設IDの重複があります")

    return columns, rows


def valid_coordinate(lat: object, lon: object) -> bool:
    try:
        latitude = float(lat)
        longitude = float(lon)
    except (ValueError, TypeError):
        return False

    return (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and 20 <= latitude <= 46
        and 122 <= longitude <= 154
    )


def select_candidate(item: dict) -> dict | None:
    candidates = item.get("candidates", [])

    if not isinstance(candidates, list):
        return None

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        latitude = candidate.get("latitude")
        longitude = candidate.get("longitude")

        if not valid_coordinate(latitude, longitude):
            continue

        return candidate

    return None


def save_csv(
    path: Path,
    columns: list[str],
    rows: list[dict],
) -> None:
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            dir=path.parent,
            prefix=".fieldResearch_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)

            writer = csv.DictWriter(
                file,
                fieldnames=columns,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(rows)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, path)

    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect field coordinate candidates"
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Update fieldResearch.csv",
    )

    args = parser.parse_args()

    columns, rows = load_csv(CSV_PATH)
    candidate_data = load_json(CANDIDATES_PATH)

    for column in CANDIDATE_COLUMNS:
        if column not in columns:
            columns.append(column)

    updated = 0
    already_filled = 0
    unavailable = 0

    for row in rows:
        field_id = row["field_id"]
        status = (
            row.get("review_status") or ""
        ).strip().lower()

        if status in PROTECTED_STATUSES:
            already_filled += 1
            continue

        item = candidate_data.get(field_id)

        if not isinstance(item, dict):
            unavailable += 1
            continue

        candidate = select_candidate(item)

        if candidate is None:
            unavailable += 1
            continue

        if (
            (row.get("candidate_latitude") or "").strip()
            or (row.get("candidate_longitude") or "").strip()
        ):
            already_filled += 1
            continue

        row["candidate_latitude"] = str(
            candidate["latitude"]
        )
        row["candidate_longitude"] = str(
            candidate["longitude"]
        )
        row["candidate_source"] = str(
            candidate.get("coordinateType", "")
        )
        row["candidate_status"] = "pending_manual_review"
        row["candidate_map_url"] = str(
            candidate.get("mapUrl", "")
        )

        updated += 1

        print(
            f"[候補] {row['field_name']}: "
            f"{row['candidate_latitude']}, "
            f"{row['candidate_longitude']}"
        )

    print()
    print("FIELD//BASE 座標候補収集")
    print("=" * 40)
    print(f"調査対象: {len(rows)}")
    print(f"今回の追加候補: {updated}")
    print(f"既存候補・確認済み: {already_filled}")
    print(f"候補なし: {unavailable}")

    if not args.apply:
        print()
        print("プレビューのみ。CSVは変更していません")
        print("反映するには --apply を指定してください")
        return 0

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup = CSV_PATH.with_name(
        f"fieldResearch.backup.{timestamp}.csv"
    )

    shutil.copy2(CSV_PATH, backup)

    save_csv(CSV_PATH, columns, rows)

    print()
    print(f"CSV更新完了: {CSV_PATH}")
    print(f"バックアップ: {backup}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

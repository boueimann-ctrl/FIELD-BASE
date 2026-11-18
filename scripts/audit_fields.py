
#!/usr/bin/env python3
"""
FIELD//BASE 掲載情報監査

対象:
- frontend/src/data/fields.ts
- frontend/src/data/fieldVerification.ts
- frontend/src/data/fieldLocations.ts

機能:
- 登録フィールド数
- ID重複
- 公式URL未登録
- 詳細住所未確認
- 料金未確認
- 座標未登録
- 確認日未登録
- 不正な確認日
- 不正な座標
- 登録IDと補足情報の整合性

注意:
- TypeScriptを実行するプログラムではありません。
- 現在の createField({...}) 形式を解析します。
- URLの存在や施設の営業状況は検証しません。
"""

from __future__ import annotations

import ast
import re
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "frontend" / "src" / "data"

FIELDS_FILE = DATA_DIR / "fields.ts"
VERIFICATION_FILE = DATA_DIR / "fieldVerification.ts"
LOCATIONS_FILE = DATA_DIR / "fieldLocations.ts"

DIRECTORY_SOURCE = (
    "https://sightin.jp/field/map/?area=kanto"
)


def read_file(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"ファイルがありません: {path}")

    return path.read_text(encoding="utf-8")


def extract_braced_block(
    text: str,
    start: int,
) -> tuple[str, int]:
    """
    { から対応する } までを取得する。
    文字列内の括弧は無視する。
    """
    if start >= len(text) or text[start] != "{":
        raise ValueError("オブジェクトの開始位置が不正です")

    depth = 0
    quote = None
    escaped = False

    for index in range(start, len(text)):
        char = text[index]

        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue

        if char in ("'", '"', "`"):
            quote = char
            continue

        if char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth == 0:
                return text[start:index + 1], index + 1

    raise ValueError("対応する閉じ括弧が見つかりません")


def parse_properties(block: str) -> dict[str, object]:
    """
    現在のTypeScriptデータで使われる
    単純なプロパティを抽出する。

    複雑な式は評価しない。
    """
    result: dict[str, object] = {}

    pattern = re.compile(
        r"""(?m)^\s*
        (?P<key>[a-zA-Z_][a-zA-Z0-9_]*)
        \s*:\s*
        (?P<value>
            '(?:\\.|[^'\\])*'
            |"(?:\\.|[^"\\])*"
            |true
            |false
            |null
            |-?\d+(?:\.\d+)?
        )
        \s*,?
        \s*(?://[^\n]*)?
        $""",
        re.VERBOSE,
    )

    for match in pattern.finditer(block):
        key = match.group("key")
        raw = match.group("value")

        if raw == "true":
            value = True
        elif raw == "false":
            value = False
        elif raw == "null":
            value = None
        elif raw.startswith(("'", '"')):
            try:
                value = ast.literal_eval(raw)
            except (SyntaxError, ValueError):
                value = raw[1:-1]
        elif "." in raw:
            value = float(raw)
        else:
            value = int(raw)

        result[key] = value

    return result


def parse_fields(text: str) -> list[dict[str, object]]:
    fields = []

    pattern = re.compile(r"\bcreateField\s*\(\s*\{")

    for match in pattern.finditer(text):
        start = text.find("{", match.start())
        block, _ = extract_braced_block(text, start)
        data = parse_properties(block)

        if "id" not in data:
            raise ValueError(
                "createFieldにidがありません: "
                + block[:100]
            )

        fields.append(data)

    return fields


def parse_verification(
    text: str,
) -> dict[str, dict[str, object]]:
    result = {}

    start_match = re.search(
        r"const\s+verifiedFields\b[^=]*=\s*\{",
        text,
    )

    if not start_match:
        raise ValueError(
            "verifiedFieldsの定義が見つかりません"
        )

    start = text.find("{", start_match.start())
    outer, _ = extract_braced_block(text, start)

    pattern = re.compile(r"""['"]([^'"]+)['"]\s*:\s*\{""")

    for match in pattern.finditer(outer):
        field_id = match.group(1)
        brace_start = outer.find("{", match.start())
        block, _ = extract_braced_block(
            outer,
            brace_start,
        )
        result[field_id] = parse_properties(block)

    return result


def parse_locations(
    text: str,
) -> dict[str, dict[str, object]]:
    result = {}

    start_match = re.search(
        r"export\s+const\s+fieldLocations\b[^=]*=\s*\{",
        text,
    )

    if not start_match:
        raise ValueError(
            "fieldLocationsの定義が見つかりません"
        )

    start = text.find("{", start_match.start())
    outer, _ = extract_braced_block(text, start)

    pattern = re.compile(r"""['"]([^'"]+)['"]\s*:\s*\{""")

    for match in pattern.finditer(outer):
        field_id = match.group(1)
        brace_start = outer.find("{", match.start())
        block, _ = extract_braced_block(
            outer,
            brace_start,
        )
        result[field_id] = parse_properties(block)

    return result


def valid_url(value: object) -> bool:
    if not isinstance(value, str):
        return False

    parsed = urlparse(value.strip())

    return (
        parsed.scheme in ("http", "https")
        and bool(parsed.netloc)
    )


def valid_date(value: object) -> bool:
    if not isinstance(value, str):
        return False

    try:
        parsed = date.fromisoformat(value)
        return parsed <= date.today()
    except ValueError:
        return False


def valid_coordinates(
    location: dict[str, object],
) -> bool:
    lat = location.get("latitude")
    lon = location.get("longitude")

    if isinstance(lat, bool) or isinstance(lon, bool):
        return False

    if not isinstance(lat, (int, float)):
        return False

    if not isinstance(lon, (int, float)):
        return False

    return -90 <= lat <= 90 and -180 <= lon <= 180


def audit() -> None:
    fields = parse_fields(read_file(FIELDS_FILE))
    verification = parse_verification(
        read_file(VERIFICATION_FILE)
    )
    locations = parse_locations(
        read_file(LOCATIONS_FILE)
    )

    ids = [str(field["id"]) for field in fields]
    counts = Counter(ids)
    duplicate_ids = sorted(
        field_id
        for field_id, count in counts.items()
        if count > 1
    )

    field_ids = set(ids)

    unknown_verification = sorted(
        set(verification) - field_ids
    )

    unknown_locations = sorted(
        set(locations) - field_ids
    )

    issues: dict[str, list[str]] = {
        "公式URL未登録": [],
        "詳細住所未確認": [],
        "料金未確認": [],
        "座標未登録": [],
        "確認日未登録": [],
        "確認日が不正": [],
        "座標が不正": [],
    }

    priorities = []

    for field in fields:
        field_id = str(field["id"])
        name = str(field.get("name", field_id))

        verified = verification.get(field_id, {})
        location = locations.get(field_id)

        website = verified.get(
            "website",
            field.get("website", ""),
        )

        address = verified.get(
            "address",
            field.get("address", ""),
        )

        verified_at = verified.get(
            "verifiedAt",
            field.get("verifiedAt"),
        )

        # createFieldではpriceの初期値がnull。
        price = field.get("price")

        missing = []

        if not valid_url(website):
            issues["公式URL未登録"].append(name)
            missing.append("公式URL")

        if (
            not isinstance(address, str)
            or not address.strip()
            or "未確認" in address
        ):
            issues["詳細住所未確認"].append(name)
            missing.append("住所")

        if price is None:
            issues["料金未確認"].append(name)
            missing.append("料金")

        if location is None:
            issues["座標未登録"].append(name)
            missing.append("座標")
        elif not valid_coordinates(location):
            issues["座標が不正"].append(name)
            missing.append("座標不正")

        if verified_at is None:
            issues["確認日未登録"].append(name)
            missing.append("確認日")
        elif not valid_date(verified_at):
            issues["確認日が不正"].append(name)
            missing.append("確認日不正")

        if missing:
            priorities.append(
                (
                    len(missing),
                    name,
                    field_id,
                    missing,
                )
            )

    priorities.sort(
        key=lambda item: (-item[0], item[1])
    )

    print()
    print("=" * 54)
    print("FIELD//BASE DATA AUDIT")
    print("=" * 54)
    print(f"登録フィールド数: {len(fields)}")
    print(f"公式情報の補足登録: {len(verification)}")
    print(f"座標登録: {len(locations)}")
    print()

    print("不足・確認項目")
    print("-" * 54)

    for label, names in issues.items():
        print(f"{label}: {len(names)}件")

    print()
    print("データ整合性")
    print("-" * 54)

    print(f"重複ID: {len(duplicate_ids)}件")
    print(
        "存在しないIDの公式情報: "
        f"{len(unknown_verification)}件"
    )
    print(
        "存在しないIDの座標: "
        f"{len(unknown_locations)}件"
    )

    if duplicate_ids:
        print("重複ID:", ", ".join(duplicate_ids))

    if unknown_verification:
        print(
            "不明な公式情報ID:",
            ", ".join(unknown_verification),
        )

    if unknown_locations:
        print(
            "不明な座標ID:",
            ", ".join(unknown_locations),
        )

    print()
    print("優先確認フィールド TOP 15")
    print("-" * 54)

    for index, (
        count,
        name,
        field_id,
        missing,
    ) in enumerate(priorities[:15], start=1):
        print(
            f"{index:2}. {name} [{field_id}]"
            f" / {count}項目"
        )
        print("    " + "・".join(missing))

    print()
    print("注意:")
    print(
        "- 公式URLの登録は公式サイトの"
        "真正性や稼働を保証しません。"
    )
    print(
        "- 料金未確認は、createFieldの"
        "初期値nullを基準に判定しています。"
    )
    print(
        "- 住所が入力されていても"
        "正確性の検証はしていません。"
    )
    print(
        "- 確認日は登録内容の形式を確認するだけで、"
        "実際の確認作業を保証しません。"
    )
    print("=" * 54)


if __name__ == "__main__":
    try:
        audit()
    except (OSError, ValueError) as error:
        print(f"監査エラー: {error}")
        raise SystemExit(1) from error

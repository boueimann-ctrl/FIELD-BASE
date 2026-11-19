
#!/usr/bin/env python3
"""FIELD//BASE official HTML address candidate collector.

Extract possible facility addresses from official HTML pages.

Safety:
- Reuse the existing robots.txt-aware HTML fetcher.
- Use only human-confirmed official website URLs.
- Match candidate addresses against registered prefecture/city.
- Never modify published field data or research CSV.
- Require --apply to save candidate JSON.
- Preserve previous candidates if collection fails.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
import time

from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from collect_fields import (
    REQUEST_DELAY,
    fetch_html,
    load_confirmed_official_urls,
)

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "src" / "data" / "generated"

RESEARCH_CSV = GENERATED / "fieldResearch.csv"
OUTPUT = GENERATED / "addressCandidates.json"

PREFECTURES = (
    "北海道",
    "青森県", "岩手県", "宮城県", "秋田県",
    "山形県", "福島県", "茨城県", "栃木県",
    "群馬県", "埼玉県", "千葉県", "東京都",
    "神奈川県", "新潟県", "富山県", "石川県",
    "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県",
    "京都府", "大阪府", "兵庫県", "奈良県",
    "和歌山県", "鳥取県", "島根県", "岡山県",
    "広島県", "山口県", "徳島県", "香川県",
    "愛媛県", "高知県", "福岡県", "佐賀県",
    "長崎県", "熊本県", "大分県", "宮崎県",
    "鹿児島県", "沖縄県",
)

PREFECTURE_PATTERN = "|".join(
    re.escape(value)
    for value in sorted(
        PREFECTURES,
        key=len,
        reverse=True,
    )
)

ADDRESS_PATTERN = re.compile(
    rf"(?:{PREFECTURE_PATTERN})"
    r"[^\s<>「」『』【】]{3,90}"
)

POSTAL_PATTERN = re.compile(
    r"〒?\s*\d{3}[-－]\d{4}"
)


class VisibleTextParser(HTMLParser):
    """Extract visible-ish HTML text without executing JavaScript."""

    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "template",
    }

    def __init__(self):
        super().__init__(
            convert_charrefs=True
        )

        self.skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if self.skip_depth:
            self.skip_depth += 1
            return

        if tag in self.SKIP_TAGS:
            self.skip_depth = 1
            return

        if tag in {
            "br", "p", "div", "li",
            "tr", "section", "footer",
            "header", "address",
        }:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if not self.skip_depth and tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
            return

        if tag in {
            "p", "div", "li", "tr",
            "section", "address",
        }:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)

    def get_text(self):
        return "".join(self.parts)


def normalize(value):
    return re.sub(
        r"[\s\u3000・／/（）()\[\]【】\-_.]+",
        "",
        str(value).casefold(),
    )


def clean_address(value):
    value = value.strip()

    value = POSTAL_PATTERN.sub(
        "",
        value,
    ).strip()

    value = re.split(
        r"[、。，,;；|｜]",
        value,
        maxsplit=1,
    )[0]

    value = re.split(
        r"(?:TEL|FAX|電話|営業時間|定休日|アクセス)",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    return value.strip(
        " \t\r\n:：-－"
    )


def load_research():
    with RESEARCH_CSV.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        required = {
            "field_id",
            "field_name",
            "prefecture",
            "city",
            "address",
        }

        missing = required - set(
            reader.fieldnames or []
        )

        if missing:
            raise ValueError(
                "CSVの必須列がありません: "
                + ", ".join(sorted(missing))
            )

        return list(reader)


def extract_candidates(html, prefecture, city):
    parser = VisibleTextParser()
    parser.feed(html)

    text = parser.get_text()

    # HTMLのタグ境界で分断された住所にも対応するため、
    # 行単位のテキストを利用する。
    lines = [
        re.sub(r"[ \t\u3000]+", "", line)
        for line in text.splitlines()
    ]

    found = set()

    for line in lines:
        for match in ADDRESS_PATTERN.finditer(line):
            address = clean_address(
                match.group()
            )

            if not address.startswith(prefecture):
                continue

            if normalize(city) not in normalize(address):
                continue

            if len(address) > 100:
                continue

            found.add(address)

    return sorted(
        found,
        key=lambda value: (
            len(value),
            value,
        ),
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
            "住所候補JSONはオブジェクト形式が必要です"
        )

    return data


def write_atomic(data):
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=OUTPUT.parent,
            prefix=".address_candidates_",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary = Path(file.name)

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
            temporary,
            OUTPUT,
        )

    finally:
        if (
            temporary is not None
            and temporary.exists()
        ):
            temporary.unlink()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=0,
    )

    parser.add_argument(
        "--apply",
        action="store_true",
    )

    args = parser.parse_args()

    if args.limit < 0:
        parser.error(
            "--limit must be zero or greater"
        )

    rows = load_research()

    confirmed_urls = (
        load_confirmed_official_urls()
    )

    output = load_existing()
    robots_cache = {}

    checked = 0
    found = 0

    today = datetime.now(
        timezone.utc
    ).date().isoformat()

    for row in rows:
        field_id = row["field_id"].strip()

        url = confirmed_urls.get(
            field_id
        )

        if not url:
            continue

        if args.limit and checked >= args.limit:
            break

        checked += 1

        print(
            f"\n[{checked}] {row['field_name']}"
        )

        diagnostics = {}

        html = fetch_html(
            url,
            robots_cache,
            diagnostics,
        )

        time.sleep(REQUEST_DELAY)

        if html is None:
            print(
                "  HTML取得失敗: "
                + diagnostics.get(
                    "reason",
                    "不明",
                )
            )
            continue

        prefecture = row[
            "prefecture"
        ].strip()

        city = row[
            "city"
        ].strip()

        if not prefecture or not city:
            print(
                "  都道府県・市区町村が未登録"
            )
            continue

        candidates = extract_candidates(
            html,
            prefecture,
            city,
        )

        if not candidates:
            print(
                "  住所候補なし"
            )
            continue

        found += 1

        print(
            f"  住所候補: {len(candidates)}件"
        )

        for address in candidates:
            print(
                f"    - {address}"
            )

        output[field_id] = {
            "fieldName": row[
                "field_name"
            ],
            "registeredAddress": row[
                "address"
            ],
            "candidateAddresses": candidates,
            "sourceUrl": url,
            "sourceType": "official_html",
            "reviewStatus": "pending",
            "collectedAt": today,
        }

    print()
    print("=" * 40)
    print("住所候補収集結果")
    print("=" * 40)

    print(
        f"取得対象: {checked}施設"
    )

    print(
        f"住所候補あり: {found}施設"
    )

    print(
        f"候補保存対象: {len(output)}施設"
    )

    if not args.apply:
        print(
            "プレビューのみ。ファイルは変更していません"
        )
        return 0

    if output == load_existing():
        print(
            "変更なし。JSONの書き換えを省略"
        )
        return 0

    write_atomic(output)

    print(
        f"保存完了: {OUTPUT}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

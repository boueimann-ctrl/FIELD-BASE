
#!/usr/bin/env python3
"""FIELD//BASE official HTML address candidate collector.

Collect address candidates from human-confirmed official websites.

Safety:
- Reuse the robots.txt-aware HTML fetcher.
- Do not modify published data or research CSV.
- Require --apply to save candidate JSON.
- Preserve existing candidates when collection fails.
- Never automatically approve extracted addresses.
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
import unicodedata

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
    r"[^\s<>「」『』【】]{3,100}"
)

POSTAL_PATTERN = re.compile(
    r"〒?\s*\d{3}[-－]\d{4}"
)

# A numeric address component is required.
# Examples:
#   十余一60-15
#   十余一60番地15
#   西新宿2丁目8-1
NUMBER_PATTERN = re.compile(
    r"\d+(?:丁目|番地|番|号|[-－−ー]\d+)"
)

AREA_PATTERN = re.compile(
    r"\d+(?:\.\d+)?"
    r"(?:㎡|m²|m2|平方メートル|坪|ヘクタール|ha)"
    r"(?:の|を|で|ある|以上|以下|超)?",
    re.IGNORECASE,
)

DESCRIPTION_WORDS = (
    "サバイバルゲーム",
    "サバゲー",
    "フィールド",
    "施設紹介",
    "営業時間",
    "アクセス方法",
    "定例会",
    "予約受付",
    "レンタル",
    "イベント",
)

ADDRESS_STOP_WORDS = (
    "電話",
    "TEL",
    "FAX",
    "営業時間",
    "定休日",
    "アクセス",
    "お問い合わせ",
    "サバイバルゲーム",
    "サバゲー",
    "フィールド",
    "施設紹介",
    "定例会",
    "予約受付",
    "レンタル",
    "イベント",
)

# These characters can appear inside Japanese street addresses.
ADDRESS_SUFFIX_PATTERN = re.compile(
    r"^[一-龥々〆ヶぁ-んァ-ヶA-Za-z0-9"
    r"－−ー\-丁目番地号条東西南北"
    r"ノの大字字]+$"
)


class VisibleTextParser(HTMLParser):
    """Extract text without running scripts."""

    SKIP_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "template",
    }

    BLOCK_TAGS = {
        "br",
        "p",
        "div",
        "li",
        "tr",
        "section",
        "footer",
        "header",
        "address",
    }

    def __init__(self):
        super().__init__(
            convert_charrefs=True
        )

        self.skip_stack = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if self.skip_stack:
            self.skip_stack.append(tag)
            return

        if tag in self.SKIP_TAGS:
            self.skip_stack.append(tag)
            return

        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if not self.skip_stack and tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.skip_stack:
            # HTML may contain nested elements in skipped sections.
            if tag in self.skip_stack:
                while self.skip_stack:
                    current = self.skip_stack.pop()
                    if current == tag:
                        break
            return

        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_stack:
            self.parts.append(data)

    def get_text(self):
        return "".join(self.parts)


def normalize(value):
    value = unicodedata.normalize(
        "NFKC",
        str(value),
    )

    return re.sub(
        r"[\s\u3000・／/（）()\[\]【】\-_.]+",
        "",
        value.casefold(),
    )


def clean_address(value):
    value = unicodedata.normalize(
        "NFKC",
        str(value),
    ).strip()

    value = POSTAL_PATTERN.sub(
        "",
        value,
    ).strip()

    value = re.split(
        r"[、。，,;；|｜]",
        value,
        maxsplit=1,
    )[0]

    for word in ADDRESS_STOP_WORDS:
        match = re.search(
            re.escape(word),
            value,
            flags=re.IGNORECASE,
        )

        if match:
            value = value[:match.start()]

    return value.strip(
        " \t\r\n:：-－"
    )


def evaluate_address(address, prefecture, city):
    """Return (accepted, reason) for an address candidate."""

    if not address.startswith(prefecture):
        return False, "都道府県不一致"

    prefix = prefecture + city

    if not normalize(address).startswith(
        normalize(prefix)
    ):
        return False, "市区町村不一致"

    suffix = address[len(prefix):]

    if not suffix:
        return False, "町名・番地なし"

    if AREA_PATTERN.search(suffix):
        return False, "面積表記を含む"

    if any(
        word in suffix
        for word in DESCRIPTION_WORDS
    ):
        return False, "施設紹介文を含む"

    if len(address) > 100:
        return False, "文字数が長すぎる"

    if not NUMBER_PATTERN.search(suffix):
        return False, "番地形式なし"

    if not ADDRESS_SUFFIX_PATTERN.fullmatch(suffix):
        return False, "住所形式以外の文字を含む"

    # Avoid accepting a bare number such as "白井市16000".
    # A number must be preceded by a plausible town name,
    # or the address must use an explicit block/lot marker.
    first_number = re.search(
        r"\d+",
        suffix,
    )

    if first_number is None:
        return False, "番地なし"

    before_number = suffix[:first_number.start()]

    if (
        not before_number
        and not re.search(
            r"(?:丁目|番地|番|号)",
            suffix,
        )
    ):
        return False, "町名なし"

    return True, "住所形式に一致"


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

        rows = list(reader)

    ids = [
        row["field_id"].strip()
        for row in rows
    ]

    if not all(ids):
        raise ValueError(
            "施設IDが空の行があります"
        )

    if len(ids) != len(set(ids)):
        raise ValueError(
            "施設IDが重複しています"
        )

    return rows


def extract_candidates(
    html,
    prefecture,
    city,
    diagnostics=None,
):
    parser = VisibleTextParser()
    parser.feed(html)

    text = parser.get_text()

    lines = [
        re.sub(
            r"[ \t\u3000]+",
            "",
            line,
        )
        for line in text.splitlines()
    ]

    accepted = set()
    rejected = {}

    for line in lines:
        for match in ADDRESS_PATTERN.finditer(line):
            address = clean_address(
                match.group()
            )

            valid, reason = evaluate_address(
                address,
                prefecture,
                city,
            )

            if valid:
                accepted.add(address)
            elif address:
                rejected[address] = reason

    if diagnostics is not None:
        diagnostics["rejected"] = [
            {
                "address": address,
                "reason": reason,
            }
            for address, reason in sorted(
                rejected.items()
            )
            if address not in accepted
        ]

    return sorted(
        accepted,
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
        if temporary is not None:
            temporary.unlink(
                missing_ok=True
            )


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
                + str(
                    diagnostics.get(
                        "reason",
                        "不明",
                    )
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

        extraction = {}

        candidates = extract_candidates(
            html,
            prefecture,
            city,
            extraction,
        )

        rejected = extraction.get(
            "rejected",
            [],
        )

        print(
            f"  採用候補: {len(candidates)}件"
        )

        for address in candidates:
            print(
                f"    - {address}"
            )

        print(
            f"  除外候補: {len(rejected)}件"
        )

        for item in rejected[:20]:
            print(
                f"    - {item['address']}"
            )

            print(
                f"      理由: {item['reason']}"
            )

        if len(rejected) > 20:
            print(
                "    ...その他の除外候補は省略"
            )

        registered = row[
            "address"
        ].strip()

        matched = any(
            normalize(address)
            == normalize(registered)
            for address in candidates
        )

        print(
            "  既存住所との一致: "
            + (
                "YES"
                if matched
                else "NO"
            )
        )

        if not candidates:
            print(
                "  保存対象の住所候補なし"
            )
            continue

        found += 1

        # Preserve the previous review status only when
        # the candidate list and source URL are unchanged.
        previous = output.get(
            field_id,
            {},
        )

        same_candidates = (
            previous.get(
                "candidateAddresses"
            ) == candidates
            and previous.get(
                "sourceUrl"
            ) == url
        )

        review_status = (
            previous.get(
                "reviewStatus",
                "pending",
            )
            if same_candidates
            else "pending"
        )

        output[field_id] = {
            "fieldName": row[
                "field_name"
            ],
            "registeredAddress": registered,
            "candidateAddresses": candidates,
            "sourceUrl": url,
            "sourceType": "official_html",
            "reviewStatus": review_status,
            "collectedAt": (
                previous.get(
                    "collectedAt",
                    today,
                )
                if same_candidates
                else today
            ),
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
            "プレビューのみ。"
            "JSONは変更していません"
        )
        return 0

    if output == load_existing():
        print(
            "変更なし。"
            "JSONの書き換えを省略"
        )
        return 0

    write_atomic(output)

    print(
        f"保存完了: {OUTPUT}"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
"""FIELD//BASE address candidate review manager.

Review official HTML address candidates locally.

- Reads fieldResearch.csv and addressCandidates.json.
- Requires explicit approval or rejection.
- Keeps coordinate review_status unchanged.
- Backs up CSV before changing it.
- Never updates published JSON.
- Runs only on localhost.
"""

from __future__ import annotations

import csv
import html
import json
import os
import secrets
import shutil
import tempfile
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "src" / "data" / "generated"

CSV_PATH = GENERATED / "fieldResearch.csv"
CANDIDATES_PATH = GENERATED / "addressCandidates.json"

HOST = "127.0.0.1"
PORT = 8766

TOKEN = secrets.token_urlsafe(32)
LOCK = threading.Lock()

REVIEW_COLUMNS = (
    "address_review_status",
    "address_review_source",
    "address_review_note",
)

REQUIRED_COLUMNS = {
    "field_id",
    "field_name",
    "prefecture",
    "city",
    "address",
    "confirmed_official_url",
}


def escape(value):
    return html.escape(str(value or ""), quote=True)


def load_csv():
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

    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError(
            "施設IDが空、または重複しています"
        )

    return columns, rows


def load_candidates():
    if not CANDIDATES_PATH.exists():
        return {}

    data = json.loads(
        CANDIDATES_PATH.read_text(encoding="utf-8")
    )

    if not isinstance(data, dict):
        raise ValueError(
            "住所候補JSONの形式が不正です"
        )

    return data


def save_csv(columns, rows):
    for column in REVIEW_COLUMNS:
        if column not in columns:
            columns.append(column)

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup = CSV_PATH.with_name(
        f"fieldResearch.backup.{stamp}.csv"
    )

    shutil.copy2(CSV_PATH, backup)

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


def get_candidate(row, candidates):
    item = candidates.get(row["field_id"])

    if not isinstance(item, dict):
        return None

    if item.get("sourceType") != "official_html":
        return None

    source = item.get("sourceUrl", "")
    confirmed = row.get("confirmed_official_url", "")

    if not source or source != confirmed:
        return None

    addresses = item.get("candidateAddresses")

    if not isinstance(addresses, list):
        return None

    if not all(
        isinstance(address, str)
        for address in addresses
    ):
        return None

    return item


def page(message=""):
    _, rows = load_csv()
    candidates = load_candidates()

    cards = []
    pending = 0
    approved = 0
    rejected = 0

    for row in rows:
        item = get_candidate(row, candidates)

        if item is None:
            continue

        field_id = row["field_id"]
        name = row["field_name"]
        address = row.get("address", "")
        status = row.get(
            "address_review_status",
            "pending",
        ) or "pending"

        addresses = item["candidateAddresses"]

        if status == "approved":
            approved += 1
        elif status == "rejected":
            rejected += 1
        else:
            pending += 1

        options = []

        for candidate_address in addresses:
            selected = (
                " selected"
                if candidate_address == address
                else ""
            )

            options.append(
                '<option value="'
                + escape(candidate_address)
                + '"'
                + selected
                + ">"
                + escape(candidate_address)
                + "</option>"
            )

        if not options:
            continue

        source_url = item["sourceUrl"]

        source_link = (
            '<a href="'
            + escape(source_url)
            + '" target="_blank" '
            + 'rel="noopener noreferrer">'
            + "公式サイトを確認</a>"
        )

        note = row.get("address_review_note", "")

        card = f"""
        <article class="card">
          <div class="heading">
            <h2>{escape(name)}</h2>
            <span class="status">{escape(status)}</span>
          </div>

          <p class="muted">
            {escape(row.get("prefecture", ""))}
            {escape(row.get("city", ""))}
          </p>

          <label>現在の登録住所</label>
          <div class="current">{escape(address)}</div>

          <label>公式HTMLから抽出した住所候補</label>

          <form method="post" action="/review">
            <input type="hidden" name="token"
                   value="{escape(TOKEN)}">

            <input type="hidden" name="field_id"
                   value="{escape(field_id)}">

            <select name="address" required>
              {''.join(options)}
            </select>

            <p>{source_link}</p>

            <label>確認メモ</label>
            <textarea name="note" rows="2"
              maxlength="1000">{escape(note)}</textarea>

            <div class="actions">
              <button name="action" value="approve"
                      class="approve">
                住所を承認
              </button>

              <button name="action" value="reject"
                      class="reject">
                候補を却下
              </button>
            </div>
          </form>

          <p class="muted small">
            取得日: {escape(item.get("collectedAt", ""))}
          </p>
        </article>
        """

        cards.append(card)

    message_html = (
        f'<div class="message">{escape(message)}</div>'
        if message
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1">
<title>FIELD//BASE Address Reviewer</title>

<style>
:root {{
  color-scheme: light;
  font-family: -apple-system, BlinkMacSystemFont,
    "Helvetica Neue", sans-serif;
}}

* {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  background: #f5f6f7;
  color: #17191c;
}}

header {{
  background: #111214;
  color: white;
  padding: 28px 24px;
}}

header h1 {{
  margin: 0 0 8px;
  font-size: 25px;
}}

header p {{
  margin: 0;
  color: #c4c8ce;
}}

main {{
  max-width: 1050px;
  margin: 0 auto;
  padding: 24px;
}}

.summary {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}}

.stat {{
  padding: 20px;
  border: 1px solid #e0e2e5;
  background: white;
  border-radius: 12px;
}}

.stat strong {{
  display: block;
  margin-top: 6px;
  font-size: 28px;
}}

.cards {{
  display: grid;
  grid-template-columns: repeat(
    auto-fit, minmax(300px, 1fr)
  );
  gap: 18px;
}}

.card {{
  padding: 22px;
  background: white;
  border: 1px solid #e0e2e5;
  border-radius: 14px;
}}

.heading {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}}

h2 {{
  margin: 0;
  font-size: 21px;
}}

.status {{
  padding: 5px 10px;
  border-radius: 20px;
  background: #edf0f3;
  font-size: 12px;
}}

.muted {{
  color: #66707c;
}}

.small {{
  font-size: 12px;
}}

label {{
  display: block;
  margin: 18px 0 8px;
  font-size: 13px;
  font-weight: 700;
}}

.current {{
  padding: 12px;
  border-radius: 8px;
  background: #f2f3f5;
  overflow-wrap: anywhere;
}}

select, textarea {{
  width: 100%;
  padding: 12px;
  border: 1px solid #cbd0d6;
  border-radius: 8px;
  background: white;
  font: inherit;
}}

a {{
  color: #1858b8;
}}

.actions {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}}

button {{
  padding: 12px 16px;
  border: 0;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
}}

.approve {{
  background: #111214;
  color: white;
}}

.reject {{
  background: #e9ebee;
  color: #25292e;
}}

.message {{
  margin-bottom: 20px;
  padding: 14px;
  border: 1px solid #ccd2d8;
  background: white;
  border-radius: 8px;
}}

@media (max-width: 600px) {{
  .summary {{
    grid-template-columns: 1fr;
  }}
}}
</style>
</head>

<body>
<header>
  <h1>FIELD//BASE / Address Reviewer</h1>
  <p>公式サイトから取得した住所候補を目視確認</p>
</header>

<main>
  {message_html}

  <section class="summary">
    <div class="stat">
      未確認
      <strong>{pending}</strong>
    </div>
    <div class="stat">
      承認済み
      <strong>{approved}</strong>
    </div>
    <div class="stat">
      却下済み
      <strong>{rejected}</strong>
    </div>
  </section>

  <section class="cards">
    {''.join(cards) if cards else
      '<p>確認できる住所候補はありません。</p>'}
  </section>
</main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):

    def send_html(self, content, status=200):
        body = content.encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8",
        )
        self.send_header(
            "Content-Length",
            str(len(body)),
        )
        self.send_header(
            "Cache-Control",
            "no-store",
        )
        self.send_header(
            "X-Content-Type-Options",
            "nosniff",
        )
        self.send_header(
            "Content-Security-Policy",
            "default-src 'none'; "
            "style-src 'unsafe-inline'; "
            "form-action 'self'; "
            "base-uri 'none'",
        )
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path != "/":
            self.send_error(404)
            return

        try:
            self.send_html(page())
        except Exception as error:
            self.send_html(
                "<h1>読み込みエラー</h1><pre>"
                + escape(error)
                + "</pre>",
                500,
            )

    def do_POST(self):
        if self.path != "/review":
            self.send_error(404)
            return

        origin = self.headers.get("Origin", "")

        if origin not in (
            "",
            f"http://{HOST}:{PORT}",
        ):
            self.send_error(403)
            return

        try:
            length = int(
                self.headers.get("Content-Length", "0")
            )
        except ValueError:
            self.send_error(400)
            return

        if length <= 0 or length > 16384:
            self.send_error(400)
            return

        try:
            raw = self.rfile.read(length)
            form = parse_qs(
                raw.decode("utf-8"),
                keep_blank_values=True,
            )

            def field(key):
                values = form.get(key, [])
                if len(values) != 1:
                    raise ValueError(
                        f"入力項目が不正です: {key}"
                    )
                return values[0]

            token = field("token")
            field_id = field("field_id")
            address = field("address")
            action = field("action")
            note = field("note").strip()

            if not secrets.compare_digest(
                token, TOKEN
            ):
                raise ValueError(
                    "確認トークンが一致しません"
                )

            if action not in ("approve", "reject"):
                raise ValueError(
                    "操作が不正です"
                )

            if len(note) > 1000:
                raise ValueError(
                    "メモが長すぎます"
                )

            with LOCK:
                columns, rows = load_csv()
                candidates = load_candidates()

                target = next(
                    (
                        row for row in rows
                        if row["field_id"] == field_id
                    ),
                    None,
                )

                if target is None:
                    raise ValueError(
                        "施設が見つかりません"
                    )

                item = get_candidate(
                    target,
                    candidates,
                )

                if item is None:
                    raise ValueError(
                        "公式サイトの確認状態が変わりました"
                    )

                if address not in item["candidateAddresses"]:
                    raise ValueError(
                        "候補に存在しない住所です"
                    )

                if action == "approve":
                    target["address"] = address
                    target[
                        "address_review_status"
                    ] = "approved"
                else:
                    target[
                        "address_review_status"
                    ] = "rejected"

                target[
                    "address_review_source"
                ] = item["sourceUrl"]

                target[
                    "address_review_note"
                ] = note

                save_csv(columns, rows)

            self.send_html(
                page("確認結果をCSVに保存しました")
            )

        except (ValueError, UnicodeError) as error:
            self.send_html(
                page(str(error)),
                400,
            )
        except Exception as error:
            self.send_html(
                "<h1>保存エラー</h1><pre>"
                + escape(error)
                + "</pre>",
                500,
            )


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(CSV_PATH)

    if not CANDIDATES_PATH.exists():
        raise FileNotFoundError(
            CANDIDATES_PATH
        )

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler,
    )

    print("=" * 48)
    print("FIELD//BASE Address Reviewer")
    print("=" * 48)
    print(f"URL: http://{HOST}:{PORT}")
    print(f"CSV: {CSV_PATH}")
    print(f"Candidates: {CANDIDATES_PATH}")
    print()
    print("終了するには Ctrl+C")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを終了します")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

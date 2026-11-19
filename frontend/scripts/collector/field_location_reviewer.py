
#!/usr/bin/env python3
"""FIELD//BASE Unified Research Manager.

Local tool for reviewing:
- Official website URLs
- Addresses extracted from official websites
- Facility coordinates

The tool updates fieldResearch.csv only.
It does not publish changes to the application.
"""

from __future__ import annotations

import csv
import ipaddress
import json
import math
import os
import secrets
import shutil
import tempfile
import threading
import webbrowser

from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "src" / "data" / "generated"

CSV_PATH = GENERATED / "fieldResearch.csv"
CANDIDATES_PATH = GENERATED / "addressCandidates.json"

HOST = "127.0.0.1"
PORT = 8765

LOCK = threading.Lock()
TOKEN = secrets.token_urlsafe(32)

REQUIRED_COLUMNS = {
    "field_id",
    "field_name",
    "prefecture",
    "city",
    "address",
    "website",
    "confirmed_official_url",
    "latitude",
    "longitude",
    "review_status",
    "notes",
}

ADDRESS_COLUMNS = (
    "address_review_status",
    "address_review_source",
    "address_review_note",
)


def load_data():
    if not CSV_PATH.exists():
        raise FileNotFoundError(CSV_PATH)

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
            "CSVの必須列がありません: "
            + ", ".join(sorted(missing))
        )

    ids = [row["field_id"].strip() for row in rows]

    if not all(ids):
        raise ValueError("施設IDが空の行があります")

    if len(ids) != len(set(ids)):
        raise ValueError("施設IDが重複しています")

    return columns, rows


def load_candidates():
    if not CANDIDATES_PATH.exists():
        return {}

    with CANDIDATES_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "住所候補JSONの形式が不正です"
        )

    return data


def valid_official_url(value):
    if not isinstance(value, str):
        return False

    if (
        not value
        or value != value.strip()
        or len(value) > 2048
        or any(ord(char) < 33 for char in value)
    ):
        return False

    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if not hostname or port is not None:
        return False

    if parsed.username or parsed.password:
        return False

    hostname = hostname.lower()

    if (
        hostname == "localhost"
        or hostname.endswith(
            (
                ".localhost",
                ".local",
                ".internal",
                ".test",
                ".invalid",
            )
        )
    ):
        return False

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        if "." not in hostname:
            return False
    else:
        if not ip.is_global:
            return False

    return True


def valid_coordinate(latitude, longitude):
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False

    return (
        math.isfinite(lat)
        and math.isfinite(lon)
        and 20 <= lat <= 46
        and 122 <= lon <= 154
    )


def valid_address_candidate(row, candidate):
    if not isinstance(candidate, dict):
        return False

    if candidate.get("sourceType") != "official_html":
        return False

    source_url = candidate.get("sourceUrl", "")

    confirmed_url = row.get(
        "confirmed_official_url", ""
    ).strip()

    if not source_url or source_url != confirmed_url:
        return False

    if not valid_official_url(source_url):
        return False

    addresses = candidate.get("candidateAddresses")

    if not isinstance(addresses, list):
        return False

    return all(
        isinstance(address, str)
        for address in addresses
    )


def backup_file():
    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup = CSV_PATH.with_name(
        f"fieldResearch.backup.{stamp}.csv"
    )

    shutil.copy2(CSV_PATH, backup)

    return backup


def save_data(columns, rows):
    columns = list(columns)

    for column in ADDRESS_COLUMNS:
        if column not in columns:
            columns.append(column)

    backup_file()

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
                lineterminator="\n",
            )

            writer.writeheader()
            writer.writerows(rows)

            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary, CSV_PATH)

    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def serialize_rows(rows, candidates):
    result = []

    for row in rows:
        field_id = row["field_id"]
        candidate = candidates.get(field_id)

        if not valid_address_candidate(
            row,
            candidate,
        ):
            candidate = None

        result.append({
            "id": field_id,
            "name": row.get("field_name", ""),
            "prefecture": row.get("prefecture", ""),
            "city": row.get("city", ""),
            "address": row.get("address", ""),
            "website": row.get("website", ""),
            "confirmed_url": row.get(
                "confirmed_official_url", ""
            ),
            "latitude": row.get("latitude", ""),
            "longitude": row.get("longitude", ""),
            "candidate_latitude": row.get(
                "candidate_latitude", ""
            ),
            "candidate_longitude": row.get(
                "candidate_longitude", ""
            ),
            "location_status": row.get(
                "review_status", "pending"
            ),
            "notes": row.get("notes", ""),
            "address_status": row.get(
                "address_review_status", ""
            ) or "pending",
            "address_source": row.get(
                "address_review_source", ""
            ),
            "address_note": row.get(
                "address_review_note", ""
            ),
            "address_candidates": (
                candidate.get("candidateAddresses", [])
                if candidate else []
            ),
            "candidate_source": (
                candidate.get("sourceUrl", "")
                if candidate else ""
            ),
            "candidate_date": (
                candidate.get("collectedAt", "")
                if candidate else ""
            ),
        })

    return result


def render_page():
    _, rows = load_data()
    candidates = load_candidates()

    payload = json.dumps(
        serialize_rows(rows, candidates),
        ensure_ascii=False,
    )

    payload = (
        payload
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )

    token = json.dumps(TOKEN)

    template = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width,initial-scale=1">

<title>FIELD//BASE Research Manager</title>

<style>
:root {
  color-scheme: dark;
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    "Helvetica Neue",
    sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: #101214;
  color: #f2f3f4;
}

header {
  padding: 25px 32px;
  border-bottom: 1px solid #303438;
}

h1 {
  margin: 0 0 8px;
  font-size: 25px;
  letter-spacing: .04em;
}

.sub,
.notice {
  color: #aab2b9;
  font-size: 13px;
  line-height: 1.7;
}

main {
  max-width: 1400px;
  margin: auto;
  padding: 24px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat,
.panel {
  background: #1b1f22;
  border: 1px solid #343a3f;
  border-radius: 12px;
}

.stat {
  padding: 18px;
}

.stat strong {
  display: block;
  font-size: 28px;
}

.stat span {
  color: #aab2b9;
  font-size: 12px;
}

.controls {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}

input,
select,
textarea {
  background: #191d20;
  border: 1px solid #41484e;
  border-radius: 8px;
  color: white;
  padding: 11px;
  font: inherit;
}

input:focus,
select:focus,
textarea:focus {
  outline: 2px solid #8cbdad;
}

#search {
  flex: 1;
  min-width: 180px;
}

.layout {
  display: grid;
  grid-template-columns:
    minmax(290px, 390px)
    minmax(0, 1fr);
  gap: 18px;
}

.panel {
  overflow: hidden;
}

.list {
  max-height: 76vh;
  overflow-y: auto;
}

.field {
  display: block;
  width: 100%;
  padding: 15px;
  border: 0;
  border-bottom: 1px solid #343a3f;
  text-align: left;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.field:hover,
.field.active {
  background: #2b3438;
}

.field-name {
  display: block;
  font-weight: 700;
  margin-bottom: 6px;
}

.field-meta {
  display: block;
  color: #aab2b9;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-line;
}

.detail {
  padding: 24px;
}

.detail h2 {
  margin: 5px 0 8px;
}

.section {
  padding: 20px 0;
  border-top: 1px solid #343a3f;
}

.section h3 {
  margin: 0 0 12px;
}

.label {
  display: block;
  color: #b6bec4;
  font-size: 12px;
  margin: 12px 0 6px;
}

.full {
  width: 100%;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-grid input {
  width: 100%;
}

textarea {
  width: 100%;
  min-height: 85px;
  resize: vertical;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 15px 0;
}

a,
button {
  display: inline-block;
  background: #30383d;
  color: #f4f5f6;
  border: 0;
  border-radius: 8px;
  padding: 11px 14px;
  font-size: 13px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
}

button.primary,
a.primary {
  background: #dce8e4;
  color: #14201d;
}

button.danger {
  background: #54383a;
  color: #ffd7d7;
}

button:disabled {
  opacity: .4;
  cursor: not-allowed;
}

.current-address {
  background: #252a2e;
  border-radius: 8px;
  padding: 14px;
  overflow-wrap: anywhere;
}

.success {
  color: #a8d6c6;
}

.error {
  color: #ff9c9c;
}

.warning {
  color: #ffca85;
}

.message {
  min-height: 22px;
  font-size: 12px;
  line-height: 1.7;
}

.empty {
  padding: 20px;
  color: #aab2b9;
}

@media(max-width:850px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }

  main {
    padding: 14px;
  }

  header {
    padding: 20px;
  }

  .detail {
    padding: 18px;
  }
}
</style>
</head>

<body>
<header>
  <h1>FIELD//BASE / RESEARCH MANAGER</h1>
  <div class="sub">
    公式URL・住所・座標の確認とCSV管理
  </div>
</header>

<main>
  <div class="stats">
    <div class="stat">
      <strong id="total">0</strong>
      <span>CSV調査対象</span>
    </div>

    <div class="stat">
      <strong id="officialCount">0</strong>
      <span>公式URL確認済み</span>
    </div>

    <div class="stat">
      <strong id="addressCount">0</strong>
      <span>住所承認済み</span>
    </div>

    <div class="stat">
      <strong id="locationCount">0</strong>
      <span>座標確認済み</span>
    </div>

    <div class="stat">
      <strong id="candidateCount">0</strong>
      <span>未承認の住所候補</span>
    </div>
  </div>

  <div class="controls">
    <input
      id="search"
      placeholder="施設名・住所・IDで検索"
    >

    <select id="filter">
      <option value="all">すべて</option>
      <option value="officialPending">
        公式URL未確認
      </option>
      <option value="officialVerified">
        公式URL確認済み
      </option>
      <option value="addressPending">
        住所未承認
      </option>
      <option value="addressApproved">
        住所承認済み
      </option>
      <option value="addressCandidate">
        住所候補あり
      </option>
      <option value="locationPending">
        座標未確認
      </option>
      <option value="locationVerified">
        座標確認済み
      </option>
    </select>
  </div>

  <div class="layout">
    <section
      class="panel list"
      id="list"
    ></section>

    <section class="panel detail">
      <div
        class="sub"
        id="position"
      ></div>

      <h2 id="name">
        施設を選択してください
      </h2>

      <div
        class="sub"
        id="address"
      ></div>

      <div class="actions">
        <button id="previous">
          前の施設
        </button>

        <button id="next">
          次の施設
        </button>
      </div>

      <div class="section">
        <h3>1. 公式サイトの確認</h3>

        <div
          class="notice"
          id="websiteInfo"
        ></div>

        <div class="actions">
          <a
            id="searchOfficial"
            class="primary"
            target="_blank"
            rel="noopener noreferrer"
          >
            公式サイトを検索
          </a>

          <a
            id="openRegistered"
            target="_blank"
            rel="noopener noreferrer"
          >
            既存URLを開く
          </a>
        </div>

        <label
          class="label"
          for="officialUrl"
        >
          確認済み公式サイトURL
        </label>

        <input
          id="officialUrl"
          class="full"
          type="url"
          placeholder="https://example.jp/"
        >

        <div
          id="httpWarning"
          class="notice warning"
        ></div>

        <div class="actions">
          <button
            class="primary"
            id="saveOfficial"
          >
            公式URLを保存
          </button>
        </div>

        <div
          id="officialMessage"
          class="message"
          role="status"
        ></div>
      </div>

      <div class="section">
        <h3>2. 住所候補の確認</h3>

        <label class="label">
          現在の登録住所
        </label>

        <div
          class="current-address"
          id="registeredAddress"
        ></div>

        <div
          class="notice"
          id="addressStatus"
        ></div>

        <label
          class="label"
          for="addressCandidate"
        >
          公式サイトから抽出した住所候補
        </label>

        <select
          id="addressCandidate"
          class="full"
        ></select>

        <div class="actions">
          <a
            id="addressSource"
            class="primary"
            target="_blank"
            rel="noopener noreferrer"
          >
            住所の取得元を確認
          </a>
        </div>

        <div
          class="notice"
          id="addressCandidateInfo"
        ></div>

        <label
          class="label"
          for="addressNote"
        >
          住所確認メモ
        </label>

        <textarea
          id="addressNote"
          placeholder="住所を確認した根拠"
        ></textarea>

        <div class="actions">
          <button
            id="approveAddress"
            class="primary"
          >
            住所を承認
          </button>

          <button
            id="rejectAddress"
            class="danger"
          >
            候補を却下
          </button>
        </div>

        <div
          id="addressMessage"
          class="message"
          role="status"
        ></div>

        <p class="notice">
          候補は未検証です。
          公式サイトの住所表記を目視確認してください。
          住所の承認は座標の確認状態を変更しません。
        </p>
      </div>

      <div class="section">
        <h3>3. 座標の確認</h3>

        <div class="actions">
          <a
            id="google"
            class="primary"
            target="_blank"
            rel="noopener noreferrer"
          >
            Googleマップ
          </a>
        </div>

        <div
          class="notice"
          id="candidate"
        ></div>

        <div class="form-grid">
          <div>
            <label
              class="label"
              for="latitude"
            >
              緯度
            </label>

            <input
              id="latitude"
              inputmode="decimal"
            >
          </div>

          <div>
            <label
              class="label"
              for="longitude"
            >
              経度
            </label>

            <input
              id="longitude"
              inputmode="decimal"
            >
          </div>
        </div>

        <label
          class="label"
          for="notes"
        >
          確認メモ
        </label>

        <textarea
          id="notes"
          placeholder="公式サイト・住所・位置の確認根拠"
        ></textarea>

        <div class="actions">
          <button
            class="primary"
            id="saveLocation"
          >
            座標を確認済みとして保存
          </button>
        </div>

        <div
          id="locationMessage"
          class="message"
          role="status"
        ></div>
      </div>
    </section>
  </div>
</main>

<script>
const fields = __FIELD_DATA__;
const token = __CSRF_TOKEN__;

let selectedId = null;
let saving = false;

const el = id =>
  document.getElementById(id);

function selected() {
  return fields.find(
    field => field.id === selectedId
  ) || null;
}

function officialVerified(field) {
  return Boolean(field.confirmed_url);
}

function addressApproved(field) {
  return field.address_status === "approved";
}

function locationVerified(field) {
  return field.location_status === "verified";
}

function hasAddressCandidate(field) {
  return field.address_candidates.length > 0;
}

function hasCoordinateCandidate(field) {
  return Boolean(
    field.candidate_latitude &&
    field.candidate_longitude
  );
}

function visibleFields() {
  const query = el("search")
    .value
    .trim()
    .toLowerCase();

  const filter = el("filter").value;

  return fields.filter(field => {
    const text = [
      field.id,
      field.name,
      field.prefecture,
      field.city,
      field.address
    ]
      .join(" ")
      .toLowerCase();

    if (!text.includes(query)) {
      return false;
    }

    if (filter === "officialPending") {
      return !officialVerified(field);
    }

    if (filter === "officialVerified") {
      return officialVerified(field);
    }

    if (filter === "addressPending") {
      return !addressApproved(field);
    }

    if (filter === "addressApproved") {
      return addressApproved(field);
    }

    if (filter === "addressCandidate") {
      return hasAddressCandidate(field);
    }

    if (filter === "locationPending") {
      return !locationVerified(field);
    }

    if (filter === "locationVerified") {
      return locationVerified(field);
    }

    return true;
  });
}

function updateStats() {
  el("total").textContent =
    fields.length;

  el("officialCount").textContent =
    fields.filter(officialVerified).length;

  el("addressCount").textContent =
    fields.filter(addressApproved).length;

  el("locationCount").textContent =
    fields.filter(locationVerified).length;

  el("candidateCount").textContent =
    fields.filter(
      field =>
        hasAddressCandidate(field) &&
        !addressApproved(field)
    ).length;
}

function renderList() {
  const list = el("list");

  list.replaceChildren();

  const visible = visibleFields();

  if (!visible.length) {
    const empty =
      document.createElement("div");

    empty.className = "empty";
    empty.textContent =
      "条件に一致する施設がありません。";

    list.appendChild(empty);
    return;
  }

  for (const field of visible) {
    const button =
      document.createElement("button");

    button.className =
      "field" +
      (
        field.id === selectedId
          ? " active"
          : ""
      );

    const name =
      document.createElement("span");

    name.className = "field-name";
    name.textContent = field.name;

    const meta =
      document.createElement("span");

    meta.className = "field-meta";

    meta.textContent =
      (
        officialVerified(field)
          ? "公式 ✓"
          : "公式 未確認"
      ) +
      " / " +
      (
        addressApproved(field)
          ? "住所 ✓"
          : "住所 未承認"
      ) +
      " / " +
      (
        locationVerified(field)
          ? "座標 ✓"
          : "座標 未確認"
      ) +
      "\n" +
      field.address;

    button.append(name, meta);

    button.onclick = () =>
      selectField(field.id);

    list.appendChild(button);
  }
}

function message(
  id,
  text,
  error = false
) {
  const node = el(id);

  node.textContent = text;

  node.className =
    "message " +
    (error ? "error" : "success");
}

function safeWebsiteUrl(value) {
  try {
    const url = new URL(value);

    if (
      !["http:", "https:"].includes(
        url.protocol
      )
    ) {
      return "";
    }

    if (url.username || url.password) {
      return "";
    }

    return url.href;

  } catch (_) {
    return "";
  }
}

function setLink(id, url) {
  const node = el(id);

  if (url) {
    node.href = url;
    node.style.display = "inline-block";
  } else {
    node.removeAttribute("href");
    node.style.display = "none";
  }
}

function updateHttpWarning() {
  const value =
    el("officialUrl").value.trim();

  el("httpWarning").textContent =
    value.toLowerCase().startsWith("http://")
      ? "注意: HTTP通信は暗号化されません。"
      : "";
}

function clearDetail() {
  selectedId = null;

  el("position").textContent = "";
  el("name").textContent =
    "対象施設がありません";
  el("address").textContent = "";
  el("websiteInfo").textContent = "";
  el("registeredAddress").textContent = "";
  el("addressStatus").textContent = "";
  el("addressCandidateInfo").textContent = "";
  el("candidate").textContent = "";

  for (const id of [
    "officialUrl",
    "latitude",
    "longitude",
    "notes",
    "addressNote"
  ]) {
    el(id).value = "";
  }

  el("addressCandidate").replaceChildren();

  for (const id of [
    "searchOfficial",
    "openRegistered",
    "addressSource",
    "google"
  ]) {
    setLink(id, "");
  }

  for (const id of [
    "previous",
    "next",
    "saveOfficial",
    "approveAddress",
    "rejectAddress",
    "saveLocation"
  ]) {
    el(id).disabled = true;
  }

  message("officialMessage", "");
  message("addressMessage", "");
  message("locationMessage", "");

  renderList();
}

function selectField(id) {
  const visible = visibleFields();

  const index = visible.findIndex(
    field => field.id === id
  );

  if (index < 0) {
    if (visible.length) {
      selectField(visible[0].id);
    } else {
      clearDetail();
    }
    return;
  }

  selectedId = id;

  const field = visible[index];

  el("position").textContent =
    (index + 1) +
    " / " +
    visible.length +
    "施設";

  el("name").textContent = field.name;

  el("address").textContent =
    field.prefecture +
    " " +
    field.city +
    " / " +
    field.address;

  el("websiteInfo").textContent =
    field.website
      ? "既存URL: " + field.website
      : "既存URLは未登録です。";

  el("officialUrl").value =
    field.confirmed_url ||
    field.website ||
    "";

  updateHttpWarning();

  const searchQuery =
    encodeURIComponent(
      field.name +
      " " +
      field.prefecture +
      " サバゲー 公式サイト"
    );

  setLink(
    "searchOfficial",
    "https://www.google.com/search?q=" +
    searchQuery
  );

  setLink(
    "openRegistered",
    safeWebsiteUrl(field.website)
  );

  el("registeredAddress").textContent =
    field.address || "未登録";

  el("addressStatus").textContent =
    "住所確認状態: " +
    (
      field.address_status === "approved"
        ? "承認済み"
        : field.address_status === "rejected"
          ? "却下済み"
          : "未確認"
    );

  const selector = el("addressCandidate");

  selector.replaceChildren();

  for (const address of field.address_candidates) {
    const option =
      document.createElement("option");

    option.value = address;
    option.textContent = address;

    if (address === field.address) {
      option.selected = true;
    }

    selector.appendChild(option);
  }

  el("addressNote").value =
    field.address_note || "";

  el("addressCandidateInfo").textContent =
    field.address_candidates.length
      ? (
          "候補: " +
          field.address_candidates.length +
          "件 / 取得日: " +
          field.candidate_date
        )
      : "現在の公式URLに対応する住所候補はありません。";

  setLink(
    "addressSource",
    safeWebsiteUrl(field.candidate_source)
  );

  const mapQuery =
    encodeURIComponent(
      field.name +
      " " +
      field.address
    );

  setLink(
    "google",
    "https://www.google.com/maps/search/?api=1&query=" +
    mapQuery
  );

  el("latitude").value =
    field.latitude ||
    field.candidate_latitude ||
    "";

  el("longitude").value =
    field.longitude ||
    field.candidate_longitude ||
    "";

  el("notes").value =
    field.notes || "";

  el("candidate").textContent =
    hasCoordinateCandidate(field)
      ? (
          "座標候補: " +
          field.candidate_latitude +
          ", " +
          field.candidate_longitude +
          "（未検証）"
        )
      : "座標候補なし";

  el("previous").disabled =
    index === 0;

  el("next").disabled =
    index === visible.length - 1;

  el("saveOfficial").disabled = saving;
  el("saveLocation").disabled = saving;

  const addressDisabled =
    saving || !hasAddressCandidate(field);

  el("approveAddress").disabled =
    addressDisabled;

  el("rejectAddress").disabled =
    addressDisabled;

  message("officialMessage", "");
  message("addressMessage", "");
  message("locationMessage", "");

  renderList();
}

function move(direction) {
  const visible = visibleFields();

  const index = visible.findIndex(
    field => field.id === selectedId
  );

  const next = index + direction;

  if (next >= 0 && next < visible.length) {
    selectField(visible[next].id);
  }
}

function refreshSelection() {
  const visible = visibleFields();

  if (!visible.length) {
    clearDetail();
    return;
  }

  if (
    !visible.some(
      field => field.id === selectedId
    )
  ) {
    selectField(visible[0].id);
  } else {
    selectField(selectedId);
  }
}

function disableSaving(value) {
  saving = value;

  const field = selected();

  el("saveOfficial").disabled =
    value || !field;

  el("saveLocation").disabled =
    value || !field;

  const addressDisabled =
    value ||
    !field ||
    !hasAddressCandidate(field);

  el("approveAddress").disabled =
    addressDisabled;

  el("rejectAddress").disabled =
    addressDisabled;
}

async function postData(path, payload) {
  const response = await fetch(
    path,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Review-Token": token
      },
      body: JSON.stringify(payload)
    }
  );

  const result = await response.json();

  if (!response.ok) {
    throw new Error(
      result.error ||
      "保存に失敗しました"
    );
  }

  return result;
}

function afterSave(field, messageId) {
  updateStats();
  refreshSelection();

  message(
    messageId,
    field.name + " の確認結果を保存しました。"
  );
}

async function saveOfficial() {
  if (saving) return;

  const field = selected();
  if (!field) return;

  const url =
    el("officialUrl").value.trim();

  if (!safeWebsiteUrl(url)) {
    message(
      "officialMessage",
      "有効なHTTPまたはHTTPSのURLを入力してください。",
      true
    );
    return;
  }

  if (
    !window.confirm(
      field.name +
      "\n" +
      url +
      "\n\n公式サイトを目視確認しましたか？"
    )
  ) {
    return;
  }

  disableSaving(true);

  try {
    await postData(
      "/api/official",
      {
        field_id: field.id,
        url
      }
    );

    const changed =
      field.confirmed_url !== url;

    field.confirmed_url = url;

    if (changed) {
      field.address_candidates = [];
      field.candidate_source = "";
      field.candidate_date = "";
      field.address_status = "pending";
      field.address_source = "";
      field.address_note = "";
    }

    afterSave(field, "officialMessage");

  } catch (error) {
    message(
      "officialMessage",
      error.message,
      true
    );

  } finally {
    disableSaving(false);
  }
}

async function reviewAddress(action) {
  if (saving) return;

  const field = selected();

  if (
    !field ||
    !hasAddressCandidate(field)
  ) {
    return;
  }

  const address =
    el("addressCandidate").value;

  const note =
    el("addressNote").value.trim();

  if (
    !field.address_candidates.includes(address)
  ) {
    message(
      "addressMessage",
      "住所候補を選択してください。",
      true
    );
    return;
  }

  const label =
    action === "approve"
      ? "承認"
      : "却下";

  if (
    !window.confirm(
      field.name +
      "\n" +
      address +
      "\n\nこの住所候補を" +
      label +
      "しますか？"
    )
  ) {
    return;
  }

  disableSaving(true);

  try {
    await postData(
      "/api/address",
      {
        field_id: field.id,
        action,
        address,
        note
      }
    );

    field.address_status =
      action === "approve"
        ? "approved"
        : "rejected";

    field.address_source =
      field.candidate_source;

    field.address_note = note;

    if (action === "approve") {
      field.address = address;
    }

    afterSave(field, "addressMessage");

  } catch (error) {
    message(
      "addressMessage",
      error.message,
      true
    );

  } finally {
    disableSaving(false);
  }
}

async function saveLocation() {
  if (saving) return;

  const field = selected();
  if (!field) return;

  const latitude =
    el("latitude").value.trim();

  const longitude =
    el("longitude").value.trim();

  const notes =
    el("notes").value.trim();

  const lat = Number(latitude);
  const lon = Number(longitude);

  if (
    !latitude ||
    !longitude ||
    !Number.isFinite(lat) ||
    !Number.isFinite(lon) ||
    lat < 20 ||
    lat > 46 ||
    lon < 122 ||
    lon > 154
  ) {
    message(
      "locationMessage",
      "日本国内の有効な緯度・経度を入力してください。",
      true
    );
    return;
  }

  if (!notes) {
    message(
      "locationMessage",
      "確認メモが必要です。",
      true
    );
    return;
  }

  if (
    !window.confirm(
      field.name +
      "\n緯度: " +
      latitude +
      "\n経度: " +
      longitude +
      "\n\n座標を確認済みとして保存しますか？"
    )
  ) {
    return;
  }

  disableSaving(true);

  try {
    await postData(
      "/api/location",
      {
        field_id: field.id,
        latitude,
        longitude,
        notes
      }
    );

    field.latitude = latitude;
    field.longitude = longitude;
    field.notes = notes;
    field.location_status = "verified";

    afterSave(field, "locationMessage");

  } catch (error) {
    message(
      "locationMessage",
      error.message,
      true
    );

  } finally {
    disableSaving(false);
  }
}

el("search").addEventListener(
  "input",
  refreshSelection
);

el("filter").addEventListener(
  "change",
  refreshSelection
);

el("previous").addEventListener(
  "click",
  () => move(-1)
);

el("next").addEventListener(
  "click",
  () => move(1)
);

el("saveOfficial").addEventListener(
  "click",
  saveOfficial
);

el("approveAddress").addEventListener(
  "click",
  () => reviewAddress("approve")
);

el("rejectAddress").addEventListener(
  "click",
  () => reviewAddress("reject")
);

el("saveLocation").addEventListener(
  "click",
  saveLocation
);

el("officialUrl").addEventListener(
  "input",
  updateHttpWarning
);

updateStats();
refreshSelection();
</script>
</body>
</html>"""

    return (
        template
        .replace(
            "__FIELD_DATA__",
            payload,
        )
        .replace(
            "__CSRF_TOKEN__",
            token,
        )
    )


class Handler(BaseHTTPRequestHandler):

    def send_content(
        self,
        status,
        body,
        content_type,
    ):
        self.send_response(status)

        self.send_header(
            "Content-Type",
            content_type,
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
            "default-src 'self'; "
            "script-src 'unsafe-inline'; "
            "style-src 'unsafe-inline'; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'none'; "
            "form-action 'self'",
        )

        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, data):
        body = json.dumps(
            data,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_content(
            status,
            body,
            "application/json; charset=utf-8",
        )

    def do_GET(self):
        if urlparse(self.path).path != "/":
            self.send_error(404)
            return

        try:
            with LOCK:
                page = render_page()

            self.send_content(
                200,
                page.encode("utf-8"),
                "text/html; charset=utf-8",
            )

        except (OSError, ValueError) as error:
            self.send_error(500, str(error))

    def do_POST(self):
        path = urlparse(self.path).path

        if path not in {
            "/api/official",
            "/api/address",
            "/api/location",
        }:
            self.send_error(404)
            return

        origin = self.headers.get("Origin")
        expected_origin = f"http://{HOST}:{PORT}"

        if origin and origin != expected_origin:
            self.send_error(403)
            return

        supplied_token = self.headers.get(
            "X-Review-Token", ""
        )

        if not secrets.compare_digest(
            supplied_token,
            TOKEN,
        ):
            self.send_error(403)
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length", "0"
                )
            )

            if length <= 0 or length > 16384:
                raise ValueError(
                    "不正なリクエストサイズ"
                )

            data = json.loads(
                self.rfile.read(length)
            )

            if not isinstance(data, dict):
                raise ValueError(
                    "リクエスト形式が不正です"
                )

            field_id = str(
                data.get("field_id", "")
            ).strip()

            with LOCK:
                columns, rows = load_data()

                match = next(
                    (
                        row for row in rows
                        if row["field_id"] == field_id
                    ),
                    None,
                )

                if match is None:
                    raise ValueError(
                        "施設IDが見つかりません"
                    )

                if path == "/api/official":
                    self.update_official(
                        match,
                        data,
                    )

                elif path == "/api/address":
                    candidates = load_candidates()

                    self.update_address(
                        match,
                        data,
                        candidates,
                    )

                else:
                    self.update_location(
                        match,
                        data,
                    )

                save_data(columns, rows)

            self.send_json(
                200,
                {
                    "ok": True,
                    "field_id": field_id,
                },
            )

        except (
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as error:
            self.send_json(
                400,
                {"error": str(error)},
            )

        except OSError as error:
            self.send_json(
                500,
                {"error": str(error)},
            )

    @staticmethod
    def update_official(row, data):
        url = str(
            data.get("url", "")
        ).strip()

        if not valid_official_url(url):
            raise ValueError(
                "有効なHTTPまたはHTTPSの公式URLを入力してください"
            )

        old_url = row.get(
            "confirmed_official_url", ""
        ).strip()

        row["confirmed_official_url"] = url

        if old_url != url:
            row["address_review_status"] = "pending"
            row["address_review_source"] = ""
            row["address_review_note"] = ""

    @staticmethod
    def update_address(row, data, candidates):
        field_id = row["field_id"]
        candidate = candidates.get(field_id)

        if not valid_address_candidate(
            row,
            candidate,
        ):
            raise ValueError(
                "現在の公式URLに対応する住所候補がありません"
            )

        address = data.get("address")
        action = data.get("action")
        note = data.get("note", "")

        if not isinstance(address, str):
            raise ValueError("住所形式が不正です")

        if not isinstance(note, str):
            raise ValueError("メモ形式が不正です")

        note = note.strip()

        if len(note) > 1000:
            raise ValueError(
                "確認メモは1000文字以内にしてください"
            )

        if address not in candidate["candidateAddresses"]:
            raise ValueError(
                "選択した住所が候補にありません"
            )

        if action not in ("approve", "reject"):
            raise ValueError(
                "承認または却下を選択してください"
            )

        if action == "approve":
            row["address"] = address
            row["address_review_status"] = "approved"
        else:
            row["address_review_status"] = "rejected"

        row["address_review_source"] = (
            candidate["sourceUrl"]
        )

        row["address_review_note"] = note

    @staticmethod
    def update_location(row, data):
        latitude = str(
            data.get("latitude", "")
        ).strip()

        longitude = str(
            data.get("longitude", "")
        ).strip()

        notes = str(
            data.get("notes", "")
        ).strip()

        if not valid_coordinate(
            latitude,
            longitude,
        ):
            raise ValueError(
                "緯度・経度が不正です"
            )

        if not notes:
            raise ValueError(
                "確認メモが必要です"
            )

        if (
            row.get("review_status", "").strip()
            == "verified"
            and valid_coordinate(
                row.get("latitude"),
                row.get("longitude"),
            )
        ):
            old_lat = float(row["latitude"])
            old_lon = float(row["longitude"])

            if not (
                math.isclose(
                    old_lat,
                    float(latitude),
                    abs_tol=1e-7,
                    rel_tol=0,
                )
                and math.isclose(
                    old_lon,
                    float(longitude),
                    abs_tol=1e-7,
                    rel_tol=0,
                )
            ):
                raise ValueError(
                    "確認済み座標の変更は自動保存できません"
                )

        row["latitude"] = latitude
        row["longitude"] = longitude
        row["review_status"] = "verified"
        row["notes"] = notes


def main():
    load_data()
    load_candidates()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler,
    )

    url = f"http://{HOST}:{PORT}"

    print()
    print("FIELD//BASE Unified Research Manager")
    print("=" * 45)
    print(f"URL: {url}")
    print(f"CSV: {CSV_PATH}")
    print(f"Address candidates: {CANDIDATES_PATH}")
    print("終了: Ctrl+C")
    print()

    webbrowser.open(url)

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nサーバーを終了します")

    finally:
        server.server_close()


if __name__ == "__main__":
    main()

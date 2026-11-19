
#!/usr/bin/env python3
"""FIELD//BASE local research manager.

Features:
- Review official websites (HTTP and HTTPS).
- Review facility coordinates independently.
- Save research progress to CSV.
- Preserve other CSV columns.
- Create backups before saving.
- Restrict server access to localhost.
- Protect POST requests with a CSRF token.
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

CSV_PATH = (
    ROOT
    / "src"
    / "data"
    / "generated"
    / "fieldResearch.csv"
)

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
            "不足しているCSV列: "
            + ", ".join(sorted(missing))
        )

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

    return columns, rows


def valid_coordinate(latitude, longitude):
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        return False

    return (
        math.isfinite(lat)
        and math.isfinite(lon)
        and 20.0 <= lat <= 46.0
        and 122.0 <= lon <= 154.0
    )


def valid_official_url(value):
    """Accept public HTTP and HTTPS website URLs."""

    if not isinstance(value, str):
        return False

    if not value:
        return False

    if value != value.strip():
        return False

    if len(value) > 2048:
        return False

    if any(
        ord(character) < 33
        for character in value
    ):
        return False

    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return False

    if parsed.scheme not in {
        "http",
        "https",
    }:
        return False

    if not hostname:
        return False

    if port is not None:
        return False

    if parsed.username or parsed.password:
        return False

    if hostname.lower() == "localhost":
        return False

    if hostname.lower().endswith(".localhost"):
        return False

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        if "." not in hostname:
            return False

        if hostname.lower().endswith(
            (".local", ".internal", ".test", ".invalid")
        ):
            return False
    else:
        if not ip.is_global:
            return False

    return True


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

        os.replace(
            temporary,
            CSV_PATH,
        )

    finally:
        if temporary is not None:
            temporary.unlink(
                missing_ok=True
            )


def serialize_rows(rows):
    result = []

    for row in rows:
        result.append({
            "id": row.get(
                "field_id", ""
            ),
            "name": row.get(
                "field_name", ""
            ),
            "prefecture": row.get(
                "prefecture", ""
            ),
            "city": row.get(
                "city", ""
            ),
            "address": row.get(
                "address", ""
            ),
            "quality": row.get(
                "address_quality", ""
            ),
            "website": row.get(
                "website", ""
            ),
            "website_status": row.get(
                "website_status", ""
            ),
            "confirmed_url": row.get(
                "confirmed_official_url", ""
            ),
            "search_url": row.get(
                "official_site_search_url", ""
            ),
            "maps_url": row.get(
                "maps_search_url", ""
            ),
            "latitude": row.get(
                "latitude", ""
            ),
            "longitude": row.get(
                "longitude", ""
            ),
            "candidate_latitude": row.get(
                "candidate_latitude", ""
            ),
            "candidate_longitude": row.get(
                "candidate_longitude", ""
            ),
            "status": row.get(
                "review_status", "pending"
            ),
            "notes": row.get(
                "notes", ""
            ),
        })

    return result


def render_page():
    _, rows = load_data()

    payload = json.dumps(
        serialize_rows(rows),
        ensure_ascii=False,
    )

    payload = payload.replace(
        "<",
        "\\u003c",
    )

    token = json.dumps(TOKEN)

    template = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta
  name="viewport"
  content="width=device-width,initial-scale=1"
>
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
  max-width: 1350px;
  margin: auto;
  padding: 24px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
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
  font-size: 12px;
  color: #aab2b9;
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
textarea:focus,
select:focus {
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

button:disabled {
  opacity: .4;
  cursor: not-allowed;
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
    公式サイト・施設座標の確認とCSV管理
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
      <strong id="locationCount">0</strong>
      <span>座標確認済み</span>
    </div>

    <div class="stat">
      <strong id="candidateCount">0</strong>
      <span>未確認の座標候補</span>
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
      <option value="locationPending">
        座標未確認
      </option>
      <option value="locationVerified">
        座標確認済み
      </option>
      <option value="candidate">
        座標候補あり
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
        <h3>公式サイトの確認</h3>

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
          placeholder="http://example.jp/"
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
            公式URLを確認済みとして保存
          </button>
        </div>

        <div
          id="officialMessage"
          class="message"
          role="status"
        ></div>

        <p class="notice">
          HTTP・HTTPSの両方に対応しています。
          施設名・所在地・運営情報を確認した
          公式サイトだけを登録してください。
          HTTPは通信が暗号化されません。
        </p>
      </div>

      <div class="section">
        <h3>座標の確認</h3>

        <div class="actions">
          <a
            id="google"
            class="primary"
            target="_blank"
            rel="noopener noreferrer"
          >
            Googleマップ
          </a>

          <a
            id="osm"
            target="_blank"
            rel="noopener noreferrer"
          >
            OpenStreetMap
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

        <p class="notice">
          候補座標は未検証です。
          地図上の位置を確認してから保存してください。
          公開用JSONへの反映は別操作です。
        </p>
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

function officialVerified(field) {
  return Boolean(field.confirmed_url);
}

function locationVerified(field) {
  return field.status === "verified";
}

function hasCandidate(field) {
  return Boolean(
    field.candidate_latitude &&
    field.candidate_longitude
  );
}

function selected() {
  return (
    fields.find(
      field => field.id === selectedId
    ) || null
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
      field.name,
      field.address,
      field.prefecture,
      field.city,
      field.id
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

    if (filter === "locationPending") {
      return !locationVerified(field);
    }

    if (filter === "locationVerified") {
      return locationVerified(field);
    }

    if (filter === "candidate") {
      return (
        hasCandidate(field) &&
        !locationVerified(field)
      );
    }

    return true;
  });
}

function updateStats() {
  el("total").textContent =
    fields.length;

  el("officialCount").textContent =
    fields.filter(
      officialVerified
    ).length;

  el("locationCount").textContent =
    fields.filter(
      locationVerified
    ).length;

  el("candidateCount").textContent =
    fields.filter(
      field =>
        hasCandidate(field) &&
        !locationVerified(field)
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
        locationVerified(field)
          ? "座標 ✓"
          : "座標 未確認"
      ) +
      " / " +
      field.address;

    button.append(
      name,
      meta
    );

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
    (
      error
        ? "error"
        : "success"
    );
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

    if (
      url.username ||
      url.password
    ) {
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
    node.style.display =
      "inline-block";
  } else {
    node.removeAttribute("href");
    node.style.display = "none";
  }
}

function updateHttpWarning() {
  const value =
    el("officialUrl").value.trim();

  const warning =
    el("httpWarning");

  if (
    value.toLowerCase().startsWith(
      "http://"
    )
  ) {
    warning.textContent =
      "注意: HTTP通信です。通信内容は暗号化されません。"
      + "施設情報を確認してから登録してください。";
  } else {
    warning.textContent = "";
  }
}

function clearDetail() {
  selectedId = null;

  el("position").textContent = "";
  el("name").textContent =
    "対象施設がありません";
  el("address").textContent = "";
  el("websiteInfo").textContent = "";

  el("officialUrl").value = "";
  el("latitude").value = "";
  el("longitude").value = "";
  el("notes").value = "";
  el("candidate").textContent = "";

  updateHttpWarning();

  for (const id of [
    "searchOfficial",
    "openRegistered",
    "google",
    "osm"
  ]) {
    setLink(id, "");
  }

  for (const id of [
    "previous",
    "next",
    "saveOfficial",
    "saveLocation"
  ]) {
    el(id).disabled = true;
  }

  message("officialMessage", "");
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
      selectField(
        visible[0].id
      );
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

  el("name").textContent =
    field.name;

  el("address").textContent =
    field.prefecture +
    " " +
    field.city +
    " / " +
    field.address;

  el("websiteInfo").textContent =
    field.website
      ? "既存URL: " + field.website
      : "既存の公式URLは未登録です。";

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
    safeWebsiteUrl(
      field.website
    )
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

  setLink(
    "osm",
    "https://www.openstreetmap.org/search?query=" +
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
    hasCandidate(field)
      ? (
          "座標候補: " +
          field.candidate_latitude +
          ", " +
          field.candidate_longitude +
          "（保存前に確認が必要）"
        )
      : "座標候補なし";

  el("previous").disabled =
    index === 0;

  el("next").disabled =
    index === visible.length - 1;

  el("saveOfficial").disabled =
    saving;

  el("saveLocation").disabled =
    saving;

  message("officialMessage", "");
  message("locationMessage", "");

  renderList();
}

function move(direction) {
  const visible = visibleFields();

  const index = visible.findIndex(
    field =>
      field.id === selectedId
  );

  const next = index + direction;

  if (
    next >= 0 &&
    next < visible.length
  ) {
    selectField(
      visible[next].id
    );
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
      field =>
        field.id === selectedId
    )
  ) {
    selectField(
      visible[0].id
    );
  } else {
    selectField(selectedId);
  }
}

function afterSave(field, kind) {
  updateStats();

  const visible = visibleFields();

  if (
    !visible.some(
      item =>
        item.id === field.id
    )
  ) {
    if (visible.length) {
      selectField(
        visible[0].id
      );
    } else {
      clearDetail();
    }
  } else {
    selectField(field.id);
  }

  message(
    kind === "official"
      ? "officialMessage"
      : "locationMessage",
    field.name +
    " を保存しました。"
  );
}

async function postData(
  path,
  payload
) {
  const response = await fetch(
    path,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
        "X-Review-Token":
          token
      },
      body: JSON.stringify(
        payload
      )
    }
  );

  const result =
    await response.json();

  if (!response.ok) {
    throw new Error(
      result.error ||
      "保存に失敗しました"
    );
  }

  return result;
}

async function saveOfficial() {
  if (saving) {
    return;
  }

  const field = selected();

  if (!field) {
    return;
  }

  const url =
    el("officialUrl")
      .value
      .trim();

  if (!safeWebsiteUrl(url)) {
    message(
      "officialMessage",
      "有効なHTTPまたはHTTPSのURLを入力してください。",
      true
    );
    return;
  }

  const isHttp =
    url.toLowerCase().startsWith(
      "http://"
    );

  const warning = isHttp
    ? (
        "\n\n注意: HTTP通信のため"
        + "暗号化されていません。"
      )
    : "";

  if (
    !window.confirm(
      field.name +
      "\n" +
      url +
      "\n\n施設名・所在地・運営情報を確認しましたか？" +
      warning
    )
  ) {
    return;
  }

  saving = true;

  el("saveOfficial").disabled =
    true;

  el("saveLocation").disabled =
    true;

  try {
    await postData(
      "/api/official",
      {
        field_id: field.id,
        url
      }
    );

    field.confirmed_url = url;

    afterSave(
      field,
      "official"
    );

  } catch (error) {
    message(
      "officialMessage",
      error.message ||
      "保存失敗",
      true
    );

  } finally {
    saving = false;

    el("saveOfficial").disabled =
      !selected();

    el("saveLocation").disabled =
      !selected();
  }
}

async function saveLocation() {
  if (saving) {
    return;
  }

  const field = selected();

  if (!field) {
    return;
  }

  const latitude =
    el("latitude")
      .value
      .trim();

  const longitude =
    el("longitude")
      .value
      .trim();

  const notes =
    el("notes")
      .value
      .trim();

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
      "\n\n位置を確認済みとして保存しますか？"
    )
  ) {
    return;
  }

  saving = true;

  el("saveOfficial").disabled =
    true;

  el("saveLocation").disabled =
    true;

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
    field.status = "verified";

    afterSave(
      field,
      "location"
    );

  } catch (error) {
    message(
      "locationMessage",
      error.message ||
      "保存失敗",
      true
    );

  } finally {
    saving = false;

    el("saveOfficial").disabled =
      !selected();

    el("saveLocation").disabled =
      !selected();
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

        except (
            OSError,
            ValueError,
        ) as error:
            self.send_error(
                500,
                str(error),
            )

    def do_POST(self):
        path = urlparse(
            self.path
        ).path

        if path not in {
            "/api/official",
            "/api/location",
        }:
            self.send_error(404)
            return

        origin = self.headers.get(
            "Origin"
        )

        expected_origin = (
            f"http://{HOST}:{PORT}"
        )

        if (
            origin
            and origin != expected_origin
        ):
            self.send_error(403)
            return

        if (
            self.headers.get(
                "X-Review-Token"
            ) != TOKEN
        ):
            self.send_error(403)
            return

        try:
            length = int(
                self.headers.get(
                    "Content-Length",
                    "0",
                )
            )

            if (
                length <= 0
                or length > 16384
            ):
                raise ValueError(
                    "不正なリクエストサイズ"
                )

            data = json.loads(
                self.rfile.read(
                    length
                )
            )

            if not isinstance(
                data,
                dict,
            ):
                raise ValueError(
                    "リクエスト形式が不正です"
                )

            field_id = str(
                data.get(
                    "field_id",
                    "",
                )
            ).strip()

            with LOCK:
                columns, rows = load_data()

                match = next(
                    (
                        row
                        for row in rows
                        if (
                            row["field_id"]
                            == field_id
                        )
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
                else:
                    self.update_location(
                        match,
                        data,
                    )

                backup_file()

                save_data(
                    columns,
                    rows,
                )

            self.send_content(
                200,
                json.dumps(
                    {
                        "ok": True,
                        "field_id": field_id,
                    }
                ).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        except (
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as error:
            self.send_content(
                400,
                json.dumps(
                    {
                        "error": str(error),
                    },
                    ensure_ascii=False,
                ).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        except OSError as error:
            self.send_content(
                500,
                json.dumps(
                    {
                        "error": str(error),
                    },
                    ensure_ascii=False,
                ).encode("utf-8"),
                "application/json; charset=utf-8",
            )

    @staticmethod
    def update_official(
        row,
        data,
    ):
        url = str(
            data.get(
                "url",
                "",
            )
        ).strip()

        if not valid_official_url(
            url
        ):
            raise ValueError(
                "有効なHTTPまたはHTTPSの公式URLを入力してください"
            )

        row[
            "confirmed_official_url"
        ] = url

    @staticmethod
    def update_location(
        row,
        data,
    ):
        latitude = str(
            data.get(
                "latitude",
                "",
            )
        ).strip()

        longitude = str(
            data.get(
                "longitude",
                "",
            )
        ).strip()

        notes = str(
            data.get(
                "notes",
                "",
            )
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
            row.get(
                "review_status",
                "",
            ).strip()
            == "verified"
            and valid_coordinate(
                row.get("latitude"),
                row.get("longitude"),
            )
        ):
            old_lat = float(
                row["latitude"]
            )

            old_lon = float(
                row["longitude"]
            )

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
                    "確認済み座標の変更は"
                    "自動保存できません"
                )

        row["latitude"] = latitude
        row["longitude"] = longitude

        row["review_status"] = (
            "verified"
        )

        row["notes"] = notes


def main():
    load_data()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler,
    )

    url = (
        f"http://{HOST}:{PORT}"
    )

    print()
    print(
        "FIELD//BASE Research Manager"
    )
    print("=" * 40)
    print(f"URL: {url}")
    print(f"CSV: {CSV_PATH}")
    print("終了: Ctrl+C")
    print()

    webbrowser.open(url)

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print(
            "\nサーバーを終了します"
        )

    finally:
        server.server_close()


if __name__ == "__main__":
    main()

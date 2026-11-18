
#!/usr/bin/env python3
"""Create GitHub Issues for changed FIELD//BASE websites."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
REPORT_FILE = ROOT / "data-monitor/report.json"

API_ROOT = "https://api.github.com"
TIMEOUT = 20

ISSUE_MARKER_PREFIX = "<!-- field-base-monitor:"

MAX_DIFF_EXCERPT_CHARS = 600
MAX_DIFF_LINES = 12


def api_request(method, endpoint, token, payload=None):
    url = API_ROOT + endpoint

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FIELD-BASE-Monitor",
    }

    data = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    with urlopen(request, timeout=TIMEOUT) as response:
        raw = response.read()

    if not raw:
        return None

    return json.loads(raw.decode("utf-8"))


def load_report():
    with REPORT_FILE.open(encoding="utf-8") as file:
        report = json.load(file)

    if not isinstance(report, dict):
        raise ValueError("Invalid monitoring report")

    results = report.get("results")

    if not isinstance(results, list):
        raise ValueError("Report results must be a list")

    return report


def issue_marker(field_id):
    return f"{ISSUE_MARKER_PREFIX}{field_id} -->"


def list_open_issues(repository, token):
    issues = []

    for page in range(1, 101):
        query = urlencode({
            "state": "open",
            "per_page": 100,
            "page": page,
        })

        endpoint = f"/repos/{repository}/issues?{query}"

        batch = api_request(
            "GET",
            endpoint,
            token,
        )

        if not isinstance(batch, list):
            raise ValueError(
                "Unexpected GitHub Issues response"
            )

        for issue in batch:
            if "pull_request" not in issue:
                issues.append(issue)

        if len(batch) < 100:
            return issues

    raise RuntimeError(
        "Too many open issues to check safely"
    )


def existing_issue_for(field_id, issues):
    marker = issue_marker(field_id)

    for issue in issues:
        body = issue.get("body") or ""

        if marker in body:
            return issue

    return None


def safe_inline(value):
    value = str(value)
    value = value.replace("\r", " ").replace("\n", " ")
    value = value.replace("`", "'")
    value = value.replace("<", "&lt;")
    value = value.replace(">", "&gt;")
    return value


def safe_url(value):
    value = str(value).strip()

    if not value.startswith(("https://", "http://")):
        return "URLを確認してください"

    return value.replace("<", "%3C").replace(">", "%3E")


def diff_excerpt(field):
    if not field.get("diff_available"):
        return (
            "前回のテキストが保存されていないため、"
            "変更箇所の差分は表示できません。"
        )

    raw = field.get("text_diff")

    if not isinstance(raw, str) or not raw.strip():
        return (
            "ハッシュ値の変更は検出されましたが、"
            "表示可能な差分がありません。"
        )

    selected = []

    for line in raw.splitlines():
        if line.startswith(("---", "+++", "@@")):
            continue

        if not line.startswith(("+", "-")):
            continue

        content = line[1:].strip()

        if not content:
            continue

        selected.append(
            f"{line[0]} {safe_inline(content)}"
        )

        if len(selected) >= MAX_DIFF_LINES:
            break

    if not selected:
        return (
            "変更は検出されましたが、"
            "抜粋できる差分がありません。"
        )

    excerpt = "\n".join(selected)

    truncated = (
        len(excerpt) > MAX_DIFF_EXCERPT_CHARS
        or len(selected) >= MAX_DIFF_LINES
        or bool(field.get("diff_truncated"))
    )

    if len(excerpt) > MAX_DIFF_EXCERPT_CHARS:
        excerpt = excerpt[:MAX_DIFF_EXCERPT_CHARS]

    result = "\n".join([
        "```diff",
        excerpt.replace("```", "'''"),
        "```",
    ])

    if truncated:
        result += (
            "\n\n差分が長いため、"
            "一部のみ表示しています。"
        )

    return result


def make_issue(field, checked_at):
    field_id = field["id"]
    name = field["name"]
    url = field["url"]

    title = (
        "[FIELD//BASE Monitor] 要確認: "
        + safe_inline(name)
    )

    body = "\n".join([
        issue_marker(field_id),
        "## 公式サイトの変更を検出",
        "",
        f"**施設名:** {safe_inline(name)}",
        f"**施設ID:** `{safe_inline(field_id)}`",
        f"**登録済み公式URL:** {safe_url(url)}",
        f"**監視日時（UTC）:** {safe_inline(checked_at)}",
        "",
        "監視プログラムが、前回取得したページ本文と"
        "異なる内容を検出しました。",
        "",
        "この通知は、料金変更・閉業・営業状況の変更を"
        "意味するものではありません。",
        "",
        "## 変更箇所の抜粋",
        "",
        diff_excerpt(field),
        "",
        "この差分はページから抽出したテキストの比較です。",
        "実際の変更内容は必ず公式サイトで確認してください。",
        "",
        "## 確認すること",
        "",
        "- [ ] 公式サイトを開いて変更内容を確認",
        "- [ ] 料金・営業時間・所在地などへの影響を確認",
        "- [ ] 必要な場合のみ施設データを更新",
        "- [ ] 情報の出典を記録",
        "- [ ] 対応完了後、このIssueを閉じる",
        "",
        "## 関連情報",
        "",
        "監視結果の詳細はGitHub Actionsの"
        "FIELD BASE Data Monitor実行レポートを参照。",
        "",
        "_このIssueは自動作成されました。_",
    ])

    return {
        "title": title,
        "body": body,
    }


def validate_field(field):
    field_id = field.get("id")
    name = field.get("name")
    url = field.get("url")

    if not all(
        isinstance(value, str) and value
        for value in (field_id, name, url)
    ):
        raise ValueError(
            "Changed field has missing information"
        )

    if not re.fullmatch(r"[a-zA-Z0-9_-]+", field_id):
        raise ValueError("Invalid field ID")


def parse_args():
    parser = argparse.ArgumentParser(
        description="FIELD//BASE GitHub Issue notifier"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview Issues without using the GitHub API",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    report = load_report()

    changed = [
        item
        for item in report["results"]
        if item.get("status") == "changed"
    ]

    print(f"変更検出: {len(changed)}件")

    if not changed:
        print("変更がないためIssueは作成しません。")
        return 0

    for field in changed:
        validate_field(field)

    checked_at = report.get("checked_at", "unknown")

    if args.dry_run:
        print("DRY RUN: GitHub APIへの通信は行いません。")

        for field in changed:
            payload = make_issue(field, checked_at)

            print("\n" + "=" * 60)
            print(payload["title"])
            print("=" * 60)
            print(payload["body"])

        return 0

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repository = os.environ.get(
        "GITHUB_REPOSITORY", ""
    ).strip()

    if not token:
        print("ERROR: GITHUB_TOKEN is missing")
        return 1

    if not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
        repository,
    ):
        print("ERROR: GITHUB_REPOSITORY is invalid")
        return 1

    issues = list_open_issues(repository, token)

    created = 0
    skipped = 0

    for field in changed:
        field_id = field["id"]
        name = field["name"]

        existing = existing_issue_for(
            field_id,
            issues,
        )

        if existing is not None:
            print(
                f"既存Issueあり: {name} "
                f"({existing.get('html_url', '')})"
            )

            skipped += 1
            continue

        payload = make_issue(field, checked_at)

        endpoint = f"/repos/{repository}/issues"

        created_issue = api_request(
            "POST",
            endpoint,
            token,
            payload,
        )

        if not isinstance(created_issue, dict):
            raise ValueError(
                "Unexpected issue creation response"
            )

        issue_url = created_issue.get("html_url")

        if not issue_url:
            raise ValueError(
                "Created issue has no URL"
            )

        issues.append(created_issue)
        created += 1

        print(f"Issue作成: {name} -> {issue_url}")

    print(
        f"完了: 新規{created}件 / "
        f"重複スキップ{skipped}件"
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())

    except (HTTPError, URLError) as exc:
        print(
            f"GitHub API error: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    except (
        OSError,
        ValueError,
        RuntimeError,
    ) as exc:
        print(
            f"Notification error: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

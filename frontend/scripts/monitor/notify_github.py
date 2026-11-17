
#!/usr/bin/env python3
"""Create GitHub Issues for changed FIELD//BASE field websites."""

from __future__ import annotations

import json
import os
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

        endpoint = (
            f"/repos/{repository}/issues?{query}"
        )

        batch = api_request(
            "GET",
            endpoint,
            token,
        )

        if not isinstance(batch, list):
            raise ValueError("Unexpected GitHub Issues response")

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


def make_issue(field, checked_at):
    field_id = field["id"]
    name = field["name"]
    url = field["url"]

    title = f"[FIELD//BASE Monitor] 要確認: {name}"

    body = "\n".join([
        issue_marker(field_id),
        "## 公式サイトの変更を検出",
        "",
        f"**施設名:** {name}",
        f"**施設ID:** `{field_id}`",
        f"**登録済み公式URL:** {url}",
        f"**監視日時（UTC）:** {checked_at}",
        "",
        "監視プログラムが、前回取得したページ本文と"
        "異なる内容を検出しました。",
        "",
        "この通知は、料金変更・閉業・営業状況の変更を"
        "意味するものではありません。",
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


def main():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repository = os.environ.get(
        "GITHUB_REPOSITORY", ""
    ).strip()

    if not token:
        print("ERROR: GITHUB_TOKEN is missing")
        return 1

    if not repository or "/" not in repository:
        print("ERROR: GITHUB_REPOSITORY is invalid")
        return 1

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

    issues = list_open_issues(repository, token)

    created = 0
    skipped = 0

    for field in changed:
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

        payload = make_issue(
            field,
            report.get("checked_at", "unknown"),
        )

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
        print(f"GitHub API error: {exc}", file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Notification error: {exc}", file=sys.stderr)
        sys.exit(1)

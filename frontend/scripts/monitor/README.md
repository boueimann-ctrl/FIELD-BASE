
# FIELD//BASE Data Monitor

FIELD//BASEに登録されているサバイバルゲームフィールドの
公式サイトを定期監視するためのツールです。

## 目的

- 公式サイトへのアクセス状況を確認する
- ページ内容の変化を検出する
- 公式URL未登録の施設を特定する
- 調査が必要な施設をレポートにまとめる

## 使用技術

- Python標準ライブラリ
- GitHub Actions
- SHA-256

外部のAI APIや有料サービスは使用しません。

## ローカル実行

frontendディレクトリで実行します。

```bash
python3 scripts/monitor/monitor.py
```

## 出力ファイル

実行すると以下のファイルが生成されます。

- data-monitor/snapshots.json
- data-monitor/report.json
- data-monitor/report.md

snapshots.jsonは前回取得したページのハッシュを保存します。

report.jsonは機械処理用の結果です。

report.mdは人間が確認するためのレポートです。

## 監視結果の意味

- missing_url: 公式URLが未登録
- invalid_url: URL形式が不正
- baseline: 初回の基準データを作成
- unchanged: 前回と同じ内容
- changed: 前回からページ内容が変化
- robots_unknown: robots.txtを確認できない
- robots_disallowed: robots.txtによって取得禁止
- http_error: HTTPエラー
- request_error: 通信エラー
- redirect_review: 別ホストへのリダイレクト
- invalid_redirect: リダイレクト先が不正
- not_html: HTML以外のコンテンツ
- too_large: 取得サイズの上限超過
- empty_content: 抽出可能なテキストなし
- parse_error: その他の解析エラー

## 自動実行

GitHub Actionsで毎週月曜日に実行します。

GitHubリポジトリのActionsタブから手動実行も可能です。

実行結果はActionsのJob Summaryで確認できます。

JSONとMarkdownのレポートはArtifactsから取得できます。

スナップショットはGitHub Actionsのキャッシュに保存します。
キャッシュが消失した場合は新しい基準データを作成します。

## 安全上の方針

- robots.txtによるアクセス制限を尊重する
- ページ取得に失敗しても閉業と断定しない
- ページ変更を料金変更と断定しない
- 施設の公開データを自動的に書き換えない
- 公式サイト以外の一覧ページを公式URLとして扱わない
- 個人情報や認証情報を収集しない

## 今後の改善予定

- 施設の公式URL登録率の向上
- 変更箇所の詳細比較
- 料金・営業状況の変更候補抽出
- GitHub Issueによる確認依頼
- 承認後の施設情報更新
```

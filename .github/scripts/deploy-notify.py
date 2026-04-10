#!/usr/bin/env python3
"""
deploy-notify.py — Slack互換 Webhook 通知ペイロード生成

GitHub Actions の shared-nas-deploy ワークフローから呼び出され、
デプロイ結果（成功/失敗）を Slack 互換 Webhook に POST する。

必須環境変数:
    DEPLOY_REPO         — リポジトリ名 (例: komei-alt/ROSCH_OS)
    DEPLOY_CONTAINER    — コンテナ名
    DEPLOY_SHA          — コミットSHA
    DEPLOY_ACTOR        — 実行者
    DEPLOY_RUN_ID       — GitHub Actions Run ID
    DEPLOY_STATUS       — ジョブステータス (success / failure / cancelled)

オプション環境変数:
    DEPLOY_COMMIT_MSG   — コミットメッセージ（先頭行のみ使用）
    ERROR_LOG           — エラーログ（失敗時のみ）
    WEBHOOK_URL         — 送信先URL（未設定時は何もせず終了）
"""

import json
import os
import sys
import urllib.request
import urllib.error


def build_payload() -> dict:
    """デプロイ結果に応じた Slack 互換ペイロードを構築する。"""
    repo = os.environ["DEPLOY_REPO"]
    repo_name = repo.split("/")[-1]
    container = os.environ["DEPLOY_CONTAINER"]
    short_sha = os.environ["DEPLOY_SHA"][:7]
    actor = os.environ["DEPLOY_ACTOR"]
    run_id = os.environ["DEPLOY_RUN_ID"]
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}"
    commit_msg = os.environ.get("DEPLOY_COMMIT_MSG", "").split("\n")[0][:80]
    status = os.environ["DEPLOY_STATUS"]

    if status == "success":
        return {
            "text": f"[{repo_name}] Deploy OK ({short_sha})",
            "attachments": [
                {
                    "color": "#36a64f",
                    "title": f"Deploy OK — {repo_name}",
                    "text": (
                        f"{repo_name} へのデプロイが完了しました。\n"
                        f"{commit_msg}\n"
                        f"by {actor} ({short_sha})"
                    ),
                }
            ],
        }

    # failure / cancelled
    error_log = os.environ.get("ERROR_LOG", "") or "(no logs captured)"
    if len(error_log) > 1500:
        error_log = error_log[:1500] + "\n... (truncated)"

    return {
        "text": f"[{repo_name}] Deploy FAILED ({short_sha})",
        "attachments": [
            {
                "color": "#dc3545",
                "title": f"Deploy FAILED — {repo_name}",
                "text": (
                    f"{repo_name} のデプロイに失敗しました。\n"
                    f"{commit_msg}\n"
                    f"by {actor} ({short_sha})\n"
                    f"Actions: {run_url}"
                ),
            },
            {
                "color": "#6c757d",
                "title": "Error Logs",
                "text": error_log,
            },
        ],
    }


def send_webhook(url: str, payload: dict) -> None:
    """ペイロードを Webhook URL へ POST する。"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"Webhook sent (HTTP {resp.status})")
    except urllib.error.URLError as e:
        print(f"Webhook notification failed: {e}", file=sys.stderr)


def main() -> None:
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    if not webhook_url:
        print("No webhook URL configured. Skipping notification.")
        return

    payload = build_payload()
    send_webhook(webhook_url, payload)


if __name__ == "__main__":
    main()

# ROSCH Actions

ロッシュ合同会社の **共有 GitHub Actions ワークフロー** リポジトリ。  
各プロジェクトから `workflow_call` で呼び出し、NAS 上の Docker 環境へデプロイする。

## 使い方

呼び出し元のワークフローで以下のように参照する:

```yaml
jobs:
  deploy:
    uses: komei-alt/ROSCH_Actions/.github/workflows/shared-nas-deploy.yml@main
    with:
      deploy_dir: /volume1/docker/my-app
      compose_dir: /volume1/docker/my-app
      container_name: my-app
      health_url: http://localhost:3000/api/health
    secrets: inherit
```

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `deploy_dir` | ✅ | — | デプロイ先ディレクトリ |
| `compose_dir` | ✅ | — | docker-compose 実行ディレクトリ |
| `container_name` | ✅ | — | ログ取得用コンテナ名 |
| `health_url` | — | — | ヘルスチェック URL（未指定時はスキップ） |
| `setup_node` | — | `false` | Node.js v20 セットアップ |
| `pre_deploy_script` | — | — | デプロイ前スクリプト |
| `sync_excludes` | — | `node_modules,data,.git,...` | tar 同期時の除外 |
| `preserve_files` | — | `data,docker-compose.yml,...` | NAS 側で維持するファイル |
| `deploy_delay` | — | `0` | デバウンス秒数 |
| `post_build_script` | — | — | ビルド後スクリプト（マイグレーション等） |
| ~~`webhook_url`~~ | — | — | ⚠️ **非推奨** — `secrets.WEBHOOK_URL` を使用 |

## Secrets

| シークレット | 必須 | 説明 |
|-------------|------|------|
| `WEBHOOK_URL` | — | Slack 互換 Webhook URL（プロジェクト固有） |
| `ROSCH_DEFAULT_WEBHOOK_URL` | — | Organization デフォルト Webhook URL（フォールバック） |

### Webhook 優先順位

```
secrets.WEBHOOK_URL  →  inputs.webhook_url  →  secrets.ROSCH_DEFAULT_WEBHOOK_URL
```

## デプロイフロー

```
Checkout → Pre-deploy → Disk Check → Sync Code → Save Rollback
    → Docker Build → Post-build → Swap Container
    → Health Check → (失敗時) Auto Rollback
    → Garbage Collection → Webhook Notify
```

## ディレクトリ構成

```
.github/
├── scripts/
│   └── deploy-notify.py      # Slack互換 Webhook 通知スクリプト
└── workflows/
    └── shared-nas-deploy.yml  # 共有デプロイワークフロー
```

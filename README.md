# BOX SDK 自動アップロード MVP

## 概要
ローカルの CSV を BOX にアップロードするシンプルな CLI。  
JWT もしくは Developer Token で認証できます（個人利用は Developer Token 推奨）。

## 前提
- Python 3.12+
- uv で依存導入済み (`uv add ...` 実施済み)
- 環境変数は `.env` に設定し、`PYTHONPATH=./src` を付けて実行する

## .env の例
Developer Token を使う場合（JWT 項目は空で可）:
```
BOX_DEVELOPER_TOKEN=xxxxx
BOX_UPLOAD_FOLDER_ID=123456789
LOCAL_DATA_DIR=./data
UPLOAD_LOG_PATH=.upload_log.json
```

JWT を使う場合（Enterprise/App User 環境向け）:
```
BOX_CLIENT_ID=...
BOX_CLIENT_SECRET=...
BOX_JWT_KEY_ID=...
BOX_JWT_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
BOX_JWT_PASSPHRASE=...
BOX_ENTERPRISE_ID=...        # もしくは BOX_APP_USER_ID=...
BOX_UPLOAD_FOLDER_ID=...
LOCAL_DATA_DIR=./data
UPLOAD_LOG_PATH=.upload_log.json
```

## 接続確認（whoami）
```bash
PYTHONPATH=./src .venv/bin/python - <<'PY'
from boxsdk_trial.config import BoxSettings, build_client
settings = BoxSettings.from_env(".env")
client = build_client(settings)
me = client.users.get_user_me()
print("OK:", me.id, me.name, me.login)
PY
```

## よく使うコマンド
- ダミー生成: `PYTHONPATH=./src uv run python -m boxsdk_trial.cli make-dummy --files 2 --rows 5`
- 一覧表示: `PYTHONPATH=./src uv run python -m boxsdk_trial.cli list`
- アップロード: `PYTHONPATH=./src uv run python -m boxsdk_trial.cli upload`
  - `--limit 3` で送るファイル数を絞れる

## 動作ログ
- アップロード済み管理: `.upload_log.json`（パスは `UPLOAD_LOG_PATH` で変更可）
- ファイルが 0 件の場合やアップロード結果は INFO/ERROR ログで表示

## トラブルシュート
- `ModuleNotFoundError: boxsdk_trial` → `PYTHONPATH=./src` を付与
- `invalid_grant` → Developer Token に切り替えるか、JWT 設定の `sub` (App User/Enterprise User) を確認
- `Missing PyJWT` → 依存は `pyjwt[crypto]` を導入済み。再インストールするなら `uv add "pyjwt[crypto]"`。

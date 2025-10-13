# クイックスタートガイド: アプリケーション更新管理機能

**作成日**: 2025-10-13
**対象読者**: 開発者
**所要時間**: 30-60分

---

## 概要

このガイドでは、アプリケーション更新管理機能のローカル開発環境を迅速にセットアップし、基本的な動作確認を行う手順を説明します。

---

## 前提条件

### 必須ソフトウェア

- **Docker** 24.0以上
- **Docker Compose** 2.20以上
- **Python** 3.12以上
- **Pipenv** 2023.10以上
- **Git** 2.40以上

### 確認方法

```bash
# Docker
docker --version
# => Docker version 24.0.0, build ...

# Docker Compose
docker-compose --version
# => Docker Compose version 2.20.0

# Python
python3 --version
# => Python 3.12.0

# Pipenv
pipenv --version
# => pipenv, version 2023.10.0

# Git
git --version
# => git version 2.40.0
```

### システム要件

- **OS**: Linux (Ubuntu 22.04推奨) / macOS 13以上
- **CPU**: 4コア以上推奨
- **メモリ**: 8GB以上推奨
- **ディスク**: 20GB以上の空き容量

---

## 1. ローカル開発環境セットアップ

### 1.1 リポジトリのクローン

```bash
# メインリポジトリをクローン
git clone https://github.com/kugel-masa/kugelpos-backend.git
cd kugelpos-backend

# 更新管理機能のブランチをチェックアウト
git checkout 002-notes-2-upgrade
```

### 1.2 環境変数の設定

```bash
# テスト環境ファイルをコピー
cp .env.test.sample .env.test

# .env.testを編集（テナントIDを変更する場合）
# デフォルトではTENANT_ID=A1234を使用
nano .env.test
```

**.env.test の内容例**:

```bash
# Tenant configuration
TENANT_ID=A1234
STORE_CODE=tokyo

# MongoDB configuration
MONGODB_URI=mongodb://localhost:27017/?replicaSet=rs0
MONGODB_DATABASE=sync_A1234

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT configuration
JWT_SECRET_KEY=your-secret-key-for-development-only
JWT_EXPIRY_SECONDS=3600

# Sync service configuration
SYNC_POLL_INTERVAL=900  # 15 minutes in seconds
```

### 1.3 Scriptsディレクトリへ移動して初期化

```bash
# Scriptsディレクトリへ移動
cd scripts

# すべてのスクリプトに実行権限を付与
bash make_scripts_executable.sh
```

### 1.4 Python仮想環境の構築

```bash
# 全サービスの仮想環境を構築
./rebuild_pipenv.sh

# 構築には5-10分かかります
# 完了後、以下のメッセージが表示されます:
# => All services' Pipenv environments rebuilt successfully
```

### 1.5 MongoDBレプリカセットの初期化

```bash
# MongoDBとRedisを起動
cd ../services
docker-compose up -d mongodb redis

# レプリカセットを初期化
../scripts/init-mongodb-replica.sh

# 初期化完了を確認
docker exec -it mongodb mongosh --eval "rs.status()" | grep "ok"
# => "ok" : 1 が表示されればOK
```

---

## 2. サービス起動手順

### 2.1 Cloud Sync Service の起動

```bash
# Servicesディレクトリへ移動
cd services

# Sync Serviceのコンテナをビルド
docker-compose build sync

# Sync Serviceを起動
docker-compose up -d sync

# 起動確認（ヘルスチェック）
curl http://localhost:8007/health
# => {"status":"healthy"}
```

**ログ確認**:

```bash
# リアルタイムログ表示
docker-compose logs -f sync

# 起動完了のメッセージを確認:
# => INFO:     Uvicorn running on http://0.0.0.0:8007 (Press CTRL+C to quit)
```

### 2.2 Edge Sync Service の起動（シード端末用）

**注意**: Edge Sync ServiceはEdge端末またはシードPOS端末で実行されます。ローカル開発環境では、Cloud Sync Serviceと同じホストで起動してシミュレートします。

```bash
# Edge Sync Serviceを別ポート（8008）で起動
docker-compose up -d edge-sync

# 起動確認
curl http://localhost:8008/health
# => {"status":"healthy"}
```

**Edge Sync Serviceの設定**:

Edge Sync Serviceは以下の環境変数で設定されます（docker-compose.override.yaml）:

```yaml
edge-sync:
  image: kugelpos/sync:latest
  container_name: edge-sync
  ports:
    - "8008:8007"
  environment:
    - EDGE_MODE=true  # Edge modeを有効化
    - P2P_SEED=true
    - P2P_PRIORITY=0
    - CACHE_DIR=/opt/kugelpos/cache
  volumes:
    - edge_cache:/opt/kugelpos/cache
```

### 2.3 テストクライアント（Edge/POS startup script）

**擬似エッジ端末の起動**:

開発環境では、エッジ端末をシミュレートするスクリプトを使用します。

```bash
# テストクライアントディレクトリへ移動
cd ../test-client

# 仮想環境の構築
pipenv install

# エッジ端末（シード）のシミュレート
pipenv run python edge_client.py \
  --edge-id edge-A1234-tokyo-001 \
  --device-type edge \
  --is-seed true \
  --priority 0 \
  --secret abcdef1234567890abcdef1234567890abcdef1234567890

# POS端末のシミュレート（別ターミナルで実行）
pipenv run python edge_client.py \
  --edge-id edge-A1234-tokyo-002 \
  --device-type pos \
  --is-seed false \
  --priority 99 \
  --secret xyz9876543210xyz9876543210xyz9876543210
```

**edge_client.py の主要機能**:

1. **認証**: `/api/v1/version-management/auth` でJWTトークンを取得
2. **バージョンチェック**: `/api/v1/version-management/check` で更新要否を確認
3. **ダウンロード**: Manifestに従ってファイルとコンテナイメージをダウンロード
4. **通知**: ダウンロード完了・適用完了をクラウドに通知

---

## 3. API動作確認

### 3.1 認証トークン取得

```bash
# デバイス認証リクエスト
curl -X POST http://localhost:8007/api/v1/version-management/auth \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "A1234",
    "store_code": "tokyo",
    "edge_id": "edge-A1234-tokyo-001",
    "device_type": "edge",
    "secret": "abcdef1234567890abcdef1234567890abcdef1234567890"
  }'

# レスポンス例:
# {
#   "success": true,
#   "data": {
#     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#     "token_type": "bearer",
#     "expires_in": 3600,
#     "edge_id": "edge-A1234-tokyo-001"
#   }
# }
```

**トークンを環境変数に保存**:

```bash
export JWT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 3.2 バージョンチェック実行

```bash
# バージョンチェックリクエスト
curl -X POST http://localhost:8007/api/v1/version-management/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "device_type": "edge",
    "edge_id": "edge-A1234-tokyo-001",
    "current_version": "1.2.2"
  }'

# レスポンス例（更新あり）:
# {
#   "success": true,
#   "data": {
#     "update_available": true,
#     "current_version": "1.2.2",
#     "target_version": "1.2.3",
#     "manifest": { ... }
#   }
# }

# レスポンス例（更新なし）:
# {
#   "success": true,
#   "data": {
#     "update_available": false,
#     "current_version": "1.2.3",
#     "message": "Device is running the latest version"
#   }
# }
```

### 3.3 Manifestダウンロード

バージョンチェックのレスポンスに含まれるManifestを確認します。

```bash
# Manifestの内容を整形して表示
curl -X POST http://localhost:8007/api/v1/version-management/check \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "device_type": "pos",
    "edge_id": "edge-A1234-tokyo-002",
    "current_version": "1.2.2"
  }' | jq '.data.manifest'

# 出力例:
# {
#   "manifest_version": "1.0",
#   "device_type": "pos",
#   "device_id": "edge-A1234-tokyo-002",
#   "target_version": "1.2.3",
#   "artifacts": [
#     {
#       "type": "script",
#       "name": "pos-startup.sh",
#       "version": "1.2.3",
#       "primary_url": "http://192.168.1.10:8007/api/v1/artifacts/pos-startup.sh?version=1.2.3",
#       "fallback_url": "https://sync.kugelpos.cloud/api/v1/artifacts/pos-startup.sh?version=1.2.3",
#       "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
#       "size": 15360,
#       "destination": "/opt/kugelpos/pos-startup.sh",
#       "permissions": "755"
#     }
#   ],
#   "available_seeds": [
#     {
#       "edge_id": "edge-A1234-tokyo-001",
#       "priority": 0,
#       "url": "http://192.168.1.10:8007"
#     }
#   ],
#   "apply_schedule": {
#     "scheduled_at": "2025-01-18T02:00:00Z",
#     "maintenance_window": 30
#   }
# }
```

### 3.4 ファイルダウンロード

```bash
# アーティファクトをダウンロード
curl -X POST http://localhost:8007/api/v1/artifact-management/download \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "artifact_type": "script",
    "artifact_name": "pos-startup.sh",
    "version": "1.2.3"
  }' \
  --output pos-startup.sh

# チェックサムを確認
sha256sum pos-startup.sh
# => e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  pos-startup.sh
```

### 3.5 デバイス一覧取得

```bash
# 全デバイスの状態を取得
curl -X GET http://localhost:8007/api/v1/devices \
  -H "Authorization: Bearer $JWT_TOKEN" | jq

# フィルタリング例（更新中のデバイスのみ）
curl -X GET "http://localhost:8007/api/v1/devices?update_status=downloading" \
  -H "Authorization: Bearer $JWT_TOKEN" | jq

# 出力例:
# {
#   "success": true,
#   "data": {
#     "devices": [
#       {
#         "edge_id": "edge-A1234-tokyo-002",
#         "device_type": "pos",
#         "current_version": "1.2.2",
#         "target_version": "1.2.3",
#         "update_status": "downloading",
#         "download_status": "in_progress",
#         "last_check_timestamp": "2025-01-17T14:30:00Z"
#       }
#     ],
#     "pagination": {
#       "total": 1,
#       "page": 1,
#       "limit": 20,
#       "total_pages": 1
#     }
#   }
# }
```

### 3.6 更新履歴取得

```bash
# 特定デバイスの更新履歴を取得
curl -X GET http://localhost:8007/api/v1/devices/edge-A1234-tokyo-001/history \
  -H "Authorization: Bearer $JWT_TOKEN" | jq

# 出力例:
# {
#   "success": true,
#   "data": {
#     "edge_id": "edge-A1234-tokyo-001",
#     "history": [
#       {
#         "update_id": "550e8400-e29b-41d4-a716-446655440000",
#         "from_version": "1.2.2",
#         "to_version": "1.2.3",
#         "start_time": "2025-01-18T02:00:00Z",
#         "end_time": "2025-01-18T02:03:30Z",
#         "downtime_seconds": 90,
#         "status": "success",
#         "rollback_performed": false,
#         "artifacts_count": 15,
#         "total_size_bytes": 524288000
#       }
#     ]
#   }
# }
```

---

## 4. テスト実行

### 4.1 ユニットテスト

**Sync Serviceのユニットテストを実行**:

```bash
# Sync Serviceディレクトリへ移動
cd services/sync

# 全テストを実行
pipenv run pytest tests/ -v

# 特定のテストファイルのみ実行
pipenv run pytest tests/test_version_management.py -v

# カバレッジ付きでテスト実行
pipenv run pytest --cov=app tests/
```

**期待される出力**:

```
============================= test session starts ==============================
collected 25 items

tests/test_auth.py::test_authenticate_device_success PASSED              [  4%]
tests/test_auth.py::test_authenticate_device_invalid_secret FAILED       [  8%]
tests/test_version_check.py::test_version_check_update_available PASSED  [ 12%]
tests/test_version_check.py::test_version_check_no_update PASSED         [ 16%]
...

========================= 23 passed, 2 failed in 12.34s ========================
```

### 4.2 統合テスト

**Sync Serviceと他サービスの統合テストを実行**:

```bash
# プロジェクトルートへ移動
cd ../..

# 全サービスの統合テストを実行
./scripts/run_all_tests.sh

# 進捗表示付きで実行
./scripts/run_all_tests_with_progress.sh
```

**テスト実行順序**:

1. `test_clean_data.py`: テストデータをクリーンアップ
2. `test_setup_data.py`: テストデータをセットアップ
3. 機能テスト（test_auth.py, test_version_check.py, etc.）

### 4.3 E2Eテスト

**エンドツーエンドシナリオテストを実行**:

```bash
# E2Eテストディレクトリへ移動
cd tests/e2e

# E2Eテストを実行
pipenv run pytest test_update_flow.py -v

# 実行されるシナリオ:
# 1. デバイス認証
# 2. バージョンチェック
# 3. ダウンロードフェーズ（Phase 1-3）
# 4. ダウンロード完了通知
# 5. 適用フェーズ（Phase 4-9）のシミュレート
# 6. 適用完了通知
# 7. 更新履歴の確認
```

**E2Eテストのカバレッジ**:

- **ユーザーストーリー1**: 自動更新とオフライン耐性
- **ユーザーストーリー2**: コンテナイメージの差分更新
- **ユーザーストーリー4**: P2P優先度制御による高速ダウンロード
- **ユーザーストーリー6**: デバイス認証とセキュアな配信
- **ユーザーストーリー7**: 2段階更新による業務影響最小化

---

## 5. トラブルシューティング

### 5.1 MongoDB接続エラー

**エラー**:

```
pymongo.errors.ServerSelectionTimeoutError: localhost:27017: [Errno 111] Connection refused
```

**解決方法**:

```bash
# MongoDBが起動しているか確認
docker ps | grep mongodb

# 起動していない場合
docker-compose up -d mongodb

# レプリカセットを再初期化
../scripts/init-mongodb-replica.sh
```

### 5.2 JWT認証エラー

**エラー**:

```json
{
  "success": false,
  "error": {
    "code": "800101",
    "message": "Invalid credentials"
  }
}
```

**解決方法**:

```bash
# デバイスが登録されているか確認
docker exec -it mongodb mongosh sync_A1234 --eval "db.edge_terminals.find({edge_id: 'edge-A1234-tokyo-001'})"

# デバイスが存在しない場合、登録
# (test_setup_data.pyを実行してテストデータをセットアップ)
cd services/sync
pipenv run pytest tests/test_setup_data.py -v
```

### 5.3 ファイルダウンロードエラー

**エラー**:

```json
{
  "success": false,
  "error": {
    "code": "800301",
    "message": "Artifact not found"
  }
}
```

**解決方法**:

```bash
# Azure Blob Storageにファイルが存在するか確認
# （開発環境ではローカルファイルシステムをシミュレート）

# テスト用のアーティファクトを配置
mkdir -p /tmp/kugelpos-artifacts/scripts/pos-startup.sh/v1.2.3
echo "#!/bin/bash" > /tmp/kugelpos-artifacts/scripts/pos-startup.sh/v1.2.3/pos-startup.sh
chmod 755 /tmp/kugelpos-artifacts/scripts/pos-startup.sh/v1.2.3/pos-startup.sh

# 環境変数を設定（docker-compose.override.yaml）
# BLOB_STORAGE_PATH=/tmp/kugelpos-artifacts
```

### 5.4 P2Pシード端末が見つからない

**エラー**:

```
ManifestのAvailable_seedsが空
```

**解決方法**:

```bash
# シード端末のダウンロードが完了しているか確認
curl -X GET http://localhost:8007/api/v1/devices/edge-A1234-tokyo-001 \
  -H "Authorization: Bearer $JWT_TOKEN" | jq '.data.download_status'

# "completed" でない場合、シード端末で先にダウンロードを完了させる
# （edge_client.py でシード端末をシミュレート）
pipenv run python edge_client.py --edge-id edge-A1234-tokyo-001 --device-type edge --is-seed true --priority 0
```

### 5.5 ポート競合

**エラー**:

```
Error starting userland proxy: listen tcp4 0.0.0.0:8007: bind: address already in use
```

**解決方法**:

```bash
# ポートを使用しているプロセスを特定
lsof -i :8007

# プロセスを終了
kill -9 <PID>

# または、docker-compose.override.yamlでポートを変更
# ports:
#   - "8017:8007"  # 8007の代わりに8017を使用
```

---

## 6. 次のステップ

### 6.1 機能開発

- **data-model.md**: データモデル設計を確認し、RepositoryとDocumentクラスを実装
- **contracts/**: API契約を確認し、FastAPIエンドポイントを実装
- **TDD**: テストファーストで開発（Red-Green-Refactorサイクル）

### 6.2 デプロイ

- **Docker Image Build**: 本番用のDockerイメージをビルド
- **Azure Container Registry**: イメージをACRにプッシュ
- **Azure Container Apps**: Sync Serviceをデプロイ
- **MongoDB Atlas**: 本番環境のMongoDBを構成

### 6.3 監視・運用

- **Azure Monitor**: メトリクスとログの収集
- **Prometheus/Grafana**: ダッシュボードの構築
- **アラート設定**: 更新失敗、ロールバック発生時の通知

---

## 7. リソース

### ドキュメント

- **spec.md**: 機能仕様書
- **research.md**: 技術調査報告書
- **data-model.md**: データモデル設計
- **contracts/**: API契約（OpenAPI 3.0）
- **CLAUDE.md**: プロジェクト全体の開発ガイドライン

### スクリプト

- **scripts/start.sh**: 全サービス起動
- **scripts/stop.sh**: 全サービス停止
- **scripts/build.sh**: 全サービスビルド
- **scripts/run_all_tests.sh**: 全テスト実行

### テストクライアント

- **test-client/edge_client.py**: エッジ端末シミュレーター
- **test-client/pos_client.py**: POS端末シミュレーター

---

## FAQ

### Q1: テスト環境でインターネット接続が必要ですか？

**A1**: ローカル開発環境ではインターネット接続は不要です。Azure Blob Storageとコンテナレジストリをローカルファイルシステムでシミュレートします。本番環境ではAzureへの接続が必要です。

### Q2: P2P配信をテストするには複数のマシンが必要ですか？

**A2**: 不要です。1台のマシンで複数のEdge Sync Serviceを異なるポートで起動し、シミュレートできます（8007, 8008, 8009等）。

### Q3: テストデータはどこに保存されますか？

**A3**: MongoDBの `sync_A1234` データベースに保存されます。テストデータをクリアするには `test_clean_data.py` を実行してください。

### Q4: ダウングレードは可能ですか？

**A4**: 本システムではダウングレードは実装されていません（仕様上、バージョンは常に前進）。問題のあるバージョンから戻す場合は、修正内容を新しいバージョン番号で再登録して適用してください。

### Q5: 自動ロールバックはどのような場合に発動しますか？

**A5**: 以下の場合に自動ロールバックが実行されます:
- サービス起動失敗（Phase 7）
- ヘルスチェック失敗（Phase 8）
- タイムアウト（120秒以内に起動完了しない）

---

## サポート

### 問題報告

GitHubのIssueで報告してください:
- https://github.com/kugel-masa/kugelpos-backend/issues

### 連絡先

- **開発チーム**: dev@kugelpos.com
- **Slack**: #kugelpos-sync-service（内部チーム用）

---

**作成日**: 2025-10-13
**作成者**: Claude Code (Documentation Writer)
**承認**: 未承認

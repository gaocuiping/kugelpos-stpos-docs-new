# Implementation Plan: Sync Service データ同期機能

**Branch**: `001-sync-service` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-sync-service/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Sync Serviceは、クラウド環境とエッジ環境（店舗）間でデータ同期を行うサービスです。マスターデータ（商品、価格、決済方法等）をクラウドからエッジへ配信し、トランザクションデータ（取引ログ、開設精算、入出金等）をエッジからクラウドへ集約します。オフライン耐性、データ整合性の自動保証、予約反映機能、P2Pファイル共有を備えた高信頼性の同期システムを実現します。

**主要機能:**
- **マスターデータ同期（クラウド→エッジ）**: 差分同期・一括同期、チェックサム検証、バージョン検証、自動補完
- **トランザクションデータ集約（エッジ→クラウド）**: At-least-once delivery、リトライ機構、サーキットブレーカー
- **予約反映機能**: 指定日時での自動マスタ反映、P2Pファイル共有によるクラウド負荷軽減
- **ファイル収集**: エッジ環境のログ・設定ファイルの遠隔収集（トラブルシューティング用）
- **エッジ端末認証**: JWT トークンベース認証、24時間有効期限

**技術的アプローチ:**
- FastAPI による非同期REST APIサーバー（Cloud Mode / Edge Mode の2モード動作）
- MongoDB によるテナント別データベース分離（`sync_{tenant_id}`形式）
- Dapr を活用したサービス間通信（pub/sub、Service Invocation）
- Motor（async MongoDB driver）による非同期データベース操作
- Circuit Breaker Pattern、Retry Pattern による回復力設計

## Technical Context

**Language/Version**: Python 3.12 以上
**Primary Dependencies**:
- FastAPI (Webフレームワーク)
- Motor (MongoDB async driver)
- Dapr (サービスメッシュ、pub/sub、Service Invocation)
- Redis (キャッシュ、メッセージング)
- Pydantic (データ検証、スキーマ定義)
- httpx (非同期HTTPクライアント、Dapr通信用)
- python-jose (JWT トークン生成・検証)
- bcrypt (認証シークレットのハッシュ化)

**Storage**:
- MongoDB 7.0+（レプリカセット構成、テナント別データベース `sync_{tenant_id}`）
- Redis（キャッシュ、Dapr pub/sub のバックエンド）

**Testing**:
- pytest (テストフレームワーク)
- pytest-asyncio (非同期テストサポート)
- httpx (APIテスト用HTTPクライアント)
- mongomock (MongoDB モック、単体テスト用、オプション)

**Target Platform**:
- Linux server（Docker コンテナ、Cloud Mode）
- Linux server（Docker コンテナ、Edge Mode、店舗環境）

**Project Type**: マイクロサービス（既存の7サービスに追加される8番目のサービス）

**Performance Goals**:
- **同期遅延**: 95パーセンタイルで5分以内 (SC-001)
- **スループット（全件同期）**: 10,000件/秒以上 (SC-002)
- **スループット（差分同期）**: 1,000件/秒以上 (SC-003)
- **並行処理**: 最大1,000エッジ端末の同時同期対応 (SC-004)
- **稼働率**: 99.9%以上 (SC-005)
- **ネットワーク復旧後の再開時間**: 30秒以内 (SC-006)
- **チェックサム検証成功率**: 99.9%以上 (SC-008)
- **バージョン補完成功率**: 95%以上 (SC-009)
- **予約反映精度**: 指定日時±30秒以内 (SC-010)
- **P2Pトラフィック削減率**: 50%以上 (SC-011)
- **ファイル収集完了時間**: 5分以内（100MB以下） (SC-012)
- **JWT認証成功率**: 99.9%以上 (SC-013)
- **データ圧縮率**: 50%以上（gzip使用） (SC-015)
- **API レスポンス**: 95パーセンタイルで500ms以下（憲章基準）

**Constraints**:
- **同期ポーリング間隔**: 30-60秒（環境変数 `SYNC_POLL_INTERVAL` で調整可能）
- **JWT トークン有効期限**: 24時間（環境変数で設定可能）
- **リトライ回数**: 最大5回（指数バックオフ: 1秒→2秒→4秒→8秒→16秒）
- **サーキットブレーカー**: 連続3回失敗でオープン、60秒後に半開状態
- **ファイル収集サイズ**: 最大100MB
- **補完同期**: 1回あたり最大20バージョン
- **データ保証**: At-least-once delivery
- **ネットワーク復旧検知**: エッジ端末からクラウドへの最初の成功したHTTPリクエスト完了時点をネットワーク復旧検知とする。復旧検知後30秒以内に同期処理を自動再開する (SC-006)

**Scale/Scope**:
- **エッジ端末数**: 最大1,000台（同時接続想定）
- **データ種別**: 4種類（master_data: マスターデータ、transaction_log: トランザクションログ、journal: 電子ジャーナル、terminal_state: ターミナル状態変更）
- **主要エンティティ**: 8つ（SyncStatus, SyncHistory, EdgeTerminal, ScheduledMasterFile, FileCollection, MasterData, TransactionLog, TerminalStateChange）
- **API エンドポイント**: 約15個（認証、同期リクエスト、マスタ予約反映、ファイル収集等）

## Service Integration Details

### データアクセス原則

**重要**: Sync Serviceは**自身のデータベース（`sync_{tenant_id}`）のみ直接アクセス可能**です。他サービスのデータは**必ずAPIを通じてアクセス**します。

### クラウド環境内通信（Cloud Sync ↔ Cloud Services）

クラウド環境では、**Pull型（API呼出）とPush型（Pub/Sub）が混在**します。

#### 通信方式マトリックス

| データ種別 | 通信方向 | 通信方式 | エンドポイント/トピック | 理由 |
|-----------|---------|---------|----------------------|------|
| マスターデータ取得 | Sync → master-data | **Dapr Service Invocation** | `POST /api/v1/sync/changes` | Syncが主導権を持ち、配信タイミングを制御 |
| ターミナルマスタ取得 | Sync → terminal | **Dapr Service Invocation** | `POST /api/v1/sync/changes` | 差分または一括取得、確実な配信確認 |
| ターミナル状態変更取得 | Sync → terminal | **Dapr Service Invocation** | `GET /api/v1/terminals/{terminal_id}/state-changes` | 特定ターミナルの状態変更取得 |
| ジャーナル配信 | Sync → journal | **Dapr Service Invocation** | `POST /api/v1/sync/apply` | エッジから受信したジャーナルの確実な配信 |
| トランザクションログ配信 | Sync → cart, terminal | **Dapr Pub/Sub (Push)** | トピック: `tranlog_report`, `cashlog_report`, `opencloselog_report` | 既存トピック活用、複数サービスへの配信 |
| ファイル保管 | Sync → Cloud Storage | **Dapr Binding** | Binding: `sync-storage` (S3/GCS/Azure Blob/Local Storage) | ストレージ抽象化、環境依存排除、テスト容易性 |

#### Dapr Service Invocation 実装例

```python
# master-dataサービスから差分データ取得
url = f"{DAPR_HTTP_ENDPOINT}/v1.0/invoke/master-data/method/api/v1/sync/changes"
headers = {"Content-Type": "application/json"}
payload = {
    "last_sync_timestamp": "2025-10-13T10:00:00Z",
    "data_types": ["categories", "products_common", "products_store"]
}

async with httpx.AsyncClient() as client:
    response = await client.post(url, json=payload, headers=headers)
    master_data = response.json()
```

#### Pub/Sub トピック詳細

**受信するトピック（既存）**:
- `tranlog_report`: トランザクションデータ（レポート用）
- `cashlog_report`: 現金入出金イベント
- `opencloselog_report`: ターミナル開閉イベント

**送信するトピック（Syncがpublish）**:
- 同上（エッジから受信したログをクラウド内サービスへ配信）

### エッジ環境内通信（Edge Sync ↔ Edge Services）

エッジ環境では、**Push型（Pub/Sub）とPull型（API呼出）が混在**します。

#### 通信方式マトリックス

| データ種別 | 通信方向 | 通信方式 | エンドポイント/トピック | 理由 |
|-----------|---------|---------|----------------------|------|
| マスターデータ適用 | Sync → master-data | **Dapr Service Invocation** | `POST /api/v1/sync/apply` | 大量データの一括適用、確実性確保 |
| ターミナルマスタ適用 | Sync → terminal | **Dapr Service Invocation** | `POST /api/v1/sync/apply` | データ適用の確実性 |
| ターミナル状態取得 | Sync → terminal | **Dapr Service Invocation** | `GET /api/v1/terminals/state-changes?store_code={store_code}` | 店舗内の全ターミナルの状態変更を取得 |
| トランザクションログ収集 | cart, terminal → Sync | **Pub/Sub (Push)** | トピック: `tranlog_report`, `cashlog_report`, `opencloselog_report` | 既存トピック活用、リアルタイム性 |
| ジャーナル取得 | Sync → journal | **Dapr Service Invocation** | `GET /api/v1/journal/unsent` | 未送信データの差分取得 |
| ファイル収集 | Sync → 各サービス | **Dapr Service Invocation** | `POST /api/v1/file-collection/collect` | 各サービスがエンドポイント提供 |

#### Dapr Service Invocation 実装例

```python
# master-dataサービスへデータ適用
url = f"{DAPR_HTTP_ENDPOINT}/v1.0/invoke/master-data/method/api/v1/sync/apply"
headers = {"Content-Type": "application/json"}
payload = {
    "sync_type": "incremental",
    "data": {
        "categories": [...],
        "products_common": [...]
    }
}

async with httpx.AsyncClient() as client:
    response = await client.post(url, json=payload, headers=headers)
    result = response.json()
```

### 環境間通信（Cloud Sync ↔ Edge Sync）

#### 認証フロー

1. Edge Sync起動時にedge_id + secretで認証
2. Cloud SyncがJWT トークン発行（tenant_id、edge_id、store_codeを含む、有効期限24時間）
3. 以降の通信はJWT トークンをAuthorizationヘッダーに付与
4. **トークン自動更新**: 有効期限1時間前に自動的に新しいトークンを取得（プロアクティブ更新）
5. **401エラー時の自動再認証**: 期限切れトークンで401エラー発生時、自動的に再認証してリトライ

#### データ圧縮

- **圧縮アルゴリズム**: gzip（圧縮レベル6）
- **対象データ**: JSON形式のマスターデータ、トランザクションログ、ジャーナル
- **Content-Encoding**: `gzip` ヘッダー使用
- **圧縮効果**: 平均60-80%のサイズ削減

#### REST APIエンドポイント

**Edge → Cloud (Pull方式)**:
- `POST /api/v1/sync/auth` - エッジデバイス認証、JWT取得
- `POST /api/v1/sync/request` - マスターデータ・ターミナルマスタのリクエスト
- `GET /api/v1/sync/scheduled-master/check` - 予約ファイル保持状況確認
- `GET /api/v1/sync/scheduled-master/download/{file_id}` - 予約ファイルダウンロード

**Edge → Cloud (Push方式)**:
- `POST /api/v1/sync/transaction-logs` - トランザクションログのpush
- `POST /api/v1/sync/journals` - ジャーナルデータのpush
- `POST /api/v1/sync/terminal-status` - ターミナル状態のpush
- `POST /api/v1/sync/file-collection/{collection_id}/upload` - ファイル収集アーカイブアップロード

### 通信方式の使い分け理由

| パターン | 使用ケース | 理由 |
|---------|-----------|------|
| **Pull (API)** | マスターデータ配信 | Syncが主導権を持ち、配信タイミングを制御 |
| **Pull (API)** | ジャーナル配信・収集 | 確実な配信確認が必要 |
| **Pull (API)** | ターミナル状態取得 | 定期的な状態確認 |
| **Pull (API)** | ファイル収集 | オンデマンド収集、各サービスが自身のファイルを管理 |
| **Push (Pub/Sub)** | トランザクションログ | 既存トピック活用、複数サービスへの配信、リアルタイム性 |
| **Dapr Binding** | ファイル保管 | ストレージ抽象化（S3/GCS/Azure/Local Storage）、環境切り替え容易、テスト容易性 |

### ファイル収集の実装方針

#### 他サービスへの要件（方式１: API呼出）

**対象サービス**: cart, terminal, master-data, journal, report, stock

各サービスは、ファイル収集用のAPIエンドポイントを実装する必要があります：

- **エンドポイント**: `POST /api/v1/file-collection/collect`
- **通信方式**: Dapr Service Invocation
- **リクエスト形式**:
  ```json
  {
    "target_paths": ["/app/logs/error.log", "/app/logs/app.log"],
    "exclude_patterns": ["*.tmp", "*.bak"],
    "max_size_mb": 50
  }
  ```
- **レスポンス形式**: zip圧縮されたバイナリデータ（Content-Type: application/zip）
- **責務**:
  - 自サービスのアプリケーションログ・設定ファイルを収集
  - ホワイトリスト検証（サービス固有のホワイトリストに基づく）
  - zip形式で圧縮（最大100MB制限）
  - バイナリデータとして返却

**実装例**:
```python
# Edge Syncから各サービスへのファイル収集呼び出し
url = f"{DAPR_HTTP_ENDPOINT}/v1.0/invoke/cart/method/api/v1/file-collection/collect"
headers = {"Content-Type": "application/json"}
payload = {
    "target_paths": ["/app/logs/cart.log"],
    "exclude_patterns": ["*.tmp"],
    "max_size_mb": 50
}

async with httpx.AsyncClient() as client:
    response = await client.post(url, json=payload, headers=headers, timeout=300.0)
    zip_bytes = response.content  # 各サービスから返却されたzipデータ
```

#### Syncサービス自身のファイル収集（方式２: 直接ファイルシステムアクセス）

Syncサービス自身のログ・設定ファイルの収集は、直接ファイルシステムにアクセスします：

- **対象ファイル**: `/app/logs/sync.log`, `/app/logs/sync_error.log`, `/app/config/settings.yaml` 等
- **実装方式**:
  - ホワイトリスト検証（`FILE_COLLECTION_WHITELIST` 環境変数）
  - `aiofiles` による非同期ファイル読み取り
  - `ThreadPoolExecutor` による zip 圧縮
  - 他サービスから収集したzipと統合して最終アーカイブを生成

**実装例**:
```python
import aiofiles
import zipfile
from concurrent.futures import ThreadPoolExecutor

# Syncサービス自身のログ収集
async def collect_sync_logs(target_paths: list[str]) -> bytes:
    # ホワイトリスト検証
    whitelist = settings.FILE_COLLECTION_WHITELIST
    validated_paths = [p for p in target_paths if any(p.startswith(w) for w in whitelist)]

    # 非同期ファイル読み取り
    files_data = []
    for path in validated_paths:
        async with aiofiles.open(path, 'rb') as f:
            content = await f.read()
            files_data.append((path, content))

    # zip圧縮（非同期化）
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        zip_bytes = await loop.run_in_executor(
            executor,
            lambda: create_zip_archive(files_data)
        )

    return zip_bytes
```

**統合処理**:
1. 各サービスから方式１でzipデータを収集
2. Syncサービス自身のログを方式２で収集
3. すべてのzipを統合して最終アーカイブを生成
4. **Dapr Binding経由でストレージにアップロード**（方式３）

#### ストレージ保管（方式３: Dapr Binding）

収集したファイルアーカイブは、Dapr Bindingコンポーネントを通じてクラウドストレージに保管します。

**メリット**:
- **ストレージ抽象化**: S3/GCS/Azure Blob/Local Storageを統一インターフェースで操作
- **環境切り替え**: YAML設定変更のみで異なるストレージバックエンドに対応
- **テスト容易**: 開発環境ではLocal Storage、本番ではS3/GCSを使用
- **認証管理簡素化**: IAMロール、サービスアカウント認証をDaprが管理
- **ベンダーロックイン回避**: ストレージプロバイダーを柔軟に変更可能

**Dapr Binding コンポーネント設定例**:

開発環境（Local Storage）: `services/dapr/components/sync-storage-local.yaml`
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: sync-storage
spec:
  type: bindings.localstorage
  version: v1
  metadata:
  - name: rootPath
    value: "/tmp/sync-storage"
```

本番環境（AWS S3）: `services/dapr/components/sync-storage-s3.yaml`
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: sync-storage
spec:
  type: bindings.aws.s3
  version: v1
  metadata:
  - name: bucket
    value: "kugelpos-sync-files"
  - name: region
    value: "ap-northeast-1"
  - name: accessKey
    secretKeyRef:
      name: aws-credentials
      key: accessKey
  - name: secretKey
    secretKeyRef:
      name: aws-credentials
      key: secretKey
```

本番環境（GCS）: `services/dapr/components/sync-storage-gcs.yaml`
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: sync-storage
spec:
  type: bindings.gcp.bucket
  version: v1
  metadata:
  - name: bucket
    value: "kugelpos-sync-files"
  - name: type
    value: "service_account"
  - name: projectId
    value: "your-gcp-project"
  - name: privateKeyId
    secretKeyRef:
      name: gcp-credentials
      key: privateKeyId
  - name: privateKey
    secretKeyRef:
      name: gcp-credentials
      key: privateKey
```

**Storage Service 実装例**:

`services/sync/app/services/file_collection/storage_service.py`
```python
from typing import Optional
from datetime import datetime
import logging
from kugel_common.utils.dapr_client_helper import get_dapr_client

logger = logging.getLogger(__name__)

class StorageService:
    """File storage service using Dapr Bindings"""

    def __init__(self, binding_name: str = "sync-storage"):
        self.binding_name = binding_name

    async def upload_archive(
        self,
        collection_id: str,
        file_data: bytes,
        tenant_id: str
    ) -> str:
        """Upload file collection archive to storage via Dapr Binding"""
        # Generate storage path with tenant isolation
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        file_key = f"{tenant_id}/file-collections/{timestamp}/{collection_id}.zip"

        # Upload via Dapr Binding
        async with get_dapr_client() as client:
            metadata = {
                "key": file_key,
                "contentType": "application/zip"
            }

            await client.invoke_binding(
                binding_name=self.binding_name,
                operation="create",
                data=file_data,
                metadata=metadata
            )

        logger.info(
            f"Uploaded archive to storage",
            extra={
                "collection_id": collection_id,
                "file_key": file_key,
                "size_bytes": len(file_data)
            }
        )

        return file_key

    async def generate_download_url(
        self,
        file_key: str,
        expiry_hours: int = 168  # 7 days
    ) -> str:
        """Generate presigned URL for secure download (S3/GCS)"""
        async with get_dapr_client() as client:
            metadata = {
                "key": file_key,
                "expiresInSec": str(expiry_hours * 3600)
            }

            try:
                response = await client.invoke_binding(
                    binding_name=self.binding_name,
                    operation="presignURL",  # S3/GCS specific operation
                    data=b"",
                    metadata=metadata
                )

                url = response.get("url", "")
                logger.info(f"Generated presigned URL", extra={"file_key": file_key})
                return url
            except Exception as e:
                # Fallback for Local Storage (no presigned URL support)
                logger.warning(
                    f"Presigned URL not supported, using direct download endpoint",
                    extra={"error": str(e)}
                )
                from app.config.settings import settings
                return f"{settings.SYNC_SERVICE_URL}/api/v1/file-collection/download/{file_key}"

    async def download_archive(self, file_key: str) -> bytes:
        """Download archive from storage via Dapr Binding"""
        async with get_dapr_client() as client:
            metadata = {"key": file_key}

            response = await client.invoke_binding(
                binding_name=self.binding_name,
                operation="get",
                data=b"",
                metadata=metadata
            )

            file_data = response.get("data", b"")
            logger.info(f"Downloaded archive", extra={"file_key": file_key, "size_bytes": len(file_data)})
            return file_data

    async def delete_archive(self, file_key: str) -> None:
        """Delete archive from storage via Dapr Binding"""
        async with get_dapr_client() as client:
            metadata = {"key": file_key}

            await client.invoke_binding(
                binding_name=self.binding_name,
                operation="delete",
                data=b"",
                metadata=metadata
            )

        logger.info(f"Deleted archive", extra={"file_key": file_key})
```

**環境変数設定**:
```bash
# Storage Backend Selection
STORAGE_BACKEND=local  # local, s3, gcs, azure (for documentation purposes)
STORAGE_BINDING_NAME=sync-storage

# Local Storage Root (development)
LOCAL_STORAGE_ROOT=/tmp/sync-storage

# AWS S3 Configuration (production)
AWS_S3_BUCKET=kugelpos-sync-files
AWS_S3_REGION=ap-northeast-1

# GCS Configuration (production alternative)
GCS_BUCKET=kugelpos-sync-files
GCS_PROJECT_ID=your-gcp-project
```

**ストレージパス構造**:
```
{tenant_id}/file-collections/{YYYYMMDD}/{collection_id}.zip

例:
tenant001/file-collections/20251014/550e8400-e29b-41d4-a716-446655440000.zip
tenant002/file-collections/20251014/550e8400-e29b-41d4-a716-446655440001.zip
```

**動作フロー**:
1. Edge Sync: ファイル収集完了 → zip生成
2. Edge Sync → Cloud Sync: `POST /api/v1/sync/file-collection/{collection_id}/upload` でzipアップロード
3. Cloud Sync: StorageService経由でDapr Bindingにアップロード
4. Cloud Sync: FileCollectionモデルに `storage_key` を保存
5. 管理者: Cloud Syncに `GET /api/v1/file-collection/tasks/{collection_id}/download` でダウンロードURL取得
6. StorageService: presigned URL生成（S3/GCS）またはプロキシダウンロード提供（Local Storage）
7. 管理者: presigned URLから直接ダウンロード（S3/GCS）またはCloud Sync経由でダウンロード（Local Storage）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. マイクロサービス独立性

- **独立データベース**: ✅ Sync Service は独自のテナント別データベース `sync_{tenant_id}` を持つ
- **サービス間通信**: ✅ Dapr pub/sub（トランザクションログ受信）、Service Invocation（Journalサービス、Master-dataサービスとの通信）
- **共通ライブラリ**: ✅ commons ライブラリを使用（ユーティリティのみ、ビジネスロジックなし）
- **独立テスト**: ✅ 独立したテストスイート（`services/sync/tests/`）

### ✅ II. 非同期優先 (Async-First)

- **データベース操作**: ✅ Motor (async MongoDB driver) を使用
- **HTTP クライアント**: ✅ httpx（非同期HTTPクライアント、Dapr通信用）
- **FastAPI エンドポイント**: ✅ すべての API は `async def` で定義
- **ブロッキング操作**: ✅ ファイルI/O は `aiofiles` で非同期化、zip圧縮は `ThreadPoolExecutor` で非同期化

### ✅ III. テスト駆動開発 (TDD)

- **テストカバレッジ目標**: 80%以上（重要なビジネスロジックは90%以上）
- **テストファイル**: `test_clean_data.py` → `test_setup_data.py` → 機能テスト
- **pytest-asyncio**: ✅ 非同期テスト対応

### ✅ IV. イベント駆動アーキテクチャ

- **Dapr Pub/Sub**: ✅ トランザクションデータを既存トピックから受信
  - `tranlog_report`: トランザクションデータ（レポート用）
  - `cashlog_report`: 現金入出金イベント
  - `opencloselog_report`: ターミナル開閉イベント
- **イベントスキーマ**: ✅ Pydantic モデルでバージョニング
- **冪等性**: ✅ `sync_status` フィールドで重複配信対応（`pending` → `sent`）

### ✅ V. 回復力とエラーハンドリング (Resilience)

- **Circuit Breaker**: ✅ 3回連続失敗でオープン、60秒後に半開状態（`HttpClientHelper`, `DaprClientHelper` で実装）
- **Retry**: ✅ 指数バックオフ、最大5回リトライ
- **Timeout**: ✅ HTTP 30秒、データベース 10秒（憲章基準）
- **エラーコード体系**: ✅ 80YYZZ形式（80=sync service、8番目のマイクロサービス）

### ✅ VI. マルチテナンシー（厳格な分離）

- **データベースレベル分離**: ✅ `sync_{tenant_id}` 形式
- **API 検証**: ✅ すべてのAPIで tenant_code を検証（JWT ペイロードから取得）
- **クロステナントアクセス禁止**: ✅ JWT トークンの tenant_id でアクセス制御

### ✅ VII. 可観測性 (Observability)

- **構造化ロギング**: ✅ JSON形式、必須フィールド（timestamp, service_name, tenant_code, correlation_id）
- **メトリクス**: ✅ リクエスト数、レスポンスタイム、同期成功/失敗率、データサイズ
- **分散トレーシング**: ✅ correlation_id を Dapr の分散トレーシングと連携

### ✅ VIII. セキュリティファースト

- **JWT トークンベース認証**: ✅ edge_id + secret で JWT 発行（24時間有効）
- **シークレットのハッシュ化**: ✅ bcrypt でハッシュ化して保存
- **入力検証**: ✅ すべてのAPI入力をPydantic スキーマで検証
- **環境変数管理**: ✅ 機密データは `.env` ファイル（コミット禁止）

### 🟡 追加検証が必要な項目

- **State Machine Pattern**: Sync Serviceでは不要（Cart Serviceの責務）
- **Plugin Architecture**: Sync Serviceでは不要（機能が明確に定義済み）

### 総合評価（Phase 0前）

✅ **合格**: すべての必須原則に準拠しています。Phase 0（research）に進むことができます。

---

## Constitution Check Re-evaluation (Phase 1完了後)

*GATE: Phase 1 (data-model.md, contracts/, quickstart.md) 完了後の再評価*

### ✅ I. マイクロサービス独立性（再評価）

- **data-model.md**: ✅ テナント別データベース分離を詳細定義（`sync_{tenant_id}`パターン、8エンティティのスキーマ）
- **contracts/*.yaml**: ✅ Dapr Service Invocation使用を明示（master-data、journalサービスとの通信）
- **quickstart.md**: ✅ AbstractRepository継承パターン、独立テスト戦略を説明
- **検証結果**: 各エンティティがBaseDocumentModelを継承し、独立したリポジトリパターンで実装される設計

### ✅ II. 非同期優先（再評価）

- **data-model.md**: ✅ すべてのRepositoryメソッドがasyncで定義（例: `async def find_by_edge_and_type`）
- **contracts/*.yaml**: ✅ すべてのAPIエンドポイントが非同期処理を前提（OpenAPI 3.0仕様）
- **quickstart.md**: ✅ Motor、httpx、aiofiles、APScheduler AsyncIOSchedulerの使用を明示
- **検証結果**: ファイルI/Oは`aiofiles`、zip圧縮は`ThreadPoolExecutor`で非同期化

### ✅ III. テスト駆動開発（再評価）

- **quickstart.md**: ✅ TDD開発ワークフローを詳細説明（Red-Green-Refactorサイクル）
- **quickstart.md**: ✅ テスト例を提供（`test_sync_status.py`、単体・統合テスト構造）
- **quickstart.md**: ✅ テストカバレッジ目標80%以上、pytest-asyncio使用を明記
- **検証結果**: `tests/unit/`、`tests/integration/`のディレクトリ構造を定義

### ✅ IV. イベント駆動アーキテクチャ（再評価）

- **research.md**: ✅ Dapr Service Invocation使用決定（HttpClientHelper + Dapr HTTP API）
- **data-model.md**: ✅ TransactionLogモデルでpub/sub受信を想定（`sync_status`フィールド）
- **sync-api.yaml**: ✅ トランザクション送信エンドポイント定義（Edge → Cloud）
- **検証結果**: 既存の`tranlog_report`、`cashlog_report`トピックからイベント受信

### ✅ V. 回復力とエラーハンドリング（再評価）

- **contracts/*.yaml**: ✅ エラーレスポンススキーマ定義（XXYYZZ形式エラーコード: 800101等）
- **data-model.md**: ✅ `retry_count`、`error_message`フィールドをSyncStatus、SyncHistoryに定義
- **research.md**: ✅ Circuit Breaker、Retry Pattern実装方針（HttpClientHelper、DaprClientHelper使用）
- **quickstart.md**: ✅ Circuit Breaker設定（`SYNC_CIRCUIT_BREAKER_THRESHOLD=3`、`SYNC_CIRCUIT_BREAKER_TIMEOUT=60`）
- **競合解決**: ✅ Last Write Wins（FR-018）はspec.mdエッジケースで定義、タイムスタンプ比較により実装
- **検証結果**: 最大5回リトライ、指数バックオフ、At-least-once delivery保証

### ✅ VI. マルチテナンシー（再評価）

- **data-model.md**: ✅ データベース戦略セクションで`sync_{tenant_id}`パターンを明示
- **contracts/auth-api.yaml**: ✅ JWTトークンレスポンスに`tenant_id`、`store_code`を含める
- **data-model.md**: ✅ EdgeTerminalモデルに`tenant_id`フィールド定義
- **quickstart.md**: ✅ `get_database(tenant_id)`関数でテナント別DB取得を説明
- **検証結果**: 完全なデータベースレベル分離を実現

### ✅ VII. 可観測性（再評価）

- **data-model.md**: ✅ SyncHistory（監査ログ）、SyncStatus（状態追跡）で詳細なログ記録
- **contracts/*.yaml**: ✅ 構造化エラーレスポンス定義（error_code、message、detail、timestamp）
- **quickstart.md**: ✅ 構造化ロギング言及（`LOG_FORMAT=json`）
- **検証結果**: 相関ID（correlation_id）、テナントID、エッジIDを含む包括的なログ設計

### ✅ VIII. セキュリティファースト（再評価）

- **contracts/auth-api.yaml**: ✅ JWT認証フロー詳細定義（24時間有効期限）
- **data-model.md**: ✅ EdgeTerminalモデルで`secret`フィールドをSHA256ハッシュ化（64文字hex）
- **contracts/file-collection-api.yaml**: ✅ ホワイトリスト検証を定義（`FILE_COLLECTION_WHITELIST`）
- **quickstart.md**: ✅ .envファイル使用、`JWT_SECRET_KEY`環境変数管理を説明
- **contracts/*.yaml**: ✅ すべてのエンドポイントで入力検証（Pydanticスキーマ、パターンマッチング）
- **検証結果**: TLS 1.2+必須、Pydanticスキーマによる入力検証、機密データのハッシュ化

### 🟢 設計フェーズ後の追加検証

- **Repository Pattern**: ✅ data-model.mdで全8エンティティのリポジトリ実装例を提供
- **Index Strategy**: ✅ data-model.mdで各エンティティのインデックス定義（複合インデックス、TTLインデックス含む）
- **State Transitions**: ✅ data-model.mdでSyncStatus、TerminalStateChangeの状態遷移図を提供
- **API Contract Quality**: ✅ contracts/*.yamlでOpenAPI 3.0準拠、詳細な例、エラーケース定義
- **Developer Experience**: ✅ quickstart.mdで30分でセットアップ完了可能な手順を提供

### 総合評価（Phase 1完了後）

✅ **合格**: すべての必須原則に準拠した設計が完了しています。実装フェーズ（Phase 2: tasks.md生成）に進むことができます。

**設計品質**:
- 8エンティティの完全なデータモデル定義（Pydanticスキーマ、インデックス、検証ルール）
- 4つのOpenAPI仕様（認証、同期、予約マスタ、ファイル収集）
- 開発者向けクイックスタートガイド（30分でセットアップ完了）
- プロジェクト憲章の8原則すべてに準拠

## Project Structure

### Documentation (this feature)

```
specs/001-sync-service/
├── spec.md              # 機能仕様書（完成）
├── checklists/
│   └── requirements.md  # 要件品質チェックリスト（完成）
├── plan.md              # このファイル (/speckit.plan 実行中)
├── research.md          # Phase 0 output（次のステップ）
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output（API仕様書）
    ├── auth-api.yaml
    ├── sync-api.yaml
    ├── scheduled-master-api.yaml
    └── file-collection-api.yaml
```

### Source Code (repository root)

```
services/sync/
├── app/
│   ├── main.py                          # FastAPI アプリケーションエントリーポイント
│   ├── config/
│   │   ├── settings.py                  # 環境変数、設定管理
│   │   └── constants.py                 # 定数定義
│   ├── models/                          # データモデル（MongoDB Document）
│   │   ├── sync_status.py               # 同期ステータス
│   │   ├── sync_history.py              # 同期履歴
│   │   ├── edge_terminal.py             # エッジ端末
│   │   ├── scheduled_master_file.py     # 予約反映マスタファイル
│   │   ├── file_collection.py           # ファイル収集
│   │   ├── master_data.py               # マスターデータ（参照用）
│   │   ├── transaction_log.py           # トランザクションログ（参照用）
│   │   └── terminal_state_change.py     # ターミナル状態変更（参照用）
│   ├── repositories/                    # Repository Pattern（データアクセス層）
│   │   ├── sync_status_repository.py
│   │   ├── sync_history_repository.py
│   │   ├── edge_terminal_repository.py
│   │   ├── scheduled_master_file_repository.py
│   │   └── file_collection_repository.py
│   ├── services/                        # ビジネスロジック層
│   │   ├── auth/
│   │   │   ├── auth_service.py          # 認証サービス（JWT発行・検証、Cloud Mode）
│   │   │   └── token_manager.py         # JWT トークンライフサイクル管理（Edge Mode専用）
│   │   ├── sync/
│   │   │   ├── sync_manager.py          # 同期マネージャー（メイン処理）
│   │   │   ├── master_sync_service.py   # マスターデータ同期
│   │   │   ├── transaction_sync_service.py  # トランザクションデータ同期
│   │   │   └── integrity_checker.py     # 整合性チェッカー（チェックサム、バージョン検証）
│   │   ├── scheduled_master/
│   │   │   ├── scheduled_master_service.py  # 予約反映サービス
│   │   │   └── p2p_manager.py           # P2Pファイル共有マネージャー
│   │   └── file_collection/
│   │       ├── file_collection_service.py   # ファイル収集サービス
│   │       └── storage_service.py       # ストレージサービス（Dapr Binding経由）
│   ├── api/                             # API エンドポイント
│   │   ├── v1/
│   │   │   ├── auth.py                  # 認証API
│   │   │   ├── sync.py                  # 同期API（リクエスト、実行、履歴）
│   │   │   ├── scheduled_master.py      # 予約反映API
│   │   │   └── file_collection.py       # ファイル収集API
│   │   └── dependencies.py              # 依存性注入（JWT検証、DB接続等）
│   ├── schemas/                         # Pydantic スキーマ（リクエスト/レスポンス）
│   │   ├── auth_schemas.py
│   │   ├── sync_schemas.py
│   │   ├── scheduled_master_schemas.py
│   │   └── file_collection_schemas.py
│   ├── middleware/                      # ミドルウェア
│   │   ├── logging_middleware.py        # リクエストログ
│   │   └── correlation_id_middleware.py # 相関ID管理
│   ├── utils/                           # ユーティリティ
│   │   ├── jwt_helper.py                # JWT ヘルパー
│   │   ├── hash_helper.py               # ハッシュ計算（SHA-256、bcrypt）
│   │   ├── file_helper.py               # ファイル操作（zip圧縮等）
│   │   ├── dapr_helper.py               # Dapr 通信ヘルパー（commons から利用）
│   │   └── authenticated_http_client.py # 自動再認証機能付きHTTPクライアント（Edge Mode用）
│   └── background/                      # バックグラウンドタスク
│       ├── polling_scheduler.py         # 定期ポーリング（エッジモード用）
│       ├── token_refresh_scheduler.py   # トークン自動更新（エッジモード用）
│       └── scheduled_master_executor.py # 予約反映実行（エッジモード用）
├── tests/                               # テストコード
│   ├── conftest.py                      # pytest設定、共通フィクスチャ
│   ├── test_clean_data.py               # データクリーンアップ（全テスト実行前）
│   ├── test_setup_data.py               # テストデータセットアップ（全テスト実行前）
│   ├── unit/                            # 単体テスト（外部依存なし、モック使用）
│   │   ├── conftest.py                  # 単体テスト用フィクスチャ
│   │   ├── test_models/                 # モデル検証テスト
│   │   │   ├── test_sync_status.py      # SyncStatus モデルテスト
│   │   │   ├── test_edge_terminal.py    # EdgeTerminal モデルテスト
│   │   │   ├── test_sync_history.py     # SyncHistory モデルテスト
│   │   │   ├── test_transaction_log.py  # TransactionLog モデルテスト
│   │   │   └── test_terminal_state_change.py  # TerminalStateChange モデルテスト
│   │   ├── test_repositories/           # リポジトリテスト（MongoDB モック）
│   │   │   ├── test_sync_status_repository.py
│   │   │   ├── test_edge_terminal_repository.py
│   │   │   └── test_transaction_log_repository.py
│   │   ├── test_services/               # サービスロジックテスト（モック使用）
│   │   │   ├── test_jwt_service.py      # JWT サービステスト
│   │   │   ├── test_master_sync_service.py  # マスターデータ同期テスト
│   │   │   ├── test_transaction_sync_service.py  # トランザクション同期テスト
│   │   │   ├── test_integrity_checker.py  # 整合性チェッカーテスト
│   │   │   ├── test_token_manager.py    # トークンマネージャーテスト
│   │   │   └── test_storage_service.py  # ストレージサービステスト
│   │   └── test_utils/                  # ユーティリティテスト
│   │       ├── test_file_helper.py      # ファイルヘルパーテスト
│   │       └── test_authenticated_http_client.py  # HTTP クライアントテスト
│   └── integration/                     # 統合テスト（実サービス呼び出し）
│       ├── conftest.py                  # 統合テスト用フィクスチャ（DB接続等）
│       ├── test_auth_api.py             # 認証API統合テスト（MongoDB + FastAPI）
│       ├── test_sync_api.py             # 同期API統合テスト
│       ├── test_scheduled_master_api.py # 予約反映API統合テスト
│       ├── test_file_collection_api.py  # ファイル収集API統合テスト
│       ├── test_background_jobs.py      # バックグラウンドジョブテスト
│       └── test_end_to_end.py           # エンドツーエンドテスト（全体フロー検証）
├── Dockerfile                           # Docker イメージ定義
├── Pipfile                              # 依存関係定義
├── Pipfile.lock                         # 依存関係ロックファイル
├── run.py                               # ローカル実行スクリプト
└── README.md                            # サービス概要、セットアップ手順
```

**Structure Decision**:

既存の Kugelpos マイクロサービスアーキテクチャに準拠した単一プロジェクト構造を採用します。`services/sync/` ディレクトリを新規作成し、既存の7サービス（account, terminal, master-data, cart, report, journal, stock）と同じディレクトリ構造・命名規則に従います。

- **app/**: FastAPI アプリケーションコード（models, repositories, services, api, schemas）
- **tests/**: pytest テストコード（unit/ と integration/ に分離）
- **Dockerfile, Pipfile**: コンテナ化、依存関係管理

**テスト戦略**:

| テスト種別 | 目的 | 依存関係 | 実行速度 | カバレッジ目標 |
|-----------|------|---------|---------|--------------|
| **Unit Tests** | 個別コンポーネントのロジック検証 | 外部依存なし（モック使用） | 高速（< 1秒） | 90%以上 |
| **Integration Tests** | 実サービス間連携検証 | MongoDB, Redis, FastAPI | 中速（数秒） | 80%以上 |

**単体テスト（Unit Tests）の特徴**:
- **外部依存なし**: データベース、外部API、ファイルシステムをすべてモック化
- **高速実行**: 全単体テストが1秒以内に完了
- **独立性**: テスト順序に依存せず、並列実行可能
- **対象**:
  - Pydantic モデルのバリデーション（test_models/）
  - リポジトリの CRUD ロジック（MongoDB モック使用、test_repositories/）
  - サービス層のビジネスロジック（外部API モック、test_services/）
  - ユーティリティ関数（test_utils/）

**統合テスト（Integration Tests）の特徴**:
- **実サービス使用**: 実際の MongoDB、Redis、FastAPI アプリケーション
- **エンドツーエンド検証**: API リクエスト → ビジネスロジック → データベース保存の全フロー
- **データ準備**: test_clean_data.py と test_setup_data.py で初期データ投入
- **対象**:
  - API エンドポイント（認証、同期、ファイル収集等、test_*_api.py）
  - バックグラウンドジョブ（APScheduler 実行、test_background_jobs.py）
  - エンドツーエンドフロー（Edge → Cloud 同期フロー全体、test_end_to_end.py）

**テスト実行例**:
```bash
# 単体テストのみ実行（高速、CI/CDで毎回実行）
pipenv run pytest tests/unit/ -v

# 統合テストのみ実行（MongoDB/Redis が必要）
pipenv run pytest tests/integration/ -v

# 全テスト実行
pipenv run pytest tests/ -v

# カバレッジ測定
pipenv run pytest tests/ --cov=app --cov-report=html
```

**モード切り替え**:
- Cloud Mode / Edge Mode は環境変数 `SYNC_MODE` で切り替え（`cloud` または `edge`）
- Cloud Mode: 同期リクエストの受付、マスタ配信、トランザクション集約
- Edge Mode: 定期ポーリング、マスタ受信、トランザクション送信、予約反映実行

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |

## Next Steps

Phase 0（research.md 生成）に進みます。以下の不明点を調査します：

1. **Dapr Service Invocation の実装パターン**: Master-dataサービス、Journalサービスとの通信方法
2. **P2Pファイル共有の実装方式**: HTTP サーバー機能（エッジ端末間通信）の実装方法
3. **バックグラウンドタスクの実装**: FastAPI での定期実行（ポーリング、予約反映実行）
4. **ファイル圧縮・解凍**: 非同期ファイルI/O、zip圧縮の実装パターン
5. **エッジ端末の動作環境**: Docker コンテナ内での実行想定、ネットワーク構成

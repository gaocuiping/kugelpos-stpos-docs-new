# データモデル設計: アプリケーション更新管理機能

**作成日**: 2025-10-13
**対象仕様**: spec.md, research.md
**バージョン**: 1.0.0

---

## 概要

本ドキュメントは、アプリケーション更新管理機能のMongoDBデータモデル設計を定義する。各エンティティのスキーマ、インデックス、バリデーションルール、状態遷移を含む。

---

## 1. DeviceVersion（デバイスバージョン）

### 概要

各エッジ端末の現在バージョン、目標バージョン、更新状態を管理するエンティティ。バージョンチェック、ダウンロード、適用の進捗状況をトラッキングする。

### MongoDB Collection名

- **クラウド**: `sync_{tenant_id}.device_versions`
- 例: `sync_A1234.device_versions`

### スキーマ定義

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from kugel_common.schemas.base_document_model import BaseDocumentModel

class DeviceVersionDocument(BaseDocumentModel):
    """
    DeviceVersion document model for MongoDB
    Tracks version status and update progress for each edge device
    """
    # Primary identifiers
    edge_id: str = Field(..., description="Unique edge device identifier (e.g., edge-A1234-tokyo-001)")
    device_type: str = Field(..., description="Device type: 'edge' or 'pos'")

    # Version information
    current_version: str = Field(..., description="Currently applied version (e.g., '1.2.2')")
    target_version: Optional[str] = Field(None, description="Target version to apply (e.g., '1.2.3')")
    pending_version: Optional[str] = Field(None, description="Downloaded but not yet applied version")

    # Status tracking
    update_status: str = Field(
        default="none",
        description="Overall update status: none|downloading|pending_apply|applying|completed|failed"
    )
    download_status: str = Field(
        default="not_started",
        description="Download phase status: not_started|in_progress|completed|failed"
    )
    apply_status: str = Field(
        default="not_started",
        description="Apply phase status: not_started|in_progress|completed|failed|rolled_back"
    )

    # Timestamps
    download_completed_at: Optional[datetime] = Field(None, description="Download phase completion timestamp")
    scheduled_apply_at: Optional[datetime] = Field(None, description="Scheduled apply time (ISO 8601)")
    apply_completed_at: Optional[datetime] = Field(None, description="Apply phase completion timestamp")
    last_check_timestamp: Optional[datetime] = Field(None, description="Last version check timestamp")

    # Error tracking
    retry_count: int = Field(default=0, description="Number of retries for current update (max 3)")
    error_message: Optional[str] = Field(None, description="Detailed error message on failure")

    class Settings:
        name = "device_versions"
        indexes = [
            [("edge_id", 1)],  # Unique index
            [("device_type", 1), ("update_status", 1)],  # Query by device type and status
            [("target_version", 1), ("download_status", 1)],  # Query by version and download status
            [("scheduled_apply_at", 1)],  # Query for scheduled applies
            [("last_check_timestamp", -1)],  # Query by last check time
        ]
```

### フィールド詳細

| フィールド名 | 型 | 必須 | デフォルト | 説明 |
|-------------|----|----|----------|------|
| edge_id | string | ✓ | - | エッジ端末の一意識別子（例: `edge-A1234-tokyo-001`） |
| device_type | string | ✓ | - | デバイスタイプ: `edge`（専用Edge端末）または `pos`（POS端末） |
| current_version | string | ✓ | - | 現在適用されているバージョン（例: `1.2.2`） |
| target_version | string | ✗ | null | 適用予定の目標バージョン（例: `1.2.3`） |
| pending_version | string | ✗ | null | ダウンロード済み未適用のバージョン（最新のみ） |
| update_status | string | ✓ | "none" | 更新全体の状態（後述の状態遷移図を参照） |
| download_status | string | ✓ | "not_started" | ダウンロードフェーズの状態 |
| apply_status | string | ✓ | "not_started" | 適用フェーズの状態 |
| download_completed_at | datetime | ✗ | null | ダウンロード完了日時（ISO 8601形式） |
| scheduled_apply_at | datetime | ✗ | null | 適用予定日時（ISO 8601形式） |
| apply_completed_at | datetime | ✗ | null | 適用完了日時（ISO 8601形式） |
| last_check_timestamp | datetime | ✗ | null | 最終バージョンチェック日時（ISO 8601形式） |
| retry_count | integer | ✓ | 0 | 現在の更新における失敗後のリトライ回数（最大3回） |
| error_message | string | ✗ | null | 更新失敗時の詳細エラーメッセージ |

### 状態遷移図

#### update_status（更新全体の状態）

```
none → downloading → pending_apply → applying → completed
                ↓                            ↓
              failed ←─────────────────── failed
```

**状態定義**:
- `none`: 更新なし（現在バージョンで安定稼働）
- `downloading`: ダウンロード中（Phase 1-3）
- `pending_apply`: ダウンロード完了、適用待ち（scheduled_at待機中）
- `applying`: 適用中（Phase 4-9）
- `completed`: 適用完了
- `failed`: ダウンロードまたは適用失敗

#### download_status（ダウンロードフェーズ）

```
not_started → in_progress → completed
                    ↓
                  failed
```

#### apply_status（適用フェーズ）

```
not_started → in_progress → completed
                    ↓
                  failed → rolled_back
```

### インデックス設計

```javascript
// Unique index for device lookup
db.device_versions.createIndex({ "edge_id": 1 }, { unique: true });

// Query by device type and update status (for monitoring)
db.device_versions.createIndex({ "device_type": 1, "update_status": 1 });

// Query by target version and download status (for seed selection)
db.device_versions.createIndex({ "target_version": 1, "download_status": 1 });

// Query for scheduled applies (for apply scheduler)
db.device_versions.createIndex({ "scheduled_apply_at": 1 });

// Query by last check time (for monitoring inactive devices)
db.device_versions.createIndex({ "last_check_timestamp": -1 });
```

### バリデーションルール

```python
from pydantic import validator

class DeviceVersionDocument(BaseDocumentModel):
    # ... (fields omitted)

    @validator("device_type")
    def validate_device_type(cls, v):
        if v not in ["edge", "pos"]:
            raise ValueError("device_type must be 'edge' or 'pos'")
        return v

    @validator("update_status")
    def validate_update_status(cls, v):
        valid_statuses = ["none", "downloading", "pending_apply", "applying", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"update_status must be one of {valid_statuses}")
        return v

    @validator("download_status")
    def validate_download_status(cls, v):
        valid_statuses = ["not_started", "in_progress", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"download_status must be one of {valid_statuses}")
        return v

    @validator("apply_status")
    def validate_apply_status(cls, v):
        valid_statuses = ["not_started", "in_progress", "completed", "failed", "rolled_back"]
        if v not in valid_statuses:
            raise ValueError(f"apply_status must be one of {valid_statuses}")
        return v

    @validator("retry_count")
    def validate_retry_count(cls, v):
        if v < 0 or v > 3:
            raise ValueError("retry_count must be between 0 and 3")
        return v
```

### サンプルドキュメント

```json
{
  "_id": "67890abcdef12345",
  "edge_id": "edge-A1234-tokyo-001",
  "device_type": "edge",
  "current_version": "1.2.2",
  "target_version": "1.2.3",
  "pending_version": "1.2.3",
  "update_status": "pending_apply",
  "download_status": "completed",
  "apply_status": "not_started",
  "download_completed_at": "2025-01-17T14:35:00Z",
  "scheduled_apply_at": "2025-01-18T02:00:00Z",
  "apply_completed_at": null,
  "last_check_timestamp": "2025-01-17T14:30:00Z",
  "retry_count": 0,
  "error_message": null,
  "created_at": "2025-01-17T14:00:00Z",
  "updated_at": "2025-01-17T14:35:00Z"
}
```

---

## 2. UpdateHistory（更新履歴）

### 概要

各エッジ端末の更新履歴を記録するエンティティ。監査とトラブルシューティングに使用。更新の開始・終了時刻、成功/失敗、ダウンタイムを記録。

### MongoDB Collection名

- **クラウド**: `sync_{tenant_id}.update_histories`
- 例: `sync_A1234.update_histories`

### スキーマ定義

```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from kugel_common.schemas.base_document_model import BaseDocumentModel

class ArtifactUpdateResult(BaseModel):
    """Individual artifact update result"""
    artifact_type: str = Field(..., description="Artifact type: script|module|config|image|document")
    artifact_name: str = Field(..., description="Artifact name (e.g., pos-startup.sh)")
    version: str = Field(..., description="Version applied")
    status: str = Field(..., description="Status: success|failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class UpdateHistoryDocument(BaseDocumentModel):
    """
    UpdateHistory document model for MongoDB
    Records complete history of all update operations
    """
    # Identifiers
    update_id: str = Field(..., description="Unique update operation ID (UUID)")
    edge_id: str = Field(..., description="Target edge device ID")
    device_type: str = Field(..., description="Device type: 'edge' or 'pos'")

    # Version information
    from_version: str = Field(..., description="Version before update (e.g., '1.2.2')")
    to_version: str = Field(..., description="Version after update (e.g., '1.2.3')")

    # Timing
    start_time: datetime = Field(..., description="Update start timestamp (ISO 8601)")
    end_time: Optional[datetime] = Field(None, description="Update end timestamp (ISO 8601)")
    downtime_seconds: Optional[int] = Field(None, description="Service downtime duration (Phase 6-8)")

    # Status
    status: str = Field(..., description="Update result: success|failed")
    error_message: Optional[str] = Field(None, description="Detailed error message on failure")
    rollback_performed: bool = Field(default=False, description="Whether automatic rollback was performed")

    # Artifact details
    artifacts_count: int = Field(default=0, description="Total number of downloaded artifacts")
    total_size_bytes: int = Field(default=0, description="Total download size in bytes")
    update_results: List[ArtifactUpdateResult] = Field(
        default_factory=list,
        description="Individual artifact update results"
    )

    class Settings:
        name = "update_histories"
        indexes = [
            [("update_id", 1)],  # Unique index
            [("edge_id", 1), ("start_time", -1)],  # Query device history by time
            [("status", 1), ("start_time", -1)],  # Query by status
            [("to_version", 1), ("start_time", -1)],  # Query by version
        ]
```

### フィールド詳細

| フィールド名 | 型 | 必須 | デフォルト | 説明 |
|-------------|----|----|----------|------|
| update_id | string | ✓ | - | 更新操作の一意識別子（UUID） |
| edge_id | string | ✓ | - | 更新対象のエッジ端末ID |
| device_type | string | ✓ | - | デバイスタイプ: `edge` または `pos` |
| from_version | string | ✓ | - | 更新前のバージョン（例: `1.2.2`） |
| to_version | string | ✓ | - | 更新後のバージョン（例: `1.2.3`） |
| start_time | datetime | ✓ | - | 更新処理の開始日時（ISO 8601形式） |
| end_time | datetime | ✗ | null | 更新処理の終了日時（ISO 8601形式） |
| downtime_seconds | integer | ✗ | null | サービス停止時間（Phase 6開始からPhase 8完了まで、秒単位） |
| status | string | ✓ | - | 更新結果: `success`（成功）または `failed`（失敗） |
| error_message | string | ✗ | null | 失敗時の詳細エラーメッセージ |
| rollback_performed | boolean | ✓ | false | 自動ロールバックが実行されたかどうか |
| artifacts_count | integer | ✓ | 0 | ダウンロードしたファイル・イメージの総数 |
| total_size_bytes | integer | ✓ | 0 | ダウンロードした総データサイズ（バイト単位） |
| update_results | array | ✓ | [] | 個別アーティファクトの更新結果リスト |

### インデックス設計

```javascript
// Unique index for update operation lookup
db.update_histories.createIndex({ "update_id": 1 }, { unique: true });

// Query device history ordered by time (most recent first)
db.update_histories.createIndex({ "edge_id": 1, "start_time": -1 });

// Query by status (for failure analysis)
db.update_histories.createIndex({ "status": 1, "start_time": -1 });

// Query by version (for version rollout tracking)
db.update_histories.createIndex({ "to_version": 1, "start_time": -1 });
```

### バリデーションルール

```python
from pydantic import validator

class UpdateHistoryDocument(BaseDocumentModel):
    # ... (fields omitted)

    @validator("status")
    def validate_status(cls, v):
        if v not in ["success", "failed"]:
            raise ValueError("status must be 'success' or 'failed'")
        return v

    @validator("downtime_seconds")
    def validate_downtime_seconds(cls, v):
        if v is not None and v < 0:
            raise ValueError("downtime_seconds must be non-negative")
        return v

    @validator("artifacts_count")
    def validate_artifacts_count(cls, v):
        if v < 0:
            raise ValueError("artifacts_count must be non-negative")
        return v

    @validator("total_size_bytes")
    def validate_total_size_bytes(cls, v):
        if v < 0:
            raise ValueError("total_size_bytes must be non-negative")
        return v
```

### サンプルドキュメント

```json
{
  "_id": "abcdef123456",
  "update_id": "550e8400-e29b-41d4-a716-446655440000",
  "edge_id": "edge-A1234-tokyo-001",
  "device_type": "edge",
  "from_version": "1.2.2",
  "to_version": "1.2.3",
  "start_time": "2025-01-18T02:00:00Z",
  "end_time": "2025-01-18T02:03:30Z",
  "downtime_seconds": 90,
  "status": "success",
  "error_message": null,
  "rollback_performed": false,
  "artifacts_count": 15,
  "total_size_bytes": 524288000,
  "update_results": [
    {
      "artifact_type": "script",
      "artifact_name": "edge-startup.sh",
      "version": "1.2.3",
      "status": "success",
      "error_message": null
    },
    {
      "artifact_type": "module",
      "artifact_name": "kugelpos_common-1.2.3-py3-none-any.whl",
      "version": "1.2.3",
      "status": "success",
      "error_message": null
    }
  ],
  "created_at": "2025-01-18T02:00:00Z",
  "updated_at": "2025-01-18T02:03:30Z"
}
```

---

## 3. EdgeTerminal（エッジ端末）

### 概要

各エッジ端末の基本情報、P2P設定、認証情報を管理するエンティティ。デバイス登録、認証、P2P優先度制御に使用。

### MongoDB Collection名

- **クラウド**: `sync_{tenant_id}.edge_terminals`
- 例: `sync_A1234.edge_terminals`

### スキーマ定義

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from kugel_common.schemas.base_document_model import BaseDocumentModel

class EdgeTerminalDocument(BaseDocumentModel):
    """
    EdgeTerminal document model for MongoDB
    Stores device registration, P2P configuration, and authentication info
    """
    # Primary identifiers
    edge_id: str = Field(
        ...,
        description="Unique edge device identifier (format: edge-<tenant_id>-<store_code>-<seq>)"
    )
    tenant_id: str = Field(..., description="Tenant identifier for multi-tenancy isolation")
    store_code: str = Field(..., description="Store identifier")

    # Device information
    device_type: str = Field(..., description="Device type: 'edge' or 'pos'")
    device_name: Optional[str] = Field(None, description="Human-readable device name")

    # P2P configuration
    is_p2p_seed: bool = Field(default=False, description="Whether device acts as P2P seed")
    p2p_priority: int = Field(
        default=99,
        description="P2P priority: 0=primary seed, 1-9=secondary seeds, 99=non-seed"
    )
    p2p_registry_url: Optional[str] = Field(None, description="Harbor registry URL (for seeds)")
    p2p_sync_api_url: Optional[str] = Field(None, description="Edge Sync Service API URL (for seeds)")

    # Authentication
    secret_hash: str = Field(..., description="SHA256 hashed secret for JWT authentication")

    # Status
    is_active: bool = Field(default=True, description="Whether device is active")
    last_seen_at: Optional[datetime] = Field(None, description="Last version check timestamp")

    class Settings:
        name = "edge_terminals"
        indexes = [
            [("edge_id", 1)],  # Unique index
            [("tenant_id", 1), ("store_code", 1)],  # Query by tenant and store
            [("is_p2p_seed", 1), ("p2p_priority", 1)],  # Query seeds by priority
            [("is_active", 1), ("last_seen_at", -1)],  # Query active devices
        ]
```

### フィールド詳細

| フィールド名 | 型 | 必須 | デフォルト | 説明 |
|-------------|----|----|----------|------|
| edge_id | string | ✓ | - | エッジ端末の一意識別子（形式: `edge-<tenant_id>-<store_code>-<連番>`） |
| tenant_id | string | ✓ | - | 所属テナントの識別子（マルチテナント分離用） |
| store_code | string | ✓ | - | 所属店舗の識別子 |
| device_type | string | ✓ | - | デバイスタイプ: `edge`（専用Edge端末）または `pos`（POS端末） |
| device_name | string | ✗ | null | 人間が読める形式のデバイス名 |
| is_p2p_seed | boolean | ✓ | false | P2Pシード端末かどうか（`true`: シード端末、`false`: 非シード端末） |
| p2p_priority | integer | ✓ | 99 | P2Pアクセス時の優先順位（0=最優先、1-9=セカンダリシード、99=非シード） |
| p2p_registry_url | string | ✗ | null | Harbor レジストリURL（シード端末のみ） |
| p2p_sync_api_url | string | ✗ | null | Edge Sync Service API URL（シード端末のみ） |
| secret_hash | string | ✓ | - | JWT認証用のシークレット（SHA256ハッシュ化） |
| is_active | boolean | ✓ | true | デバイスがアクティブかどうか |
| last_seen_at | datetime | ✗ | null | 最終バージョンチェック日時 |

### インデックス設計

```javascript
// Unique index for device lookup
db.edge_terminals.createIndex({ "edge_id": 1 }, { unique: true });

// Query by tenant and store (for store-level operations)
db.edge_terminals.createIndex({ "tenant_id": 1, "store_code": 1 });

// Query P2P seeds by priority (for seed selection)
db.edge_terminals.createIndex({ "is_p2p_seed": 1, "p2p_priority": 1 });

// Query active devices (for monitoring)
db.edge_terminals.createIndex({ "is_active": 1, "last_seen_at": -1 });
```

### バリデーションルール

```python
from pydantic import validator

class EdgeTerminalDocument(BaseDocumentModel):
    # ... (fields omitted)

    @validator("edge_id")
    def validate_edge_id(cls, v):
        if not v.startswith("edge-"):
            raise ValueError("edge_id must start with 'edge-'")
        return v

    @validator("device_type")
    def validate_device_type(cls, v):
        if v not in ["edge", "pos"]:
            raise ValueError("device_type must be 'edge' or 'pos'")
        return v

    @validator("p2p_priority")
    def validate_p2p_priority(cls, v):
        if v < 0 or v > 99:
            raise ValueError("p2p_priority must be between 0 and 99")
        return v

    @validator("p2p_registry_url")
    def validate_p2p_registry_url(cls, v, values):
        if values.get("is_p2p_seed") and not v:
            raise ValueError("p2p_registry_url is required for P2P seed devices")
        return v

    @validator("p2p_sync_api_url")
    def validate_p2p_sync_api_url(cls, v, values):
        if values.get("is_p2p_seed") and not v:
            raise ValueError("p2p_sync_api_url is required for P2P seed devices")
        return v
```

### サンプルドキュメント

```json
{
  "_id": "123456789abc",
  "edge_id": "edge-A1234-tokyo-001",
  "tenant_id": "A1234",
  "store_code": "tokyo",
  "device_type": "edge",
  "device_name": "Tokyo Store Edge Server",
  "is_p2p_seed": true,
  "p2p_priority": 0,
  "p2p_registry_url": "edge-tokyo-001:5000",
  "p2p_sync_api_url": "http://192.168.1.10:8007",
  "secret_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "is_active": true,
  "last_seen_at": "2025-01-17T14:30:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-17T14:30:00Z"
}
```

---

## 4. Manifest（更新マニフェスト）

### 概要

エッジ端末に配信される更新内容を定義するエンティティ。クラウドからエッジ端末へのバージョンチェックレスポンスとして返却される。MongoDBには保存されず、API応答として動的に生成される。

### データ構造（Pydantic Schema）

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class ArtifactItem(BaseModel):
    """Individual artifact in the manifest"""
    type: str = Field(..., description="Artifact type: script|module|config|image|document")
    name: str = Field(..., description="Artifact filename")
    version: str = Field(..., description="Artifact version")
    primary_url: str = Field(..., description="Primary download URL (cloud or P2P)")
    fallback_url: str = Field(..., description="Fallback download URL (cloud)")
    checksum: str = Field(..., description="SHA256 checksum")
    size: int = Field(..., description="File size in bytes")
    destination: str = Field(..., description="Destination path on edge device")
    permissions: Optional[str] = Field(None, description="File permissions (e.g., '755')")

class ContainerImageItem(BaseModel):
    """Individual container image in the manifest"""
    service: str = Field(..., description="Service name (account|terminal|cart|...)")
    version: str = Field(..., description="Image version")
    primary_registry: str = Field(..., description="Primary registry URL")
    primary_image: str = Field(..., description="Primary image name with tag")
    fallback_registry: str = Field(..., description="Fallback registry URL")
    fallback_image: str = Field(..., description="Fallback image name with tag")
    checksum: str = Field(..., description="Image digest (SHA256)")

class AvailableSeed(BaseModel):
    """P2P seed device information"""
    edge_id: str = Field(..., description="Seed device ID")
    priority: int = Field(..., description="Seed priority (0-9)")
    url: str = Field(..., description="Edge Sync Service API URL")

class ApplySchedule(BaseModel):
    """Apply phase schedule information"""
    scheduled_at: datetime = Field(..., description="Apply start time (ISO 8601)")
    maintenance_window: int = Field(..., description="Maintenance window duration in minutes")

class Manifest(BaseModel):
    """
    Update manifest returned to edge devices
    Dynamically generated per device based on current state
    """
    manifest_version: str = Field(default="1.0", description="Manifest format version")
    device_type: str = Field(..., description="Target device type: edge|pos")
    device_id: str = Field(..., description="Target device ID (edge_id)")
    target_version: str = Field(..., description="Target version to apply")

    artifacts: List[ArtifactItem] = Field(
        default_factory=list,
        description="List of files to download"
    )
    container_images: List[ContainerImageItem] = Field(
        default_factory=list,
        description="List of container images to download"
    )
    available_seeds: List[AvailableSeed] = Field(
        default_factory=list,
        description="List of available P2P seed devices"
    )
    apply_schedule: ApplySchedule = Field(..., description="Apply phase schedule")
```

### サンプルマニフェスト

```json
{
  "manifest_version": "1.0",
  "device_type": "pos",
  "device_id": "edge-A1234-tokyo-002",
  "target_version": "1.2.3",
  "artifacts": [
    {
      "type": "script",
      "name": "pos-startup.sh",
      "version": "1.2.3",
      "primary_url": "http://192.168.1.10:8007/api/v1/artifacts/pos-startup.sh?version=1.2.3",
      "fallback_url": "https://sync.kugelpos.cloud/api/v1/artifacts/pos-startup.sh?version=1.2.3",
      "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "size": 15360,
      "destination": "/opt/kugelpos/pos-startup.sh",
      "permissions": "755"
    },
    {
      "type": "module",
      "name": "kugelpos_common-1.2.3-py3-none-any.whl",
      "version": "1.2.3",
      "primary_url": "http://192.168.1.10:8007/api/v1/artifacts/kugelpos_common-1.2.3-py3-none-any.whl?version=1.2.3",
      "fallback_url": "https://sync.kugelpos.cloud/api/v1/artifacts/kugelpos_common-1.2.3-py3-none-any.whl?version=1.2.3",
      "checksum": "abc123...",
      "size": 2097152,
      "destination": "/opt/kugelpos/modules/kugelpos_common-1.2.3-py3-none-any.whl",
      "permissions": null
    }
  ],
  "container_images": [
    {
      "service": "cart",
      "version": "1.2.3",
      "primary_registry": "edge-tokyo-001:5000",
      "primary_image": "cart:1.2.3",
      "fallback_registry": "masakugel.azurecr.io",
      "fallback_image": "production/services/cart:1.2.3",
      "checksum": "sha256:def456..."
    }
  ],
  "available_seeds": [
    {
      "edge_id": "edge-A1234-tokyo-001",
      "priority": 0,
      "url": "http://192.168.1.10:8007"
    }
  ],
  "apply_schedule": {
    "scheduled_at": "2025-01-18T02:00:00Z",
    "maintenance_window": 30
  }
}
```

---

## 5. PendingUpdate（ダウンロード済み未適用更新）

### 概要

ダウンロード完了後、適用待ち状態のバージョンを管理するエンティティ。エッジ端末のローカルファイルシステムに保存される（MongoDBには保存されない）。

### ファイルパス

- **保存先**: `/opt/kugelpos/pending-updates/{version}/`
- **ファイル名**: `status.json`

### データ構造

```python
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class PendingUpdate(BaseModel):
    """
    PendingUpdate stored locally on edge device
    Tracks downloaded but not yet applied version
    """
    version: str = Field(..., description="Downloaded version (e.g., '1.2.3')")
    download_status: str = Field(
        ...,
        description="Download status: in_progress|completed|failed"
    )
    download_started_at: datetime = Field(..., description="Download start time (ISO 8601)")
    download_completed_at: Optional[datetime] = Field(None, description="Download completion time")

    verification_status: str = Field(
        default="not_started",
        description="Checksum verification status: not_started|in_progress|passed|failed"
    )
    ready_to_apply: bool = Field(default=False, description="Whether ready to apply")

    artifacts_count: int = Field(default=0, description="Number of downloaded artifacts")
    total_size_bytes: int = Field(default=0, description="Total download size in bytes")

    manifest_json: Dict[str, Any] = Field(..., description="Complete manifest JSON")
    status_json: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed status information (file-level progress, errors)"
    )
```

### サンプル status.json

```json
{
  "version": "1.2.3",
  "download_status": "completed",
  "download_started_at": "2025-01-17T14:30:00Z",
  "download_completed_at": "2025-01-17T14:35:00Z",
  "verification_status": "passed",
  "ready_to_apply": true,
  "artifacts_count": 15,
  "total_size_bytes": 524288000,
  "manifest_json": {
    "manifest_version": "1.0",
    "device_type": "pos",
    "target_version": "1.2.3",
    "artifacts": [
      {
        "type": "script",
        "name": "pos-startup.sh",
        "checksum": "e3b0c442...",
        "size": 15360
      }
    ],
    "apply_schedule": {
      "scheduled_at": "2025-01-18T02:00:00Z",
      "maintenance_window": 30
    }
  },
  "status_json": {
    "artifacts": [
      {
        "name": "pos-startup.sh",
        "status": "completed",
        "downloaded_bytes": 15360,
        "checksum_verified": true
      }
    ]
  }
}
```

---

## リレーションシップ図

```
┌─────────────────────┐
│ EdgeTerminal        │
│ (端末マスター)        │
│ - edge_id (PK)      │
│ - is_p2p_seed       │
│ - p2p_priority      │
└──────────┬──────────┘
           │ 1:1
           ↓
┌─────────────────────┐
│ DeviceVersion       │
│ (バージョン状態)      │
│ - edge_id (PK, FK)  │
│ - current_version   │
│ - target_version    │
└──────────┬──────────┘
           │ 1:N
           ↓
┌─────────────────────┐
│ UpdateHistory       │
│ (更新履歴)           │
│ - update_id (PK)    │
│ - edge_id (FK)      │
│ - from_version      │
│ - to_version        │
└─────────────────────┘

          ↓ API Response
┌─────────────────────┐
│ Manifest            │
│ (動的生成)           │
│ - target_version    │
│ - artifacts[]       │
│ - available_seeds[] │
└──────────┬──────────┘
           │ Download
           ↓
┌─────────────────────┐
│ PendingUpdate       │
│ (ローカルファイル)    │
│ - status.json       │
│ - manifest.json     │
└─────────────────────┘
```

---

## クエリパターンと最適化

### 1. バージョンチェック時のクエリ

**目的**: デバイスの現在状態を取得し、更新が必要か判定

```python
# Query device version by edge_id
device_version = await device_version_repo.find_one({"edge_id": edge_id})

# Index used: { "edge_id": 1 } (unique)
```

### 2. P2Pシード端末の選択

**目的**: ダウンロード完了済みのシード端末を優先度順に取得

```python
# Query seeds with download completed for target version
seeds = await device_version_repo.find({
    "target_version": target_version,
    "download_status": "completed",
    "device_type": "edge",  # or query edge_terminals for is_p2p_seed=true
})

# Order by p2p_priority (from edge_terminals)
seeds_sorted = await edge_terminal_repo.find(
    {"edge_id": {"$in": [s.edge_id for s in seeds]}, "is_p2p_seed": True},
    sort=[("p2p_priority", 1)]  # Ascending order (0 first)
)

# Index used: { "is_p2p_seed": 1, "p2p_priority": 1 }
```

### 3. 適用予定デバイスの取得

**目的**: scheduled_at時刻に到達したデバイスを取得して適用を実行

```python
from datetime import datetime, timezone

# Query devices ready to apply
now = datetime.now(timezone.utc)
devices_to_apply = await device_version_repo.find({
    "update_status": "pending_apply",
    "scheduled_apply_at": {"$lte": now}
})

# Index used: { "scheduled_apply_at": 1 }
```

### 4. 更新履歴の取得

**目的**: 特定デバイスの更新履歴を最新順に取得

```python
# Query update history for a device
history = await update_history_repo.find(
    {"edge_id": edge_id},
    sort=[("start_time", -1)],  # Descending order (most recent first)
    limit=10
)

# Index used: { "edge_id": 1, "start_time": -1 }
```

### 5. 失敗した更新の集計

**目的**: 特定バージョンの展開で失敗したデバイスを集計

```python
# Count failed updates for a version
failed_count = await update_history_repo.count_documents({
    "to_version": target_version,
    "status": "failed"
})

# Group by error_message
failed_breakdown = await update_history_repo.aggregate([
    {"$match": {"to_version": target_version, "status": "failed"}},
    {"$group": {"_id": "$error_message", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
])

# Index used: { "to_version": 1, "start_time": -1 }
```

---

## データライフサイクル管理

### 1. UpdateHistory（更新履歴）の保持期間

**方針**: 90日間保持後、古い履歴を自動削除

```python
from datetime import datetime, timedelta

# MongoDB TTL Index (Time To Live)
await update_history_collection.create_index(
    "created_at",
    expireAfterSeconds=7776000  # 90 days in seconds
)
```

### 2. PendingUpdate（ダウンロード済み未適用）の保持期間

**方針**: 7日間未適用のファイルは自動削除（ディスク容量節約）

```bash
#!/bin/bash
# /opt/kugelpos/scripts/cleanup_pending_updates.sh

PENDING_DIR="/opt/kugelpos/pending-updates"
MAX_AGE_DAYS=7

find "$PENDING_DIR" -maxdepth 1 -type d -mtime +$MAX_AGE_DAYS -exec rm -rf {} \;
```

**Cron設定**:
```cron
0 3 * * * /opt/kugelpos/scripts/cleanup_pending_updates.sh
```

### 3. DeviceVersion（デバイスバージョン）のクリーンアップ

**方針**: 非アクティブデバイス（30日以上未チェック）を論理削除

```python
from datetime import datetime, timedelta, timezone

# Mark inactive devices
inactive_threshold = datetime.now(timezone.utc) - timedelta(days=30)

await edge_terminal_repo.update_many(
    {"last_seen_at": {"$lt": inactive_threshold}, "is_active": True},
    {"$set": {"is_active": False}}
)
```

---

## まとめ

### 設計の重要ポイント

1. **テナント分離**: すべてのコレクションは `sync_{tenant_id}` データベースに格納され、テナント間のデータ完全分離を保証
2. **インデックス最適化**: 頻繁なクエリパターン（edge_id検索、優先度順ソート、時系列検索）に最適化されたインデックス設計
3. **状態管理**: DeviceVersionで明確な状態遷移を定義し、不正な状態遷移を防止
4. **監査性**: UpdateHistoryで全更新操作を記録し、トラブルシューティングとコンプライアンスを支援
5. **スケーラビリティ**: 各エンティティは独立してスケール可能、P2P優先度制御により1000台規模に対応

### 次のステップ

- **API契約設計** (contracts/): 本データモデルを基にRESTful APIエンドポイントを設計
- **Repository実装**: AbstractRepositoryパターンを継承し、各エンティティのCRUD操作を実装
- **テスト実装**: TDD原則に従い、各エンティティのバリデーション、状態遷移、クエリ最適化をテスト

---

**作成日**: 2025-10-13
**作成者**: Claude Code (Data Model Designer)
**承認**: 未承認

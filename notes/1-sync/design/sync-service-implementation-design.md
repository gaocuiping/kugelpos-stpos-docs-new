# Sync Service 実装デザイン

## 1. 概要

### 1.1 目的
本ドキュメントは、sync-service-requirements.mdに記載された要件を満たすSync Serviceの実装デザインを定義する。

### 1.2 設計方針
- 既存のKugelposアーキテクチャパターンに準拠
- FastAPIベースのRESTful API
- Mongoデータベースによるデータ永続化
- Daprを活用したサービス間通信
- エッジ・クラウド間の効率的な差分同期

## 2. サービスアーキテクチャ

### 2.1 モード設計

#### 2.1.1 Cloud Mode
```python
# クラウドモードの責務
- エッジ端末の認証・管理
- 同期リクエストの受信と処理
- マスターデータの配信
- トランザクションデータの収集
- 同期状態の一元管理
- 同期履歴の記録
```

#### 2.1.2 Edge Mode
```python
# エッジモードの責務
- クラウドへの定期ポーリング
- 差分データの取得と適用
- ローカルデータの収集と送信
- オフライン時のキューイング
- 同期結果のレポート
```

### 2.2 ディレクトリ構造

```
services/sync/
├── app/
│   ├── main.py                          # FastAPIアプリケーション初期化
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py                  # 認証エンドポイント
│   │       ├── sync.py                  # 同期エンドポイント
│   │       ├── status.py                # ステータス管理エンドポイント
│   │       ├── schemas.py               # APIスキーマ定義
│   │       └── schemas_transformer.py   # スキーマ変換
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # 環境設定
│   │   └── settings_database.py         # DB設定
│   ├── core/
│   │   ├── __init__.py
│   │   ├── sync_orchestrator.py         # 同期処理オーケストレータ
│   │   ├── cloud_sync_engine.py         # クラウド側同期エンジン
│   │   ├── edge_sync_engine.py          # エッジ側同期エンジン
│   │   ├── data_collector.py            # データ収集モジュール
│   │   └── data_applier.py              # データ適用モジュール
│   ├── database/
│   │   ├── __init__.py
│   │   └── database_setup.py            # DB初期化
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── get_sync_service.py          # サービス依存性注入
│   │   └── auth.py                      # 認証依存性
│   ├── exceptions/
│   │   ├── __init__.py
│   │   ├── sync_error_codes.py          # エラーコード定義
│   │   └── sync_exceptions.py           # カスタム例外
│   ├── models/
│   │   ├── __init__.py
│   │   ├── documents/
│   │   │   ├── __init__.py
│   │   │   ├── sync_status_document.py      # 同期状態ドキュメント
│   │   │   ├── sync_history_document.py     # 同期履歴ドキュメント
│   │   │   ├── sync_request_document.py     # 同期リクエストドキュメント
│   │   │   ├── edge_device_document.py      # エッジ端末ドキュメント
│   │   │   └── sync_queue_document.py       # 同期キュードキュメント
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── sync_status_repository.py    # 同期状態リポジトリ
│   │       ├── sync_history_repository.py   # 同期履歴リポジトリ
│   │       ├── edge_device_repository.py    # エッジ端末リポジトリ
│   │       └── sync_queue_repository.py     # 同期キューリポジトリ
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py              # 認証サービス
│   │   ├── sync_service.py              # 同期サービス
│   │   ├── data_services/
│   │   │   ├── __init__.py
│   │   │   ├── master_data_service.py   # マスターデータ同期
│   │   │   ├── transaction_service.py   # トランザクション同期
│   │   │   ├── journal_service.py       # ジャーナル同期
│   │   │   └── log_service.py          # ログ同期
│   │   └── strategies/
│   │       ├── __init__.py
│   │       ├── differential_sync.py     # 差分同期戦略
│   │       └── bulk_sync.py            # 一括同期戦略
│   └── utils/
│       ├── __init__.py
│       ├── compression.py               # データ圧縮ユーティリティ
│       ├── encryption.py                # 暗号化ユーティリティ
│       ├── retry_handler.py             # リトライハンドラ
│       ├── queue_manager.py             # キュー管理
│       └── dapr_client_helper.py        # Daprクライアント
├── tests/
├── logging.conf
├── Pipfile
├── Pipfile.lock
├── Dockerfile
├── run.py
├── run_all_tests.sh
├── .env.sample
└── README.md
```

## 3. データモデル設計

### 3.1 MongoDB Collection設計

#### 3.1.1 edge_devices Collection
```python
from datetime import datetime
from typing import Optional
from pydantic import Field
from kugel_common.models.documents.base_document import BaseDocumentModel

class EdgeDeviceDocument(BaseDocumentModel):
    """エッジ端末管理ドキュメント"""

    # 識別情報
    edge_id: str = Field(description="エッジ端末ID（テナント内で一意）")
    tenant_id: str = Field(description="テナントID")
    store_code: str = Field(description="店舗コード")

    # 認証情報
    secret_hash: str = Field(description="パスワードのbcryptハッシュ")

    # ステータス情報
    status: str = Field(default="active", description="端末状態: active|inactive|suspended")
    description: Optional[str] = Field(None, description="端末の説明")

    # 時刻情報
    last_authenticated: Optional[datetime] = Field(None, description="最終認証時刻")
    last_sync: Optional[datetime] = Field(None, description="最終同期時刻")
    registered_at: datetime = Field(default_factory=datetime.utcnow, description="登録日時")

    # メタ情報
    edge_version: Optional[str] = Field(None, description="エッジアプリバージョン")
    ip_address: Optional[str] = Field(None, description="エッジのIPアドレス")

    class Config:
        collection = "edge_devices"
        indexes = [
            {"keys": [("tenant_id", 1), ("edge_id", 1)], "unique": True},
            {"keys": [("tenant_id", 1), ("store_code", 1)]},
            {"keys": [("status", 1)]},
        ]
```

#### 3.1.2 sync_status Collection
```python
from datetime import datetime
from typing import Optional
from pydantic import Field
from kugel_common.models.documents.base_document import BaseDocumentModel

class SyncStatusDocument(BaseDocumentModel):
    """同期状態管理ドキュメント"""

    # 識別情報
    edge_id: str = Field(description="エッジ端末ID")
    data_type: str = Field(description="データ種別: master_data|tran_log|journal|log_application等")

    # 同期状態
    last_sync_timestamp: datetime = Field(description="最終同期時刻")
    sync_type: str = Field(default="differential", description="同期タイプ: differential|bulk")
    status: str = Field(default="idle", description="状態: idle|syncing|completed|failed")

    # エラー情報
    retry_count: int = Field(default=0, description="リトライ回数")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")

    # 統計情報
    last_record_count: Optional[int] = Field(None, description="最終同期レコード数")
    last_data_size_bytes: Optional[int] = Field(None, description="最終同期データサイズ")
    total_synced_records: int = Field(default=0, description="累計同期レコード数")

    class Config:
        collection = "sync_status"
        indexes = [
            {"keys": [("edge_id", 1), ("data_type", 1)], "unique": True},
            {"keys": [("status", 1)]},
            {"keys": [("last_sync_timestamp", -1)]},
        ]
```

#### 3.1.3 sync_history Collection
```python
from datetime import datetime
from typing import Optional
from pydantic import Field
from kugel_common.models.documents.base_document import BaseDocumentModel

class SyncHistoryDocument(BaseDocumentModel):
    """同期履歴ドキュメント"""

    # 識別情報
    sync_id: str = Field(description="同期処理ID (SYNC_{tenant_id}_{edge_id}_{ulid})")
    edge_id: str = Field(description="エッジ端末ID")
    data_type: str = Field(description="データ種別")

    # 同期情報
    sync_type: str = Field(description="同期タイプ: differential|bulk")
    sync_direction: str = Field(description="同期方向: cloud-to-edge|edge-to-cloud")

    # タイミング情報
    start_time: datetime = Field(description="開始時刻")
    end_time: Optional[datetime] = Field(None, description="終了時刻")
    processing_time_ms: Optional[int] = Field(None, description="処理時間（ミリ秒）")

    # 統計情報
    record_count: int = Field(default=0, description="レコード数")
    data_size_bytes: int = Field(default=0, description="データサイズ（バイト）")

    # 結果情報
    status: str = Field(description="結果: success|partial|failed")
    error_details: Optional[str] = Field(None, description="エラー詳細")
    retry_count: int = Field(default=0, description="リトライ回数")

    # データ範囲（差分同期用）
    from_timestamp: Optional[datetime] = Field(None, description="同期開始タイムスタンプ")
    to_timestamp: Optional[datetime] = Field(None, description="同期終了タイムスタンプ")

    class Config:
        collection = "sync_history"
        indexes = [
            {"keys": [("sync_id", 1)], "unique": True},
            {"keys": [("edge_id", 1), ("start_time", -1)]},
            {"keys": [("data_type", 1), ("start_time", -1)]},
            {"keys": [("status", 1)]},
        ]
```

#### 3.1.4 sync_queue Collection（エッジ側のみ）
```python
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field
from kugel_common.models.documents.base_document import BaseDocumentModel

class SyncQueueDocument(BaseDocumentModel):
    """同期キュードキュメント（オフライン時のデータ保存用）"""

    # 識別情報
    queue_id: str = Field(description="キューID")
    data_type: str = Field(description="データ種別")

    # データ情報
    operation: str = Field(description="操作種別: create|update|delete")
    data: Dict[str, Any] = Field(description="同期対象データ")

    # 状態情報
    status: str = Field(default="pending", description="状態: pending|processing|completed|failed")
    retry_count: int = Field(default=0, description="リトライ回数")
    error_message: Optional[str] = Field(None, description="エラーメッセージ")

    # タイミング情報
    queued_at: datetime = Field(default_factory=datetime.utcnow, description="キュー登録時刻")
    processed_at: Optional[datetime] = Field(None, description="処理時刻")

    class Config:
        collection = "sync_queue"
        indexes = [
            {"keys": [("status", 1), ("queued_at", 1)]},
            {"keys": [("data_type", 1), ("status", 1)]},
        ]
```

## 4. API実装デザイン

### 4.1 認証API

#### 4.1.1 エッジ端末認証
```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.schemas import (
    EdgeAuthRequest,
    EdgeAuthResponse,
    ApiResponse
)
from app.services.auth_service import AuthService
from app.dependencies.get_sync_service import get_auth_service

router = APIRouter(prefix="/sync", tags=["sync-auth"])

@router.post("/auth", response_model=ApiResponse[EdgeAuthResponse])
async def authenticate_edge(
    request: EdgeAuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse[EdgeAuthResponse]:
    """
    エッジ端末の認証

    - tenant_id, edge_id, secretで認証
    - JWTトークンを発行
    """
    try:
        token_data = await auth_service.authenticate_edge(
            tenant_id=request.tenant_id,
            edge_id=request.edge_id,
            secret=request.secret
        )

        return ApiResponse[EdgeAuthResponse](
            success=True,
            data=EdgeAuthResponse(**token_data)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
```

### 4.2 同期API

#### 4.2.1 同期リクエスト受信（Cloud Mode）
```python
# app/api/v1/sync.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.v1.schemas import (
    SyncRequest,
    SyncResponse,
    ApiResponse
)
from app.core.sync_orchestrator import SyncOrchestrator
from app.dependencies.auth import get_current_edge_device
from app.models.documents.edge_device_document import EdgeDeviceDocument

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/pull", response_model=ApiResponse[SyncResponse])
async def pull_data(
    request: SyncRequest,
    edge_device: EdgeDeviceDocument = Depends(get_current_edge_device),
    sync_orchestrator: SyncOrchestrator = Depends(get_sync_orchestrator)
) -> ApiResponse[SyncResponse]:
    """
    エッジからのデータ取得リクエスト（Pull）

    - 差分データまたは一括データを返す
    - データは圧縮して送信
    """
    result = await sync_orchestrator.process_pull_request(
        edge_id=edge_device.edge_id,
        data_type=request.data_type,
        last_sync_timestamp=request.last_sync_timestamp,
        sync_type=request.sync_type
    )

    return ApiResponse[SyncResponse](
        success=True,
        data=result
    )

@router.post("/push", response_model=ApiResponse)
async def push_data(
    request: SyncPushRequest,
    edge_device: EdgeDeviceDocument = Depends(get_current_edge_device),
    sync_orchestrator: SyncOrchestrator = Depends(get_sync_orchestrator)
) -> ApiResponse:
    """
    エッジからのデータ送信（Push）

    - トランザクション、ジャーナル、ログデータの受信
    - 受信データを各サービスに配信
    """
    await sync_orchestrator.process_push_request(
        edge_id=edge_device.edge_id,
        data_type=request.data_type,
        data=request.data
    )

    return ApiResponse(
        success=True,
        message="Data received successfully"
    )
```

## 5. 同期フロー実装

### 5.1 差分同期フロー

#### 5.1.1 エッジ側処理（Edge Sync Engine）
```python
# app/core/edge_sync_engine.py
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from logging import getLogger

logger = getLogger(__name__)

class EdgeSyncEngine:
    """エッジ側同期エンジン"""

    def __init__(self, config, http_client, queue_manager):
        self.config = config
        self.http_client = http_client
        self.queue_manager = queue_manager
        self.sync_interval = config.SYNC_POLL_INTERVAL
        self.is_running = False

    async def start(self):
        """同期処理を開始"""
        self.is_running = True

        # データタイプごとに独立したタスクを起動
        tasks = []
        for data_type in self.config.SYNC_DATA_TYPES:
            task = asyncio.create_task(
                self._sync_loop(data_type)
            )
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _sync_loop(self, data_type: str):
        """データタイプ別の同期ループ"""
        while self.is_running:
            try:
                # Pull同期（クラウドからデータ取得）
                if self._should_pull(data_type):
                    await self._pull_sync(data_type)

                # Push同期（クラウドへデータ送信）
                if self._should_push(data_type):
                    await self._push_sync(data_type)

                # キューからの再送信
                await self._process_queue(data_type)

            except Exception as e:
                logger.error(f"Sync error for {data_type}: {e}")
                await self._handle_sync_error(data_type, e)

            # 次回同期まで待機
            await asyncio.sleep(self.sync_interval)

    async def _pull_sync(self, data_type: str):
        """Pullモードでの同期"""
        # 最終同期タイムスタンプを取得
        last_sync = await self._get_last_sync_timestamp(data_type)

        # 同期リクエスト送信
        request = {
            "data_type": data_type,
            "last_sync_timestamp": last_sync,
            "sync_type": "differential"
        }

        response = await self.http_client.post(
            f"{self.config.CLOUD_SYNC_URL}/pull",
            json=request,
            headers=self._get_auth_headers()
        )

        if response.status_code == 200:
            # 受信データを適用
            await self._apply_received_data(
                data_type,
                response.json()["data"]
            )
            # 同期状態を更新
            await self._update_sync_status(data_type, "completed")
        else:
            raise Exception(f"Pull sync failed: {response.status_code}")

    async def _push_sync(self, data_type: str):
        """Pushモードでの同期"""
        # 送信対象データを収集
        data = await self._collect_local_data(data_type)

        if not data:
            return

        # データ送信
        request = {
            "data_type": data_type,
            "data": data
        }

        response = await self.http_client.post(
            f"{self.config.CLOUD_SYNC_URL}/push",
            json=request,
            headers=self._get_auth_headers()
        )

        if response.status_code == 200:
            # 送信済みデータをマーク
            await self._mark_as_synced(data_type, data)
        else:
            # 失敗時はキューに追加
            await self.queue_manager.add_to_queue(data_type, data)

    def _should_pull(self, data_type: str) -> bool:
        """Pull同期が必要か判定"""
        # マスターデータはクラウドから取得
        return data_type in ["master_data", "terminal"]

    def _should_push(self, data_type: str) -> bool:
        """Push同期が必要か判定"""
        # トランザクション、ジャーナル、ログはエッジから送信
        return data_type in [
            "tran_log",
            "open_close_log",
            "cash_in_out_log",
            "journal",
            "log_application",
            "log_request"
        ]
```

#### 5.1.2 クラウド側処理（Cloud Sync Engine）
```python
# app/core/cloud_sync_engine.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from logging import getLogger

logger = getLogger(__name__)

class CloudSyncEngine:
    """クラウド側同期エンジン"""

    def __init__(self, db, dapr_client, config):
        self.db = db
        self.dapr_client = dapr_client
        self.config = config

    async def process_pull_request(
        self,
        edge_id: str,
        data_type: str,
        last_sync_timestamp: datetime,
        sync_type: str = "differential"
    ) -> Dict[str, Any]:
        """Pull リクエスト処理"""

        # 同期開始を記録
        sync_id = await self._start_sync_session(
            edge_id, data_type, sync_type, "cloud-to-edge"
        )

        try:
            if sync_type == "differential":
                # 差分データを取得
                data = await self._get_differential_data(
                    data_type, last_sync_timestamp
                )
            else:
                # 一括データを取得
                data = await self._get_bulk_data(data_type)

            # データ圧縮
            compressed_data = self._compress_data(data)

            # 同期成功を記録
            await self._complete_sync_session(
                sync_id,
                len(data),
                len(compressed_data),
                "success"
            )

            return {
                "sync_id": sync_id,
                "data_type": data_type,
                "sync_type": sync_type,
                "record_count": len(data),
                "compressed_data": compressed_data,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            # 同期失敗を記録
            await self._complete_sync_session(
                sync_id, 0, 0, "failed", str(e)
            )
            raise

    async def process_push_request(
        self,
        edge_id: str,
        data_type: str,
        data: List[Dict[str, Any]]
    ):
        """Push リクエスト処理"""

        # 同期開始を記録
        sync_id = await self._start_sync_session(
            edge_id, data_type, "differential", "edge-to-cloud"
        )

        try:
            # データを各サービスに配信
            await self._distribute_to_services(data_type, data)

            # 同期成功を記録
            await self._complete_sync_session(
                sync_id,
                len(data),
                0,
                "success"
            )

        except Exception as e:
            # 同期失敗を記録
            await self._complete_sync_session(
                sync_id, 0, 0, "failed", str(e)
            )
            raise

    async def _get_differential_data(
        self,
        data_type: str,
        last_sync_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        """差分データ取得"""

        # データタイプに応じて適切なサービスから取得
        if data_type == "master_data":
            return await self._get_master_data_changes(last_sync_timestamp)
        elif data_type == "terminal":
            return await self._get_terminal_changes(last_sync_timestamp)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    async def _distribute_to_services(
        self,
        data_type: str,
        data: List[Dict[str, Any]]
    ):
        """受信データを各サービスに配信"""

        service_map = {
            "tran_log": "cart",
            "open_close_log": "terminal",
            "cash_in_out_log": "terminal",
            "journal": "journal",
            "log_application": "report",
            "log_request": "report"
        }

        target_service = service_map.get(data_type)
        if not target_service:
            raise ValueError(f"No service mapping for {data_type}")

        # Dapr Service Invocationで配信
        await self.dapr_client.invoke_method(
            target_service,
            f"sync/{data_type}",
            data=data
        )
```

### 5.2 一括同期フロー

#### 5.2.1 24時間営業対応のノーダウンタイム更新戦略
```python
# app/services/strategies/bulk_sync.py
from typing import Dict, Any, List
from datetime import datetime
import asyncio

class BulkSyncStrategy:
    """一括同期戦略"""

    async def sync_with_versioning(
        self,
        db,
        collection_name: str,
        new_data: List[Dict[str, Any]]
    ):
        """
        バージョニング方式での一括同期

        1. 新バージョンのデータを投入
        2. バージョンを切り替え
        3. 旧バージョンのデータを削除
        """

        # 現在のバージョンを取得
        current_version = await self._get_current_version(db, collection_name)
        new_version = current_version + 1

        # 新バージョンのデータを投入
        for item in new_data:
            item["_sync_version"] = new_version
            item["_sync_active"] = False

        await db[collection_name].insert_many(new_data)

        # バージョン切り替え（トランザクション）
        async with await db.client.start_session() as session:
            async with session.start_transaction():
                # 新バージョンをアクティブ化
                await db[collection_name].update_many(
                    {"_sync_version": new_version},
                    {"$set": {"_sync_active": True}},
                    session=session
                )

                # 旧バージョンを非アクティブ化
                await db[collection_name].update_many(
                    {"_sync_version": current_version},
                    {"$set": {"_sync_active": False}},
                    session=session
                )

        # 旧バージョンを遅延削除（5分後）
        await asyncio.sleep(300)
        await db[collection_name].delete_many(
            {"_sync_version": current_version}
        )

    async def sync_with_shadow_table(
        self,
        db,
        collection_name: str,
        new_data: List[Dict[str, Any]]
    ):
        """
        Shadow Table方式での一括同期

        1. 一時コレクションにデータ投入
        2. コレクション名を入れ替え
        3. 旧コレクションを削除
        """

        temp_collection = f"{collection_name}_temp"
        backup_collection = f"{collection_name}_backup"

        # 一時コレクションにデータ投入
        await db[temp_collection].insert_many(new_data)

        # インデックス作成
        await self._create_indexes(db[temp_collection], collection_name)

        # コレクション名の入れ替え（原子的操作）
        await db[collection_name].rename(backup_collection)
        await db[temp_collection].rename(collection_name)

        # バックアップコレクションを遅延削除
        await asyncio.sleep(300)
        await db.drop_collection(backup_collection)
```

## 6. サービス間通信

### 6.1 Dapr Integration

#### 6.1.1 Pub/Sub設定
```yaml
# dapr/components/pubsub-sync.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: sync-pubsub
spec:
  type: pubsub.redis
  version: v1
  metadata:
  - name: redisHost
    value: redis:6379
  - name: redisPassword
    value: ""
  - name: consumerID
    value: "sync-service"
```

#### 6.1.2 トピック定義
```python
# app/utils/pubsub_topics.py
class SyncTopics:
    """同期関連のPub/Subトピック"""

    # マスターデータ更新通知
    MASTER_DATA_UPDATED = "sync.master_data.updated"

    # トランザクション受信通知
    TRANSACTION_RECEIVED = "sync.transaction.received"

    # 同期完了通知
    SYNC_COMPLETED = "sync.completed"

    # 同期エラー通知
    SYNC_ERROR = "sync.error"
```

### 6.2 他サービスとの連携

#### 6.2.1 データ収集インターフェース
```python
# app/core/data_collector.py
class DataCollector:
    """各サービスからデータを収集"""

    async def collect_master_data(self, last_sync: datetime) -> List[Dict]:
        """Master Dataサービスから差分データ収集"""
        response = await self.dapr_client.invoke_method(
            "master-data",
            "api/v1/sync/changes",
            data={
                "from_timestamp": last_sync.isoformat(),
                "data_types": ["products", "prices", "tax_rules"]
            }
        )
        return response.json()

    async def collect_transaction_logs(self, last_sync: datetime) -> List[Dict]:
        """Cartサービスからトランザクションログ収集"""
        response = await self.dapr_client.invoke_method(
            "cart",
            "api/v1/sync/transactions",
            data={
                "from_timestamp": last_sync.isoformat()
            }
        )
        return response.json()
```

#### 6.2.2 データ配信インターフェース
```python
# app/core/data_applier.py
class DataApplier:
    """各サービスへデータを配信"""

    async def apply_to_service(
        self,
        service_name: str,
        data_type: str,
        data: List[Dict]
    ):
        """指定サービスにデータを適用"""

        endpoint_map = {
            "master-data": "/api/v1/sync/apply",
            "cart": "/api/v1/sync/transactions",
            "journal": "/api/v1/sync/journals",
            "terminal": "/api/v1/sync/terminals"
        }

        endpoint = endpoint_map.get(service_name)
        if not endpoint:
            raise ValueError(f"Unknown service: {service_name}")

        response = await self.dapr_client.invoke_method(
            service_name,
            endpoint,
            data={
                "data_type": data_type,
                "records": data
            }
        )

        if response.status_code != 200:
            raise Exception(f"Failed to apply data to {service_name}")
```

## 7. エラーハンドリングと信頼性

### 7.1 サーキットブレーカー実装
```python
# app/utils/circuit_breaker.py
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """サーキットブレーカーパターン実装"""

    def __init__(self, failure_threshold=3, timeout_seconds=60):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        """関数呼び出しをラップ"""

        # 状態確認
        if self.state == CircuitState.OPEN:
            if datetime.utcnow() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is open")

        try:
            # 関数実行
            result = await func(*args, **kwargs)

            # 成功時の処理
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0

            return result

        except Exception as e:
            # 失敗時の処理
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN

            raise e
```

### 7.2 リトライ機構
```python
# app/utils/retry_handler.py
import asyncio
from typing import Callable, Any

class RetryHandler:
    """指数バックオフによるリトライ"""

    def __init__(self, max_retries=5, base_delay=1):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """リトライ付き実行"""

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e

                # 指数バックオフ
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
```

### 7.3 オフライン対応
```python
# app/utils/queue_manager.py
from typing import Dict, Any, List
from datetime import datetime

class QueueManager:
    """オフライン時のキュー管理"""

    def __init__(self, db, max_queue_size=10000):
        self.db = db
        self.max_queue_size = max_queue_size

    async def add_to_queue(
        self,
        data_type: str,
        data: Dict[str, Any],
        operation: str = "create"
    ):
        """キューにデータを追加"""

        # キューサイズチェック
        queue_size = await self.db.sync_queue.count_documents(
            {"status": "pending"}
        )

        if queue_size >= self.max_queue_size:
            # 古いデータから削除
            await self._cleanup_old_entries()

        # キューに追加
        queue_doc = {
            "queue_id": self._generate_queue_id(),
            "data_type": data_type,
            "operation": operation,
            "data": data,
            "status": "pending",
            "queued_at": datetime.utcnow(),
            "retry_count": 0
        }

        await self.db.sync_queue.insert_one(queue_doc)

    async def process_queue(self, data_type: str = None) -> List[Dict]:
        """キューからデータを取得して処理"""

        filter_query = {"status": "pending"}
        if data_type:
            filter_query["data_type"] = data_type

        # ペンディングのデータを取得
        pending_items = await self.db.sync_queue.find(
            filter_query
        ).sort("queued_at", 1).limit(100).to_list(100)

        return pending_items
```

## 8. パフォーマンス最適化

### 8.1 データ圧縮
```python
# app/utils/compression.py
import gzip
import json
from typing import Any, Dict

class DataCompressor:
    """データ圧縮ユーティリティ"""

    @staticmethod
    def compress(data: Any) -> bytes:
        """データをgzip圧縮"""
        json_str = json.dumps(data, ensure_ascii=False)
        return gzip.compress(json_str.encode('utf-8'))

    @staticmethod
    def decompress(compressed_data: bytes) -> Any:
        """gzip圧縮データを展開"""
        json_str = gzip.decompress(compressed_data).decode('utf-8')
        return json.loads(json_str)

    @staticmethod
    def get_compression_ratio(original: Any, compressed: bytes) -> float:
        """圧縮率を計算"""
        original_size = len(json.dumps(original).encode('utf-8'))
        compressed_size = len(compressed)
        return 1 - (compressed_size / original_size)
```

### 8.2 バッチ処理最適化
```python
# app/core/batch_processor.py
import asyncio
from typing import List, Dict, Any

class BatchProcessor:
    """バッチ処理最適化"""

    def __init__(self, batch_size=1000, max_concurrent=10):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_in_batches(
        self,
        data: List[Dict[str, Any]],
        processor_func
    ):
        """データをバッチ処理"""

        # バッチに分割
        batches = [
            data[i:i + self.batch_size]
            for i in range(0, len(data), self.batch_size)
        ]

        # 並行処理
        tasks = []
        for batch in batches:
            task = self._process_batch_with_limit(batch, processor_func)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

    async def _process_batch_with_limit(self, batch, processor_func):
        """セマフォによる並行数制限"""
        async with self.semaphore:
            return await processor_func(batch)
```

## 9. 監視とログ

### 9.1 メトリクス収集
```python
# app/utils/metrics.py
from datetime import datetime
from typing import Dict, Any

class SyncMetrics:
    """同期メトリクス収集"""

    def __init__(self):
        self.metrics = {}

    async def record_sync_operation(
        self,
        edge_id: str,
        data_type: str,
        operation: str,
        record_count: int,
        data_size: int,
        duration_ms: int,
        status: str
    ):
        """同期操作を記録"""

        key = f"{edge_id}:{data_type}:{operation}"

        if key not in self.metrics:
            self.metrics[key] = {
                "total_count": 0,
                "total_records": 0,
                "total_bytes": 0,
                "total_duration_ms": 0,
                "success_count": 0,
                "failure_count": 0,
                "last_operation": None
            }

        metric = self.metrics[key]
        metric["total_count"] += 1
        metric["total_records"] += record_count
        metric["total_bytes"] += data_size
        metric["total_duration_ms"] += duration_ms

        if status == "success":
            metric["success_count"] += 1
        else:
            metric["failure_count"] += 1

        metric["last_operation"] = datetime.utcnow()

    def get_metrics(self) -> Dict[str, Any]:
        """メトリクスを取得"""
        return self.metrics
```

### 9.2 ヘルスチェック
```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from app.api.v1.schemas import HealthCheckResponse

router = APIRouter(prefix="/sync", tags=["sync-health"])

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    sync_service = Depends(get_sync_service)
):
    """ヘルスチェックエンドポイント"""

    components = await sync_service.check_health()

    overall_status = "healthy"
    if any(c["status"] == "unhealthy" for c in components):
        overall_status = "unhealthy"
    elif any(c["status"] == "degraded" for c in components):
        overall_status = "degraded"

    return HealthCheckResponse(
        status=overall_status,
        components=components,
        timestamp=datetime.utcnow()
    )
```

## 10. セキュリティ実装

### 10.1 JWT認証
```python
# app/utils/jwt_handler.py
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

class JWTHandler:
    """JWT トークンハンドラ"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(
        self,
        edge_id: str,
        tenant_id: str,
        store_code: str,
        expires_delta: timedelta = timedelta(hours=1)
    ) -> str:
        """JWTトークン生成"""

        payload = {
            "edge_id": edge_id,
            "tenant_id": tenant_id,
            "store_code": store_code,
            "exp": datetime.utcnow() + expires_delta,
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """JWTトークン検証"""

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
```

### 10.2 データ暗号化
```python
# app/utils/encryption.py
from cryptography.fernet import Fernet
import base64
import json
from typing import Any

class DataEncryption:
    """データ暗号化ユーティリティ"""

    def __init__(self, encryption_key: bytes = None):
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            self.cipher = Fernet(Fernet.generate_key())

    def encrypt_data(self, data: Any) -> str:
        """データを暗号化"""
        json_str = json.dumps(data, ensure_ascii=False)
        encrypted = self.cipher.encrypt(json_str.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    def decrypt_data(self, encrypted_data: str) -> Any:
        """データを復号化"""
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return json.loads(decrypted.decode('utf-8'))
```

## 11. 設定管理

### 11.1 環境設定
```python
# app/config/settings.py
from pydantic import BaseSettings
from typing import Optional

class SyncSettings(BaseSettings):
    """Sync Service設定"""

    # 基本設定
    SERVICE_NAME: str = "sync"
    SERVICE_VERSION: str = "1.0.0"

    # 動作モード
    SYNC_MODE: str = "cloud"  # cloud|edge

    # エッジ設定（エッジモード時）
    EDGE_ID: Optional[str] = None
    EDGE_SECRET: Optional[str] = None
    CLOUD_SYNC_URL: Optional[str] = None

    # クラウド設定（クラウドモード時）
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 1

    # 同期設定
    SYNC_POLL_INTERVAL: int = 60  # 秒
    SYNC_DATA_TYPES: list = [
        "master_data",
        "terminal",
        "tran_log",
        "open_close_log",
        "cash_in_out_log",
        "journal",
        "log_application",
        "log_request"
    ]

    # バッチ処理設定
    BATCH_SIZE: int = 1000
    MAX_CONCURRENT_BATCHES: int = 10

    # リトライ設定
    MAX_RETRY_COUNT: int = 5
    RETRY_BACKOFF_BASE: int = 2

    # サーキットブレーカー設定
    CIRCUIT_BREAKER_THRESHOLD: int = 3
    CIRCUIT_BREAKER_TIMEOUT: int = 60

    # キュー設定
    MAX_QUEUE_SIZE: int = 10000
    QUEUE_CLEANUP_DAYS: int = 7

    # データベース設定
    MONGODB_URI: str = "mongodb://localhost:27017/?replicaSet=rs0"
    DB_NAME_PREFIX: str = "sync_"

    # Redis設定
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # Dapr設定
    DAPR_HTTP_PORT: int = 3500
    DAPR_GRPC_PORT: int = 50001

    # ログ設定
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = SyncSettings()
```

## 12. テスト戦略

### 12.1 単体テスト例
```python
# tests/test_sync_engine.py
import pytest
from unittest.mock import Mock, AsyncMock
from app.core.edge_sync_engine import EdgeSyncEngine

@pytest.mark.asyncio
async def test_pull_sync_success():
    """Pull同期成功テスト"""

    # モック設定
    config = Mock(
        CLOUD_SYNC_URL="http://cloud.example.com",
        SYNC_POLL_INTERVAL=60
    )
    http_client = AsyncMock()
    queue_manager = AsyncMock()

    engine = EdgeSyncEngine(config, http_client, queue_manager)

    # テストデータ
    http_client.post.return_value = Mock(
        status_code=200,
        json=lambda: {
            "data": {
                "records": [{"id": 1, "name": "test"}],
                "sync_id": "SYNC123"
            }
        }
    )

    # 実行
    await engine._pull_sync("master_data")

    # 検証
    assert http_client.post.called
    assert queue_manager.add_to_queue.not_called
```

### 12.2 統合テスト例
```python
# tests/test_sync_integration.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_end_to_end_sync_flow():
    """エンドツーエンド同期フロー"""

    async with AsyncClient(app=app, base_url="http://test") as client:
        # 認証
        auth_response = await client.post(
            "/api/v1/sync/auth",
            json={
                "tenant_id": "A1234",
                "edge_id": "EDGE001",
                "secret": "test_secret"
            }
        )

        assert auth_response.status_code == 200
        token = auth_response.json()["data"]["access_token"]

        # Pull同期
        sync_response = await client.post(
            "/api/v1/sync/pull",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "data_type": "master_data",
                "last_sync_timestamp": "2025-01-01T00:00:00Z",
                "sync_type": "differential"
            }
        )

        assert sync_response.status_code == 200
        assert "sync_id" in sync_response.json()["data"]
```

## 13. デプロイメント

### 13.1 Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 依存関係インストール
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy

# アプリケーションコピー
COPY . .

# ポート公開
EXPOSE 8007

# 実行コマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
```

### 13.2 Docker Compose設定
```yaml
# services/docker-compose.yml への追加
  sync:
    build: ./sync
    container_name: sync
    ports:
      - "8007:8007"
      - "5687:5678"  # デバッグポート
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/?replicaSet=rs0
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - SYNC_MODE=${SYNC_MODE:-cloud}
      - EDGE_ID=${EDGE_ID:-}
      - EDGE_SECRET=${EDGE_SECRET:-}
      - CLOUD_SYNC_URL=${CLOUD_SYNC_URL:-}
      - LOG_LEVEL=INFO
    depends_on:
      - mongodb
      - redis
    networks:
      - kugelpos-network
    volumes:
      - ./sync:/app
    restart: unless-stopped
```

## 14. 運用考慮事項

### 14.1 監視項目
- 同期遅延時間
- 同期失敗率
- データ転送量
- キューサイズ
- エッジ端末の接続状態
- サーキットブレーカー状態

### 14.2 アラート設定
- 同期遅延が5分を超えた場合
- 同期失敗率が10%を超えた場合
- キューサイズが80%を超えた場合
- エッジ端末の切断が30分以上続いた場合

### 14.3 メンテナンス
- 同期履歴の定期削除（30日以上前のデータ）
- キューデータのクリーンアップ
- 失敗した同期の手動リトライ
- エッジ端末の認証情報ローテーション

## 15. 今後の拡張計画

### 15.1 Phase 2
- 優先度ベースの同期制御
- 差分圧縮アルゴリズムの最適化
- リアルタイム同期（WebSocket）

### 15.2 Phase 3
- 競合解決戦略の拡張（CRDTなど）
- マルチリージョン対応
- エッジ間同期（P2P）

### 15.3 Phase 4
- AI基づいた同期スケジュール最適化
- 予測的データプリフェッチ
- 自動フェイルオーバー機能
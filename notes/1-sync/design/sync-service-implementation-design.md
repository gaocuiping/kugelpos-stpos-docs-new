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
- ファイル収集機能によるアプリケーションログ統合管理

## 2. サービスアーキテクチャ

### 2.1 モード設計

#### 2.1.1 Cloud Mode
```python
# クラウドモードの責務
- エッジ端末の認証・管理
- 同期リクエストの受信と処理
- マスターデータの配信
- トランザクションデータの収集
- ファイル収集指示の管理とアーカイブ保存
- 同期状態の一元管理
- 同期履歴の記録
```

#### 2.1.2 Edge Mode
```python
# エッジモードの責務
- クラウドへの定期ポーリング
- 差分データの取得と適用
- ローカルデータの収集と送信
- ファイル収集とzip圧縮
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
│   │       ├── file_collection.py       # ファイル収集エンドポイント
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
│   │   ├── file_collection_engine.py    # ファイル収集エンジン
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
│   │   │   ├── sync_queue_document.py       # 同期キュードキュメント
│   │   │   ├── file_collection_request_document.py    # ファイル収集リクエスト
│   │   │   ├── file_collection_history_document.py    # ファイル収集履歴
│   │   │   └── file_collection_instruction_document.py # ファイル収集指示
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── sync_status_repository.py    # 同期状態リポジトリ
│   │       ├── sync_history_repository.py   # 同期履歴リポジトリ
│   │       ├── edge_device_repository.py    # エッジ端末リポジトリ
│   │       ├── sync_queue_repository.py     # 同期キューリポジトリ
│   │       └── file_collection_repository.py # ファイル収集リポジトリ
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py              # 認証サービス
│   │   ├── sync_service.py              # 同期サービス
│   │   ├── file_collection_service.py   # ファイル収集サービス
│   │   ├── data_services/
│   │   │   ├── __init__.py
│   │   │   ├── master_data_service.py   # マスターデータ同期
│   │   │   ├── transaction_service.py   # トランザクション同期
│   │   │   └── journal_service.py       # ジャーナル同期
│   │   └── strategies/
│   │       ├── __init__.py
│   │       ├── differential_sync.py     # 差分同期戦略
│   │       └── bulk_sync.py            # 一括同期戦略
│   └── utils/
│       ├── __init__.py
│       ├── compression.py               # データ圧縮ユーティリティ
│       ├── file_compression.py          # ファイル圧縮ユーティリティ（zip）
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

#### 3.1.5 file_collection_request Collection
```python
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from kugel_common.models.documents.base_document import BaseDocumentModel

class FileCollectionRequestDocument(BaseDocumentModel):
    """ファイル収集リクエストドキュメント"""

    # 識別情報
    collection_id: str = Field(description="収集ID (COLLECT_{tenant_id}_{edge_id}_{ulid})")
    edge_id: str = Field(description="エッジ端末ID")

    # 収集情報
    collection_name: str = Field(description="収集名（管理用）")
    target_paths: List[str] = Field(description="収集対象パス配列")
    exclude_patterns: List[str] = Field(default=[], description="除外パターン配列")
    max_archive_size_mb: int = Field(default=100, description="最大アーカイブサイズ（MB）")

    # 状態情報
    status: str = Field(default="queued", description="状態: queued|processing|completed|failed|expired")
    requested_by: str = Field(description="要求者")

    # 実行情報
    start_time: Optional[datetime] = Field(None, description="開始時刻")
    end_time: Optional[datetime] = Field(None, description="終了時刻")
    error_details: Optional[Dict[str, Any]] = Field(None, description="エラー詳細")

    class Config:
        collection = "file_collection_request"
        indexes = [
            {"keys": [("collection_id", 1)], "unique": True},
            {"keys": [("edge_id", 1), ("status", 1)]},
            {"keys": [("status", 1), ("created_at", -1)]},
        ]
```

#### 3.1.6 file_collection_history Collection
```python
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from kugel_common.models.documents.base_document import BaseDocumentModel

class FileCollectionHistoryDocument(BaseDocumentModel):
    """ファイル収集履歴ドキュメント"""

    # 識別情報
    collection_id: str = Field(description="収集ID")
    edge_id: str = Field(description="エッジ端末ID")

    # 収集情報
    collection_name: str = Field(description="収集名")
    target_paths: List[str] = Field(description="収集対象パス配列")
    exclude_patterns: List[str] = Field(default=[], description="除外パターン配列")

    # 実行情報
    start_time: datetime = Field(description="開始時刻")
    end_time: datetime = Field(description="終了時刻")
    processing_time_ms: int = Field(description="処理時間（ミリ秒）")

    # 結果情報
    status: str = Field(description="最終状態: completed|failed")
    file_count: int = Field(description="収集ファイル数")
    archive_size_bytes: int = Field(description="アーカイブサイズ（バイト）")
    archive_path: str = Field(description="アーカイブ保存パス")

    # エラー情報
    error_details: Optional[Dict[str, Any]] = Field(None, description="エラー詳細")

    # 管理情報
    requested_by: str = Field(description="要求者")

    class Config:
        collection = "file_collection_history"
        indexes = [
            {"keys": [("collection_id", 1)], "unique": True},
            {"keys": [("edge_id", 1), ("start_time", -1)]},
            {"keys": [("status", 1)]},
        ]
```

#### 3.1.7 file_collection_instruction Collection（クラウド側のみ）
```python
from datetime import datetime
from typing import Optional, List
from pydantic import Field
from kugel_common.models.documents.base_document import BaseDocumentModel

class FileCollectionInstructionDocument(BaseDocumentModel):
    """ファイル収集指示ドキュメント"""

    # 識別情報
    collection_id: str = Field(description="収集ID")
    edge_id: str = Field(description="対象エッジ端末ID")

    # 収集指示
    collection_name: str = Field(description="収集名")
    target_paths: List[str] = Field(description="収集対象パス配列")
    exclude_patterns: List[str] = Field(default=[], description="除外パターン配列")
    max_archive_size_mb: int = Field(default=100, description="最大アーカイブサイズ（MB）")

    # 管理情報
    status: str = Field(default="pending", description="状態: pending|sent|processing|completed|failed|expired")
    priority: str = Field(default="normal", description="優先度: low|normal|high|urgent")
    requested_by: str = Field(description="要求者")
    expires_at: datetime = Field(description="有効期限")

    class Config:
        collection = "file_collection_instruction"
        indexes = [
            {"keys": [("collection_id", 1)], "unique": True},
            {"keys": [("edge_id", 1), ("status", 1)]},
            {"keys": [("status", 1), ("priority", -1)]},
            {"keys": [("expires_at", 1)]},  # TTLインデックス
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

### 4.3 ファイル収集API

#### 4.3.1 ファイル収集指示（Cloud Mode）
```python
# app/api/v1/file_collection.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from app.api.v1.schemas import (
    FileCollectionRequest,
    FileCollectionResponse,
    ApiResponse
)
from app.services.file_collection_service import FileCollectionService
from app.dependencies.auth import get_current_edge_device
from app.models.documents.edge_device_document import EdgeDeviceDocument

router = APIRouter(prefix="/sync/file-collection", tags=["file-collection"])

@router.post("/", response_model=ApiResponse[FileCollectionResponse])
async def create_file_collection(
    request: FileCollectionRequest,
    file_collection_service: FileCollectionService = Depends(get_file_collection_service)
) -> ApiResponse[FileCollectionResponse]:
    """
    ファイル収集指示の作成（管理者向け）

    - エッジ端末に対するファイル収集指示を作成
    - 次回の同期リクエストで指示を配信
    """
    result = await file_collection_service.create_collection_request(
        edge_id=request.edge_id,
        collection_name=request.collection_name,
        target_paths=request.target_paths,
        exclude_patterns=request.exclude_patterns,
        max_archive_size_mb=request.max_archive_size_mb,
        requested_by=request.requested_by
    )

    return ApiResponse[FileCollectionResponse](
        success=True,
        data=result
    )

@router.post("/{collection_id}/upload")
async def upload_collection_archive(
    collection_id: str,
    archive: UploadFile = File(...),
    edge_device: EdgeDeviceDocument = Depends(get_current_edge_device),
    file_collection_service: FileCollectionService = Depends(get_file_collection_service)
) -> ApiResponse:
    """
    エッジからのファイルアーカイブアップロード

    - zip形式の圧縮ファイルを受信
    - ファイル検証と保存
    """
    # ファイル形式チェック
    if not archive.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ZIP files are allowed"
        )

    # ファイルサイズチェック
    if archive.size > 100 * 1024 * 1024:  # 100MB制限
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum limit"
        )

    result = await file_collection_service.receive_archive(
        collection_id=collection_id,
        edge_id=edge_device.edge_id,
        archive_file=archive
    )

    return ApiResponse(
        success=True,
        data=result,
        message="Archive uploaded successfully"
    )

@router.get("/{collection_id}")
async def get_collection_status(
    collection_id: str,
    file_collection_service: FileCollectionService = Depends(get_file_collection_service)
) -> ApiResponse:
    """
    ファイル収集状態の確認
    """
    result = await file_collection_service.get_collection_status(collection_id)

    return ApiResponse(
        success=True,
        data=result
    )

@router.get("/{collection_id}/download")
async def download_collection_archive(
    collection_id: str,
    file_collection_service: FileCollectionService = Depends(get_file_collection_service)
):
    """
    収集済みアーカイブのダウンロード
    """
    return await file_collection_service.download_archive(collection_id)
```

## 5. 同期フロー実装

### 5.1 差分同期フロー（ファイル収集対応）

#### 5.1.1 エッジ側処理（Edge Sync Engine）
```python
# app/core/edge_sync_engine.py
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from logging import getLogger

logger = getLogger(__name__)

class EdgeSyncEngine:
    """エッジ側同期エンジン（ファイル収集対応）"""

    def __init__(self, config, http_client, queue_manager, file_collection_engine):
        self.config = config
        self.http_client = http_client
        self.queue_manager = queue_manager
        self.file_collection_engine = file_collection_engine
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
        """Pullモードでの同期（ファイル収集指示を含む可能性）"""
        # 最終同期タイムスタンプを取得
        last_sync = await self._get_last_sync_timestamp(data_type)

        # 同期リクエスト送信
        request = {
            "data_type": data_type,
            "last_sync_timestamp": last_sync,
            "sync_type": "differential"
        }

        response = await self.http_client.post(
            f"{self.config.CLOUD_SYNC_URL}/request",
            json=request,
            headers=self._get_auth_headers()
        )

        if response.status_code == 200:
            response_data = response.json()["data"]
            
            # 通常の同期データを適用
            if "sync_data" in response_data:
                await self._apply_received_data(
                    data_type,
                    response_data["sync_data"]
                )
            
            # ファイル収集指示がある場合は処理
            if "file_collection_request" in response_data:
                await self._handle_file_collection_request(
                    response_data["file_collection_request"]
                )
            
            # 同期状態を更新
            await self._update_sync_status(data_type, "completed")
        else:
            raise Exception(f"Pull sync failed: {response.status_code}")

    async def _handle_file_collection_request(self, collection_request: Dict[str, Any]):
        """
        ファイル収集指示の処理
        """
        try:
            # ファイル収集エンジンに処理を委譲
            result = await self.file_collection_engine.process_collection_request(
                collection_request
            )
            
            logger.info(f"File collection completed: {result}")
            
        except Exception as e:
            logger.error(f"File collection failed: {e}")
            
            # エラー状態をクラウドに通知
            await self._notify_collection_error(
                collection_request["collection_id"],
                str(e)
            )

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

#### 5.1.2 ファイル収集エンジン
```python
# app/core/file_collection_engine.py
import zipfile
import os
import tempfile
import fnmatch
from pathlib import Path
from typing import Dict, Any, List
from logging import getLogger

logger = getLogger(__name__)

class FileCollectionEngine:
    """ファイル収集専用エンジン"""

    def __init__(self, config, http_client):
        self.config = config
        self.http_client = http_client
        self.allowed_paths = config.FILE_COLLECTION_ALLOWED_PATHS.split(',')
        self.forbidden_paths = ["/etc", "/root", "/sys", "/proc", "/dev"]

    async def process_collection_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        ファイル収集リクエストの処理
        """
        collection_id = request["collection_id"]
        target_paths = request["target_paths"]
        exclude_patterns = request.get("exclude_patterns", [])
        max_size_mb = request.get("max_archive_size_mb", 100)

        # Step 1: パス検証
        validated_paths = await self._validate_paths(target_paths)

        # Step 2: ファイル収集
        collected_files = await self._collect_files(validated_paths, exclude_patterns)

        # Step 3: zip圧縮
        archive_path = await self._create_zip_archive(
            collected_files, collection_id, max_size_mb
        )

        # Step 4: クラウドにアップロード
        upload_result = await self._upload_archive(collection_id, archive_path)

        # Step 5: 一時ファイル削除
        os.unlink(archive_path)

        return {
            "collection_id": collection_id,
            "status": "completed",
            "file_count": len(collected_files),
            "archive_size_bytes": upload_result["size"]
        }

    async def _validate_paths(self, target_paths: List[str]) -> List[str]:
        """
        収集対象パスのセキュリティ検証
        """
        validated_paths = []

        for path in target_paths:
            # パストラバーサル攻撃対策
            normalized_path = os.path.normpath(path)
            if ".." in normalized_path:
                raise ValueError(f"Invalid path detected: {path}")

            # 禁止パスチェック
            is_forbidden = any(
                normalized_path.startswith(forbidden)
                for forbidden in self.forbidden_paths
            )
            if is_forbidden:
                raise ValueError(f"Forbidden path: {path}")

            # ホワイトリストチェック
            is_allowed = any(
                normalized_path.startswith(allowed.strip())
                for allowed in self.allowed_paths
            )
            if not is_allowed:
                raise ValueError(f"Path not in allowed list: {path}")

            # 存在チェック
            if os.path.exists(normalized_path):
                validated_paths.append(normalized_path)
            else:
                logger.warning(f"Path not found: {path}")

        return validated_paths

    async def _collect_files(
        self, 
        paths: List[str], 
        exclude_patterns: List[str]
    ) -> List[str]:
        """
        ファイル収集（ディレクトリの場合は再帰的に処理）
        """
        collected_files = []

        for path in paths:
            if os.path.isfile(path):
                if not self._should_exclude(path, exclude_patterns):
                    collected_files.append(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if not self._should_exclude(file_path, exclude_patterns):
                            collected_files.append(file_path)

        return collected_files

    async def _create_zip_archive(
        self, 
        files: List[str], 
        collection_id: str, 
        max_size_mb: int
    ) -> str:
        """
        ファイルをzip形式で圧縮
        """
        with tempfile.NamedTemporaryFile(
            suffix=f"_{collection_id}.zip",
            delete=False
        ) as temp_file:
            archive_path = temp_file.name

        total_size = 0
        max_size_bytes = max_size_mb * 1024 * 1024

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                try:
                    file_size = os.path.getsize(file_path)

                    if total_size + file_size > max_size_bytes:
                        logger.warning(f"Archive size limit reached: {max_size_mb}MB")
                        break

                    # アーカイブ内でのパス名を設定
                    arcname = os.path.relpath(file_path, '/')
                    zipf.write(file_path, arcname)
                    total_size += file_size

                except (OSError, PermissionError) as e:
                    logger.warning(f"Cannot read file {file_path}: {e}")

        logger.info(f"Created archive: {archive_path} ({total_size} bytes)")
        return archive_path

    async def _upload_archive(self, collection_id: str, archive_path: str) -> Dict[str, Any]:
        """
        圧縮アーカイブをクラウドにアップロード
        """
        headers = {"Authorization": f"Bearer {self.config.EDGE_TOKEN}"}

        with open(archive_path, 'rb') as f:
            files = {
                'archive': (
                    f"{collection_id}.zip",
                    f,
                    'application/zip'
                )
            }

            response = await self.http_client.post(
                f"{self.config.CLOUD_SYNC_URL}/file-collection/{collection_id}/upload",
                files=files,
                headers=headers,
                timeout=600.0  # 10分タイムアウト
            )

            if response.status_code != 200:
                raise Exception(f"Upload failed: {response.status_code}")

            return response.json()["data"]

    def _should_exclude(self, filepath: str, exclude_patterns: List[str]) -> bool:
        """
        ファイルが除外パターンにマッチするかチェック
        """
        return any(
            fnmatch.fnmatch(filepath, pattern)
            for pattern in exclude_patterns
        )
```

#### 5.1.3 クラウド側処理（Cloud Sync Engine）
```python
# app/core/cloud_sync_engine.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from logging import getLogger

logger = getLogger(__name__)

class CloudSyncEngine:
    """クラウド側同期エンジン（ファイル収集対応）"""

    def __init__(self, db, dapr_client, config, file_collection_service):
        self.db = db
        self.dapr_client = dapr_client
        self.config = config
        self.file_collection_service = file_collection_service

    async def process_pull_request(
        self,
        edge_id: str,
        data_type: str,
        last_sync_timestamp: datetime,
        sync_type: str = "differential"
    ) -> Dict[str, Any]:
        """Pull リクエスト処理（ファイル収集指示を含む）"""

        # 同期開始を記録
        sync_id = await self._start_sync_session(
            edge_id, data_type, sync_type, "cloud-to-edge"
        )

        try:
            response_data = {}

            # 通常の同期データ取得
            if sync_type == "differential":
                sync_data = await self._get_differential_data(
                    data_type, last_sync_timestamp
                )
            else:
                sync_data = await self._get_bulk_data(data_type)

            if sync_data:
                compressed_data = self._compress_data(sync_data)
                response_data["sync_data"] = {
                    "records": sync_data,
                    "compressed_data": compressed_data,
                    "record_count": len(sync_data)
                }

            # ファイル収集指示があるかチェック
            collection_request = await self.file_collection_service.get_pending_collection(edge_id)
            if collection_request:
                response_data["file_collection_request"] = {
                    "collection_id": collection_request.collection_id,
                    "collection_name": collection_request.collection_name,
                    "target_paths": collection_request.target_paths,
                    "exclude_patterns": collection_request.exclude_patterns,
                    "max_archive_size_mb": collection_request.max_archive_size_mb
                }

                # 指示を送信済みにマーク
                await self.file_collection_service.mark_as_sent(collection_request.collection_id)

            # 同期成功を記録
            await self._complete_sync_session(
                sync_id,
                len(sync_data) if sync_data else 0,
                len(compressed_data) if sync_data else 0,
                "success"
            )

            return {
                "sync_id": sync_id,
                "data_type": data_type,
                "sync_type": sync_type,
                "timestamp": datetime.utcnow(),
                **response_data
            }

        except Exception as e:
            # 同期失敗を記録
            await self._complete_sync_session(
                sync_id, 0, 0, "failed", str(e)
            )
            raise
```

### 5.2 ファイル収集サービス

#### 5.2.1 ファイル収集サービス実装
```python
# app/services/file_collection_service.py
import os
import shutil
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import UploadFile
from fastapi.responses import FileResponse
from logging import getLogger

logger = getLogger(__name__)

class FileCollectionService:
    """ファイル収集サービス"""

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.storage_path = config.FILE_COLLECTION_STORAGE_PATH
        self.retention_days = config.FILE_COLLECTION_RETENTION_DAYS

    async def create_collection_request(
        self,
        edge_id: str,
        collection_name: str,
        target_paths: List[str],
        exclude_patterns: List[str] = None,
        max_archive_size_mb: int = 100,
        requested_by: str = "system"
    ) -> Dict[str, Any]:
        """
        ファイル収集リクエストの作成
        """
        collection_id = self._generate_collection_id(edge_id)

        # 収集指示をDBに保存
        instruction_doc = {
            "collection_id": collection_id,
            "edge_id": edge_id,
            "collection_name": collection_name,
            "target_paths": target_paths,
            "exclude_patterns": exclude_patterns or [],
            "max_archive_size_mb": max_archive_size_mb,
            "status": "pending",
            "priority": "normal",
            "requested_by": requested_by,
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await self.db.file_collection_instruction.insert_one(instruction_doc)

        return {
            "collection_id": collection_id,
            "status": "queued",
            "message": "File collection request created"
        }

    async def get_pending_collection(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """
        指定エッジの未送信収集指示を取得
        """
        instruction = await self.db.file_collection_instruction.find_one({
            "edge_id": edge_id,
            "status": "pending",
            "expires_at": {"$gt": datetime.utcnow()}
        })

        return instruction

    async def mark_as_sent(self, collection_id: str):
        """
        収集指示を送信済みにマーク
        """
        await self.db.file_collection_instruction.update_one(
            {"collection_id": collection_id},
            {
                "$set": {
                    "status": "sent",
                    "updated_at": datetime.utcnow()
                }
            }
        )

    async def receive_archive(
        self,
        collection_id: str,
        edge_id: str,
        archive_file: UploadFile
    ) -> Dict[str, Any]:
        """
        エッジからのアーカイブファイル受信
        """
        # 収集リクエストの存在確認
        request_doc = await self.db.file_collection_request.find_one({
            "collection_id": collection_id,
            "edge_id": edge_id
        })

        if not request_doc:
            raise ValueError(f"Collection request not found: {collection_id}")

        # ファイル保存
        archive_path = os.path.join(
            self.storage_path,
            f"{collection_id}.zip"
        )

        os.makedirs(os.path.dirname(archive_path), exist_ok=True)

        with open(archive_path, 'wb') as f:
            shutil.copyfileobj(archive_file.file, f)

        # 履歴に記録
        history_doc = {
            "collection_id": collection_id,
            "edge_id": edge_id,
            "collection_name": request_doc["collection_name"],
            "target_paths": request_doc["target_paths"],
            "exclude_patterns": request_doc["exclude_patterns"],
            "start_time": request_doc.get("start_time", datetime.utcnow()),
            "end_time": datetime.utcnow(),
            "processing_time_ms": 0,  # エッジ側で計算
            "status": "completed",
            "file_count": 0, # メタデータから取得
            "archive_size_bytes": archive_file.size,
            "archive_path": archive_path,
            "error_details": None,
            "requested_by": request_doc["requested_by"],
            "created_at": datetime.utcnow()
        }

        await self.db.file_collection_history.insert_one(history_doc)

        # リクエストを完了にマーク
        await self.db.file_collection_request.update_one(
            {"collection_id": collection_id},
            {
                "$set": {
                    "status": "completed",
                    "end_time": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        return {
            "collection_id": collection_id,
            "file_count": 0,  # 後で実装
            "archive_size_bytes": archive_file.size,
            "status": "completed"
        }

    async def download_archive(self, collection_id: str) -> FileResponse:
        """
        収集済みアーカイブのダウンロード
        """
        history = await self.db.file_collection_history.find_one({
            "collection_id": collection_id
        })

        if not history or not os.path.exists(history["archive_path"]):
            raise ValueError(f"Archive not found: {collection_id}")

        return FileResponse(
            path=history["archive_path"],
            filename=f"{collection_id}.zip",
            media_type="application/zip"
        )

    def _generate_collection_id(self, edge_id: str) -> str:
        """
        収集IDの生成
        """
        import ulid
        return f"COLLECT_{self.config.TENANT_ID}_{edge_id}_{ulid.new().str}"
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

    # ファイル収集完了通知
    FILE_COLLECTION_COMPLETED = "sync.file_collection.completed"

    # ファイル収集エラー通知
    FILE_COLLECTION_ERROR = "sync.file_collection.error"
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
        "journal"
        # 注記: アプリケーションログはファイル収集で処理
    ]

    # ファイル収集設定
    FILE_COLLECTION_MAX_ARCHIVE_SIZE_MB: int = 100
    FILE_COLLECTION_ALLOWED_PATHS: str = "/var/log/kugelpos,/opt/kugelpos/data"
    FILE_COLLECTION_STORAGE_PATH: str = "/storage/collections"
    FILE_COLLECTION_RETENTION_DAYS: int = 30

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

### 12.1 単体テスト例（ファイル収集を含む）
```python
# tests/test_file_collection_engine.py
import pytest
import tempfile
import os
import zipfile
from unittest.mock import Mock, AsyncMock
from app.core.file_collection_engine import FileCollectionEngine

@pytest.mark.asyncio
async def test_file_collection_success():
    """ファイル収集成功テスト"""

    # モック設定
    config = Mock(
        FILE_COLLECTION_ALLOWED_PATHS="/tmp/test",
        EDGE_TOKEN="test_token"
    )
    http_client = AsyncMock()
    
    engine = FileCollectionEngine(config, http_client)

    # テスト用ファイル作成
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.log")
        with open(test_file, 'w') as f:
            f.write("test log content")

        # 実行
        request = {
            "collection_id": "TEST_COLLECT_001",
            "target_paths": [test_file],
            "exclude_patterns": [],
            "max_archive_size_mb": 100
        }

        # HTTP応答をモック
        http_client.post.return_value = Mock(
            status_code=200,
            json=lambda: {"data": {"size": 1024}}
        )

        result = await engine.process_collection_request(request)

        # 検証
        assert result["status"] == "completed"
        assert result["file_count"] == 1
        assert http_client.post.called

@pytest.mark.asyncio
async def test_file_collection_path_validation():
    """パス検証テスト"""

    config = Mock(
        FILE_COLLECTION_ALLOWED_PATHS="/var/log/kugelpos"
    )
    engine = FileCollectionEngine(config, None)

    # 禁止パスのテスト
    forbidden_paths = ["/etc/passwd", "/root/.ssh/id_rsa"]
    
    with pytest.raises(ValueError, match="Forbidden path"):
        await engine._validate_paths(forbidden_paths)

    # 許可されていないパスのテスト
    unauthorized_paths = ["/home/user/file.txt"]
    
    with pytest.raises(ValueError, match="Path not in allowed list"):
        await engine._validate_paths(unauthorized_paths)
```

### 12.2 統合テスト例（ファイル収集を含む）
```python
# tests/test_file_collection_integration.py
import pytest
import tempfile
import os
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_file_collection_end_to_end():
    """ファイル収集エンドツーエンドテスト"""

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

        token = auth_response.json()["data"]["access_token"]

        # ファイル収集指示作成（管理者）
        collection_response = await client.post(
            "/api/v1/sync/file-collection/",
            json={
                "edge_id": "EDGE001",
                "collection_name": "test_logs",
                "target_paths": ["/var/log/kugelpos/test.log"],
                "exclude_patterns": ["*.tmp"],
                "max_archive_size_mb": 50,
                "requested_by": "admin"
            }
        )

        collection_id = collection_response.json()["data"]["collection_id"]

        # 同期リクエスト（ファイル収集指示を受信）
        sync_response = await client.post(
            "/api/v1/sync/request",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "data_type": "master_data",
                "last_sync_timestamp": "2025-01-01T00:00:00Z",
                "sync_type": "differential"
            }
        )

        assert sync_response.status_code == 200
        response_data = sync_response.json()["data"]
        assert "file_collection_request" in response_data

        # ファイルアップロード（エッジからの模擬アップロード）
        with tempfile.NamedTemporaryFile(suffix=".zip") as temp_zip:
            with zipfile.ZipFile(temp_zip, 'w') as zipf:
                zipf.writestr("test.log", "test log content")

            temp_zip.seek(0)
            
            upload_response = await client.post(
                f"/api/v1/sync/file-collection/{collection_id}/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"archive": ("test.zip", temp_zip, "application/zip")}
            )

            assert upload_response.status_code == 200
```

## 13. デプロイメント

### 13.1 Dockerfile（ファイル収集対応）
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# システムパッケージ（zip処理用）
RUN apt-get update && apt-get install -y \
    zip \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 依存関係インストール
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system --deploy

# アプリケーションコピー
COPY . .

# ストレージディレクトリ作成
RUN mkdir -p /storage/collections

# ポート公開
EXPOSE 8007

# 実行コマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
```

### 13.2 Docker Compose設定（ファイル収集対応）
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
      - FILE_COLLECTION_ALLOWED_PATHS=/var/log/kugelpos,/opt/kugelpos/data
      - FILE_COLLECTION_STORAGE_PATH=/storage/collections
      - LOG_LEVEL=INFO
    depends_on:
      - mongodb
      - redis
    networks:
      - kugelpos-network
    volumes:
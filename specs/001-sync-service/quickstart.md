# Sync Service - 開発者向けクイックスタートガイド

## 概要

このガイドは、Sync Service の開発環境を素早くセットアップし、機能実装を開始するための手順を提供します。

**推定時間**: 30分

**前提条件**:
- Docker & Docker Compose がインストール済み
- Python 3.12+ がインストール済み
- Pipenv がインストール済み (`pip install pipenv`)
- Git リポジトリがクローン済み
- FastAPI と MongoDB の基本的な理解

## アーキテクチャ概要

Sync Service は、クラウドとエッジ端末間の双方向データ同期を提供します:

- **クラウドモード**: エッジ端末からデータを受信し、マスタデータを提供
- **エッジモード**: クラウドにトランザクションデータを送信し、マスタデータを受信
- **デュアルモード設計**: 環境変数によるモード切り替えを備えた単一コードベース

**主要機能**:
- マスタデータ同期 (クラウド → エッジ): 商品、スタッフ、税ルール、設定
- トランザクション同期 (エッジ → クラウド): 売上、ジャーナル、端末状態
- P2P配信を伴うスケジュールされたマスタファイル適用
- トラブルシューティング用のリモートファイル収集
- 24時間有効期限のJWTベース認証

## クイックスタート (5分)

### 1. リポジトリのクローンと Sync Service へ移動

```bash
# Clone repository (if not already done)
git clone https://github.com/kugel-masa/kugelpos-backend.git
cd kugelpos-backend

# Navigate to sync service directory
cd services/sync
```

### 2. サービスディレクトリ構造の作成

```bash
# Create directory structure for sync service
mkdir -p app/{config,models,repositories,services,api,schemas,middleware,utils,background}
mkdir -p tests/{unit,integration,fixtures}
mkdir -p app/models/{documents,repositories}
mkdir -p app/api/{v1,deps}
mkdir -p app/services/{sync,auth,scheduled_master,file_collection}
mkdir -p app/background/{jobs,tasks}

# Create empty __init__.py files
find app -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;
```

### 3. 基本設定ファイルの作成

`Pipfile` を作成:

```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
fastapi = ">=0.104.0"
uvicorn = {extras = ["standard"], version = ">=0.24.0"}
motor = ">=3.3.0"
pydantic = ">=2.4.0"
pydantic-settings = ">=2.0.0"
python-jose = {extras = ["cryptography"], version = ">=3.3.0"}
passlib = {extras = ["bcrypt"], version = ">=1.7.4"}
python-multipart = ">=0.0.6"
httpx = ">=0.25.0"
aiofiles = ">=23.2.0"
apscheduler = ">=3.10.0"
kugel-common = {path = "../commons/dist/kugel_common-0.1.0-py3-none-any.whl"}

[dev-packages]
pytest = ">=7.4.0"
pytest-asyncio = ">=0.21.0"
pytest-cov = ">=4.1.0"
httpx = ">=0.25.0"
ruff = ">=0.1.0"
mypy = ">=1.6.0"

[requires]
python_version = "3.12"

[scripts]
dev = "uvicorn app.main:app --reload --host 0.0.0.0 --port 8007"
test = "pytest tests/ -v"
lint = "ruff check app/"
format = "ruff format app/"
typecheck = "mypy app/"
```

`.env.example` を作成:

```bash
# Service Configuration
SERVICE_NAME=sync
SERVICE_PORT=8007
SYNC_MODE=cloud  # cloud or edge

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/?replicaSet=rs0
MONGODB_DATABASE_PREFIX=sync

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Dapr Configuration
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Edge Mode Authentication (for Edge Mode only)
EDGE_ID=edge-tenant001-store001-001
EDGE_SECRET=<SHA256-hashed-secret>

# Token Refresh Settings (for Edge Mode only)
TOKEN_REFRESH_THRESHOLD_SECONDS=3600  # Refresh 1 hour before expiration
TOKEN_REFRESH_CHECK_INTERVAL=300      # Check every 5 minutes

# Sync Configuration
SYNC_POLL_INTERVAL=30  # seconds (30-60)
SYNC_RETRY_MAX=5
SYNC_CIRCUIT_BREAKER_THRESHOLD=3
SYNC_CIRCUIT_BREAKER_TIMEOUT=60

# File Collection Configuration
FILE_COLLECTION_MAX_SIZE_MB=100
FILE_COLLECTION_WHITELIST=/app/logs,/app/config,/app/data

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # json or text
```

### 4. 依存関係のインストール

```bash
# Install all dependencies
pipenv install

# Install development dependencies
pipenv install --dev
```

## 開発環境のセットアップ (10分)

### 1. インフラストラクチャサービスの起動

```bash
# Navigate to services directory
cd ..

# Start MongoDB and Redis
docker-compose up -d mongodb redis

# Verify MongoDB replica set status
docker exec -it mongodb mongosh --eval "rs.status()"

# If replica set not initialized, run:
../scripts/init-mongodb-replica.sh
```

### 2. データベースコレクションとインデックスの初期化

`scripts/init_db.py` を作成:

```python
"""Initialize database collections and indexes for sync service"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import get_settings

async def create_indexes():
    """Create all indexes for sync service"""
    settings = get_settings()
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    db = client[f"sync_{settings.TENANT_ID}"]  # Example tenant

    print("Creating indexes for sync service...")

    # SyncStatus indexes
    await db.status_sync.create_index(
        [("edge_id", 1), ("data_type", 1)],
        unique=True,
        name="edge_data_unique"
    )
    await db.status_sync.create_index(
        [("status", 1), ("next_sync_at", 1)],
        name="scheduled_sync"
    )
    print("✓ SyncStatus indexes created")

    # SyncHistory indexes
    await db.info_sync_history.create_index(
        [("sync_id", 1)],
        unique=True,
        name="sync_id_unique"
    )
    await db.info_sync_history.create_index(
        [("edge_id", 1), ("started_at", -1)],
        name="edge_history"
    )
    print("✓ SyncHistory indexes created")

    # EdgeTerminal indexes
    await db.info_edge_terminal.create_index(
        [("edge_id", 1)],
        unique=True,
        name="edge_id_unique"
    )
    await db.info_edge_terminal.create_index(
        [("store_code", 1), ("p2p_priority", 1), ("status", 1)],
        name="p2p_discovery"
    )
    print("✓ EdgeTerminal indexes created")

    # Additional indexes for other collections...

    print("All indexes created successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())
```

初期化を実行:

```bash
pipenv run python scripts/init_db.py
```

### 3. メインアプリケーションエントリポイントの作成

`app/main.py` を作成:

```python
"""Main FastAPI application for Sync Service"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import get_settings
from app.api.v1 import router as v1_router
from app.background.scheduler import start_scheduler, stop_scheduler

settings = get_settings()

app = FastAPI(
    title="Sync Service",
    description="Bidirectional data synchronization between cloud and edge terminals",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(v1_router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    print(f"Starting Sync Service in {settings.SYNC_MODE} mode...")

    # Start background scheduler (for polling in edge mode)
    if settings.SYNC_MODE == "edge":
        await start_scheduler()
        # Start token refresh scheduler (Edge Mode only)
        from app.background.token_refresh_scheduler import start_token_refresh_job
        await start_token_refresh_job()

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    print("Shutting down Sync Service...")

    # Stop background scheduler
    if settings.SYNC_MODE == "edge":
        await stop_scheduler()
        from app.background.token_refresh_scheduler import scheduler as token_scheduler
        token_scheduler.shutdown()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_info = {
        "status": "healthy",
        "service": "sync",
        "mode": settings.SYNC_MODE
    }

    # Add token health for Edge Mode
    if settings.SYNC_MODE == "edge":
        from app.services.auth.token_manager import get_token_manager
        token_manager = get_token_manager()
        health_info["token"] = {
            "present": token_manager.get_token() is not None,
            "expired": token_manager.is_expired(),
            "should_refresh": token_manager.should_refresh()
        }

    return health_info
```

### 4. 開発サーバーの起動

```bash
# Method 1: Using pipenv script
pipenv run dev

# Method 2: Using uvicorn directly
pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8007

# Verify service is running
curl http://localhost:8007/health
# Expected: {"status":"healthy","service":"sync","mode":"cloud"}
```

## 実装ワークフロー (15分)

### フェーズ1: データモデルの実装

`data-model.md` の Pydantic モデルから開始します:

**例: SyncStatus モデル**

`app/models/documents/sync_status.py` を作成:

```python
from kugel_common.models.base import BaseDocumentModel
from pydantic import Field
from typing import Optional, Literal
from datetime import datetime

class SyncStatusModel(BaseDocumentModel):
    """Synchronization status tracking for edge terminals"""

    edge_id: str = Field(
        ...,
        description="Edge terminal ID",
        pattern="^edge-[a-zA-Z0-9]+-[a-zA-Z0-9]+-[0-9]{3}$",
    )

    data_type: Literal["master_data", "transaction_log", "terminal_state"] = Field(
        ...,
        description="Type of data being synchronized (Note: journal data is included in transaction_log via journal_text field)"
    )

    last_sync_at: Optional[datetime] = None
    sync_type: Optional[Literal["full", "incremental", "complete"]] = None
    status: Literal["idle", "syncing", "success", "failed"] = Field(default="idle")
    retry_count: int = Field(default=0, ge=0, le=5)
    error_message: Optional[str] = Field(None, max_length=2000)
    next_sync_at: Optional[datetime] = None
```

**テスト駆動開発 (TDD) でテストを先に記述**:

`tests/unit/test_sync_status.py` を作成:

```python
import pytest
from pydantic import ValidationError
from app.models.documents.sync_status import SyncStatusModel

def test_sync_status_valid():
    """Test valid SyncStatus creation"""
    status = SyncStatusModel(
        edge_id="edge-tenant001-store001-001",
        data_type="master_data",
        status="idle"
    )
    assert status.edge_id == "edge-tenant001-store001-001"
    assert status.retry_count == 0

def test_sync_status_invalid_edge_id():
    """Test invalid edge_id pattern"""
    with pytest.raises(ValidationError):
        SyncStatusModel(
            edge_id="invalid-format",
            data_type="master_data"
        )

def test_sync_status_retry_count_limit():
    """Test retry count validation"""
    with pytest.raises(ValidationError):
        SyncStatusModel(
            edge_id="edge-tenant001-store001-001",
            data_type="master_data",
            retry_count=6  # Exceeds max of 5
        )
```

テストを実行:

```bash
pipenv run pytest tests/unit/test_sync_status.py -v
```

### フェーズ2: リポジトリの実装

リポジトリパターンに従ってリポジトリを作成:

`app/models/repositories/sync_status_repository.py`:

```python
from kugel_common.models.repositories.abstract_repository import AbstractRepository
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.documents.sync_status import SyncStatusModel
from typing import Optional, List
from datetime import datetime

class SyncStatusRepository(AbstractRepository[SyncStatusModel]):
    """Repository for SyncStatus operations"""

    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__("status_sync", SyncStatusModel, db)

    async def find_by_edge_and_type(
        self,
        edge_id: str,
        data_type: str
    ) -> Optional[SyncStatusModel]:
        """Find sync status by edge ID and data type"""
        return await self.find_one({"edge_id": edge_id, "data_type": data_type})

    async def find_pending_syncs(
        self,
        current_time: datetime
    ) -> List[SyncStatusModel]:
        """Find sync tasks ready for execution"""
        query = {
            "status": "idle",
            "next_sync_at": {"$lte": current_time}
        }
        return await self.find_many(query, limit=100)
```

### フェーズ3: API エンドポイントの実装

API 仕様については `contracts/*.yaml` を参照:

`app/api/v1/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import TokenRequest, TokenResponse
from app.services.auth.jwt_service import JWTService
from app.models.repositories.edge_terminal_repository import EdgeTerminalRepository
from app.api.deps import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/token", response_model=TokenResponse)
async def obtain_token(
    request: TokenRequest,
    db = Depends(get_db)
):
    """
    Obtain JWT token for edge terminal authentication

    Related: auth-api.yaml POST /auth/token
    """
    terminal_repo = EdgeTerminalRepository(db)
    jwt_service = JWTService()

    # Find edge terminal
    terminal = await terminal_repo.find_by_edge_id(request.edge_id)
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid edge_id or secret"
        )

    # Verify secret (SHA256 hash)
    if not jwt_service.verify_secret(request.secret, terminal.secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid edge_id or secret"
        )

    # Generate JWT token
    token = jwt_service.create_access_token({
        "edge_id": terminal.edge_id,
        "tenant_id": terminal.tenant_id,
        "store_code": terminal.store_code
    })

    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=86400,  # 24 hours
        edge_id=terminal.edge_id,
        tenant_id=terminal.tenant_id,
        store_code=terminal.store_code
    )
```

### フェーズ4: バックグラウンドジョブの実装 (APScheduler)

`app/background/scheduler.py`:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config.settings import get_settings
from app.background.jobs.sync_poller import poll_cloud_for_updates

scheduler = AsyncIOScheduler()
settings = get_settings()

async def start_scheduler():
    """Start background scheduler for edge mode"""
    interval = settings.SYNC_POLL_INTERVAL

    scheduler.add_job(
        poll_cloud_for_updates,
        trigger=IntervalTrigger(seconds=interval),
        id="sync_polling",
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    print(f"Scheduler started (polling interval: {interval}s)")

async def stop_scheduler():
    """Stop background scheduler"""
    scheduler.shutdown()
    print("Scheduler stopped")
```

### フェーズ5: JWT トークン管理の実装 (エッジモード)

**トークンマネージャー** - `app/services/auth/token_manager.py`:

```python
"""JWT token lifecycle management for Edge Mode"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.config.settings import get_settings

settings = get_settings()

class TokenManager:
    """Manages JWT token lifecycle with proactive refresh"""

    def __init__(self):
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._refresh_threshold_seconds = settings.TOKEN_REFRESH_THRESHOLD_SECONDS

    def set_token(self, token: str) -> None:
        """Store token and extract expiration"""
        self._token = token
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            self._token_expires_at = datetime.fromtimestamp(payload["exp"])
        except Exception:
            # Fallback to 24h expiration
            self._token_expires_at = datetime.utcnow() + timedelta(hours=24)

    def get_token(self) -> Optional[str]:
        """Get current token if valid"""
        if self._token and not self.should_refresh():
            return self._token
        return None

    def should_refresh(self) -> bool:
        """Check if token needs proactive refresh"""
        if not self._token_expires_at:
            return True
        time_until_expiry = (self._token_expires_at - datetime.utcnow()).total_seconds()
        return time_until_expiry <= self._refresh_threshold_seconds

    def is_expired(self) -> bool:
        """Check if token is expired"""
        if not self._token_expires_at:
            return True
        return datetime.utcnow() >= self._token_expires_at

    def clear_token(self) -> None:
        """Clear stored token (after 401 error)"""
        self._token = None
        self._token_expires_at = None

# Singleton instance
_token_manager: Optional[TokenManager] = None

def get_token_manager() -> TokenManager:
    """Get singleton token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
```

**トークン更新スケジューラー** - `app/background/token_refresh_scheduler.py`:

```python
"""Proactive JWT token refresh scheduler for Edge Mode"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.auth.token_manager import get_token_manager
from app.services.auth.auth_service import AuthService
from app.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()
settings = get_settings()

async def start_token_refresh_job():
    """Start proactive token refresh job"""
    interval = settings.TOKEN_REFRESH_CHECK_INTERVAL

    scheduler.add_job(
        check_and_refresh_token,
        trigger=IntervalTrigger(seconds=interval),
        id="token_refresh",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(f"Token refresh scheduler started (check interval: {interval}s)")

async def check_and_refresh_token():
    """Check token expiration and refresh if needed"""
    token_manager = get_token_manager()
    try:
        if token_manager.should_refresh():
            logger.info("Token refresh needed, requesting new token...")
            auth_service = AuthService()
            new_token = await auth_service.authenticate(
                edge_id=settings.EDGE_ID,
                secret=settings.EDGE_SECRET
            )
            token_manager.set_token(new_token)
            logger.info("Token refreshed successfully")
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
```

**認証付きHTTPクライアント** - `app/utils/authenticated_http_client.py`:

```python
"""HTTP client with automatic token refresh on 401"""
from kugel_common.utils.http_client_helper import get_service_client
from app.services.auth.token_manager import get_token_manager
from app.services.auth.auth_service import AuthService
from app.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class AuthenticatedHttpClient:
    """HTTP client with automatic token refresh on 401"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.auth_service = AuthService()
        self.token_manager = get_token_manager()

    async def request(self, method: str, endpoint: str, **kwargs):
        """Execute HTTP request with automatic re-auth on 401"""
        token = self.token_manager.get_token()

        if not token:
            # Token expired or not available, authenticate first
            await self._authenticate()
            token = self.token_manager.get_token()

        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers

        try:
            async with get_service_client(self.base_url) as client:
                if method == "GET":
                    return await client.get(endpoint, **kwargs)
                elif method == "POST":
                    return await client.post(endpoint, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")

        except Exception as e:
            # Check for 401 Unauthorized
            if hasattr(e, "status_code") and e.status_code == 401:
                logger.warning("401 Unauthorized, re-authenticating...")
                self.token_manager.clear_token()

                # Retry authentication
                await self._authenticate()

                # Retry original request
                headers["Authorization"] = f"Bearer {self.token_manager.get_token()}"
                async with get_service_client(self.base_url) as client:
                    if method == "GET":
                        return await client.get(endpoint, **kwargs)
                    elif method == "POST":
                        return await client.post(endpoint, **kwargs)

            raise  # Re-raise if not 401

    async def _authenticate(self) -> None:
        """Perform authentication and store token"""
        new_token = await self.auth_service.authenticate(
            edge_id=settings.EDGE_ID,
            secret=settings.EDGE_SECRET
        )
        self.token_manager.set_token(new_token)
        logger.info("Authentication successful")
```

**使用例**:

```python
# Using AuthenticatedHttpClient for cloud API calls (Edge Mode)
from app.utils.authenticated_http_client import AuthenticatedHttpClient

client = AuthenticatedHttpClient(settings.CLOUD_SYNC_URL)

# Automatic token management - no manual handling required
response = await client.request("POST", "/api/v1/sync/request", json={
    "data_types": ["master_data"],
    "sync_type": "incremental"
})
```

## テスト戦略

### テスト構造の概要

```
tests/
├── conftest.py                      # 共通フィクスチャ（DB接続、テストクライアント等）
├── test_clean_data.py               # 全テスト実行前のデータクリーンアップ
├── test_setup_data.py               # 全テスト実行前のテストデータ投入
├── unit/                            # 単体テスト（外部依存なし）
│   ├── conftest.py                  # 単体テスト用フィクスチャ（モック等）
│   ├── test_models/                 # Pydantic モデルのバリデーションテスト
│   │   ├── test_sync_status.py
│   │   ├── test_edge_terminal.py
│   │   └── test_transaction_log.py
│   ├── test_repositories/           # リポジトリロジックテスト（MongoDB モック）
│   │   ├── test_sync_status_repository.py
│   │   └── test_edge_terminal_repository.py
│   ├── test_services/               # ビジネスロジックテスト（外部API モック）
│   │   ├── test_jwt_service.py
│   │   ├── test_master_sync_service.py
│   │   ├── test_token_manager.py
│   │   └── test_storage_service.py
│   └── test_utils/                  # ユーティリティ関数テスト
│       ├── test_file_helper.py
│       └── test_authenticated_http_client.py
└── integration/                     # 統合テスト（実サービス使用）
    ├── conftest.py                  # 統合テスト用フィクスチャ（実DB接続）
    ├── test_auth_api.py             # 認証API統合テスト
    ├── test_sync_api.py             # 同期API統合テスト
    ├── test_scheduled_master_api.py # 予約反映API統合テスト
    ├── test_file_collection_api.py  # ファイル収集API統合テスト
    ├── test_background_jobs.py      # バックグラウンドジョブテスト
    └── test_end_to_end.py           # エンドツーエンドテスト
```

### 単体テスト (Unit Tests)

**特徴**:
- 外部依存なし（DB、API、ファイルシステムをモック化）
- 高速実行（全テスト < 1秒）
- CI/CD で毎回実行

**実行コマンド**:
```bash
# すべての単体テストを実行
pipenv run pytest tests/unit/ -v

# 特定のテストディレクトリのみ実行
pipenv run pytest tests/unit/test_models/ -v
pipenv run pytest tests/unit/test_services/ -v

# カバレッジ測定（90%以上を目標）
pipenv run pytest tests/unit/ --cov=app --cov-report=html

# 並列実行（高速化）
pipenv run pytest tests/unit/ -n auto
```

**単体テスト例（モックを使用）**:

`tests/unit/test_services/test_master_sync_service.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.sync.master_sync_service import MasterSyncService

@pytest.mark.asyncio
async def test_fetch_master_data_success():
    """Test successful master data fetch with mocked HTTP client"""
    # Arrange: モックHTTPクライアントを準備
    mock_http_client = AsyncMock()
    mock_http_client.post.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "categories": [{"id": "cat001", "name": "Food"}],
            "products": [{"id": "prod001", "name": "Apple"}]
        }
    )

    service = MasterSyncService(http_client=mock_http_client)

    # Act: サービスメソッド実行
    result = await service.fetch_master_data(
        data_types=["categories", "products"],
        last_sync_at=None
    )

    # Assert: 結果検証
    assert len(result["categories"]) == 1
    assert result["categories"][0]["name"] == "Food"
    mock_http_client.post.assert_called_once()
```

### 統合テスト (Integration Tests)

**特徴**:
- 実サービス使用（MongoDB、Redis、FastAPI）
- エンドツーエンド検証
- ローカル開発・デプロイ前に実行

**実行コマンド**:
```bash
# MongoDB と Redis を起動
docker-compose up -d mongodb redis

# 統合テストを実行
pipenv run pytest tests/integration/ -v

# 特定のAPIテストのみ実行
pipenv run pytest tests/integration/test_auth_api.py -v

# カバレッジ測定（80%以上を目標）
pipenv run pytest tests/integration/ --cov=app --cov-report=html
```

**統合テスト例（実サービス使用）**:

`tests/integration/test_auth_api.py`:
```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.repositories.edge_terminal_repository import EdgeTerminalRepository

@pytest.mark.asyncio
async def test_auth_token_endpoint_success(test_db):
    """Test JWT token generation with real database"""
    # Arrange: テストデータを実際のMongoDBに投入
    terminal_repo = EdgeTerminalRepository(test_db)
    await terminal_repo.create({
        "edge_id": "edge-tenant001-store001-001",
        "tenant_id": "tenant001",
        "store_code": "store001",
        "secret": "hashed_secret_here",  # SHA256 hash
        "status": "online"
    })

    # Act: 実際のFastAPI エンドポイントを呼び出し
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/token", json={
            "edge_id": "edge-tenant001-store001-001",
            "secret": "plain_secret_here"
        })

    # Assert: レスポンス検証
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "Bearer"
    assert data["edge_id"] == "edge-tenant001-store001-001"
```

### テスト実行順序

```bash
# 1. データクリーンアップ
pipenv run pytest tests/test_clean_data.py -v

# 2. テストデータセットアップ
pipenv run pytest tests/test_setup_data.py -v

# 3. すべてのテストを実行
pipenv run pytest tests/ -v

# または一括実行（推奨）
pipenv run pytest tests/ -v --tb=short
```

## 一般的な開発タスク

### リントとフォーマッティングの実行

```bash
# Check code style
pipenv run lint

# Auto-fix issues
pipenv run ruff check --fix app/

# Format code
pipenv run format
```

### 型チェック

```bash
pipenv run typecheck
```

### すべての品質チェックを実行

```bash
# Lint, format, typecheck, and test
pipenv run lint && pipenv run format && pipenv run typecheck && pipenv run test
```

## Docker 開発

### Docker イメージのビルド

```bash
# From project root
cd ../..
./scripts/build.sh sync
```

### Docker Compose での実行

```bash
cd services
docker-compose up -d sync
docker-compose logs -f sync
```

## 次のステップ

1. **設計ドキュメントを読む**:
   - `spec.md`: 機能仕様
   - `data-model.md`: エンティティスキーマとリレーションシップ
   - `contracts/*.yaml`: API 仕様
   - `research.md`: 技術決定

2. **コア機能を実装する**:
   - 認証から開始 (US-006)
   - 次にマスタデータ同期 (US-001)
   - トランザクションデータ同期 (US-002)
   - スケジュールされたマスタファイル (US-003)
   - ファイル収集 (US-005)

3. **TDD ワークフローに従う**:
   - 最初にテストを記述 (red)
   - 最小限のコードを実装 (green)
   - 品質のためにリファクタリング (refactor)

4. **プロジェクト標準を参照**:
   - `.specify/memory/constitution.md`: プロジェクト原則
   - `CLAUDE.md`: 開発規約
   - 既存サービス (cart, report) をパターンとして参考に

## トラブルシューティング

### MongoDB 接続の問題

```bash
# Check MongoDB status
docker exec -it mongodb mongosh --eval "db.adminCommand('ping')"

# Verify replica set
docker exec -it mongodb mongosh --eval "rs.status()"

# Re-initialize replica set
./scripts/init-mongodb-replica.sh
```

### ポート競合

```bash
# Check if port 8007 is in use
lsof -i :8007

# Kill process using port
kill -9 $(lsof -t -i :8007)
```

### インポートエラー

```bash
# Ensure kugel-common is installed
cd services/commons
pipenv run python setup.py sdist bdist_wheel

cd ../sync
pipenv install ../commons/dist/kugel_common-0.1.0-py3-none-any.whl --force-reinstall
```

## 追加リソース

- **Kugelpos アーキテクチャ**: プロジェクトルートの `CLAUDE.md` を参照
- **FastAPI ドキュメント**: https://fastapi.tiangolo.com
- **Motor ドキュメント**: https://motor.readthedocs.io
- **Pydantic ドキュメント**: https://docs.pydantic.dev
- **APScheduler ドキュメント**: https://apscheduler.readthedocs.io

---

**ドキュメントバージョン**: 1.0.0
**最終更新日**: 2025-10-13
**推定合計時間**: 30分

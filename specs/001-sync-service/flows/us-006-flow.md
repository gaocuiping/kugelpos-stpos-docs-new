# User Story 6: エッジ端末の認証とセキュリティフロー

## 概要

各店舗のエッジ端末が、edge_idとsecretによる認証でクラウドに接続し、JWT トークンを取得してセキュアな通信を確立できる機能。

**主要機能**:
- edge_id + secret による初回認証
- JWT トークン発行（有効期限24時間）
- トークン自動更新（有効期限1時間前）
- 401エラー時の自動再認証
- シークレットのSHA-256ハッシュ化保存

## コンポーネント図

```mermaid
graph TB
    subgraph "Cloud Environment"
        CloudSync["Cloud Sync Service<br/>（認証サーバー）"]
        CloudDB[("MongoDB<br/>sync_tenant001")]
    end

    subgraph "Edge Environment"
        EdgeSync["Edge Sync Service<br/>（認証クライアント）"]
        TokenManager["Token Manager<br/>（トークンライフサイクル管理）"]
        AuthHTTPClient["Authenticated HTTP Client<br/>（自動再認証）"]
        EdgeDB[("MongoDB<br/>Edge Local")]
    end

    EdgeSync -->|"1. 初回認証<br/>edge_id + secret"| CloudSync
    CloudSync -->|"2. JWT発行<br/>24時間有効"| EdgeSync
    EdgeSync -->|"3. トークン保存"| EdgeDB
    TokenManager -->|"4. 定期チェック<br/>1時間前更新"| TokenManager
    TokenManager -->|"5. 自動更新"| CloudSync
    AuthHTTPClient -->|"6. API呼出<br/>Authorization: Bearer {token}"| CloudSync
    CloudSync -->|"7. 401エラー"| AuthHTTPClient
    AuthHTTPClient -->|"8. 自動再認証"| CloudSync
```

## 認証フロー概要

```mermaid
stateDiagram-v2
    [*] --> Unauthenticated: サービス起動
    Unauthenticated --> Authenticating: 初回認証要求
    Authenticating --> Authenticated: JWT取得成功
    Authenticating --> Unauthenticated: 認証失敗<br/>(無効なsecret)
    Authenticated --> TokenRefreshing: 有効期限1時間前
    TokenRefreshing --> Authenticated: 更新成功
    TokenRefreshing --> Unauthenticated: 更新失敗
    Authenticated --> Reauthenticating: 401エラー検出
    Reauthenticating --> Authenticated: 再認証成功
    Reauthenticating --> Unauthenticated: 再認証失敗

    Authenticated: Token valid (24 hours)<br/>Auto-refresh at 23 hours
    Reauthenticating: Retry max 3 times<br/>Exponential backoff
```

## フロー1: 初回認証（edge_id + secret）

**シナリオ**: エッジ端末起動時に、edge_idとsecretでクラウドに認証し、JWT トークンを取得。

```mermaid
sequenceDiagram
    participant EdgeSync as Edge Sync Service
    participant CloudSync as Cloud Sync Service
    participant CloudDB as MongoDB<br/>(sync_tenant001)
    participant EdgeDB as MongoDB<br/>(Edge Local)

    Note over EdgeSync,EdgeDB: 🔐 初回認証フロー

    rect rgb(240, 255, 240)
        Note right of EdgeSync: 1. サービス起動時の認証
        EdgeSync->>EdgeSync: 環境変数読み込み<br/>EDGE_ID = "edge-tenant001-store001-001"<br/>EDGE_SECRET = "plain_secret_value"

        Note over EdgeSync: ⚠️ 平文secretは環境変数のみ<br/>ハッシュ化してクラウドに送信しない
    end

    rect rgb(255, 250, 240)
        Note right of EdgeSync: 2. 認証リクエスト
        EdgeSync->>CloudSync: POST /api/v1/sync/auth<br/>{<br/> "edge_id": "edge-tenant001-store001-001",<br/> "secret": "plain_secret_value"<br/>}
        activate CloudSync
    end

    rect rgb(240, 245, 255)
        Note right of CloudSync: 3. EdgeTerminal検索とsecret検証
        CloudSync->>CloudDB: SELECT FROM info_edge_terminal<br/>WHERE edge_id = "edge-tenant001-store001-001"
        activate CloudDB

        Note over CloudDB: {<br/> "edge_id": "edge-tenant001-store001-001",<br/> "tenant_id": "tenant001",<br/> "store_code": "store001",<br/> "secret": "abc123...def" (SHA-256ハッシュ),<br/> "status": "online"<br/>}

        CloudDB-->>CloudSync: EdgeTerminal ドキュメント
        deactivate CloudDB

        CloudSync->>CloudSync: ハッシュ検証<br/>received_hash = sha256(plain_secret_value)<br/>stored_hash = "abc123...def"<br/>received_hash == stored_hash

        alt secret一致
            Note over CloudSync: ✅ 認証成功
        else secret不一致
            CloudSync-->>EdgeSync: ❌ 401 Unauthorized<br/>{<br/> "error_code": "800401",<br/> "message": "Invalid credentials",<br/> "timestamp": "2025-10-14T10:00:00Z"<br/>}
            Note over EdgeSync: 認証失敗<br/>サービス起動停止
        end
    end

    rect rgb(255, 255, 240)
        Note right of CloudSync: 4. JWT トークン生成
        CloudSync->>CloudSync: JWT生成<br/>payload = {<br/> "edge_id": "edge-tenant001-store001-001",<br/> "tenant_id": "tenant001",<br/> "store_code": "store001",<br/> "exp": now + 24 hours,<br/> "iat": now<br/>}<br/>token = jwt.encode(payload, JWT_SECRET_KEY)

        Note over CloudSync: トークン有効期限: 24時間<br/>アルゴリズム: HS256
    end

    rect rgb(240, 255, 240)
        Note right of CloudSync: 5. レスポンス返却
        CloudSync-->>EdgeSync: 200 OK<br/>{<br/> "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",<br/> "token_type": "Bearer",<br/> "expires_in": 86400,<br/> "tenant_id": "tenant001",<br/> "edge_id": "edge-tenant001-store001-001",<br/> "store_code": "store001"<br/>}
        deactivate CloudSync
    end

    rect rgb(240, 245, 255)
        Note right of EdgeSync: 6. トークン保存
        EdgeSync->>EdgeDB: トークン保存<br/>Collection: local_auth_token<br/>{<br/> "access_token": "eyJhbGciOi...",<br/> "expires_at": "2025-10-15T10:00:00Z",<br/> "issued_at": "2025-10-14T10:00:00Z"<br/>}
        activate EdgeDB
        EdgeDB-->>EdgeSync: 保存成功
        deactivate EdgeDB

        Note over EdgeSync: ✅ 認証完了<br/>同期処理開始可能
    end
```

**JWT ペイロード例**:

```json
{
  "edge_id": "edge-tenant001-store001-001",
  "tenant_id": "tenant001",
  "store_code": "store001",
  "exp": 1697356800,  // 有効期限（Unix timestamp）
  "iat": 1697270400   // 発行時刻（Unix timestamp）
}
```

**認証実装例（Cloud Side）**:

```python
from datetime import datetime, timedelta
from jose import jwt
import hashlib

JWT_SECRET_KEY = "your-secret-key"  # 環境変数から取得
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def hash_secret(plain_secret: str) -> str:
    """Hash secret with SHA-256"""
    return hashlib.sha256(plain_secret.encode('utf-8')).hexdigest()

async def authenticate_edge_terminal(
    edge_id: str,
    plain_secret: str,
    repository: EdgeTerminalRepository
) -> dict:
    """Authenticate edge terminal and issue JWT"""
    # EdgeTerminal検索
    edge_terminal = await repository.find_by_edge_id(edge_id)

    if not edge_terminal:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Secret検証
    received_hash = hash_secret(plain_secret)
    if received_hash != edge_terminal.secret:
        logger.warning(
            f"Authentication failed: secret mismatch",
            extra={"edge_id": edge_id}
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # JWT生成
    expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "edge_id": edge_terminal.edge_id,
        "tenant_id": edge_terminal.tenant_id,
        "store_code": edge_terminal.store_code,
        "exp": expires_at,
        "iat": datetime.utcnow()
    }

    access_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    logger.info(
        f"JWT issued successfully",
        extra={
            "edge_id": edge_id,
            "tenant_id": edge_terminal.tenant_id,
            "expires_at": expires_at.isoformat()
        }
    )

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": JWT_EXPIRATION_HOURS * 3600,
        "tenant_id": edge_terminal.tenant_id,
        "edge_id": edge_terminal.edge_id,
        "store_code": edge_terminal.store_code
    }
```

## フロー2: トークン自動更新（有効期限1時間前）

**シナリオ**: トークンが有効期限切れになる前に、自動的に新しいトークンを取得（プロアクティブ更新）。

```mermaid
sequenceDiagram
    participant Scheduler as APScheduler<br/>(Background)
    participant TokenManager as Token Manager
    participant EdgeDB as MongoDB<br/>(Edge Local)
    participant CloudSync as Cloud Sync Service

    Note over Scheduler,CloudSync: 🔄 トークン自動更新

    rect rgb(240, 255, 240)
        Note right of Scheduler: 1. 定期チェック（5分間隔）
        Scheduler->>TokenManager: check_token_expiration()
        activate TokenManager

        TokenManager->>EdgeDB: トークン取得<br/>SELECT FROM local_auth_token
        activate EdgeDB
        EdgeDB-->>TokenManager: {<br/> "access_token": "eyJhbGciOi...",<br/> "expires_at": "2025-10-15T10:00:00Z",<br/> "issued_at": "2025-10-14T10:00:00Z"<br/>}
        deactivate EdgeDB
    end

    rect rgb(255, 250, 240)
        Note right of TokenManager: 2. 有効期限チェック
        TokenManager->>TokenManager: 残り時間計算<br/>remaining = expires_at - now<br/>= 55 minutes

        alt 残り時間 <= 1時間
            Note over TokenManager: ⚠️ 更新が必要<br/>（残り55分）
        else 残り時間 > 1時間
            Note over TokenManager: ✅ 更新不要<br/>（残り5時間）
            TokenManager-->>Scheduler: スキップ
            deactivate TokenManager
        end
    end

    rect rgb(240, 245, 255)
        Note right of TokenManager: 3. トークン更新リクエスト
        TokenManager->>CloudSync: POST /api/v1/sync/auth<br/>{<br/> "edge_id": "edge-tenant001-store001-001",<br/> "secret": "plain_secret_value"<br/>}
        activate CloudSync

        CloudSync->>CloudSync: 認証処理<br/>（フロー1と同じ）

        CloudSync-->>TokenManager: 200 OK<br/>{<br/> "access_token": "eyJhbGciOi...",<br/> "expires_in": 86400<br/>}
        deactivate CloudSync
    end

    rect rgb(255, 255, 240)
        Note right of TokenManager: 4. 新トークン保存
        TokenManager->>EdgeDB: トークン更新<br/>UPDATE local_auth_token<br/>SET<br/> access_token = "eyJhbGciOi...",<br/> expires_at = "2025-10-16T09:00:00Z",<br/> issued_at = "2025-10-15T09:00:00Z"
        activate EdgeDB
        EdgeDB-->>TokenManager: 更新成功
        deactivate EdgeDB

        TokenManager-->>Scheduler: ✅ 更新完了
        deactivate TokenManager

        Note over Scheduler: ログ記録:<br/>INFO: Token refreshed successfully<br/>edge_id=edge-tenant001-store001-001<br/>new_expires_at=2025-10-16T09:00:00Z
    end
```

**トークン自動更新実装例（Edge Side）**:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TokenManager:
    """JWT token lifecycle management"""

    def __init__(self, edge_id: str, secret: str, repository):
        self.edge_id = edge_id
        self.secret = secret
        self.repository = repository
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """Start token refresh scheduler"""
        # 5分間隔でトークン有効期限をチェック
        self.scheduler.add_job(
            self.check_and_refresh_token,
            'interval',
            minutes=5,
            id='token_refresh',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("Token refresh scheduler started")

    async def check_and_refresh_token(self):
        """Check token expiration and refresh if needed"""
        # 現在のトークン取得
        token_data = await self.repository.get_token()

        if not token_data:
            logger.warning("No token found, authenticating...")
            await self.authenticate()
            return

        expires_at = token_data["expires_at"]
        remaining = (expires_at - datetime.utcnow()).total_seconds()

        # 残り1時間以内なら更新
        if remaining <= 3600:  # 1 hour
            logger.info(
                f"Token expiring soon, refreshing...",
                extra={
                    "edge_id": self.edge_id,
                    "remaining_seconds": remaining
                }
            )
            await self.refresh_token()
        else:
            logger.debug(
                f"Token still valid",
                extra={
                    "edge_id": self.edge_id,
                    "remaining_hours": remaining / 3600
                }
            )

    async def refresh_token(self):
        """Refresh JWT token"""
        try:
            # 認証API呼び出し
            response = await self.authenticate()

            # 新トークン保存
            await self.repository.save_token(
                access_token=response["access_token"],
                expires_at=datetime.utcnow() + timedelta(seconds=response["expires_in"]),
                issued_at=datetime.utcnow()
            )

            logger.info(
                f"Token refreshed successfully",
                extra={
                    "edge_id": self.edge_id,
                    "new_expires_at": (
                        datetime.utcnow() + timedelta(seconds=response["expires_in"])
                    ).isoformat()
                }
            )

        except Exception as e:
            logger.error(
                f"Token refresh failed",
                extra={"edge_id": self.edge_id, "error": str(e)}
            )

    async def authenticate(self) -> dict:
        """Authenticate with edge_id and secret"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CLOUD_SYNC_URL}/api/v1/sync/auth",
                json={
                    "edge_id": self.edge_id,
                    "secret": self.secret
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
```

## フロー3: 401エラー時の自動再認証

**シナリオ**: 同期API呼び出し時に401エラーが発生した場合、自動的に再認証してリトライ。

```mermaid
sequenceDiagram
    participant EdgeSync as Edge Sync Service
    participant AuthHTTPClient as Authenticated<br/>HTTP Client
    participant TokenManager as Token Manager
    participant CloudSync as Cloud Sync Service

    Note over EdgeSync,CloudSync: 🔁 自動再認証フロー

    rect rgb(240, 255, 240)
        Note right of EdgeSync: 1. 同期APIリクエスト
        EdgeSync->>AuthHTTPClient: POST /api/v1/sync/request<br/>Authorization: Bearer {expired_token}
        activate AuthHTTPClient

        AuthHTTPClient->>CloudSync: POST /api/v1/sync/request<br/>Authorization: Bearer {expired_token}
        activate CloudSync
    end

    rect rgb(255, 250, 240)
        Note right of CloudSync: 2. JWT検証失敗
        CloudSync->>CloudSync: JWT検証<br/>decode(token, JWT_SECRET_KEY)

        Note over CloudSync: ❌ TokenExpiredError<br/>exp: 1697356800 (過去)<br/>now: 1697360400

        CloudSync-->>AuthHTTPClient: 401 Unauthorized<br/>{<br/> "error_code": "800402",<br/> "message": "Token expired",<br/> "timestamp": "2025-10-15T11:00:00Z"<br/>}
        deactivate CloudSync
    end

    rect rgb(240, 245, 255)
        Note right of AuthHTTPClient: 3. 401エラー検出
        AuthHTTPClient->>AuthHTTPClient: status_code == 401<br/>→ 再認証が必要

        Note over AuthHTTPClient: ⚠️ トークン期限切れ検出<br/>自動再認証開始
    end

    rect rgb(255, 255, 240)
        Note right of AuthHTTPClient: 4. 再認証実行
        AuthHTTPClient->>TokenManager: reauthenticate()
        activate TokenManager

        TokenManager->>CloudSync: POST /api/v1/sync/auth<br/>{<br/> "edge_id": "edge-tenant001-store001-001",<br/> "secret": "plain_secret_value"<br/>}
        activate CloudSync

        CloudSync->>CloudSync: 認証処理

        CloudSync-->>TokenManager: 200 OK<br/>{<br/> "access_token": "eyJhbGciOi...",<br/> "expires_in": 86400<br/>}
        deactivate CloudSync

        TokenManager->>TokenManager: 新トークン保存

        TokenManager-->>AuthHTTPClient: ✅ 再認証成功<br/>new_token: "eyJhbGciOi..."
        deactivate TokenManager
    end

    rect rgb(240, 255, 240)
        Note right of AuthHTTPClient: 5. 元のリクエストをリトライ
        AuthHTTPClient->>CloudSync: POST /api/v1/sync/request<br/>Authorization: Bearer {new_token}
        activate CloudSync

        CloudSync->>CloudSync: JWT検証<br/>✅ トークン有効

        CloudSync-->>AuthHTTPClient: 200 OK<br/>{<br/> "sync_data": {...}<br/>}
        deactivate CloudSync

        AuthHTTPClient-->>EdgeSync: 200 OK<br/>{<br/> "sync_data": {...}<br/>}
        deactivate AuthHTTPClient

        Note over EdgeSync: ✅ リクエスト成功<br/>（ユーザーは再認証を意識しない）
    end

    alt 再認証失敗（3回リトライ）
        Note over AuthHTTPClient: ❌ 再認証失敗<br/>retry_count: 3

        AuthHTTPClient-->>EdgeSync: Exception: ReauthenticationFailed<br/>error_code: 800403

        Note over EdgeSync: エラーログ記録<br/>管理者通知<br/>サービス停止
    end
```

**自動再認証HTTP Client実装例（Edge Side）**:

```python
import httpx
from typing import Optional
from datetime import datetime

class AuthenticatedHTTPClient:
    """HTTP client with automatic reauthentication"""

    def __init__(self, token_manager: TokenManager, base_url: str):
        self.token_manager = token_manager
        self.base_url = base_url
        self.max_retries = 3

    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """POST request with automatic reauthentication"""
        return await self._request("POST", endpoint, **kwargs)

    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """GET request with automatic reauthentication"""
        return await self._request("GET", endpoint, **kwargs)

    async def _request(
        self,
        method: str,
        endpoint: str,
        retry_count: int = 0,
        **kwargs
    ) -> httpx.Response:
        """Execute HTTP request with auto-reauthentication"""
        # トークン取得
        token_data = await self.token_manager.repository.get_token()

        if not token_data:
            raise ValueError("No authentication token available")

        # Authorizationヘッダー追加
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token_data['access_token']}"

        # リクエスト実行
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}{endpoint}"
            response = await client.request(method, url, headers=headers, **kwargs)

            # 401エラー検出
            if response.status_code == 401:
                logger.warning(
                    f"401 Unauthorized detected, reauthenticating...",
                    extra={
                        "endpoint": endpoint,
                        "retry_count": retry_count
                    }
                )

                if retry_count >= self.max_retries:
                    logger.error(
                        f"Reauthentication failed after {self.max_retries} retries"
                    )
                    raise ReauthenticationFailedError(
                        f"Failed to reauthenticate after {self.max_retries} attempts"
                    )

                # 再認証実行
                await self.token_manager.authenticate()

                # 指数バックオフ
                await asyncio.sleep(2 ** retry_count)

                # リトライ
                return await self._request(
                    method,
                    endpoint,
                    retry_count=retry_count + 1,
                    **kwargs
                )

            return response
```

## フロー4: JWT検証（Cloud Side）

**シナリオ**: クラウド側で受信したリクエストのJWT トークンを検証し、テナント分離を保証。

```mermaid
sequenceDiagram
    participant EdgeSync as Edge Sync Service
    participant CloudSync as Cloud Sync Service
    participant JWTMiddleware as JWT Middleware
    participant CloudDB as MongoDB<br/>(sync_tenant001)

    Note over EdgeSync,CloudDB: 🔒 JWT検証とテナント分離

    rect rgb(240, 255, 240)
        Note right of EdgeSync: 1. 認証済みリクエスト
        EdgeSync->>CloudSync: POST /api/v1/sync/request<br/>Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...<br/>{<br/> "data_type": "master_data"<br/>}
        activate CloudSync
    end

    rect rgb(255, 250, 240)
        Note right of CloudSync: 2. JWT検証（Middleware）
        CloudSync->>JWTMiddleware: verify_jwt(token)
        activate JWTMiddleware

        JWTMiddleware->>JWTMiddleware: JWT decode<br/>jwt.decode(<br/> token,<br/> JWT_SECRET_KEY,<br/> algorithms=["HS256"]<br/>)

        alt トークン有効
            JWTMiddleware->>JWTMiddleware: ペイロード抽出<br/>{<br/> "edge_id": "edge-tenant001-store001-001",<br/> "tenant_id": "tenant001",<br/> "store_code": "store001",<br/> "exp": 1697356800,<br/> "iat": 1697270400<br/>}

            Note over JWTMiddleware: ✅ 署名検証成功<br/>✅ 有効期限内<br/>exp > now

            JWTMiddleware-->>CloudSync: ペイロード返却
            deactivate JWTMiddleware
        else トークン期限切れ
            JWTMiddleware-->>CloudSync: ❌ TokenExpiredError
            deactivate JWTMiddleware

            CloudSync-->>EdgeSync: 401 Unauthorized<br/>{<br/> "error_code": "800402",<br/> "message": "Token expired"<br/>}
            deactivate CloudSync
        else 署名不一致
            JWTMiddleware-->>CloudSync: ❌ InvalidSignatureError
            deactivate JWTMiddleware

            CloudSync-->>EdgeSync: 401 Unauthorized<br/>{<br/> "error_code": "800404",<br/> "message": "Invalid token signature"<br/>}
            deactivate CloudSync
        end
    end

    rect rgb(240, 245, 255)
        Note right of CloudSync: 3. テナント分離
        CloudSync->>CloudSync: テナント別DB取得<br/>db = get_database(tenant_id="tenant001")<br/>→ sync_tenant001

        Note over CloudSync: ✅ テナントID検証完了<br/>クロステナントアクセス防止
    end

    rect rgb(255, 255, 240)
        Note right of CloudSync: 4. ビジネスロジック実行
        CloudSync->>CloudDB: SELECT FROM cache_master_data<br/>WHERE tenant_id = "tenant001"
        activate CloudDB
        CloudDB-->>CloudSync: マスターデータ
        deactivate CloudDB

        CloudSync-->>EdgeSync: 200 OK<br/>{<br/> "sync_data": {...}<br/>}
        deactivate CloudSync
    end
```

**JWT検証実装例（Cloud Side）**:

```python
from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def verify_jwt_token(
    authorization: str = Header(...)
) -> dict:
    """Verify JWT token and return payload"""
    # Bearerスキーム確認
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication scheme"
        )

    token = authorization.replace("Bearer ", "")

    try:
        # JWT decode
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        # 有効期限確認（joseが自動的にチェックするが明示的にも確認）
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=401,
                detail="Token expired"
            )

        logger.debug(
            f"JWT verified successfully",
            extra={
                "edge_id": payload.get("edge_id"),
                "tenant_id": payload.get("tenant_id")
            }
        )

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )
    except jwt.JWTError as e:
        logger.warning(f"JWT verification failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

# FastAPI依存性注入での使用例
@router.post("/api/v1/sync/request")
async def sync_request(
    request: SyncRequestSchema,
    payload: dict = Depends(verify_jwt_token)
):
    """Sync request endpoint with JWT authentication"""
    tenant_id = payload["tenant_id"]
    edge_id = payload["edge_id"]

    # テナント別DB取得
    db = get_database(tenant_id)

    # ビジネスロジック実行...
```

## 受入シナリオ検証

### シナリオ1: 有効なedge_idとsecret、認証API呼び出し、24時間有効なJWT トークンを取得

**前提条件**:
- EdgeTerminal登録済み: `edge-tenant001-store001-001`
- secret（ハッシュ化）: `abc123...def`（SHA-256）

**検証手順**:
1. Edge Sync起動時に認証API呼び出し
2. edge_id + plain secret送信
3. Cloud Syncがsecret検証（ハッシュ比較）
4. JWT トークン生成（有効期限: 24時間）
5. Edge Syncがトークン保存

**期待結果**:
- HTTPステータス: 200 OK
- access_token: JWT文字列（HS256アルゴリズム）
- expires_in: 86400秒（24時間）
- tenant_id, edge_id, store_code が含まれる
- JWT認証成功率: 99.9%以上（SC-013）

### シナリオ2: 無効なsecret、認証API呼び出し、401 Unauthorizedエラー

**前提条件**:
- 誤ったsecretを使用

**検証手順**:
1. Edge Syncが誤ったsecretで認証リクエスト
2. Cloud Syncがハッシュ検証失敗
3. 401エラー返却

**期待結果**:
- HTTPステータス: 401 Unauthorized
- error_code: "800401"
- message: "Invalid credentials"
- トークン発行されない
- エラーログ記録（WARNING レベル）

### シナリオ3: JWT トークン取得済み、同期APIにアクセス、トークンをAuthorizationヘッダーに付与してアクセス成功

**前提条件**:
- 有効なJWT トークン取得済み

**検証手順**:
1. Edge Syncが同期APIリクエスト
2. Authorization: Bearer {token} ヘッダー付与
3. Cloud SyncがJWT検証
4. ビジネスロジック実行

**期待結果**:
- HTTPステータス: 200 OK
- JWT検証成功
- テナント別DB（sync_tenant001）にアクセス
- クロステナントアクセス防止

### シナリオ4: JWT トークンの有効期限切れ、同期APIにアクセス、401エラーで再認証要求

**前提条件**:
- トークン有効期限切れ（exp < now）

**検証手順**:
1. Edge Syncが期限切れトークンで同期APIリクエスト
2. Cloud SyncがJWT検証失敗（TokenExpiredError）
3. 401エラー返却
4. AuthenticatedHTTPClientが401検出
5. 自動再認証実行
6. 新トークン取得
7. 元のリクエストをリトライ

**期待結果**:
- 初回リクエスト: 401 Unauthorized
- 自動再認証成功
- リトライリクエスト: 200 OK
- ユーザーは再認証を意識しない（透過的）
- トークン自動更新成功率: 99.5%以上（SC-016）
- トークン期限切れによる同期遅延: 30秒以内（SC-017）

## パフォーマンス指標

| 指標 | 目標値 | 測定方法 |
|-----|-------|---------|
| **JWT認証成功率** | 99.9%以上 | 成功回数 / 全認証試行回数 |
| **JWT発行時間** | 100ms以内 | 認証リクエスト → レスポンス時間 |
| **JWT検証時間** | 10ms以内 | jwt.decode実行時間 |
| **トークン自動更新成功率** | 99.5%以上 | 更新成功回数 / 全更新試行回数 |
| **トークン期限切れによる同期遅延** | 30秒以内 | 401検出 → 再認証完了までの時間 |
| **再認証失敗時のアラート送信** | 5秒以内 | 再認証失敗 → 管理者通知送信時間 |
| **SHA-256ハッシュ計算時間** | 1ms以内 | hashlib.sha256実行時間 |

## セキュリティ考慮事項

### シークレット管理

**保存方法**:
- **クラウド側**: SHA-256ハッシュのみ保存（64文字hex）
- **エッジ側**: 平文は環境変数のみ、メモリ上で使用、永続化しない

**環境変数例**:
```bash
# Edge環境（.env）
EDGE_ID=edge-tenant001-store001-001
EDGE_SECRET=your_plain_secret_value_here

# Cloud環境（.env）
JWT_SECRET_KEY=your_jwt_secret_key_here_at_least_32_chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

### JWT セキュリティ

- **アルゴリズム**: HS256（HMAC with SHA-256）
- **署名キー**: 最低32文字、環境変数で管理
- **有効期限**: 24時間（環境変数で調整可能）
- **ペイロード**: テナントID、エッジID、店舗コードを含む
- **検証**: すべてのAPI呼び出しで検証実施

### 監査ログ

**記録対象**:
- 認証成功・失敗（edge_id, timestamp, result）
- トークン発行（edge_id, tenant_id, expires_at）
- トークン更新（edge_id, old_expires_at, new_expires_at）
- 401エラー発生（edge_id, endpoint, timestamp）
- 再認証成功・失敗（edge_id, retry_count, result）

**ログ例**:
```json
{
  "level": "INFO",
  "timestamp": "2025-10-14T10:00:00Z",
  "service": "sync",
  "event_type": "authentication",
  "edge_id": "edge-tenant001-store001-001",
  "tenant_id": "tenant001",
  "result": "success",
  "token_expires_at": "2025-10-15T10:00:00Z"
}
```

## まとめ

User Story 6（エッジ端末の認証とセキュリティ）は、以下の4つの主要フローで構成されます:

1. **初回認証（edge_id + secret）**: サービス起動時の認証、JWT トークン発行（24時間有効）
2. **トークン自動更新（有効期限1時間前）**: APSchedulerによる定期チェック（5分間隔）、プロアクティブ更新
3. **401エラー時の自動再認証**: AuthenticatedHTTPClientによる透過的な再認証、指数バックオフでリトライ
4. **JWT検証（Cloud Side）**: すべてのAPIでJWT検証、テナント分離保証

**主要な設計ポイント**:
- **SHA-256ハッシュ化**: secretはハッシュ化してクラウドに保存、平文は環境変数のみ
- **JWT トークンベース**: HS256アルゴリズム、24時間有効期限
- **プロアクティブ更新**: 有効期限1時間前に自動更新、期限切れを未然に防止
- **透過的な再認証**: 401エラー時に自動的に再認証、ユーザーは意識不要
- **テナント分離**: JWT ペイロードのtenant_idでデータベースアクセス制御
- **包括的監査ログ**: すべての認証イベントを記録、セキュリティ監視

この機能により、エッジ端末とクラウド間のセキュアな通信が確立され、すべての同期機能の基盤となります。

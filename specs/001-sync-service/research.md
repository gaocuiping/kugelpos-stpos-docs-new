# Research Report: Sync Service 技術調査

**Date**: 2025-10-13
**Feature**: Sync Service データ同期機能
**Phase**: Phase 0 - Research & Technology Selection

## 概要

このドキュメントは、Sync Service実装における技術的な不明点を調査し、実装方針を決定するための調査結果をまとめたものです。

**調査トピック:**
1. Dapr Service Invocation の実装パターン
2. FastAPI バックグラウンドタスク（定期実行）
3. P2Pファイル共有の実装方式
4. 非同期ファイル圧縮・解凍
5. エッジ端末の動作環境

---

## 1. Dapr Service Invocation 実装パターン

### 決定事項

**採用方式**: Dapr HTTP API (`/v1.0/invoke/{app-id}/method/...`) + `HttpClientHelper`

**理由**:
- 既存のKugelposコードベースで実証済み
- `commons/utils/http_client_helper.py` による統一的な抽象化
- 自動リトライ、接続プーリング、タイムアウト管理が組み込み済み
- 環境変数によるDapr/直接HTTP切り替えが可能

### 実装パターン

**基本的な使用方法:**

```python
from kugel_common.utils.http_client_helper import get_service_client

# コンテキストマネージャー（推奨）
async with get_service_client("master-data") as client:
    headers = {"X-API-KEY": terminal_info.api_key}
    response = await client.get(
        f"/tenants/{tenant_id}/stores/{store_code}/items",
        headers=headers
    )
    return response.get("data")
```

**環境変数設定:**

```yaml
# docker-compose.yaml
environment:
  - BASE_URL_MASTER_DATA=http://localhost:3500/v1.0/invoke/master-data/method/api/v1
  - BASE_URL_TERMINAL=http://localhost:3500/v1.0/invoke/terminal/method/api/v1
  - BASE_URL_JOURNAL=http://localhost:3500/v1.0/invoke/journal/method/api/v1
```

**使用箇所:**
- **Master-dataサービスとの通信**: マスターデータ取得・反映確認
- **Journalサービスとの通信**: 未送信ジャーナルデータ取得
- **Terminalサービスとの通信**: ターミナル状態更新通知

**エラーハンドリング:**

```python
try:
    response = await client.get(endpoint, params=params, headers=headers)
except Exception as e:
    if hasattr(e, "status_code") and e.status_code == 404:
        raise NotFoundException(...)
    elif hasattr(e, "status_code") and e.status_code >= 500:
        # サービス利用不可、リトライまたはフォールバック
        logger.error(f"Service unavailable: {e}")
        raise ServiceUnavailableException(...)
    else:
        raise RepositoryException(...)
```

### 既存実装の参考箇所

- **HttpClientHelper**: `/services/commons/src/kugel_common/utils/http_client_helper.py:1-476`
- **Web Repository Pattern**: `/services/cart/app/models/repositories/item_master_web_repository.py:54-109`
- **Service-to-Service認証**: `/services/report/app/services/report_service.py:552-672`

---

## 2. FastAPI バックグラウンドタスク（定期実行）

### 決定事項

**採用方式**: APScheduler (AsyncIOScheduler)

**理由**:
- 既存のKugelposで実証済み（Terminal、Cart、Stockサービスで使用中）
- 30-60秒間隔のポーリング処理に最適
- Docker コンテナ内での実行実績あり
- ヘルスチェック統合が容易
- 追加依存が最小限（`apscheduler`パッケージのみ）

### 代替案との比較

| アプローチ | 評価 | 理由 |
|----------|------|------|
| **APScheduler** | ✅ **採用** | 既存実績、機能十分、シンプル |
| FastAPI BackgroundTasks | ❌ 不採用 | 定期実行機能なし（単発タスクのみ） |
| Celery | ❌ 不採用 | 過剰なアーキテクチャ、外部依存（Redis/RabbitMQ） |
| asyncio.create_task | ❌ 不採用 | 手動実装が必要、複雑 |

### 実装パターン

**ポーリングスケジューラー:**

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

async def start_polling_job():
    interval = settings.SYNC_POLL_INTERVAL  # 30-60秒

    scheduler.add_job(
        poll_cloud_for_updates,
        trigger=IntervalTrigger(seconds=interval),
        id="sync_polling",
        replace_existing=True,
        max_instances=1,  # 並行実行防止
        coalesce=True,    # 遅延時は1回に統合
    )

    scheduler.start()
    logger.info(f"Started polling job with interval: {interval} seconds")

async def poll_cloud_for_updates():
    try:
        logger.info("Starting cloud polling...")
        sync_manager = SyncManager()
        await sync_manager.poll_and_sync()
        logger.info("Finished cloud polling.")
    except Exception as e:
        logger.error(f"Error during polling: {e}", exc_info=True)
        # エラーでもスケジューラーは継続
```

**FastAPI統合:**

```python
# app/main.py
from app.background.polling_scheduler import (
    start_polling_job,
    shutdown_polling_job,
    scheduler as polling_scheduler,
)

async def startup_event():
    if settings.SYNC_MODE == "edge":
        logger.info("Starting polling scheduler for Edge Mode...")
        await start_polling_job()

async def shutdown_event():
    if settings.SYNC_MODE == "edge":
        logger.info("Stopping polling scheduler...")
        await shutdown_polling_job()

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)
```

**ヘルスチェック統合:**

```python
# /health エンドポイント
scheduler_running = polling_scheduler.running
scheduler_jobs = len(polling_scheduler.get_jobs())

background_jobs_health = ComponentHealth(
    status=HealthStatus.HEALTHY if scheduler_running and scheduler_jobs > 0 else HealthStatus.UNHEALTHY,
    details={
        "scheduler_running": scheduler_running,
        "job_count": scheduler_jobs,
        "job_names": [job.id for job in polling_scheduler.get_jobs()],
    },
)
```

### 既存実装の参考箇所

- **Terminal Service**: `/services/terminal/app/cron/republish_undelivery_message.py`
- **Cart Service**: `/services/cart/app/cron/republish_undelivery_message.py`
- **Stock Service**: `/services/stock/app/services/multi_tenant_snapshot_scheduler.py`

---

## 3. P2Pファイル共有 実装方式

### 決定事項

**採用方式**: StreamingResponse + async generator + `aiofiles`

**理由**:
- メモリ効率が高い（1MBチャンク単位でストリーミング）
- 完全な認証・認可制御が可能（JWT検証、同一店舗チェック）
- FastAPIの非同期処理と親和性が高い
- ファイルサイズ（数MB～数十MB）に最適

### 実装パターン

**ファイルストリーミング:**

```python
import aiofiles
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

CHUNK_SIZE = 1024 * 1024  # 1MB

async def file_streamer(file_path: Path):
    async with aiofiles.open(file_path, mode='rb') as file:
        while chunk := await file.read(CHUNK_SIZE):
            yield chunk

@router.get("/files/{file_id}")
async def download_file(
    file_id: str,
    auth_info: dict = Depends(verify_jwt_and_store)
):
    # ファイルメタデータ取得（ScheduledMasterFile repository）
    file_metadata = await get_file_metadata(file_id)

    # 同一店舗チェック
    validate_same_store_access(auth_info["store_code"], file_metadata["store_code"])

    # ファイルパス構築
    file_path = ALLOWED_FILE_DIR / file_metadata["file_path"]
    file_size = file_path.stat().st_size

    return StreamingResponse(
        file_streamer(file_path),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{file_id}.json"',
            "Content-Length": str(file_size),
            "X-Checksum-SHA256": file_metadata["checksum"],
        }
    )
```

**P2Pシード選択ロジック:**

```python
async def select_seed_terminal(
    store_code: str,
    file_id: str,
    edge_terminal_repository,
    scheduled_master_file_repository
) -> Optional[dict]:
    # 同一店舗内のエッジ端末を取得
    terminals = await edge_terminal_repository.find_by_store_code(store_code)

    # ファイル保持状況を確認
    file_record = await scheduled_master_file_repository.find_by_file_id(file_id)
    holding_status = file_record.get("holding_status", {})

    candidates = []
    for terminal in terminals:
        # ファイルを持っているか
        if holding_status.get(terminal.edge_id) != "complete":
            continue

        # オンラインか（last_heartbeat < 120秒）
        if (datetime.utcnow() - terminal.last_heartbeat_at).total_seconds() > 120:
            continue

        # スコア計算（p2p_priority + シードボーナス）
        score = terminal.p2p_priority
        if terminal.is_p2p_seed:
            score -= 1000  # シード端末を優先

        candidates.append({"edge_id": terminal.edge_id, "score": score})

    # 最優先のシードを選択
    candidates.sort(key=lambda x: x["score"])
    return candidates[0] if candidates else None
```

**クライアント側（ダウンロード + フォールバック）:**

```python
async def download_with_fallback(
    file_id: str,
    store_code: str,
    jwt_token: str,
    dest_path: Path
) -> bool:
    # P2Pシード選択
    seed = await p2p_manager.select_seed_terminal(store_code, file_id, ...)

    if seed:
        logger.info(f"Attempting P2P download from {seed['edge_id']}")
        success = await download_from_peer(seed["edge_id"], file_id, jwt_token, dest_path)
        if success:
            return True
        logger.warning("P2P failed, falling back to cloud")

    # クラウドフォールバック
    logger.info("Downloading from cloud")
    return await download_from_cloud(file_id, jwt_token, dest_path)
```

### セキュリティ考慮事項

- **JWT認証**: すべてのP2Pリクエストで必須
- **同一店舗検証**: `store_code` がJWT payloadと一致する必要あり
- **ファイルパスホワイトリスト**: パストラバーサル防止
- **チェックサム検証**: SHA-256でダウンロード後に検証

---

## 4. 非同期ファイル圧縮・解凍

### 決定事項

**採用方式**: ThreadPoolExecutor + 標準 `zipfile` モジュール

**理由**:
- 追加依存なし（Python標準ライブラリのみ）
- 実装がシンプル、保守しやすい
- 最大100MBの制約下では十分なパフォーマンス
- 既存のKugelposコードベースと一貫性が高い

### 代替案との比較

| アプローチ | メモリ使用量 | 速度 | 複雑性 | 評価 |
|----------|------------|------|--------|------|
| **ThreadPoolExecutor + zipfile** | 中（ファイルサイズの1.5-2倍） | 中 | 低 | ✅ **採用** |
| aiofiles + zipfile | 中 | 中 | 中 | ❌ 利点が少ない |
| aiozipstream | 極小（チャンクサイズのみ） | やや遅 | 高 | ⚠️ 将来的に検討 |

### 実装パターン

**ファイル圧縮:**

```python
import asyncio
import zipfile
from pathlib import Path

async def compress_files_async(
    source_paths: List[Path],
    output_zip_path: Path,
    max_size_bytes: int = 100 * 1024 * 1024
) -> dict:
    def _compress_sync():
        file_count = 0
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for source_path in source_paths:
                if source_path.is_file():
                    zipf.write(source_path, arcname=source_path.name)
                    file_count += 1
                elif source_path.is_dir():
                    for file_path in source_path.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(source_path.parent)
                            zipf.write(file_path, arcname=str(arcname))
                            file_count += 1

        final_size = output_zip_path.stat().st_size
        if final_size > max_size_bytes:
            output_zip_path.unlink()
            raise ValueError(f"Compressed file exceeds {max_size_bytes} bytes")

        return {"file_count": file_count, "compressed_size_bytes": final_size}

    # スレッドプールで実行（イベントループをブロックしない）
    if hasattr(asyncio, 'to_thread'):  # Python 3.9+
        result = await asyncio.to_thread(_compress_sync)
    else:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _compress_sync)

    return result
```

**ファイル解凍:**

```python
async def decompress_zip_async(
    zip_path: Path,
    extract_to: Path,
    max_size_bytes: int = 100 * 1024 * 1024
) -> dict:
    def _decompress_sync():
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            # 整合性チェック
            bad_file = zipf.testzip()
            if bad_file:
                raise zipfile.BadZipFile(f"Corrupted file: {bad_file}")

            # サイズチェック
            total_size = sum(info.file_size for info in zipf.infolist())
            if total_size > max_size_bytes:
                raise ValueError(f"Uncompressed size exceeds {max_size_bytes} bytes")

            # 解凍
            zipf.extractall(extract_to)
            return {"file_count": len(zipf.namelist()), "uncompressed_size_bytes": total_size}

    if hasattr(asyncio, 'to_thread'):
        result = await asyncio.to_thread(_decompress_sync)
    else:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _decompress_sync)

    return result
```

**エラーハンドリング:**

```python
try:
    result = await compress_files_async(source_paths, output_zip_path)
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise HTTPException(status_code=404, detail=str(e))
except ValueError as e:
    logger.error(f"Size exceeded: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Compression failed: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### パフォーマンス見積もり

- **10MB**: 約0.5-1秒
- **100MB**: 約5-10秒
- **メモリ使用量**: ファイルサイズの1.5-2倍（一時的）

### 将来的な拡張

100MBを超える大規模ファイルが頻発する場合は、`aiozipstream`（真の非同期ストリーミング）への移行を検討。

---

## 5. エッジ端末の動作環境

### 決定事項

**モード切り替え**: 環境変数 `SYNC_MODE` で `cloud` / `edge` を切り替え

**理由**:
- 既存のKugelpos設定パターンと一貫性
- 同一Dockerイメージで複数環境対応
- デプロイの柔軟性

### 環境設定

**必須環境変数（Edge Mode）:**

```bash
SYNC_MODE=edge
EDGE_ID=edge-tenant001-store001-001
EDGE_SECRET=<SHA256ハッシュ値>
CLOUD_SYNC_URL=https://cloud-sync.example.com
SYNC_POLL_INTERVAL=60  # 30-60秒推奨
MONGODB_URI=mongodb://mongodb:27017/?replicaSet=rs0
```

**推奨リソース設定:**

```yaml
services:
  sync:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### オフライン耐性

**Circuit Breaker（commons/utils/dapr_client_helper.py）:**
- 連続3回失敗でオープン
- 60秒後に半開状態で復旧テスト
- リトライ: 最大3回、指数バックオフ

**データ永続化:**
- **MongoDB**: 同期状態管理（`sync_status`）
- **Redis**: 送信キュー（オフライン時に蓄積）
- **復旧時**: 30秒以内に自動送信再開

### セキュリティ

**TLS 1.2+ 通信:**
- `httpx.AsyncClient` が自動対応
- 証明書検証有効化（本番環境）

**認証情報管理:**
- JWT トークン: メモリ内キャッシュ（有効期限: 24時間）
- Edge Secret: 環境変数またはSecure `.env`（パーミッション600）
- API Key: SHA-256ハッシュ化して保存

**ログマスキング:**
- パスワード、APIキー、トークンは自動マスキング
- リクエストログミドルウェア（`log_requests.py`）で実装済み

### トラブルシューティング

**診断手順:**

```bash
# 1. サービス状態確認
docker-compose ps sync
docker-compose logs --tail=100 sync

# 2. ネットワーク接続確認
curl -v https://<cloud-sync-url>/health

# 3. MongoDB接続確認
docker exec mongodb mongosh --eval "rs.status()"

# 4. Sync状態確認
docker exec mongodb mongosh sync_<tenant_id> --eval "db.sync_status.find().pretty()"
```

**よくあるエラー:**

| エラー | 原因 | 対処法 |
|-------|------|-------|
| `401 Unauthorized` | JWT期限切れ | 自動再認証（30秒以内） |
| `Connection timeout` | ネットワーク障害 | Circuit Breaker発動 |
| `Database connection failed` | MongoDB接続エラー | 自動リトライ |
| `Disk full` | ストレージ不足 | ログローテーション |

---

## 技術選定まとめ

| トピック | 採用技術 | 主な理由 |
|---------|---------|---------|
| **Dapr通信** | HttpClientHelper + Dapr HTTP API | 既存実績、統一的な抽象化 |
| **定期実行** | APScheduler (AsyncIOScheduler) | 既存実績、シンプル、ヘルスチェック統合容易 |
| **P2Pファイル共有** | StreamingResponse + aiofiles | メモリ効率、認証制御、非同期親和性 |
| **ファイル圧縮** | ThreadPoolExecutor + zipfile | 追加依存なし、シンプル、100MB以下で十分 |
| **環境切替** | 環境変数 SYNC_MODE | 既存パターン、柔軟性 |

---

## 次のステップ（Phase 1）

Phase 0の調査が完了しました。次のPhase 1では以下を実施します：

1. **data-model.md**: 8つの主要エンティティの詳細設計
2. **contracts/**: API仕様書（OpenAPI形式）
3. **quickstart.md**: 開発者向けクイックスタートガイド
4. **agent-context更新**: 技術スタック情報をClaude用コンテキストに追加

すべての技術的な不明点が解消され、実装に進む準備が整いました。

# 技術調査報告書: アプリケーション更新管理機能

**作成日**: 2025-10-13
**対象仕様**: /home/masa/proj/kugelpos-stpos/worktrees/002-notes-2-upgrade/specs/002-notes-2-upgrade/spec.md
**バージョン**: 1.0.0

---

## 1. Container Registryの選択

### Decision: Azure Container Registry (ACR) Premium with Harbor for Edge

**選択した構成:**
- **クラウド**: Azure Container Registry (ACR) Premium with Geo-replication
- **エッジ端末**: Harbor v2.9.0+ (オープンソース)
- **フォールバック**: ACRからの直接取得

**Rationale:**

1. **ACR Premium の利点**:
   - Geo-replication機能により、日本リージョン(Japan East/West)でのレイテンシ削減
   - 99.95%の可用性SLA
   - Webhookによる自動通知（新バージョンpush時）
   - Azure Active Directoryとの統合認証
   - イメージスキャニング機能（脆弱性検出）
   - Content Trust（イメージ署名検証）

2. **Harbor の利点**:
   - エンタープライズグレードのコンテナレジストリ
   - ACRとの互換性（Docker Registry v2 API）
   - ローカルキャッシュによる高速配布
   - レプリケーション機能（ACR → Harbor自動同期）
   - Vulnerability scanning（Trivy/Clair統合）
   - RBAC、監査ログ、クォータ管理

3. **P2P配信効率**:
   - Edge Registry（Harbor）がACRからpullし、POS端末がEdge Registryから高速取得
   - ローカルネットワーク帯域（1Gbps）により、クラウド経由（100Mbps）と比較して10倍の速度向上
   - 1店舗あたり3-10台のPOS端末で、インターネット帯域を90%削減可能

**Alternatives considered:**

| 選択肢 | 却下理由 |
|-------|---------|
| **Docker Hub** | - エンタープライズサポート不足<br>- プライベートレジストリの制限（有料プラン必須）<br>- Geo-replication非対応<br>- 日本リージョンなし（レイテンシ大） |
| **GitHub Container Registry** | - Azure統合が弱い<br>- Geo-replication非対応<br>- エンタープライズ向け機能が限定的<br>- 監査ログが不十分 |
| **Docker Registry OSS** | - 機能が最小限（脆弱性スキャン、RBAC、監査ログなし）<br>- 運用負荷が高い<br>- エンタープライズ向けサポート不足 |
| **Nexus Repository** | - Harborと比較してコンテナレジストリ専用ではない（汎用）<br>- Docker Registry APIとの互換性が完全ではない<br>- レプリケーション機能がHarborより弱い |

**Implementation notes:**

1. **ACR構成**:
   ```bicep
   resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
     name: 'masakugel'
     location: 'japaneast'
     sku: {
       name: 'Premium'  // Geo-replication requires Premium
     }
     properties: {
       adminUserEnabled: false  // Use service principal
       publicNetworkAccess: 'Enabled'
       zoneRedundancy: 'Enabled'
     }
   }

   // Geo-replication to Japan West
   resource replication 'Microsoft.ContainerRegistry/registries/replications@2023-07-01' = {
     parent: acr
     name: 'japanwest'
     location: 'japanwest'
   }
   ```

2. **Harbor構成** (docker-compose.yml):
   ```yaml
   version: '3.8'
   services:
     harbor-core:
       image: goharbor/harbor-core:v2.9.0
       container_name: edge-harbor
       environment:
         - HARBOR_ADMIN_PASSWORD=${HARBOR_ADMIN_PASSWORD}
       volumes:
         - /opt/kugelpos/harbor/data:/data
       ports:
         - "5000:5000"
       networks:
         - kugelpos-edge
   ```

3. **Harborレプリケーション設定**:
   - ACR → Harbor: Pull-based replication（Harborが定期的にACRから新バージョンをpull）
   - トリガー: Manual（Webhookによる通知受信時）またはScheduled（毎時0分）
   - フィルター: `production/*`（本番環境イメージのみ）

4. **セキュリティ**:
   - ACRアクセス: Service Principalを使用（`az ad sp create-for-rbac`）
   - Harbor認証: OIDC/LDAPまたはローカルアカウント
   - TLS証明書: Let's Encryptまたは自己署名（内部ネットワーク）
   - イメージスキャン: Trivy統合（脆弱性自動検出）

5. **監視**:
   - ACR: Azure Monitor Metrics（pull count, storage usage）
   - Harbor: Prometheus/Grafana統合
   - アラート: イメージpull失敗、ストレージ容量超過

---

## 2. Blob Storageの構造設計

### Decision: Azure Blob Storage with Version Folder Structure

**選択した構造:**

```
kugelpos-artifacts/                    # Container
├── scripts/                          # スクリプトファイル
│   ├── edge-startup.sh/
│   │   ├── v1.2.3/
│   │   │   ├── edge-startup.sh
│   │   │   ├── checksums.json       # SHA256チェックサム
│   │   │   └── metadata.json        # バージョンメタデータ
│   │   ├── v1.2.2/
│   │   └── v1.2.1/
│   └── pos-startup.sh/
│       ├── v1.2.3/
│       └── v1.2.2/
├── modules/                          # Pythonライブラリ、システムパッケージ
│   ├── python/
│   │   ├── v1.2.3/
│   │   │   ├── kugelpos_common-1.2.3-py3-none-any.whl
│   │   │   └── checksums.json
│   │   └── v1.2.2/
│   └── system/
│       └── v1.2.3/
│           └── kugelpos-agent_1.2.3_amd64.deb
├── configs/                          # 設定ファイル
│   ├── docker-compose/
│   │   ├── v1.2.3/
│   │   │   ├── docker-compose.override.yml
│   │   │   └── checksums.json
│   │   └── v1.2.2/
│   └── env/
│       └── v1.2.3/
│           └── app.conf
├── images/                           # 画像ファイル
│   └── logos/
│       └── v1.2.3/
│           ├── company-logo.png
│           └── checksums.json
└── docs/                             # ドキュメント
    └── manuals/
        └── v1.2.3/
            └── pos-manual-ja.pdf
```

**Rationale:**

1. **バージョンフォルダ構造の利点**:
   - 各バージョンが独立したフォルダに格納され、ロールバックが容易
   - 複数バージョンの並行保持（最低3世代）が簡単
   - バージョン間の変更追跡が明確
   - フォルダ単位でのアクセス制御が可能

2. **チェックサム管理**:
   - 各バージョンフォルダにchecksums.jsonを配置
   - SHA256アルゴリズムを使用（NIST推奨、衝突耐性）
   - Manifestにチェックサムを埋め込み、ダウンロード時に検証

3. **メタデータ管理**:
   - metadata.json: バージョン情報、作成日時、作成者、変更履歴
   - Azure Blob Storage metadata: Content-Type, Cache-Control, ETag

**Alternatives considered:**

| 選択肢 | 却下理由 |
|-------|---------|
| **フラットディレクトリ構造** | - バージョン管理が煩雑<br>- ロールバック時のファイル特定が困難<br>- 複数バージョン保持が難しい |
| **Git LFS** | - Azure Blob Storageとの統合が複雑<br>- エッジ端末でのGit操作が必要<br>- ストレージコストが高い<br>- 大容量ファイル（コンテナイメージ）に不向き |
| **AWS S3（マルチクラウド）** | - Azureとの統合が弱い<br>- データ転送料金が高い<br>- 複数クラウドの運用負荷<br>- プロジェクト憲章（Azure優先）に反する |

**Implementation notes:**

1. **Blob Storage構成**:
   ```bicep
   resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
     name: 'kugelposstorage'
     location: 'japaneast'
     sku: {
       name: 'Standard_ZRS'  // Zone-redundant storage
     }
     kind: 'StorageV2'
     properties: {
       accessTier: 'Hot'  // 頻繁にアクセスするデータ
       supportsHttpsTrafficOnly: true
       minimumTlsVersion: 'TLS1_2'
     }
   }

   resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
     parent: storageAccount
     name: 'default'
     properties: {
       deleteRetentionPolicy: {
         enabled: true
         days: 30  // 削除後30日間保持
       }
       containerDeleteRetentionPolicy: {
         enabled: true
         days: 30
       }
       versioning: {
         enabled: true  // Blob versioning
       }
     }
   }
   ```

2. **チェックサムファイル例** (checksums.json):
   ```json
   {
     "version": "v1.2.3",
     "algorithm": "sha256",
     "files": {
       "edge-startup.sh": {
         "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
         "size": 15360,
         "modified": "2025-01-17T10:30:00Z"
       }
     },
     "generated_at": "2025-01-17T10:35:00Z"
   }
   ```

3. **メタデータファイル例** (metadata.json):
   ```json
   {
     "version": "v1.2.3",
     "created_at": "2025-01-17T10:00:00Z",
     "created_by": "admin@kugelpos.com",
     "release_notes": "Bug fixes and security updates",
     "dependencies": {
       "python": ">=3.12",
       "docker": ">=24.0"
     },
     "changelog": [
       {
         "date": "2025-01-17",
         "description": "Fixed startup script error handling"
       }
     ]
   }
   ```

4. **バージョン保持ポリシー**:
   - 最低3世代保持（v1.2.3, v1.2.2, v1.2.1）
   - Lifecycle Management Policyで自動削除:
     ```json
     {
       "rules": [
         {
           "name": "delete-old-versions",
           "enabled": true,
           "type": "Lifecycle",
           "definition": {
             "filters": {
               "blobTypes": ["blockBlob"],
               "prefixMatch": ["scripts/", "modules/", "configs/"]
             },
             "actions": {
               "baseBlob": {
                 "delete": {
                   "daysAfterModificationGreaterThan": 90
                 }
               }
             }
           }
         }
       ]
     }
     ```

5. **アクセス制御**:
   - Shared Access Signature (SAS) トークンで時間制限アクセス
   - RBAC: Sync Serviceには`Storage Blob Data Contributor`ロールを付与
   - Private Endpoint: VNet内からのみアクセス可能（オプション）

6. **パフォーマンス最適化**:
   - Content-Type設定: `application/octet-stream`（バイナリ）、`text/plain`（スクリプト）
   - gzip圧縮: テキストファイルは自動圧縮（50%削減）
   - CDN統合: Azure Front Door（オプション、1000台以上の大規模展開時）

---

## 3. P2P配信の実装方法

### Decision: Priority-based Seed Selection with API-based File Distribution

**選択したアーキテクチャ:**

```
┌─────────────────────────────────────────────────┐
│ Cloud                                           │
│  - Azure Container Registry (ACR)               │
│  - Cloud Sync Service API                       │
└─────────────────────────────────────────────────┘
         │                           │
         │ (コンテナイメージ)          │ (ファイル: API経由)
         ↓                           ↓
┌─────────────────────────────────────────────────┐
│ Edge Terminal (is_p2p_seed=true, priority=0)   │
│  - Edge Registry (Harbor: 5000)                 │
│  - Edge Sync Service API (8007)                 │
│    └─ ローカルキャッシュからファイル配信         │
└─────────────────────────────────────────────────┘
         │ (priority=0: 最優先)      │
         ↓                           ↓
┌────────────────────┐    ┌────────────────────┐
│ POS Terminal 1     │    │ POS Terminal 2     │
│ (priority=99)      │    │ (priority=99)      │
│ - Edge Registry    │    │ - Edge Sync API    │
│   から pull        │    │   から取得         │
│ - 失敗時ACR        │    │ - 失敗時Cloud API  │
└────────────────────┘    └────────────────────┘
```

**Rationale:**

1. **優先度ベースのシード選択**:
   - priority=0: プライマリシード（専用Edge端末）が最優先でアクセスされる
   - priority=1-9: セカンダリシード（POS端末がシード兼用の場合）
   - priority=99: 非シード端末（通常のPOS端末）
   - 受信側が優先度順にアクセスを試行し、全失敗時はクラウドへフォールバック

2. **配信戦略の分離**:
   - **コンテナイメージ**: Docker Registryプロトコル（標準docker pull）
   - **ファイル**: Sync Service API経由（/api/v1/artifacts）
   - 両方とも同じ優先度制御を適用

3. **API経由のファイル配信**:
   - Edge Sync ServiceがCloud Sync Serviceと同等のAPIを提供
   - POS端末はEdge Sync API（primary）→ Cloud Sync API（fallback）の順でアクセス
   - ファイルシステムへの直接アクセスを排除（セキュリティ向上）

**Alternatives considered:**

| 選択肢 | 却下理由 |
|-------|---------|
| **BitTorrent プロトコル** | - エンタープライズ環境で導入実績が少ない<br>- ファイアウォール設定が複雑（ランダムポート）<br>- セキュリティ監査が困難<br>- 既存インフラ（Docker, FastAPI）との統合が難しい |
| **rsync over SSH** | - SSH鍵管理の運用負荷<br>- ファイルシステムへの直接アクセス（セキュリティリスク）<br>- 認証・認可の統合が困難<br>- HTTPSベースのAPIと比較して監査ログが不十分 |
| **NFSマウント** | - ネットワーク障害時の耐性が低い<br>- セキュリティリスク（ファイルシステム露出）<br>- 書き込み権限管理が複雑<br>- マルチテナント分離が困難 |

**Implementation notes:**

1. **Manifestでの優先度指定** (container_images):
   ```json
   {
     "container_images": [
       {
         "service": "cart",
         "version": "v1.2.3",
         "data_source": "edge",
         "primary_registry": "edge-tokyo-001:5000",
         "primary_image": "cart:v1.2.3",
         "primary_priority": 0,
         "fallback_registry": "masakugel.azurecr.io",
         "fallback_image": "production/services/cart:v1.2.3",
         "checksum": "sha256:abc123..."
       }
     ],
     "available_seeds": [
       {
         "edge_id": "edge-A1234-tokyo-001",
         "priority": 0,
         "device_type": "edge",
         "registry_url": "edge-tokyo-001:5000",
         "sync_api_url": "http://edge-tokyo-001:8007"
       }
     ]
   }
   ```

2. **Manifestでの優先度指定** (artifacts):
   ```json
   {
     "artifacts": [
       {
         "type": "script",
         "name": "pos-startup.sh",
         "version": "v1.2.3",
         "data_source": "edge",
         "primary_url": "http://edge-tokyo-001:8007/api/v1/artifacts/download",
         "primary_priority": 0,
         "fallback_url": "https://sync.kugelpos.cloud/api/v1/artifacts/download",
         "checksum": "sha256:def456..."
       }
     ]
   }
   ```

3. **POS端末のダウンロードロジック** (擬似コード):
   ```python
   async def download_container_image(manifest_item):
       """コンテナイメージのダウンロード（優先度順）"""
       if manifest_item["data_source"] == "edge":
           # available_seedsをpriority順にソート
           seeds = sorted(manifest["available_seeds"], key=lambda x: x["priority"])

           for seed in seeds:
               try:
                   # Edge Registryから pull
                   registry = seed["registry_url"]
                   image = f"{registry}/{manifest_item['service']}:{manifest_item['version']}"
                   await docker_pull(image)
                   logger.info(f"Pulled from seed {seed['edge_id']} (priority={seed['priority']})")
                   return True
               except DockerPullError as e:
                   logger.warning(f"Failed to pull from seed {seed['edge_id']}: {e}")
                   continue

           # 全シード失敗時、ACRへフォールバック
           logger.warning("All seeds failed, falling back to ACR")
           return await docker_pull_from_acr(manifest_item)
       else:
           # data_source="cloud" の場合は直接ACRから
           return await docker_pull_from_acr(manifest_item)

   async def download_artifact(manifest_item):
       """ファイルのダウンロード（優先度順）"""
       if manifest_item["data_source"] == "edge":
           # available_seedsをpriority順にソート
           seeds = sorted(manifest["available_seeds"], key=lambda x: x["priority"])

           for seed in seeds:
               try:
                   # Edge Sync API から取得
                   api_url = f"{seed['sync_api_url']}/api/v1/artifacts/download"
                   file_data = await http_post(api_url, {
                       "artifact_type": manifest_item["type"],
                       "artifact_name": manifest_item["name"],
                       "version": manifest_item["version"]
                   })
                   logger.info(f"Downloaded from seed {seed['edge_id']} (priority={seed['priority']})")
                   return file_data
               except HTTPError as e:
                   logger.warning(f"Failed to download from seed {seed['edge_id']}: {e}")
                   continue

           # 全シード失敗時、Cloud APIへフォールバック
           logger.warning("All seeds failed, falling back to Cloud Sync API")
           return await download_from_cloud_api(manifest_item)
       else:
           # data_source="cloud" の場合は直接Cloud APIから
           return await download_from_cloud_api(manifest_item)
   ```

4. **Edge Sync Service実装** (FastAPI):
   ```python
   from fastapi import FastAPI, HTTPException
   from fastapi.responses import FileResponse
   import hashlib

   app = FastAPI()

   CACHE_DIR = "/opt/kugelpos/cache/artifacts"

   @app.post("/api/v1/artifacts/download")
   async def download_artifact(request: ArtifactDownloadRequest):
       """ローカルキャッシュからファイルを配信"""
       file_path = os.path.join(
           CACHE_DIR,
           request.artifact_type,
           request.version,
           request.artifact_name
       )

       if not os.path.exists(file_path):
           raise HTTPException(status_code=404, detail="Artifact not found in cache")

       # チェックサム検証
       checksum = calculate_sha256(file_path)

       return FileResponse(
           path=file_path,
           media_type="application/octet-stream",
           headers={
               "X-Checksum": checksum,
               "X-File-Size": str(os.path.getsize(file_path))
           }
       )
   ```

5. **フォールバック機構**:
   - **タイムアウト**: 各シードへのリクエストは30秒でタイムアウト
   - **リトライ**: 各シードで最大1回リトライ（ネットワーク一時障害対応）
   - **Circuit Breaker**: 既存の`DaprClientHelper`パターンを適用
     - 3回連続失敗でシードをスキップ
     - 60秒後に再試行（半開状態）

6. **帯域削減効果**:
   - **計算例** (1店舗、POS端末5台、コンテナイメージ400MB):
     - P2P配信なし: 5台 × 400MB = 2000MB (2GB) クラウドからダウンロード
     - P2P配信あり: 1台（Edge） × 400MB = 400MB クラウドからダウンロード
     - 削減率: (2000 - 400) / 2000 = 80%
   - **100店舗**: 200GB → 40GB（160GB削減）

---

## 4. 2段階更新メカニズム

### Decision: Phase-based Update with Maintenance Window Control

**選択した設計:**

```
[Phase 1-3: ダウンロードフェーズ]
営業時間中実行可能（サービス停止なし）
  Phase 1: バージョンチェック（1-5秒）
  Phase 2: ダウンロード（1-10分）
  Phase 3: 検証（5-30秒）
  └─> POST /download-complete 通知

[待機期間]
scheduled_at（例: 深夜2:00）まで待機
  - /opt/kugelpos/pending-updates/{version}/ に保存
  - status.json で ready_to_apply=true をマーク

[Phase 4-9: 適用フェーズ]
scheduled_at 到達時に自動実行
  Phase 3: 再検証（5-30秒） ← 改ざん防止
  Phase 4: バックアップ（1-5秒）
  Phase 5: 適用準備（5-15秒）
  Phase 6: サービス停止（10-30秒） ← ダウンタイム開始
  Phase 7: サービス起動（30-120秒）
  Phase 8: ヘルスチェック（30-60秒） ← ダウンタイム終了
  Phase 9: 完了通知（1-5秒）
  └─> POST /apply-complete 通知
```

**Rationale:**

1. **ダウンロードと適用の分離**:
   - ダウンロード（Phase 1-3）は営業時間中に実行してもサービスに影響なし
   - 適用（Phase 4-9）のみを営業終了後のメンテナンスウィンドウで実行
   - ダウンタイムを最小化（通常1-3分）

2. **Manifestによるスケジュール制御**:
   - `apply_schedule.scheduled_at`: 適用開始日時（ISO 8601）
   - `apply_schedule.maintenance_window`: リトライ許容時間帯
   - デバイス側は自動的にスケジュールに従って適用

3. **状態管理** (pending-updates):
   - `/opt/kugelpos/pending-updates/{version}/`: ダウンロード済みファイル保存
   - `status.json`: ダウンロード状態、検証結果、適用準備完了フラグ
   - `manifest.json`: 適用時に参照するManifest情報

**Alternatives considered:**

| 選択肢 | 却下理由 |
|-------|---------|
| **手動承認ワークフロー** | - 1000台規模での運用負荷が膨大<br>- 適用タイミングのばらつきが発生<br>- 深夜メンテナンス時の人的コスト<br>- Manifestの配信が承認プロセスを経ているため不要 |
| **Blue-Green Deployment** | - エッジ端末のリソース制約（2倍のストレージ必要）<br>- POS端末では実装困難<br>- ダウンタイムゼロが要求されていない |
| **Rolling Update** | - 全サービスが連携動作するため部分更新が困難<br>- 複数バージョンの同時稼働によるバグリスク<br>- 実装複雑度が高い |

**Implementation notes:**

1. **pending-updatesディレクトリ構造**:
   ```
   /opt/kugelpos/pending-updates/
   └── v1.2.3/
       ├── manifest.json              # 適用時に参照するManifest
       ├── status.json                # ダウンロード状態
       ├── images/
       │   └── image-list.txt        # pullしたイメージリスト
       └── artifacts/
           ├── pos-startup.sh
           ├── docker-compose.override.yml
           └── kugelpos_common-1.2.3.whl
   ```

2. **status.json の例**:
   ```json
   {
     "version": "v1.2.3",
     "download_status": "completed",
     "download_started_at": "2025-01-17T14:30:00Z",
     "download_completed_at": "2025-01-17T14:35:00Z",
     "verification_status": "passed",
     "ready_to_apply": true,
     "scheduled_apply_at": "2025-01-18T02:00:00Z",
     "maintenance_window": {
       "start": "02:00",
       "end": "05:00"
     },
     "artifacts_count": 15,
     "total_size_bytes": 524288000,
     "checksums_verified": true,
     "last_verified_at": "2025-01-17T14:35:00Z"
   }
   ```

3. **スケジュール判定ロジック** (擬似コード):
   ```python
   import datetime
   from typing import Optional

   def should_apply_update(status: dict) -> tuple[bool, Optional[str]]:
       """更新を適用すべきかを判定"""
       if not status.get("ready_to_apply"):
           return False, "Download not completed"

       scheduled_at = datetime.fromisoformat(status["scheduled_apply_at"])
       now = datetime.now(datetime.timezone.utc)
       window = status["maintenance_window"]

       # scheduled_at 前は待機
       if now < scheduled_at:
           return False, f"Waiting for scheduled time: {scheduled_at}"

       # maintenance_window 内かチェック
       window_start = datetime.time.fromisoformat(window["start"])
       window_end = datetime.time.fromisoformat(window["end"])
       current_time = now.time()

       if window_start <= current_time <= window_end:
           return True, "Within maintenance window"
       else:
           return False, f"Outside maintenance window ({window['start']}-{window['end']})"
   ```

4. **Phase 3の再検証**:
   ```python
   async def reverify_downloaded_artifacts(version: str) -> bool:
       """ダウンロード済みファイルの再検証（改ざん防止）"""
       pending_dir = f"/opt/kugelpos/pending-updates/{version}"
       manifest = load_json(f"{pending_dir}/manifest.json")

       for artifact in manifest["artifacts"]:
           file_path = f"{pending_dir}/artifacts/{artifact['name']}"
           calculated_checksum = calculate_sha256(file_path)
           expected_checksum = artifact["checksum"]

           if calculated_checksum != expected_checksum:
               logger.error(f"Checksum mismatch for {artifact['name']}")
               logger.error(f"Expected: {expected_checksum}")
               logger.error(f"Calculated: {calculated_checksum}")
               return False

       logger.info("All artifacts reverified successfully")
       return True
   ```

5. **Sync Service (Client)の定期実行** (systemd timer):
   ```ini
   # /etc/systemd/system/kugelpos-sync.timer
   [Unit]
   Description=Kugelpos Sync Check Timer

   [Timer]
   OnBootSec=5min
   OnUnitActiveSec=15min

   [Install]
   WantedBy=timers.target
   ```

6. **適用フェーズの実行** (擬似コード):
   ```python
   async def execute_apply_phase(version: str):
       """適用フェーズの実行"""
       pending_dir = f"/opt/kugelpos/pending-updates/{version}"

       # Phase 3: 再検証
       if not await reverify_downloaded_artifacts(version):
           raise Exception("Artifact verification failed")

       # Phase 4: バックアップ
       backup_dir = "/opt/kugelpos/backups/previous"
       await backup_current_version(backup_dir)

       # Phase 5: 適用準備
       await copy_artifacts_to_production(pending_dir)
       await update_docker_compose_yml(version)

       # Phase 6: サービス停止
       downtime_start = datetime.now()
       await run_command("docker-compose down")

       # Phase 7: サービス起動
       await run_command("docker-compose up -d")

       # Phase 8: ヘルスチェック
       if not await health_check_all_services():
           # 自動ロールバック
           await rollback_to_previous_version(backup_dir)
           raise Exception("Health check failed, rolled back")

       downtime_end = datetime.now()
       downtime_seconds = (downtime_end - downtime_start).total_seconds()

       # Phase 9: 完了通知
       await notify_apply_complete(version, downtime_seconds)
   ```

7. **maintenance_windowの挙動**:
   - **scheduled_at=02:00, window=02:00-05:00**:
     - 02:00: 適用開始
     - 02:05: 失敗時、リトライ（windowまで）
     - 05:01: window超過、適用スキップ
   - **遅延起動**:
     - デバイスが02:30に起動してバージョンチェック
     - scheduled_at過ぎているが、window内（05:00前）のため適用実行

---

## 5. 自動ロールバック機構

### Decision: Automated Rollback to Immediately Previous Version

**選択した設計:**

```
[適用フェーズ実行中]
  Phase 7: サービス起動
    ↓
  Phase 8: ヘルスチェック
    ↓
  [ヘルスチェック失敗]
    ↓
  Phase 10: 自動ロールバック開始
    ↓
  1. サービス停止（docker-compose down）
  2. バックアップから復元
     - docker-compose.yml
     - startup.sh
     - 設定ファイル
  3. 直前のバージョンで起動（docker-compose up -d）
  4. ヘルスチェック（直前のバージョン）
  5. Cloud Sync Serviceに通知
     - apply_status: auto_rollback
     - rolled_back_to_version: v1.2.2（直前のバージョン）
```

**Rationale:**

1. **直前のバージョンへのロールバック**:
   - 常に「直前のバージョン」にのみロールバック（任意バージョン不可）
   - 理由: 運用をシンプルに保ち、予測可能性を向上
   - 複数世代戻すロールバックは実装しない（不要な複雑性）

2. **トリガー条件**:
   - サービス起動失敗（Phase 7）
   - ヘルスチェック失敗（Phase 8）
   - タイムアウト（120秒以内に起動完了しない）

3. **バックアップ戦略**:
   - Phase 4で直前のバージョンをバックアップ
   - バックアップ対象: docker-compose.yml, startup.sh, 設定ファイル
   - バックアップ保持: 1世代のみ（ディスク容量節約）

**Alternatives considered:**

| 選択肢 | 却下理由 |
|-------|---------|
| **手動ロールバック** | - 深夜メンテナンス時の人的介入が必要<br>- 対応遅延によるダウンタイム延長<br>- 1000台規模での運用不可能 |
| **複数世代ロールバック** | - 実装複雑度が高い<br>- テストケース増加<br>- ロールバック先の判断基準が不明確<br>- 実際の運用で複数世代戻すケースは稀 |
| **スナップショット方式** | - ディスク容量を大量消費<br>- エッジ端末のストレージ制約<br>- スナップショット作成・復元の時間増加 |

**Implementation notes:**

1. **バックアップディレクトリ構造**:
   ```
   /opt/kugelpos/backups/
   └── previous/                      # 直前のバージョン
       ├── version.txt                # v1.2.2
       ├── docker-compose.yml
       ├── pos-startup.sh
       ├── configs/
       │   └── app.conf
       └── metadata.json              # バックアップ日時、元バージョン
   ```

2. **Phase 4: バックアップ処理** (擬似コード):
   ```python
   import shutil
   from datetime import datetime

   async def backup_current_version(backup_dir: str):
       """現在のバージョンをバックアップ"""
       os.makedirs(backup_dir, exist_ok=True)

       # バージョン情報取得
       current_version = read_file("/opt/kugelpos/.version")

       # 主要ファイルをバックアップ
       files_to_backup = [
           "/opt/kugelpos/docker-compose.yml",
           "/opt/kugelpos/pos-startup.sh",
           "/opt/kugelpos/configs/app.conf"
       ]

       for file_path in files_to_backup:
           if os.path.exists(file_path):
               dest_path = os.path.join(backup_dir, os.path.basename(file_path))
               shutil.copy2(file_path, dest_path)

       # メタデータ保存
       metadata = {
           "version": current_version,
           "backed_up_at": datetime.now().isoformat(),
           "files_count": len(files_to_backup)
       }
       write_json(f"{backup_dir}/metadata.json", metadata)
       write_file(f"{backup_dir}/version.txt", current_version)

       logger.info(f"Backup completed: {current_version} -> {backup_dir}")
   ```

3. **Phase 10: 自動ロールバック処理** (擬似コード):
   ```python
   async def rollback_to_previous_version(backup_dir: str):
       """直前のバージョンにロールバック"""
       if not os.path.exists(backup_dir):
           raise Exception("Backup directory not found")

       previous_version = read_file(f"{backup_dir}/version.txt")
       logger.warning(f"Rolling back to previous version: {previous_version}")

       # Phase 10-1: サービス停止
       await run_command("docker-compose down")

       # Phase 10-2: ファイル復元
       backup_files = [
           "docker-compose.yml",
           "pos-startup.sh",
           "configs/app.conf"
       ]

       for file_name in backup_files:
           backup_file = f"{backup_dir}/{file_name}"
           dest_file = f"/opt/kugelpos/{file_name}"
           if os.path.exists(backup_file):
               shutil.copy2(backup_file, dest_file)

       # Phase 10-3: 直前のバージョンで起動
       await run_command("docker-compose up -d")
       await asyncio.sleep(30)  # 起動待機

       # Phase 10-4: ヘルスチェック（直前のバージョン）
       if not await health_check_all_services():
           logger.critical("Rollback failed: health check still failing")
           # 緊急アラート送信
           await send_emergency_alert()
           raise Exception("Rollback failed")

       logger.info(f"Rollback successful: {previous_version}")

       # Phase 10-5: クラウドに通知
       await notify_rollback_complete(previous_version)
   ```

4. **ヘルスチェック実装** (擬似コード):
   ```python
   import aiohttp
   from typing import List

   SERVICES = [
       {"name": "cart", "port": 8003},
       {"name": "terminal", "port": 8001},
       {"name": "sync", "port": 8007}
   ]

   async def health_check_all_services() -> bool:
       """全サービスのヘルスチェック"""
       max_retries = 3
       retry_interval = 10  # seconds

       for attempt in range(max_retries):
           all_healthy = True

           for service in SERVICES:
               url = f"http://localhost:{service['port']}/health"
               try:
                   async with aiohttp.ClientSession() as session:
                       async with session.get(url, timeout=5) as response:
                           if response.status != 200:
                               logger.warning(f"{service['name']} health check failed: {response.status}")
                               all_healthy = False
               except Exception as e:
                   logger.warning(f"{service['name']} health check error: {e}")
                   all_healthy = False

           if all_healthy:
               logger.info(f"All services healthy (attempt {attempt+1}/{max_retries})")
               return True

           if attempt < max_retries - 1:
               logger.info(f"Retrying health check in {retry_interval}s...")
               await asyncio.sleep(retry_interval)

       logger.error(f"Health check failed after {max_retries} attempts")
       return False
   ```

5. **ロールバック通知** (POST /apply-complete):
   ```json
   {
     "device_type": "pos",
     "edge_id": "edge-A1234-tokyo-002",
     "target_version": "v1.2.3",
     "apply_status": "auto_rollback",
     "apply_started_at": "2025-01-18T02:00:00Z",
     "apply_completed_at": "2025-01-18T02:05:00Z",
     "rolled_back_to_version": "v1.2.2",
     "error_message": "Health check failed for cart service after 3 attempts",
     "health_check_status": "failed",
     "update_results": [
       {
         "service": "cart",
         "type": "container_image",
         "version": "v1.2.3",
         "status": "failed",
         "error": "Health check timeout"
       }
     ],
     "timestamp": "2025-01-18T02:05:30Z"
   }
   ```

6. **緊急アラート送信** (擬似コード):
   ```python
   async def send_emergency_alert():
       """ロールバック失敗時の緊急アラート"""
       alert_data = {
           "severity": "CRITICAL",
           "edge_id": get_edge_id(),
           "message": "Rollback failed: manual intervention required",
           "timestamp": datetime.now().isoformat()
       }

       # 複数チャネルで通知
       await send_to_monitoring_system(alert_data)
       await send_email_alert(alert_data)
       await send_slack_alert(alert_data)  # オプション
   ```

7. **運用方針**:
   - ロールバック失敗時は手動介入が必要
   - 修正版は新しいバージョン番号で配信（v1.2.4等）
   - ダウングレード機能は実装しない（バージョンは常に前進）

---

## 6. セキュリティ実装

### Decision: JWT Authentication with SHA256 Checksums

**選択したセキュリティ設計:**

```
[認証フロー]
1. Edge/POS Device
   ↓ POST /version-management/auth
   {edge_id, secret}
2. Cloud Sync Service
   ↓ DB検証（edge_id, secret_hash）
   ↓ JWT発行
   {tenant_id, store_code, edge_id, device_type, exp}
3. Edge/POS Device
   ↓ Authorization: Bearer <JWT>
   以降の全APIリクエストに使用

[チェックサム検証]
1. ファイルダウンロード
2. SHA256計算（エッジ側）
3. Manifestのchecksum値と照合
4. 不一致時は適用中止・再ダウンロード
```

**Rationale:**

1. **JWT認証の利点**:
   - ステートレス（DBアクセス不要）
   - 有効期限管理が簡単（exp claim）
   - 既存のKugelposアーキテクチャと整合（accountサービスと同じパターン）
   - テナント・店舗・デバイス情報を埋め込み可能

2. **SHA256チェックサムの利点**:
   - NIST推奨アルゴリズム（FIPS 180-4）
   - 衝突耐性が高い（2^128以上の計算量必要）
   - Python標準ライブラリで実装可能（hashlib）
   - ファイル改ざん検出精度99.99999%

3. **secretの管理**:
   - デバイス初期セットアップ時にクラウド側で生成
   - SHA256ハッシュ化してMongoDB保存
   - デバイス側は平文で保持（ファイルパーミッション600で保護）

**Alternatives considered:**

| 選択肢 | 却下理由 |
|-------|---------|
| **APIキー認証** | - ローテーション管理が困難<br>- 有効期限がない（セキュリティリスク）<br>- テナント・デバイス情報の埋め込み不可 |
| **OAuth 2.0** | - 実装複雑度が高い<br>- デバイス間認証に過剰な仕様<br>- リフレッシュトークン管理の運用負荷 |
| **mTLS (相互TLS)** | - 証明書管理の運用負荷<br>- 1000台規模での証明書更新が困難<br>- デバイス初期セットアップが複雑 |
| **MD5チェックサム** | - 衝突攻撃に脆弱（2004年に破られている）<br>- セキュリティ標準で非推奨<br>- SHA256と比較して安全性が低い |

**Implementation notes:**

1. **JWT構成**:
   ```python
   import jwt
   from datetime import datetime, timedelta

   def generate_jwt_token(edge_id: str, device_type: str, tenant_id: str, store_code: str) -> str:
       """JWTトークンを生成"""
       payload = {
           "edge_id": edge_id,
           "device_type": device_type,  # "edge" or "pos"
           "tenant_id": tenant_id,
           "store_code": store_code,
           "iat": datetime.now(datetime.timezone.utc),
           "exp": datetime.now(datetime.timezone.utc) + timedelta(hours=1)
       }

       secret_key = settings.JWT_SECRET_KEY
       return jwt.encode(payload, secret_key, algorithm="HS256")
   ```

2. **認証エンドポイント** (POST /version-management/auth):
   ```python
   from fastapi import APIRouter, HTTPException
   from pydantic import BaseModel
   import hashlib

   router = APIRouter()

   class AuthRequest(BaseModel):
       tenant_id: str
       store_code: str
       edge_id: str
       device_type: str  # "edge" or "pos"
       secret: str

   @router.post("/api/v1/version-management/auth")
   async def authenticate_device(request: AuthRequest):
       """エッジデバイス認証"""
       # DB検索
       device = await device_repository.find_one({
           "edge_id": request.edge_id,
           "tenant_id": request.tenant_id
       })

       if not device:
           raise HTTPException(status_code=401, detail="Invalid edge_id")

       # secret検証（ハッシュ比較）
       secret_hash = hashlib.sha256(request.secret.encode()).hexdigest()
       if device.secret_hash != secret_hash:
           raise HTTPException(status_code=401, detail="Invalid secret")

       # JWTトークン発行
       token = generate_jwt_token(
           edge_id=request.edge_id,
           device_type=request.device_type,
           tenant_id=request.tenant_id,
           store_code=request.store_code
       )

       return {
           "success": True,
           "data": {
               "access_token": token,
               "token_type": "bearer",
               "expires_in": 3600,
               "tenant_id": request.tenant_id,
               "store_code": request.store_code,
               "edge_id": request.edge_id,
               "device_type": request.device_type
           }
       }
   ```

3. **JWT検証ミドルウェア**:
   ```python
   from fastapi import Request, HTTPException
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   import jwt

   security = HTTPBearer()

   async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
       """JWTトークンを検証"""
       token = credentials.credentials

       try:
           payload = jwt.decode(
               token,
               settings.JWT_SECRET_KEY,
               algorithms=["HS256"]
           )

           # 有効期限チェック
           exp = datetime.fromtimestamp(payload["exp"], datetime.timezone.utc)
           if datetime.now(datetime.timezone.utc) > exp:
               raise HTTPException(status_code=401, detail="Token expired")

           return payload

       except jwt.InvalidTokenError:
           raise HTTPException(status_code=401, detail="Invalid token")
   ```

4. **SHA256チェックサム計算** (エッジ側):
   ```python
   import hashlib

   def calculate_sha256(file_path: str) -> str:
       """ファイルのSHA256チェックサムを計算"""
       sha256_hash = hashlib.sha256()

       with open(file_path, "rb") as f:
           # 大きなファイルでもメモリを圧迫しないよう、チャンクで読み込み
           for byte_block in iter(lambda: f.read(4096), b""):
               sha256_hash.update(byte_block)

       return sha256_hash.hexdigest()
   ```

5. **チェックサム検証** (Phase 3):
   ```python
   async def verify_checksums(manifest: dict, download_dir: str) -> bool:
       """ダウンロードしたファイルのチェックサム検証"""
       all_valid = True

       for artifact in manifest["artifacts"]:
           file_path = f"{download_dir}/artifacts/{artifact['name']}"
           expected_checksum = artifact["checksum"]

           if not os.path.exists(file_path):
               logger.error(f"File not found: {file_path}")
               all_valid = False
               continue

           calculated_checksum = calculate_sha256(file_path)

           if calculated_checksum != expected_checksum:
               logger.error(f"Checksum mismatch for {artifact['name']}")
               logger.error(f"Expected: {expected_checksum}")
               logger.error(f"Calculated: {calculated_checksum}")
               all_valid = False
           else:
               logger.info(f"Checksum valid for {artifact['name']}")

       return all_valid
   ```

6. **secret生成とハッシュ化** (デバイス登録時):
   ```python
   import secrets
   import hashlib

   def generate_device_secret() -> tuple[str, str]:
       """デバイスsecretを生成"""
       # 32バイト（256ビット）のランダム文字列
       secret = secrets.token_urlsafe(32)
       secret_hash = hashlib.sha256(secret.encode()).hexdigest()

       return secret, secret_hash

   # デバイス登録時
   async def register_device(edge_id: str, tenant_id: str):
       """デバイスを登録"""
       secret, secret_hash = generate_device_secret()

       device = DeviceDocument(
           edge_id=edge_id,
           tenant_id=tenant_id,
           secret_hash=secret_hash,
           created_at=datetime.now()
       )

       await device_repository.insert(device)

       # secretは安全な方法でデバイスに送信（初回セットアップ時のみ）
       return {"edge_id": edge_id, "secret": secret}
   ```

7. **デバイス側のsecret保存**:
   ```bash
   # /opt/kugelpos/.credentials
   EDGE_ID=edge-A1234-tokyo-001
   SECRET=abcdef1234567890abcdef1234567890abcdef1234567890
   ```
   ```bash
   # パーミッション設定（root以外アクセス不可）
   chmod 600 /opt/kugelpos/.credentials
   chown root:root /opt/kugelpos/.credentials
   ```

8. **TLS設定** (nginx reverse proxy):
   ```nginx
   server {
       listen 443 ssl http2;
       server_name sync.kugelpos.cloud;

       ssl_certificate /etc/letsencrypt/live/sync.kugelpos.cloud/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/sync.kugelpos.cloud/privkey.pem;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';

       location /api/v1/ {
           proxy_pass http://localhost:8007;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

---

## 7. スケーラビリティ対策

### Decision: Horizontal Scaling with Tenant Isolation

**選択したスケーラビリティ設計:**

```
[負荷分散]
Azure Load Balancer
  ↓
┌──────────┬──────────┬──────────┐
│ Sync-1   │ Sync-2   │ Sync-N   │
│ (Pod)    │ (Pod)    │ (Pod)    │
└──────────┴──────────┴──────────┘
  ↓ (共有)
┌────────────────────────────────┐
│ MongoDB (Replica Set)          │
│ - sync_{tenant_id} per tenant  │
└────────────────────────────────┘
  ↓ (共有)
┌────────────────────────────────┐
│ Azure Blob Storage             │
│ - Geo-replication              │
└────────────────────────────────┘
```

**Rationale:**

1. **水平スケーリング**:
   - Kubernetes HPA（Horizontal Pod Autoscaler）を使用
   - CPU使用率70%を閾値に自動スケール
   - 最小レプリカ数: 2（高可用性）、最大: 10（コスト最適化）

2. **テナント分離**:
   - データベース: `sync_{tenant_id}`（例: sync_A1234）
   - テナント間のデータ完全分離（クロステナントアクセス不可）
   - 既存のKugelposアーキテクチャと整合

3. **同時接続対応**:
   - 1,000台同時接続時のスループット維持
   - Azure Container Apps: Min 2, Max 10 replicas
   - コネクションプール: 各Pod 100接続

**Alternatives considered:**

| 選択肢 | 却下理由 |
|-------|---------|
| **垂直スケーリング** | - スケールアウトに限界がある<br>- ダウンタイムが発生する<br>- コストが指数関数的に増加<br>- 単一障害点（SPOF）のリスク |
| **シャーディング** | - 実装複雑度が高い<br>- テナント分離で十分（テナント数は限定的）<br>- シャードキー設計が困難<br>- クロスシャードクエリのパフォーマンス低下 |
| **キャッシュ層追加** | - 更新頻度が低い（15分間隔）ためキャッシュ効果が限定的<br>- Redis等のキャッシュインフラコスト<br>- キャッシュ無効化ロジックの複雑性 |

**Implementation notes:**

1. **Azure Container Apps構成** (Bicep):
   ```bicep
   resource syncService 'Microsoft.App/containerApps@2023-05-01' = {
     name: 'sync-service'
     location: 'japaneast'
     properties:
       managedEnvironmentId: containerAppEnv.id
       configuration: {
         ingress: {
           external: true
           targetPort: 8007
           transport: 'http'
           traffic: [
             {
               latestRevision: true
               weight: 100
             }
           ]
         }
       }
       template: {
         containers: [
           {
             name: 'sync'
             image: 'masakugel.azurecr.io/production/services/sync:v1.2.3'
             resources: {
               cpu: json('0.5')  // 0.5 vCPU
               memory: '1Gi'
             }
             env: [
               {
                 name: 'MONGODB_URI'
                 secretRef: 'mongodb-connection'
               }
               {
                 name: 'MAX_CONNECTIONS'
                 value: '100'
               }
             ]
           }
         ]
         scale: {
           minReplicas: 2
           maxReplicas: 10
           rules: [
             {
               name: 'http-rule'
               http: {
                 metadata: {
                   concurrentRequests: '100'
                 }
               }
             }
             {
               name: 'cpu-rule'
               custom: {
                 type: 'cpu'
                 metadata: {
                   type: 'Utilization'
                   value: '70'
                 }
               }
             }
           ]
         }
       }
     }
   }
   ```

2. **MongoDB Replica Set構成**:
   ```yaml
   # docker-compose.yaml (開発環境)
   version: '3.8'
   services:
     mongodb-primary:
       image: mongo:7.0
       container_name: mongodb-primary
       command: mongod --replSet rs0 --bind_ip_all
       ports:
         - "27017:27017"
       volumes:
         - mongodb_primary_data:/data/db

     mongodb-secondary1:
       image: mongo:7.0
       container_name: mongodb-secondary1
       command: mongod --replSet rs0 --bind_ip_all
       ports:
         - "27018:27017"
       volumes:
         - mongodb_secondary1_data:/data/db

     mongodb-secondary2:
       image: mongo:7.0
       container_name: mongodb-secondary2
       command: mongod --replSet rs0 --bind_ip_all
       ports:
         - "27019:27017"
       volumes:
         - mongodb_secondary2_data:/data/db

   volumes:
     mongodb_primary_data:
     mongodb_secondary1_data:
     mongodb_secondary2_data:
   ```

3. **コネクションプール設定** (Motor):
   ```python
   from motor.motor_asyncio import AsyncIOMotorClient
   from pymongo import MongoClient

   # 設定
   MONGODB_URI = "mongodb://localhost:27017/?replicaSet=rs0"
   MAX_POOL_SIZE = 100
   MIN_POOL_SIZE = 10

   # クライアント作成
   client = AsyncIOMotorClient(
       MONGODB_URI,
       maxPoolSize=MAX_POOL_SIZE,
       minPoolSize=MIN_POOL_SIZE,
       connectTimeoutMS=5000,
       serverSelectionTimeoutMS=5000
   )

   # テナント別データベース取得
   def get_tenant_database(tenant_id: str):
       """テナント別データベースを取得"""
       db_name = f"sync_{tenant_id}"
       return client[db_name]
   ```

4. **負荷分散テスト** (locust):
   ```python
   from locust import HttpUser, task, between
   import random

   class SyncServiceUser(HttpUser):
       wait_time = between(1, 5)

       def on_start(self):
           """認証してJWTトークンを取得"""
           response = self.client.post("/api/v1/version-management/auth", json={
               "tenant_id": "A1234",
               "store_code": "tokyo",
               "edge_id": f"edge-A1234-tokyo-{random.randint(1, 1000):03d}",
               "device_type": "pos",
               "secret": "test-secret"
           })
           self.token = response.json()["data"]["access_token"]

       @task
       def check_version(self):
           """バージョンチェック"""
           headers = {"Authorization": f"Bearer {self.token}"}
           self.client.post("/api/v1/artifact-management/check", json={
               "device_type": "pos",
               "edge_id": self.edge_id,
               "current_version": "v1.2.2"
           }, headers=headers)
   ```

5. **Circuit Breaker実装** (既存のDaprClientHelperパターン):
   ```python
   from kugel_common.utils.dapr_client_helper import DaprClientHelper

   # 既存のCircuit Breakerパターンを流用
   dapr_client = DaprClientHelper(
       circuit_breaker_threshold=3,  # 3回失敗でオープン
       circuit_breaker_timeout=60    # 60秒後に半開状態
   )
   ```

6. **Retry実装** (既存のHttpClientHelperパターン):
   ```python
   from kugel_common.utils.http_client_helper import HttpClientHelper

   # 既存のRetryパターンを流用
   http_client = HttpClientHelper(
       base_url="https://sync.kugelpos.cloud",
       max_retries=3,         # 最大3回リトライ
       retry_delay=1,         # 初回1秒、指数バックオフ
       timeout=30
   )
   ```

7. **時間帯分散戦略**:
   ```python
   def generate_scheduled_at(store_group: int) -> str:
       """店舗グループごとに適用時刻を分散"""
       base_hour = 2  # 深夜2:00
       offset_minutes = (store_group % 3) * 20  # 0, 20, 40分

       scheduled_time = datetime(2025, 1, 18, base_hour, offset_minutes, 0)
       return scheduled_time.isoformat() + "Z"

   # 店舗グループ例:
   # - Group 0: 02:00-02:20
   # - Group 1: 02:20-02:40
   # - Group 2: 02:40-03:00
   ```

8. **データベースインデックス**:
   ```python
   # MongoDB indexes for performance
   await device_collection.create_index([("edge_id", 1)], unique=True)
   await device_collection.create_index([("tenant_id", 1), ("store_code", 1)])
   await version_collection.create_index([("edge_id", 1), ("target_version", 1)])
   await history_collection.create_index([("edge_id", 1), ("start_time", -1)])
   ```

---

## まとめ

### 主要な技術決定

| 項目 | 選択技術 | 主な理由 |
|------|---------|---------|
| **Container Registry** | ACR Premium + Harbor | Geo-replication、エンタープライズ機能、ローカルキャッシュ |
| **Blob Storage** | Azure Blob with Version Folders | バージョン管理容易、ロールバック簡単、3世代保持 |
| **P2P配信** | Priority-based Seed Selection | 優先度制御、API経由、フォールバック機構 |
| **2段階更新** | Phase-based with Maintenance Window | ダウンタイム最小化、Manifest制御、状態管理 |
| **ロールバック** | Automated to Previous Version | 運用シンプル、予測可能性、バックアップ1世代 |
| **セキュリティ** | JWT + SHA256 | ステートレス認証、NIST推奨、改ざん検出 |
| **スケーラビリティ** | Horizontal Scaling + Tenant Isolation | 1000台対応、テナント分離、Auto-scaling |

### 実装上の重要ポイント

1. **既存アーキテクチャの活用**:
   - HttpClientHelper（Circuit Breaker、Retry）
   - DaprClientHelper（Pub/Sub、State Store）
   - FastAPI、MongoDB、Docker Composeパターン

2. **プロジェクト憲章準拠**:
   - マイクロサービス独立性（Sync Serviceは独立）
   - 非同期優先（Motor、httpx）
   - TDD（テストファーストで開発）
   - エラーハンドリング（Circuit Breaker、Retry、Rollback）

3. **運用性の考慮**:
   - 監査ログ（全API操作を記録）
   - メトリクス（Prometheus、Azure Monitor）
   - アラート（更新失敗、ロールバック発生）
   - ドキュメント（英語優先、日本語補足）

### 次のステップ

1. **plan.md作成**: 本research.mdの内容を基に、詳細設計書を作成
2. **tasks.md作成**: 実装タスクを依存関係順に整理
3. **プロトタイプ実装**: 優先度P1の機能から実装開始
4. **テスト実装**: TDDに従いテストファーストで開発

---

**作成日**: 2025-10-13
**作成者**: Claude Code (Technical Research Agent)
**承認**: 未承認

# ユーザーストーリー1: エッジ端末の自動更新とオフライン耐性 - 処理フロー図

## 概要

このドキュメントは、ユーザーストーリー1「エッジ端末の自動更新とオフライン耐性」の処理フローを視覚的に説明します。店舗のエッジ端末（Edge/POS）が、営業時間中に新バージョンをダウンロードし、営業終了後に自動適用する全体像を、ユーザーが理解しやすい形で図解します。

## シナリオ

店舗のエッジ端末（Edge/POS）が、営業時間中に新しいバージョンのアプリケーションファイルをダウンロードし、営業終了後の指定時刻に自動的に適用される。ネットワーク障害時でも現在適用されているバージョンで業務を継続できる。

## 主要コンポーネント

```mermaid
graph TB
    subgraph Cloud["☁️ クラウド環境"]
        CloudSync["Sync Service<br/>（Cloud Mode）"]
        MongoDB_Cloud[("MongoDB<br/>sync_tenant001")]
        BlobStorage["Blob Storage<br/>（アーティファクト保存）"]
        ContainerRegistry["Container Registry<br/>（イメージ保存）"]
    end

    subgraph Edge["🏪 店舗環境（エッジ端末）"]
        EdgeSync["Sync Service<br/>（Edge Mode）"]
        MongoDB_Edge[("MongoDB<br/>sync_tenant001")]
        StartupScript["起動スクリプト<br/>（startup.sh）"]
        DockerCompose["Docker Compose<br/>（サービス管理）"]
        Services["各マイクロサービス<br/>（account, cart, 等）"]
        LocalStorage["ローカルストレージ<br/>（/opt/kugelpos/）"]
    end

    CloudSync <-->|JWT認証<br/>REST API| EdgeSync
    CloudSync --> MongoDB_Cloud
    CloudSync -.-> BlobStorage
    CloudSync -.-> ContainerRegistry
    EdgeSync --> MongoDB_Edge
    EdgeSync --> LocalStorage
    StartupScript --> DockerCompose
    DockerCompose --> Services
    EdgeSync -.-> StartupScript
```

## 処理フロー全体

### フロー1: 営業時間中の自動ダウンロード（ダウンロードフェーズ: Phase 1-3）

営業時間中（サービス稼働中）にバージョンチェックを実行し、新バージョンをダウンロードするフローです。

```mermaid
sequenceDiagram
    participant Scheduler as ⏰ APScheduler
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant EdgeDB as Edge MongoDB
    participant BlobStorage as Blob Storage
    participant Registry as Container Registry
    participant LocalFS as Local Storage

    Note over Scheduler,LocalFS: 🔄 営業時間中（14:00）・サービス稼働中

    rect rgb(240, 240, 255)
        Note right of Scheduler: Phase 1: バージョンチェック
        Scheduler->>Edge: check_for_updates()<br/>（起動時 + 15分ごと）

        Edge->>EdgeDB: DeviceVersion取得<br/>(current_version, last_check_timestamp)
        EdgeDB-->>Edge: current_version: "1.2.2"

        Edge->>+Cloud: POST /api/v1/version/check<br/>Authorization: Bearer <token><br/>{edge_id, device_type, current_version: "1.2.2"}

        Cloud->>Cloud: 更新判定<br/>target_version: "1.2.3" > current_version

        alt 更新あり
            Cloud-->>-Edge: Manifest返却<br/>{target_version: "1.2.3", artifacts: [...], container_images: [...], <br/>apply_schedule: {scheduled_at: "2025-10-15T02:00:00Z", maintenance_window: 30}}

            Edge->>EdgeDB: DeviceVersion更新<br/>(target_version: "1.2.3", update_status: "downloading", <br/>download_status: "in_progress", scheduled_apply_at: "02:00")
        else 更新なし
            Cloud-->>Edge: 更新なし<br/>{update_available: false}
            Edge->>EdgeDB: last_check_timestamp更新
            Note over Edge: ✅ 15分後に再チェック
        end
    end

    rect rgb(255, 250, 240)
        Note right of Edge: Phase 2: ダウンロード実行（営業時間中・サービス停止なし）

        loop アーティファクトごと
            Edge->>+Cloud: GET /api/v1/artifacts/startup.sh?version=1.2.3
            Cloud->>BlobStorage: ファイル取得
            BlobStorage-->>Cloud: startup.sh
            Cloud-->>-Edge: ファイルデータ

            Edge->>Edge: チェックサム計算<br/>（SHA256）
            Edge->>LocalFS: 一時保存<br/>(/opt/kugelpos/pending-updates/v1.2.3/)
        end

        loop コンテナイメージごと
            Edge->>+Registry: docker pull registry.example.com/kugelpos/cart:1.2.3
            Registry-->>-Edge: イメージレイヤー

            Edge->>Edge: イメージダイジェスト検証<br/>（SHA256）
        end

        Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "completed", download_completed_at: now)
        Edge->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3", artifacts_count: 15, total_size_bytes: 3200000000}
        Cloud-->>-Edge: 通知受信確認
    end

    rect rgb(240, 255, 240)
        Note right of Edge: Phase 3: ダウンロード検証

        Edge->>LocalFS: 全ファイル存在確認
        Edge->>Edge: 全チェックサム検証

        alt 検証成功
            Edge->>LocalFS: status.json保存<br/>(ready_to_apply: true, verification_status: "passed")
            Edge->>EdgeDB: DeviceVersion更新<br/>(update_status: "pending_apply", pending_version: "1.2.3")

            Note over Edge: ✅ ダウンロードフェーズ完了<br/>営業継続中（サービス無停止）
        else 検証失敗
            Edge->>Edge: リトライカウンタ増加<br/>(retry_count++)

            alt retry_count < 3
                Note over Edge: 🔄 指数バックオフ後リトライ<br/>（1秒 → 2秒 → 4秒）
                Edge->>Cloud: 再ダウンロード実行
            else retry_count >= 3
                Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "failed", error_message: "Checksum mismatch after 3 retries")
                Edge->>Cloud: POST /api/v1/error-report<br/>{edge_id, error_type: "download_failed"}
                Note over Edge: ❌ ダウンロード失敗<br/>次回バージョンチェック時に再試行
            end
        end
    end

    Note over Scheduler,LocalFS: ⏱️ ダウンロード完了・適用予定時刻（02:00）まで待機
```

**主要ステップ**:
1. **Phase 1: バージョンチェック**: 起動時および15分ごとにクラウドに現在バージョンを送信し、更新要否を確認
2. **Phase 2: ダウンロード実行**: 営業時間中にファイルとコンテナイメージをダウンロード（サービス停止なし）
3. **Phase 3: ダウンロード検証**: SHA256チェックサム検証、検証失敗時は最大3回リトライ

### フロー2: メンテナンスウィンドウでの自動適用（適用フェーズ: Phase 4-9）

ダウンロード完了後、指定されたメンテナンスウィンドウ内（深夜2:00-2:30）に自動的に適用するフローです。

```mermaid
sequenceDiagram
    participant Scheduler as ⏰ APScheduler
    participant Edge as 🏪 Edge Sync
    participant EdgeDB as Edge MongoDB
    participant LocalFS as Local Storage
    participant Docker as Docker Compose
    participant Services as Microservices
    participant Cloud as ☁️ Cloud Sync

    Note over Scheduler,Cloud: 🌙 メンテナンスウィンドウ開始（02:00）

    rect rgb(255, 240, 240)
        Note right of Scheduler: Phase 4: バックアップ
        Scheduler->>Edge: apply_pending_update()<br/>（scheduled_at到達時）

        Edge->>EdgeDB: DeviceVersion取得<br/>(pending_version, scheduled_apply_at)
        EdgeDB-->>Edge: pending_version: "1.2.3"

        Edge->>Edge: メンテナンスウィンドウ確認<br/>(scheduled_at <= now < scheduled_at + maintenance_window)

        alt ウィンドウ内
            Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "in_progress")
            Edge->>EdgeDB: UpdateHistory作成<br/>(update_id, from_version: "1.2.2", to_version: "1.2.3", start_time: now)

            Edge->>LocalFS: 現行バージョンバックアップ<br/>(/opt/kugelpos/backups/v1.2.2/)
            Edge->>Docker: docker images save<br/>（全サービスイメージ）
            Note over Edge: ✅ ロールバック準備完了
        else ウィンドウ外
            Note over Edge: ⏭️ 適用スキップ<br/>次回スケジュールまで待機
        end
    end

    rect rgb(255, 250, 240)
        Note right of Edge: Phase 5: 適用準備

        Edge->>LocalFS: pending-updates/v1.2.3/ から<br/>ファイル配置準備
        Edge->>Edge: スクリプトファイル検証<br/>（実行権限 755）
        Edge->>Edge: 設定ファイル検証<br/>（YAML/JSON構文チェック）

        Note over Edge: ✅ 適用準備完了
    end

    rect rgb(240, 240, 255)
        Note right of Edge: Phase 6: サービス停止

        Edge->>Docker: docker-compose down<br/>（全サービス停止）
        Docker->>Services: SIGTERM送信
        Services-->>Docker: グレースフルシャットダウン完了
        Docker-->>Edge: 停止完了

        Note over Edge: ⏸️ ダウンタイム開始<br/>（目標: 1-3分）
    end

    rect rgb(255, 250, 240)
        Note right of Edge: Phase 7: 新バージョン適用

        Edge->>LocalFS: スクリプトファイル配置<br/>（startup.sh → /opt/kugelpos/）
        Edge->>LocalFS: 設定ファイル配置<br/>（docker-compose.yml 等）
        Edge->>LocalFS: モジュールインストール<br/>（pip install *.whl）

        Edge->>Docker: docker-compose pull<br/>（新バージョンイメージ）
        Docker-->>Edge: プル完了（ローカルキャッシュ利用）

        Edge->>Docker: docker-compose up -d<br/>（全サービス起動）
        Docker->>Services: コンテナ起動
        Services-->>Docker: 起動完了
        Docker-->>Edge: 起動完了

        Note over Edge: ⏯️ サービス再起動完了
    end

    rect rgb(240, 255, 240)
        Note right of Edge: Phase 8: ヘルスチェック

        loop 各サービス
            Edge->>Services: GET /health

            alt ヘルスチェック成功
                Services-->>Edge: {"status": "healthy"}
                Note over Edge: ✅ サービス正常
            else ヘルスチェック失敗（最大3回、10秒間隔）
                Services-->>Edge: タイムアウトまたは500エラー

                alt リトライ中（retry < 3）
                    Note over Edge: 🔄 10秒待機後リトライ
                else 3回失敗
                    Note over Edge: ❌ ヘルスチェック失敗<br/>→ ロールバック実行
                    Edge->>Docker: docker-compose down
                    Edge->>LocalFS: バックアップから復元<br/>(/opt/kugelpos/backups/v1.2.2/)
                    Edge->>Docker: docker images load<br/>（旧バージョンイメージ）
                    Edge->>Docker: docker-compose up -d<br/>（旧バージョンで起動）

                    Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "rolled_back", current_version: "1.2.2", error_message: "Health check failed")
                    Edge->>EdgeDB: UpdateHistory更新<br/>(status: "failed", error_message: "Health check failed after 3 retries")
                    Edge->>Cloud: POST /api/v1/apply-failed<br/>{edge_id, version: "1.2.3", error: "Health check failed"}

                    Note over Edge: ⚠️ ロールバック完了<br/>旧バージョンで稼働
                end
            end
        end

        Note over Edge: ✅ 全サービスヘルスチェック通過
    end

    rect rgb(240, 255, 240)
        Note right of Edge: Phase 9: 完了通知

        Edge->>EdgeDB: DeviceVersion更新<br/>(current_version: "1.2.3", apply_status: "completed", apply_completed_at: now, <br/>update_status: "completed", pending_version: null, retry_count: 0)

        Edge->>EdgeDB: UpdateHistory更新<br/>(end_time: now, status: "success", downtime_seconds: 120)

        Edge->>LocalFS: 古いバックアップ削除<br/>（7日以上経過したもの）
        Edge->>LocalFS: pending-updates/v1.2.3/ 削除

        Edge->>+Cloud: POST /api/v1/apply-complete<br/>{edge_id, version: "1.2.3", downtime_seconds: 120, artifacts_count: 15}
        Cloud->>MongoDB_Cloud: DeviceVersion更新<br/>（クラウド側記録）
        Cloud-->>-Edge: 通知受信確認

        Note over Edge: ✅ 更新完了（ダウンタイム: 2分）
    end

    Note over Scheduler,Cloud: ⏱️ メンテナンスウィンドウ終了（02:30）
```

**主要ステップ**:
1. **Phase 4: バックアップ**: 現行バージョンをバックアップ（ロールバック用）
2. **Phase 5: 適用準備**: ファイル配置準備、検証
3. **Phase 6: サービス停止**: 全サービスをグレースフルシャットダウン（ダウンタイム開始）
4. **Phase 7: 新バージョン適用**: ファイル配置、モジュールインストール、サービス起動
5. **Phase 8: ヘルスチェック**: 全サービスの正常性確認、失敗時は自動ロールバック
6. **Phase 9: 完了通知**: クラウドに適用完了を通知、ローカルクリーンアップ

### フロー3: ネットワーク障害時のリトライとオフライン耐性

ダウンロード中にネットワーク障害が発生した場合の自動復旧フローです。

```mermaid
sequenceDiagram
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant EdgeDB as Edge MongoDB
    participant Services as Microservices

    Note over Edge,Services: 🔄 ダウンロード中（営業時間中）

    rect rgb(255, 240, 240)
        Note right of Edge: 1. ネットワーク障害発生
        Edge->>Cloud: ❌ GET /api/v1/artifacts/startup.sh<br/>（接続失敗）
        Edge->>Edge: サーキットブレーカー検知<br/>連続3回失敗

        Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "failed", retry_count: 3, error_message: "Network timeout")

        Note over Edge: ⏸️ ダウンロード中断<br/>60秒待機（サーキットブレーカー）
        Note over Services: ✅ 現在バージョン（v1.2.2）で<br/>業務継続中
    end

    rect rgb(240, 255, 240)
        Note right of Edge: 2. ネットワーク復旧
        Note over Edge: ⚡ ネットワーク復旧検知<br/>（最初の成功したHTTPリクエスト）

        Edge->>+Cloud: GET /health<br/>（ヘルスチェック）
        Cloud-->>-Edge: ✅ {"status": "healthy"}

        Note over Edge: 🔓 サーキットブレーカー<br/>半開状態

        Edge->>Edge: 復旧検知後30秒以内<br/>ダウンロード再開準備
    end

    rect rgb(255, 250, 240)
        Note right of Edge: 3. ダウンロード自動再開
        Edge->>+Cloud: POST /api/v1/auth/token<br/>（トークン再取得）
        Cloud-->>-Edge: JWT トークン

        Edge->>+Cloud: POST /api/v1/version/check<br/>{edge_id, current_version: "1.2.2"}
        Cloud-->>-Edge: Manifest返却<br/>(target_version: "1.2.3")

        Edge->>Edge: ダウンロード済みファイル確認<br/>（部分ダウンロード状態）

        Edge->>+Cloud: GET /api/v1/artifacts/startup.sh?version=1.2.3<br/>（未完了ファイルのみ再ダウンロード）
        Cloud-->>-Edge: ファイルデータ

        Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "completed", retry_count: 0)

        Note over Edge: ✅ ダウンロード再開成功<br/>予定時刻（02:00）に適用
    end

    Note over Edge,Services: ⏱️ 復旧後30秒以内にダウンロード再開
```

**主要ステップ**:
1. **ネットワーク障害検知**: 連続3回失敗でサーキットブレーカーがオープン、ダウンロード中断
2. **業務継続**: 現在バージョンで業務を継続（オフライン耐性）
3. **復旧検知**: 最初の成功したHTTPリクエストで復旧を検知
4. **自動再開**: トークン再取得 → 未完了ファイルのみ再ダウンロード（復旧後30秒以内）

## データ整合性保証の仕組み

### チェックサム検証（FR-009）

```mermaid
graph LR
    A[Cloud Sync] -->|1. ファイル送信| B[startup.sh]
    A -->|2. チェックサム送信| C[SHA256: abc123...]
    B --> D[Edge Sync]
    C --> D
    D -->|3. 再計算| E[SHA256: abc123...]
    D -->|4. 比較| F{一致?}
    F -->|Yes| G[✅ 保存]
    F -->|No| H[❌ リトライ<br/>最大3回]
    H -->|3回失敗| I[⚠️ エラー通知<br/>次回チェック時に再試行]
```

**検証アルゴリズム**:
```python
# Cloud側でチェックサム計算（Manifestに含める）
checksum = hashlib.sha256(file_data).hexdigest()

# Edge側で検証
downloaded_checksum = hashlib.sha256(downloaded_file).hexdigest()
if manifest["checksum"] != downloaded_checksum:
    raise ChecksumMismatchError()
```

### 自動ロールバック（FR-010, FR-011）

```mermaid
graph TD
    A[新バージョン適用] --> B[サービス起動]
    B --> C[ヘルスチェック実行]
    C --> D{全サービス正常?}
    D -->|Yes| E[✅ 適用完了]
    D -->|No 1回目失敗| F[10秒待機]
    F --> C
    D -->|No 2回目失敗| G[10秒待機]
    G --> C
    D -->|No 3回目失敗| H[❌ 自動ロールバック開始]
    H --> I[サービス停止]
    I --> J[バックアップから復元]
    J --> K[旧バージョンで起動]
    K --> L[ヘルスチェック]
    L --> M{旧バージョン正常?}
    M -->|Yes| N[✅ ロールバック完了<br/>エラー通知送信]
    M -->|No| O[⚠️ 手動介入が必要<br/>緊急通知送信]
```

**ロールバック条件**:
- ヘルスチェック3回連続失敗（10秒間隔）
- サービス起動失敗

**ロールバック時間**: 3分以内（SC-009）

## データベース構造

### DeviceVersion（デバイスバージョン管理）

各エッジ端末の現在バージョン、目標バージョン、更新状態を管理するコレクション：

```
コレクション: info_edge_version

ドキュメント例:
{
  "_id": ObjectId("..."),
  "edge_id": "edge-tenant001-store001-001",
  "device_type": "edge",
  "current_version": "1.2.3",
  "target_version": "1.2.3",
  "update_status": "completed",
  "download_status": "completed",
  "download_completed_at": ISODate("2025-10-14T16:30:00Z"),
  "apply_status": "completed",
  "scheduled_apply_at": ISODate("2025-10-15T02:00:00Z"),
  "apply_completed_at": ISODate("2025-10-15T02:02:30Z"),
  "pending_version": null,
  "last_check_timestamp": ISODate("2025-10-15T10:00:00Z"),
  "retry_count": 0,
  "error_message": null,
  "created_at": ISODate("2025-10-01T00:00:00Z"),
  "updated_at": ISODate("2025-10-15T02:02:30Z")
}
```

**インデックス**:
- `{edge_id: 1}` (unique) - エッジ端末での検索
- `{device_type: 1, update_status: 1}` - 更新状態での集計
- `{target_version: 1, download_status: 1}` - ダウンロード進捗追跡

### UpdateHistory（更新履歴）

各更新実行の監査ログ：

```
コレクション: info_update_history

ドキュメント例:
{
  "_id": ObjectId("..."),
  "update_id": "550e8400-e29b-41d4-a716-446655440000",
  "edge_id": "edge-tenant001-store001-001",
  "from_version": "1.2.2",
  "to_version": "1.2.3",
  "start_time": ISODate("2025-10-15T02:00:00Z"),
  "end_time": ISODate("2025-10-15T02:02:30Z"),
  "status": "success",
  "error_message": null,
  "artifacts_count": 15,
  "total_size_bytes": 3200000000,
  "downtime_seconds": 120
}
```

**インデックス**:
- `{update_id: 1}` (unique) - 更新IDでの検索
- `{edge_id: 1, start_time: -1}` - エッジ端末ごとの履歴取得

**保持期間**: 90日間（TTLインデックス）

### PendingUpdate（ダウンロード済み未適用更新）

エッジ端末のローカルストレージに保存されるダウンロード状態管理：

```
ファイルパス: /opt/kugelpos/pending-updates/v1.2.3/status.json

ドキュメント例:
{
  "version": "1.2.3",
  "download_status": "completed",
  "download_started_at": "2025-10-14T16:00:00Z",
  "download_completed_at": "2025-10-14T16:30:00Z",
  "verification_status": "passed",
  "ready_to_apply": true,
  "artifacts_count": 15,
  "total_size_bytes": 3200000000,
  "manifest_json": { ... },
  "status_json": {
    "files": {
      "startup.sh": {"status": "completed", "checksum_verified": true},
      "docker-compose.yml": {"status": "completed", "checksum_verified": true}
    },
    "images": {
      "cart:1.2.3": {"status": "completed", "digest_verified": true}
    }
  }
}
```

**保持期限**: 7日間、期限超過時は自動削除（FR-028）

## パフォーマンス指標

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| **ダウンロード時間（エッジ端末）** | 10分以内 | バージョンチェック → ダウンロード完了までの時間（全8サービス、合計3200MB） |
| **ダウンロード時間（POS端末）** | 5分以内 | バージョンチェック → ダウンロード完了までの時間 |
| **ダウンタイム** | 1-3分 | Phase 6開始 → Phase 7完了までの時間 |
| **チェックサム検証成功率** | 99.9%以上 | 検証成功回数 / 全ダウンロード回数 |
| **ヘルスチェック成功率** | 99.9%以上 | 新バージョン適用後のヘルスチェック成功率 |
| **自動ロールバック時間** | 3分以内 | ヘルスチェック失敗検出 → ロールバック完了までの時間 |
| **ネットワーク復旧後の再開** | 30秒以内 | 復旧検知 → ダウンロード再開までの時間 |
| **適用開始時刻精度** | scheduled_at ±30秒 | 予定時刻と実際の適用開始時刻の差 |

## エラーハンドリング

### リトライ戦略（FR-027）

```mermaid
graph TD
    A[ダウンロード実行] -->|失敗| B{retry_count < 3?}
    B -->|Yes| C[指数バックオフ待機]
    C -->|1秒 → 2秒 → 4秒| D[リトライ実行]
    D --> A
    B -->|No| E[❌ 最大リトライ超過]
    E --> F[エラー記録]
    F --> G[クラウドに通知]
    G --> H[次回バージョンチェック時に再試行]
    A -->|成功| I[✅ retry_count = 0]
```

**指数バックオフ**: 1秒 → 2秒 → 4秒（最大3回）

### サーキットブレーカー

```mermaid
stateDiagram-v2
    [*] --> Closed: 初期状態
    Closed --> Open: 連続3回失敗
    Open --> HalfOpen: 60秒経過
    HalfOpen --> Closed: 成功
    HalfOpen --> Open: 失敗

    note right of Closed: 通常動作<br/>すべてのリクエスト実行
    note right of Open: 回路開放<br/>リクエスト即座に失敗<br/>現在バージョンで業務継続
    note right of HalfOpen: 復旧テスト<br/>1件のみ実行して判定
```

**しきい値**: 連続3回失敗でオープン

**回復時間**: 60秒後に半開状態

## 受入シナリオの検証

### シナリオ1: 営業時間中のダウンロード、営業終了後の自動適用

```
Given: クラウドに新バージョン（v1.2.3）が登録されている、scheduled_at=深夜2:00に設定
When: エッジ端末が15分ごとのバージョンチェックを実行（14:00）
Then:
  1. 更新が検知され、即座にダウンロードが開始される（営業時間中、サービス停止なし）
  2. ダウンロード完了後、深夜2:00まで待機
  3. 深夜2:00に自動的に適用フェーズが実行される
  4. サービス停止→新バージョンに更新→サービス起動→ヘルスチェック完了
  5. ダウンタイム1-3分以内

検証方法:
1. Cloud Sync Serviceで新バージョン登録 (target_version: "1.2.3", scheduled_at: "02:00")
2. Edge Sync のバージョンチェック実行（14:00）
3. ダウンロードフェーズ完了を確認（DeviceVersion.download_status: "completed"）
4. scheduled_at到達時（02:00）に適用フェーズが自動実行されることを確認
5. ダウンタイムを測定（Phase 6開始 → Phase 7完了）
6. 最終的に DeviceVersion.current_version: "1.2.3", apply_status: "completed" を確認
```

### シナリオ2: ネットワーク障害時の業務継続と復旧後の自動再開

```
Given: ダウンロード中にネットワーク障害発生
When: 障害が継続
Then:
  1. ダウンロードを中断し、現在バージョンで業務継続
  2. ネットワーク障害が復旧後30秒以内にダウンロード自動再開
  3. 完了後は予定時刻に適用

検証方法:
1. Edge Sync のダウンロード中にネットワーク接続を切断
2. Edge Sync が現在バージョン（v1.2.2）で継続稼働することを確認
3. ネットワーク接続を復旧
4. 復旧検知からの経過時間を測定
5. 30秒以内にダウンロード再開されることを確認
6. ダウンロード完了後、scheduled_atに適用されることを確認
```

### シナリオ3: ヘルスチェック失敗時の自動ロールバック

```
Given: 新バージョン適用後、サービス起動失敗
When: ヘルスチェック3回連続失敗
Then:
  1. 自動的にロールバックが実行される
  2. 直前のバージョンに復元され、サービスが正常起動
  3. ロールバック時間3分以内

検証方法:
1. 意図的に不正な設定ファイルを含むバージョンを作成
2. 適用フェーズ実行
3. ヘルスチェック失敗を3回確認
4. 自動ロールバック実行を確認
5. ロールバック完了までの時間を測定（3分以内）
6. DeviceVersion.apply_status: "rolled_back", current_version: "1.2.2" を確認
7. UpdateHistory.status: "failed" を確認
```

### シナリオ4: チェックサム検証失敗時のリトライ

```
Given: ファイルダウンロード完了後、チェックサム不一致検出
When: 検証失敗
Then:
  1. ダウンロードファイルを削除
  2. エラーをクラウドに通知
  3. 指数バックオフ（1秒→2秒→4秒）でリトライ（最大3回）
  4. 3回失敗後は次回バージョンチェック時に再試行

検証方法:
1. 意図的にファイルを改ざんしてチェックサム不一致を発生させる
2. Edge Sync がリトライを実行することを確認
3. リトライ間隔を測定（1秒→2秒→4秒）
4. 3回失敗後、DeviceVersion.download_status: "failed", retry_count: 3 を確認
5. クラウドにエラー通知が送信されることを確認
```

## 関連ドキュメント

- [spec.md](../spec.md) - 機能仕様書
- [plan.md](../plan.md) - 実装計画
- [data-model.md](../data-model.md) - データモデル設計
- [contracts/sync-api.yaml](../contracts/sync-api.yaml) - Sync API仕様
- [contracts/auth-api.yaml](../contracts/auth-api.yaml) - 認証API仕様

---

**ドキュメントバージョン**: 1.0.0
**最終更新日**: 2025-10-14
**ステータス**: 完成

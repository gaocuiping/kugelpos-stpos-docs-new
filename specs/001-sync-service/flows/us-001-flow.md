# ユーザストーリー1: マスタデータ同期 - 処理フロー図

## 概要

このドキュメントは、ユーザストーリー1「マスターデータの自動同期」の処理フローを視覚的に説明します。クラウドからエッジ端末へのマスタデータ配信の全体像を、ユーザが理解しやすい形で図解します。

## シナリオ

店舗管理者がクラウド側でマスターデータ（商品、価格、決済方法、スタッフ情報）を更新すると、すべての店舗のエッジ端末に自動的に同期され、最新の情報で販売業務を継続できる。

## 主要コンポーネント

```mermaid
graph TB
    subgraph Cloud["☁️ クラウド環境"]
        MasterData["Master-data Service<br/>（商品・価格・スタッフマスタ）"]
        TerminalSvc["Terminal Service<br/>（端末設定マスタ）"]
        CloudSync["Sync Service<br/>（Cloud Mode）"]
        MongoDB_Cloud[("MongoDB<br/>sync_tenant001")]
    end

    subgraph Edge["🏪 店舗環境（エッジ）"]
        EdgeSync["Sync Service<br/>（Edge Mode）"]
        EdgeMasterData["Master-data Service<br/>（ローカルDB）"]
        EdgeTerminal["Terminal Service<br/>（ローカルDB）"]
        MongoDB_Edge[("MongoDB<br/>sync_tenant001")]
        POS["POS端末<br/>（商品販売）"]
    end

    MasterData -.-> CloudSync
    TerminalSvc -.-> CloudSync
    CloudSync <-->|JWT認証<br/>REST API| EdgeSync
    EdgeSync --> EdgeMasterData
    EdgeSync --> EdgeTerminal
    EdgeSync --> MongoDB_Edge
    EdgeMasterData --> POS
    EdgeTerminal --> POS
    CloudSync --> MongoDB_Cloud
```

## 処理フロー全体

### フロー1: 初回セットアップ（一括同期）

新しいエッジ端末を設置した際の初回マスタデータ取得フローです。

```mermaid
sequenceDiagram
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant Master as Master-data Service
    participant Terminal as Terminal Service
    participant EdgeDB as Edge MongoDB
    participant EdgeMaster as Edge Master-data

    Note over Edge,EdgeMaster: 🚀 初回セットアップ

    rect rgb(240, 240, 255)
        Note right of Edge: 1. 認証フェーズ
        Edge->>+Cloud: POST /api/v1/auth/token<br/>{edge_id, secret}
        Cloud->>Cloud: シークレット検証<br/>（SHA256ハッシュ比較）
        Cloud-->>-Edge: JWT トークン（24時間有効）<br/>{tenant_id, edge_id, store_code}
    end

    rect rgb(255, 250, 240)
        Note right of Edge: 2. 一括同期リクエスト
        Edge->>+Cloud: POST /api/v1/sync/request<br/>Authorization: Bearer <token><br/>{sync_type: "full", data_types: ["categories", "products", "staff", "payment_methods", "tax_rules"]}

        Note over Cloud: 3. マスタデータ収集
        Cloud->>+Master: Dapr Service Invocation<br/>POST /api/v1/sync/changes<br/>{last_sync_timestamp: null, data_types: [...]}
        Master->>Master: 全データ取得<br/>（初回は全件）
        Master-->>-Cloud: マスタデータ<br/>{categories: [...], products: [...], ...}<br/>+ checksum, record_count

        Cloud->>+Terminal: Dapr Service Invocation<br/>POST /api/v1/sync/changes
        Terminal-->>-Cloud: ターミナル設定マスタ

        Note over Cloud: 4. データ整形・検証
        Cloud->>Cloud: チェックサム計算<br/>レコード件数カウント
        Cloud->>EdgeDB: SyncHistory保存<br/>(sync_id, started_at, direction: cloud_to_edge)

        Cloud-->>-Edge: マスタデータ + メタ情報<br/>{data: {...}, checksum: "abc123...", record_count: 5432}
    end

    rect rgb(240, 255, 240)
        Note right of Edge: 5. データ検証・保存
        Edge->>Edge: チェックサム検証<br/>（SHA-256）
        Edge->>Edge: レコード件数検証
        Edge->>EdgeDB: MasterData保存<br/>(category, version, data, data_hash)

        Note over Edge: 6. マスタデータ適用
        Edge->>+EdgeMaster: Dapr Service Invocation<br/>POST /api/v1/sync/apply<br/>{sync_type: "full", data: {...}}
        EdgeMaster->>EdgeMaster: 既存データ削除<br/>新規データ一括投入
        EdgeMaster-->>-Edge: 適用完了<br/>{applied_count: 5432}

        Edge->>EdgeDB: SyncStatus更新<br/>(status: "success", last_sync_at, sync_type: "full")
        Edge->>EdgeDB: SyncHistory保存<br/>(completed_at, status: "success", record_count)
    end

    Note over Edge,EdgeMaster: ✅ 初回同期完了（5分以内）
```

**主要ステップ**:
1. **認証**: Edge Syncがedge_id + secretでJWT トークンを取得
2. **一括同期リクエスト**: `sync_type: "full"` で全データを要求
3. **データ収集**: Cloud SyncがMaster-dataサービスとTerminalサービスから全データを取得
4. **整形・検証**: チェックサム計算、レコード件数カウント
5. **データ検証**: Edge側でチェックサムとレコード件数を検証
6. **適用**: Edge Master-dataサービスにデータを一括投入

### フロー2: 定期同期（差分同期）

通常運用時の30-60秒間隔での差分データ取得フローです。

```mermaid
sequenceDiagram
    participant Scheduler as ⏰ APScheduler
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant Master as Master-data Service
    participant EdgeDB as Edge MongoDB
    participant EdgeMaster as Edge Master-data

    Note over Scheduler,EdgeMaster: 🔄 定期ポーリング（30-60秒間隔）

    rect rgb(255, 250, 240)
        Note right of Scheduler: 1. 定期ジョブ起動
        Scheduler->>Edge: poll_cloud_for_updates()

        Edge->>EdgeDB: SyncStatus取得<br/>(last_sync_at, next_sync_at)
        EdgeDB-->>Edge: last_sync_at: "2025-10-14T10:00:00Z"

        Note right of Edge: 2. 差分同期リクエスト
        Edge->>+Cloud: POST /api/v1/sync/request<br/>Authorization: Bearer <token><br/>{sync_type: "incremental", last_sync_at: "2025-10-14T10:00:00Z"}

        Note over Cloud: 3. 差分データ取得
        Cloud->>+Master: Dapr Service Invocation<br/>POST /api/v1/sync/changes<br/>{last_sync_timestamp: "2025-10-14T10:00:00Z"}
        Master->>Master: updated_at > last_sync_timestamp<br/>でフィルタリング
        Master-->>-Cloud: 差分データ<br/>{products: [商品3件], categories: []}

        alt 差分データあり
            Cloud-->>Edge: 差分データ + メタ情報<br/>{data: {...}, record_count: 3}

            Edge->>Edge: データ検証
            Edge->>EdgeDB: MasterData更新<br/>(version: 5433, 5434, 5435)

            Edge->>+EdgeMaster: POST /api/v1/sync/apply<br/>{sync_type: "incremental", data: {...}}
            EdgeMaster->>EdgeMaster: 既存レコード更新<br/>または新規追加
            EdgeMaster-->>-Edge: 適用完了

            Edge->>EdgeDB: SyncStatus更新<br/>(last_sync_at: now, status: "success")
        else 差分データなし
            Cloud-->>-Edge: 差分なし<br/>{data: {}, record_count: 0}
            Edge->>EdgeDB: SyncStatus更新<br/>(last_sync_at: now, status: "success")
        end
    end

    Note over Scheduler,EdgeMaster: ⏱️ 次回ポーリング: 30秒後
```

**ポーリング間隔**: 30-60秒（環境変数 `SYNC_POLL_INTERVAL` で調整可能）

**主要ステップ**:
1. **定期ジョブ起動**: APSchedulerが30-60秒間隔でポーリング実行
2. **前回同期時刻取得**: SyncStatusから `last_sync_at` を取得
3. **差分リクエスト**: `sync_type: "incremental"` + `last_sync_at` で差分のみ要求
4. **差分データ取得**: Master-dataサービスが `updated_at > last_sync_at` でフィルタリング
5. **差分適用**: 変更されたレコードのみ更新

### フロー3: バージョンギャップ補完

ネットワーク障害などで一部バージョンが欠落した場合の自動補完フローです。

```mermaid
sequenceDiagram
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant Master as Master-data Service
    participant EdgeDB as Edge MongoDB
    participant EdgeMaster as Edge Master-data

    Note over Edge,EdgeMaster: 🔧 バージョンギャップ検出・補完

    rect rgb(255, 240, 240)
        Note right of Edge: 1. ギャップ検出
        Edge->>Edge: detect_version_gaps()<br/>category: "products"
        Edge->>EdgeDB: バージョン一覧取得<br/>SELECT version FROM master_data<br/>WHERE category = "products"
        EdgeDB-->>Edge: [100, 101, 102, 105, 106]<br/>⚠️ バージョン103, 104が欠落

        Note over Edge: ギャップ数: 2件（< 20件）<br/>→ 補完同期実行
    end

    rect rgb(255, 250, 240)
        Note right of Edge: 2. 補完リクエスト
        Edge->>+Cloud: POST /api/v1/sync/request<br/>{sync_type: "complete", category: "products", missing_versions: [103, 104]}

        Cloud->>+Master: Dapr Service Invocation<br/>POST /api/v1/sync/changes<br/>{versions: [103, 104]}
        Master->>Master: バージョン指定で取得<br/>WHERE version IN (103, 104)
        Master-->>-Cloud: 補完データ<br/>{products: [v103, v104]}

        Cloud-->>-Edge: 補完データ<br/>{data: {...}, record_count: 2}
    end

    rect rgb(240, 255, 240)
        Note right of Edge: 3. 補完データ適用
        Edge->>EdgeDB: MasterData保存<br/>(version: 103, 104)
        Edge->>+EdgeMaster: POST /api/v1/sync/apply<br/>{sync_type: "incremental", data: {...}}
        EdgeMaster-->>-Edge: 適用完了

        Edge->>EdgeDB: SyncStatus更新<br/>(sync_type: "complete")
        Edge->>EdgeDB: SyncHistory保存<br/>(sync_type: "complete", record_count: 2)
    end

    Note over Edge: ✅ バージョン連続性回復<br/>[100-106] 完全

    alt ギャップ数が50件超
        Note over Edge: ⚠️ ギャップ数: 50件超<br/>→ 一括同期を推奨
        Edge->>Edge: ログに警告出力
        Edge->>Cloud: POST /api/v1/sync/request<br/>{sync_type: "full"}
    end
```

**補完ルール**:
- **最大20件/回**: 1回の補完同期で最大20バージョンまで取得
- **50件超の場合**: 一括同期への切り替えを推奨（警告ログ出力）

**主要ステップ**:
1. **ギャップ検出**: カテゴリごとにバージョン番号の連続性をチェック
2. **補完リクエスト**: 欠落バージョンを指定して `sync_type: "complete"` でリクエスト
3. **適用**: 欠落バージョンのみを取得・適用

### フロー4: ネットワーク復旧後の自動再開

オフライン状態から復旧した際の自動同期再開フローです。

```mermaid
sequenceDiagram
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant EdgeDB as Edge MongoDB

    Note over Edge,EdgeDB: 🔌 ネットワーク障害発生

    rect rgb(255, 240, 240)
        Note right of Edge: 1. オフライン状態
        Edge->>Cloud: ❌ POST /api/v1/sync/request<br/>（接続失敗）
        Edge->>Edge: サーキットブレーカー検知<br/>連続3回失敗
        Edge->>EdgeDB: SyncStatus更新<br/>(status: "failed", retry_count: 3)

        Note over Edge: ⏸️ 同期停止<br/>60秒待機（サーキットブレーカー）
    end

    rect rgb(240, 255, 240)
        Note right of Edge: 2. ネットワーク復旧
        Note over Edge: ⚡ ネットワーク復旧検知<br/>（最初の成功したHTTPリクエスト）

        Edge->>+Cloud: GET /health<br/>（ヘルスチェック）
        Cloud-->>-Edge: ✅ {"status": "healthy"}

        Note over Edge: 🔓 サーキットブレーカー<br/>半開状態

        Edge->>Edge: 復旧検知後30秒以内<br/>同期再開準備
    end

    rect rgb(255, 250, 240)
        Note right of Edge: 3. 同期自動再開
        Edge->>+Cloud: POST /api/v1/auth/token<br/>（トークン再取得）
        Cloud-->>-Edge: JWT トークン

        Edge->>+Cloud: POST /api/v1/sync/request<br/>{sync_type: "incremental", last_sync_at: "障害発生時刻"}
        Cloud-->>-Edge: 障害期間中の差分データ

        Edge->>EdgeDB: データ適用
        Edge->>EdgeDB: SyncStatus更新<br/>(status: "success", retry_count: 0)
    end

    Note over Edge,EdgeDB: ✅ 同期正常化（復旧後30秒以内）
```

**復旧検知**: エッジ端末からクラウドへの最初の成功したHTTPリクエスト完了時点

**自動再開時間**: 復旧検知後30秒以内（SC-006）

**主要ステップ**:
1. **オフライン検知**: 連続3回失敗でサーキットブレーカーがオープン
2. **復旧検知**: 最初の成功したHTTPリクエスト（ヘルスチェック等）で検知
3. **自動再開**: トークン再取得 → 差分同期実行

## データ整合性保証の仕組み

### チェックサム検証（FR-006）

```mermaid
graph LR
    A[Cloud Sync] -->|1. データ送信| B[マスタデータ]
    A -->|2. チェックサム計算| C[SHA-256 Hash]
    B --> D[Edge Sync]
    C --> D
    D -->|3. 再計算| E[SHA-256 Hash]
    D -->|4. 比較| F{一致?}
    F -->|Yes| G[✅ 適用]
    F -->|No| H[❌ リトライ<br/>最大3回]
    H -->|3回失敗| I[⚠️ エラーログ<br/>管理者通知]
```

**検証アルゴリズム**:
```python
# Cloud側でチェックサム計算
data_json = json.dumps(data, sort_keys=True)
checksum = hashlib.sha256(data_json.encode()).hexdigest()

# Edge側で検証
received_checksum = response["checksum"]
calculated_checksum = calculate_checksum(response["data"])
if received_checksum != calculated_checksum:
    raise ChecksumMismatchError()
```

### レコード件数検証（FR-007）

```mermaid
graph LR
    A[Cloud Sync] -->|1. データ送信| B[products: 1234件]
    A -->|2. 件数カウント| C[record_count: 1234]
    B --> D[Edge Sync]
    C --> D
    D -->|3. 再カウント| E[len products: 1234]
    D -->|4. 比較| F{一致?}
    F -->|Yes| G[✅ 適用]
    F -->|No| H[❌ ロールバック<br/>リトライ]
```

**検証タイミング**:
- Cloud側: データ送信前にカウント
- Edge側: 受信後、DB保存前に再カウント
- 不一致時: トランザクションロールバック → リトライ

## データベース構造

### SyncStatus（同期状態管理）

マスタデータ同期の現在状態を追跡するコレクション：

```
コレクション: status_sync

ドキュメント例:
{
  "_id": ObjectId("..."),
  "edge_id": "edge-tenant001-store001-001",
  "data_type": "master_data",
  "last_sync_at": ISODate("2025-10-14T10:30:00Z"),
  "sync_type": "incremental",
  "status": "success",
  "retry_count": 0,
  "error_message": null,
  "next_sync_at": ISODate("2025-10-14T10:31:00Z"),
  "created_at": ISODate("2025-10-14T08:00:00Z"),
  "updated_at": ISODate("2025-10-14T10:30:00Z")
}
```

**インデックス**:
- `{edge_id: 1, data_type: 1}` (unique) - エッジ端末・データ種別での検索
- `{status: 1, next_sync_at: 1}` - ポーリングジョブ用

### SyncHistory（同期履歴）

各同期実行の監査ログ：

```
コレクション: info_sync_history

ドキュメント例:
{
  "_id": ObjectId("..."),
  "sync_id": "550e8400-e29b-41d4-a716-446655440000",
  "edge_id": "edge-tenant001-store001-001",
  "data_type": "master_data",
  "sync_type": "incremental",
  "direction": "cloud_to_edge",
  "started_at": ISODate("2025-10-14T10:30:00Z"),
  "completed_at": ISODate("2025-10-14T10:30:15Z"),
  "record_count": 12,
  "data_size_bytes": 45678,
  "status": "success",
  "error_detail": null,
  "retry_count": 0,
  "duration_ms": 15000
}
```

**保持期間**: 90日間（TTLインデックス）

### MasterData（マスタデータキャッシュ）

エッジ端末に同期されたマスタデータ：

```
コレクション: cache_master_data

ドキュメント例:
{
  "_id": ObjectId("..."),
  "category": "products_common",
  "version": 5433,
  "updated_at": ISODate("2025-10-14T10:30:00Z"),
  "data": {
    "product_id": "P001",
    "name": "商品A",
    "price": 1000,
    ...
  },
  "data_hash": "abc123...",
  "record_count": 1
}
```

**バージョン管理**: カテゴリごとに連続したバージョン番号で管理

## パフォーマンス指標

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| **同期遅延** | 95パーセンタイルで5分以内 | Cloud側でマスタ更新 → Edge側で適用完了までの時間 |
| **スループット（全件）** | 10,000件/秒以上 | 初回一括同期時のレコード処理速度 |
| **スループット（差分）** | 1,000件/秒以上 | 定期差分同期時のレコード処理速度 |
| **チェックサム検証成功率** | 99.9%以上 | 検証成功回数 / 全同期回数 |
| **ネットワーク復旧後の再開** | 30秒以内 | 復旧検知 → 同期再開までの時間 |

## エラーハンドリング

### リトライ戦略

```mermaid
graph TD
    A[同期実行] -->|失敗| B{retry_count < 5?}
    B -->|Yes| C[指数バックオフ待機]
    C -->|1秒 → 2秒 → 4秒 → 8秒 → 16秒| D[リトライ実行]
    D --> A
    B -->|No| E[❌ 最大リトライ超過]
    E --> F[エラーログ記録]
    F --> G[管理者通知]
    A -->|成功| H[✅ retry_count = 0]
```

**指数バックオフ**: 1秒 → 2秒 → 4秒 → 8秒 → 16秒（最大5回）

### サーキットブレーカー

```mermaid
stateDiagram-v2
    [*] --> Closed: 初期状態
    Closed --> Open: 連続3回失敗
    Open --> HalfOpen: 60秒経過
    HalfOpen --> Closed: 成功
    HalfOpen --> Open: 失敗

    note right of Closed: 通常動作<br/>すべてのリクエスト実行
    note right of Open: 回路開放<br/>リクエスト即座に失敗
    note right of HalfOpen: 復旧テスト<br/>1件のみ実行して判定
```

**しきい値**: 連続3回失敗でオープン

**回復時間**: 60秒後に半開状態

## 受入シナリオの検証

### シナリオ1: 新商品登録の同期

```
Given: クラウド側で新商品を登録
When: 60秒経過後
Then: すべてのエッジ端末で新商品が利用可能

検証方法:
1. Master-data Serviceで商品追加 (product_id: "P999")
2. Edge Sync のポーリング待機（最大60秒）
3. Edge Master-data Service のDBを確認
4. 商品 P999 が存在することを確認
```

### シナリオ2: オフライン時の更新・復旧後自動同期

```
Given: エッジ端末がオフライン状態
When: クラウド側でマスターデータを更新
Then: オンライン復旧後30秒以内に自動同期完了

検証方法:
1. Edge Sync のネットワーク接続を切断
2. Master-data Service で価格更新（10件）
3. Edge Sync のネットワーク接続を復旧
4. 復旧検知からの経過時間を測定
5. 30秒以内に10件の価格更新が反映されることを確認
```

### シナリオ3: 初期セットアップ・一括同期

```
Given: 初期セットアップ時
When: 一括同期を実行
Then: すべてのマスターデータが5分以内に同期完了

検証方法:
1. 新規エッジ端末を登録（edge_id, secret）
2. Edge Sync 起動 → 認証 → 一括同期実行
3. 開始時刻と完了時刻を記録
4. 全カテゴリ（categories, products, staff, payment_methods, tax_rules）のデータ件数を確認
5. 処理時間が5分以内であることを確認
```

### シナリオ4: 差分同期

```
Given: 定期同期実行中
When: 差分データが存在
Then: 差分のみが30秒間隔で同期される

検証方法:
1. 定期ポーリング中のEdge Syncを監視
2. Master-data Serviceで商品3件を更新
3. 次回ポーリング（30-60秒後）を待機
4. Edge側で更新された3件のみが適用されることを確認
5. SyncHistoryで record_count: 3 を確認
```

## 関連ドキュメント

- [spec.md](./spec.md) - 機能仕様書
- [plan.md](./plan.md) - 実装計画
- [data-model.md](./data-model.md) - データモデル設計
- [contracts/sync-api.yaml](./contracts/sync-api.yaml) - 同期API仕様
- [contracts/auth-api.yaml](./contracts/auth-api.yaml) - 認証API仕様

---

**ドキュメントバージョン**: 1.0.0
**最終更新日**: 2025-10-14
**ステータス**: 完成

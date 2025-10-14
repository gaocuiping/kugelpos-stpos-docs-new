# ユーザーストーリー2: コンテナイメージの差分更新 - 処理フロー図

## 概要

このドキュメントは、ユーザーストーリー2「コンテナイメージの差分更新」の処理フローを視覚的に説明します。マイクロサービス（account, cart, sync等）のコンテナイメージが更新された際、変更されたサービスのイメージのみを効率的にダウンロードし、Dockerのレイヤーキャッシュを活用して帯域を削減する仕組みを、ユーザーが理解しやすい形で図解します。

## シナリオ

マイクロサービス（account, terminal, master-data, cart, report, journal, stock, sync）のコンテナイメージが更新された際、変更されたサービスのイメージのみを効率的にダウンロードし、Dockerのレイヤーキャッシュを活用して帯域を削減する。

## 主要コンポーネント

```mermaid
graph TB
    subgraph Cloud["☁️ クラウド環境"]
        CloudSync["Sync Service<br/>（Cloud Mode）"]
        MongoDB_Cloud[("MongoDB<br/>sync_tenant001")]
        PrimaryRegistry["Primary Container Registry<br/>（メインレジストリ）"]
        FallbackRegistry["Fallback Container Registry<br/>（バックアップレジストリ）"]
    end

    subgraph Edge["🏪 店舗環境（エッジ端末）"]
        EdgeSync["Sync Service<br/>（Edge Mode）"]
        Docker["Docker Engine<br/>（レイヤーキャッシュ）"]
        Services["マイクロサービス<br/>（account, cart, sync等）"]
        LocalRegistry["Local Registry<br/>（pullしたイメージ）"]
    end

    CloudSync <-->|JWT認証<br/>REST API| EdgeSync
    CloudSync --> MongoDB_Cloud
    CloudSync -.-> PrimaryRegistry
    CloudSync -.-> FallbackRegistry
    EdgeSync --> Docker
    Docker -.->|docker pull| PrimaryRegistry
    Docker -.->|フォールバック| FallbackRegistry
    Docker --> LocalRegistry
    Docker --> Services
```

## 処理フロー全体

### フロー1: 差分イメージのダウンロード（変更1サービスのみ）

8つのサービスのうち1つ（例: cart）のみが更新された際の差分ダウンロードフローです。

```mermaid
sequenceDiagram
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant EdgeDB as Edge MongoDB
    participant Docker as Docker Engine
    participant PrimaryReg as Primary Registry
    participant FallbackReg as Fallback Registry

    Note over Edge,FallbackReg: 🔄 バージョンチェック（15分ごと）

    rect rgb(240, 240, 255)
        Note right of Edge: 1. バージョンチェック
        Edge->>EdgeDB: DeviceVersion取得
        EdgeDB-->>Edge: current_version: "1.2.2"<br/>適用中イメージ:<br/>- account:1.2.2<br/>- cart:1.2.2<br/>- sync:1.2.2<br/>...（全8サービス）

        Edge->>+Cloud: POST /api/v1/version/check<br/>{edge_id, device_type, current_version: "1.2.2"}

        Cloud->>MongoDB_Cloud: バージョン比較<br/>target_version: "1.2.3"

        Note over Cloud: 差分検出:<br/>- cart: 1.2.2 → 1.2.3（更新あり）<br/>- 他7サービス: 変更なし
    end

    rect rgb(255, 250, 240)
        Note right of Cloud: 2. Manifest生成（差分のみ）
        Cloud-->>-Edge: Manifest返却<br/>{<br/>  target_version: "1.2.3",<br/>  container_images: [<br/>    {service: "cart", version: "1.2.3",<br/>     primary_registry: "registry.example.com",<br/>     primary_image: "kugelpos/cart:1.2.3",<br/>     fallback_registry: "backup-registry.example.com",<br/>     fallback_image: "kugelpos/cart:1.2.3",<br/>     checksum: "sha256:abc123..."}<br/>  ],<br/>  apply_schedule: {scheduled_at: "2025-10-15T02:00:00Z"}<br/>}

        Note over Edge: ✅ cart イメージのみが<br/>ダウンロード対象
    end

    rect rgb(240, 255, 240)
        Note right of Edge: 3. 差分イメージダウンロード（営業時間中）

        Edge->>EdgeDB: DeviceVersion更新<br/>(update_status: "downloading", download_status: "in_progress")

        Edge->>Docker: docker pull registry.example.com/kugelpos/cart:1.2.3

        alt Primary Registry成功
            Docker->>+PrimaryReg: レイヤー要求<br/>（既存レイヤーはスキップ）
            PrimaryReg-->>-Docker: 差分レイヤーのみ返却<br/>（レイヤーキャッシュ活用）

            Note over Docker: Dockerレイヤーキャッシュ:<br/>- 既存レイヤー（共通部分）: スキップ<br/>- 新規レイヤー（差分部分）: ダウンロード<br/>→ 帯域削減率85%以上（SC-004）

            Docker-->>Edge: ダウンロード完了<br/>（差分レイヤーのみ、約60MB）
        else Primary Registry失敗
            Docker->>PrimaryReg: ❌ レイヤー要求失敗<br/>（タイムアウト/ネットワークエラー）

            Note over Edge: フォールバック実行
            Edge->>Docker: docker pull backup-registry.example.com/kugelpos/cart:1.2.3

            Docker->>+FallbackReg: レイヤー要求
            FallbackReg-->>-Docker: 差分レイヤー返却
            Docker-->>Edge: ダウンロード完了<br/>（Fallback Registry経由）
        end

        Edge->>Docker: docker inspect kugelpos/cart:1.2.3<br/>（イメージダイジェスト取得）
        Docker-->>Edge: sha256:abc123...

        Edge->>Edge: ダイジェスト検証<br/>（Manifestのchecksumと比較）

        alt ダイジェスト一致
            Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "completed", download_completed_at: now)
            Edge->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3", artifacts_count: 1, total_size_bytes: 60000000}
            Cloud-->>-Edge: 通知受信確認

            Note over Edge: ✅ ダウンロード完了<br/>（差分1イメージのみ、約60MB）
        else ダイジェスト不一致
            Edge->>Docker: docker rmi kugelpos/cart:1.2.3<br/>（不正イメージ削除）
            Edge->>Edge: リトライカウンタ増加

            alt retry_count < 3
                Note over Edge: 🔄 指数バックオフ後リトライ
                Edge->>Docker: docker pull 再実行
            else retry_count >= 3
                Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "failed", error_message: "Digest mismatch")
                Edge->>Cloud: POST /api/v1/error-report
                Note over Edge: ❌ ダウンロード失敗
            end
        end
    end

    Note over Edge,FallbackReg: ⏱️ 差分イメージダウンロード完了（約2分）<br/>全サービス更新（3200MB）と比較して帯域削減率87.5%
```

**主要ステップ**:
1. **バージョンチェック**: クラウド側で変更されたサービスを検出（cart: 1.2.2 → 1.2.3）
2. **Manifest生成**: 変更されたサービスのイメージのみを含むManifestを返却
3. **差分ダウンロード**: Dockerレイヤーキャッシュを活用して差分レイヤーのみダウンロード
4. **ダイジェスト検証**: イメージダイジェスト（SHA256）がManifestの値と一致することを確認

**帯域削減効果**:
- 全サービス更新時: 3200MB（8サービス × 400MB）
- 差分更新時（1サービス）: 約60MB（Dockerレイヤーキャッシュ活用）
- 削減率: 約98%（実際の差分レイヤーサイズに依存）

### フロー2: 適用フェーズ（変更サービスのみ再起動）

ダウンロード完了後、メンテナンスウィンドウ内に変更されたサービスのみを再起動するフローです。

```mermaid
sequenceDiagram
    participant Scheduler as ⏰ APScheduler
    participant Edge as 🏪 Edge Sync
    participant EdgeDB as Edge MongoDB
    participant Docker as Docker Compose
    participant CartSvc as Cart Service
    participant OtherSvc as Other Services<br/>（account, sync等）
    participant Cloud as ☁️ Cloud Sync

    Note over Scheduler,Cloud: 🌙 メンテナンスウィンドウ開始（02:00）

    rect rgb(255, 240, 240)
        Note right of Scheduler: 1. 適用準備
        Scheduler->>Edge: apply_pending_update()

        Edge->>EdgeDB: DeviceVersion取得<br/>(pending_version: "1.2.3")

        Edge->>Edge: Manifest解析<br/>変更サービス: cart のみ

        Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "in_progress")
        Edge->>EdgeDB: UpdateHistory作成<br/>(update_id, from_version: "1.2.2", to_version: "1.2.3")
    end

    rect rgb(240, 240, 255)
        Note right of Edge: 2. 変更サービスのみ停止

        Edge->>Docker: docker-compose stop cart
        Docker->>CartSvc: SIGTERM送信
        CartSvc-->>Docker: グレースフルシャットダウン完了
        Docker-->>Edge: cart 停止完了

        Note over OtherSvc: ✅ 他7サービスは<br/>稼働継続
        Note over Edge: ⏸️ ダウンタイム開始<br/>（cartサービスのみ、目標: 1分以内）
    end

    rect rgb(255, 250, 240)
        Note right of Edge: 3. 新バージョン適用

        Edge->>Docker: docker-compose up -d cart<br/>（新イメージで起動）
        Docker->>CartSvc: kugelpos/cart:1.2.3 でコンテナ起動
        CartSvc-->>Docker: 起動完了
        Docker-->>Edge: cart 起動完了

        Note over Edge: ⏯️ cartサービス再起動完了
    end

    rect rgb(240, 255, 240)
        Note right of Edge: 4. ヘルスチェック

        loop 最大3回、10秒間隔
            Edge->>CartSvc: GET /health

            alt ヘルスチェック成功
                CartSvc-->>Edge: {"status": "healthy"}
                Note over Edge: ✅ cartサービス正常
            else ヘルスチェック失敗
                CartSvc-->>Edge: タイムアウトまたは500エラー

                alt 最終リトライで失敗
                    Note over Edge: ❌ ロールバック実行
                    Edge->>Docker: docker-compose stop cart
                    Edge->>Docker: docker tag kugelpos/cart:1.2.2 kugelpos/cart:current
                    Edge->>Docker: docker-compose up -d cart<br/>（旧バージョンで起動）

                    Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "rolled_back", current_version: "1.2.2")
                    Edge->>Cloud: POST /api/v1/apply-failed
                    Note over Edge: ⚠️ ロールバック完了
                end
            end
        end
    end

    rect rgb(240, 255, 240)
        Note right of Edge: 5. 完了通知

        Edge->>EdgeDB: DeviceVersion更新<br/>(current_version: "1.2.3", apply_status: "completed", apply_completed_at: now)

        Edge->>EdgeDB: UpdateHistory更新<br/>(end_time: now, status: "success", downtime_seconds: 45)

        Edge->>+Cloud: POST /api/v1/apply-complete<br/>{edge_id, version: "1.2.3", downtime_seconds: 45, updated_services: ["cart"]}
        Cloud-->>-Edge: 通知受信確認

        Note over Edge: ✅ 更新完了（ダウンタイム: 45秒）<br/>他7サービスは無停止
    end

    Note over Scheduler,Cloud: ⏱️ 変更サービスのみ再起動・ダウンタイム最小化
```

**主要ステップ**:
1. **適用準備**: Manifestを解析して変更されたサービス（cart）を特定
2. **変更サービスのみ停止**: cartサービスのみ停止（他7サービスは稼働継続）
3. **新バージョン適用**: cartサービスを新イメージ（1.2.3）で起動
4. **ヘルスチェック**: cartサービスの正常性確認、失敗時はロールバック
5. **完了通知**: クラウドに適用完了を通知

**ダウンタイム**:
- 変更サービスのみ: 約45秒（1サービス）
- 全サービス更新時: 約2-3分（8サービス）
- ダウンタイム削減効果: 約75%

### フロー3: 初回セットアップ（全イメージダウンロード）

新規エッジ端末設置時の全イメージダウンロードフローです。

```mermaid
sequenceDiagram
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant EdgeDB as Edge MongoDB
    participant Docker as Docker Engine
    participant Registry as Container Registry

    Note over Edge,Registry: 🚀 初回セットアップ

    rect rgb(240, 240, 255)
        Note right of Edge: 1. 初回バージョンチェック
        Edge->>+Cloud: POST /api/v1/version/check<br/>{edge_id, device_type, current_version: null}

        Cloud->>Cloud: 初回セットアップ検出<br/>（current_version: null）

        Cloud-->>-Edge: Manifest返却<br/>{<br/>  target_version: "1.2.3",<br/>  container_images: [<br/>    {service: "account", version: "1.2.3", ...},<br/>    {service: "terminal", version: "1.2.3", ...},<br/>    {service: "master-data", version: "1.2.3", ...},<br/>    {service: "cart", version: "1.2.3", ...},<br/>    {service: "report", version: "1.2.3", ...},<br/>    {service: "journal", version: "1.2.3", ...},<br/>    {service: "stock", version: "1.2.3", ...},<br/>    {service: "sync", version: "1.2.3", ...}<br/>  ]<br/>}

        Note over Edge: ✅ 全8サービスイメージが<br/>ダウンロード対象
    end

    rect rgb(255, 250, 240)
        Note right of Edge: 2. 全イメージダウンロード

        Edge->>EdgeDB: DeviceVersion作成<br/>(target_version: "1.2.3", update_status: "downloading")

        loop 全8サービス（並列実行可能）
            Edge->>Docker: docker pull registry.example.com/kugelpos/{service}:1.2.3

            Docker->>+Registry: イメージレイヤー要求<br/>（全レイヤーダウンロード）
            Registry-->>-Docker: 全レイヤー返却<br/>（1サービスあたり約400MB）

            Docker-->>Edge: {service} ダウンロード完了
        end

        Note over Edge: ✅ 全8サービスイメージ<br/>ダウンロード完了（約3200MB）<br/>目標: 10分以内（SC-003）
    end

    rect rgb(240, 255, 240)
        Note right of Edge: 3. ダイジェスト検証

        loop 全8サービス
            Edge->>Docker: docker inspect kugelpos/{service}:1.2.3
            Docker-->>Edge: sha256:xyz789...

            Edge->>Edge: ダイジェスト検証<br/>（Manifestのchecksumと比較）
        end

        Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "completed", download_completed_at: now)

        Edge->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3", artifacts_count: 8, total_size_bytes: 3200000000}
        Cloud-->>-Edge: 通知受信確認

        Note over Edge: ✅ 初回ダウンロード完了<br/>適用待ち状態
    end

    Note over Edge,Registry: ⏱️ 全8サービスイメージダウンロード完了（約10分）
```

**主要ステップ**:
1. **初回バージョンチェック**: `current_version: null` で全イメージが対象
2. **全イメージダウンロード**: 8サービス × 400MB ≈ 3200MB をダウンロード
3. **ダイジェスト検証**: 全イメージのダイジェストを検証

**パフォーマンス**:
- 目標: 10分以内（SC-003）
- 実際のダウンロード時間はネットワーク帯域に依存

## Dockerレイヤーキャッシュの仕組み

### レイヤーキャッシュ活用例

```mermaid
graph TB
    subgraph Old["旧バージョン cart:1.2.2<br/>（既存ローカル）"]
        L1["Layer 1: Base OS<br/>（Ubuntu 22.04）<br/>200MB"]
        L2["Layer 2: Python 3.12<br/>100MB"]
        L3["Layer 3: Dependencies<br/>（Pipenv）<br/>80MB"]
        L4["Layer 4: App Code v1.2.2<br/>20MB"]
    end

    subgraph New["新バージョン cart:1.2.3<br/>（ダウンロード対象）"]
        N1["Layer 1: Base OS<br/>（Ubuntu 22.04）<br/>200MB - ✅ キャッシュヒット"]
        N2["Layer 2: Python 3.12<br/>100MB - ✅ キャッシュヒット"]
        N3["Layer 3: Dependencies<br/>（Pipenv）<br/>80MB - ✅ キャッシュヒット"]
        N4["Layer 4: App Code v1.2.3<br/>20MB - ⬇️ ダウンロード"]
    end

    L1 -.->|"再利用（SHA256一致）"| N1
    L2 -.->|"再利用（SHA256一致）"| N2
    L3 -.->|"再利用（SHA256一致）"| N3
    L4 -.->|"変更あり"| N4

    style N1 fill:#d4edda
    style N2 fill:#d4edda
    style N3 fill:#d4edda
    style N4 fill:#fff3cd
```

**レイヤーキャッシュ効果**:
- 旧バージョン全体: 400MB
- 新バージョン全体: 400MB
- 実際のダウンロード: 20MB（差分レイヤーのみ）
- 削減率: 95%（= 380MB / 400MB）

### docker pull 実行時の動作

```
$ docker pull registry.example.com/kugelpos/cart:1.2.3

1.2.3: Pulling from kugelpos/cart
Layer 1 (sha256:abc123...): Already exists  ← キャッシュヒット
Layer 2 (sha256:def456...): Already exists  ← キャッシュヒット
Layer 3 (sha256:ghi789...): Already exists  ← キャッシュヒット
Layer 4 (sha256:jkl012...): Downloading     ← 差分ダウンロード
Layer 4 (sha256:jkl012...): Download complete
Digest: sha256:xyz789...
Status: Downloaded newer image for registry.example.com/kugelpos/cart:1.2.3
```

**検証ポイント**:
- 各レイヤーはSHA256ハッシュで識別
- ローカルに同じSHA256のレイヤーが存在すれば再利用
- 変更されたレイヤーのみダウンロード

## データベース構造

### DeviceVersion（イメージバージョン管理）

```
コレクション: info_edge_version

ドキュメント例（差分更新時）:
{
  "_id": ObjectId("..."),
  "edge_id": "edge-tenant001-store001-001",
  "device_type": "edge",
  "current_version": "1.2.3",
  "target_version": "1.2.3",
  "update_status": "completed",
  "download_status": "completed",
  "download_completed_at": ISODate("2025-10-14T16:05:00Z"),
  "apply_status": "completed",
  "apply_completed_at": ISODate("2025-10-15T02:01:00Z"),
  "updated_services": ["cart"],  // 差分更新時のみ記録
  "total_size_bytes": 60000000,  // 実際のダウンロードサイズ（レイヤーキャッシュ後）
  "artifacts_count": 1,
  "retry_count": 0,
  "error_message": null,
  "created_at": ISODate("2025-10-01T00:00:00Z"),
  "updated_at": ISODate("2025-10-15T02:01:00Z")
}
```

**差分更新の記録**:
- `updated_services`: 更新されたサービスのリスト
- `total_size_bytes`: 実際のダウンロードサイズ（レイヤーキャッシュ適用後）
- `artifacts_count`: ダウンロードしたイメージ数

## パフォーマンス指標

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| **全イメージダウンロード時間** | 10分以内 | 初回セットアップ時の全8サービスダウンロード時間（合計3200MB） |
| **差分イメージダウンロード時間** | 2分以内 | 1サービス更新時のダウンロード時間（レイヤーキャッシュ適用後） |
| **帯域削減率（差分更新）** | 85%以上 | (全サービス更新時のサイズ - 差分更新時のサイズ) / 全サービス更新時のサイズ |
| **ダウンタイム（差分適用）** | 1分以内 | 変更サービスのみ停止・再起動（他サービス稼働継続） |
| **ダイジェスト検証成功率** | 99.9%以上 | 検証成功回数 / 全ダウンロード回数 |

**帯域削減率の計算例**:
- 全サービス更新: 3200MB（8サービス × 400MB）
- 差分更新（1サービス、レイヤーキャッシュ適用後）: 約60MB
- 削減率: (3200 - 60) / 3200 = 98.1%

## エラーハンドリング

### レジストリアクセス失敗時のフォールバック

```mermaid
graph TD
    A[docker pull開始] --> B{Primary Registry}
    B -->|成功| C[✅ ダウンロード完了]
    B -->|失敗| D[Fallback Registry試行]
    D -->|成功| C
    D -->|失敗| E{retry_count < 3?}
    E -->|Yes| F[指数バックオフ待機]
    F --> A
    E -->|No| G[❌ ダウンロード失敗]
    G --> H[エラー記録・通知]
```

**フォールバック戦略**:
1. Primary Registryからダウンロード試行
2. 失敗時はFallback Registryへ自動切り替え
3. 両方失敗時は指数バックオフでリトライ（最大3回）

### ダイジェスト検証失敗時のリトライ

```mermaid
graph TD
    A[イメージダウンロード完了] --> B[docker inspect実行]
    B --> C{ダイジェスト一致?}
    C -->|Yes| D[✅ 検証成功]
    C -->|No| E[docker rmi実行<br/>不正イメージ削除]
    E --> F{retry_count < 3?}
    F -->|Yes| G[指数バックオフ待機]
    G --> A
    F -->|No| H[❌ 検証失敗<br/>エラー通知]
```

**検証失敗時の対応**:
1. 不正なイメージをローカルから削除（`docker rmi`）
2. リトライカウンタ増加
3. 指数バックオフ後に再ダウンロード（最大3回）
4. 3回失敗後はクラウドにエラー通知

## 受入シナリオの検証

### シナリオ1: 1サービスのみ更新（差分ダウンロード）

```
Given: 8つのサービスのうちcartサービスのみv1.2.3に更新
When: エッジ端末がバージョンチェック実行
Then:
  1. cartイメージのみがダウンロード対象として返却される
  2. Dockerレイヤーキャッシュにより差分のみダウンロード（全サービス更新と比較して帯域を大幅に削減）
  3. 適用時はcartサービスのみ再起動、他サービスは稼働継続

検証方法:
1. Cloud側でcartサービスのみv1.2.3に更新
2. Edge Sync のバージョンチェック実行
3. Manifestにcartイメージのみが含まれることを確認
4. docker pull実行時、レイヤーキャッシュが活用されることを確認（ログ出力: "Already exists"）
5. ダウンロードサイズを測定（目標: 全サービス更新時の15%以下）
6. 適用時、cartサービスのみ再起動されることを確認
```

### シナリオ2: 初回セットアップ（全イメージダウンロード）

```
Given: 初回セットアップ時
When: 全イメージダウンロード
Then: 10分以内に全8サービスのイメージ取得完了

検証方法:
1. 新規エッジ端末を登録（edge_id, secret）
2. Edge Sync 起動 → 認証 → バージョンチェック実行（current_version: null）
3. Manifestに全8サービスイメージが含まれることを確認
4. 開始時刻と完了時刻を記録
5. 全イメージダウンロード完了時刻を確認（目標: 10分以内）
6. 各イメージのダイジェスト検証が成功することを確認
```

### シナリオ3: レイヤーキャッシュの効果検証

```
Given: cartイメージの前バージョン（v1.2.2）が既に存在
When: v1.2.3をpull
Then: Dockerレイヤーキャッシュにより差分のみダウンロード

検証方法:
1. Edge Sync で cart:1.2.2 を適用済みの状態
2. docker images でローカルイメージを確認
3. Cloud側で cart:1.2.3 を登録（アプリコードのみ変更、ベースイメージは同じ）
4. Edge Sync で cart:1.2.3 をダウンロード
5. docker pull のログ出力を確認:
   - "Already exists" が複数回表示される（共通レイヤー）
   - "Downloading" は差分レイヤーのみ
6. ダウンロードサイズを測定:
   - 全レイヤーサイズ: 400MB
   - 実際のダウンロード: 約20-60MB
   - 削減率: 85%以上
```

### シナリオ4: Primary Registry失敗時のフォールバック

```
Given: Primary Registryがダウン
When: イメージダウンロード実行
Then: Fallback Registryから自動的にダウンロード

検証方法:
1. Primary Registry を意図的に停止
2. Edge Sync でバージョンチェック → ダウンロード実行
3. docker pull のログで Primary Registry への接続失敗を確認
4. 自動的に Fallback Registry へフォールバックすることを確認
5. Fallback Registry からダウンロード完了することを確認
6. DeviceVersion に成功として記録されることを確認
```

## 関連ドキュメント

- [spec.md](../spec.md) - 機能仕様書
- [plan.md](../plan.md) - 実装計画
- [data-model.md](../data-model.md) - データモデル設計
- [contracts/sync-api.yaml](../contracts/sync-api.yaml) - Sync API仕様

---

**ドキュメントバージョン**: 1.0.0
**最終更新日**: 2025-10-14
**ステータス**: 完成

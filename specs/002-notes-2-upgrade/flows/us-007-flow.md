# ユーザーストーリー7: 2段階更新による業務影響最小化 - 処理フロー図

## 概要

このドキュメントは、ユーザーストーリー7「2段階更新による業務影響最小化」の処理フローを視覚的に説明します。店舗のエッジ端末（Edge/POS）が、営業時間中に新バージョンのダウンロードを完了し（ダウンロードフェーズ）、管理者が指定したメンテナンスウィンドウ（scheduled_at開始時刻、maintenance_window期間）内に自動適用される（適用フェーズ）仕組みを、ユーザーが理解しやすい形で図解します。

## シナリオ

店舗のエッジ端末（Edge/POS）が、営業時間中に新バージョンのダウンロードを完了し（ダウンロードフェーズ）、管理者が指定したメンテナンスウィンドウ（scheduled_at開始時刻、maintenance_window期間）内に自動適用される（適用フェーズ）。ダウンロードと適用を分離することで、営業時間中のダウンロード時間（1-10分）は業務に影響を与えず、サービス停止は適用時の1-3分のみに抑えられる。

## 主要コンポーネント

```mermaid
graph TB
    subgraph Cloud["☁️ クラウド環境"]
        CloudSync["Sync Service<br/>（Cloud Mode）"]
        MongoDB_Cloud[("MongoDB<br/>sync_tenant001")]
    end

    subgraph Edge["🏪 店舗環境（エッジ端末）"]
        EdgeSync["Sync Service<br/>（Edge Mode）"]
        Scheduler["APScheduler<br/>（定期ジョブ）"]
        DownloadPhase["ダウンロードフェーズ<br/>（Phase 1-3）<br/>営業時間中・サービス無停止"]
        ApplyPhase["適用フェーズ<br/>（Phase 4-9）<br/>メンテナンスウィンドウ内"]
        Services["マイクロサービス<br/>（稼働中）"]
    end

    CloudSync <-->|REST API| EdgeSync
    CloudSync --> MongoDB_Cloud
    Scheduler --> EdgeSync
    EdgeSync --> DownloadPhase
    EdgeSync --> ApplyPhase
    DownloadPhase -.->|サービス無停止| Services
    ApplyPhase -->|サービス停止<br/>1-3分| Services
```

## 処理フロー全体

### フロー1: 2段階更新の全体像

ダウンロードフェーズ（Phase 1-3）と適用フェーズ（Phase 4-9）を分離した全体フローです。

```mermaid
sequenceDiagram
    participant Clock as ⏰ 時刻
    participant Scheduler as APScheduler
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant Services as Microservices
    participant EdgeDB as Edge MongoDB

    Note over Clock,EdgeDB: 📅 2段階更新の全体像

    rect rgb(240, 255, 240)
        Note over Clock: 営業時間中（14:00）
        Note over Services: ✅ 全サービス稼働中<br/>（業務継続）

        rect rgb(255, 250, 240)
            Note right of Scheduler: ダウンロードフェーズ（Phase 1-3）
            Scheduler->>Edge: check_for_updates()<br/>（15分ごと）

            Edge->>+Cloud: POST /api/v1/version/check<br/>{edge_id, current_version: "1.2.2"}

            Cloud-->>-Edge: Manifest返却<br/>{target_version: "1.2.3",<br/> artifacts: [...], container_images: [...],<br/> apply_schedule: {<br/>   scheduled_at: "2025-10-15T02:00:00Z",<br/>   maintenance_window: 30<br/> }}

            Note over Edge: ✅ Manifest受信<br/>適用予定: 深夜2:00<br/>メンテナンスウィンドウ: 30分

            Edge->>Edge: Phase 1: バージョンチェック完了

            Edge->>Cloud: GET /api/v1/artifacts/...<br/>GET /api/v1/artifacts/...

            Edge->>Edge: Phase 2: ダウンロード実行<br/>（ファイル・イメージ）

            Edge->>Edge: Phase 3: チェックサム検証

            Edge->>EdgeDB: DeviceVersion更新<br/>(update_status: "pending_apply",<br/> download_status: "completed",<br/> scheduled_apply_at: "2025-10-15T02:00:00Z")

            Edge->>EdgeDB: PendingUpdate保存<br/>(/opt/kugelpos/pending-updates/v1.2.3/status.json)

            Note over Edge: ✅ ダウンロードフェーズ完了<br/>（所要時間: 5分）
            Note over Services: ✅ サービス無停止<br/>業務継続中
        end
    end

    rect rgb(255, 240, 240)
        Note over Clock: 深夜・メンテナンスウィンドウ開始（02:00）
        Note over Services: ⏸️ メンテナンスウィンドウ突入<br/>（scheduled_at到達）

        rect rgb(240, 240, 255)
            Note right of Scheduler: 適用フェーズ（Phase 4-9）
            Scheduler->>Edge: apply_pending_update()<br/>（scheduled_at到達時）

            Edge->>EdgeDB: PendingUpdate取得<br/>(/opt/kugelpos/pending-updates/v1.2.3/)

            Edge->>Edge: メンテナンスウィンドウ確認<br/>(scheduled_at <= now < scheduled_at + 30分)

            alt ウィンドウ内
                Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "in_progress")

                Edge->>Edge: Phase 4: バックアップ<br/>（現行バージョン）

                Edge->>Edge: Phase 5: 適用準備<br/>（ファイル配置準備）

                Edge->>Services: Phase 6: サービス停止<br/>docker-compose down

                Note over Services: ⏸️ ダウンタイム開始<br/>（目標: 1-3分）

                Edge->>Edge: Phase 7: 新バージョン適用<br/>（ファイル配置・サービス起動）

                Edge->>Services: Phase 8: ヘルスチェック<br/>GET /health（全サービス）

                Note over Services: ⏯️ サービス再起動完了

                Edge->>EdgeDB: DeviceVersion更新<br/>(current_version: "1.2.3",<br/> apply_status: "completed",<br/> apply_completed_at: now)

                Edge->>+Cloud: Phase 9: 完了通知<br/>POST /api/v1/apply-complete
                Cloud-->>-Edge: 通知受信確認

                Note over Edge: ✅ 適用フェーズ完了<br/>（ダウンタイム: 2分30秒）
            else ウィンドウ外
                Note over Edge: ⏭️ 適用スキップ<br/>次回スケジュールまで待機
            end
        end

        Note over Clock: メンテナンスウィンドウ終了（02:30）
        Note over Services: ✅ サービス正常稼働<br/>新バージョン（v1.2.3）
    end
```

**主要ステップ**:
1. **ダウンロードフェーズ（Phase 1-3）**: 営業時間中にダウンロード・検証（サービス無停止）
2. **待機**: scheduled_at（深夜2:00）まで待機
3. **適用フェーズ（Phase 4-9）**: メンテナンスウィンドウ内に適用（サービス停止1-3分）

**業務影響の最小化**:
- 営業時間中: ダウンロードのみ（5-10分）、サービス無停止
- 深夜メンテナンス: 適用のみ（1-3分）、サービス停止

### フロー2: ダウンロードフェーズ（Phase 1-3）詳細

営業時間中にサービスを停止せずにダウンロードを完了するフローです。

```mermaid
sequenceDiagram
    participant Scheduler as ⏰ APScheduler
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant EdgeDB as Edge MongoDB
    participant Services as Microservices
    participant LocalFS as Local Storage

    Note over Scheduler,LocalFS: 🌞 営業時間中（14:00）・サービス稼働中

    rect rgb(255, 250, 240)
        Note right of Scheduler: Phase 1: バージョンチェック
        Scheduler->>Edge: check_for_updates()

        Edge->>EdgeDB: DeviceVersion取得
        EdgeDB-->>Edge: current_version: "1.2.2"

        Edge->>+Cloud: POST /api/v1/version/check<br/>{edge_id, device_type, current_version: "1.2.2"}

        Cloud-->>-Edge: Manifest返却<br/>{<br/>  target_version: "1.2.3",<br/>  artifacts: [{name: "startup.sh", ...}, ...],<br/>  container_images: [{service: "cart", ...}, ...],<br/>  apply_schedule: {<br/>    scheduled_at: "2025-10-15T02:00:00Z",<br/>    maintenance_window: 30<br/>  }<br/>}

        Edge->>EdgeDB: DeviceVersion更新<br/>(target_version: "1.2.3",<br/> update_status: "downloading",<br/> scheduled_apply_at: "2025-10-15T02:00:00Z")

        Note over Edge: ✅ Phase 1完了<br/>適用予定時刻: 深夜2:00
        Note over Services: ✅ サービス稼働継続
    end

    rect rgb(240, 255, 240)
        Note right of Edge: Phase 2: ダウンロード実行

        loop アーティファクトごと
            Edge->>+Cloud: GET /api/v1/artifacts/startup.sh?version=1.2.3
            Cloud-->>-Edge: ファイルデータ

            Edge->>LocalFS: 一時保存<br/>(/opt/kugelpos/pending-updates/v1.2.3/)
        end

        loop コンテナイメージごと
            Edge->>Registry: docker pull registry.example.com/kugelpos/cart:1.2.3
            Registry-->>Edge: イメージレイヤー
        end

        Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "in_progress")

        Note over Edge: ✅ Phase 2完了<br/>全ファイル・イメージダウンロード
        Note over Services: ✅ サービス稼働継続<br/>ダウンロード中も業務影響なし
    end

    rect rgb(255, 240, 240)
        Note right of Edge: Phase 3: チェックサム検証

        Edge->>Edge: 全ファイルチェックサム検証<br/>（SHA256）

        Edge->>Edge: 全イメージダイジェスト検証<br/>（docker inspect）

        alt 検証成功
            Edge->>LocalFS: status.json保存<br/>(ready_to_apply: true,<br/> verification_status: "passed")

            Edge->>EdgeDB: DeviceVersion更新<br/>(update_status: "pending_apply",<br/> download_status: "completed",<br/> download_completed_at: now,<br/> pending_version: "1.2.3")

            Edge->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3"}
            Cloud-->>-Edge: 通知受信確認

            Note over Edge: ✅ Phase 3完了<br/>適用準備完了
        else 検証失敗
            Note over Edge: ❌ 検証失敗<br/>リトライ実行
        end

        Note over Services: ✅ サービス稼働継続<br/>業務に影響なし
    end

    Note over Scheduler,LocalFS: ⏱️ ダウンロードフェーズ完了（所要時間: 5分）<br/>scheduled_at（02:00）まで待機
```

**主要ステップ**:
1. **Phase 1**: バージョンチェック、Manifest受信（scheduled_at, maintenance_window取得）
2. **Phase 2**: ファイル・イメージダウンロード（サービス無停止）
3. **Phase 3**: チェックサム・ダイジェスト検証

**サービス稼働の保証**:
- 全フェーズでサービスは無停止
- ダウンロード中も業務に影響なし
- scheduled_atまで待機

### フロー3: 適用フェーズ（Phase 4-9）詳細

メンテナンスウィンドウ内にサービスを停止して新バージョンを適用するフローです。

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

        Edge->>EdgeDB: DeviceVersion取得<br/>(pending_version: "1.2.3",<br/> scheduled_apply_at: "2025-10-15T02:00:00Z")

        Edge->>Edge: メンテナンスウィンドウ確認<br/>(scheduled_at <= now < scheduled_at + maintenance_window)

        alt ウィンドウ内
            Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "in_progress")

            Edge->>LocalFS: 現行バージョンバックアップ<br/>(/opt/kugelpos/backups/v1.2.2/)

            Note over Edge: ✅ Phase 4完了<br/>ロールバック準備完了
        else ウィンドウ外
            Note over Edge: ⏭️ 適用スキップ<br/>次回スケジュールまで待機
        end
    end

    rect rgb(240, 240, 255)
        Note right of Edge: Phase 5: 適用準備
        Edge->>LocalFS: pending-updates/v1.2.3/ から<br/>ファイル配置準備

        Edge->>Edge: スクリプトファイル検証<br/>（実行権限 755）

        Note over Edge: ✅ Phase 5完了<br/>適用準備完了
    end

    rect rgb(255, 240, 240)
        Note right of Edge: Phase 6: サービス停止
        Edge->>Docker: docker-compose down

        Docker->>Services: SIGTERM送信<br/>（グレースフルシャットダウン）

        Services-->>Docker: シャットダウン完了

        Docker-->>Edge: 全サービス停止完了

        Note over Services: ⏸️ ダウンタイム開始<br/>（目標: 1-3分）
    end

    rect rgb(240, 255, 240)
        Note right of Edge: Phase 7: 新バージョン適用
        Edge->>LocalFS: スクリプトファイル配置<br/>（startup.sh → /opt/kugelpos/）

        Edge->>LocalFS: 設定ファイル配置<br/>（docker-compose.yml 等）

        Edge->>HostOS: モジュールインストール<br/>（pip install *.whl）

        Edge->>Docker: docker-compose pull<br/>（新バージョンイメージ）

        Edge->>Docker: docker-compose up -d<br/>（全サービス起動）

        Docker->>Services: コンテナ起動

        Services-->>Docker: 起動完了

        Docker-->>Edge: 全サービス起動完了

        Note over Services: ⏯️ サービス再起動完了
    end

    rect rgb(255, 250, 240)
        Note right of Edge: Phase 8: ヘルスチェック
        loop 各サービス（最大3回、10秒間隔）
            Edge->>Services: GET /health

            alt ヘルスチェック成功
                Services-->>Edge: {"status": "healthy"}
                Note over Edge: ✅ サービス正常
            else ヘルスチェック失敗
                Services-->>Edge: タイムアウト/500エラー

                alt 3回失敗
                    Note over Edge: ❌ 自動ロールバック実行

                    Edge->>Docker: docker-compose down
                    Edge->>LocalFS: バックアップから復元
                    Edge->>Docker: docker-compose up -d<br/>（旧バージョンで起動）

                    Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "rolled_back")
                end
            end
        end

        Note over Edge: ✅ Phase 8完了<br/>全サービス正常
        Note over Services: ⏱️ ダウンタイム終了（2分30秒）
    end

    rect rgb(240, 240, 255)
        Note right of Edge: Phase 9: 完了通知
        Edge->>EdgeDB: DeviceVersion更新<br/>(current_version: "1.2.3",<br/> apply_status: "completed",<br/> apply_completed_at: now,<br/> pending_version: null)

        Edge->>LocalFS: 古いバックアップ削除<br/>（7日以上経過）

        Edge->>LocalFS: pending-updates/v1.2.3/ 削除

        Edge->>+Cloud: POST /api/v1/apply-complete<br/>{edge_id, version: "1.2.3", downtime_seconds: 150}
        Cloud-->>-Edge: 通知受信確認

        Note over Edge: ✅ Phase 9完了<br/>更新完了
    end

    Note over Scheduler,Cloud: ⏱️ 適用フェーズ完了（ダウンタイム: 2分30秒）
```

**主要ステップ**:
1. **Phase 4**: 現行バージョンバックアップ
2. **Phase 5**: 適用準備（ファイル配置準備）
3. **Phase 6**: サービス停止（ダウンタイム開始）
4. **Phase 7**: 新バージョン適用（ファイル配置・サービス起動）
5. **Phase 8**: ヘルスチェック（失敗時は自動ロールバック）
6. **Phase 9**: 完了通知（ダウンタイム終了）

**ダウンタイムの最小化**:
- ダウンタイムはPhase 6～Phase 8のみ（目標: 1-3分）
- ダウンロード時間（5-10分）はダウンタイムに含まれない

### フロー4: メンテナンスウィンドウ超過時の動作

適用フェーズがメンテナンスウィンドウを超過した場合の動作フローです。

```mermaid
sequenceDiagram
    participant Scheduler as ⏰ APScheduler
    participant Edge as 🏪 Edge Sync
    participant EdgeDB as Edge MongoDB
    participant Docker as Docker Compose
    participant Services as Microservices

    Note over Scheduler,Services: ⚠️ メンテナンスウィンドウ超過時の動作

    rect rgb(255, 240, 240)
        Note right of Scheduler: 適用開始（02:00）
        Scheduler->>Edge: apply_pending_update()

        Edge->>EdgeDB: DeviceVersion取得<br/>(scheduled_apply_at: "2025-10-15T02:00:00Z",<br/> maintenance_window: 30分)

        Edge->>Edge: メンテナンスウィンドウ確認<br/>(scheduled_at <= now < scheduled_at + 30分)

        Note over Edge: ✅ ウィンドウ内<br/>適用開始

        Edge->>Docker: 適用フェーズ実行<br/>（Phase 4-7）

        Note over Docker: Phase 7でエラー発生<br/>（例: イメージpull遅延）
    end

    rect rgb(255, 250, 240)
        Note right of Edge: ウィンドウ終了時刻接近（02:28）
        Edge->>Edge: 経過時間チェック<br/>(now - scheduled_at = 28分)

        alt ウィンドウ内（28分 < 30分）
            Note over Edge: ⚡ リトライ継続<br/>（ウィンドウ終了まで2分）

            Edge->>Docker: リトライ実行<br/>（Phase 7再試行）

            alt リトライ成功（02:29）
                Docker-->>Edge: 適用成功

                Edge->>Services: Phase 8: ヘルスチェック

                Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "completed")

                Note over Edge: ✅ ウィンドウ内に完了<br/>（残り1分で成功）
            else ウィンドウ終了（02:30）
                Note over Edge: ⚠️ メンテナンスウィンドウ終了<br/>適用スキップ

                Edge->>Docker: docker-compose down<br/>（中断）

                Edge->>EdgeDB: DeviceVersion更新<br/>(apply_status: "skipped",<br/> error_message: "Maintenance window expired")

                Note over Edge: ⏭️ 適用スキップ<br/>次回スケジュールまで待機
            end
        end
    end

    rect rgb(240, 240, 255)
        Note right of Edge: ウィンドウ外（02:35）
        Edge->>EdgeDB: 次回スケジュール確認<br/>（scheduled_apply_at更新）

        Note over Edge: ⏱️ 次回メンテナンスウィンドウ待機<br/>（例: 翌日02:00）
    end
```

**主要ステップ**:
1. **適用開始**: scheduled_at到達時、メンテナンスウィンドウ内で適用開始
2. **ウィンドウ内リトライ**: エラー発生時、ウィンドウ終了時刻までリトライ継続
3. **ウィンドウ超過**: 終了時刻を過ぎた場合、適用スキップ
4. **次回スケジュール**: 次回メンテナンスウィンドウまで待機

**メンテナンスウィンドウの保証**:
- ウィンドウ内であればリトライ継続
- ウィンドウ終了時刻を過ぎた場合、即座に適用スキップ
- 業務開始時刻（例: 06:00）に確実にサービス稼働

## データベース構造

### DeviceVersion（2段階更新状態管理）

```
コレクション: info_edge_version

ドキュメント例（ダウンロード完了・適用待ち）:
{
  "_id": ObjectId("..."),
  "edge_id": "edge-tenant001-store001-001",
  "device_type": "edge",
  "current_version": "1.2.2",
  "target_version": "1.2.3",
  "update_status": "pending_apply",
  "download_status": "completed",
  "download_completed_at": ISODate("2025-10-14T16:30:00Z"),
  "apply_status": "not_started",
  "scheduled_apply_at": ISODate("2025-10-15T02:00:00Z"),
  "apply_completed_at": null,
  "pending_version": "1.2.3",
  "last_check_timestamp": ISODate("2025-10-14T16:30:00Z"),
  "retry_count": 0,
  "error_message": null,
  "created_at": ISODate("2025-10-01T00:00:00Z"),
  "updated_at": ISODate("2025-10-14T16:30:00Z")
}
```

**2段階更新の状態遷移**:
1. `update_status: "none"` → `"downloading"` (Phase 1開始)
2. `download_status: "in_progress"` (Phase 2実行中)
3. `download_status: "completed"` (Phase 3完了)
4. `update_status: "pending_apply"` (scheduled_at待機中)
5. `apply_status: "in_progress"` (Phase 4-8実行中)
6. `update_status: "completed"` (Phase 9完了)

### PendingUpdate（ダウンロード済み未適用状態）

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
  "scheduled_apply_at": "2025-10-15T02:00:00Z",
  "maintenance_window": 30,
  "artifacts_count": 15,
  "total_size_bytes": 3200000000,
  "manifest_json": { ... }
}
```

## パフォーマンス指標

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| **ダウンロード時間** | 10分以内 | Phase 1開始 → Phase 3完了までの時間 |
| **ダウンタイム** | 1-3分 | Phase 6開始 → Phase 8完了までの時間 |
| **適用開始時刻精度** | scheduled_at ±30秒 | scheduled_atと実際の適用開始時刻の差 |
| **メンテナンスウィンドウ遵守率** | 99%以上 | ウィンドウ内完了回数 / 全適用回数 |

## 受入シナリオの検証

### シナリオ1: 営業時間中のダウンロード、営業終了後の自動適用

```
Given: クラウドに新バージョン（v1.2.3）が登録され、scheduled_at=深夜2:00、maintenance_window=30分に設定
When: エッジ端末が15分ごとのバージョンチェックを実行（14:00）
Then:
  1. 更新が検知され、即座にダウンロードが開始される（営業時間中、サービス停止なし）
  2. ダウンロード完了後、深夜2:00まで待機
  3. 深夜2:00に自動的に適用フェーズが実行される
  4. サービス停止→新バージョンに更新→サービス起動→ヘルスチェック完了
  5. ダウンタイム1-3分以内

検証方法:
1. Cloud側で新バージョン登録（target_version: "1.2.3", scheduled_at: "02:00", maintenance_window: 30）
2. Edge Sync のバージョンチェック実行（14:00）
3. ダウンロードフェーズ完了を確認（DeviceVersion.download_status: "completed", update_status: "pending_apply"）
4. scheduled_at到達まで待機（サービス稼働継続を確認）
5. scheduled_at到達時（02:00）、適用フェーズ自動実行を確認
6. ダウンタイムを測定（Phase 6開始 → Phase 8完了）
7. 最終的に DeviceVersion.current_version: "1.2.3", apply_status: "completed" を確認
```

### シナリオ2: メンテナンスウィンドウ内での適用リトライ

```
Given: 適用予定時刻（scheduled_at）での適用失敗時
When: メンテナンスウィンドウ（maintenance_window）内であればリトライ継続
Then: ウィンドウ終了時刻を過ぎた場合は適用をスキップし、次回スケジュールまで待機

検証方法:
1. 意図的に適用失敗を発生させる（Phase 7でイメージpull遅延）
2. scheduled_at到達時（02:00）、適用フェーズ実行
3. Phase 7でエラー発生を確認
4. メンテナンスウィンドウ内（02:00-02:30）であればリトライ継続することを確認
5. ウィンドウ終了時刻（02:30）を過ぎた場合、適用スキップを確認
6. DeviceVersion.apply_status: "skipped"、error_message: "Maintenance window expired" を確認
7. 次回スケジュール（scheduled_apply_at更新）を確認
```

### シナリオ3: Edge Sync ServiceとCloud Sync Serviceの透過的切り替え

```
Given: POS端末がEdge端末からファイル取得
When: Edge Sync Service APIにリクエスト送信（例: GET http://192.168.1.10:8007/api/v1/artifacts/startup.sh?version=1.2.3）
Then: ローカルキャッシュからファイルを取得

検証方法:
1. Edge端末でv1.2.3ダウンロード完了（ローカルキャッシュに保存）
2. POS端末からEdge Sync Service API（http://192.168.1.10:8007/api/v1/artifacts/startup.sh?version=1.2.3）にアクセス
3. Edge Sync Serviceがローカルキャッシュ（/opt/kugelpos/pending-updates/v1.2.3/startup.sh）からファイルを返すことを確認
4. POS端末がファイル取得成功することを確認
5. Edge端末停止時、POS端末がCloud Sync Service（primary_url）へ自動フォールバックすることを確認
```

### シナリオ4: Edge Sync ServiceのAPI互換性

```
Given: Edge Sync ServiceがCloud Sync Serviceと同等のAPI（/api/v1/version、/api/v1/artifacts）を提供
When: POS端末がEdge端末をprimary_urlに設定
Then: Cloud Sync ServiceとEdge Sync Serviceを透過的に切り替えてダウンロード可能

検証方法:
1. POS端末のManifestでavailable_seedsにEdge端末を設定
2. POS端末がEdge Sync Service API（/api/v1/artifacts）にアクセス
3. エンドポイント・レスポンス形式がCloud Sync Serviceと同等であることを確認
4. POS端末がCloud/Edge Sync Serviceを透過的に切り替え可能であることを確認
5. Edge端末停止時のフォールバック動作を確認
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

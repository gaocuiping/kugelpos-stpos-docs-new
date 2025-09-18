# Sync Service Architecture

## 4. Component Architecture

このクラス図は、Sync Serviceを構成する主要コンポーネントとその関係を示しています。各コンポーネントは明確な責務を持ち、疎結合な設計により柔軟性と拡張性を実現しています。

### 主要コンポーネント

#### SyncService
- システムのエントリーポイント
- モード（Cloud/Edge）に応じた動作切り替え
- サービスのライフサイクル管理（start/stop）

#### SyncManager
- 同期処理の中央制御
- 各種サービスとリポジトリの協調
- 同期リクエストのオーケストレーション

#### CloudSyncService
クラウド側の同期処理を担当：
- **track_sync_status()**: エッジインスタンスの同期状態を追跡
- **provide_delta_data()**: 他サービスのAPIから取得した差分データの提供
- **handle_bulk_request()**: バルク同期リクエストの処理（APIを通じてデータ取得）
- **manage_edge_instances()**: テナント別DBでエッジインスタンスを管理
- **authenticate_edge()**: テナントID検証とJWT認証によるエッジデバイスの認証

#### EdgeSyncService  
エッジ側の同期処理を担当：
- **poll_cloud_updates()**: クラウドからの更新をポーリング
- **apply_changes()**: 受信した変更を各サービスのAPIを通じて適用
- **push_local_changes()**: 各サービスのAPIから取得したローカル変更をクラウドへプッシュ
- **request_bulk_sync()**: バルク同期のリクエスト

### サポートコンポーネント

#### SyncRepository
- Sync専用データベースへの同期状態の永続化
- タイムスタンプの管理
- ペンディング同期の管理
- 他サービスのデータベースへは直接アクセス不可

#### DataTransformer
- データの圧縮/解凍
- データ形式の変換
- データ検証

#### CircuitBreaker
- 障害時の自動遮断
- 段階的な復旧制御
- システム保護機能

#### QueueManager
- 同期タスクのキューイング
- Redis/Daprを使用したメッセージング
- 非同期処理の管理

### データモデル

#### SyncStatus
同期状態を表現：
- edge_id: エッジインスタンスの識別子
- service_name: 対象サービス名
- last_sync: 最終同期時刻
- sync_type: 同期タイプ（differential/bulk）
- status: 現在の状態

#### SyncRequest
同期リクエストの構造：
- edge_id: リクエスト元のエッジID
- tenant_id: テナントID
- store_code: 店舗コード
- service_name: 対象サービス
- sync_type: リクエストする同期タイプ
- last_timestamp: 最後の同期タイムスタンプ
- data_filter: フィルタ条件

```mermaid
classDiagram
    class SyncService {
        +mode: str
        +sync_manager: SyncManager
        +start()
        +stop()
    }
    
    class SyncManager {
        +mode: str
        +sync_repository: SyncRepository
        +orchestrate_sync()
        +handle_sync_request()
    }
    
    class CloudSyncService {
        +track_sync_status()
        +provide_delta_data()
        +handle_bulk_request()
        +manage_edge_instances()
        +authenticate_edge()
    }
    
    class EdgeSyncService {
        +poll_cloud_updates()
        +apply_changes()
        +push_local_changes()
        +request_bulk_sync()
    }
    
    class SyncRepository {
        +save_sync_status()
        +get_sync_status()
        +update_timestamp()
        +get_pending_syncs()
    }
    
    class SyncStatus {
        +edge_id: str
        +service_name: str
        +last_sync: datetime
        +sync_type: str
        +status: str
    }
    
    class SyncRequest {
        +edge_id: str
        +tenant_id: str
        +store_code: str
        +service_name: str
        +sync_type: str
        +last_timestamp: datetime
        +data_filter: dict
    }
    
    class DataTransformer {
        +compress_data()
        +decompress_data()
        +validate_data()
        +transform_format()
    }
    
    class CircuitBreaker {
        +state: str
        +failure_count: int
        +timeout: int
        +call_with_circuit_breaker()
    }
    
    class QueueManager {
        +redis_client: Redis
        +dapr_client: DaprClient
        +enqueue_sync()
        +dequeue_sync()
        +process_queue()
    }
    
    SyncService --> SyncManager
    SyncManager --> CloudSyncService
    SyncManager --> EdgeSyncService
    SyncManager --> SyncRepository
    CloudSyncService --> SyncStatus
    EdgeSyncService --> SyncRequest
    SyncManager --> DataTransformer
    SyncManager --> CircuitBreaker
    SyncManager --> QueueManager
    
    SyncRepository --> SyncStatus
```
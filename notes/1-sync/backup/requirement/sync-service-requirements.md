# Sync Service 機能要件書

## 1. 概要

### 1.1 目的
クラウド環境とエッジ環境（店舗）間でデータの同期を行うサービスを開発し、オフライン耐性を持つPOSシステムを実現する。

### 1.2 背景
- 店舗のPOSシステムは、ネットワーク障害時でも業務を継続できる必要がある
- クラウドで一元管理されるマスターデータを各店舗に配信する必要がある
- 店舗で発生したトランザクションデータをクラウドに集約して分析する必要がある
- トラブルシューティングやコンプライアンス対応のため、エッジ環境のファイルをクラウドで収集する必要がある

### 1.3 スコープ
本サービスは以下のデータの同期を対象とする：
- **マスターデータ**: 商品、価格、決済方法、税制、スタッフ情報など（クラウド→エッジ）
- **ターミナルデータ**: テナント情報、店舗情報、端末情報、端末ステータス（双方向同期）
- **トランザクションデータ**: 取引ログ（売上・返品・取消を含む）、開設精算、入出金（エッジ→クラウド）
- **ジャーナルデータ**: 電子ジャーナル（エッジ→クラウド）
- **ファイル収集**: エッジ環境の任意ファイル・ディレクトリの圧縮収集（アプリケーションログを含む）（エッジ→クラウド）

## 2. 機能要件

### 2.1 サービス構成

#### 2.1.1 新規サービス「sync」の追加
- クラウド環境とエッジ環境の両方に配置
- 環境変数`SYNC_MODE`により動作モードを切り替え
  - `cloud`: クラウドモード
  - `edge`: エッジモード

#### 2.1.2 サービス配置
```
クラウド環境:
  - sync (Cloud Mode)
  - account, terminal, master-data, cart, report, journal, stock

エッジ環境:
  - sync (Edge Mode)  
  - account, terminal, master-data, cart, report, journal, stock
```

### 2.2 同期メカニズム

#### 2.2.1 差分同期メカニズム

**基本フロー:**
1. エッジ側syncが定期的（30-60秒間隔）にクラウド側syncに同期リクエストを送信
   - リクエストに含まれる情報：edge_id、data_type、last_sync_timestamp
2. クラウド側syncが同期開始を記録
   - sync_historyに開始時刻、ステータス"syncing"を記録
   - sync_statusを"syncing"に更新
3. クラウド側syncが最終同期時刻以降の変更データを抽出
   - 各データ種別の更新日時（updated_at）を基準に差分を特定
4. 差分データをエッジ側syncに送信
   - データがない場合は"no_changes"レスポンス
   - データがある場合は圧縮して一括送信
5. エッジ側syncが受信データを各サービスに配信
   - 成功/失敗をトラッキング
6. エッジ側syncが同期結果をクラウド側に通知
   - 処理件数、成功/失敗状態を含む
7. クラウド側syncが同期終了を記録
   - sync_historyに終了時刻、処理結果を記録
   - sync_statusを"completed"または"failed"に更新
   - last_sync_timestampを更新

**実装詳細:**
- ポーリング間隔: 環境変数`SYNC_POLL_INTERVAL`で設定（デフォルト: 30-60秒）
- タイムスタンプベースの変更追跡
  - 全データに`created_at`、`updated_at`フィールドが必須
  - `updated_at > last_sync_timestamp`のレコードを差分として抽出
- 各データ種別ごとに独立した同期状態管理
- リトライ機構（指数バックオフ）
- トランザクション管理
  - 同期処理をトランザクションとして管理
  - 部分的な失敗時はロールバック可能

#### 2.2.2 一括同期メカニズム

**スナップショット方式（マスターデータ用）:**
1. エッジ側syncがフル同期リクエストを送信
2. クラウド側syncが対象データの全件スナップショットを作成
3. データを圧縮して転送
4. エッジ側syncが既存データを削除後、新データを投入
5. 同期完了を通知

**重要課題（実装プラン立案時に解決必要）:**
- 24時間営業店舗でのノーダウンタイム更新の実現
- 現状の「削除→投入」方式では一時的なサービス停止が発生
- 以下の対策を実装プラン時に検討：
  - Blue-Green Deployment方式（2つのDBを切り替え）
  - Shadow Table方式（一時テーブルへの投入後、名前変更）
  - Versioning方式（バージョン管理による段階的切り替え）
  - トランザクション内での高速置換

**ストリーミング方式（大量データ用）:**
1. エッジ側syncがストリーム同期をリクエスト
2. クラウド側syncがデータストリームを開始
3. チャンク単位でデータを順次転送
4. エッジ側syncが受信したチャンクを順次処理
5. 全チャンク処理完了後、同期完了を通知

### 2.3 データ別同期方法

#### 2.3.0 データ種別同期仕様一覧

| データ種別 | 同期方向 | 差分同期 | 一括同期 | ポーリング間隔 | 備考 |
|------------|----------|----------|----------|----------------|------|
| master_data | クラウド→エッジ | ✓ | ✓ | 30秒-1分 | 初期セットアップ時は一括同期 |
| terminal | 双方向 | ✓ | × | 30秒-1分 | 店舗情報、端末情報、端末状態 |
| tran_log | エッジ→クラウド | ✓ | × | 30秒-1分 | 取引データ（売上・返品・取消） |
| open_close_log | エッジ→クラウド | ✓ | × | 30秒-1分 | 開設精算データ |
| cash_in_out_log | エッジ→クラウド | ✓ | × | 30秒-1分 | 入出金データ |
| journal | エッジ→クラウド | ✓ | × | 30秒-1分 | 電子ジャーナル |
| file_collection | エッジ→クラウド | × | ✓ | オンデマンド | 任意ファイル・ディレクトリの収集（アプリログ含む） |

**注記:**
- ✓: サポート、×: 非サポート
- ポーリング間隔は環境変数`SYNC_POLL_INTERVAL`で調整可能

### 2.3 データ別同期方法

#### 2.3.1 マスターデータ（クラウド → エッジ）

**対象データ:**
- 商品マスター（products）
- 価格情報（prices）
- 決済方法（payment_methods）
- 税制ルール（tax_rules）
- スタッフ情報（staff）
- プロモーション情報（promotions）

**同期方法:**
- **初期同期**: 一括同期（スナップショット方式）
- **定期同期**: 差分同期（30-60秒間隔）
- **手動同期**: 管理画面から任意のタイミングで実行可能
- **予約反映**: ファイル名に指定された日時での自動反映

**一括同期タイミング:**
- システム初期セットアップ時
- 日次バッチ（営業時間外）
- マスターデータ大幅変更時（手動実行）

**差分同期タイミング:**
- 30秒-1分間隔の定期ポーリング（エッジ側からクラウドへ問い合わせ）

**予約反映の更新タイミング:**
- **S（Settlement）**: 精算業務完了時に反映
- **T（Transaction）**: 取引後、商品未登録時に反映

**予約反映の更新区分:**
- **A（All）**: 全件更新（既存データを全て置き換え）
- **M（Modified）**: 差分更新（変更分のみ適用）

#### 2.3.2 トランザクションデータ（エッジ → クラウド）

**対象データ:**
- 取引ログ（tran_log） ※売上・返品・取消取引を含む
- 開設精算（open_close_log）
- 入出金（cash_in_out_log）

**同期方法:**
- **差分同期**: 非同期での定期同期（30秒～1分間隔）
- **復旧時同期**: ネットワーク復旧時に未送信分を一括送信

**同期タイミング:**
- 定期的なポーリング（30秒～1分間隔）
- ネットワーク障害時はローカルキューに保存
- ネットワーク復旧時に未送信分を自動送信

#### 2.3.3 ジャーナルデータ（エッジ → クラウド）

**対象データ:**
- 電子ジャーナル（electronic_journal）
- 監査ログ（audit_log）

**同期方法:**
- **差分同期**: 非同期での定期同期（30秒～1分間隔）
- **復旧時同期**: ネットワーク復旧時に未送信分を送信

**同期タイミング:**
- 定期的なポーリング（30秒～1分間隔）
- ネットワーク障害時はローカルキューに保存
- ネットワーク復旧時に未送信分を自動送信

#### 2.3.4 ファイル収集（エッジ → クラウド）

**対象データ:**
- エッジ環境の任意のファイル・ディレクトリ
- アプリケーションログ（log_application、log_request、その他ログ）
- 設定ファイル、データベースファイル、システムファイル等

**同期方法:**
- **同期レスポンス連動**: エッジ側の定期同期リクエストのレスポンスに収集指示が含まれる場合に実行
- **圧縮アーカイブ**: 収集対象をzip形式で圧縮してクラウドに送信

**収集フロー:**
1. エッジ側が定期的な同期リクエスト（tran_log, journal等）をクラウド側に送信
2. クラウド側が同期レスポンスを返却
   - 通常の同期データ + 収集指示（オプション）
   - 収集指示内容：対象パス、アーカイブファイル名、除外パターン
3. エッジ側がレスポンスに収集指示が含まれている場合、収集処理を開始
   - 指定パスの存在確認とアクセス権限チェック
   - セキュリティ検証（パストラバーサル攻撃対策、ホワイトリスト検証）
4. エッジ側が指定パスを圧縮アーカイブ作成
   - zip形式での圧縮
   - 最大アーカイブサイズ制限（100MB、設定可能）
   - 一時ディレクトリでの作業
5. エッジ側がファイル収集専用APIでクラウド側にアーカイブを送信
   - チャンク分割対応（大容量ファイル用）
   - 送信完了後、一時ファイルを削除
6. クラウド側がアーカイブを受信・保存し、収集完了をレスポンスで通知
   - 成功時：ステータス"completed"を返却
   - 失敗時：エラー詳細を返却

**セキュリティ制限:**
- 収集可能パスの事前許可制（ホワイトリスト、環境変数で設定）
- システムディレクトリ（/etc, /root, /sys, /proc等）の収集禁止
- 最大ファイルサイズ・アーカイブサイズ制限
- パストラバーサル攻撃の検証
- 収集権限の事前チェック

**同期タイミング:**
- 定期同期リクエストのレスポンスに収集指示が含まれている場合のみ実行
- クラウド側で収集が必要と判断された際に指示
- 緊急時やトラブルシューティング時の手動指示

### 2.4 同期状態管理

**管理主体**: クラウド側syncサービスが全エッジインスタンスの同期状態を一元管理

**管理対象データ種別:**

【マスターデータ（クラウド → エッジ）】
- `master_data`: マスターデータ（商品、価格、決済方法、税制、スタッフ等）

【トランザクションデータ（エッジ → クラウド）】
- `terminal`: 端末情報（店舗情報、端末情報、端末状態）
- `tran_log`: 取引ログ（売上、返品、取消）
- `open_close_log`: 開設精算ログ
- `cash_in_out_log`: 入出金ログ

【ジャーナルデータ（エッジ → クラウド）】
- `journal`: 電子ジャーナル

【ファイル収集（エッジ → クラウド）】
- `file_collection`: 任意ファイル・ディレクトリの圧縮収集（アプリログ、システムログ、設定ファイル等）

#### 2.4.1 同期ステータス

クラウド側syncサービスが、各エッジインスタンス・データ種別ごとに以下を管理：
- `edge_id`: エッジインスタンス識別子（テナント内で一意）
- `data_type`: データ種別（tran_log, open_close_log, master_data等）
- `last_sync_timestamp`: 最終同期時刻
- `sync_type`: 同期タイプ（differential/bulk）
- `status`: 同期状態（idle/syncing/completed/failed）
- `retry_count`: リトライ回数
- `error_message`: エラーメッセージ

#### 2.4.2 同期履歴

クラウド側syncサービスが同期実行履歴を記録：
- エッジID
- データ種別
- 同期タイプ（differential/bulk）
- 同期方向（cloud-to-edge/edge-to-cloud）
- 同期開始・終了時刻
- 同期データ件数・サイズ
- 成功/失敗状態
- エラー詳細
- リトライ回数
- 処理時間（ミリ秒）

### 2.5 優先度制御（将来実装）

**注記**: 優先度制御は実装の複雑性を考慮し、初期バージョンでは見送り。将来的な拡張として検討。

初期実装では以下のシンプルな方式を採用：

**エッジ側の動作：**
- 各データ種別は独立したポーリング間隔で同期リクエストを送信
- ネットワーク障害時は送信予定データをローカルキューに保存
- ネットワーク復旧時にキューから順次送信（FIFO）

**クラウド側の動作：**
- 受信した同期リクエストを到着順に処理（FIFO）
- 複数エッジからのリクエストも到着順に処理
- 優先度による順序制御は行わない

### 2.6 競合解決

#### 2.6.1 競合検出

- 同一レコードへの同時更新を検出
- タイムスタンプ（updated_at）による変更追跡

#### 2.6.2 解決戦略

**Last Write Wins (後勝ち):**
- 唯一の解決方法としてシンプルに実装
- 最新タイムスタンプ（updated_at）のデータを採用
- 適用対象：全データ種別
- 競合発生時はログに記録（監査用）

※将来的に必要に応じて他の解決戦略を検討

### 2.7 エラーハンドリング

#### 2.7.1 リトライ機構

- 指数バックオフによるリトライ
- 最大リトライ回数: 5回（設定可能）
- リトライ間隔: 1秒 → 2秒 → 4秒 → 8秒 → 16秒

#### 2.7.2 サーキットブレーカー

- 連続失敗しきい値: 3回
- 回路開放時間: 60秒
- 半開状態での段階的復旧

#### 2.7.3 フォールバック

- ネットワーク障害時はローカルキューに保存
- キュー容量超過時は古いログから削除
- 重要データは必ず永続化

## 3. 非機能要件

### 3.1 パフォーマンス要件

- **同期遅延**: 5分以内
- **スループット**: 1000件/秒以上
- **データ圧縮率**: 50%以上（gzip使用）
- **並行処理**: 最大1,000エッジの同時同期対応

### 3.2 可用性要件

- **稼働率**: 99.9%以上
- **自動復旧**: ネットワーク復旧後30秒以内に同期再開
- **データ保証**: At-least-once delivery

### 3.3 セキュリティ要件

#### 3.3.1 通信セキュリティ
- **通信暗号化**: TLS 1.3による暗号化
- **データ暗号化**: 機密データは暗号化して保存

#### 3.3.2 エッジ端末認証

**認証フロー:**
1. エッジ端末が`edge_id`と`secret`を使用して認証リクエスト送信
2. クラウド側syncサービスが認証し、JWTトークンを発行
3. JWTトークンに`tenant_id`、`edge_id`、`store_code`を含める
4. 以降のAPIアクセスはJWTトークンをAuthorizationヘッダーに付与

**JWT構成:**
```json
{
  "edge_id": "EDGE001",
  "tenant_id": "A1234",
  "store_code": "STORE001",
  "exp": 1234567890,  // 有効期限
  "iat": 1234567800   // 発行時刻
}
```

**エッジ端末管理:**
- 各テナントのDB（`sync_{tenant_id}`）にエッジ端末情報を管理
- エッジ端末IDはテナント内で一意
- テナント間の完全な分離を実現

### 3.4 運用要件

- **監視**: メトリクス、ログ、ヘルスチェック
- **アラート**: 同期遅延、エラー率上昇時に通知
- **バックアップ**: 同期状態の定期バックアップ

## 4. インターフェース仕様

### 4.1 REST API

#### 4.1.0 エッジ端末認証
```
POST /api/v1/sync/auth
Headers:
  Content-Type: application/json

Request:
{
  "tenant_id": "A1234",
  "edge_id": "EDGE001",
  "secret": "secure_password_123"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}

Error Response: 401 Unauthorized
{
  "success": false,
  "error": {
    "code": "AUTH_002",
    "message": "Invalid edge_id or secret"
  }
}

Error Response: 404 Not Found
{
  "success": false,
  "error": {
    "code": "AUTH_003",
    "message": "Tenant not found"
  }
}
```

### 4.2 同期API

#### 4.2.1 同期状態確認（エッジ側からの定期リクエスト）
```
POST /api/v1/sync/request
Headers:
  Authorization: Bearer <JWT_TOKEN>
  Content-Type: application/json

Request:
{
  "edge_id": "EDGE001",
  "data_type": "tran_log",
  "last_sync_timestamp": "2025-01-15T10:00:00Z",
  "sync_type": "differential"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "sync_data": {
      "records": [...],
      "next_sync_timestamp": "2025-01-15T10:30:00Z"
    },
    "file_collection_request": {
      "collection_id": "COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
      "collection_name": "error_logs_20250115",
      "target_paths": [
        "/var/log/kugelpos/error.log",
        "/var/log/kugelpos/application/"
      ],
      "exclude_patterns": ["*.tmp", "cache/*"],
      "max_archive_size_mb": 50
    }
  }
}

Response (収集指示なしの場合): 200 OK
{
  "success": true,
  "data": {
    "sync_data": {
      "records": [...],
      "next_sync_timestamp": "2025-01-15T10:30:00Z"
    }
  }
}

Error Response: 401 Unauthorized
{
  "success": false,
  "error": {
    "code": "AUTH_001",
    "message": "Invalid or expired token"
  }
}
```

#### 4.2.2 手動同期実行
```
POST /api/v1/sync/execute
Headers:
  Authorization: Bearer <JWT_TOKEN>
  Content-Type: application/json

Request:
{
  "data_type": "master_data",
  "sync_type": "bulk",
  "data_filter": {}
}

Response: 202 Accepted
{
  "success": true,
  "data": {
    "sync_id": "SYNC_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
    "status": "queued",
    "message": "Sync request has been queued for processing"
  }
}

Error Response: 400 Bad Request
{
  "success": false,
  "error": {
    "code": "SYNC_001",
    "message": "Invalid data_type specified"
  }
}
```

#### 4.2.3 同期履歴取得
```
GET /api/v1/sync/history?from=2025-01-01&to=2025-01-15
Headers:
  Authorization: Bearer <JWT_TOKEN>

Response: 200 OK
{
  "success": true,
  "data": {
    "histories": [
      {
        "sync_id": "SYNC_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
        "edge_id": "EDGE001",
        "data_type": "tran_log",
        "sync_type": "differential",
        "sync_direction": "edge-to-cloud",
        "start_time": "2025-01-15T10:30:00Z",
        "end_time": "2025-01-15T10:30:45Z",
        "record_count": 150,
        "data_size_bytes": 524288,
        "status": "success"
      }
    ],
    "total": 1
  }
}

Error Response: 400 Bad Request
{
  "success": false,
  "error": {
    "code": "SYNC_002",
    "message": "Invalid date format"
  }
}
```

#### 4.2.4 ファイル送信（エッジからクラウドへ）
```
POST /api/v1/sync/file-collection/{collection_id}/upload
Headers:
  Authorization: Bearer <JWT_TOKEN>
  Content-Type: multipart/form-data

Request:
Content-Disposition: form-data; name="archive"; filename="error_logs_20250115.zip"
Content-Type: application/zip

<compressed archive data>

Response: 200 OK
{
  "success": true,
  "data": {
    "collection_id": "COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
    "file_count": 45,
    "archive_size_bytes": 15728640,
    "status": "completed",
    "message": "File collection completed successfully"
  }
}

Response (収集処理失敗時): 200 OK
{
  "success": true,
  "data": {
    "collection_id": "COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
    "status": "failed",
    "error_details": {
      "error_code": "COLLECTION_ERROR",
      "message": "Failed to collect some files",
      "failed_paths": ["/var/log/kugelpos/application/"]
    }
  }
}

Error Response: 413 Payload Too Large
{
  "success": false,
  "error": {
    "code": "COLLECT_004",
    "message": "Archive size exceeds maximum limit"
  }
}

Error Response: 400 Bad Request
{
  "success": false,
  "error": {
    "code": "COLLECT_005",
    "message": "Invalid archive format or corrupted file"
  }
}
```


#### 4.2.5 ファイル収集履歴確認
```
GET /api/v1/sync/file-collection/{collection_id}
Headers:
  Authorization: Bearer <JWT_TOKEN>

Response: 200 OK
{
  "success": true,
  "data": {
    "collection_id": "COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
    "edge_id": "EDGE001",
    "collection_name": "error_logs_20250115",
    "status": "completed",
    "file_count": 45,
    "archive_size_bytes": 15728640,
    "download_url": "/api/v1/sync/file-collection/COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU/download",
    "start_time": "2025-01-15T14:00:00Z",
    "end_time": "2025-01-15T14:02:30Z"
  }
}

Error Response: 404 Not Found
{
  "success": false,
  "error": {
    "code": "COLLECT_002",
    "message": "Collection not found"
  }
}
```

#### 4.2.6 ファイルダウンロード
```
GET /api/v1/sync/file-collection/{collection_id}/download
Headers:
  Authorization: Bearer <JWT_TOKEN>

Response: 200 OK
Headers:
  Content-Type: application/zip
  Content-Disposition: attachment; filename="error_logs_20250115.zip"
  Content-Length: 15728640

Body: <compressed archive data>

Error Response: 404 Not Found
{
  "success": false,
  "error": {
    "code": "COLLECT_003",
    "message": "Archive file not found or expired"
  }
}
```

### 4.3 内部通信

サービス間通信はDaprを使用：
- Service Invocation: サービス間のAPIエンドポイント探索
- Pub/Sub: イベント駆動型通信
- State Store: 同期状態の管理

## 5. データモデル

### 5.0 データベース構成

#### テナント別データベース
- sync サービスも他のサービスと同様に、テナント毎に独立したデータベースを使用
- データベース名: `sync_{tenant_id}` (例: sync_A1234)
- 各テナントの同期状態、履歴、リクエストは完全に分離して管理


### 5.1 同期ステータス（sync_status）
```json
{
  "_id": "ObjectId",
  "edge_id": "EDGE001",
  "data_type": "tran_log",
  "last_sync_timestamp": "2025-01-15T10:30:00Z",
  "sync_type": "differential",
  "status": "completed",
  "retry_count": 0,
  "error_message": null,
  "created_at": "2025-01-15T09:00:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### 5.2 同期リクエスト（sync_request）
```json
{
  "_id": "ObjectId",
  "edge_id": "EDGE001",
  "data_type": "master_data",
  "sync_type": "bulk",
  "last_timestamp": "2025-01-15T09:00:00Z",
  "data_filter": {
    "categories": ["food", "beverage"]
  },
  "created_at": "2025-01-15T10:00:00Z"
}
```

### 5.3 エッジ端末管理（edge_devices）
```json
{
  "_id": "ObjectId",
  "edge_id": "EDGE001",
  "tenant_id": "A1234",
  "store_code": "STORE001",
  "secret_hash": "$2b$12$...",  // bcryptハッシュ
  "status": "active",  // active|inactive|suspended
  "description": "店舗1号店 POS端末",
  "last_authenticated": "2025-01-15T10:00:00Z",
  "registered_at": "2025-01-01T09:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### 5.4 同期履歴（sync_history）
```json
{
  "_id": "ObjectId",
  "sync_id": "SYNC_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",  // 同期処理の一意識別子（テナント_エッジ_ULID）
  "edge_id": "EDGE001",
  "data_type": "tran_log",
  "sync_type": "differential",
  "sync_direction": "edge-to-cloud",
  "start_time": "2025-01-15T10:00:00Z",
  "end_time": "2025-01-15T10:00:45Z",
  "record_count": 150,
  "data_size_bytes": 524288,
  "status": "success",
  "error_details": null,
  "retry_count": 0,
  "processing_time_ms": 450,
  "created_at": "2025-01-15T10:00:00Z"
}
```

### 5.5 ファイル収集リクエスト（file_collection_request）
```json
{
  "_id": "ObjectId",
  "collection_id": "COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
  "edge_id": "EDGE001",
  "collection_name": "error_logs_20250115",
  "target_paths": [
    "/var/log/kugelpos/error.log",
    "/var/log/kugelpos/application/"
  ],
  "exclude_patterns": ["*.tmp", "cache/*"],
  "max_archive_size_mb": 50,
  "status": "queued",  // queued|processing|completed|failed|expired
  "requested_by": "admin_user_123",
  "created_at": "2025-01-15T14:00:00Z",
  "updated_at": "2025-01-15T14:00:00Z"
}
```

### 5.6 ファイル収集履歴（file_collection_history）
```json
{
  "_id": "ObjectId",
  "collection_id": "COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
  "edge_id": "EDGE001",
  "collection_name": "error_logs_20250115",
  "target_paths": [
    "/var/log/kugelpos/error.log",
    "/var/log/kugelpos/application/"
  ],
  "exclude_patterns": ["*.tmp", "cache/*"],
  "start_time": "2025-01-15T14:00:00Z",
  "end_time": "2025-01-15T14:02:30Z",
  "file_count": 45,
  "archive_size_bytes": 15728640,
  "archive_path": "/storage/collections/COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU.zip",
  "status": "completed",
  "error_details": null,
  "processing_time_ms": 150000,
  "requested_by": "admin_user_123",
  "created_at": "2025-01-15T14:00:00Z"
}
```

### 5.7 ファイル収集指示（file_collection_instruction）
```json
{
  "_id": "ObjectId",
  "collection_id": "COLLECT_A1234_EDGE001_01JK3X9Y5Z8QWERTYU",
  "edge_id": "EDGE001",
  "collection_name": "error_logs_20250115",
  "target_paths": [
    "/var/log/kugelpos/error.log",
    "/var/log/kugelpos/application/"
  ],
  "exclude_patterns": ["*.tmp", "cache/*"],
  "max_archive_size_mb": 50,
  "status": "pending",  // pending|sent|processing|completed|failed|expired
  "priority": "normal",  // low|normal|high|urgent
  "requested_by": "admin_user_123",
  "expires_at": "2025-01-16T14:00:00Z",
  "created_at": "2025-01-15T14:00:00Z",
  "updated_at": "2025-01-15T14:00:00Z"
}
```

## 6. 実装提案

### 6.1 技術スタック

- **言語**: Python 3.12+
- **フレームワーク**: FastAPI
- **データベース**: MongoDB (Motor)
- **キャッシュ**: Redis
- **メッセージング**: Dapr Pub/Sub
- **圧縮**: zip（ファイル収集用）、gzip/brotli（データ転送用）
- **暗号化**: TLS 1.3

### 6.2 ディレクトリ構成
```
services/sync/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       └── sync_endpoints.py
│   ├── services/
│   │   ├── sync_manager.py
│   │   ├── cloud_sync_service.py
│   │   └── edge_sync_service.py
│   ├── repositories/
│   │   └── sync_repository.py
│   ├── models/
│   │   ├── sync_status.py
│   │   └── sync_request.py
│   ├── utils/
│   │   ├── data_transformer.py
│   │   └── circuit_breaker.py
│   └── config/
│       └── settings_sync.py
├── tests/
├── Dockerfile
└── requirements.txt
```

### 6.3 環境変数
```env
# データベース接続
MONGODB_URI=mongodb://localhost:27017/?replicaSet=rs0

# 動作モード
SYNC_MODE=cloud|edge

# エッジID（エッジモード時のみ）
EDGE_ID=EDGE001

# エッジ認証情報（エッジモード時のみ）
EDGE_SECRET=secure_password_123

# クラウドエンドポイント（エッジモード時のみ）
CLOUD_SYNC_URL=https://cloud.example.com/api/v1/sync

# ポーリング間隔（秒）
SYNC_POLL_INTERVAL=60

# リトライ設定
MAX_RETRY_COUNT=5
RETRY_BACKOFF_BASE=2

# サーキットブレーカー
CIRCUIT_BREAKER_THRESHOLD=3
CIRCUIT_BREAKER_TIMEOUT=60

# ファイル収集設定
FILE_COLLECTION_MAX_ARCHIVE_SIZE_MB=100
FILE_COLLECTION_ALLOWED_PATHS=/var/log/kugelpos,/opt/kugelpos/data,/tmp/kugelpos
FILE_COLLECTION_STORAGE_PATH=/storage/collections
FILE_COLLECTION_RETENTION_DAYS=30
```
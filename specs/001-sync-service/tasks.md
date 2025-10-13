# Tasks: Sync Service データ同期機能

**Input**: `/specs/001-sync-service/` の設計ドキュメント
**Prerequisites**: plan.md (必須), spec.md (ユーザーストーリー), research.md, data-model.md, contracts/

**テストについて**: この機能は憲章 III (TDD 必須) に準拠し、すべての実装タスクの前にテストタスクを含みます。Red-Green-Refactor サイクルに従います。

**構成**: タスクはユーザーストーリーごとにグループ化され、各ストーリーを独立して実装・テスト可能にしています。

## Format: `[ID] [P?] [Story] 説明`
- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: タスクが属するユーザーストーリー（例: US1, US2, US3）
- **[Test]**: テストタスク（実装前に作成、RED 確認必須）
- 説明には正確なファイルパスを含む

## パス規約
- **サービスルート**: `services/sync/`
- **アプリケーションコード**: `services/sync/app/`
- **テストコード**: `services/sync/tests/`
- Kugelpos マイクロサービスアーキテクチャに準拠

---

## Phase 1: Setup (共有インフラストラクチャ)

**目的**: プロジェクト初期化と基本構造の構築

- [ ] T001 Sync Service ディレクトリ構造を作成 (`services/sync/` 配下)
- [ ] T002 Pipfile を作成し、依存関係を定義 (`services/sync/Pipfile` - pytest, pytest-asyncio, pytest-cov, ruff 含む)
- [ ] T003 [P] Dockerfile を作成 (`services/sync/Dockerfile`)
- [ ] T004 [P] .env.example を作成 (`services/sync/.env.example` - ローカルキュー環境変数を含む)
- [ ] T005 [P] README.md を作成 (`services/sync/README.md`)
- [ ] T006 設定ファイルを作成 (`services/sync/app/config/settings.py`)
- [ ] T007 [P] 定数定義ファイルを作成 (`services/sync/app/config/constants.py`)
- [ ] T008 メインアプリケーションエントリーポイントを作成 (`services/sync/app/main.py`)
- [ ] T009 [P] pytest 設定ファイルを作成 (`services/sync/pytest.ini`)
- [ ] T010 [P] conftest.py を作成 (`services/sync/tests/conftest.py` - テスト共通フィクスチャ、DB接続、モック設定)
- [ ] T011 [P] test_clean_data.py を作成 (`services/sync/tests/test_clean_data.py` - テストデータクリーンアップ)
- [ ] T012 [P] test_setup_data.py を作成 (`services/sync/tests/test_setup_data.py` - テストデータセットアップ)

---

## Phase 2: Foundational (ブロッキング前提条件)

**目的**: すべてのユーザーストーリー実装の前に完了必須のコアインフラストラクチャ

**⚠️ CRITICAL**: このフェーズが完了するまで、ユーザーストーリーの作業を開始できません

- [ ] T013 BaseDocumentModel を継承した基底モデルを確認 (commons ライブラリから利用)
- [ ] T014 AbstractRepository を継承した基底リポジトリを確認 (commons ライブラリから利用)
- [ ] T015 [P] データベース接続管理を実装 (`services/sync/app/utils/db_helper.py`)
- [ ] T016 [P] エラーハンドリング基盤を実装 (`services/sync/app/middleware/error_handler.py`)
- [ ] T017 [P] ロギングミドルウェアを実装 (`services/sync/app/middleware/logging_middleware.py`)
- [ ] T018 [P] Correlation ID ミドルウェアを実装 (`services/sync/app/middleware/correlation_id_middleware.py`)
- [ ] T019 データベースインデックス作成スクリプトを実装 (`services/sync/scripts/init_db.py`)
  - **シンプル化適用**: 初期リリースでは基本インデックスのみ実装、複合インデックスはパフォーマンス測定後に追加
  - 実装内容: 基本インデックス（primary key、TTL）のみ作成
  - 参照: data-model.md の各エンティティ「Indexes」セクション
  - **基本インデックス一覧** (約10-12インデックス):
    - **SyncStatus**: `{edge_id, data_type}` (unique) - Primary key相当
    - **SyncHistory**: `{sync_id}` (unique), `{started_at}` (TTL: 90日)
    - **EdgeTerminal**: `{edge_id}` (unique) - Primary key相当
    - **ScheduledMasterFile**: `{file_id}` (unique) - Primary key相当
    - **FileCollection**: `{collection_id}` (unique) - Primary key相当
    - **TransactionLog**: `{log_id}` (unique), `{synced_at}` (TTL: 30日)
    - **MasterData**: `{category, version}` (unique) - Primary key相当
    - **TerminalStateChange**: `{terminal_id, status_changed_at}` (unique), `{synced_at}` (TTL: 90日)
  - **除外する複合インデックス** (パフォーマンス測定後に追加):
    - SyncStatus: `{status, next_sync_at}`, `{edge_id, updated_at}`
    - SyncHistory: `{edge_id, started_at}`, `{data_type, started_at}`, `{status, started_at}`
    - EdgeTerminal: `{store_code, p2p_priority, status}`, `{tenant_id, store_code}`, `{status, last_heartbeat_at}`
    - ScheduledMasterFile: `{scheduled_at, timing_type, priority}`, `{store_id, applied_count}`, `{scheduled_at, applied_count}`
    - FileCollection: `{edge_id, created_at}`, `{status, created_at}`, `{completed_at, status}`
    - TransactionLog: `{sync_status, occurred_at}`, `{edge_id, occurred_at}`
    - MasterData: `{category, version DESC}`, `{category, updated_at}`
    - TerminalStateChange: `{sync_status, status_changed_at}`, `{business_date, status}`
  - 実装方法:
    - `create_indexes()` 関数で基本インデックスのみ作成
    - 既存インデックスはスキップ (冪等性)
    - 作成完了時にログ出力
  - **憲章準拠**: "推測ではなく計測に基づいて最適化" (パフォーマンスの意識)
- [ ] T020 [P] JWT ヘルパーを実装 (`services/sync/app/utils/jwt_helper.py`)
- [ ] T021 [P] ハッシュヘルパーを実装 (`services/sync/app/utils/hash_helper.py`)
- [ ] T022 [P] ファイルヘルパーを実装 (`services/sync/app/utils/file_helper.py` - zip圧縮/解凍)
- [ ] T023 API 依存性注入を実装 (`services/sync/app/api/dependencies.py`)
- [ ] T024 ヘルスチェックエンドポイントを実装 (`services/sync/app/api/v1/health.py`)
- [ ] T025 [P] pyproject.toml を作成 (`services/sync/pyproject.toml` - ruff, mypy 設定)
- [ ] T026 [P] mypy.ini を作成 (`services/sync/mypy.ini` - 型チェック設定)
- [ ] T027 Pipfile に lint, format, typecheck スクリプトを追加
  - `lint = "ruff check app/"`:
  - `format = "ruff format app/"`:
  - `typecheck = "mypy app/"`

**Checkpoint**: 基盤が準備完了 - ユーザーストーリー実装を並列開始可能

---

## Phase 3: User Story 6 - エッジ端末の認証とセキュリティ (優先度: P1) 🎯 必須基盤

**Goal**: すべての同期機能のセキュリティ基盤となる認証機構を実装

**独立テスト**: Edge 端末が認証 API に対して edge_id と secret を送信し、有効な JWT トークンを取得できることを確認。無効な secret 使用時は 401 エラーが返されることを検証。

### US6 テストタスク

- [ ] T028 [P] [US6 Test] EdgeTerminal モデルのユニットテストを作成 (`tests/unit/test_edge_terminal.py`)
  - 検証項目: edge_id パターン検証、secret ハッシュ化検証、P2P 優先度範囲 (0-99)、is_p2p_seed 検証
  - 期待結果: すべてのテストが RED（失敗）であることを確認
- [ ] T029 [P] [US6 Test] JWT サービスのユニットテストを作成 (`tests/unit/test_jwt_service.py`)
  - 検証項目: トークン生成、トークン検証、有効期限切れ検証、ペイロード検証 (edge_id, tenant_id, store_code)
  - 期待結果: すべてのテストが RED（失敗）であることを確認

### US6 実装タスク

- [ ] T030 [P] [US6] EdgeTerminal モデルを実装 (`services/sync/app/models/documents/edge_terminal.py`)
  - 期待結果: T028 のテストが GREEN（成功）に変わることを確認
- [ ] T031 [US6 Test] EdgeTerminal リポジトリのユニットテストを作成 (`tests/unit/test_edge_terminal_repository.py`)
  - 検証項目: find_by_edge_id, find_by_store_code, P2P シード検索 (p2p_priority でソート)
- [ ] T032 [US6] EdgeTerminal リポジトリを実装 (`services/sync/app/models/repositories/edge_terminal_repository.py`)
  - 期待結果: T031 のテストが GREEN（成功）に変わることを確認
- [ ] T033 [US6] JWT サービスを実装 (`services/sync/app/services/auth/jwt_service.py` - トークン生成・検証)
  - 期待結果: T029 のテストが GREEN（成功）に変わることを確認
- [ ] T034 [P] [US6] 認証リクエスト/レスポンススキーマを実装 (`services/sync/app/schemas/auth_schemas.py`)
- [ ] T035 [US6 Test] 認証 API の統合テストを作成 (`tests/integration/test_auth_api.py`)
  - 検証シナリオ:
    - 正常系: 有効な edge_id + secret → JWT トークン取得成功 (200)
    - 異常系: 無効な secret → 401 エラー
    - 異常系: 存在しない edge_id → 401 エラー
    - トークン検証: 有効なトークン → 認証成功
    - トークン検証: 期限切れトークン → 401 エラー
    - トークンリフレッシュ: 有効なトークン → 新トークン取得成功
- [ ] T036 [US6] 認証 API エンドポイントを実装 (`services/sync/app/api/v1/auth.py` - `/auth/token`, `/auth/refresh`, `/auth/verify`)
  - 期待結果: T035 のテストが GREEN（成功）に変わることを確認
- [ ] T037 [US6] JWT 検証デコレータを実装 (`services/sync/app/api/dependencies.py` - `verify_jwt_token` 依存関数)

**Checkpoint**: 認証機能が完全に動作し、独立してテスト可能

---

## Phase 4: User Story 1 - マスターデータの自動同期 (優先度: P1) 🎯 MVP コア機能

**Goal**: クラウド側のマスターデータ更新をすべての店舗のエッジ端末に自動同期

**独立テスト**: クラウド側でマスターデータを更新し、30-60秒以内にエッジ端末のデータベースに反映されることを確認。ネットワーク障害時でも、復旧後に自動同期されることを検証。

### US1 テストタスク

- [ ] T038 [P] [US1 Test] SyncStatus モデルのユニットテストを作成 (`tests/unit/test_sync_status.py`)
  - 検証項目: 状態遷移検証 (idle → syncing → success/failed)、retry_count 範囲 (0-5)、next_sync_at 計算
- [ ] T039 [P] [US1 Test] SyncHistory モデルのユニットテストを作成 (`tests/unit/test_sync_history.py`)
  - 検証項目: duration_ms 計算、イミュータビリティ (更新禁止)
- [ ] T040 [P] [US1 Test] MasterData モデルのユニットテストを作成 (`tests/unit/test_master_data.py`)
  - 検証項目: data_hash 検証、category 列挙型検証、version 連番検証

### US1 実装タスク

- [ ] T041 [P] [US1] SyncStatus モデルを実装 (`services/sync/app/models/documents/sync_status.py`)
  - 期待結果: T038 のテストが GREEN（成功）に変わることを確認
- [ ] T042 [P] [US1] SyncHistory モデルを実装 (`services/sync/app/models/documents/sync_history.py`)
  - 期待結果: T039 のテストが GREEN（成功）に変わることを確認
- [ ] T043 [P] [US1] MasterData モデルを実装 (`services/sync/app/models/documents/master_data.py`)
  - 期待結果: T040 のテストが GREEN（成功）に変わることを確認
- [ ] T044 [US1 Test] SyncStatus リポジトリのユニットテストを作成 (`tests/unit/test_sync_status_repository.py`)
  - 検証項目: find_by_edge_and_type, find_pending_syncs, update_status
- [ ] T045 [US1] SyncStatus リポジトリを実装 (`services/sync/app/models/repositories/sync_status_repository.py`)
- [ ] T046 [US1] SyncHistory リポジトリを実装 (`services/sync/app/models/repositories/sync_history_repository.py`)
- [ ] T047 [US1] MasterData リポジトリを実装 (`services/sync/app/models/repositories/master_data_repository.py`)
- [ ] T048 [US1 Test] 整合性チェッカーのユニットテストを作成 (`tests/unit/test_integrity_checker.py`)
  - 検証項目: チェックサム検証 (一致/不一致)、レコード件数検証、バージョンギャップ検出 (最大20件)
- [ ] T049 [US1] 整合性チェッカーを実装 (`services/sync/app/services/sync/integrity_checker.py`)
  - 実装内容: チェックサム検証 (FR-007)、レコード件数検証 (FR-008)、バージョンギャップ検出 (FR-009)
- [ ] T050 [US1 Test] Master Data Sync Service のユニットテストを作成 (`tests/unit/test_master_sync_service.py`)
  - 検証項目: 一括同期、差分同期、補完同期、Last Write Wins (FR-018)
- [ ] T051 [US1] Master Data Sync Service を実装 (`services/sync/app/services/sync/master_sync_service.py`)
  - 実装内容: 一括同期 (FR-002)、差分同期 (FR-003)、補完同期 (FR-009)、Last Write Wins (FR-018)
- [ ] T052 [P] [US1] 同期リクエスト/レスポンススキーマを実装 (`services/sync/app/schemas/sync_schemas.py`)
- [ ] T053 [US1 Test] 同期 API の統合テストを作成 (`tests/integration/test_sync_api.py`)
  - 検証シナリオ:
    - POST /sync/poll: 初回同期 (一括同期)、差分同期、補完同期
    - POST /sync/master-data/ack: 同期完了確認
    - GET /sync/status: 同期状態取得
- [ ] T054 [US1] 同期 API エンドポイント (Cloud Mode) を実装 (`services/sync/app/api/v1/sync.py`)
  - 実装内容: `POST /sync/poll`, `POST /sync/master-data/ack`, `GET /sync/status`
- [ ] T055 [US1] ポーリングスケジューラー (Edge Mode) を実装 (`services/sync/app/background/polling_scheduler.py`)
  - 実装内容: APScheduler 使用、30-60秒間隔、max_instances=1
- [ ] T056 [US1] ポーリングジョブロジックを実装 (`services/sync/app/background/jobs/sync_poller.py`)
  - 実装内容: クラウドへのポーリング処理、エラーハンドリング、リトライ機構
- [ ] T057 [US1] main.py に Edge Mode 用スケジューラー起動ロジックを統合

**Checkpoint**: マスターデータ同期が完全に動作し、独立してテスト可能

---

## Phase 5: User Story 2 - トランザクションデータのクラウド集約 (優先度: P1) 🎯 MVP コア機能

**Goal**: 店舗のレジ端末で発生したトランザクションデータをリアルタイムでクラウドに送信

**独立テスト**: エッジ端末でトランザクションを作成し、60秒以内にクラウド側のデータベースに反映されることを確認。ネットワーク障害時にローカルに保存され、復旧後に自動送信されることを検証。

### US2 テストタスク

- [ ] T058 [P] [US2 Test] TransactionLog モデルのユニットテストを作成 (`tests/unit/test_transaction_log.py`)
  - 検証項目: log_id 一意性、sync_status 遷移 (pending → sending → sent/failed)、retry_count 範囲
- [ ] T059 [P] [US2 Test] TerminalStateChange モデルのユニットテストを作成 (`tests/unit/test_terminal_state_change.py`)
  - 検証項目: 状態遷移 (Idle → Opened → Closed)、business_date 形式 (YYYYMMDD)、カウンター検証
- [ ] ~~T060 [P] [US2 Test] Transaction Queue Manager のユニットテストを作成~~ **削除** (シンプル化: Repository パターンで直接管理)

### US2 実装タスク

- [ ] T061 [P] [US2] TransactionLog モデルを実装 (`services/sync/app/models/documents/transaction_log.py`)
- [ ] T062 [P] [US2] TerminalStateChange モデルを実装 (`services/sync/app/models/documents/terminal_state_change.py`)
- [ ] T063 [US2] TransactionLog リポジトリを実装 (`services/sync/app/models/repositories/transaction_log_repository.py`)
  - 実装内容:
    - `find_pending_logs(batch_size: int)`: pending ログをバッチ取得 (sync_status='pending' でソート)
    - `mark_as_sent(log_ids: list)`: 送信完了マーク (sync_status='sent' に更新)
    - `count_pending()`: pending ログ件数取得 (キュー容量管理用)
- [ ] T064 [US2] TerminalStateChange リポジトリを実装 (`services/sync/app/models/repositories/terminal_state_change_repository.py`)
- [ ] ~~T065 [US2] Transaction Queue Manager を実装~~ **削除** (シンプル化: TransactionLog Repository で直接管理)
  - **代替実装**: T063 の TransactionLog Repository メソッドを使用
  - **FIFO削除**: MongoDB TTLインデックスで自動削除 (data-model.md: TransactionLog の synced_at TTL 30日)
  - **容量管理**: T063 の `count_pending()` メソッドで監視、環境変数 `TRANSACTION_QUEUE_MAX_SIZE` (デフォルト: 10000)
- [ ] T066 [US2 Test] Transaction Sync Service のユニットテストを作成 (`tests/unit/test_transaction_sync_service.py`)
  - 検証項目: 送信処理、リトライ機構 (FR-019)、At-least-once delivery (FR-021)
- [ ] T067 [US2] Transaction Sync Service を実装 (`services/sync/app/services/sync/transaction_sync_service.py`)
  - 実装内容: トランザクション送信・受信、リトライ機構 (FR-019)、TransactionLog Repository で直接キュー管理
- [ ] T068 [P] [US2] トランザクション送信リクエスト/レスポンススキーマを実装 (`services/sync/app/schemas/sync_schemas.py` に追加)
- [ ] T069 [US2] トランザクション同期 API エンドポイントを実装 (`services/sync/app/api/v1/sync.py` に追加)
  - 実装内容: `POST /sync/transactions`, `POST /sync/terminal-state`
- [ ] T070 [US2] トランザクション送信スケジューラージョブを実装 (`services/sync/app/background/jobs/transaction_sender.py`)
  - 実装内容: 30-60秒間隔でクラウド送信、TransactionLog Repository の `find_pending_logs()` でバッチ取得
- [ ] T071 [US2] Dapr Pub/Sub トピック購読ハンドラーを実装 (`services/sync/app/api/v1/pubsub.py`)
  - 実装内容: `tranlog_report`, `cashlog_report`, `opencloselog_report` 受信

**Checkpoint**: トランザクションデータ集約が完全に動作し、独立してテスト可能

---

## Phase 6: User Story 4 - データ整合性の自動保証 (優先度: P2)

**Goal**: マスターデータ同期時の整合性検証と自動補完機構を実装

**独立テスト**: 意図的にデータ破損やバージョン欠落を発生させ、自動検証と補完機構が正常に動作することを確認。

### US4 実装タスク

- [ ] T072 [US4] チェックサム検証ロジックを integrity_checker.py に追加 (T049 で作成済みのファイルを拡張、FR-007)
- [ ] T073 [US4] レコード件数検証ロジックを integrity_checker.py に追加 (FR-008)
- [ ] T074 [US4] バージョンギャップ検出・補完ロジックを integrity_checker.py に追加 (FR-009: 最大20件/回)
- [ ] T075 [US4] 補完同期トリガーロジックを master_sync_service.py に追加 (T051 で作成済みのファイルを拡張)
- [ ] T076 [US4] 一括同期切り替え推奨ロジックを master_sync_service.py に追加 (FR-010: 欠落バージョン50件超過時)
- [ ] T077 [US4] エラーハンドリング強化 (自動リトライ、ロールバック処理)

**Checkpoint**: データ整合性保証機能が完全に動作し、独立してテスト可能

---

## Phase 7: User Story 3 - マスターデータ予約反映 (優先度: P2)

**Goal**: 指定日時に新しいマスタファイルを全店舗に自動反映し、P2P 共有でクラウド負荷を軽減

**独立テスト**: クラウド側でファイル名に反映日時を含むマスタファイルを配信し、指定日時に全エッジ端末で自動反映されることを確認。P2P 共有により、同一店舗内の2台目以降の端末はエッジ間通信でファイルを取得することを検証。

### US3 テストタスク

- [ ] T078 [P] [US3 Test] ScheduledMasterFile モデルのユニットテストを作成 (`tests/unit/test_scheduled_master_file.py`)
  - 検証項目: ファイル名パターン検証、timing_type 判定 (scheduled/immediate)、priority 範囲、holding_status 管理
- [ ] T079 [P] [US3 Test] P2P Manager のユニットテストを作成 (`tests/unit/test_p2p_manager.py`)
  - 検証項目: シード選択ロジック (p2p_priority でソート)、フォールバック処理、ダウンロード処理

### US3 実装タスク

- [ ] T080 [P] [US3] ScheduledMasterFile モデルを実装 (`services/sync/app/models/documents/scheduled_master_file.py`)
- [ ] T081 [US3] ScheduledMasterFile リポジトリを実装 (`services/sync/app/models/repositories/scheduled_master_file_repository.py`)
- [ ] T082 [US3] Scheduled Master Service を実装 (`services/sync/app/services/scheduled_master/scheduled_master_service.py`)
  - 実装内容: ファイル登録 (FR-011)、配信、適用ロジック、更新区分サポート (FR-012: A=全件、M=差分)
- [ ] T083 [US3] P2P Manager を実装 (`services/sync/app/services/scheduled_master/p2p_manager.py`)
  - 実装内容: シード選択 (FR-013)、ファイル共有ロジック、ファイル保持状況管理 (FR-014)
- [ ] T084 [P] [US3] 予約マスタリクエスト/レスポンススキーマを実装 (`services/sync/app/schemas/scheduled_master_schemas.py`)
- [ ] T085 [US3 Test] 予約マスタ API の統合テストを作成 (`tests/integration/test_scheduled_master_api.py`)
  - 検証シナリオ:
    - ファイル登録: POST /scheduled-master/files
    - ファイル一覧取得: GET /scheduled-master/files
    - ファイルダウンロード: GET /scheduled-master/files/{file_id}/download
    - 適用確認: POST /scheduled-master/files/{file_id}/ack
- [ ] T086 [US3] 予約マスタ API エンドポイント (Cloud Mode) を実装 (`services/sync/app/api/v1/scheduled_master.py`)
  - 実装内容: `GET /scheduled-master/files`, `POST /scheduled-master/files`, `GET /scheduled-master/files/{file_id}`, `GET /scheduled-master/files/{file_id}/download`, `POST /scheduled-master/files/{file_id}/ack`
- [ ] T087 [US3] P2P ファイル配信エンドポイント (Edge Mode) を実装 (`services/sync/app/api/v1/p2p.py`)
  - 実装内容: `GET /p2p/files/{file_id}` (StreamingResponse 使用), `GET /p2p/peers` (シード検索)
- [ ] T088 [US3] 予約反映スケジューラーを実装 (`services/sync/app/background/scheduled_master_executor.py`)
  - 実装内容: 1分間隔でスキャン、指定日時に反映実行 (FR-011: scheduled_at ±30秒以内)
  - 検証項目: 指定日時±30秒以内での反映精度を統合テストで検証 (SC-010)
- [ ] T089 [US3] P2P ダウンロード + フォールバックロジックを実装 (p2p_manager.py に追加)
  - 実装内容: P2P優先、失敗時はクラウドフォールバック

**Checkpoint**: 予約反映と P2P 共有が完全に動作し、独立してテスト可能

---

## Phase 8: User Story 5 - ファイル収集とトラブルシューティング (優先度: P3)

**Goal**: 店舗システム障害時、本部がエッジ端末のログとシステムファイルを遠隔収集

**独立テスト**: クラウド側から特定のエッジ端末に対してファイル収集指示を送信し、指定したパスのファイルが zip 形式で圧縮され、クラウドに送信されることを確認。

### US5 テストタスク

- [ ] T090 [P] [US5 Test] FileCollection モデルのユニットテストを作成 (`tests/unit/test_file_collection.py`)
  - 検証項目: 状態遷移 (pending → collecting → completed/failed)、max_size_mb 範囲、target_paths 検証
- [ ] T091 [P] [US5 Test] File Collection Service のユニットテストを作成 (`tests/unit/test_file_collection_service.py`)
  - 検証項目: ホワイトリスト検証 (FR-016)、zip 圧縮 (最大100MB)、方式1・方式2の統合

### US5 実装タスク

- [ ] T092 [P] [US5] FileCollection モデルを実装 (`services/sync/app/models/documents/file_collection.py`)
- [ ] T093 [US5] FileCollection リポジトリを実装 (`services/sync/app/models/repositories/file_collection_repository.py`)
- [ ] T094 [US5] File Collection Service を実装 (`services/sync/app/services/file_collection/file_collection_service.py`)
  - 実装内容: 収集タスク管理、zip 圧縮 (FR-015)、ホワイトリスト検証 (FR-016)
- [ ] T095 [P] [US5] ファイル収集リクエスト/レスポンススキーマを実装 (`services/sync/app/schemas/file_collection_schemas.py`)
- [ ] T096 [US5 Test] ファイル収集 API の統合テストを作成 (`tests/integration/test_file_collection_api.py`)
  - 検証シナリオ:
    - タスク作成: POST /file-collection/tasks (単一端末、複数端末、全端末)
    - タスク一覧: GET /file-collection/tasks
    - アーカイブダウンロード: GET /file-collection/tasks/{collection_id}/download
    - ホワイトリスト違反: 401エラー
- [ ] T097 [US5] ファイル収集 API エンドポイント (Cloud Mode) を実装 (`services/sync/app/api/v1/file_collection.py`)
  - 実装内容: `GET /file-collection/tasks`, `POST /file-collection/tasks`, `GET /file-collection/tasks/{collection_id}`, `DELETE /file-collection/tasks/{collection_id}`, `GET /file-collection/tasks/{collection_id}/download`
- [ ] T098 [US5] ファイル収集 Edge API エンドポイント (Edge Mode) を実装 (`services/sync/app/api/v1/file_collection.py` に追加)
  - 実装内容: `GET /edge/file-collection/poll`, `POST /edge/file-collection/tasks/{collection_id}/upload`, `POST /edge/file-collection/tasks/{collection_id}/fail`
- [ ] T099 [US5] ファイル収集ポーリングジョブを実装 (`services/sync/app/background/jobs/file_collection_poller.py`)
  - 実装内容: 定期的にクラウドからタスク取得
- [ ] T100 [US5] ファイル収集実行ロジックを実装 (file_collection_service.py に追加)
  - 実装内容:
    - **方式1 (他サービス)**: 各サービスへの Dapr Service Invocation (`POST /api/v1/file-collection/collect`)
    - **方式2 (Sync自身)**: 直接ファイルシステムアクセス (`aiofiles` 使用)
    - 統合処理: 方式1で収集したzipと方式2で収集したzipを統合して最終アーカイブ生成

**Checkpoint**: ファイル収集機能が完全に動作し、独立してテスト可能

---

## Phase 9: Polish & Cross-Cutting Concerns

**目的**: すべてのユーザーストーリーに影響する改善と統合

- [ ] T101 [P] Circuit Breaker 設定を確認・調整
  - 対象: commons の `HttpClientHelper`, `DaprClientHelper`
  - 設定箇所: `services/sync/app/config/settings.py`
  - 確認項目: 失敗閾値3回、タイムアウト60秒
- [ ] T102 [P] Dapr コンポーネント設定ファイルを作成 (`services/dapr/components/sync-statestore.yaml`, `sync-pubsub.yaml`)
- [ ] T103 [P] docker-compose.yaml に sync サービスエントリを追加 (`services/docker-compose.yaml`)
- [ ] T104 [P] docker-compose.override.yaml に開発用設定を追加 (`services/docker-compose.override.yaml`)
- [ ] T105 全 API エンドポイントのエラーハンドリングを統一
  - エラーコード体系: 80YYZZ 形式 (80=sync service)
  - 構造化エラーレスポンス: error_code, message, detail, timestamp
- [ ] T106 全サービスに構造化ロギングを追加
  - 必須フィールド: timestamp, service_name, tenant_code, correlation_id, edge_id
  - ログレベル: DEBUG, INFO, WARNING, ERROR, CRITICAL
  - 機密情報マスキング: パスワード、APIキー、JWT トークン
- [ ] T107 [P] 全サービスコードで ruff による linting 実行 (`pipenv run lint`)
  - 修正必須: エラーレベルの問題
  - 修正推奨: 警告レベルの問題
- [ ] T108 [P] 全サービスコードで ruff による formatting 実行 (`pipenv run format`)
- [ ] T109 [P] 全サービスコードで mypy による型チェック実行 (`pipenv run typecheck`)
  - 目標: 型エラー0件
- [ ] T110 全サービスのテストカバレッジを測定 (`pipenv run pytest --cov=app tests/`)
  - 目標: 80%以上（重要なビジネスロジックは90%以上）
  - カバレッジレポート生成: `--cov-report=html`
  - 検証項目:
    - ネットワーク復旧後30秒以内の同期再開 (SC-006)
    - タイムアウト、リトライ、サーキットブレーカーの動作検証
- [ ] T111 カバレッジ不足箇所のテスト追加
  - 優先度: 認証、整合性チェック、データ同期ロジック、TransactionLog Repository
- [ ] T112 quickstart.md の手順を検証
  - 検証内容: `services/sync/` で 30分以内にセットアップ完了できることを確認
  - テスト実行: `pipenv run pytest tests/` が成功すること
- [ ] T113 [P] README.md を最終更新
  - 更新内容: セットアップ手順、環境変数一覧、API ドキュメントへのリンク、テスト実行方法
- [ ] T114 パフォーマンス最適化
  - 最適化対象: データベースクエリ、インデックス使用状況確認
  - 目標: API レスポンス 95パーセンタイルで500ms以下
- [ ] T115 セキュリティ強化
  - 強化項目: JWT シークレットローテーション計画、TLS 設定確認、入力検証テスト、ホワイトリスト検証
  - セキュリティスキャン: `pipenv check` 実行

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存関係なし - 即座に開始可能
- **Foundational (Phase 2)**: Setup 完了後 - すべてのユーザーストーリーをブロック
- **User Stories (Phase 3-8)**: すべて Foundational 完了後
  - 並列実行可能 (スタッフ配置に応じて)
  - または優先順位順に順次実行 (P1 → P2 → P3)
- **Polish (Phase 9)**: すべての必要なユーザーストーリー完了後

### User Story Dependencies

- **User Story 6 (P1 - 認証)**: Foundational 完了後、他のストーリーに依存なし - **最優先で実装必須**
- **User Story 1 (P1 - マスターデータ同期)**: US-006 完了後 (JWT 認証が必要)、他のストーリーに依存なし
- **User Story 2 (P1 - トランザクション集約)**: US-006 完了後 (JWT 認証が必要)、US-001 と独立してテスト可能
- **User Story 4 (P2 - 整合性保証)**: US-001 完了後 (マスターデータ同期の拡張)
- **User Story 3 (P2 - 予約反映)**: US-001, US-004 完了後推奨 (整合性機能を活用)
- **User Story 5 (P3 - ファイル収集)**: US-006 完了後、他のストーリーと独立

### Within Each User Story (TDD サイクル)

1. **RED**: テストタスクを実装 → すべてのテストが失敗することを確認
2. **GREEN**: 実装タスクを完了 → すべてのテストが成功することを確認
3. **REFACTOR**: コード品質改善、リファクタリング → テストが引き続き成功することを確認
4. **順序**: テスト → モデル → リポジトリ → サービス → API エンドポイント → バックグラウンドジョブ

### Parallel Opportunities

- **Setup (Phase 1)**: T003, T004, T005, T007, T009, T010, T011, T012 は並列実行可能 (67%)
- **Foundational (Phase 2)**: T015, T016, T017, T018, T020, T021, T022, T025, T026 は並列実行可能 (60%)
- **Foundational 完了後**: 複数のユーザーストーリーを並列実行可能 (チームリソース次第)
- **各ユーザーストーリー内**:
  - テストタスク ([P] マーク付き) は並列実行可能
  - モデル作成タスク ([P] マーク付き) は並列実行可能
  - スキーマ作成タスク ([P] マーク付き) は並列実行可能

---

## Parallel Example: User Story 1 (マスターデータ同期)

```bash
# Phase 1: すべてのテストを並列作成 (RED 確認)
Task: "[US1 Test] SyncStatus モデルのユニットテストを作成"
Task: "[US1 Test] SyncHistory モデルのユニットテストを作成"
Task: "[US1 Test] MasterData モデルのユニットテストを作成"
→ すべてのテストが RED（失敗）であることを確認

# Phase 2: すべてのモデルを並列実装 (GREEN 確認)
Task: "[US1] SyncStatus モデルを実装"
Task: "[US1] SyncHistory モデルを実装"
Task: "[US1] MasterData モデルを実装"
→ すべてのテストが GREEN（成功）に変わることを確認

# Phase 3: リポジトリを順次作成 (モデル完了後)
Task: "[US1] SyncStatus リポジトリを実装"
Task: "[US1] SyncHistory リポジトリを実装"
Task: "[US1] MasterData リポジトリを実装"
```

---

## Implementation Strategy

### MVP First (Phase 1-5: Setup → Foundational → US6 → US1 → US2)

1. Phase 1: Setup を完了 (テスト基盤含む)
2. Phase 2: Foundational を完了 (CRITICAL - すべてのストーリーをブロック、コード品質ツール設定含む)
3. Phase 3: US-006 (認証) を完了 - **セキュリティ基盤、TDD サイクル確立**
4. Phase 4: US-001 (マスターデータ同期) を完了
5. Phase 5: US-002 (トランザクション集約) を完了 - **ローカルキュー管理含む**
6. **STOP and VALIDATE**: 独立してテスト、カバレッジ80%以上確認
7. デプロイ/デモ準備完了

### Incremental Delivery

1. Setup + Foundational → 基盤準備完了 (テスト・コード品質ツール設定済み)
2. US-006 (認証) → 独立テスト → デプロイ/デモ
3. US-001 (マスターデータ同期) → 独立テスト → デプロイ/デモ (MVP!)
4. US-002 (トランザクション集約) → 独立テスト → デプロイ/デモ
5. US-004 (整合性保証) → 独立テスト → デプロイ/デモ
6. US-003 (予約反映) → 独立テスト → デプロイ/デモ
7. US-005 (ファイル収集) → 独立テスト → デプロイ/デモ
8. 各ストーリーは以前のストーリーを壊さずに価値を追加

### Parallel Team Strategy

複数の開発者がいる場合:

1. チーム全体で Setup + Foundational を完了
2. Foundational 完了後:
   - Developer A: US-006 (認証) - **最優先、TDD サイクル確立**
3. US-006 完了後:
   - Developer A: US-001 (マスターデータ同期)
   - Developer B: US-002 (トランザクション集約)
4. US-001, US-002 完了後:
   - Developer A: US-004 (整合性保証)
   - Developer B: US-003 (予約反映)
   - Developer C: US-005 (ファイル収集)
5. ストーリーが独立して完了・統合

---

## Notes

- **[P] タスク** = 異なるファイル、依存関係なし、並列実行可能
- **[Test] タスク** = テストファーストで実装、RED → GREEN → REFACTOR サイクル
- **[Story] ラベル** = タスクを特定のユーザーストーリーにマッピング
- 各ユーザーストーリーは独立して完成・テスト可能であるべき
- **TDD 必須**: 各実装タスクの前に必ずテストタスクを実行、RED 確認後に実装開始
- 各タスクまたは論理グループ後にコミット
- 任意のチェックポイントで停止し、ストーリーを独立して検証
- 回避: 曖昧なタスク、同一ファイルの競合、ストーリー独立性を壊す横断的依存関係

---

## Task Count Summary

- **Total Tasks**: 113 (シンプル化適用後: Transaction Queue Manager 削除、基本インデックスのみ)
- **Setup (Phase 1)**: 12 tasks (テスト基盤含む)
- **Foundational (Phase 2)**: 15 tasks (コード品質ツール設定含む、基本インデックスのみ)
- **US-006 (認証) - P1**: 10 tasks (テスト3 + 実装7)
- **US-001 (マスターデータ同期) - P1**: 20 tasks (テスト7 + 実装13)
- **US-002 (トランザクション集約) - P1**: 12 tasks (テスト1 + 実装11、TransactionLog Repository で直接管理)
  - **削除**: T060 (Transaction Queue Manager テスト), T065 (Transaction Queue Manager 実装)
- **US-004 (整合性保証) - P2**: 6 tasks
- **US-003 (予約反映) - P2**: 12 tasks (テスト2 + 実装10)
- **US-005 (ファイル収集) - P3**: 11 tasks (テスト2 + 実装9)
- **Polish (Phase 9)**: 15 tasks (コード品質チェック、テストカバレッジ測定含む)

**Test Tasks**: 全113タスク中、15タスクがテスト専用タスク (約13%)

**Parallel Opportunities**:
- Setup: 8 tasks (67%)
- Foundational: 9 tasks (60%)
- User Stories: 各ストーリー内のテスト・モデル・スキーマ作成タスク

**Suggested MVP Scope**: Phase 1-5 (Setup + Foundational + US-006 + US-001 + US-002) = 69 tasks
  - **シンプル化効果**: 71タスク → 69タスク (約3%削減)

---

## 変更履歴

**Version 2.1.0** (2025-10-13):
- **シンプル化提案1**: Transaction Queue Manager を削除、TransactionLog Repository で直接管理
  - T060 (Transaction Queue Manager テスト) 削除
  - T065 (Transaction Queue Manager 実装) 削除
  - T063: TransactionLog Repository に `find_pending_logs()`, `mark_as_sent()` メソッド追加
  - T067, T070: TransactionLog Repository を直接使用するように変更
- **シンプル化提案2**: データベースインデックスを基本インデックスのみに簡素化
  - T019: 基本インデックス（primary key、TTL）のみ実装、複合インデックスはパフォーマンス測定後に追加
  - インデックス数: 約28 → 約10-12 (約60%削減)
- 総タスク数: 115 → 113 (2タスク削減)
- MVP スコープ: 71タスク → 69タスク (約3%削減)

**Version 2.0.0** (2025-10-13):
- **提案1**: TDD 対応 - すべての実装タスクの前にテストタスクを追加 (憲章 III 準拠)
- **提案2**: FR-021 ローカルキュー管理タスクを Phase 5 (US-002) に追加
- **提案3**: Phase 2 に ruff/mypy 設定タスク追加、Phase 9 にコード品質チェックタスク追加 (憲章コード品質基準準拠)
- **提案5**: T019 (旧 T015) にデータベースインデックス詳細仕様を追加
- タスク番号を T001-T115 に再採番
- 総タスク数: 84 → 115 (31タスク追加)

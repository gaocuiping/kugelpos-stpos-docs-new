---
layout: default
title: Stock サービス テストケース
parent: テスト
nav_order: 106
---

# Stock サービス プロフェッショナルテストケース設計書

本ドキュメントは、Stock サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

## 📊 現在のテストカバレッジ概況

以下の表は、各テスト階層における設計済ケース数と現在の実装状況（スクリプト自動同期結果）を示しています。

| テスト階層 | 総ケース数 | 実装済 (Implemented) | 未実装 (Missing) | カバレッジ (進捗率) |
|:---|:---:|:---:|:---:|:---:|
| **単体テスト (Unit)** | 4 | 1 | 3 | **25.0%** |
| **結合テスト (Integration)** | 3 | 3 | 0 | **100.0%** |
| **シナリオテスト (Scenario)** | 3 | 3 | 0 | **100.0%** |
| **全体合計 (Total)** | **10** | **7** | **3** | **70.0%** |


### 状態 (Status) の定義

| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB/WebSocket）を Mock し、在庫計算、トランザクションマッピング、およびアラート判定ロジックを検証する。

### 1.1 在庫計算ロジック (`StockService`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **SK-U-001** | **StockServiceの検証** | `StockService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_negative_stock_allowed` <br> *(# Test that negative stock is allowed)* | 在庫が 0 未満になる更新でもエラーにならず、負の値として正しく保存・履歴記録されること。 |
| **SK-U-002** | **StockServiceの検証** | `StockService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_update_stock_zero_change` <br> *(待追加：変化量ゼロの更新処理)* | 変化量が 0 の場合、在庫数は更新されず、履歴のみが記録される（またはスキップされる）仕様通りの動作。 |
| **SK-U-003** | **StockServiceの検証** | `StockService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_process_transaction_with_cancelled_items` <br> *(待追加：キャンセル行のフィルタリング)* | 取引データ内に `is_cancelled: true` の行が含まれる場合、その行の在庫減算がスキップされること。 |
| **SK-U-004** | **StockServiceの検証** | `StockService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_store_stocks` / `test_get_target_stores_all` | 特定エンドポイントまたは全店舗跨ぎでの在庫照会結果が、ロールとテナント権限の範囲内で抽出可能であること。 |
| **SK-A-CRE** | **Create and set up a new tenant in the stock service.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_tenant` | 系统自动追加的代码接口测试 |
| **SK-A-GET** | **Get all stocks for a store** | `API / GET` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `get_store_stocks` | 系统自动追加的代码接口测试 |
| **SK-A-GET** | **Get items with low stock** | `API / GET` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `get_low_stocks` | 系统自动追加的代码接口测试 |
| **SK-A-CRE** | **Create a stock snapshot** | `API / POST` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `create_snapshot` | 系统自动追加的代码接口测试 |
| **SK-A-GET** | **Get stock snapshots filtered by generate_date_time range** | `API / GET` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `get_snapshots_by_date_range` | 系统自动追加的代码接口测试 |
| **SK-A-GET** | **Get a specific snapshot** | `API / GET` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `get_snapshot_by_id` | 系统自动追加的代码接口测试 |
| **SK-A-GET** | **Get items that need reordering** | `API / GET` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `get_reorder_alerts` | 系统自动追加的代码接口测试 |
| **SK-A-GET** | **Get current stock for an item** | `API / GET` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `get_stock` | 系统自动追加的代码接口测试 |
| **SK-A-UPD** | **Update stock quantity** | `API / PUT` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `update_stock` | 系统自动追加的代码接口测试 |
| **SK-A-GET** | **Get stock update history for an item** | `API / GET` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `get_stock_history` | 系统自动追加的代码接口测试 |
| **SK-A-SET** | **Set minimum quantity for an item** | `API / PUT` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `set_minimum_quantity` | 系统自动追加的代码接口测试 |
| **SK-A-SET** | **Set reorder point and quantity for an item** | `API / PUT` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `set_reorder_parameters` | 系统自动追加的代码接口测试 |
| **SK-A-HAN** | **Handle transaction log from pubsub** | `API / POST` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `handle_transaction_log` | 系统自动追加的代码接口测试 |
| **SK-A-GET** | **Get snapshot schedule configuration for a tenant.** | `API / GET` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `get_snapshot_schedule` | 系统自动追加的代码接口测试 |
| **SK-A-UPD** | **Update snapshot schedule configuration for a tenant.** | `API / PUT` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `update_snapshot_schedule` | 系统自动追加的代码接口测试 |
| **SK-A-DEL** | **Delete snapshot schedule configuration for a tenant.** | `API / DELETE` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `delete_snapshot_schedule` | 系统自动追加的代码接口测试 |

### 1.2 アラート判定 (`AlertService`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **SK-U-101** | **アラート境界値の検証** | `AlertService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_alert_threshold_boundary` <br> *(待追加：閾値境界値検証)* | 在庫が `minimum_quantity` と「ちょうど同値」になった際のアラート発火有無が仕様通りであること。 |
| **SK-U-102** | **WebSocketマルチセッション検証** | `WebSocket` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_websocket_multiple_clients` / `test_websocket_unauthorized_connection` | セッション並行処理によるブロードキャストと、不正なアクセスに対するハンドシェイク遮断処理の堅牢性。 |
| **SK-U-301** | **クーロントリガーの検証** | `Cron Triggers` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_create_cron_trigger_daily` (日次Cronの作成)<br>`test_create_cron_trigger_invalid_interval` (不正な間隔のCron)<br>`test_create_cron_trigger_monthly` (月次Cronの作成)<br>`test_create_cron_trigger_weekly` (週次Cronの作成) | 自動ストックスナップショット向けの各種周期（Cron）パターンのバリデーション検証。 |
| **SK-U-302** | **スケジュール操作と管理の検証** | `Schedule Operations` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_delete_snapshot_schedule` (スケジュール削除)<br>`test_get_snapshot_schedule_after_delete` (削除後の取得)<br>`test_get_snapshot_schedule_after_update` (更新後の取得)<br>`test_get_snapshot_schedule_default` (デフォルト取得)<br>`test_update_snapshot_schedule_retention_validation` (保存期間のバリデーション)<br>`test_update_snapshot_schedule_success` (スケジュール更新成功)<br>`test_update_snapshot_schedule_validation_error` (更新時の入力エラー) | スケジュール設定自体のCRUD、保存期間チェックなどのスケジューラー管理機能。 |
| **SK-U-303** | **テナント固有パラメータ検証** | `Tenant Parameters` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_remove_tenant_schedule` (テナントスケジュール削除)<br>`test_set_reorder_parameters` (発注点パラメータ設定)<br>`test_update_tenant_schedule_disabled` (テナント無効化設定)<br>`test_update_tenant_schedule_enabled` (テナント有効化設定) | 店舗（テナント）ごとの発注点設定の有効無効化、固有スケジュールの設定操作検証。 |
| **SK-U-304** | **スナップショット生成の検証** | `Snapshot Generate` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_create_snapshot` (スナップショット作成)<br>`test_create_snapshot_with_generate_date_time` (特定日時のスナップショット作成)<br>`test_stock_snapshot_includes_reorder_fields` (発注点項目の包含) | 特定日時でのスナップショットデータ生成ロジックの正確性と、発注点情報包含の検証。 |
| **SK-U-305** | **スナップショット抽出の検証** | `Snapshot Retrieve` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_snapshots_by_date_range` (期間指定・スナップ取得)<br>`test_get_snapshots_with_end_date_only` (終了日のみ指定)<br>`test_get_snapshots_with_start_date_only` (開始日のみ指定)<br>`test_get_snapshots_without_date_range` (全期間取得) | スナップショット検索時の期間（日付）指定の組み合わせ・境界条件の正常系検証。 |
| **SK-U-306** | **履歴とページネーション検証** | `History & Pagination` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_pagination_parameters` (ページネーション設定)<br>`test_stock_history` (在庫履歴取得) | 履歴系巨大データのページネーション（Limit/Offset等）によるクエリ安定性。 |
| **SK-U-307** | **最小在庫アラートの境界検証** | `Minimum Stock Alert` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_reorder_alerts_empty` (空のアラート取得)<br>`test_minimum_stock_alert` (最小在庫アラート)<br>`test_update_stock_triggers_reorder_alert` (在庫更新時のアラート発火)<br>`test_websocket_minimum_stock_alert` (WS経由最小在庫アラート)<br>`test_websocket_no_alert_when_above_thresholds` (閾値超過時のアラート非発火) | 閾値を割った際の在庫不足アラート発生と、満たしている際の非発火境界の検証。 |
| **SK-U-308** | **発注点とWebSocketアラート検証** | `Reorder & WS Alert` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_websocket_connection` (WS接続確立)<br>`test_websocket_reorder_alert` (WS経由発注アラート)<br>`test_websocket_reorder_alert_new_item` (新規商品のWSアラート) | 発注点レベルに対する警告イベントと、新規商品登録時の WebSocket ブロードキャストの疎通。 |
| **SK-U-309** | **店舗スコープ照会と情報隔離** | `Store Scope Queries` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_all_tenant_ids` (全テナントID取得)<br>`test_get_target_stores_specific` (特定店舗指定取得)<br>`test_get_stock` (在庫取得) | 複数テナント混在環境でのストアID指定横断クエリ等による情報漏洩防止と正当性。 |
| **SK-U-310** | **ライフサイクルと環境修復検証** | `Lifecycle & Health` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_health_check` (ヘルスチェック)<br>`test_get_status` (ステータス取得)<br>`test_shutdown` (シャットダウン挙動)<br>`test_cleanup_test_data` (テストデータ修復) | 起動中・シャットダウン時のステータスハンドリングやテストデータ自己修復とクリーンアップ。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）、Dapr Pub/Sub 連携、およびスケジューラーの動作を検証する。

| ID | テストタイトル | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **SK-I-001** | **MongoDBデータ永続化検証** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_update_stock` / `test_get_snapshots_pagination` | `update_quantity_atomic_async` による DB レベルのアトミック減算、および大量 Snapshot 履歴のページネーション取得。 |
| **SK-I-002** | **Dapr Pub/Subイベント検証** | `Dapr PubSub` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_dapr_subscribe` <br> *(# Test Dapr subscription endpoint)* | `topic-tranlog` に対するサブスクリプション設定が正しく公開されていること。 |
| **SK-I-003** | **スケジューラージョブ検証** | `Scheduler` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_snapshot_scheduler` / `test_create_cron_trigger...` / `test_update_snapshot_schedule...` | 手動起動に加え、Daily/Weekly/Monthly 等の Cron 式の登録、削除、無効化などのスケジューリング全容が機能すること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、在庫のライフサイクルをエンドツーエンドで検証する。

| ID | テストタイトル | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|:---|
| **SK-S-001** | **基本在庫運用と履歴管理の検証** | 基本在庫運用と履歴管理 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. **初期取得**: `GET` 要求による現行在庫の確認<br>2. **アトミック更新**: 増減量(Quantity)を指定した `PUT` 更新<br>3. **履歴検証**: `History` コレクションに更新前後の差分と理由が正しく追記されること | `test_stock` | 単純な上書きではなく、アトミックな増減計算により並行処理時も在庫数が正確に保たれること。 |
| **SK-S-002** | **棚卸スナップショット・スケジュールの検証** | 棚卸スナップショット・スケジュール | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 定期実行 API または Scheduler 経由での Snapshot 生成起動<br>2. `Snapshot` 履歴の取得検証<br>3. 日付範囲パラメータ (`start_date`, `end_date`) を用いた検索 | `test_snapshot_date_range` / `test_snapshot_scheduler` | 月次・日次などの指定時点で、全商品の在庫数が静止点（スナップショット）として確実に保管され、後から期間指定で検索できること。 |
| **SK-S-003** | **リアルタイム発注警告 (WebSocket)の検証** | リアルタイム発注警告 (WebSocket) | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. クライアントが WebSocket エンドポイントに接続<br>2. 別の API 経由で対象商品の在庫数を「発注点 (Reorder Level)」以下に減算<br>3. クライアント側でリアルタイムに JSON Alert を受信 | `test_websocket_alerts` / `test_reorder_alerts` | 下限割れ（発注点割れ）を検知した直後に、プッシュ型通信で接続中のPOSや管理画面へ即座に通知が届くこと。 |

---

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: テスト環境のセットアップおよび共通クレンジングを共通化する。

| 関数名 (Helper Function) | 役割 (Responsibility) | 备注 (Notes) |
|:---|:---|:---|
| `test_setup_data` | 初期在庫マスター（ITEM001等）の投入 | テスト実行前の環境構築 |
| `test_clean_data` | 全在庫・履歴データの物理削除 | 冪等性確保のための後処理 |
| `conftest.test_auth_headers` | Bearer Token 基盤の提供 | 認可が必要な API 用のヘッダー生成 |

> [!TIP]
> 文档现已覆盖 Stock 服务相关的 11 个测试文件，单体测试层级的 GAP 已作为后续优先补全项。

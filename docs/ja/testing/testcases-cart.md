---
layout: default
title: Cart サービス テストケース
parent: テスト
nav_order: 102
---

# Cart サービス プロフェッショナルテストケース設計書

本ドキュメントは、Cart サービスのソースコード（`app/`）を詳細に解析した结果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

## 📊 現在のテストカバレッジ概況

以下の表は、各テスト階層における設計済ケース数と現在の実装状況（スクリプト自動同期結果）を示しています。

| テスト階層 | 総ケース数 | 実装済 (Implemented) | 未実装 (Missing) | カバレッジ (進捗率) |
|:---|:---:|:---:|:---:|:---:|
| **単体テスト (Unit)** | 11 | 10 | 1 | **90.9%** |
| **結合テスト (Integration)** | 5 | 4 | 1 | **80.0%** |
| **シナリオテスト (Scenario)** | 6 | 5 | 1 | **83.3%** |
| **全体合計 (Total)** | **22** | **19** | **3** | **86.4%** |

### 状態 (Status) の定義

| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB/API）を Mock し、各モジュールの純粋なロジック、計算精度、および状態遷移を検証する。

### 1.1 状態管理 & サービスフロー (`CartService` / `TranService`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | <div style="width: 250px">匹配规则 (Mapping Rules / Function Name & Comments)</div> | <div style="width: 200px">期待される結果</div> |
|:---|:---|:---|:---|:---|:---|
| **CT-U-001** | **CartServiceの検証** | `CartService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_cart_operations` <br> *(# Check if the terminal is opened [异常系])* | `TerminalStatusException` が送出されること。 |
| **CT-U-002** | **CartStateManagerの検証** | `CartStateManager` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_resume_item_entry_from_invalid_states` <br> *(# Test that resume item entry fails from invalid states)* | `EventBadSequenceException` が送出されること。 |
| **CT-U-003** | **CartServiceの検証** | `CartService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_add_payment_to_cart_async_balance_zero` <br> *(# The balance is equal to 0 [単体テスト边界])* | `BalanceZeroException` が送出されること。 |
| **CT-U-004** | **取引サービス統合の検証** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_void_already_voided_transaction_raises_exception` <br> *(# Test that void operation on already voided transaction raises exception)* | `AlreadyVoidedException` が送出されること。 |
| **CT-U-005** | **取引サービス統合の検証** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_return_already_refunded_transaction_raises_exception` <br> *(# Test that return operation on already refunded transaction raises exception)* | `AlreadyRefundedException` が送出されること。 |
| **CT-U-006** | **取引サービス統合の検証** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_transaction_list_with_status_merges_correctly` <br> *(# Test that transaction list correctly merges void/return status)* | 状態フラグ（isVoided等）が正しくマージされていること。 |
| **CT-U-007** | **CartServiceの検証** | `CartService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_cashless_payment_simple` / `test_cashless_payment_with_detailed_receipt_info` | 異常な明細情報に対するキャッシュレス決済処理の安全性確保。 |
| **CT-U-008** | **CartServiceの検証** | `CartService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_payment_by_others` / `test_multiple_payment_methods` | 複数・他者支払いの異常系・正常系遷移の確保。 |
| **CT-U-009** | **取引サービス統合の検証** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_void_return_resets_original_refund_status` / `test_return_voided_transaction_prevention` | 排他的な（相容れない）キャンセル操作の衝突と二重精算を防ぐ。 |

### 1.2 計算エンジン (`logics/`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | <div style="width: 250px">匹配规则 (Mapping Rules / Function Name & Comments)</div> | <div style="width: 200px">期待される結果</div> |
|:---|:---|:---|:---|:---|:---|
| **CT-U-101** | **calc_tax_logicの検証** | `calc_tax_logic` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_calc_subtotal_async` / `test_calc_subtotal_skips_cancelled_items` | 取消されたアイテムを除外して、各税区分の `tax_amount` が正確に計算されること。 |
| **CT-U-102** | **calc_tax_logicの検証** | `calc_tax_logic` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_calc_tax_rounding_ceil` <br> *(待追加：端数処理モードの網羅検証)* | `RoundMethod.Ceil/Floor` に従い正しく丸められること。 |
| **CT-U-103** | **calc_line_itemの検証** | `calc_line_item` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_update_sales_info_async_with_discounts` / `test_update_sales_info_async_with_cancelled_items` | %割引 -> 定額割引 の順序での算出と、赤黒処理が独立して行われること。 |
| **CT-U-104** | **calc_discountの検証** | `calc_discount` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_discount_engine` | 各種割引計算エンジンの内部状態推移の正確性。 |

### 1.3 ユーティリティ & キャッシュ (`utils/`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | <div style="width: 250px">匹配规则 (Mapping Rules / Function Name & Comments)</div> | <div style="width: 200px">期待される結果</div> |
|:---|:---|:---|:---|:---|:---|
| **CT-U-201** | **TerminalInfoCacheの検証** | `TerminalInfoCache` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_cache_initialization` / `test_cache_clear_all` / `test_cache_expiration` / `test_cache_clear_by_tenant` | TTL 経過後の自動削除およびテナント間のデータ隔離が徹底され、メモリリークを防ぐ。 |
| **CT-U-202** | **TextHelperの検証** | `TextHelper` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_truncate_text_japanese` / `test_truncate_text_edge_cases` / `test_fixed_left_with_truncate` | 日本語/ASCII 混在時の正確な表示幅計算（全角半角）と強制改行処理が崩れないこと。 |
| **CT-U-203** | **DaprSessionの検証** | `DaprSession` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_session_reuses_existing_session` / `test_session_timeout_configuration` | Dapr セッションタイムアウトの正確な引継ぎと、再利用による負荷軽減。 |
| **CT-U-204** | **gRPCHelperの検証** | `gRPCHelper` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_stub_creates_separate_channels_for_different_tenants` / `test_close_handles_errors_gracefully` | 通信断絶時のコネクションセーフティと、マルチテナント間のRPCチャネル共有汚染の防止。 |
| **CT-U-301** | **キャッシュとマスタ参照の検証** | `Cache & Master` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_cache_miss` (キャッシュミス)<br>`test_cache_remove` (キャッシュ削除)<br>`test_cache_set_and_get` (キャッシュ設定と取得)<br>`test_cache_update` (キャッシュ更新)<br>`test_get_channel_cache_stats` (チャネルキャッシュ統計)<br>`test_get_item_by_code_from_cache` (キャッシュからの商品取得)<br>`test_get_item_by_code_multiple_calls_reuse_stub` (複数呼出時のスタブ再利用)<br>`test_get_item_by_code_uses_module_level_stub` (モジュールレベルスタブ使用)<br>`test_set_item_master_documents` (商品マスタドキュメント設定)<br>`test_unregistered_item_error` (未登録商品エラー)<br>`test_get_tenant_terminal_ids` (テナント・端末ID取得) | キャッシュ（TTL、Miss時振る舞い）やマスタ参照の各種バリエーションと未登録商品ハンドリング。 |
| **CT-U-302** | **Dapr Session/Channelの堅牢性検証** | `Session/Channel` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_close_all_channels` (全チャネル切断)<br>`test_close_session` (セッション終了)<br>`test_close_without_channels_is_safe` (チャネル無し切断の安全性)<br>`test_close_without_session_is_safe` (セッション無し切断の安全性)<br>`test_get_session_after_close_creates_new_session` (切断後の新規セッション作成)<br>`test_get_session_creates_new_session` (新規セッション作成)<br>`test_get_stub_after_close_creates_new_channel` (切断後のスタブ再作成)<br>`test_get_stub_creates_channel_on_first_call` (初回スタブ生成時のチャネル作成)<br>`test_get_stub_reuses_existing_channel` (既存チャネルの再利用)<br>`test_multiple_close_calls_are_safe` (複数回切断の安全性)<br>`test_session_connector_configuration` (セッションコネクタの設定) | Dapr や gRPC セッション・チャネルの多重・不正クローズに対する安全な回復処理とコネクション再利用。 |
| **CT-U-303** | **特殊決済とステータス取得の検証** | `Payment & Status` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_bill_with_insufficient_balance` (残高不足での決済)<br>`test_get_status_by_transaction_not_found` (取引不在時のステータス取得)<br>`test_get_status_for_transactions` (複数取引のステータス取得)<br>`test_get_transaction_list_with_status_empty_list` (空リストのステータス取得)<br>`test_line_item_operations` (明細行の操作)<br>`test_transaction_operations` (取引操作)<br>`test_transaction_status_in_list` (リスト内状態の取得)<br>`test_transaction_status_in_single_get` (単一取得時の状態)<br>`test_payment_process` (支払プロセス)<br>`test_stamp_duty` (印紙税計算)<br>`test_update_sales_info_async_empty_cart` (空カートでの売上情報非同期更新) | 残高不足決済、空カートでの計算、印紙税適用しきい値、トランザクション状態の空配列等、取引異常系。 |
| **CT-U-304** | **取消・返品による状態遷移検証** | `Void, Return & State` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_duplicate_return_prevention` (二重返品防止)<br>`test_mark_as_refunded_new_document` (新規文書の返金マーク)<br>`test_mark_as_voided_existing_document` (既存文書の取消マーク)<br>`test_reset_refund_status_no_existing_document` (文書不在時の返金状態リセット)<br>`test_reset_refund_status_preserves_void_info` (取消情報を保つ状態リセット)<br>`test_reset_refund_status_success` (返金状態リセット成功)<br>`test_resume_item_entry_clears_all_payments` (再開時の全支払クリア)<br>`test_resume_item_entry_preserves_line_items` (再開時の明細保護)<br>`test_return_async_checks_refund_status` (返品時の返金状態確認)<br>`test_return_async_checks_void_status` (返品時の取消状態確認)<br>`test_return_transaction_success` (返品取引成功)<br>`test_void_async_checks_status_history` (非同期取消の履歴確認)<br>`test_void_returned_transaction_prevention` (返品済取引の取消防止) | レジューム時の支払情報リセット、取消/返品の二重実行抑止、ステータス履歴の参照等、状態遷移の防御機能。 |
| **CT-U-305** | **レシート印字テキストとUIの検証** | `Text & UI` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_fixed_left_japanese_truncate` (日本語左寄せ切捨て)<br>`test_fixed_left_without_truncate` (切捨て無し左寄せ)<br>`test_line_split_simulation` (行分割シミュレーション)<br>`test_truncate_text_ascii` (ASCIIテキスト切捨て)<br>`test_truncate_text_mixed` (混合テキスト切捨て)<br>`test_truncate_text_with_suffix` (接尾辞付き切捨て) | レシート・ジャーナル印字用のテキストフォーマット（サフィックス付き全角/半角混在時のパディング強制改行等）。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）、Dapr サービス、およびリポジトリ間のデータ連携を検証する。

### 2.1 データ永続化 / 通信

| ID | テストタイトル | 連携先 | 状态 (Status) | <div style="width: 250px">匹配规则 (Mapping Rules / Function Name & Comments)</div> | <div style="width: 200px">期待される結果</div> |
|:---|:---|:---|:---|:---|:---|
| **CT-I-001** | **MongoDBデータ永続化検証** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_mark_as_voided_new_document` <br> *(# Test persistent status marking)* | 保存前后的对象属性一致。 |
| **CT-I-002** | **gRPCネットワーク通信検証** | `gRPC` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_item_by_code_adds_to_cache` <br> *(# Verify item master gRPC cache logic)* | 通信成功且二次请求使用缓存。 |
| **CT-I-003** | **Dapr Pub/Subイベント検証** | `Dapr PubSub` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_void_transaction_success` <br> *(# Test successful void and event publishing)* | `transaction_completed` 消息正确发送。 |
| **CT-I-004** | **取引サービス統合の検証** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_tranlog_by_query_merges_status` <br> *(# Test status merging in paginated queries)* | ページネーション取得時、過去の取消・返品状態が正しく統合される。 |
| **CT-I-005** | **MongoDBアトミックトランザクション検証** | `Mongo Transaction` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_atomic_update_with_transaction` (待追加) | エラー発生時、両方のドキュメントがロールバックされること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、複雑な業務フローをエンドツーエンドで検証する。

| ID | テストタイトル | シナリオ名 | 状态 (Status) | <div style="width: 200px">业务步骤 (Business Steps)</div> | <div style="width: 200px">匹配规则 (Function & Comments)</div> | <div style="width: 200px">期待される検証点</div> |
|:---|:---|:---|:---|:---|:---|:---|
| **CT-S-001** | **標準販売フローの検証** | 標準販売フロー | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `POST /carts` (作成)<br>2. `POST /.../lineItems` (追加)<br>3. `POST /.../subtotal` (小計)<br>4. `POST /.../payments` (支払)<br>5. `POST /.../bill` (完了) | `test_cart_operations` <br> *(# カートの基本的な操作テスト)* | 合計金額、税額、取引ログ、および状態遷移の完全性。 |
| **CT-S-002** | **レジュームの検証** | レジューム | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. カート作成・商品追加<br>2. `Paying` 状態へ遷移<br>3. 現金 100円を入力 (一部支払)<br>4. `POST /.../resume-item-entry` 実行 | `test_resume_item_entry_from_paying_state` <br> *(# Test resuming item entry from paying state)* | 支払い情報のクリア、および `EnteringItem` への状態回退。 |
| **CT-S-003** | **印紙税適用の検証** | 印紙税適用 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. カート作成<br>2. 50,001円以上の商品を追加<br>3. 現金決済を実行 | `test_duplicate_void_prevention` <br> *(# Test stamp duty calculation boundary)* | `is_stamp_duty_applied` が true であること。 |
| **CT-S-004** | **キャッシュレスの検証** | キャッシュレス | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. カート作成<br>2. 支払リクエスト (camelCase 形式で送信) | `test_cashless_payment_with_wrong_case` <br> *(# Test camelCase vs snake_case validation)* | バリデーションエラー (422) の返却。 |
| **CT-S-005** | **異常解析の検証** | 異常解析 | ![Missing](https://img.shields.io/badge/Status-Missing-red) | 1. カート作成<br>2. 非常に複雑なレシート情報を含む支払リクエスト | `test_payment_cashless_error` 等 | 解析不能時の適切なエラーレスポンス (406等)。 |
| **CT-S-006** | **ヘルスチェックの検証** | ヘルスチェック | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `GET /health` 実行<br>2. バックグラウンドジョブのステータスを確認 | `test_health_endpoint_background_jobs_details` | システム各コンポーネントの生存確認。 |

### 3.2 異常系・リカバリシナリオ
**【Scenario-02】: 支払い中断とレジューム**
- **ステップ**:
  1. 商品登録完了、支払い待ち状態 (`Paying`) に遷移
  2. 現金 100円 を入力 (一部支払い)
  3. `POST /carts/{id}/resume-item-entry` を実行
- **検証ポイント**:
  - 既存の `payments` リストが空になっていること。
  - カートステータスが `EnteringItem` に戻り、追加の商品登録が可能であること。

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: テストケースの実行に必要な環境構築（テナント作成、端末オープン等）を共通化する。これらは各テストの「前提条件」として機能する。

| 関数名 (Helper Function) | 役割 (Responsibility) | 备注 (Notes) |
|:---|:---|:---|
| `get_authentication_token` | Admin 認証トークンの取得 | 全ての管理 API 操作の基盤 |
| `create_tenant` | テスト用テナントの動的作成 | 環境汚染を防ぐための独立したテナント構築 |
| `open_terminal` | ターミナルの営業開始 (Opened) | 決済・カート操作を可能にするための状態制御 |
| `get_terminal_info` | ターミナル詳細情報の取得 | API Key や TerminalID の動的取得 |
| `create_cart_with_items` | 標準的な商品入りカートの即時作成 | シナリオテストの前座として多用 |

> [!NOTE]
> 自动化同步脚本在扫描代码时，会优先识别这些 Helper 函数的存在，以确保测试环境初始化逻辑的鲁棒性。

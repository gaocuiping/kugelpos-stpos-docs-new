---
layout: default
title: Cart サービス テストケース
parent: テスト
nav_order: 102
---

# Cart サービス プロフェッショナルテストケース設計書

本ドキュメントは、Cart サービスのソースコード（`app/`）を詳細に解析した结果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

### 状態 (Status) の定義
| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB/API）を Mock し、各モジュールの純粋なロジック、計算精度、および状態遷移を検証する。

### 1.1 状態管理 & サービスフロー (`CartService` / `TranService`)
| ID | テスト対象 | 状態 (Status) | 匹配规则 (Mapping Rules / Function Name & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **CT-U-001** | `CartService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_cart_operations` <br> *(# Check if the terminal is opened [异常系])* | `TerminalStatusException` が送出されること。 |
| **CT-U-002** | `CartStateManager` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_resume_item_entry_from_invalid_states` <br> *(# Test that resume item entry fails from invalid states)* | `EventBadSequenceException` が送出されること。 |
| **CT-U-003** | `CartService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_add_payment_to_cart_async_balance_zero` <br> *(# The balance is equal to 0 [単体テスト边界])* | `BalanceZeroException` が送出されること。 |
| **CT-U-004** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_void_already_voided_transaction_raises_exception` <br> *(# Test that void operation on already voided transaction raises exception)* | `AlreadyVoidedException` が送出されること。 |
| **CT-U-005** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_return_already_refunded_transaction_raises_exception` <br> *(# Test that return operation on already refunded transaction raises exception)* | `AlreadyRefundedException` が送出されること。 |
| **CT-U-006** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_transaction_list_with_status_merges_correctly` <br> *(# Test that transaction list correctly merges void/return status)* | 状態フラグ（isVoided等）が正しくマージされていること。 |

### 1.3 ユーティリティ & キャッシュ (`utils/`)
| ID | テスト対象 | 状态 (Status) | 匹配规则 (Mapping Rules / Function Name & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **CT-U-201** | `TerminalInfoCache` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_cache_expiration` / `test_cache_clear_by_tenant` | TTL 経過後の自動削除およびテナント間のデータ隔離。 |
| **CT-U-202** | `TextHelper` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_truncate_text_mixed` / `test_line_split_simulation` | 日本語/ASCII 混在時の正確な表示幅計算と改行処理。 |

### 1.2 計算エンジン (`logics/`)
| ID | テスト対象 | 状态 (Status) | 匹配规则 (Mapping Rules / Function Name & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **CT-U-101** | `calc_tax_logic` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_calc_subtotal_async` <br> *(# Test the main calc_subtotal_async function)* | 各税区分の `tax_amount` が正確に計算されること。 |
| **CT-U-102** | `calc_tax_logic` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_calc_tax_rounding_ceil` <br> *(待追加：端数処理モードの網羅検証)* | `RoundMethod.Ceil/Floor` に従い正しく丸められること。 |
| **CT-U-103** | `calc_line_item` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_update_sales_info_async_with_discounts` <br> *(# Test update_sales_info_async with various discounts)* | %割引 -> 定額割引 の順序で算出されること。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）、Dapr サービス、およびリポジトリ間のデータ連携を検証する。

### 2.1 データ永続化 / 通信
| ID | 連携先 | 状态 (Status) | 匹配规则 (Mapping Rules / Function Name & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **CT-I-001** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_mark_as_voided_new_document` <br> *(# Test persistent status marking)* | 保存前后的对象属性一致。 |
| **CT-I-002** | `gRPC` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_item_by_code_adds_to_cache` <br> *(# Verify item master gRPC cache logic)* | 通信成功且二次请求使用缓存。 |
| **CT-I-003** | `Dapr PubSub` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_void_transaction_success` <br> *(# Test successful void and event publishing)* | `transaction_completed` 消息正确发送。 |
| **CT-I-004** | `TranService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_tranlog_by_query_merges_status` <br> *(# Test status merging in paginated queries)* | ページネーション取得時、過去の取消・返品状態が正しく統合される。 |
| **CT-I-005** | `Mongo Transaction` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_atomic_update_with_transaction` (待追加) | エラー発生時、両方のドキュメントがロールバックされること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、複雑な業務フローをエンドツーエンドで検証する。

| ID | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|
| **CT-S-001** | 標準販売フロー | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `POST /carts` (作成)<br>2. `POST /.../lineItems` (追加)<br>3. `POST /.../subtotal` (小計)<br>4. `POST /.../payments` (支払)<br>5. `POST /.../bill` (完了) | `test_cart_operations` <br> *(# カートの基本的な操作テスト)* | 合計金額、税額、取引ログ、および状態遷移の完全性。 |
| **CT-S-002** | レジューム | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. カート作成・商品追加<br>2. `Paying` 状態へ遷移<br>3. 現金 100円を入力 (一部支払)<br>4. `POST /.../resume-item-entry` 実行 | `test_resume_item_entry_from_paying_state` <br> *(# Test resuming item entry from paying state)* | 支払い情報のクリア、および `EnteringItem` への状態回退。 |
| **CT-S-003** | 印紙税適用 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. カート作成<br>2. 50,001円以上の商品を追加<br>3. 現金決済を実行 | `test_duplicate_void_prevention` <br> *(# Test stamp duty calculation boundary)* | `is_stamp_duty_applied` が true であること。 |
| **CT-S-004** | キャッシュレス | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. カート作成<br>2. 支払リクエスト (camelCase 形式で送信) | `test_cashless_payment_with_wrong_case` <br> *(# Test camelCase vs snake_case validation)* | バリデーションエラー (422) の返却。 |
| **CT-S-005** | 異常解析 | ![Missing](https://img.shields.io/badge/Status-Missing-red) | 1. カート作成<br>2. 非常に複雑なレシート情報を含む支払リクエスト | `test_payment_cashless_error` 等 | 解析不能時の適切なエラーレスポンス (406等)。 |
| **CT-S-006** | ヘルスチェック | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `GET /health` 実行<br>2. バックグラウンドジョブのステータスを確認 | `test_health_endpoint_background_jobs_details` | システム各コンポーネントの生存確認。 |

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

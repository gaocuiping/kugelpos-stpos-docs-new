---
layout: default
title: Report サービス テストケース
parent: テスト
nav_order: 105
---

# Report サービス プロフェッショナルテストケース設計書

本ドキュメントは、Report サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

## 📊 現在のテストカバレッジ概況

以下の表は、各テスト階層における設計済ケース数と現在の実装状況（スクリプト自動同期結果）を示しています。

| テスト階層 | 総ケース数 | 実装済 (Implemented) | 未実装 (Missing) | カバレッジ (進捗率) |
|:---|:---:|:---:|:---:|:---:|
| **単体テスト (Unit)** | 4 | 1 | 3 | **25.0%** |
| **結合テスト (Integration)** | 2 | 2 | 0 | **100.0%** |
| **シナリオテスト (Scenario)** | 3 | 3 | 0 | **100.0%** |
| **全体合計 (Total)** | **9** | **6** | **3** | **66.7%** |


### 状態 (Status) の定義

| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB/PubSub）を Mock し、集計計算、税額配分、およびプラグイン管理ロジックを検証する。

### 1.1 集計コアロジック (`ReportService`)

| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **RP-U-001** | `ReportService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_partial_return_tax_accuracy` <br> *(待追加：部分返品時の税計算)* | 複数明細から一部のみを返品した際、残りの明細との合計税額が 1 円単位で整合すること。 |
| **RP-U-002** | `ReportService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_payment_equals_sales_plus_tax_always` / `test_three_way_payment_split` / `test_five_way_payment_split` | 決済金額の合計が「純売上＋税額」と完全に一致し、複雑な分割払いの際も 1 円の誤差も生じないこと。 |
| **RP-U-003** | `ReportService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_multiple_tax_rates_no_cartesian_product` / `test_mixed_tax_types` / `test_store_wide_multi_terminal_with_cartesian_product_risk` | 複数税率(8%, 10%)や非課税アイテムが混在する巨大ジャーナル集計時に、デカルト積（直積）爆発を起こさず正確な全件レポートが生成される。 |
| **RP-U-004** | `ReportService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_complex_void_scenario` / `test_multiple_returns_same_day` / `test_void_vs_cancelled_difference` | 返品(Return)、取消(Void)、またはフラグ上での Cancelled の違いを正確に解釈し、純売上から正しく控除（または無視）されること。 |
| **RP-U-005** | `ReportService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_flash_report_rejects_date_range_store` / `test_flash_report_accepts_single_date` | リアルタイムフラッシュレポート取得時、仕様外となる複数日（Range）指定が API レベルで安全に遮断されること。 |

### 1.2 プラグイン管理 (`ReportPluginManager`)

| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **RP-U-101** | `PluginManager` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_plugin_load_failure_handling` <br> *(待追加：プラグインエラー処理)* | 特定のレポートプラグインの読み込みに失敗した場合でも、システム全体が停止せず、他プラグインへ影響を与えないこと。 |

### 1.3 集計バリエーション・境界値検証

| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **RP-U-301** | `Tax Variations` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_empty_taxes_array`<br>`test_external_tax_only`<br>`test_internal_tax_only`<br>`test_zero_taxes`<br>`test_tax_breakdown_label` | 内外税の片方のみ、税額ゼロ、空配列といった各種税区分境界での集計安全性を検証。 |
| **RP-U-302** | `Payment Logic` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_payment_amount_calculation`<br>`test_payment_sum_equals_sales_with_tax`<br>`test_sales_report_amount_bug`<br>`test_zero_amount_transaction` | 基本的な決済金額計算、ゼロ円取引、および既知の売上集計バグの回帰検証を含む金額整合性チェック。 |
| **RP-U-303** | `Complex Payment Splits` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_extreme_split_payments_with_multiple_taxes`<br>`test_mixed_transaction_types_with_cartesian_risk`<br>`test_multi_transaction_payment_integrity`<br>`test_multiple_payment_methods_mixed`<br>`test_rounding_one_yen_difference` | 複数税率での極端な分割払いや端数丸めによる「1円のズレ」許容検証、複数決済手段混在時のデカルト積リスク防御機能。 |
| **RP-U-304** | `Return Transactions` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_return_exceeds_sales`<br>`test_return_transaction_basic`<br>`test_return_transactions_aggregation`<br>`test_with_returns` | 返品（返金）に関する基本ロジックや、売上額を超過する返金といったエラー・境界値の検証。 |
| **RP-U-305** | `Void Transactions` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_multiple_voids_same_transaction_type`<br>`test_void_return_basic`<br>`test_void_sales_basic` | 取消（Void）操作の基本動作と、同一取引に対する複数回の取消試行等の防御的振る舞いの検証。 |
| **RP-U-306** | `Discounts & Flags` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_cancelled_flag_exclusion`<br>`test_with_discounts` | 赤黒処理等のためのキャンセル・フラグ指定の除外要件、および割引適用時の集計の正確性。 |
| **RP-U-307** | `Category & Item Reports` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_category_report_format_verification`<br>`test_category_report_operations`<br>`test_category_report_with_date_range`<br>`test_item_report_operations`<br>`test_item_report_with_date_range` | カテゴリ別、商品別のレポート生成時のフォーマット検証、および期間指定時の正確なデータ集約。 |
| **RP-U-308** | `Payment Reports` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_payment_report_basic`<br>`test_payment_report_date_validation`<br>`test_payment_report_error_handling`<br>`test_payment_report_via_api`<br>`test_payment_report_with_date_range` | 決済手段別レポート特有のバリデーション・エラー処理やAPI呼び出し時の振る舞い検証。 |
| **RP-U-309** | `General Scope Reports` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_daily_report_accepts_date_range`<br>`test_flash_report_rejects_date_range_terminal`<br>`test_report_operations`<br>`test_store_report_without_requesting_terminal` | 日次レポート、フラッシュレポート等の期間（Range）指定の可否判断や、特定端末非指定（店舗全体）時の集約検証。 |
| **RP-U-310** | `Multi-Store & Terminal` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_multi_store_mixed_transactions`<br>`test_multi_store_multi_terminal_uniqueness` | 複数店舗および複数端末が混在する中でのトランザクション集計時の一意性と他テナント漏洩防御。 |
| **RP-U-311** | `Journal Messaging` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_send_daily_report_to_journal`<br>`test_send_flash_report_to_journal`<br>`test_unknown_report_scope_skips_journal` | 精算完了時のジャーナル送信機能、および未定義スコープのジャーナルパブリッシュのスキップ検証。 |
| **RP-U-312** | `Health & Base Setup` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_flush_backward_compatibility`<br>`test_health_endpoint`<br>`test_health_endpoint_without_dapr`<br>`test_api_key_request_creates_journal` | Dapr 未接続時のヘルスチェック縮退動作や、API Key認証、DB後方互換性等インフラ基盤の検証。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）による大規模データ集計、および Journal サービスからの Pub/Sub 連携を検証する。

| ID | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **RP-I-001** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_data_integrity` / `test_store_wide_daily_integrity` | 数万件規模・複数端末横断のジャーナルデータに対し、集計結果がタイムアウトせずに正確な総額（Integrity）が証明されること。 |
| **RP-I-002** | `Journal API` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_api_key_journal_integration` / `test_jwt_request_does_not_create_journal` | API Key による通信のみジャーナル履歴として追記され、JWT による単なる参照要求は副作用を起こさないこと。 |
| **RP-I-003** | `Error Handlers` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_journal_error_does_not_fail_report` / `test_payment_report_empty_data` | 一部のジャーナルデータが破損・欠落していてもレポート出力全体がクラッシュせず、取得可能分を正常にフォールバック返却すること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、販売から最終レポート出力までの整合性を検証する。

| ID | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|
| **RP-S-001** | 大規模・複雑ジャーナル集計検証 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 複数店舗・複数端末からのトランザクションを同時投入<br>2. 返品(Return)・取消(Void)を含むデータの集計計算<br>3. 複数税率(複数税区分)が混在するケースのデカルト積(Cartesian product)爆発回避検証 | `test_comprehensive_aggregation` | 複数条件が重なる複雑なジャーナル群に対しても、重複計上や計算エラーを起こさず、正確な全件合計(税込/税抜/税額)が算出されること。 |
| **RP-S-002** | 決済照合・部門別売上フロー | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 複数決済手段での販売ジャーナル投入<br>2. 部門(Category)別・商品(Item)別の集計データ生成<br>3. 決済方法別レポート取得 | `test_payment_report_all` / `test_category_report` | 物理的な現金・キャッシュレス等の決済内訳と、システム上の売上合計額が完全に一致し、各集計軸でのレポートが正しく出力されること。 |
| **RP-S-003** | 重要バグ・エッジケース回帰テスト | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `test_extreme_split_payments` (Issue 78等: 極端な分割支払い)<br>2. `test_split_payment_count_bug` (件数集計バグ)<br>3. 日付境界値のバリデーション | `test_critical_issue_78` / `test_split_payment_bug` | 過去に発生した重大インシデント（内税計算、分割支払い時の集計ミスなど）に特化したシナリオが再発していないことの自動担保。 |

---

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: 大規模なテスト用ジャーナルデータを動的に生成・クレンジングする。

| 関数名 (Helper Function) | 役割 (Responsibility) | 备注 (Notes) |
|:---|:---|:---|
| `log_maker.create_tran_log` | 柔軟な属性を持つ取引ログの自動生成 | テストデータのバリエーション確保 |
| `test_setup_data` | 大規模な履歴データの事前投入 | 集計パフォーマンス検証用 |
| `check_report_data.assert_summary` | 集計結果の共通アサーション | テストコードの簡素化・共通化 |

> [!IMPORTANT]
> Report サービスは 23 のテストファイルを持ち、全サービス中で最もテスト密度が高い主力コンポーネントです。

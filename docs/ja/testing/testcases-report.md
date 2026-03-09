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
| **RP-U-002** | `ReportService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_split_payment_bug` | 複数決済手段（現金＋クレジット等）が併用された際、それぞれの売上が重複なく正確に配分されること。 |
| **RP-U-003** | `ReportService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_discount_rounding_distribution` <br> *(待追加：値引端数処理)* | 合計金額に対する値引が複数商品に案分される際、端数（1円）の調整が特定のルールに基づき正確に行われること。 |

### 1.2 プラグイン管理 (`ReportPluginManager`)

| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **RP-U-101** | `PluginManager` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_plugin_load_failure_handling` <br> *(待追加：プラグインエラー処理)* | 特定のレポートプラグインの読み込みに失敗した場合でも、システム全体が停止せず、他プラグインへ影響を与えないこと。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）による大規模データ集計、および Journal サービスからの Pub/Sub 連携を検証する。

| ID | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **RP-I-001** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_data_integrity` <br> *(# Stress test for data integrity)* | 数万件規模のジャーナルデータに対し、集計結果がタイムアウトせずに正確に算出されること。 |
| **RP-I-002** | `Journal API` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_journal_integration` | Journal サービスからの疑似的な Pub/Sub 通知を受け、Report 側のキャッシュが更新されること。 |

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

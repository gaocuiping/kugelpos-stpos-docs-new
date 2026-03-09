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
| **RP-S-001** | 日次売上分析 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 各種取引（販売/返品/取消）投入<br>2. 日次売上レポート取得<br>3. 部門別内訳の確認 | `test_report` / `test_category_report` | 赤黒処理（返品・取消）が正しく相殺され、純売上額が正確に表示されること。 |
| **RP-S-002** | 決済照合フロー | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 複数決済手段での販売<br>2. 決済方法別レポート取得 | `test_payment_report_all` | 物理的な現金在高と、システム上の決済レポート額が完全に一致すること。 |
| **RP-S-003** | 回帰テスト(Issue 90) | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 内税商品の販売<br>2. レポートでの税額・本体価格確認 | `test_issue_90_internal_tax_not_deducted` | 過去に発生した内税計算ミスが再発していないことの自動担保。 |

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

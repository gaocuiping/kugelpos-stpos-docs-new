---
layout: default
title: Journal サービス テストケース
parent: テスト
nav_order: 103
---

# Journal サービス プロフェッショナルテストケース設計書

本ドキュメントは、Journal サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

## 📊 現在のテストカバレッジ概況

以下の表は、各テスト階層における設計済ケース数と現在の実装状況（スクリプト自動同期結果）を示しています。

| テスト階層 | 総ケース数 | 実装済 (Implemented) | 未実装 (Missing) | カバレッジ (進捗率) |
|:---|:---:|:---:|:---:|:---:|
| **単体テスト (Unit)** | 15 | 13 | 2 | **86.7%** |
| **結合テスト (Integration)** | 2 | 2 | 0 | **100.0%** |
| **シナリオテスト (Scenario)** | 2 | 2 | 0 | **100.0%** |
| **全体合計 (Total)** | **19** | **17** | **2** | **89.5%** |


### 状態 (Status) の定義

| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（Dapr/DB）を Mock し、電文パース、取引種別変換、および検索パラメータ構築ロジックを検証する。

### 1.1 電文処理ロジック (`LogService`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **JN-U-001** | **ログ連携サービスの検証** | `LogService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_process_tranlog_async` / `test_receive_tranlog_with_edge_cases` | 様々な取引種別（Normal, Void, Return）の Tranlog が、共通のジャーナル形式に正確かつ堅牢に（エッジケース含め）変換されること。 |
| **JN-U-002** | **ログ連携サービスの検証** | `LogService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_transaction_type_conversion_parametrized` / `test_normal_sales_cancelled_converts_to_cancel_type` | `kugel_common.enums.TransactionType` と内部保存形式の全マッピングが正しく行われ、特に「取消された通常販売」が負数種別へ反転すること。 |
| **JN-U-003** | **ログ連携サービスの検証** | `LogService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_process_malformed_payload` <br> *(待追加：不正なJSON形式)* | Dapr から不正な形式やフィールド欠落した電文を受信した際、システムがクラッシュせず適切にエラーログを出力すること。 |
| **JN-U-004** | **ログ連携サービスの検証** | `LogService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_event_id_idempotency` <br> *(待追加：イベントの冪等性)* | 同一の `event_id` を持つ電文を複数回受信した場合、DB への重複登録が防止されること。 |
| **JN-U-005** | **ログ連携サービスの検証** | `LogService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_receive_tranlog_transaction_rollback_on_error` | 一部のジャーナル保存プロセスで致命的エラーが発生した場合、中途半端に記録されず全体がロールバックされること。 |
| **JN-U-301** | **取引種別の正負マッピング検証** | `Transaction Type Mapping` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_cancelled_normal_sales_creates_negative_type` (キャンセル通常取引の負数変換)<br>`test_conversion_logic_with_mock_transaction` (モック取引での変換ロジック)<br>`test_non_normal_sales_types_remain_unchanged` (通常外取引の種別保持)<br>`test_normal_sales_not_cancelled_keeps_original_type` (通常取引未取消の種別維持)<br>`test_transaction_type_values` (取引種別の値検査) | 通常売上やキャンセルなど、生データからジャーナル内部種別へのマッピング（正負変換）プロセスの厳密な検証。 |
| **JN-U-302** | **Daprエッジケースペイロード検証** | `Dapr Payload Receive` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_receive_tranlog_normal_sales_cancelled` (取消された通常取引の受信)<br>`test_receive_tranlog_normal_sales_not_cancelled` (未取消の通常取引の受信)<br>`test_receive_tranlog_other_transaction_types_unchanged` (その他取引種別での受信) | パイプライン経由で受信した様々な状態の Transaction ログがシステムに適切に分類されること。 |
| **JN-U-303** | **健全性とスコープの検証** | `Health & Scopes` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_health_endpoint` (ヘルスチェック経由)<br>`test_health_endpoint_without_dapr` (Dapr無しのヘルスチェック)<br>`test_report_operations` (報告生成挙動) | マイクロサービスのエンドポイント健全性と、Dapr 切断時のグレースフルな振る舞い検証。 |
| **JN-A-REC** | **Create a new journal entry.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `receive_journals` | システムが自動追加したAPIインターフェーステスト |
| **JN-A-GET** | **Retrieve journal entries with various filtering options.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_journals` | システムが自動追加したAPIインターフェーステスト |
| **JN-A-HAN** | **Handle transaction logs received via Dapr pub/sub.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `handle_tranlog` | システムが自動追加したAPIインターフェーステスト |
| **JN-A-HAN** | **Handle cash in/out logs received via Dapr pub/sub.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `handle_cashlog` | システムが自動追加したAPIインターフェーステスト |
| **JN-A-HAN** | **Handle terminal open/close logs received via Dapr pub/sub.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `handle_opencloselog` | システムが自動追加したAPIインターフェーステスト |
| **JN-A-REC** | **Direct API endpoint for receiving transaction data.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `receive_transactions` | システムが自動追加したAPIインターフェーステスト |
| **JN-A-CRE** | **Setup the database for the tenant. This will create the required collections and indexes.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_tenant` | システムが自動追加したAPIインターフェーステスト |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）への永続化、および Dapr Pub/Sub のサブスクリプション連携を検証する。

| ID | テストタイトル | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **JN-I-001** | **MongoDBデータ永続化検証** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_journal_search` <br> *(# Test journal search with filters)* | 保存されたジャーナルデータが、複合インデックス（日付/店舗/端末）を用いて正確に抽出できること。 |
| **JN-I-002** | **Dapr Pub/Subイベント検証** | `Dapr PubSub` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_health_check` / `dapr/subscribe` | 各種トピック（tranlog, cashlog, opencloselog）の購読設定が正常に構成されていること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、ジャーナルの収集から照会までのフローをエンドツーエンドで検証する。

| ID | テストタイトル | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|:---|
| **JN-S-001** | **ジャーナル収集・照会の検証** | ジャーナル収集・照会 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `POST /api/v1/tranlog` (疑似) <br>2. `GET /api/v1/journals` | `test_journal.py` | 送信した取引データが遅滞なくジャーナル一覧に反映され、詳細が一致すること。 |
| **JN-S-002** | **ページネーション検証の検証** | ページネーション検証 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 大量ログ投入 <br>2. `limit/page` 指定での取得 | `test_journal_pagination` | ページ境界（Offset）のデータ欠落がなく、メタデータの `total` が正確であること。 |

---

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: テスト環境のセットアップおよび共通クレンジングを共通化する。

| 関数名 (Helper Function) | 役割 (Responsibility) | 備考 (Notes) |
|:---|:---|:---|
| `test_setup_data` | テスト用ジャーナル（過去分含む）の投入 | 検索・集計テスト用のデータ準備 |
| `test_clean_data` | 全ジャーナルログの物理削除 | 冪等性確保のための後処理 |
| `conftest.http_client` | FastAPI AsyncClient 提供 | 非同期通信テストの基底 |

> [!NOTE]
> Journal サービスは「データの正確性」が生命線であるため、Unit テストでの電文パース網羅率が 85% 達成の鍵となります。

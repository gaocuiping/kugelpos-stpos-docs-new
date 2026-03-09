---
layout: default
title: Journal サービス テストケース
parent: テスト
nav_order: 103
---

# Journal サービス プロフェッショナルテストケース設計書

本ドキュメントは、Journal サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

### 状態 (Status) の定義
| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（Dapr/DB）を Mock し、電文パース、取引種別変換、および検索パラメータ構築ロジックを検証する。

### 1.1 電文処理ロジック (`LogService`)
| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **JN-U-001** | `LogService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_process_tranlog_async` <br> *(# Normal transaction logs)* | 様々な取引種別（Normal, Void, Return）の Tranlog が、共通のジャーナル形式に正確に変換・パースされること。 |
| **JN-U-002** | `LogService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_transaction_type_conversion` | `kugel_common.enums.TransactionType` と内部保存形式の全マッピングが正しく行われること。 |
| **JN-U-003** | `LogService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_process_malformed_payload` <br> *(待追加：不正なJSON形式)* | Dapr から不正な形式やフィールド欠落した電文を受信した際、システムがクラッシュせず適切にエラーログを出力すること。 |
| **JN-U-004** | `LogService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_event_id_idempotency` <br> *(待追加：イベントの冪等性)* | 同一の `event_id` を持つ電文を複数回受信した場合、DB への重複登録が防止されること。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）への永続化、および Dapr Pub/Sub のサブスクリプション連携を検証する。

| ID | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **JN-I-001** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_journal_search` <br> *(# Test journal search with filters)* | 保存されたジャーナルデータが、複合インデックス（日付/店舗/端末）を用いて正確に抽出できること。 |
| **JN-I-002** | `Dapr PubSub` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_health_check` / `dapr/subscribe` | 各種トピック（tranlog, cashlog, opencloselog）の購読設定が正常に構成されていること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、ジャーナルの収集から照会までのフローをエンドツーエンドで検証する。

| ID | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|
| **JN-S-001** | ジャーナル収集・照会 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `POST /api/v1/tranlog` (疑似) <br>2. `GET /api/v1/journals` | `test_journal.py` | 送信した取引データが遅滞なくジャーナル一覧に反映され、詳細が一致すること。 |
| **JN-S-002** | ページネーション検証 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 大量ログ投入 <br>2. `limit/page` 指定での取得 | `test_journal_pagination` | ページ境界（Offset）のデータ欠落がなく、メタデータの `total` が正確であること。 |

---

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: テスト環境のセットアップおよび共通クレンジングを共通化する。

| 関数名 (Helper Function) | 役割 (Responsibility) | 备注 (Notes) |
|:---|:---|:---|
| `test_setup_data` | テスト用ジャーナル（過去分含む）の投入 | 検索・集計テスト用のデータ準備 |
| `test_clean_data` | 全ジャーナルログの物理削除 | 冪等性確保のための後処理 |
| `conftest.http_client` | FastAPI AsyncClient 提供 | 非同期通信テストの基底 |

> [!NOTE]
> Journal サービスは「データの正確性」が生命線であるため、Unit テストでの電文パース網羅率が 85% 達成の鍵となります。

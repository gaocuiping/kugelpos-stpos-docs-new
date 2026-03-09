# Stock サービス プロフェッショナルテストケース設計書

本ドキュメントは、Stock サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

### 状態 (Status) の定義
| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB/WebSocket）を Mock し、在庫計算、トランザクションマッピング、およびアラート判定ロジックを検証する。

### 1.1 在庫計算ロジック (`StockService`)
| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **SK-U-001** | `StockService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_negative_stock_allowed` <br> *(# Test that negative stock is allowed)* | 在庫が 0 未満になる更新でもエラーにならず、負の値として正しく保存・履歴記録されること。 |
| **SK-U-002** | `StockService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_update_stock_zero_change` <br> *(待追加：変化量ゼロの更新処理)* | 変化量が 0 の場合、在庫数は更新されず、履歴のみが記録される（またはスキップされる）仕様通りの動作。 |
| **SK-U-003** | `StockService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_process_transaction_with_cancelled_items` <br> *(待追加：キャンセル行のフィルタリング)* | 取引データ内に `is_cancelled: true` の行が含まれる場合、その行の在庫減算がスキップされること。 |

### 1.2 アラート判定 (`AlertService`)
| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **SK-U-101** | `AlertService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_alert_threshold_boundary` <br> *(待追加：閾値境界値検証)* | 在庫が `minimum_quantity` と「ちょうど同値」になった際のアラート発火有無が仕様通りであること。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）、Dapr Pub/Sub 連携、およびスケジューラーの動作を検証する。

| ID | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **SK-I-001** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_update_stock` <br> *(# Test updating stock quantity)* | `update_quantity_atomic_async` により、アトミックな増減が DB レベルで保証されること。 |
| **SK-I-002** | `Dapr PubSub` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_dapr_subscribe` <br> *(# Test Dapr subscription endpoint)* | `topic-tranlog` に対するサブスクリプション設定が正しく公開されていること。 |
| **SK-I-003** | `Scheduler` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_snapshot_scheduler` <br> *(# Test snapshot scheduler)* | 設定されたスケジュールに基づき、在庫スナップショットが自動生成されること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、在庫のライフサイクルをエンドツーエンドで検証する。

| ID | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|
| **SK-S-001** | 基本在庫運用 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 在庫取得<br>2. 購入(入庫)による在庫増<br>3. 履歴の確認 | `test_get_stock` / `test_update_stock` | 実行前後の数量差分が正確に計算・記録されていること。 |
| **SK-S-002** | 棚卸スナップショット | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 在庫調整<br>2. 手動スナップショット作成<br>3. 日付範囲指定で取得 | `test_create_snapshot` / `test_snapshot_date_range` | 特定時点の全商品在庫が静止点として保存・検索できること。 |
| **SK-S-003** | リアルタイム告警 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. WebSocket接続<br>2. 在庫を閾値以下に減らすご更新<br>3. アラート受信確認 | `test_websocket_alerts` | 下限割れを検知し、WebSocket 経由で即座にクライアントへ通知されること。 |

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

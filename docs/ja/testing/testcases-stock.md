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

| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **SK-U-001** | `StockService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_negative_stock_allowed` <br> *(# Test that negative stock is allowed)* | 在庫が 0 未満になる更新でもエラーにならず、負の値として正しく保存・履歴記録されること。 |
| **SK-U-002** | `StockService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_update_stock_zero_change` <br> *(待追加：変化量ゼロの更新処理)* | 変化量が 0 の場合、在庫数は更新されず、履歴のみが記録される（またはスキップされる）仕様通りの動作。 |
| **SK-U-003** | `StockService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_process_transaction_with_cancelled_items` <br> *(待追加：キャンセル行のフィルタリング)* | 取引データ内に `is_cancelled: true` の行が含まれる場合、その行の在庫減算がスキップされること。 |
| **SK-U-004** | `StockService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_get_store_stocks` / `test_get_target_stores_all` | 特定エンドポイントまたは全店舗跨ぎでの在庫照会結果が、ロールとテナント権限の範囲内で抽出可能であること。 |

### 1.2 アラート判定 (`AlertService`)

| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **SK-U-101** | `AlertService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_alert_threshold_boundary` <br> *(待追加：閾値境界値検証)* | 在庫が `minimum_quantity` と「ちょうど同値」になった際のアラート発火有無が仕様通りであること。 |
| **SK-U-102** | `WebSocket` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_websocket_multiple_clients` / `test_websocket_unauthorized_connection` | セッション並行処理によるブロードキャストと、不正なアクセスに対するハンドシェイク遮断処理の堅牢性。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）、Dapr Pub/Sub 連携、およびスケジューラーの動作を検証する。

| ID | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **SK-I-001** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_update_stock` / `test_get_snapshots_pagination` | `update_quantity_atomic_async` による DB レベルのアトミック減算、および大量 Snapshot 履歴のページネーション取得。 |
| **SK-I-002** | `Dapr PubSub` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_dapr_subscribe` <br> *(# Test Dapr subscription endpoint)* | `topic-tranlog` に対するサブスクリプション設定が正しく公開されていること。 |
| **SK-I-003** | `Scheduler` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_snapshot_scheduler` / `test_create_cron_trigger...` / `test_update_snapshot_schedule...` | 手動起動に加え、Daily/Weekly/Monthly 等の Cron 式の登録、削除、無効化などのスケジューリング全容が機能すること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、在庫のライフサイクルをエンドツーエンドで検証する。

| ID | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|
| **SK-S-001** | 基本在庫運用と履歴管理 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. **初期取得**: `GET` 要求による現行在庫の確認<br>2. **アトミック更新**: 増減量(Quantity)を指定した `PUT` 更新<br>3. **履歴検証**: `History` コレクションに更新前後の差分と理由が正しく追記されること | `test_stock` | 単純な上書きではなく、アトミックな増減計算により並行処理時も在庫数が正確に保たれること。 |
| **SK-S-002** | 棚卸スナップショット・スケジュール | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 定期実行 API または Scheduler 経由での Snapshot 生成起動<br>2. `Snapshot` 履歴の取得検証<br>3. 日付範囲パラメータ (`start_date`, `end_date`) を用いた検索 | `test_snapshot_date_range` / `test_snapshot_scheduler` | 月次・日次などの指定時点で、全商品の在庫数が静止点（スナップショット）として確実に保管され、後から期間指定で検索できること。 |
| **SK-S-003** | リアルタイム発注警告 (WebSocket) | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. クライアントが WebSocket エンドポイントに接続<br>2. 別の API 経由で対象商品の在庫数を「発注点 (Reorder Level)」以下に減算<br>3. クライアント側でリアルタイムに JSON Alert を受信 | `test_websocket_alerts` / `test_reorder_alerts` | 下限割れ（発注点割れ）を検知した直後に、プッシュ型通信で接続中のPOSや管理画面へ即座に通知が届くこと。 |

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

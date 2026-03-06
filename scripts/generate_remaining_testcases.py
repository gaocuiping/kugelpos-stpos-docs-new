import os

base = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs"

testcases = {
    'terminal': {
        'ja': """---
title: "Terminal サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 12
layout: default
---

# Terminal サービス テスト設計書

本ドキュメントは、各レジ端末の起動や設定を管理する Terminal サービスの詳細なテストケースです。
端末登録の競合排除と稼働状況の監視（ハートビート）を重点的に検証します。

## 1. サービスの概要とテスト戦略

**前提条件・テストデータ**:
- **DB**: MongoDB `terminals` コレクション、`stores` コレクション
- **キャッシュ**: Dapr StateStore (Redis) を活用したハートビート管理

---

## 2. ユニットテスト (API・ロジック単位)

### 2.1 ターミナル登録・管理 (Terminal CRUD)

| ID | ターゲットAPI | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **TM-U-010** | `POST /terminals` | 未登録のMACアドレスと店舗IDで新規登録 | `201 Created`、DBに設定初期値が保存されること | ❌ 推奨 |
| **TM-U-011** | `POST /terminals` | 既に他店舗に登録済みのMACアドレスで登録試行 | `409 Conflict`、二重登録がブロックされること | ❌ 推奨 |
| **TM-U-012** | `GET /terminals/{id}` | 存在するターミナルIDでの設定取得 | `200 OK`、ターミナル設定（決済端末IP等）が返却されること | ❌ 推奨 |
| **TM-U-013** | `PUT /terminals/{id}` | ターミナルの機器設定（プリンタIP等）の更新 | `200 OK`、DBが更新され、変更内容が反映されること | ❌ 推奨 |

### 2.2 稼働監視・ハートビート (Heartbeat monitoring)

| ID | ターゲットAPI | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **TM-U-020** | `POST /heartbeat` | 稼働中のターミナルから定周期で送信 | `200 OK`、Redis上の `last_active_at` が更新されること | ❌ 推奨 |
| **TM-U-021** | `GET /status` | 管理画面等からの端末ステータス一覧取得 | 最後にハートビートを受信した時間から、稼働/オフラインを正確に判定して返すこと | ❌ 推奨 |
""",
        'en': """---
title: "Terminal Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 12
layout: default
---

# Terminal Service Test Specification

This document details the test cases for the Terminal service, which manages the startup and configuration of POS registers.
Key areas include preventing terminal registration conflicts and monitoring operational status (heartbeat).

## 1. Overview and Test Strategy

**Prerequisites & Test Data**:
- **DB**: MongoDB `terminals` and `stores` collections
- **Cache**: Heartbeat management utilizing Dapr StateStore (Redis)

---

## 2. Unit Tests (API & Logic)

### 2.1 Terminal Registration & Management (Terminal CRUD)

| ID | Target API | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|------------|---------------------------|------------------|--------|
| **TM-U-010** | `POST /terminals` | New registration with unregistered MAC and Store ID | `201 Created`, initial settings saved to DB | ❌ Recommended |
| **TM-U-011** | `POST /terminals` | Registration attempt with MAC already bound to another store | `409 Conflict`, double registration blocked | ❌ Recommended |
| **TM-U-012** | `GET /terminals/{id}` | Fetch configuration for existing terminal ID | `200 OK`, configuration returned | ❌ Recommended |
| **TM-U-013** | `PUT /terminals/{id}` | Update terminal device settings | `200 OK`, DB updated and changes reflected | ❌ Recommended |

### 2.2 Heartbeat Monitoring

| ID | Target API | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|------------|---------------------------|------------------|--------|
| **TM-U-020** | `POST /heartbeat` | Periodic transmission from active terminal | `200 OK`, `last_active_at` updated in Redis | ❌ Recommended |
| **TM-U-021** | `GET /status` | Fetching terminal statuses from admin panel | Accurately returns Online/Offline based on last heartbeat | ❌ Recommended |
"""
    },
    'master-data': {
        'ja': """---
title: "Master Data サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 13
layout: default
---

# Master Data サービス テスト設計書

マスターデータの整合性と、他サービス（特にCart）への高速提供（キャッシュ）を中心に検証します。

## 1. サービスの概要とテスト戦略

商品の価格・税・カテゴリ・支払方法など、トランザクションの基盤となる静的データを管理します。
マスター更新時の**キャッシュ無効化（Invalidation）**が最大のテストポイントになります。

---

## 2. ユニットテスト (API・ロジック単位)

### 2.1 商品マスター (Item Master)

| ID | ターゲットAPI | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **MD-U-010** | `GET /items/{jan}` |  存在するJANコードでの商品検索 | `200 OK`、単価・税区分・部門情報が正しく返却されること | ❌ 推奨 |
| **MD-U-011** | `GET /items/{jan}` | 無効なJANコード、または削除済みの商品 | `404 Not Found` が返却されること | ❌ 推奨 |
| **MD-U-012** | `PUT /items/{jan}` | 商品の価格改定（単価の更新） | DB更新後、Dapr StateStore上のキャッシュエントリーが削除（無効化）されること | ❌ 推奨 |

### 2.2 税率・支払方法 (Tax & Payment Master)

| ID | ターゲットモジュール | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|------------------|--------------------------------|--------------|------|
| **MD-U-020** | `GET /taxes` | 現在有効な消費税率（標準、軽減等）一覧取得 | `200 OK`、有効期間内の税情報のみが返却されること | ❌ 推奨 |
| **MD-U-021** | `GET /payments` | 利用可能な支払方法（現金、クレカ、QR）一覧 | `200 OK`、店舗設定に基づく有効な支払方法が返ること | ❌ 推奨 |

## 3. エンドツーエンド・システム間シナリオ

| ID | シナリオフロー (Cache Invalidation Scenario) | 期待される結果とアサーション | 状態 |
|----|--------------------------------------------|--------------------------|------|
| **MD-S-001** | **マスター即時反映フロー** <br>1. MasterDataで商品Aを100円→120円に更新<br>2. Cartサービスで商品Aをスキャン | MasterData更新のPub/SubイベントによってCart側のキャッシュが破棄され、120円としてスキャンされること | ❌ 推奨 |
""",
        'en': """---
title: "Master Data Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 13
layout: default
---

# Master Data Service Test Specification

Focuses on master data integrity and rapid provisioning (caching) to other services (especially Cart).

## 1. Overview and Test Strategy

Manages static data fundamental to transactions: item prices, taxes, categories, and payment methods.
The most critical test point is **cache invalidation** upon master data updates.

---

## 2. Unit Tests (API & Logic)

### 2.1 Item Master

| ID | Target API | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|------------|---------------------------|------------------|--------|
| **MD-U-010** | `GET /items/{jan}` | Item lookup with existing JAN code | `200 OK`, correct price, tax class, and department returned | ❌ Recommended |
| **MD-U-011** | `GET /items/{jan}` | Invalid JAN code or deleted item | `404 Not Found` returned | ❌ Recommended |
| **MD-U-012** | `PUT /items/{jan}` | Item price revision (unit price update) | After DB update, cache entry in Dapr StateStore is deleted (invalidated) | ❌ Recommended |

### 2.2 Tax & Payment Master

| ID | Target Module | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|---------------|---------------------------|------------------|--------|
| **MD-U-020** | `GET /taxes` | Fetch list of currently valid tax rates (standard, reduced) | `200 OK`, returns only tax info within valid date ranges | ❌ Recommended |
| **MD-U-021** | `GET /payments` | Fetch available payment methods (Cash, CC, QR) | `200 OK`, returns valid payment methods based on store config | ❌ Recommended |

## 3. End-to-End Inter-System Scenarios

| ID | Scenario Flow (Cache Invalidation) | Expected Result & Assertions | Status |
|----|----------------------------------|------------------------------|--------|
| **MD-S-001** | **Immediate Master Reflection Flow** <br>1. Update Item A from 100 to 120 yen in MasterData<br>2. Scan Item A in Cart service | Cart cache is invalidated by MasterData update Pub/Sub event, scanned as 120 yen | ❌ Recommended |
"""
    },
    'report': {
        'ja': """---
title: "Report サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 15
layout: default
---

# Report サービス テスト設計書

複雑な集計ロジックと直積（Cartesian product）バグの防止を目的としたテスト仕様です。

## 1. サービスの概要とテスト戦略

各決済の履歴（Journal）を集計し、精算・売上レポートを生成します。
既に計算ロジックに対する非常に高いカバレッジを持ちます。継続的な整合性の監視が必要です。

---

## 2. ユニットテスト (API・ロジック単位)

### 2.1 集計ロジックの正確性 (Aggregation Engine)

| ID | ターゲット分析 | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **RP-U-010** | `Category Report` | 期間内の部門（カテゴリ）別売上の集計 | キャンセルされた取引（Cancelフラグ=True）が正確に除外されて集計されること | ✅ 実装済 |
| **RP-U-011** | `Item Report` | 特定商品の期間内販売点数・金額集計 | 返品取引（Return）のマイナス分が正しく加味され、純売上が算出されること | ✅ 実装済 |
| **RP-U-012** | `Payment Report`| 個別会計（スプリットペイメント：現金+クレカ等） | 決済手段ごとの金額が二重計上されずに按分・集計されること | ✅ 実装済 |

### 2.2 データ整合性とエッジケース (Data Integrity & Edge Cases)

| ID | リスク領域 | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|----------|--------------------------------|--------------|------|
| **RP-U-020** | 整合性 | 1日の全取引の内、「総支払額 == 総売上額 + 全税金」の計算 | 式が例外なく常にTrueとなること | ✅ 実装済 |
| **RP-U-021** | 直積によるバグ | 1スリップに【商品A(10%税)・商品B(8%税)】×【3人での分割払い】の取引 | SQLのJOIN等による直積バグが発生せず、実質額だけが集計されること | ✅ 実装済 |
| **RP-U-022** | 丸め誤差 | 内税商品の割り戻し計算時における1円以下の小数の丸め | 法定の丸め規則（切り捨て等）に基づき、数円の誤差が発生しないこと | ✅ 実装済 |

## 3. インテグレーションテスト (統合検証)

| ID | コンポーネント連携 | テストシナリオ | 確認ポイント | 状態 |
|----|-----------------|--------------|------------|------|
| **RP-I-001** | Report → Journal | Z精算（日次締め）実行時のジャーナルへのレポート送信 | 発行された精算レポートが、Dapr Pub/Sub 経由で電子ジャーナルに確実に取り込まれること | ❌ 推奨 |
""",
        'en': """---
title: "Report Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 15
layout: default
---

# Report Service Test Specification

Test specifications aimed at complex aggregation logic and preventing Cartesian product bugs.

## 1. Overview and Test Strategy

Aggregates payment histories (Journal) to generate settlement and sales reports.
Already possesses extremely high coverage for calculation logic. Continuous monitoring of integrity is required.

---

## 2. Unit Tests (API & Logic)

### 2.1 Aggregation Engine Accuracy

| ID | Target Analysis | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|-----------------|---------------------------|------------------|--------|
| **RP-U-010** | `Category Report` | Aggregate sales by department (category) over period | Cancelled transactions accurately excluded from aggregation | ✅ Implemented |
| **RP-U-011** | `Item Report` | Aggregate sales quantity/amount for specific items | Negative amounts from return transactions correctly factored | ✅ Implemented |
| **RP-U-012** | `Payment Report`| Split payments (e.g., Cash + CC) | Amounts per payment method correctly prorated without double counting | ✅ Implemented |

### 2.2 Data Integrity & Edge Cases

| ID | Risk Area | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|-----------|---------------------------|------------------|--------|
| **RP-U-020** | Integrity | Calculate "Total Payments == Total Sales + Total Tax" | The equation is always True without exception | ✅ Implemented |
| **RP-U-021** | Cartesian Bug | Slip with [Item A & Item B] × [3-way split payment] | No Cartesian product bug from SQL joins; only actual amounts aggregated | ✅ Implemented |
| **RP-U-022** | Rounding Error | Sub-yen rounding when calculating internal tax kickbacks | No multi-yen discrepancies based on legal rounding rules | ✅ Implemented |

## 3. Integration Tests

| ID | Component Integration | Scenario | Check Point | Status |
|----|-----------------------|----------|-------------|--------|
| **RP-I-001** | Report → Journal | Sending report to Journal upon Z-closing | Issued settlement report reliably ingested into E-Journal via Dapr Pub/Sub | ❌ Recommended |
"""
    },
    'journal': {
        'ja': """---
title: "Journal サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 16
layout: default
---

# Journal サービス テスト設計書

法的な要件を伴う「電子ジャーナル」の永続化と検索性能の担保を目的とします。

## 1. サービスの概要とテスト戦略

Cartからの決済完了イベント、および Reportからの精算イベントを受け取り、変更不可（Immutable）のログとして保存します。
データの欠損防止（メッセージロスト対策）と、高速な全文/条件検索のテストが主体となります。

---

## 2. ユニットテスト (ログ受信と変換)

| ID | ターゲット処理 | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **JN-U-010** | `Transaction Type` | Normal Sales（通常売上）ログの解釈と保存 | ステータスが正確にマッピングされ、ジャーナルDBに保存されること | ✅ 実装済 |
| **JN-U-011** | `Transaction Type` | Cancelled（直前取消）売上ログの受信 | 内部でキャンセル扱い（マイナス取引）にトランスフォームされて保存されること | ✅ 実装済 |
| **JN-U-012** | `Search API` | 日付（Date Range）とターミナルIDでの検索パラメータ | 条件に合致するログだけが、正しいページネーション設定で返却されること | ❌ 推奨 |
| **JN-U-013** | `Search API` | 対象期間内にデータが1件も存在しない場合の検索 | 空のリストと総ページ数0が、ステータス `200 OK` で返されること | ❌ 推奨 |

## 3. インテグレーションテスト (非同期処理・メッセージング)

| ID | コンポーネント・フロー | テストシナリオ | 確認ポイント | 状態 |
|----|-------------------|--------------|------------|------|
| **JN-I-001** | Pub/Sub 耐障害性 | メッセージ受信スレッド処理中にDB接続がロストした場合 | DBエラー時はトランザクションがロールバックされ、Dapr側で再送(Retry)が行われること | ✅ 実装済 |
| **JN-I-002** | Elasticsearch連携 | ジャーナルのRDBMS保存後、全文検索エンジンへの同期 | 取引明細内の商品名テキストフリーワード検索で結果がヒットすること | ❌ 推奨 |
""",
        'en': """---
title: "Journal Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 16
layout: default
---

# Journal Service Test Specification

Aims to guarantee the persistence and search performance of "Electronic Journals" which carry legal requirements.

## 1. Overview and Test Strategy

Receives transaction completion events from Cart and settlement events from Report, saving them as immutable logs.
Tests focus primarily on preventing data loss (message lost countermeasures) and high-speed full-text/conditional search.

---

## 2. Unit Tests (Log Reception & Conversion)

| ID | Target Process | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|----------------|---------------------------|------------------|--------|
| **JN-U-010** | `Transaction Type` | Interpretation and saving of Normal Sales log | Status accurately mapped and saved to Journal DB | ✅ Implemented |
| **JN-U-011** | `Transaction Type` | Reception of Cancelled (immediate void) sales log | Transformed internally as a cancellation (negative transaction) and saved | ✅ Implemented |
| **JN-U-012** | `Search API` | Search parameters by Date Range and Terminal ID | Only matching logs returned with correct pagination | ❌ Recommended |
| **JN-U-013** | `Search API` | Search when no data exists within target period | Empty list and total pages 0 returned with `200 OK` | ❌ Recommended |

## 3. Integration Tests (Async & Messaging)

| ID | Component Flow | Scenario | Check Point | Status |
|----|----------------|----------|-------------|--------|
| **JN-I-001** | Pub/Sub Fault Tolerance | DB connection lost during message receiving thread | Transaction rolled back on DB error, Dapr performs retry | ✅ Implemented |
| **JN-I-002** | Elasticsearch Sync | Syncing to full-text search engine after saving journal to RDBMS | Free-word text search within transaction details returns hits | ❌ Recommended |
"""
    },
    'stock': {
        'ja': """---
title: "Stock サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 17
layout: default
---

# Stock サービス テスト設計書

在庫のリアルタイム引き当てと、発注アラートの非同期的Websocket通知を中心に検証します。

## 1. サービスの概要とテスト戦略

Cart（購入）や管理画面（入庫）からの在庫増減を正確に管理します。
同時に、適正在庫を下回った際にフロントエンドへリアルタイムでアラート（WebSocket）を飛ばす挙動のテストが重要です。

---

## 2. ユニットテスト (API・ロジック単位)

### 2.1 在庫増減・排他制御 (Stock Adjustment)

| ID | ターゲットAPI | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|-------------|--------------------------------|--------------|------|
| **SK-U-010** | `GET /stock/{item}` | 複数倉庫・店舗をまたいだ商品の在庫一覧取得 | 各ロケーションの在庫数が配列で返却されること | ✅ 実装済 |
| **SK-U-011** | `POST /stock/adjust`| 販売によるマイナス調整処理 | 在庫数が減算され、ストック履歴（ヒストリーログ）が追記されること | ✅ 実装済 |
| **SK-U-012** | `Logic` | マイナス在庫許可フラグ（Negative Stock Allowed）の検証 | フラグOFF時に在庫が0を下回る引当を行うと、例外(400)が発生し在庫移動がブロックされること | ✅ 実装済 |
| **SK-U-013** | `Concurrency` | 同一商品に対する並行する2件の引当リクエスト（競合状態） | アトミック操作（楽観的ロック等）により、在庫数が正確に加減算されること | ❌ 推奨 |

### 2.2 アラートとWebSocket通知 (Alerts & WebSocket)

| ID | ターゲットフロー | テストシナリオ (Before/When/Then) | 期待される結果 | 状態 |
|----|--------------|--------------------------------|--------------|------|
| **SK-U-020** | `Reorder Logic` | 在庫減算後、在庫数が「発注点」を下回った場合 | Database上のReorder AlertフラグがTrueに更新されること | ✅ 実装済 |
| **SK-U-021** | `WebSocket` | WebSocketクライアントを接続した状態で、アラート条件を満たす在庫減算を実行 | 接続中のクライアントに、Json形式のアラートメッセージが即時Pushされること | ✅ 実装済 |
| **SK-U-022** | `WebSocket` | 認証トークンを持たない未承認クライアントの WebSocket 接続試行 | 接続が拒否（Close/401）されること | ✅ 実装済 |

## 3. インテグレーション・スケジュールテスト

| ID | コンポーネント連携 | テストシナリオ | 確認ポイント | 状態 |
|----|-----------------|--------------|------------|------|
| **SK-I-001** | `CRON Scheduler` | Dapr Chronバインディングを用いた月末の「在庫スナップショット」自動生成処理 | 指定日時にスケジュールトリガーが発火し、全商品の在庫数が履歴テーブルにコピーされること | ✅ 実装済 |
""",
        'en': """---
title: "Stock Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 17
layout: default
---

# Stock Service Test Specification

Focuses on real-time inventory allocation and asynchronous WebSocket notifications for reorder alerts.

## 1. Overview and Test Strategy

Accurately manages inventory increments/decrements from Cart (purchases) and Admin Panel (receiving).
Crucially, tests behavior of real-time alerts (WebSocket) pushed to the frontend when inventory falls below appropriate levels.

---

## 2. Unit Tests (API & Logic)

### 2.1 Stock Adjustment & Concurrency Control

| ID | Target API | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|------------|---------------------------|------------------|--------|
| **SK-U-010** | `GET /stock/{item}` | Stock list retrieval across multiple warehouses/stores | Stock quantity for each location returned as array | ✅ Implemented |
| **SK-U-011** | `POST /stock/adjust`| Minus adjustment processing due to sales | Stock count decreased, stock history log appended | ✅ Implemented |
| **SK-U-012** | `Logic` | Negative Stock Allowed flag verification | If OFF, allocations dropping stock below 0 raise exception (400) and are blocked | ✅ Implemented |
| **SK-U-013** | `Concurrency` | Two concurrent allocation requests for same item (race condition) | Stock accurately adjusted via atomic operations | ❌ Recommended |

### 2.2 Alerts & WebSocket Notifications

| ID | Target Flow | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|-------------|---------------------------|------------------|--------|
| **SK-U-020** | `Reorder Logic` | Stock drops below "reorder point" after deduction | Reorder Alert flag on Database updated to True | ✅ Implemented |
| **SK-U-021** | `WebSocket` | Execute alert-triggering deduction while WS client connected | Alert message in JSON format pushed immediately to connected client | ✅ Implemented |
| **SK-U-022** | `WebSocket` | WebSocket connection attempt from unauthorized client without token | Connection rejected (Close/401) | ✅ Implemented |

## 3. Integration & Scheduled Tests

| ID | Component Integration | Scenario | Check Point | Status |
|----|-----------------------|----------|-------------|--------|
| **SK-I-001** | `CRON Scheduler` | Auto-generation of end-of-month "Inventory Snapshot" via Dapr CRON binding | Schedule trigger fires at designated time, stock counts copied to history table | ✅ Implemented |
"""
    }
}

for svc, langs in testcases.items():
    for lang, content in langs.items():
        dst = os.path.join(base, lang, 'testing', f'testcases-{svc}.md')
        with open(dst, 'w') as f:
            f.write(content)

print("Generated enhanced test case templates for remaining services!")

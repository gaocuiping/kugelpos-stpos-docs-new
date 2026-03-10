import os

base = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs"

# 1. Review Document Content (Markdown)
ja_review = """---
title: "テストケース設計 評価・改善報告"
parent: テスト
grand_parent: 日本語
nav_order: 18
layout: default
---

# テストケース設計 評価・改善報告 (Test Case Design Review)

各マイクロサービスのテストケース設計に対するレビュー結果と、不足していた観点（エッジケース、異常系、非機能要件）の分析報告です。

## 1. 評価サマリー

初期のテストケース群は、正常系のビジネスロジック（Happy Path）や基本的なエラー制御において高い網羅性を持っていました。
しかし、**極端な負荷（パフォーマンス）**、**分散システム特有の障害（ネットワーク分断）**、**悪意のある入力（セキュリティ）** に対するテストが不足していることが判明しました。

## 2. サービス別の不足点と改善方針

各サービスにおける具体的な課題と、追加すべき要件を定義します。

### 2.1 Account サービス
- **現状の評価**: 認証フローやテナント管理はカバーされている。
- **不足している観点**:
  - 【セキュリティ】ブルートフォース攻撃（総当たり攻撃）対策としての Rate Limiting（レート制限）の検証。
  - 【セキュリティ】JWT リプレイ攻撃の防止テスト。

### 2.2 Terminal サービス
- **現状の評価**: DBとRedisを用いたCRUD・ハートビート基本動作は良好。
- **不足している観点**:
  - 【障害耐性】Dapr StateStore (Redis) がダウンした際のフォールバック挙動。
  - 【エッジケース】複数端末から**ミリ秒単位**で同時に同じ店舗へアクセスした場合の競合状態。

### 2.3 Master Data サービス
- **現状の評価**: キャッシュ無効化(Invalidation)のアプローチは適切。
- **不足している観点**:
  - 【パフォーマンス】本番環境相当のデータ（商品 100,000 件）を一括同期・キャッシュ更新する際の処理時間とメモリリークの検証。
  - 【異常系】キャッシュのみ更新され、DB更新が失敗する「スプリットブレイン」状態の防止。

### 2.4 Cart サービス（最重要）
- **現状の評価**: 複雑な税計算・割引・二重送信防止に対する強力なカバレッジあり。
- **不足している観点**:
  - 【境界値】買い物かごへの商品追加上限（例えば 9999個、あるいは合計金額が 1億円を超えるオーバーフロー）のテスト。
  - 【非機能/状態管理】決済フローの途中でブラウザや端末の電源が落ち、**数日間放置されたカートセッション**の破棄検証。

### 2.5 Report サービス
- **現状の評価**: 直積バグ（Cartesian product）回避や複雑な集計は完璧。
- **不足している観点**:
  - 【エッジケース】レジのタイムゾーン（例: UTC から JST）を跨ぐ深夜24時付近のトランザクションが、どちらの「日」に集計されるかの境界検証。
  - 【境界値】閏年（2月29日）の月次レポート集計テスト。

### 2.6 Journal サービス
- **現状の評価**: トランザクションタイプの変換は適切に定義されている。
- **不足している観点**:
  - 【性能・ペネトレーション】検索 API に `limit=10,000,000` のような巨大なページネーションを要求された際の DB 死守（防御的プログラミング）のテスト。
  - 【異常系】極端に巨大な JSON ペイロード（数MBのレシートデータ）を受信したときの処理。

### 2.7 Stock サービス
- **現状の評価**: 在庫増減と WebSocket 通知の連携は素晴らしい。
- **不足している観点**:
  - 【耐障害性】WebSocket サーバー（Stock）とクライアント間のネットワークが瞬断し、再接続した際に「見逃したアラート」を再送できるかの検証。
  - 【コンカレンシー】1つの残り在庫を、10のレジから同時に購入試行した際のトランザクションロック検証。

---

## 3. アクションプラン

上記の分析に基づき、各サービスのテスト仕様書（`testcases-*.md`）の末尾に「**第4章: 追加・エッジケース (Supplementary & Edge Cases)**」を新設し、具体的なテストシナリオを追記しました。
"""

en_review = """---
title: "Test Case Design Review & Improvements"
parent: Testing
grand_parent: English
nav_order: 18
layout: default
---

# Test Case Design Review & Improvements

This document contains the review results for the test case designs of each microservice, analyzing missing perspectives (edge cases, negative cases, and non-functional requirements).

## 1. Evaluation Summary

The initial test cases provided high coverage for happy-path business logic and basic error control.
However, it was identified that tests for **extreme loads (performance)**, **distributed system failures (network partitions)**, and **malicious inputs (security)** were lacking.

## 2. Shortcomings and Improvement Strategy per Service

We define the specific issues and requirements to be added for each service.

### 2.1 Account Service
- **Status**: Authentication flows and tenant management are covered.
- **Missing Perspectives**:
  - [Security] Rate limiting verification against brute-force attacks.
  - [Security] Prevention tests for JWT replay attacks.

### 2.2 Terminal Service
- **Status**: Basic CRUD and heartbeat operations using DB and Redis are good.
- **Missing Perspectives**:
  - [Fault Tolerance] Fallback behavior when Dapr StateStore (Redis) is down.
  - [Edge Case] Race conditions when multiple terminals concurrently access the same store within milliseconds.

### 2.3 Master Data Service
- **Status**: The approach to cache invalidation is appropriate.
- **Missing Perspectives**:
  - [Performance] Processing time and memory leak verification during bulk sync/cache updates of production-equivalent data (100,000 items).
  - [Negative Case] Preventing "split-brain" states where only the cache is updated but the DB fails.

### 2.4 Cart Service (Critical)
- **Status**: Strong coverage for complex tax, discount, and double-submission prevention logic.
- **Missing Perspectives**:
  - [Boundary] Tests for cart item limits (e.g., 9999 items) or total amount overflows (e.g., exceeding 100M yen).
  - [Non-functional/State] Verification of garbage collection/discarding for cart sessions abandoned for several days due to browser/terminal power drops mid-payment.

### 2.5 Report Service
- **Status**: Avoidance of Cartesian product bugs and complex aggregations are perfect.
- **Missing Perspectives**:
  - [Edge Case] Boundary testing for transactions occurring around midnight across different timezones (e.g., UTC vs JST) to ensure proper daily aggregation.
  - [Boundary] Monthly report aggregation tests during leap years (Feb 29).

### 2.6 Journal Service
- **Status**: Transaction type conversions are appropriately defined.
- **Missing Perspectives**:
  - [Performance/Security] Defensive programming tests to protect the DB when the Search API is hit with extreme pagination like `limit=10,000,000`.
  - [Negative Case] Processing of an extremely massive JSON payload (multi-MB receipt data).

### 2.7 Stock Service
- **Status**: Coordination between stock adjustment and WebSocket alerts is excellent.
- **Missing Perspectives**:
  - [Fault Tolerance] Verification of alert resending ("missed alerts") upon reconnection after a momentary network drop between the WebSocket server and client.
  - [Concurrency] Transaction lock verification when 10 registers simultaneously attempt to purchase the last 1 remaining item.

---

## 3. Action Plan

Based on the above analysis, a "**Section 4: Supplementary & Edge Cases**" has been appended to the end of each service's test specification (`testcases-*.md`) containing these specific, advanced test scenarios.
"""

# 2. Supplementary Cases to Append (Japanese & English tuples)
supplements = {
    'account': (
"""
## 4. 追加・エッジケース (Supplementary & Edge Cases)

| ID | ターゲット | テストシナリオ (非機能・異常系) | 期待される結果 | 状態 |
|----|----------|-----------------------------|--------------|------|
| **AC-E-001** | `Security` | 同一IPから1秒間に50回の `POST /login` (ブルートフォース試行) | レートリミット機能が動作し、`429 Too Many Requests` が返却されること | ❌ 推奨 |
| **AC-E-002** | `Security` | ログアウト直後に、以前の有効なJWTを用いて再度リクエスト | トークンがブラックリスト（または失効リスト）に入り、`401` で拒否される（リプレイ防止） | ❌ 推奨 |
""",
"""
## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **AC-E-001** | `Security` | 50 `POST /login` requests in 1 second from same IP (Brute-force) | Rate limiter triggers, returning `429 Too Many Requests` | ❌ Recommended |
| **AC-E-002** | `Security` | Requesting with a valid JWT immediately after logout | Token is blacklisted/revoked, rejected with `401` (Anti-replay) | ❌ Recommended |
"""
    ),
    'terminal': (
"""
## 4. 追加・エッジケース (Supplementary & Edge Cases)

| ID | ターゲット | テストシナリオ (非機能・異常系) | 期待される結果 | 状態 |
|----|----------|-----------------------------|--------------|------|
| **TM-E-001** | `Resilience` | `POST /heartbeat` 時に Dapr Redis への接続が失敗（タイムアウト） | システムをクラッシュさせず、エラーログを出力し `503 Service Unavailable` または縮退処理で応えること | ❌ 推奨 |
| **TM-E-002** | `Concurrency` | 同一店舗に対してミリ秒単位で全く同時に「ターミナル初期登録」のリクエストを送る | Databaseのユニークインデックスやロック機構により、片方だけが成功しもう片方が `409` になること | ❌ 推奨 |
""",
"""
## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **TM-E-001** | `Resilience` | Dapr Redis connection failure (timeout) during `POST /heartbeat` | Does not crash; logs error and handles gracefully (e.g. `503 Service Unavailable` or degraded mode) | ❌ Recommended |
| **TM-E-002** | `Concurrency` | Sending "terminal initial registration" to the same store at the exact same millisecond | DB unique index/locking ensures only one succeeds, the other returns `409` | ❌ Recommended |
"""
    ),
    'master-data': (
"""
## 4. 追加・エッジケース (Supplementary & Edge Cases)

| ID | ターゲット | テストシナリオ (非機能・異常系) | 期待される結果 | 状態 |
|----|----------|-----------------------------|--------------|------|
| **MD-E-001** | `Performance`| 100,000件の商品データに対する一括キャッシュリフレッシュバッチの実行 | メモリリーク（OOM）を起こさず、指定時間（例：5分）以内に処理が完了すること | ❌ 推奨 |
| **MD-E-002** | `Integrity` | キャッシュ（Dapr Redis）への保存中にネットワークエラーが発生（スプリットブレイン） | MongoDBとRedis間でデータ不整合が起きないよう、分散再試行または自動復旧（Self-Healing）が機能すること | ❌ 推奨 |
""",
"""
## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **MD-E-001** | `Performance`| Bulk cache refresh batch execution for 100,000 item records | Completes within target time (e.g. 5 min) without causing memory leaks (OOM) | ❌ Recommended |
| **MD-E-002** | `Integrity` | Network error during saving to Cache (Dapr Redis) (Split-brain) | Distributed retry or Self-Healing functions correctly to prevent MongoDB-Redis data inconsistency | ❌ Recommended |
"""
    ),
    'cart': (
"""
## 4. 追加・エッジケース (Supplementary & Edge Cases)

| ID | ターゲット | テストシナリオ (非機能・異常系) | 期待される結果 | 状態 |
|----|----------|-----------------------------|--------------|------|
| **CT-E-001** | `Boundary` | カート内の特定商品の数量を 9,999 個（またはシステム上限）に設定 | 小計がオーバーフローを起こさず正確に計算される、または適切な上限エラー(`400`)が返ること | ❌ 推奨 |
| **CT-E-002** | `State Ttl`| 決済未完了のまま、カートセッションデータが Dapr StateStore に 72時間放置される | TTL（Time To Live）設定によりデータが自動的にガベージコレクションされ、メモリを圧迫しないこと | ❌ 推奨 |
| **CT-E-003** | `Security` | 割引率 (Discount Rate) パラメータに `1.5`（150%引）などの不正な値を送信 | バリデーションエラー(`422`)となり、マイナス請求が発生しないこと | ❌ 推奨 |
""",
"""
## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **CT-E-001** | `Boundary` | Setting cart item quantity to 9,999 (or system max) | Subtotal calculated accurately without overflow, or appropriate limit error (`400`) returned | ❌ Recommended |
| **CT-E-002** | `State Ttl`| Unsettled cart session left in Dapr StateStore for 72 hours | Automatically garbage collected via TTL, not eating memory | ❌ Recommended |
| **CT-E-003** | `Security` | Sending invalid discount rate like `1.5` (150% off) | Validation error (`422`) triggered, no negative billing occurs | ❌ Recommended |
"""
    ),
    'report': (
"""
## 4. 追加・エッジケース (Supplementary & Edge Cases)

| ID | ターゲット | テストシナリオ (非機能・異常系) | 期待される結果 | 状態 |
|----|----------|-----------------------------|--------------|------|
| **RP-E-001** | `Boundary` | 閏年（2024年）の2月28日〜3月1日にまたがる月次・週次集計処理 | 日付補正のバグ（例：2月が28日までと想定された計算）が発生せず、29日のデータが含まれること | ❌ 推奨 |
| **RP-E-002** | `Timezone` | タイムゾーンが UTC+9 (JST) の環境で、23:59:59 に発生したトランザクション | タイムゾーン変換に関わらず、正確に「当日分」の精算レポートに計上されること | ❌ 推奨 |
""",
"""
## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **RP-E-001** | `Boundary` | Monthly/Weekly aggregation across Feb 28 to Mar 1 in a Leap Year (2024) | No date-handling bugs; data for Feb 29 accurately included | ❌ Recommended |
| **RP-E-002** | `Timezone` | Transaction at 23:59:59 in UTC+9 (JST) environment | Exactly counted towards the "same day" settlement report regardless of timezone conversions | ❌ Recommended |
"""
    ),
    'journal': (
"""
## 4. 追加・エッジケース (Supplementary & Edge Cases)

| ID | ターゲット | テストシナリオ (非機能・異常系) | 期待される結果 | 状態 |
|----|----------|-----------------------------|--------------|------|
| **JN-E-001** | `Security` | `GET /search?limit=10000000` のように、破滅的な巨大ページネーションを要求 | アプリケーションレベルで防御され、`400 Bad Request` またはハードリミット（例：100）が適用されること | ❌ 推奨 |
| **JN-E-002** | `Edge Case`| メッセージキューから受信した Payload サイズが 5MB を超える超長尺レシートデータ | Jsonパースでメモリ超過を起こさず、適切にDB（またはBlob領域）にストリーミング保存されること | ❌ 推奨 |
""",
"""
## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **JN-E-001** | `Security` | Requesting catastrophic pagination size via `GET /search?limit=10000000` | Defended at app-level; `400 Bad Request` or forced hard-limit (e.g. 100) applied | ❌ Recommended |
| **JN-E-002** | `Edge Case`| Receiving ultra-long receipt data > 5MB payload from message queue | Parses JSON without OOM, streams/saves appropriately to DB (or Blob) | ❌ Recommended |
"""
    ),
    'stock': (
"""
## 4. 追加・エッジケース (Supplementary & Edge Cases)

| ID | ターゲット | テストシナリオ (非機能・異常系) | 期待される結果 | 状態 |
|----|----------|-----------------------------|--------------|------|
| **SK-E-001** | `Resilience` | WebSocketクライアントの接続が一時的に切れ（再接続中）に発注アラートが発生 | 再接続時にキューされた過去の未送信分アラートがリカバリー送信される、または取得APIが提供されている | ❌ 推奨 |
| **SK-E-002** | `Concurrency`| 在庫残り「1」の商品に対して、10箇所のレジ(Cart)から完全に同時に引当イベントが発火 | トランザクションロックが効き、1件のみが成功し、残り9件には「在庫不足」イベントが返信されること | ❌ 推奨 |
""",
"""
## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **SK-E-001** | `Resilience` | Reorder alert triggers while WebSocket client temporarily disconnected | Upon reconnect, queued/missed alerts are recovered/sent, or fetch API available | ❌ Recommended |
| **SK-E-002** | `Concurrency`| 10 Cart terminals fire allocation event for an item with exactly "1" stock perfectly concurrently | Tx-lock applies; only 1 succeeds, remaining 9 receive "Out of Stock" event reply | ❌ Recommended |
"""
    )
}

# Write Reviews
with open(os.path.join(base, 'ja', 'testing', 'testcase-review.md'), 'w', encoding='utf-8') as f:
    f.write(ja_review)
with open(os.path.join(base, 'en', 'testing', 'testcase-review.md'), 'w', encoding='utf-8') as f:
    f.write(en_review)

# Append to Service Testcases
for svc, (ja_supp, en_supp) in supplements.items():
    ja_path = os.path.join(base, 'ja', 'testing', f'testcases-{svc}.md')
    en_path = os.path.join(base, 'en', 'testing', f'testcases-{svc}.md')
    
    if os.path.exists(ja_path):
        with open(ja_path, 'a', encoding='utf-8') as f:
            f.write(ja_supp)
            
    if os.path.exists(en_path):
        with open(en_path, 'a', encoding='utf-8') as f:
            f.write(en_supp)

# Update indices
def update_index(path, title, filename):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if filename not in content:
        # Just append it below the main test review
        content = content.replace(
            '[Test Review](test-review.html) | Comprehensive Test Assessment & Strategy',
            f'[Test Review](test-review.html) | Comprehensive Test Assessment & Strategy\n| [{title}]({filename}.html) | {title} |'
        ).replace(
            '[Test Review](test-review.html) | 包括的なテスト評価と戦略',
            f'[Test Review](test-review.html) | 包括的なテスト評価と戦略\n| [{title}]({filename}.html) | {title} |'
        )
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

update_index(os.path.join(base, 'ja', 'testing', 'index.md'), 'テストケース設計 評価・改善報告', 'testcase-review')
update_index(os.path.join(base, 'en', 'testing', 'index.md'), 'Test Case Design Review', 'testcase-review')

print("Review document created and test cases supplemented successfully.")

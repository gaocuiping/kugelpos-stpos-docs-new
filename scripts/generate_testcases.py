import os

base = '/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs'

testcases = {
    'account': {
        'ja': '''---
title: "Account サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 11
layout: default
---

# Account サービス テストケース

現在のテストコードから抽出したテストケースと、不足している推奨シナリオのリストです。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| AC-U-01 | ヘルスチェックAPIが正常に動作し、Dapr依存なしでも稼働するか | Health | 🟡 中 | ✅ 実装済 |
| AC-U-02 | 正常システムオペレーション時の動作検証 | Basic | 🟡 中 | ✅ 実装済 |
| AC-U-03 | 正常な資格情報によるログインでJWTトークンが発行されるか | Auth | 🔴 高 | ❌ 推奨 |
| AC-U-04 | 無効なパスワードでのログインで401エラーが返されるか | Auth | 🔴 高 | ❌ 推奨 |
| AC-U-05 | 存在しないユーザーでのログインで401エラーが返されるか | Auth | 🔴 高 | ❌ 推奨 |
| AC-U-06 | トークンの有効期限切れ時に401エラーが返されるか | Auth | 🔴 高 | ❌ 推奨 |
| AC-U-07 | リフレッシュトークンで新しいアクセストークンが取得できるか | Auth | 🟠 高 | ❌ 推奨 |
| AC-U-08 | テナントIDヘッダーがない場合のアククセス拒否 | Tenant | 🔴 高 | ❌ 推奨 |
| AC-U-09 | ユーザー情報取得APIが正しいデータを返すか | Profile | 🟡 中 | ❌ 推奨 |
| AC-U-10 | パスワード変更が正常に行えるか | Profile | 🟡 中 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| AC-I-01 | JWTによる認証付きのAPI呼び出しフロー全体 | Scenario | 🔴 高 | ❌ 推奨 |
| AC-I-02 | MongoDB へのユーザー作成・保存・取得の一連の流れ | Integration | 🟠 高 | ❌ 推奨 |
| AC-I-03 | マルチテナント環境でのデータ隔離検証 | Integration | 🔴 高 | ❌ 推奨 |
''',
        'en': '''---
title: "Account Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 11
layout: default
---

# Account Service Test Cases

List of test cases extracted from current test code and missing recommended scenarios.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| AC-U-01 | Health check API works normally, even without Dapr | Health | 🟡 Med | ✅ Implemented |
| AC-U-02 | Verify basic system operations | Basic | 🟡 Med | ✅ Implemented |
| AC-U-03 | Login with valid credentials issues JWT token | Auth | 🔴 High | ❌ Recommended |
| AC-U-04 | Login with invalid password returns 401 | Auth | 🔴 High | ❌ Recommended |
| AC-U-05 | Login with non-existent user returns 401 | Auth | 🔴 High | ❌ Recommended |
| AC-U-06 | Expired token access returns 401 | Auth | 🔴 High | ❌ Recommended |
| AC-U-07 | Refresh token successfully gets new access token | Auth | 🟠 High | ❌ Recommended |
| AC-U-08 | Missing tenant ID header is rejected | Tenant | 🔴 High | ❌ Recommended |
| AC-U-09 | Get user profile API returns correct data | Profile | 🟡 Med | ❌ Recommended |
| AC-U-10 | Password change is processed correctly | Profile | 🟡 Med | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| AC-I-01 | End-to-end API call flow with JWT authentication | Scenario | 🔴 High | ❌ Recommended |
| AC-I-02 | Complete flow of user creation, saving, and retrieval in MongoDB | Integration | 🟠 High | ❌ Recommended |
| AC-I-03 | Data isolation verification in multi-tenant environment | Integration | 🔴 High | ❌ Recommended |
'''
    },
    'terminal': {
        'ja': '''---
title: "Terminal サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 12
layout: default
---

# Terminal サービス テストケース

現在のテストコードから抽出したテストケースと、不足している推奨シナリオのリストです。現状、ビジネスロジックのテストが大幅に不足しています。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| TM-U-01 | ヘルスチェックAPIの正常動作（バックグラウンドジョブ詳細含む） | Health | 🟡 中 | ✅ 実装済 |
| TM-U-02 | 基本的なターミナルオペレーションの動作検証 | Basic | 🟡 中 | ✅ 実装済 |
| TM-U-03 | ターミナルの新規登録が成功するか | CRUD | 🔴 高 | ❌ 推奨 |
| TM-U-04 | 既存ターミナルIDでの登録試行時、409エラーが返されるか | CRUD | 🔴 高 | ❌ 推奨 |
| TM-U-05 | ターミナル情報の更新が成功するか | CRUD | 🟠 高 | ❌ 推奨 |
| TM-U-06 | 存在しないターミナルIDの取得で404エラーが返されるか | CRUD | 🟠 高 | ❌ 推奨 |
| TM-U-07 | ターミナルのハートビート（最終アクセス時刻更新）が機能するか | Status | 🔴 高 | ❌ 推奨 |
| TM-U-08 | ターミナルの状態（稼働中・停止中）変更プロセスの検証 | Status | 🟠 高 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| TM-I-01 | MongoDBへのターミナル・店舗情報の永続化 | Integration | 🔴 高 | ❌ 推奨 |
| TM-I-02 | Redis キャッシュによるターミナル情報取得の高速化検証 | Integration | 🟠 高 | ❌ 推奨 |
| TM-S-01 | ターミナル起動 → 登録 → ハートビートの一連のフロー | Scenario | 🟠 高 | ❌ 推奨 |
''',
        'en': '''---
title: "Terminal Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 12
layout: default
---

# Terminal Service Test Cases

List of test cases extracted from current test code and missing recommended scenarios. Currently, business logic tests are significantly lacking.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| TM-U-01 | Health check API normal operation (including background job details) | Health | 🟡 Med | ✅ Implemented |
| TM-U-02 | Verify basic terminal operations | Basic | 🟡 Med | ✅ Implemented |
| TM-U-03 | New terminal registration succeeds | CRUD | 🔴 High | ❌ Recommended |
| TM-U-04 | Registering existing terminal ID returns 409 | CRUD | 🔴 High | ❌ Recommended |
| TM-U-05 | Terminal information update succeeds | CRUD | 🟠 High | ❌ Recommended |
| TM-U-06 | Fetching non-existent terminal ID returns 404 | CRUD | 🟠 High | ❌ Recommended |
| TM-U-07 | Terminal heartbeat (last access time update) functions | Status | 🔴 High | ❌ Recommended |
| TM-U-08 | Terminal status (active/inactive) change process validation | Status | 🟠 High | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| TM-I-01 | Persistence of terminal/store information to MongoDB | Integration | 🔴 High | ❌ Recommended |
| TM-I-02 | Terminal info retrieval acceleration via Redis cache | Integration | 🟠 High | ❌ Recommended |
| TM-S-01 | Terminal boot → registration → heartbeat end-to-end flow | Scenario | 🟠 High | ❌ Recommended |
'''
    },
    'master-data': {
        'ja': '''---
title: "Master Data サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 13
layout: default
---

# Master Data サービス テストケース

現在のテストコードから抽出したテストケースと、不足している推奨シナリオのリストです。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| MD-U-01 | ヘルスチェックAPIとレスポンス時間の検証 | Health | 🟡 中 | ✅ 実装済 |
| MD-U-02 | 基本的なオペレーションの動作検証 | Basic | 🟡 中 | ✅ 実装済 |
| MD-U-03 | 商品（Item）マスターの取得（全件・個別） | Item | 🔴 高 | ❌ 推奨 |
| MD-U-04 | カテゴリマスターの取得と階層構造の検証 | Category | 🟠 高 | ❌ 推奨 |
| MD-U-05 | 税率（Tax）マスターの取得検証 | Tax | 🔴 高 | ❌ 推奨 |
| MD-U-06 | 支払方法（Payment）マスターの取得検証 | Payment | 🟠 高 | ❌ 推奨 |
| MD-U-07 | Dapr Statestore (Redis) からのマスターキャッシュ取得 | Cache | 🔴 高 | ❌ 推奨 |
| MD-U-08 | 存在しないマスターデータ要求時の 404 エラー処理 | Error | 🟡 中 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| MD-I-01 | マスターデータ更新時の Dapr pub/sub 経由でのキャッシュ破棄通知 | Integration | 🔴 高 | ❌ 推奨 |
| MD-I-02 | MongoDBからの商品データ読み込みとRedisへのキャッシュ保存処理 | Integration | 🔴 高 | ❌ 推奨 |
| MD-S-01 | カートサービスなどの他サービスから、gRPC経由での商品情報取得フロー | Scenario | 🟠 高 | ❌ 推奨 |
''',
        'en': '''---
title: "Master Data Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 13
layout: default
---

# Master Data Service Test Cases

List of test cases extracted from current test code and missing recommended scenarios.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| MD-U-01 | Health check API and response time validation | Health | 🟡 Med | ✅ Implemented |
| MD-U-02 | Verify basic operations | Basic | 🟡 Med | ✅ Implemented |
| MD-U-03 | Item master retrieval (all/individual) | Item | 🔴 High | ❌ Recommended |
| MD-U-04 | Category master retrieval and hierarchy validation | Category | 🟠 High | ❌ Recommended |
| MD-U-05 | Tax master retrieval validation | Tax | 🔴 High | ❌ Recommended |
| MD-U-06 | Payment method master retrieval validation | Payment | 🟠 High | ❌ Recommended |
| MD-U-07 | Master cache retrieval from Dapr Statestore (Redis) | Cache | 🔴 High | ❌ Recommended |
| MD-U-08 | 404 error handling when requesting non-existent master data | Error | 🟡 Med | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| MD-I-01 | Cache invalidation notification via Dapr pub/sub on master data update | Integration | 🔴 High | ❌ Recommended |
| MD-I-02 | Loading item data from MongoDB and saving cache to Redis | Integration | 🔴 High | ❌ Recommended |
| MD-S-01 | Item info retrieval flow via gRPC from other services like Cart | Scenario | 🟠 High | ❌ Recommended |
'''
    },
    'cart': {
        'ja': '''---
title: "Cart サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 14
layout: default
---

# Cart サービス テストケース

ビジネスロジックが豊富で、多くのテストが既に実装されています。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| CT-U-01 | ヘルスチェックAPIの正常動作 | Health | 🟡 中 | ✅ 実装済 |
| CT-U-02 | アイテム登録（Item Entry）の再開・レジューム機能 | Main | 🔴 高 | ✅ 実装済 |
| CT-U-03 | キャッシュレス決済時のエラーハンドリング | Payment | 🔴 高 | ✅ 実装済 |
| CT-U-04 | 小計（Subtotal）ロジックの計算精度検証 | Calc | 🔴 高 | ✅ 実装済 |
| CT-U-05 | ターミナルキャッシュの取得と更新 | Cache | 🟡 中 | ✅ 実装済 |
| CT-U-06 | トランザクション状態（Tran Service Status）検証 | Status | 🟠 高 | ✅ 実装済 |
| CT-U-07 | 既に取り消し済みの取引に対する再取消（二重Void）の防止 | Void | 🔴 高 | ✅ 実装済 |
| CT-U-08 | 既に返品済みの取引に対する再返品（二重Return）の防止 | Return | 🔴 高 | ✅ 実装済 |
| CT-U-09 | 二重Void/Return防止に伴うリスト状態と単一取得時の整合性 | Void/Return | 🔴 高 | ✅ 実装済 |
| CT-U-10 | Dapr Statestore セッション作成、再利用、タイムアウト処理 | Session | 🟠 高 | ✅ 実装済 |
| CT-U-11 | gRPC チャンネル（モジュールレベルスタブ）の生成・再利用 | gRPC | 🟠 高 | ✅ 実装済 |
| CT-U-12 | 単一商品の税計算、複数商品の税計算（内税・外税混在） | Tax | 🔴 高 | ❌ 推奨 |
| CT-U-13 | 割引計算（単品割引、カート全体割引） | Discount | 🟠 高 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| CT-I-01 | Cart から Master-data への gRPC 直接通信による商品情報取得 | Integration | 🔴 高 | ✅ 実装済 |
| CT-I-02 | 購入完了時の Stock サービスへの在庫引当 (Pub/Sub) | Integration | 🔴 高 | ❌ 推奨 |
| CT-I-03 | Transaction完了時の Journal サービスへの履歴保存 (Pub/Sub) | Integration | 🔴 高 | ❌ 推奨 |
| CT-S-01 | item-book シナリオ（商品スキャン → 数量変更 → 割引 → 支払） | Scenario | 🔴 高 | ❌ 推奨 |
''',
        'en': '''---
title: "Cart Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 14
layout: default
---

# Cart Service Test Cases

Rich business logic with many tests already implemented.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| CT-U-01 | Health check API normal operation | Health | 🟡 Med | ✅ Implemented |
| CT-U-02 | Item Entry resume function | Main | 🔴 High | ✅ Implemented |
| CT-U-03 | Error handling during cashless payment | Payment | 🔴 High | ✅ Implemented |
| CT-U-04 | Subtotal logic calculation accuracy validation | Calc | 🔴 High | ✅ Implemented |
| CT-U-05 | Terminal cache retrieval and update | Cache | 🟡 Med | ✅ Implemented |
| CT-U-06 | Transaction status validation | Status | 🟠 High | ✅ Implemented |
| CT-U-07 | Prevention of double void on already voided transactions | Void | 🔴 High | ✅ Implemented |
| CT-U-08 | Prevention of double return on already returned transactions | Return | 🔴 High | ✅ Implemented |
| CT-U-09 | List status and single retrieval consistency with double void/return prevention | Void/Return | 🔴 High | ✅ Implemented |
| CT-U-10 | Dapr Statestore session creation, reuse, timeout | Session | 🟠 High | ✅ Implemented |
| CT-U-11 | gRPC channel creation and reuse | gRPC | 🟠 High | ✅ Implemented |
| CT-U-12 | Single/multiple item tax calculation (mixed internal/external tax) | Tax | 🔴 High | ❌ Recommended |
| CT-U-13 | Discount calculation (single item, whole cart) | Discount | 🟠 High | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| CT-I-01 | Item info retrieval via direct gRPC from Cart to Master-data | Integration | 🔴 High | ✅ Implemented |
| CT-I-02 | Inventory allocation to Stock service on purchase completion (Pub/Sub) | Integration | 🔴 High | ❌ Recommended |
| CT-I-03 | History saving to Journal service on transaction completion (Pub/Sub) | Integration | 🔴 High | ❌ Recommended |
| CT-S-01 | item-book scenario (item scan → qty change → discount → payment) | Scenario | 🔴 High | ❌ Recommended |
'''
    },
    'report': {
        'ja': '''---
title: "Report サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 15
layout: default
---

# Report サービス テストケース

集計ロジックを中心に非常に豊富にテストされています。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| RP-U-01 | レポートオペレーションの基本動作検証 | Basic | 🟡 中 | ✅ 実装済 |
| RP-U-02 | Cancelされた取引の集計除外フラグの検証 | Cancel | 🔴 高 | ✅ 実装済 |
| RP-U-03 | カテゴリレポートのフォーマットと期間計算の検証 | Category | 🔴 高 | ✅ 実装済 |
| RP-U-04 | 複数店舗・ターミナルにまたがる一意識別のテスト | Multi | 🟠 高 | ✅ 実装済 |
| RP-U-05 | 返品（Return）取引の集計ロジックの検証 | Return | 🔴 高 | ✅ 実装済 |
| RP-U-06 | 複数税率混在時の直積（Cartesian product）バグ防止のテスト | Tax | 🔴 高 | ✅ 実装済 |
| RP-U-07 | 複数支払方法（スプリットペイメント）混在の検証 | Payment | 🔴 高 | ✅ 実装済 |
| RP-U-08 | 支払金額が「売上＋税金」に常に一致するデータ整合性の検証 | Integrity | 🔴 高 | ✅ 実装済 |
| RP-U-09 | 0円取引、空の税金配列などエッジケースの検証 | Edge | 🟡 中 | ✅ 実装済 |
| RP-U-10 | Flashレポートの期間（Store/Terminal）バリデーション | Flash | 🟠 高 | ✅ 実装済 |
| RP-U-11 | アイテム（商品）レポート期間計算の検証 | Item | 🟠 高 | ✅ 実装済 |
| RP-U-12 | ジャーナル統合（Flash/Dailyレポート送信）のテスト | Journal | 🔴 高 | ✅ 実装済 |
| RP-U-13 | 支払レポートのエラーハンドリングと日付バリデーション | Payment | 🟠 高 | ✅ 実装済 |
| RP-U-14 | 内税・外税・混在・複数税率の表示とブレークダウン計算 | Tax | 🔴 高 | ✅ 実装済 |
| RP-U-15 | 無効化（Void）された売上と返品の複雑なシナリオ検証 | Void | 🔴 高 | ✅ 実装済 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| RP-I-01 | Report作成時のDapr StateStore保存検証 | Integration | 🔴 高 | ❌ 推奨 |
| RP-I-02 | JournalサービスへのDapr Pub/Subレポート発行テスト | Integration | 🔴 高 | ❌ 推奨 |
''',
        'en': '''---
title: "Report Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 15
layout: default
---

# Report Service Test Cases

Extensively tested, especially around aggregation logic.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| RP-U-01 | Basic report operations verification | Basic | 🟡 Med | ✅ Implemented |
| RP-U-02 | Validation of cancelled transaction exclusion flag | Cancel | 🔴 High | ✅ Implemented |
| RP-U-03 | Category report formatting and date calculation | Category | 🔴 High | ✅ Implemented |
| RP-U-04 | Unique identification across multiple stores and terminals | Multi | 🟠 High | ✅ Implemented |
| RP-U-05 | Aggregation logic validation for Return transactions | Return | 🔴 High | ✅ Implemented |
| RP-U-06 | Cartesian product bug prevention for mixed multiple tax rates | Tax | 🔴 High | ✅ Implemented |
| RP-U-07 | Mixed payment methods (split payment) verification | Payment | 🔴 High | ✅ Implemented |
| RP-U-08 | Data integrity: payment amount always equals sales + tax | Integrity | 🔴 High | ✅ Implemented |
| RP-U-09 | Edge cases: 0 yen transaction, empty tax array | Edge | 🟡 Med | ✅ Implemented |
| RP-U-10 | Flash report date validation (Store/Terminal) | Flash | 🟠 High | ✅ Implemented |
| RP-U-11 | Item report date calculation verification | Item | 🟠 High | ✅ Implemented |
| RP-U-12 | Journal integration (Flash/Daily report transmission) | Journal | 🔴 High | ✅ Implemented |
| RP-U-13 | Payment report error handling and date validation | Payment | 🟠 High | ✅ Implemented |
| RP-U-14 | Internal/external mixed tax rates display and breakdown | Tax | 🔴 High | ✅ Implemented |
| RP-U-15 | Complex scenarios of voided sales and returns | Void | 🔴 High | ✅ Implemented |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| RP-I-01 | Dapr StateStore saving verification on report creation | Integration | 🔴 High | ❌ Recommended |
| RP-I-02 | Dapr Pub/Sub report publishing test to Journal service | Integration | 🔴 High | ❌ Recommended |
'''
    },
    'stock': {
        'ja': '''---
title: "Stock サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 16
layout: default
---

# Stock サービス テストケース

在庫管理、スナップショットスケジューラー、WebSocketアラートなどがカバーされています。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| SK-U-01 | 在庫（Stock）の取得・更新・履歴の検証 | Basic | 🔴 高 | ✅ 実装済 |
| SK-U-02 | 発注アラート（条件、更新トリガー、最小在庫）の検証 | Alert | 🔴 高 | ✅ 実装済 |
| SK-U-03 | スナップショットスケジューラー（CRON設定、テナント更新）の検証 | Schedule | 🟠 高 | ✅ 実装済 |
| SK-U-04 | スナップショットデータの期間指定（Date Range）による取得検証 | Snapshot | 🟠 高 | ✅ 実装済 |
| SK-U-05 | マイナス在庫許可フラグの動作検証 | Edge | 🟡 中 | ✅ 実装済 |
| SK-U-06 | 複数店舗の在庫一覧取得検証 | Store | 🟡 中 | ✅ 実装済 |
| SK-U-07 | WebSocket接続とアラート（再発注・最小在庫）の受信検証 | WS | 🔴 高 | ✅ 実装済 |
| SK-U-08 | WebSocketマルチクライアントおよび未承認アクセス検証 | WS | 🟠 高 | ✅ 実装済 |
| SK-U-09 | 手動在庫調整時のバリデーション | CRUD | 🔴 高 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| SK-I-01 | Dapr Subscribe 経由の他サービスからの在庫引当要求の処理 | Integration | 🔴 高 | ✅ 実装済 |
| SK-I-02 | MongoDB への在庫更新アトミック操作検証 | Integration | 🔴 高 | ❌ 推奨 |
| SK-S-01 | 在庫更新 → 発注アラート起動 → WebSocket通知のE2Eフロー | Scenario | 🔴 高 | ❌ 推奨 |
''',
        'en': '''---
title: "Stock Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 16
layout: default
---

# Stock Service Test Cases

Covers inventory management, snapshot scheduler, and WebSocket alerts.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| SK-U-01 | Stock retrieval, update, and history verification | Basic | 🔴 High | ✅ Implemented |
| SK-U-02 | Reorder alert verification (conditions, triggers, min stock) | Alert | 🔴 High | ✅ Implemented |
| SK-U-03 | Snapshot scheduler verification (CRON settings, tenant updates) | Schedule | 🟠 High | ✅ Implemented |
| SK-U-04 | Snapshot retrieval by date range verification | Snapshot | 🟠 High | ✅ Implemented |
| SK-U-05 | Negative stock allowed flag behavior | Edge | 🟡 Med | ✅ Implemented |
| SK-U-06 | Multi-store stock list retrieval | Store | 🟡 Med | ✅ Implemented |
| SK-U-07 | WebSocket connection and alert reception | WS | 🔴 High | ✅ Implemented |
| SK-U-08 | WebSocket multi-client and unauthorized access | WS | 🟠 High | ✅ Implemented |
| SK-U-09 | Manual stock adjustment validation | CRUD | 🔴 High | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| SK-I-01 | Processing inventory allocation requests from other services via Dapr Subscribe | Integration | 🔴 High | ✅ Implemented |
| SK-I-02 | MongoDB atomic operation verification for stock updates | Integration | 🔴 High | ❌ Recommended |
| SK-S-01 | Stock update → reorder alert trigger → WebSocket notification E2E flow | Scenario | 🔴 High | ❌ Recommended |
'''
    },
    'journal': {
        'ja': '''---
title: "Journal サービス テストケース"
parent: テスト
grand_parent: 日本語
nav_order: 17
layout: default
---

# Journal サービス テストケース

ジャーナル保存とトランザクション種別の変換を中心にテストされています。

## Unit Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| JN-U-01 | ヘルスチェックAPIの正常動作 | Health | 🟡 中 | ✅ 実装済 |
| JN-U-02 | ジャーナルレポート操作の検証 | Basic | 🟡 中 | ✅ 実装済 |
| JN-U-03 | 正常な売上（キャンセル未）のトランザクションログ受信検証 | Log | 🔴 高 | ✅ 実装済 |
| JN-U-04 | キャンセルされた売上のトランザクションログ受信とタイプ変換 | Log | 🔴 高 | ✅ 実装済 |
| JN-U-05 | エラー発生時のトランザクションロールバック処理 | Error | 🟠 高 | ✅ 実装済 |
| JN-U-06 | トランザクション種別の変換ロジック（通常、キャンセル、マイナスタイプ） | Conversion | 🔴 高 | ✅ 実装済 |
| JN-U-07 | ジャーナルの期間検索とページネーション | Search | 🟠 高 | ❌ 推奨 |

## Integration & Scenario Tests

| ID | テストケース | 種別 | 優先度 | 状態 |
|----|------------|------|-------|------|
| JN-I-01 | ReportサービスからのPub/Sub経由のジャーナル受信 | Integration | 🔴 高 | ❌ 推奨 |
| JN-I-02 | Elasticsearch/MongoDB等の検索インデックスとの同期 | Integration | 🟠 高 | ❌ 推奨 |
| JN-S-01 | トランザクション完了 → ジャーナル保存 → APIでの検索のE2E | Scenario | 🟠 高 | ❌ 推奨 |
''',
        'en': '''---
title: "Journal Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 17
layout: default
---

# Journal Service Test Cases

Tested mainly around journal saving and transaction type conversions.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| JN-U-01 | Health check API normal operation | Health | 🟡 Med | ✅ Implemented |
| JN-U-02 | Journal report operations verification | Basic | 🟡 Med | ✅ Implemented |
| JN-U-03 | Transaction log reception of normal sales (not cancelled) | Log | 🔴 High | ✅ Implemented |
| JN-U-04 | Transaction log reception and type conversion of cancelled sales | Log | 🔴 High | ✅ Implemented |
| JN-U-05 | Transaction rollback process on error | Error | 🟠 High | ✅ Implemented |
| JN-U-06 | Transaction type conversion logic (normal, cancelled, negative types) | Conversion | 🔴 High | ✅ Implemented |
| JN-U-07 | Journal date range search and pagination | Search | 🟠 High | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| JN-I-01 | Receiving journal from Report service via Pub/Sub | Integration | 🔴 High | ❌ Recommended |
| JN-I-02 | Synchronization with search indexes like Elasticsearch/MongoDB | Integration | 🟠 High | ❌ Recommended |
| JN-S-01 | Transaction complete → Journal saved → Searched via API E2E | Scenario | 🟠 High | ❌ Recommended |
'''
    }
}

for svc, langs in testcases.items():
    for lang, content in langs.items():
        dst = os.path.join(base, lang, 'testing', f'testcases-{svc}.md')
        with open(dst, 'w') as f:
            f.write(content)

print("Generated all testcase files successfully!")

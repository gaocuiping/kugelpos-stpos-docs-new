import os

base = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs"

services = ['cart', 'terminal', 'account', 'master-data', 'report', 'journal', 'stock']

# Extracted from test-review.md (Existing tests)
existing_tests = {
    'cart': {
        'unit': [
            ('test_calc_subtotal_logic.py', '小計計算ロジック（内税・外税）', '✅ 高', 'Subtotal calculation logic (Inclusive/Exclusive Tax)', '✅ High'),
            ('test_tran_service_unit_simple.py', 'Void/返品の事前バリデーション', '✅ 中', 'Pre-validation for Void/Return', '✅ Med'),
            ('test_tran_service_status.py', 'トランザクションステータス管理', '✅ 中', 'Transaction status management', '✅ Med'),
            ('test_terminal_cache.py', '端末キャッシュ管理ロジック', '✅ 中', 'Terminal cache management', '✅ Med'),
            ('test_text_helper.py', 'テキストユーティリティ', '✅ 中', 'Text utility helpers', '✅ Med'),
            ('repositories/test_item_master_grpc_repository.py', 'gRPCリポジトリ', '✅ 中', 'gRPC Repository', '✅ Med'),
            ('utils/test_grpc_channel_helper.py', 'gRPCチャンネル管理', '✅ 中', 'gRPC channel', '✅ Med'),
            ('utils/test_dapr_statestore_session_helper.py', 'Dapr状態ストア', '✅ 中', 'Dapr statestore', '✅ Med'),
        ],
        'integration': [],
        'scenario': [
            ('test_cart.py', '通常売上・値引・数量変更等', '✅ 86%', 'Normal sales, discounts, quantity', '✅ 86%'),
            ('test_void_return.py', 'Void・返品フロー', '✅ 高', 'Void & Return flow', '✅ High'),
            ('test_payment_cashless_error.py', 'キャッシュレスエラー', '⚠️ 部分', 'Cashless error scenario', '⚠️ Partial'),
            ('test_resume_item_entry.py', '商品入力再開フロー', '✅ 中', 'Resume item entry', '✅ Med'),
        ]
    },
    'terminal': {
        'unit': [], 'integration': [],
        'scenario': [('test_terminal.py', 'Tenant/Store/Terminal CRUD・開閉局・入出金', '✅ 91%', 'Tenant/Store/Terminal CRUD, Open/Close, Cash', '✅ 91%')]
    },
    'account': {
        'unit': [], 'integration': [],
        'scenario': [('test_operations.py', 'ログイン・スーパー管理者登録・重複エラー', '✅ 67%', 'Login, Super Admin, Duplicate Error', '✅ 67%')]
    },
    'master-data': {
        'unit': [], 'integration': [],
        'scenario': [('複数ファイル', 'Staff/Category/Item/Payment/Settings CRUD', '⚠️ 63%', 'Staff/Category/Item/Payment/Settings CRUD operations', '⚠️ 63%')]
    },
    'report': {
        'unit': [
            ('test_journal_integration.py', 'レポート集計ロジック（mock使用）', '✅ 中', 'Report aggregation logic (mocked)', '✅ Med'),
            ('test_terminal_id_parsing.py', '端末IDパースロジック', '✅ 中', 'Terminal ID parsing', '✅ Med'),
        ],
        'integration': [],
        'scenario': [
            ('test_report.py', '店舗・端末別売上レポート', '✅ 高', 'Sales report by Store/Terminal', '✅ High'),
            ('test_category_report.py', 'カテゴリ別レポート', '✅ 高', 'Sales report by Category', '✅ High'),
            ('test_item_report.py', '商品別レポート', '✅ 高', 'Sales report by Item', '✅ High'),
            ('test_payment_report_all.py', '決済方法別レポート', '✅ 高', 'Sales report by Payment Method', '✅ High'),
            ('test_cancelled_transactions.py', '取消取引含む集計', '✅ 高', 'Aggregating Cancelled tx', '✅ High'),
            ('test_void_transactions.py', 'Void取引含む集計', '✅ 高', 'Aggregating Void tx', '✅ High'),
            ('test_return_transactions.py', '返品取引含む集計', '✅ 高', 'Aggregating Return tx', '✅ High'),
            ('test_split_payment_bug.py', '分割支払の集計', '✅ 高', 'Aggregating Split payments', '✅ High'),
            ('test_critical_issue_78.py', 'バグ修正回帰テスト', '✅ 高', 'Bug regression', '✅ High'),
            ('test_issue_90_internal_tax_not_deducted.py', '内税回帰テスト', '✅ 高', 'Inclusive tax regression', '✅ High'),
        ]
    },
    'journal': {
        'unit': [
            ('test_log_service.py', 'tranlog受信・取引種別変換ロジック（6ケース）', '✅ 高', 'Tranlog reception & TxType conversion', '✅ High'),
            ('test_transaction_type_conversion.py', '取引種別変換（パラメータ化）', '✅ 高', 'TxType conversion', '✅ High'),
        ],
        'integration': [],
        'scenario': [
            ('test_journal.py', 'Journal照会（BearerToken・APIキー・ページング）', '⚠️ 29%', 'Journal Query API', '⚠️ 29%')
        ]
    },
    'stock': {
        'unit': [
            ('test_snapshot_scheduler.py', 'スナップショット自動スケジューラー', '✅ 中', 'Snapshot Scheduler', '✅ Med'),
        ],
        'integration': [],
        'scenario': [
            ('test_stock.py', '在庫CRUD・tranlog受信・スナップショット', '✅ 高', 'Stock CRUD, tranlog reception, Snapshot', '✅ High'),
            ('test_reorder_alerts.py', '発注アラート', '✅ 高', 'Reorder Alerts', '✅ High'),
            ('test_snapshot_date_range.py', 'スナップショット日付範囲（境界値）', '✅ 高', 'Snapshot boundary', '✅ High'),
            ('test_snapshot_schedule_api.py', 'スケジュール管理', '✅ 中', 'Schedule Management API', '✅ Med'),
            ('test_websocket_alerts.py', 'WebSocket通知', '✅ 中', 'WebSocket Notifications', '✅ Med'),
            ('test_websocket_reorder_new.py', 'WebSocket新設計', '✅ 中', 'WebSocket new design', '✅ Med'),
        ]
    }
}

# The Supplemented/Recommended tests
recommended_tests = {
    'cart': {
        'unit': [
            ('CT-U-003', 'DELETE /entry/{id}', '登録した商品の一部を取消（行キャンセル）する', '指定された行が削除され、小計が再計算されること', '❌ 補充(単体)', 'Cancel part of cart item', 'Specific line deleted, subtotal recalculated', '❌ Missing Unit'),
            ('CT-U-011', 'tax_engine', '単一商品に複数の税率（例：消費税10% + 軽減税率8%）', '各税金が正しく按分・計算されること', '❌ 補充(単体)', 'Multiple tax rates on a single item', 'Tax prorated and calculated correctly', '❌ Missing Unit'),
            ('CT-U-012', 'discount_engine', '単品「100円引き」と全体「10%引き」の複合', '割引適用順序に従い、正確な金額を算出', '❌ 補充(単体)', 'Compound discounts (Item -100 & Cart -10%)', 'Applied in correct sequence', '❌ Missing Unit'),
            ('CT-U-013', 'calc_subtotal', '割引適用によって金額がマイナスになる場合', 'エラーまたは0円下限として処理されること', '❌ 補充(単体)', 'Discount results in negative subtotal', 'Handled as error or floored at 0', '❌ Missing Unit'),
            ('CT-E-003', 'Security', '割引率に `1.5`（150%引）などの不正な値を送信', 'バリデーションエラー(422)', '❌ 補充(境界)', 'Send invalid discount rate (150%)', 'Validation 422 triggers', '❌ Missing Boundary'),
        ],
        'integration': [
            ('CT-I-002', 'Cart → Dapr (Stock)', '購入完了時の Pub/Sub 経由の在庫引当通知', 'メッセージが送信される', '❌ 補充(結合)', 'Inventory deduction via Dapr Pub/Sub', 'Message correctly sent', '❌ Missing Int'),
            ('CT-I-003', 'Cart → Dapr (Journal)', '決済完了後のジャーナル生成通知', '取引データが送信される', '❌ 補充(結合)', 'Journal generation via Dapr Pub/Sub', 'Message correctly sent', '❌ Missing Int'),
        ],
        'scenario': [
            ('CT-E-001', 'Boundary', '特定商品の数量を 9,999 個（システム上限）に設定', 'オーバーフローせずエラーか計算される', '❌ 補充(総合)', 'Qty = 9999', 'Overflow prevented', '❌ Missing Scenario'),
            ('CT-E-002', 'State Ttl', '未決済カートが 72時間放置される', 'TTLでGCされメモリ圧迫しない', '❌ 補充(総合)', 'Cart idle for 72hr', 'Collected via TTL', '❌ Missing Scenario'),
        ]
    },
    'account': {
        'unit': [
            ('AC-U-010', 'login_logic', '正しいユーザーIDとパスワードでの認証処理', 'JWTトークンが生成される', '❌ 補充(単体)', 'Auth with correct credentials', 'JWT token generated', '❌ Missing Unit'),
            ('AC-E-001', 'Security', '1秒間に50回の `POST /login` (ブルートフォース)', '`429 Too Many Requests`', '❌ 補充(単体)', 'Bruteforce /login 50 times in 1s', '429 Rate limited', '❌ Missing Unit'),
            ('AC-E-002', 'Security', 'ログアウト直後に、古い有効なJWTを用いて再度リクエスト', 'トークンが失効リストに入り `401`', '❌ 補充(単体)', 'Reuse JWT after logout', '401 Rejected (Anti-replay)', '❌ Missing Unit'),
        ],
        'integration': [
            ('AC-I-001', 'Dapr (Redis)', 'JWTトークンのキャッシュ/ブラックリスト同期', 'Redis上にトークン情報が正しく格納される', '❌ 補充(結合)', 'Store JWT in Redis blacklist', 'Redis sync works', '❌ Missing Int'),
        ],
        'scenario': [
            ('AC-S-001', 'Multi-tenant', '別テナントの管理者としてログインし、他テナントにアクセス', '`403 Forbidden`', '❌ 補充(総合)', 'Access tenant B as admin of tenant A', '403 Forbidden', '❌ Missing Scenario'),
        ]
    },
    'terminal': {
        'unit': [
            ('TM-U-010', 'POST /terminals', '未登録のMACアドレスと店舗IDで新規登録バリデーション', 'DB保存用データ構築確認', '❌ 補充(単体)', 'Register unregistered MAC', 'DB insert data built', '❌ Missing Unit'),
            ('TM-U-011', 'POST /terminals', '登録済みのMACアドレスで重複登録試行', '`409 Conflict` (ビジネスロジック内)', '❌ 補充(単体)', 'Register MAC already bound', '409 Conflict raised', '❌ Missing Unit'),
            ('TM-U-020', 'POST /heartbeat', 'ハートビート更新ロジック', '`last_active_at` 更新', '❌ 補充(単体)', 'Heartbeat reception logic', 'last_active_at updated', '❌ Missing Unit'),
            ('TM-E-002', 'Concurrency', '同一店舗にミリ秒単位で全く同時に「新規登録」', 'ロック機構により片方だけ成功', '❌ 補充(単体)', 'Concurrent registration requested at once', 'Tx lock applies, one 409', '❌ Missing Unit'),
        ],
        'integration': [
            ('TM-E-001', 'Resilience', '`POST /heartbeat` 時に Dapr Redis への接続がダウン', '`503 Service Unavailable` でクラッシュ回避', '❌ 補充(結合)', 'Dapr Redis down during heartbeat', '503 Fail-safe, no crash', '❌ Missing Int'),
        ],
        'scenario': []
    },
    'master-data': {
        'unit': [
            ('MD-U-010', 'GET /items', '存在するJANコードでの商品検索ロジック', '各種情報パース確認', '❌ 補充(単体)', 'Valid JAN code search logic', 'Fields correctly parsed', '❌ Missing Unit'),
            ('MD-U-012', 'PUT /items', '商品の価格改定時の状態破棄処理', 'キャッシュパージロジックが呼ばれる', '❌ 補充(単体)', 'Cache purge on price update logic', 'Purge invoked', '❌ Missing Unit'),
            ('MD-U-020', 'GET /taxes', '有効期間内外の税率フィルタリングロジック', '有効期間内のみ抽出', '❌ 補充(単体)', 'Tax date filtering logic', 'Only active tax filtered', '❌ Missing Unit'),
        ],
        'integration': [
            ('MD-E-002', 'Integrity', 'キャッシュ（Dapr Redis）への保存中にネットワーク障害', 'スプリットブレイン防止(自己復旧)', '❌ 補充(結合)', 'Network failure during Dapr state update', 'Self-healing triggers', '❌ Missing Int'),
        ],
        'scenario': [
            ('MD-E-001', 'Performance', '100,000件の商品データに対する一括キャッシュリフレッシュバッチ', 'OOM起こさず完了', '❌ 補充(総合)', 'Bulk refresh 100K records', 'Completes w/o OOM', '❌ Missing Scenario'),
        ]
    },
    'report': {
        'unit': [
            ('RP-E-001', 'Boundary', '閏年の2月28日〜3月1日にまたがる月次集計', '29日が含まれる', '❌ 補充(単体)', 'Leap year (Feb 29) aggregation logic', 'Feb 29 correctly aggregated', '❌ Missing Unit'),
            ('RP-E-002', 'Timezone', 'タイムゾーンが UTC+9 の環境で 23:59:59 に発生したトランザクション', '当日分として集計', '❌ 補充(単体)', 'Tx at 23:59:59 in UTC+9', 'Aggregated into same day', '❌ Missing Unit'),
        ],
        'integration': [
            ('RP-I-001', 'Report → Journal', 'Z精算（日次締め）実行時のレポート送信(Dapr)', 'Pub/Sub メッセージ構築確認', '❌ 補充(結合)', 'Z-report transmit via Pub/Sub', 'Message built correctly', '❌ Missing Int'),
        ],
        'scenario': []
    },
    'journal': {
        'unit': [
            ('JN-U-012', 'Search Logic', '日付（Date Range）とターミナルIDでの検索パラメータ構築', '正しいクエリ', '❌ 補充(単体)', 'Date/Term_id search parameter building', 'Correct query object', '❌ Missing Unit'),
        ],
        'integration': [
            ('JN-I-002', 'Elasticsearch', 'ジャーナルのRDBMS保存後、全文検索エンジンへの同期', '検索でヒットする', '❌ 補充(結合)', 'Sync to local search engine', 'Hit searchable text', '❌ Missing Int'),
        ],
        'scenario': [
            ('JN-E-001', 'Security', '`GET /search?limit=10000000` のような巨大ページネーション', '`400` ハードリミット', '❌ 補充(総合)', 'Catastrophic pagination (limit=10,000,000)', 'Hard limit applied (400)', '❌ Missing Scenario'),
            ('JN-E-002', 'Edge Case', '5MB を超える超長尺レシートデータ受信', 'OOMせずストリーミング保存', '❌ 補充(総合)', 'Huge 5MB receipt payload', 'Stream saved w/o OOM', '❌ Missing Scenario'),
        ]
    },
    'stock': {
        'unit': [
            ('SK-U-013', 'Concurrency', '同一商品に対する並行する2件の引当リクエスト', 'アトミック減算', '❌ 補充(単体)', 'Concurrent deduction on same item', 'Atomic subtraction applied', '❌ Missing Unit'),
        ],
        'integration': [],
        'scenario': [
            ('SK-E-001', 'Resilience', 'WebSocketクラ切断中に発注アラート', '再接続時に送信', '❌ 補充(総合)', 'WS disconnect during alert trigger', 'Queued & re-sent on connect', '❌ Missing Scenario'),
            ('SK-E-002', 'Concurrency', '残り「1」に 10箇所のレジから完全に同時に引当', '1成功、9失敗', '❌ 補充(総合)', '10 registers deduct stock=1 perfectly concurrently', '1 success, 9 failure replies', '❌ Missing Scenario'),
        ]
    }
}

title_map = {
    'cart': 'Cart', 'terminal': 'Terminal', 'account': 'Account', 
    'master-data': 'Master Data', 'report': 'Report', 'journal': 'Journal', 'stock': 'Stock'
}

order_map = {'cart': 14, 'terminal': 12, 'account': 11, 'master-data': 13, 'report': 15, 'journal': 16, 'stock': 17}

for lang in ['ja', 'en']:
    parent = 'テスト' if lang == 'ja' else 'Testing'
    grand = '日本語' if lang == 'ja' else 'English'
    
    for svc in services:
        order = order_map[svc]
        display_name = title_map[svc]
        
        ex = existing_tests.get(svc, {'unit': [], 'integration': [], 'scenario': []})
        re = recommended_tests.get(svc, {'unit': [], 'integration': [], 'scenario': []})
        
        md = f"""---
title: "{display_name} サービス テストケース"
parent: {parent}
grand_parent: {grand}
nav_order: {order}
layout: default
---

# {display_name} サービス テスト設計書

{"本ドキュメントは、「テスト評審レポート」に基づき構成を最適化したテストケースの設計書です。\n既存の実装テストと、今後の開発において追加すべき「推奨テスト（異常系・エッジケース等）」を「単体(Unit)」「結合(Integration)」「総合(Scenario)」の3つのレベルに明確に分離して定義しています。" if lang == 'ja' else 
"This document is a restructured test case design based on the Test Review Report.\nIt cleanly separates existing implemented tests and recommended supplementary tests (edge cases, negative flows) into three distinct levels: Unit, Integration, and Scenario/E2E."}

---

## 1. サービスの概要とテスト戦略 (Overview & Strategy)
{"各サービスに特有のビジネスロジック、依存関係、およびテストにおける最大のフォーカスポイントに対する全体方針です。" if lang == 'ja' else "Overall policy regarding specific business logic, dependencies, and main test focuses for this service."}

---

## 2. 単体テスト (Unit / ロジック単位)
{"ビジネスロジックが集中する Service 層や Model 層のクラス・関数群を、外部通信（DBやgRPC）から隔離(Mock)して検証します。" if lang == 'ja' else "Validates functions and classes in Service/Model layers isolated from external I/O using Mocks."}

### 2.1 既存のテストケース (test-review.md より抽出実装済)
| {"テストファイル" if lang == 'ja' else "Test File"} | {"カバー内容" if lang == 'ja' else "Coverage Target"} | {"状態" if lang == 'ja' else "Status"} |
|---|---|---|
"""
        if not ex['unit']:
            md += f"| - | {"※現在、単体テストは実装されていません" if lang == 'ja' else "No unit tests currently implemented"} | ❌ |\n"
        for eu in ex['unit']:
            desc = eu[1] if lang == 'ja' else eu[3]
            stat = eu[2] if lang == 'ja' else eu[4]
            md += f"| {eu[0]} | {desc} | {stat} |\n"
            
        md += f"""
### 2.2 推奨・補充テストケース (不足分の強化対象)
| ID | {"ターゲット" if lang == 'ja' else "Target"} | {"テストシナリオ (非機能・異常系含む)" if lang == 'ja' else "Test Scenario"} | {"期待される結果" if lang == 'ja' else "Expected Outcome"} | {"状態" if lang == 'ja' else "Status"} |
|---|---|---|---|---|
"""
        if not re['unit']:
            md += f"| - | - | {"※追加要請の単体テストは現在ありません" if lang == 'ja' else "No recommended unit tests at the moment"} | - | - |\n"
        for ru in re['unit']:
            target, desc, expect, stat = (ru[1], ru[2], ru[3], ru[4]) if lang == 'ja' else (ru[1], ru[5], ru[6], ru[7])
            md += f"| **{ru[0]}** | `{target}` | {desc} | {expect} | {stat} |\n"

        md += f"""
---

## 3. 結合テスト (Integration / サービス間連携)
{"Redis(Dapr StateStore) や 複数サービス間の Pub/Sub メッセージチェーンなど、コンポーネントを実際につなげた状態でのシステム連携を検証します。" if lang == 'ja' else "Validates component combinations, including actual Redis/DB access and Pub/Sub message chains between microservices."}

### 3.1 既存のテストケース (実装済)
| {"テストファイル" if lang == 'ja' else "Test File"} | {"カバー内容" if lang == 'ja' else "Coverage Target"} | {"状態" if lang == 'ja' else "Status"} |
|---|---|---|
"""
        if not ex['integration']:
            md += f"| - | {"※現在、結合テストは実装されていません" if lang == 'ja' else "No integration tests currently implemented"} | ❌ |\n"
        for eu in ex['integration']:
            desc = eu[1] if lang == 'ja' else eu[3]
            stat = eu[2] if lang == 'ja' else eu[4]
            md += f"| {eu[0]} | {desc} | {stat} |\n"
            
        md += f"""
### 3.2 推奨・補充テストケース (不足分の連携強化)
| ID | {"ターゲット" if lang == 'ja' else "Target"} | {"テストシナリオ" if lang == 'ja' else "Test Scenario"} | {"期待される結果" if lang == 'ja' else "Expected Outcome"} | {"状態" if lang == 'ja' else "Status"} |
|---|---|---|---|---|
"""
        if not re['integration']:
            md += f"| - | - | {"※追加要請の結合テストは現在ありません" if lang == 'ja' else "No recommended integration tests at the moment"} | - | - |\n"
        for ru in re['integration']:
            target, desc, expect, stat = (ru[1], ru[2], ru[3], ru[4]) if lang == 'ja' else (ru[1], ru[5], ru[6], ru[7])
            md += f"| **{ru[0]}** | `{target}` | {desc} | {expect} | {stat} |\n"

        md += f"""
---

## 4. 総合テスト (Scenario & E2E / API横断フロー)
{"一連の業務フロー（例：商品追加→値引→キャンセル→決済完了）を、実際の HTTP クライアント経由でエンドツーエンドで検証します。" if lang == 'ja' else "End-to-end validation of business workflows (e.g. entry -> discount -> cancel -> payment) acting via HTTP clients."}

### 4.1 既存のテストケース (実装済)
| {"テストファイル" if lang == 'ja' else "Test File"} | {"カバー内容" if lang == 'ja' else "Coverage Target"} | {"状態" if lang == 'ja' else "Status"} |
|---|---|---|
"""
        if not ex['scenario']:
            md += f"| - | {"※現在、シナリオテストは実装されていません" if lang == 'ja' else "No scenario tests currently implemented"} | ❌ |\n"
        for eu in ex['scenario']:
            desc = eu[1] if lang == 'ja' else eu[3]
            stat = eu[2] if lang == 'ja' else eu[4]
            md += f"| {eu[0]} | {desc} | {stat} |\n"
            
        md += f"""
### 4.2 推奨・補充テストケース (巨大過付加・長期セッション等)
| ID | {"ターゲット" if lang == 'ja' else "Target"} | {"テストシナリオ (非機能含む)" if lang == 'ja' else "Test Scenario"} | {"期待される結果" if lang == 'ja' else "Expected Outcome"} | {"状態" if lang == 'ja' else "Status"} |
|---|---|---|---|---|
"""
        if not re['scenario']:
            md += f"| - | - | {"※追加要請のシナリオエッジケースは現在ありません" if lang == 'ja' else "No recommended scenario tests at the moment"} | - | - |\n"
        for ru in re['scenario']:
            target, desc, expect, stat = (ru[1], ru[2], ru[3], ru[4]) if lang == 'ja' else (ru[1], ru[5], ru[6], ru[7])
            md += f"| **{ru[0]}** | `{target}` | {desc} | {expect} | {stat} |\n"

        filepath = os.path.join(base, lang, 'testing', f'testcases-{svc}.md')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md)

print("Testcases successfully restructured by Unit/Integration/Scenario levels for all services.")

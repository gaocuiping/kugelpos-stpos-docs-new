# ユーザストーリー2: トランザクションデータのクラウド集約 - 処理フロー図

## 概要

このドキュメントは、ユーザストーリー2「トランザクションデータのクラウド集約」の処理フローを視覚的に説明します。店舗のレジ端末で発生したトランザクションデータ（売上、返品、入出金等）がクラウドに送信され、本部での売上分析やレポート生成が可能になる仕組みを図解します。

## シナリオ

店舗のレジ端末で発生した売上取引、返品、入出金などのトランザクションデータが、リアルタイムでクラウドに送信され、本部での売上分析やレポート生成が可能になる。トランザクションデータには電子ジャーナル情報（journal_textフィールド）も含まれており、クラウド側でDapr Pub/Subを通じてJournal Serviceへ自動配信される。

## 主要コンポーネント

```mermaid
graph TB
    subgraph Edge["🏪 店舗環境（エッジ）"]
        POS["POS端末<br/>（販売・返品）"]
        Cart["Cart Service<br/>（取引処理）"]
        Terminal["Terminal Service<br/>（開設精算・入出金）"]
        EdgeSync["Sync Service<br/>（Edge Mode）"]
        EdgeDB[("MongoDB<br/>log_tran_pending")]
    end

    subgraph Cloud["☁️ クラウド環境"]
        CloudSync["Sync Service<br/>（Cloud Mode）"]
        CloudCart["Cart Service<br/>（取引処理）"]
        CloudTerminal["Terminal Service<br/>（開設精算・入出金）"]
        Report["Report Service<br/>（売上分析）"]
        Journal["Journal Service<br/>（電子ジャーナル）"]
        CloudDB[("MongoDB<br/>sync_tenant001")]
        Redis[("Redis<br/>Pub/Sub")]
    end

    POS --> Cart
    POS --> Terminal
    Cart -->|Pub/Sub<br/>tranlog_report| EdgeSync
    Terminal -->|Pub/Sub<br/>opencloselog_report<br/>cashlog_report| EdgeSync
    EdgeSync --> EdgeDB
    EdgeSync -->|REST API<br/>POST /api/v1/sync/transaction-logs| CloudSync
    CloudSync --> CloudDB
    CloudSync -->|Pub/Sub<br/>tranlog_report| Redis
    CloudSync -->|Pub/Sub<br/>opencloselog_report| Redis
    CloudSync -->|Pub/Sub<br/>cashlog_report| Redis
    Redis --> CloudCart
    Redis --> CloudTerminal
    Redis --> Report
    Redis --> Journal
```

## トランザクションログの種類

### log_type別のデータフロー

| log_type | 日本語名 | ソース | Pub/Subトピック | 含まれるデータ |
|----------|---------|--------|----------------|--------------|
| **transaction** | 取引ログ | Cart Service | `tranlog_report` | 売上取引、返品、値引き、商品明細、決済方法、journal_text |
| **opening_closing** | 開設精算ログ | Terminal Service | `opencloselog_report` | レジ開設・精算、開設金額、売上金額、差異、journal_text |
| **cash_inout** | 入出金ログ | Terminal Service | `cashlog_report` | 入金・出金、金額、理由、承認者、journal_text |

**共通フィールド**: すべてのlog_typeに `journal_text`（電子ジャーナル）と `receipt_text`（レシート）が含まれます。

## 処理フロー全体

### フロー1: リアルタイムトランザクション送信（オンライン時）

POS端末で取引が完了した際の、リアルタイム送信フローです。

```mermaid
sequenceDiagram
    participant POS as 🛒 POS端末
    participant Cart as Cart Service
    participant EdgeSync as 🏪 Edge Sync
    participant EdgeDB as Edge MongoDB
    participant CloudSync as ☁️ Cloud Sync
    participant Redis as Redis Pub/Sub
    participant Report as Report Service
    participant Journal as Journal Service

    Note over POS,Journal: 💳 リアルタイム取引処理

    rect rgb(240, 240, 255)
        Note right of POS: 1. 取引実行
        POS->>+Cart: 商品スキャン・決済実行
        Cart->>Cart: BaseTransaction作成<br/>（商品明細、金額、決済方法、<br/>journal_text、receipt_text）
        Cart->>Cart: データベース保存
    end

    rect rgb(255, 250, 240)
        Note right of Cart: 2. Pub/Sub通知（エッジ内）
        Cart->>EdgeSync: Dapr Pub/Sub<br/>Topic: tranlog_report<br/>{log_type: "transaction", data: {...}, journal_text: "..."}
        Note over EdgeSync: イベント受信<br/>（非同期処理）
    end

    rect rgb(240, 255, 240)
        Note right of EdgeSync: 3. ローカルキューイング
        EdgeSync->>EdgeSync: TransactionLog作成<br/>（log_id: UUID生成）
        EdgeSync->>EdgeDB: 保存<br/>Collection: log_tran_pending<br/>sync_status: "pending"
    end

    rect rgb(255, 240, 240)
        Note right of EdgeSync: 4. 定期送信（30-60秒間隔）
        EdgeSync->>EdgeDB: pending ログ取得<br/>WHERE sync_status = 'pending'<br/>ORDER BY occurred_at ASC<br/>LIMIT 100
        EdgeDB-->>EdgeSync: 未送信ログ（100件）

        EdgeSync->>EdgeSync: データ圧縮（gzip）<br/>圧縮率: 60-80%
        EdgeSync->>+CloudSync: POST /api/v1/sync/transaction-logs<br/>Authorization: Bearer <token><br/>Content-Encoding: gzip<br/>[{log_id, log_type, occurred_at, data, journal_text}, ...]
    end

    rect rgb(240, 255, 255)
        Note right of CloudSync: 5. クラウド受信・Pub/Sub配信
        CloudSync->>CloudSync: データ解凍・検証
        CloudSync->>CloudSync: log_type 判別

        par 並行配信
            CloudSync->>Redis: Pub/Sub Publish<br/>Topic: tranlog_report<br/>（log_type: "transaction"）
            CloudSync->>Redis: Pub/Sub Publish<br/>Topic: opencloselog_report<br/>（log_type: "opening_closing"）
            CloudSync->>Redis: Pub/Sub Publish<br/>Topic: cashlog_report<br/>（log_type: "cash_inout"）
        end

        CloudSync-->>-EdgeSync: 送信成功<br/>{received_count: 100}
    end

    rect rgb(240, 255, 240)
        Note right of EdgeSync: 6. 送信完了マーク
        EdgeSync->>EdgeDB: ステータス更新<br/>sync_status: "sent"<br/>synced_at: now
    end

    rect rgb(255, 255, 240)
        Note right of Redis: 7. 各サービスで処理
        Redis->>CloudCart: tranlog_report 受信<br/>（クラウド側でトランザクション保存）
        Redis->>CloudTerminal: opencloselog_report / cashlog_report 受信<br/>（クラウド側で開設精算・入出金保存）
        Redis->>Report: 各種ログ受信<br/>（売上分析用）
        Redis->>Journal: journal_text 抽出<br/>（電子ジャーナル保存）
        CloudCart->>CloudCart: トランザクションログ保存<br/>（クラウド側MongoDB）
        CloudTerminal->>CloudTerminal: 開設精算・入出金ログ保存<br/>（クラウド側MongoDB）
        Report->>Report: 日次売上集計<br/>レポート生成
        Journal->>Journal: ジャーナル保存<br/>（法的保管要件対応）
    end

    Note over POS,Journal: ✅ 取引データがクラウドに集約完了（60秒以内）
```

**所要時間**: 60秒以内（取引発生 → クラウド反映）

**主要ステップ**:
1. **取引実行**: POS端末で商品スキャン・決済完了
2. **Pub/Sub通知**: Cart/Terminalサービスが既存トピックでイベント発行
3. **ローカルキューイング**: Edge Syncがローカルデータベースに一時保存
4. **定期送信**: 30-60秒間隔でバッチ送信（最大100件/回）
5. **クラウド配信**: log_type別にPub/Subトピックへ振り分け
6. **送信完了**: Edge側でステータスを `sent` に更新
7. **各サービス処理**: Report ServiceとJournal Serviceが非同期処理

### フロー2: オフライン時のトランザクション蓄積・復旧後送信

ネットワーク障害時の動作とオンライン復旧後の自動送信フローです。

```mermaid
sequenceDiagram
    participant POS as 🛒 POS端末
    participant Cart as Cart Service
    participant EdgeSync as 🏪 Edge Sync
    participant EdgeDB as Edge MongoDB
    participant CloudSync as ☁️ Cloud Sync

    Note over POS,CloudSync: 🔌 ネットワーク障害発生

    rect rgb(255, 240, 240)
        Note right of POS: 1. オフライン時の取引継続
        POS->>Cart: 取引実行（通常通り）
        Cart->>Cart: ローカルDB保存
        Cart->>EdgeSync: Pub/Sub通知<br/>（エッジ内のみ）
        EdgeSync->>EdgeDB: TransactionLog保存<br/>sync_status: "pending"

        Note over EdgeSync: 取引データは<br/>ローカルDBに蓄積
    end

    rect rgb(255, 245, 240)
        Note right of EdgeSync: 2. 送信試行・失敗
        loop 定期送信タイミング（30-60秒）
            EdgeSync->>CloudSync: ❌ POST /api/v1/sync/transaction-logs<br/>（接続失敗）
            EdgeSync->>EdgeSync: リトライカウント増加<br/>retry_count++
            EdgeSync->>EdgeDB: ステータス更新<br/>sync_status: "failed"<br/>retry_count: 1, 2, 3...
        end

        Note over EdgeSync: ⚠️ サーキットブレーカー<br/>連続3回失敗でオープン
    end

    rect rgb(255, 255, 240)
        Note right of EdgeDB: 3. ローカルキュー管理
        EdgeDB->>EdgeDB: 全ログ件数確認<br/>COUNT(*)

        alt キュー容量内（< 10,000件）
            Note over EdgeDB: ✅ データ保持継続
        else キュー容量超過（≥ 10,000件）
            EdgeDB->>EdgeDB: ⚠️ 送信済みの古いログから削除<br/>DELETE WHERE sync_status='sent'<br/>ORDER BY synced_at ASC<br/>LIMIT 1000
            Note over EdgeDB: 送信済みの最も古い1000件を削除<br/>（未送信データは保持）
        end
    end

    rect rgb(240, 255, 240)
        Note right of EdgeSync: 4. ネットワーク復旧
        Note over EdgeSync: ⚡ 復旧検知<br/>（最初の成功したHTTPリクエスト）

        EdgeSync->>+CloudSync: GET /health
        CloudSync-->>-EdgeSync: ✅ {"status": "healthy"}

        Note over EdgeSync: 🔓 サーキットブレーカー<br/>半開状態

        EdgeSync->>CloudSync: POST /api/v1/auth/token<br/>（トークン再取得）
        CloudSync-->>EdgeSync: JWT トークン
    end

    rect rgb(240, 245, 255)
        Note right of EdgeSync: 5. 蓄積データの一括送信（復旧後30秒以内）
        EdgeSync->>EdgeDB: pending ログ全件取得<br/>WHERE sync_status='pending'<br/>ORDER BY occurred_at ASC
        EdgeDB-->>EdgeSync: 蓄積ログ（例: 500件）

        loop バッチ送信（100件ずつ）
            EdgeSync->>EdgeSync: データ圧縮（gzip）
            EdgeSync->>+CloudSync: POST /api/v1/sync/transaction-logs<br/>Content-Encoding: gzip<br/>Batch 1/5（100件）
            CloudSync-->>-EdgeSync: 送信成功

            EdgeSync->>EdgeDB: ステータス更新<br/>sync_status: "sent"<br/>synced_at: now
        end
    end

    Note over POS,CloudSync: ✅ オフライン期間のデータ送信完了
```

**復旧時の動作**:
- **復旧検知**: 最初の成功したHTTPリクエスト完了時点
- **自動再開**: 復旧後30秒以内に蓄積データ送信開始
- **バッチ送信**: 100件ずつに分割して順次送信
- **キュー管理**: 容量超過時は送信済み（`sync_status='sent'`）の古いデータから削除、未送信データ（`pending`）は確実に保持（デフォルト: 10,000件または100MB）

**主要ステップ**:
1. **オフライン時取引**: 通常通りPOS業務継続、ローカルDB保存
2. **送信試行失敗**: 定期送信タイミングで接続失敗、リトライ
3. **キュー管理**: 容量監視、超過時は古いデータ削除
4. **復旧検知**: ヘルスチェック成功でネットワーク復旧を検知
5. **一括送信**: 蓄積データを100件ずつバッチ送信

### フロー3: リトライ機構（指数バックオフ）

送信失敗時の自動リトライフローです。

```mermaid
sequenceDiagram
    participant EdgeSync as 🏪 Edge Sync
    participant EdgeDB as Edge MongoDB
    participant CloudSync as ☁️ Cloud Sync

    Note over EdgeSync,CloudSync: 🔄 リトライ機構

    rect rgb(255, 245, 240)
        Note right of EdgeSync: 1. 初回送信失敗
        EdgeSync->>+CloudSync: POST /api/v1/sync/transaction-logs
        CloudSync-->>-EdgeSync: ❌ 500 Internal Server Error

        EdgeSync->>EdgeDB: ステータス更新<br/>sync_status: "failed"<br/>retry_count: 1<br/>error_message: "500 error"
    end

    rect rgb(255, 250, 240)
        Note right of EdgeSync: 2. リトライ1回目（1秒後）
        EdgeSync->>EdgeSync: 待機: 1秒
        EdgeSync->>+CloudSync: リトライ1回目
        CloudSync-->>-EdgeSync: ❌ 503 Service Unavailable

        EdgeSync->>EdgeDB: retry_count: 2
    end

    rect rgb(255, 250, 245)
        Note right of EdgeSync: 3. リトライ2回目（2秒後）
        EdgeSync->>EdgeSync: 待機: 2秒
        EdgeSync->>+CloudSync: リトライ2回目
        CloudSync-->>-EdgeSync: ❌ Timeout

        EdgeSync->>EdgeDB: retry_count: 3
    end

    rect rgb(255, 252, 245)
        Note right of EdgeSync: 4. リトライ3回目（4秒後）
        EdgeSync->>EdgeSync: 待機: 4秒
        EdgeSync->>+CloudSync: リトライ3回目
        CloudSync-->>-EdgeSync: ✅ 200 OK

        EdgeSync->>EdgeDB: ステータス更新<br/>sync_status: "sent"<br/>retry_count: 0（リセット）
    end

    Note over EdgeSync,CloudSync: ✅ リトライ成功

    alt リトライ5回失敗
        Note over EdgeSync: ⚠️ 最大リトライ超過<br/>retry_count = 5
        EdgeSync->>EdgeDB: sync_status: "failed"<br/>retry_count: 5
        EdgeSync->>EdgeSync: エラーログ記録<br/>管理者通知
    end
```

**指数バックオフ戦略**:
- **リトライ間隔**: 1秒 → 2秒 → 4秒 → 8秒 → 16秒
- **最大リトライ回数**: 5回
- **成功時**: retry_count を 0 にリセット
- **5回失敗時**: エラーログ記録、管理者通知

### フロー4: journal_text の配信（Journal Serviceへ）

トランザクションログに含まれる電子ジャーナルデータの配信フローです。

```mermaid
sequenceDiagram
    participant Edge as 🏪 Edge Sync
    participant Cloud as ☁️ Cloud Sync
    participant Redis as Redis Pub/Sub
    participant Journal as Journal Service
    participant JournalDB as Journal MongoDB

    Note over Edge,JournalDB: 📜 電子ジャーナル配信

    rect rgb(240, 255, 240)
        Note right of Edge: 1. トランザクションログ送信
        Edge->>+Cloud: POST /api/v1/sync/transaction-logs<br/>[{<br/>  log_id: "uuid-001",<br/>  log_type: "transaction",<br/>  occurred_at: "2025-10-14T10:30:00Z",<br/>  data: {<br/>    transaction_id: "TXN-12345",<br/>    items: [...],<br/>    total_amount: 3500,<br/>    journal_text: "=== 電子ジャーナル ===\n...",<br/>    receipt_text: "=== レシート ===\n..."<br/>  }<br/>}]
    end

    rect rgb(240, 245, 255)
        Note right of Cloud: 2. log_type 判別・Pub/Sub配信
        Cloud->>Cloud: log_type 確認<br/>"transaction" → tranlog_report<br/>"opening_closing" → opencloselog_report<br/>"cash_inout" → cashlog_report

        Cloud->>Redis: Pub/Sub Publish<br/>Topic: tranlog_report<br/>Payload: {log_id, log_type, data: {...}}
        Cloud-->>-Edge: 送信成功
    end

    rect rgb(255, 250, 240)
        Note right of Redis: 3. Journal Service 受信
        Redis->>+Journal: Subscribe: tranlog_report<br/>（非同期イベント受信）

        Journal->>Journal: journal_text 抽出<br/>data.journal_text<br/>data.receipt_text
    end

    rect rgb(240, 255, 255)
        Note right of Journal: 4. ジャーナル保存
        Journal->>JournalDB: Journal保存<br/>Collection: journal<br/>{<br/>  journal_id: UUID,<br/>  transaction_id: "TXN-12345",<br/>  occurred_at: "2025-10-14T10:30:00Z",<br/>  journal_text: "...",<br/>  receipt_text: "...",<br/>  log_type: "transaction"<br/>}

        Journal-->>-Redis: Ack（処理完了）
    end

    Note over Edge,JournalDB: ✅ 電子ジャーナル保存完了（法的保管要件対応）
```

**journal_text の流れ**:
1. **Edge側**: Cart/Terminal ServiceがBaseTransactionやOpenCloseLogに `journal_text` を含めてPub/Sub発行
2. **Edge Sync**: TransactionLogとしてローカルDB保存、クラウドへ送信
3. **Cloud Sync**: 受信後、log_type別にPub/Subトピックへ振り分け
4. **Journal Service**: Pub/Sub経由で受信、journal_textを抽出してMongoDB保存

**メリット**:
- **単一データフロー**: トランザクションデータとジャーナルデータを別々に同期する必要なし
- **At-least-once delivery**: トランザクション送信のリトライ機構がジャーナルにも適用
- **リアルタイム性**: Pub/Sub経由で即座にJournal Serviceへ配信

## データベース構造

### TransactionLog（送信キュー）

エッジ側でクラウド送信待ちのトランザクションログを管理：

```
コレクション: log_tran_pending

ドキュメント例:
{
  "_id": ObjectId("..."),
  "log_id": "550e8400-e29b-41d4-a716-446655440000",
  "edge_id": "edge-tenant001-store001-001",
  "log_type": "transaction",
  "occurred_at": ISODate("2025-10-14T10:30:00Z"),
  "data": {
    "transaction_id": "TXN-12345",
    "store_code": "store001",
    "terminal_no": "1",
    "items": [
      {"product_id": "P001", "quantity": 2, "price": 1000},
      {"product_id": "P002", "quantity": 1, "price": 1500}
    ],
    "total_amount": 3500,
    "payment_method": "cash",
    "journal_text": "=== 電子ジャーナル ===\n取引番号: TXN-12345\n...",
    "receipt_text": "=== レシート ===\nありがとうございました\n..."
  },
  "sync_status": "pending",  // pending, sending, sent, failed
  "synced_at": null,
  "retry_count": 0,
  "error_message": null,
  "created_at": ISODate("2025-10-14T10:30:05Z"),
  "updated_at": ISODate("2025-10-14T10:30:05Z")
}
```

**インデックス**:
- `{sync_status: 1, occurred_at: 1}` - 送信キュー検索用
- `{log_id: 1}` (unique) - 冪等性保証
- `{synced_at: 1}` (TTL: 30日) - 古いデータ自動削除

### SyncStatus（送信状態管理）

トランザクションログ送信の状態を追跡：

```
コレクション: status_sync

ドキュメント例:
{
  "_id": ObjectId("..."),
  "edge_id": "edge-tenant001-store001-001",
  "data_type": "transaction_log",
  "last_sync_at": ISODate("2025-10-14T10:30:00Z"),
  "sync_type": "incremental",
  "status": "success",
  "retry_count": 0,
  "error_message": null,
  "next_sync_at": ISODate("2025-10-14T10:31:00Z")
}
```

## パフォーマンス指標

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| **送信遅延** | 60秒以内 | 取引発生（occurred_at） → クラウド受信完了までの時間 |
| **At-least-once delivery** | 100%保証 | リトライ機構により全トランザクションが最低1回配信 |
| **バッチサイズ** | 最大100件/回 | 定期送信時のバッチサイズ |
| **送信間隔** | 30-60秒 | ポーリング間隔（環境変数 `SYNC_POLL_INTERVAL`） |
| **データ圧縮率** | 50%以上（gzip） | 圧縮前サイズ vs 圧縮後サイズ |
| **復旧後再開時間** | 30秒以内 | ネットワーク復旧検知 → 送信再開までの時間 |
| **キュー容量** | 10,000件または100MB | 容量超過時は送信済みデータから削除（未送信データは保持） |

## エラーハンドリング

### At-least-once Delivery保証

```mermaid
graph TD
    A[トランザクション発生] --> B[ローカルDB保存<br/>sync_status: pending]
    B --> C{送信成功?}
    C -->|Yes| D[sync_status: sent]
    C -->|No| E{retry_count < 5?}
    E -->|Yes| F[指数バックオフ待機]
    F --> G[リトライ]
    G --> C
    E -->|No| H[⚠️ 最大リトライ超過<br/>エラーログ記録]
    D --> I[✅ 配信保証完了]
    H --> J[管理者通知<br/>手動介入]
```

**保証メカニズム**:
1. **ローカルDB永続化**: トランザクション発生時に必ずローカルDB保存
2. **ステータス管理**: `pending` → `sent` の遷移で送信状況を追跡
3. **リトライ機構**: 最大5回の自動リトライ
4. **冪等性**: `log_id`（UUID）で重複配信を防止
5. **ガベージコレクション**: 30日経過した `sent` レコードを自動削除（キュー容量超過時は即座に削除対象）
6. **未送信データ保護**: キュー容量超過時も `sync_status='pending'` のデータは削除せず確実に送信

### サーキットブレーカー

オフライン状態での無駄なリトライを防止：

```mermaid
stateDiagram-v2
    [*] --> Closed: 初期状態
    Closed --> Open: 連続3回失敗
    Open --> HalfOpen: 60秒経過
    HalfOpen --> Closed: 送信成功
    HalfOpen --> Open: 送信失敗

    note right of Closed: 通常動作<br/>すべてのリクエスト実行
    note right of Open: 回路開放<br/>送信スキップ（リソース節約）
    note right of HalfOpen: 復旧テスト<br/>1件のみ送信して判定
```

**動作**:
- **Closed（閉）**: 通常動作、すべての送信リクエスト実行
- **Open（開）**: 連続3回失敗で開放、送信スキップ
- **Half-Open（半開）**: 60秒後に1件テスト送信、成功なら通常復帰

## 受入シナリオの検証

### シナリオ1: リアルタイム送信

```
Given: エッジ端末で売上取引を完了
When: 60秒経過後
Then: クラウド側でトランザクションデータが参照可能、かつjournal_textがJournal Serviceに配信済み

検証方法:
1. POS端末で売上取引実行（商品2点、合計3,500円）
2. Cart ServiceがPub/Sub発行 → Edge Syncが受信
3. 60秒待機
4. Cloud SyncのMongoDBを確認（SyncHistory）
5. Journal ServiceのMongoDBを確認（journal_textが保存されていること）
```

### シナリオ2: オフライン時の蓄積・復旧後送信

```
Given: エッジ端末がオフライン状態
When: トランザクションを実行
Then: ローカルDBに保存され、オンライン復旧後に自動送信

検証方法:
1. Edge SyncのネットワークをOFF
2. POS端末で取引10件実行
3. Edge MongoDBのlog_tran_pendingを確認（10件、sync_status: pending）
4. ネットワークをON
5. 復旧後30秒以内に全10件が送信完了（sync_status: sent）
```

### シナリオ3: バッチ処理

```
Given: 複数の取引ログが蓄積
When: 定期送信タイミング到達
Then: バッチ処理で一括送信され、送信完了ステータスに更新

検証方法:
1. Edge側でトランザクションログ150件を作成（sync_status: pending）
2. 定期送信タイミング（30-60秒）待機
3. バッチ1（100件）送信 → sync_status: sent
4. バッチ2（50件）送信 → sync_status: sent
5. 全150件の送信完了を確認
```

### シナリオ4: リトライ機構

```
Given: 送信失敗したトランザクション
When: リトライ機構が動作
Then: 最大5回まで指数バックオフでリトライ

検証方法:
1. Cloud Syncを一時停止（送信失敗をシミュレート）
2. Edge Syncでトランザクション送信試行 → 失敗
3. リトライ動作確認:
   - 1秒後にリトライ1回目 → 失敗（retry_count: 1）
   - 2秒後にリトライ2回目 → 失敗（retry_count: 2）
   - 4秒後にリトライ3回目 → 失敗（retry_count: 3）
4. Cloud Syncを再起動
5. リトライ4回目 → 成功（sync_status: sent, retry_count: 0）
```

### シナリオ5: log_type別配信

```
Given: log_type別のトランザクションログ（transaction/opening_closing/cash_inout）
When: クラウド受信後
Then: log_typeに応じた適切なDapr Pub/Subトピックに振り分けられJournal Serviceで処理

検証方法:
1. 3種類のトランザクション作成:
   - transaction（Cart Service）
   - opening_closing（Terminal Service）
   - cash_inout（Terminal Service）
2. Edge Sync → Cloud Sync 送信
3. Cloud SyncのログでPub/Sub配信確認:
   - transaction → tranlog_report
   - opening_closing → opencloselog_report
   - cash_inout → cashlog_report
4. Journal Serviceで全3種類のjournal_textが保存されていることを確認
```

## 関連ドキュメント

- [spec.md](../spec.md) - 機能仕様書
- [plan.md](../plan.md) - 実装計画
- [data-model.md](../data-model.md) - データモデル設計
- [contracts/sync-api.yaml](../contracts/sync-api.yaml) - 同期API仕様
- [us-001-flow.md](./us-001-flow.md) - ユーザストーリー1（マスタデータ同期）

---

**ドキュメントバージョン**: 1.0.0
**最終更新日**: 2025-10-14
**ステータス**: 完成

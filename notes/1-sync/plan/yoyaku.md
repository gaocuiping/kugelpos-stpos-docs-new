# マスタデータ予約反映システム 実装プラン

## 1. システム概要

マスタデータ管理サーバ（Mサーバ）から店舗単位で配信されるマスタファイルを事前受信し、ファイル名に含まれる反映日時に自動更新を実行する機能を実装する。全店共通マスタ（店舗ID=COMMON）は全店舗に配信される。

### 1.1 システム構成の拡張

```mermaid
graph TB
    subgraph "Master Data Management Server (M Server)"
        MS[Master Data Management]
        MDB[(Master DB)]
        MFS[File Repository]
        MS --> MDB
        MS --> MFS
    end
    
    subgraph "Cloud Environment"
        CS[Sync Service<br/>Cloud Mode]
        CSR[Scheduled Reflection<br/>Manager]
        CSFS[Staged Files<br/>Storage]
        CM[MongoDB Cloud]
        CSAPI[Sync API<br/>Endpoint]
        
        CS --> CSR
        CSR --> CSFS
        CSR --> CM
        CS --> CSAPI
        CSAPI --> CSFS
    end
    
    subgraph "Edge Environment A (Store 001)"
        ESA[Sync Service<br/>Edge Mode]
        ESRA[Scheduled Reflection<br/>Manager]
        ESFSA[Staged Files<br/>Storage]
        EMA[MongoDB Edge]
        ESAAPI[Sync Client<br/>API Caller]
        
        ESA --> ESRA
        ESRA --> ESFSA
        ESRA --> EMA 
        ESA --> ESAAPI
        ESAAPI --> ESFSA
    end
    
    subgraph "Edge Environment B (Store 002)"
        ESB[Sync Service<br/>Edge Mode]
        ESRB[Scheduled Reflection<br/>Manager]
        ESFSB[Staged Files<br/>Storage]
        EMB[MongoDB Edge]
        ESBAPI[Sync Client<br/>API Caller]
        
        ESB --> ESRB
        ESRB --> ESFSB
        ESRB --> EMB
        ESB --> ESBAPI
        ESBAPI --> ESFSB
    end
    
    MS -->|File Distribution<br/>202501011200_T_01_ITEM01_20250115123456_A_S001.json<br/>202501011200_T_01_ITEM01_20250115123456_A_S002.json<br/>202501011200_T_01_CATEG1_20250115123456_A_SCOMMON.json| CS
    
    ESAAPI -.->|1. Sync Request<br/>GET /api/sync/files?store_id=001| CSAPI
    CSAPI -.->|2. File List Response<br/>file_info_list| ESAAPI
    ESAAPI -.->|3. File Download<br/>GET /api/files/FILE_ID| CSAPI
    CSAPI -.->|4. File Content| ESAAPI
    
    ESBAPI -.->|1. Sync Request<br/>GET /api/sync/files?store_id=002| CSAPI
    CSAPI -.->|2. File List Response<br/>file_info_list| ESBAPI
    ESBAPI -.->|3. File Download<br/>GET /api/files/FILE_ID| CSAPI
    CSAPI -.->|4. File Content| ESBAPI
    
    style MS fill:#f99,stroke:#333,stroke-width:4px
    style CSR fill:#9f9,stroke:#333,stroke-width:3px
    style CSAPI fill:#9f9,stroke:#333,stroke-width:3px
    style ESRA fill:#99f,stroke:#333,stroke-width:3px
    style ESRB fill:#99f,stroke:#333,stroke-width:3px
    style ESAAPI fill:#99f,stroke:#333,stroke-width:3px
    style ESBAPI fill:#99f,stroke:#333,stroke-width:3px
```

## 2. ファイル命名規則（Mサーバ仕様）

### 2.1 ファイル名構成

```
[マスタ反映日時]_[更新タイミング]_[反映優先順位]_[ファイルID]_[マスタ作成日時]_[更新区分]_S[店舗ID].json

店舗固有マスタ例：202501011200_T_01_ITEM01_20250115123456_A_S001.json
全店共通マスタ例：202501011200_T_01_CATEG1_20250115123456_A_SCOMMON.json
```

### 2.2 各項目の詳細

| 項目名 | 内容 | 桁数 | フォーマット | 例 |
|--------|------|------|-------------|-----|
| マスタ反映日時 | マスタが反映される日付・時刻 | 12 | YYYYMMDDHHMM | 202501011200 |
| 更新タイミング | マスタ反映のタイミング種別 | 1 | S/T | T |
| 反映優先順位 | 同一日時反映時の優先順位 | 2 | 数値 | 01 |
| ファイルID | マスタレイアウトの識別子 | 6 | 英数字 | ITEM01 |
| マスタ作成日時 | マスタが作成された日時 | 14 | YYYYMMDDHHMMSS | 20250115123456 |
| 更新区分 | 更新処理の種別 | 1 | A/M | A |
| 店舗ID | 対象店舗の識別子 | 6 | 数値/COMMON | 001/COMMON |

### 2.3 店舗ID定義

- **001-999**: 店舗固有マスタ（該当店舗のみに配信）
- **COMMON**: 全店共通マスタ（全店舗に配信）

## 3. データベース設計

### 3.1 予約反映管理テーブル（`scheduled_master_updates`）

````python
class ScheduledMasterUpdateDocument(AbstractDocument):
    """予約反映管理ドキュメント"""
    
    tenant_id: str
    store_id: str                     # 店舗ID（ファイル名から抽出、COMMONも含む）
    file_name: str                    # 受信ファイル名（完全なファイル名）
    
    # ファイル名から解析される項目
    scheduled_datetime: datetime      # マスタ反映日時（YYYYMMDDHHMM）
    update_timing: str               # 更新タイミング（S/T）
    priority: int                    # 反映優先順位（01-99）
    file_id: str                     # ファイルID（6桁英数字）
    created_datetime: datetime       # マスタ作成日時（YYYYMMDDHHMMSS）
    update_type: str                 # 更新区分（A/M）
    
    # システム管理項目
    status: str                      # pending/processing/completed/failed/cancelled
    file_path: str                   # ステージングファイルパス
    file_hash: str                   # ファイル整合性チェック用
    received_at: datetime            # ファイル受信日時
    processed_at: Optional[datetime] # 処理完了日時
    error_message: Optional[str]     # エラーメッセージ
    retry_count: int                 # リトライ回数
    
    # 配信対象
    is_common_master: bool           # True: 全店共通, False: 店舗固有
    target_store_id: Optional[str]   # 実際の配信対象店舗ID（Edge環境での実行時店舗ID）
    
    class Config:
        collection = "scheduled_master_updates"
        indexes = [
            {"keys": [("tenant_id", 1), ("store_id", 1), ("scheduled_datetime", 1)]},
            {"keys": [("tenant_id", 1), ("target_store_id", 1), ("scheduled_datetime", 1)]},
            {"keys": [("status", 1), ("scheduled_datetime", 1)]},
            {"keys": [("file_id", 1), ("scheduled_datetime", 1)]},
            {"keys": [("priority", 1)]},
            {"keys": [("is_common_master", 1)]},
        ]
````

### 3.2 配信ロジック仕様

#### 3.2.1 Cloud環境での配信処理

1. **受信**: Mサーバからファイルを受信
2. **解析**: ファイル名から店舗IDを抽出
3. **保存**: Staged Files Storageに保存
4. **登録**: scheduled_master_updatesテーブルに登録

#### 3.2.2 Edge-Cloud間同期フロー

```mermaid
sequenceDiagram
    participant Edge as Edge Sync Service
    participant Cloud as Cloud Sync API
    participant Storage as Cloud File Storage
    participant DB as Cloud MongoDB
    
    Note over Edge: 定期同期実行（例：5分間隔）
    
    Edge->>Cloud: GET /api/sync/files?store_id=001&last_sync=timestamp
    Cloud->>DB: 該当店舗の未取得ファイル検索
    DB-->>Cloud: ファイル情報リスト
    Cloud-->>Edge: レスポンス: [{file_id, file_name, scheduled_datetime, ...}]
    
    loop 各配信ファイル
        Edge->>Cloud: GET /api/files/{file_id}
        Cloud->>Storage: ファイル取得
        Storage-->>Cloud: ファイル内容
        Cloud-->>Edge: ファイル内容
        Edge->>Edge: ローカルファイル保存
        Edge->>Edge: scheduled_master_updatesに登録
    end
    
    Edge->>Cloud: POST /api/sync/ack (取得完了通知)
    Cloud->>DB: 配信状態更新
```

## 4. API仕様

### 4.1 同期ファイル一覧取得API

```
GET /api/sync/files?store_id={store_id}&last_sync={timestamp}
```

**パラメータ:**
- `store_id`: 店舗ID
- `last_sync`: 最後の同期タイムスタンプ（オプション）

**レスポンス:**
```json
{
  "files": [
    {
      "file_id": "uuid-string",
      "file_name": "202501011200_T_01_ITEM01_20250115123456_A_S001.json",
      "scheduled_datetime": "2025-01-01T12:00:00Z",
      "update_timing": "T",
      "priority": 1,
      "file_id_code": "ITEM01",
      "created_datetime": "2025-01-15T12:34:56Z",
      "update_type": "A",
      "store_id": "001",
      "file_hash": "sha256-hash",
      "file_size": 1024
    }
  ],
  "total_count": 1,
  "sync_timestamp": "2025-01-15T15:30:00Z"
}
```

### 4.2 ファイル取得API

```
GET /api/files/{file_id}
```

**レスポンス:**
- Content-Type: application/json
- ファイル内容（バイナリ）

### 4.3 取得完了通知API

```
POST /api/sync/ack
```

**リクエストボディ:**
```json
{
  "store_id": "001",
  "downloaded_files": [
    {
      "file_id": "uuid-string",
      "download_timestamp": "2025-01-15T15:35:00Z",
      "file_hash": "sha256-hash"
    }
  ]
}
```

## 5. Edge環境でのスケジュール実行仕様

### 5.1 同期処理スケジュール

- **同期間隔**: 5分間隔
- **リトライ**: 3回まで（指数バックオフ）
- **タイムアウト**: 30秒

### 5.2 反映処理スケジュール

- **チェック間隔**: 1分間隔
- **実行条件**: `scheduled_datetime <= 現在時刻 AND status = 'pending'`
- **優先順位**: `priority`昇順で実行
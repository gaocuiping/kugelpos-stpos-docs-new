# シーケンス図 - コンポーネント間相互作用

## 1. エッジ端末の起動・更新シーケンス

```mermaid
sequenceDiagram
    participant ES as edge-startup.sh
    participant SYNC as Sync Service<br/>(Cloud)
    participant ACR as Azure Container<br/>Registry
    participant DC as Docker Compose
    participant ER as Edge Registry
    
    Note over ES: システム起動
    
    ES->>ES: 設定ファイル読込<br/>(/etc/kugelpos/edge.conf)
    ES->>ES: 現在バージョン取得<br/>(docker images)
    
    ES->>SYNC: GET /version-management/check
    Note right of ES: {<br/>  "device_type": "edge",<br/>  "device_id": "edge-tokyo-001",<br/>  "current_versions": {...}<br/>}
    
    SYNC->>SYNC: バージョン設定確認
    SYNC-->>ES: バージョン応答
    Note left of SYNC: {<br/>  "update_required": true,<br/>  "target_versions": {...}<br/>}
    
    alt 更新が必要
        loop 各サービス
            ES->>ACR: docker pull image:version
            ACR-->>ES: イメージダウンロード
            ES->>ER: docker tag & push<br/>(ローカルレジストリ)
        end
        
        ES->>ES: docker-compose.yml 更新
        ES->>DC: docker-compose down
        ES->>DC: docker-compose up -d
        DC-->>ES: サービス起動完了
        
        ES->>ES: ヘルスチェック実行
        
        ES->>SYNC: POST /version-management/complete
        Note right of ES: {<br/>  "device_type": "edge",<br/>  "device_id": "edge-tokyo-001",<br/>  "update_results": [...]<br/>}
        
        SYNC-->>ES: 完了確認
    else 更新不要
        ES->>DC: docker-compose up -d
        DC-->>ES: サービス起動完了
    end
    
    ES->>ER: docker-compose up -d<br/>(レジストリ起動)
    ER-->>ES: レジストリ起動完了
```

## 2. POS端末の起動・更新シーケンス（認証付き）

```mermaid
sequenceDiagram
    participant PS as pos-startup.sh
    participant SYNC as Sync Service<br/>(Cloud)
    participant TERM as Terminal Service<br/>(Cloud)
    participant ER as Edge Registry<br/>(Local)
    participant ACR as Azure Container<br/>Registry
    participant DC as Docker/Compose
    
    Note over PS: システム起動
    
    PS->>PS: 設定ファイル読込<br/>(/etc/kugelpos/pos.conf)
    PS->>PS: API キー取得
    
    PS->>SYNC: GET /version-management/check
    Note right of PS: {<br/>  "device_type": "pos",<br/>  "device_id": "pos-001",<br/>  "api_key": "xxxx-xxxx",<br/>  "current_versions": {...}<br/>}
    
    SYNC->>TERM: POST /terminals/verify
    Note right of SYNC: {<br/>  "terminal_id": "pos-001",<br/>  "api_key": "xxxx-xxxx"<br/>}
    
    TERM->>TERM: 端末検証
    
    alt 認証成功
        TERM-->>SYNC: 端末情報
        Note left of TERM: {<br/>  "valid": true,<br/>  "terminal_info": {...}<br/>}
        
        SYNC->>SYNC: バージョン設定確認
        SYNC-->>PS: バージョン応答
        
        alt 更新が必要
            loop 各サービス
                PS->>ER: docker pull image:version<br/>(エッジレジストリ)
                alt エッジから取得成功
                    ER-->>PS: イメージダウンロード
                else エッジから取得失敗
                    PS->>ACR: docker pull image:version<br/>(クラウド直接)
                    ACR-->>PS: イメージダウンロード
                end
            end
            
            PS->>PS: docker-compose.yml 更新
            PS->>DC: サービス再起動
            DC-->>PS: 起動完了
            
            PS->>SYNC: POST /version-management/complete
            SYNC-->>PS: 完了確認
        else 更新不要
            PS->>DC: サービス起動
        end
        
    else 認証失敗
        TERM-->>SYNC: 認証エラー
        SYNC-->>PS: 401 Unauthorized
        PS->>PS: オフラインモード移行
        PS->>DC: キャッシュイメージで起動
    end
    
    PS->>PS: POSアプリケーション起動
```

## 3. 管理者によるバージョン設定シーケンス

```mermaid
sequenceDiagram
    participant ADMIN as Admin Console
    participant API as Sync API
    participant DB as MongoDB
    
    ADMIN->>API: GET /version-management/devices
    API->>DB: 端末一覧取得
    DB-->>API: 端末リスト
    API-->>ADMIN: 端末一覧表示
    
    ADMIN->>ADMIN: バージョン設定UI表示
    
    Note over ADMIN: 管理者が<br/>端末別バージョン設定
    
    ADMIN->>API: POST /version-management/configs
    Note right of ADMIN: {<br/>  "device_type": "edge",<br/>  "device_id": "edge-tokyo-001",<br/>  "target_versions": {<br/>    "cart": "v1.2.4",<br/>    "terminal": "v1.2.4"<br/>  }<br/>}
    
    API->>API: 設定検証
    
    alt バージョン存在確認
        API->>API: ACRにイメージ存在確認
    end
    
    API->>DB: バージョン設定保存
    DB-->>API: 保存完了
    
    API->>API: 更新履歴記録
    
    API-->>ADMIN: 設定完了応答
    
    ADMIN->>ADMIN: 設定結果表示
```

## 4. 定期バージョンチェックシーケンス

```mermaid
sequenceDiagram
    participant CRON as Cron Job<br/>(POS/Edge)
    participant SYNC as Sync Service
    participant DB as MongoDB
    
    Note over CRON: 6時間ごとに実行
    
    CRON->>CRON: 現在バージョン確認
    
    CRON->>SYNC: GET /version-management/check
    SYNC->>DB: バージョン設定取得
    DB-->>SYNC: 設定情報
    
    SYNC->>SYNC: バージョン比較
    
    alt 更新あり & 更新時間帯内
        SYNC-->>CRON: 更新指示
        CRON->>CRON: 更新スクリプト実行
        Note over CRON: ログファイルに<br/>更新開始記録
    else 更新あり & 更新時間帯外
        SYNC-->>CRON: 更新保留応答
        Note left of SYNC: {<br/>  "update_required": true,<br/>  "update_window": "02:00-05:00",<br/>  "next_check": "02:00"<br/>}
        CRON->>CRON: 次回チェック予約
    else 更新なし
        SYNC-->>CRON: 更新不要応答
        Note over CRON: ログファイルに<br/>チェック完了記録
    end
```

## 5. 障害時のフォールバックシーケンス

```mermaid
sequenceDiagram
    participant POS as POS Terminal
    participant ER as Edge Registry
    participant ACR as ACR (Cloud)
    participant SYNC as Sync Service
    participant LOCAL as Local Cache
    
    Note over POS: 更新処理開始
    
    POS->>SYNC: バージョン確認
    
    alt Sync Service 接続失敗
        POS->>POS: タイムアウト検知
        POS->>LOCAL: ローカル設定確認
        LOCAL-->>POS: 最終成功バージョン
        POS->>POS: 現行バージョンで起動
        Note over POS: オフラインモード
    else Sync Service 接続成功
        SYNC-->>POS: 更新必要
        
        POS->>ER: イメージ取得試行
        
        alt Edge Registry 接続失敗
            POS->>POS: エッジ失敗検知
            POS->>ACR: クラウド直接接続
            
            alt ACR 接続成功
                ACR-->>POS: イメージ取得
                POS->>POS: 更新実行
            else ACR 接続失敗
                POS->>LOCAL: キャッシュ確認
                
                alt キャッシュあり
                    LOCAL-->>POS: キャッシュイメージ
                    POS->>POS: キャッシュで起動
                    Note over POS: デグレードモード
                else キャッシュなし
                    POS->>POS: 起動失敗
                    POS->>POS: エラー通知
                    Note over POS: サービス停止
                end
            end
        else Edge Registry 接続成功
            ER-->>POS: イメージ取得
            POS->>POS: 正常更新
        end
    end
```

## 6. ロールバックシーケンス

```mermaid
sequenceDiagram
    participant ADMIN as Admin Console
    participant API as Sync API
    participant DB as MongoDB
    participant EDGE as Edge/POS
    participant DC as Docker Compose
    
    Note over ADMIN: 問題検知
    
    ADMIN->>API: GET /version-management/history
    API->>DB: 更新履歴取得
    DB-->>API: 履歴データ
    API-->>ADMIN: 更新履歴表示
    
    ADMIN->>ADMIN: ロールバック<br/>バージョン選択
    
    ADMIN->>API: POST /version-management/rollback
    Note right of ADMIN: {<br/>  "device_id": "edge-tokyo-001",<br/>  "rollback_to": {<br/>    "cart": "v1.2.2",<br/>    "terminal": "v1.2.2"<br/>  },<br/>  "reason": "Performance issue"<br/>}
    
    API->>DB: ロールバック設定保存
    DB-->>API: 保存完了
    
    API->>API: 緊急フラグ設定
    
    API-->>ADMIN: ロールバック受付
    
    Note over EDGE: 次回チェック時<br/>または<br/>強制更新トリガー
    
    EDGE->>API: バージョン確認
    API-->>EDGE: ロールバック指示
    Note left of API: {<br/>  "update_required": true,<br/>  "rollback": true,<br/>  "target_versions": {...}<br/>}
    
    EDGE->>EDGE: 旧バージョン確認
    
    alt ローカルにキャッシュあり
        EDGE->>DC: docker-compose down
        EDGE->>EDGE: compose.yml を旧版に
        EDGE->>DC: docker-compose up -d
        DC-->>EDGE: ロールバック完了
    else キャッシュなし
        EDGE->>EDGE: イメージ再取得
        EDGE->>DC: サービス更新
    end
    
    EDGE->>API: ロールバック完了通知
    API->>DB: ステータス更新
    API-->>ADMIN: 完了通知（WebSocket）
```

---

**ドキュメントバージョン**: 1.0.0  
**作成日**: 2025-01-16  
**最終更新日**: 2025-01-16
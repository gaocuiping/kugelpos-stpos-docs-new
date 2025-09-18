# アプリケーションバージョン管理機能要件書

## 1. 概要

本書は、Kugelpos システムにおけるコンテナイメージのバージョン管理機能に関する要件を定義する。

## 2. システム構成

### 2.1 クラウド側コンポーネント

#### 2.1.1 イメージレジストリー
- **製品**: Azure Container Registry (ACR)
- **役割**: 全バージョンのコンテナイメージを集中管理
- **構成**: Premium SKU（ジオレプリケーション対応）

#### 2.1.2 バージョン管理機能
- **役割**: 全環境のバージョン情報を一元管理
- **機能**:
  - エッジ端末別バージョン設定
  - POS端末別バージョン設定
  - 更新履歴管理
  - ロールバック指示

#### 2.1.3 クラウドサービス
- **対象サービス**: account, terminal, master-data, cart, report, journal, stock, sync
- **デプロイ基盤**: Azure Container Apps
- **更新方式**: Blue-Greenデプロイメント

### 2.2 エッジ側コンポーネント

#### 2.2.1 イメージレジストリー
- **製品**: 選定必要（候補: Harbor, Docker Registry, Nexus Repository）
- **役割**: クラウドから取得したイメージのローカルキャッシュ
- **要件**:
  - プロキシキャッシュ機能
  - 自動削除ポリシー対応
  - 軽量動作（エッジ環境考慮）

#### 2.2.2 エッジサービス
- **対象サービス**: クラウドサービスと同一構成
- **アクセス元**: POS端末以外のデバイス（カート、スマホレジ等）
- **デプロイ基盤**: Docker Compose

### 2.3 POS端末側コンポーネント

#### 2.3.1 POSサービス
- **構成**: エッジサービスと同一のコンテナイメージを使用
- **特徴**: ローカル完結型動作
- **デプロイ基盤**: Docker または Docker Compose

## 3. バージョン管理要件

### 3.1 イメージ登録要件

#### 3.1.1 バージョンタグ規則
```
<service-name>:<version>
例: kugelpos.cart:v1.2.3
    kugelpos.cart:v1.2.3-rc1
    kugelpos.cart:v1.2.3-hotfix1
```

#### 3.1.2 レジストリ登録フロー
1. CI/CDパイプラインでビルド
2. バージョンタグ付与
3. ACRへプッシュ
4. バージョン管理システムへ登録

### 3.2 クラウドサービス更新要件

#### 3.2.1 更新プロセス
1. システム管理者がバージョン管理画面で対象バージョンを指定
2. Azure Container Apps コンテナイメージ情報更新
3. Blue-Greenデプロイメント実行
4. ヘルスチェック確認
5. トラフィック切替（ダウンタイムゼロ）

#### 3.2.2 ロールバック要件
- 即座に前バージョンへの切替が可能
- 最低3世代のバージョン保持

### 3.3 エッジサービス更新要件

#### 3.3.1 バージョン指定
```json
{
  "edge_id": "edge-tokyo-001",
  "services": {
    "cart": "v1.2.3",
    "terminal": "v1.2.3",
    "master-data": "v1.2.2"
  },
  "update_policy": {
    "window": "02:00-05:00",
    "auto_update": true
  }
}
```

#### 3.3.2 更新フロー
1. **起動時チェック**
   - エッジ端末起動時にクラウドのバージョン管理APIを呼び出し
   - 自身のIDで登録されているバージョン情報を取得
   
2. **更新判定**
   - 現在バージョンと指定バージョンを比較
   - 更新が必要な場合は更新処理開始

3. **イメージ取得**
   - ACRから必要なイメージをプル
   - エッジ側レジストリーにキャッシュ

4. **サービス更新**
   - docker-compose down
   - docker-compose.yml更新
   - docker-compose up -d

5. **完了通知**
   - クラウドのバージョン管理APIに更新完了を通知
   - 更新結果（成功/失敗）と現在バージョンを送信

### 3.4 POS端末更新要件

#### 3.4.1 更新チェック
1. **起動時チェック**
   - POS端末起動時にクラウドのバージョン管理APIを呼び出し
   - 自身の端末IDで登録されているバージョン情報を取得

2. **定期チェック**
   - 6時間ごとに更新チェック実施

#### 3.4.2 イメージ取得優先順位
1. **エッジ側レジストリーから取得試行**
   ```bash
   docker pull edge-registry:5000/kugelpos.cart:v1.2.3
   ```
   
2. **エッジから取得失敗時はクラウド側から取得**
   ```bash
   docker pull acr.azurecr.io/kugelpos.cart:v1.2.3
   ```

3. **フォールバック**
   - 両方失敗時は現行バージョンで動作継続
   - エラーログをクラウドに送信

#### 3.4.3 更新完了通知
```json
{
  "terminal_id": "pos-001",
  "edge_id": "edge-tokyo-001", 
  "update_result": "success",
  "services": {
    "cart": {
      "previous": "v1.2.2",
      "current": "v1.2.3",
      "source": "edge"  // "edge" or "cloud"
    }
  },
  "timestamp": "2025-01-16T10:30:00Z"
}
```

### 3.5 バージョンロールバック要件

#### 3.5.1 ロールバック指示
- クラウドのバージョン管理画面から特定端末を選択
- ロールバックしたいバージョンを指定
- 次回起動時または強制更新トリガーで適用

#### 3.5.2 ロールバック対象
- エッジ端末: サービス単位でロールバック可能
- POS端末: サービス単位でロールバック可能
- クラウド: 環境全体でロールバック

#### 3.5.3 制約事項
- データベーススキーマの後方互換性が必要
- APIの後方互換性が必要
- 最低3世代前までロールバック可能

### 3.6 サービス間連携要件

#### 3.6.1 バージョン管理APIの実装
- **実装先**: Syncサービス内に実装
- **理由**: 
  - エッジ端末との通信基盤が既に存在
  - クラウド/エッジモードの切り替え機能を保有
  - データ同期とバージョン管理を統合的に管理

#### 3.6.2 POS端末認証連携
- **認証フロー**:
  1. POS端末がSyncサービスのバージョン管理APIにアクセス
  2. Syncサービスが内部でTerminalサービスの検証APIを呼び出し
  3. Terminalサービスが端末ID・APIキーを検証
  4. 認証成功時のみバージョン情報を返却

- **Terminalサービスの役割**:
  - POS端末情報（terminal_id、api_key）の管理
  - 端末の実在性検証
  - 端末メタデータ（tenant_id、store_code、terminal_no）の提供

- **端末検証API** (Terminalサービス側):
  ```
  POST /api/v1/terminals/verify
  ```
  リクエスト:
  ```json
  {
    "terminal_id": "pos-001",
    "api_key": "xxxx-xxxx-xxxx-xxxx"
  }
  ```
  レスポンス:
  ```json
  {
    "valid": true,
    "terminal_info": {
      "tenant_id": "tenant1",
      "store_code": "store1",
      "terminal_no": 1
    }
  }
  ```

#### 3.6.3 バージョン管理の制約
- **端末実在性の保証**:
  - Terminalサービスに登録されている端末のみバージョン管理可能
  - 未登録端末からのアクセスは拒否
  
- **データ整合性**:
  - バージョン設定時に端末情報を検証
  - tenant_id、store_code、terminal_noを記録し追跡可能に

- **セキュリティ**:
  - API認証は各サービスで独立して実施
  - サービス間通信は内部ネットワーク経由
  - APIキーは暗号化して保存

## 4. API仕様

### 4.1 バージョン確認API

#### エンドポイント
```
GET /api/v1/version-management/check
```

#### リクエスト
```json
{
  "device_type": "edge|pos",
  "device_id": "edge-tokyo-001",  // POS端末の場合はterminal_id
  "api_key": "xxxx-xxxx-xxxx-xxxx",  // POS端末の場合は必須
  "current_versions": {
    "cart": "v1.2.2",
    "terminal": "v1.2.2"
  }
}
```

#### レスポンス
```json
{
  "update_required": true,
  "target_versions": {
    "cart": "v1.2.3",
    "terminal": "v1.2.3"
  },
  "update_policy": {
    "force": false,
    "window": "02:00-05:00"
  }
}
```

### 4.2 更新完了通知API

#### エンドポイント
```
POST /api/v1/version-management/complete
```

#### リクエスト
```json
{
  "device_type": "edge|pos",
  "device_id": "edge-tokyo-001",  // POS端末の場合はterminal_id
  "api_key": "xxxx-xxxx-xxxx-xxxx",  // POS端末の場合は必須
  "update_results": [
    {
      "service": "cart",
      "status": "success",
      "version": "v1.2.3",
      "error": null
    }
  ],
  "timestamp": "2025-01-16T10:30:00Z"
}
```

#### レスポンス
```json
{
  "status": "acknowledged",
  "next_check": "2025-01-16T16:30:00Z"
}
```

## 5. エッジ側レジストリー製品選定基準

### 5.1 必須要件
- [ ] プロキシキャッシュ機能: クラウドレジストリからプルしたイメージをローカルキャッシュし、2回目以降は高速配信
- [ ] 認証・認可機能: 不正アクセス防止のためのユーザー認証とロールベースのアクセス制御
- [ ] REST API対応: プログラムによる自動化やCI/CD連携のためのAPI提供
- [ ] Docker互換性: 標準的なdocker pull/pushコマンドでの操作が可能

### 5.2 推奨要件
- [ ] Web UI: ブラウザからイメージ管理や設定変更が可能な管理画面
- [ ] 自動削除ポリシー: 古いイメージや未使用タグの自動削除によるストレージ最適化
- [ ] レプリケーション機能: 複数エッジ間でのイメージ同期やバックアップ
- [ ] 脆弱性スキャン: イメージ内のセキュリティ脆弱性を自動検出・警告

### 5.3 候補製品比較

| 製品 | OSS | 軽量性 | 機能充実度 | 運用実績 |
|-----|-----|-------|-----------|---------|
| Harbor | ✓ | △ | ◎ | ◎ |
| Docker Registry | ✓ | ◎ | △ | ○ |
| Nexus Repository | △ | ○ | ◎ | ◎ |

## 6. 起動スクリプト要件

### 6.1 エッジ端末起動スクリプト

#### 6.1.1 基本機能
- **スクリプト名**: `edge-startup.sh`
- **実行タイミング**: システム起動時（systemdサービスとして登録）
- **実行権限**: root権限

#### 6.1.2 処理フロー
```bash
#!/bin/bash
# 1. 設定読み込み
source /etc/kugelpos/edge.conf

# 2. バージョン確認
response=$(curl -X GET "${SYNC_API_URL}/version-management/check" \
  -H "Content-Type: application/json" \
  -d '{
    "device_type": "edge",
    "device_id": "'${EDGE_ID}'",
    "current_versions": '$(get_current_versions)'
  }')

# 3. 更新判定
if [[ $(echo $response | jq -r '.update_required') == "true" ]]; then
  # 4. イメージ取得
  for service in $(echo $response | jq -r '.target_versions | keys[]'); do
    version=$(echo $response | jq -r ".target_versions.${service}")
    docker pull ${ACR_URL}/${service}:${version}
  done
  
  # 5. docker-compose.yml更新
  update_compose_file $response
  
  # 6. サービス再起動
  docker-compose down
  docker-compose up -d
  
  # 7. 完了通知
  curl -X POST "${SYNC_API_URL}/version-management/complete" \
    -H "Content-Type: application/json" \
    -d '{
      "device_type": "edge",
      "device_id": "'${EDGE_ID}'",
      "update_results": '$(generate_update_results)'
    }'
fi

# 8. エッジレジストリ起動（Harbor等）
docker-compose -f docker-compose.registry.yml up -d
```

#### 6.1.3 エラーハンドリング
- ネットワークエラー時: 現行バージョンで起動継続
- イメージプル失敗時: ロールバック実行
- 起動失敗時: 前回成功バージョンで再起動

#### 6.1.4 ログ出力
- ログファイル: `/var/log/kugelpos/edge-startup.log`
- ログローテーション: 7日保持、最大100MB

### 6.2 POS端末起動スクリプト

#### 6.2.1 基本機能
- **スクリプト名**: `pos-startup.sh`
- **実行タイミング**: システム起動時（systemdサービスとして登録）
- **実行権限**: kugelpos ユーザー権限

#### 6.2.2 処理フロー
```bash
#!/bin/bash
# 1. 設定読み込み
source /etc/kugelpos/pos.conf

# 2. バージョン確認
response=$(curl -X GET "${SYNC_API_URL}/version-management/check" \
  -H "Content-Type: application/json" \
  -d '{
    "device_type": "pos",
    "device_id": "'${TERMINAL_ID}'",
    "api_key": "'${API_KEY}'",
    "current_versions": '$(get_current_versions)'
  }')

# 3. 更新判定
if [[ $(echo $response | jq -r '.update_required') == "true" ]]; then
  # 4. イメージ取得（エッジ優先）
  for service in $(echo $response | jq -r '.target_versions | keys[]'); do
    version=$(echo $response | jq -r ".target_versions.${service}")
    
    # エッジレジストリから取得試行
    if ! docker pull ${EDGE_REGISTRY}/${service}:${version} 2>/dev/null; then
      # 失敗時はクラウドから取得
      docker pull ${ACR_URL}/${service}:${version}
    fi
  done
  
  # 5. docker-compose.yml更新
  update_compose_file $response
  
  # 6. サービス再起動
  docker-compose down
  docker-compose up -d
  
  # 7. 完了通知
  curl -X POST "${SYNC_API_URL}/version-management/complete" \
    -H "Content-Type: application/json" \
    -d '{
      "device_type": "pos",
      "device_id": "'${TERMINAL_ID}'",
      "api_key": "'${API_KEY}'",
      "update_results": '$(generate_update_results)'
    }'
fi

# 8. POS アプリケーション起動
/usr/local/bin/pos-app start
```

#### 6.2.3 エラーハンドリング
- 認証エラー時: オフラインモードで起動
- エッジ接続失敗時: クラウド直接接続を試行
- 両方失敗時: キャッシュされたイメージで起動

#### 6.2.4 ログ出力
- ログファイル: `/var/log/kugelpos/pos-startup.log`
- syslogへの転送: facility local0

### 6.3 共通要件

#### 6.3.1 設定ファイル
**エッジ端末設定** (`/etc/kugelpos/edge.conf`):
```bash
EDGE_ID="edge-tokyo-001"
SYNC_API_URL="https://sync.kugelpos.cloud/api/v1"
ACR_URL="kugelpos.azurecr.io"
UPDATE_WINDOW_START="02:00"
UPDATE_WINDOW_END="05:00"
```

**POS端末設定** (`/etc/kugelpos/pos.conf`):
```bash
TERMINAL_ID="pos-001"
API_KEY="xxxx-xxxx-xxxx-xxxx"
SYNC_API_URL="https://sync.kugelpos.cloud/api/v1"
EDGE_REGISTRY="edge-local:5000"
ACR_URL="kugelpos.azurecr.io"
```

#### 6.3.2 ヘルスチェック
- 起動完了確認: 全サービスのヘルスエンドポイント確認
- タイムアウト: 5分以内に起動完了
- 失敗時: 自動リトライ（最大3回）

#### 6.3.3 セキュリティ
- API キーは環境変数または暗号化ファイルから読み込み
- 通信はすべてHTTPS
- ログに認証情報を出力しない

---

**文書バージョン**: 1.0.0  
**作成日**: 2025-09-16  
**最終更新日**: 2025-09-16
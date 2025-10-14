# ユーザーストーリー4: P2P優先度制御による店舗内高速ダウンロード - 処理フロー図

## 概要

このドキュメントは、ユーザーストーリー4「P2P優先度制御による店舗内高速ダウンロード」の処理フローを視覚的に説明します。同一店舗内の複数エッジ端末間で、P2P（Peer-to-Peer）優先度制御を用いてファイルとコンテナイメージを効率的に配信し、店舗全体のインターネット帯域を削減する仕組みを、ユーザーが理解しやすい形で図解します。

## シナリオ

同一店舗内の複数エッジ端末間で、P2P（Peer-to-Peer）優先度制御を用いてファイルとコンテナイメージを効率的に配信し、店舗全体のインターネット帯域を削減する。シード端末（is_p2p_seed=true）がクラウドから取得し、非シード端末（is_p2p_seed=false）は店舗内ネットワーク経由でシード端末から取得する。

## 店舗構成パターン

### パターン1: 専用Edge端末あり

```mermaid
graph TB
    subgraph Cloud["☁️ クラウド環境"]
        CloudSync["Sync Service"]
        Registry["Container Registry"]
    end

    subgraph Store["🏪 店舗（専用Edge端末あり）"]
        Edge["Edge端末<br/>device_type: edge<br/>is_p2p_seed: true<br/>priority: 0<br/>（プライマリシード）"]
        POS1["POS-001<br/>device_type: pos<br/>is_p2p_seed: false<br/>priority: 99<br/>（非シード）"]
        POS2["POS-002<br/>device_type: pos<br/>is_p2p_seed: false<br/>priority: 99<br/>（非シード）"]
        POS3["POS-003<br/>device_type: pos<br/>is_p2p_seed: false<br/>priority: 99<br/>（非シード）"]
    end

    CloudSync -->|1. クラウドから<br/>ダウンロード| Edge
    Registry -->|1. イメージpull| Edge
    Edge -->|2. P2P配信<br/>（priority: 0）| POS1
    Edge -->|2. P2P配信<br/>（priority: 0）| POS2
    Edge -->|2. P2P配信<br/>（priority: 0）| POS3

    style Edge fill:#d4edda
    style POS1 fill:#fff3cd
    style POS2 fill:#fff3cd
    style POS3 fill:#fff3cd
```

**特徴**:
- 専用Edge端末（priority=0）: プライマリシード、クラウドから取得
- POS端末（priority=99）: 非シード、専用Edge端末からP2P受信

### パターン2: POS端末のみ（専用Edge端末不在）

```mermaid
graph TB
    subgraph Cloud["☁️ クラウド環境"]
        CloudSync["Sync Service"]
        Registry["Container Registry"]
    end

    subgraph Store["🏪 店舗（POS端末のみ）"]
        POS1["POS-001<br/>device_type: pos<br/>is_p2p_seed: true<br/>priority: 0<br/>（プライマリシード兼POS）"]
        POS2["POS-002<br/>device_type: pos<br/>is_p2p_seed: true<br/>priority: 1<br/>（セカンダリシード兼POS）"]
        POS3["POS-003<br/>device_type: pos<br/>is_p2p_seed: false<br/>priority: 99<br/>（非シード）"]
        POS4["POS-004<br/>device_type: pos<br/>is_p2p_seed: false<br/>priority: 99<br/>（非シード）"]
    end

    CloudSync -->|1. クラウドから<br/>ダウンロード| POS1
    Registry -->|1. イメージpull| POS1
    POS1 -->|2a. P2P配信<br/>（priority: 0）| POS2
    POS1 -->|2a. P2P配信<br/>（priority: 0）| POS3
    POS1 -->|2a. P2P配信<br/>（priority: 0）| POS4
    POS2 -->|2b. フォールバック<br/>（priority: 1）| POS3
    POS2 -->|2b. フォールバック<br/>（priority: 1）| POS4

    style POS1 fill:#d4edda
    style POS2 fill:#d1ecf1
    style POS3 fill:#fff3cd
    style POS4 fill:#fff3cd
```

**特徴**:
- POS-001（priority=0）: プライマリシード兼POS、クラウドから取得
- POS-002（priority=1）: セカンダリシード兼POS、POS-001からP2P受信可能
- POS-003/004（priority=99）: 非シード、priority順（0→1）でP2P受信試行

## 処理フロー全体

### フロー1: パターン1 - 専用Edge端末経由のP2P配信

専用Edge端末（priority=0）がクラウドから取得し、POS端末（priority=99）がEdge端末からP2P受信するフローです。

```mermaid
sequenceDiagram
    participant Cloud as ☁️ Cloud Sync
    participant Edge as 🏪 Edge端末<br/>(priority=0)
    participant EdgeDB as Edge MongoDB
    participant POS1 as POS-001<br/>(priority=99)
    participant POS1DB as POS-001 MongoDB
    participant LocalNet as 店舗内ネットワーク

    Note over Cloud,LocalNet: 🔄 パターン1: 専用Edge端末経由のP2P配信

    rect rgb(240, 240, 255)
        Note right of Edge: 1. Edge端末（シード）がクラウドからダウンロード
        Edge->>+Cloud: POST /api/v1/version/check<br/>{edge_id: "edge-tenant001-store001-001", device_type: "edge", current_version: "1.2.2"}

        Cloud->>Cloud: シード端末検出<br/>is_p2p_seed: true, priority: 0

        Cloud-->>-Edge: Manifest返却<br/>{target_version: "1.2.3", available_seeds: []}

        Note over Edge: ✅ available_seeds空<br/>→ クラウドから直接ダウンロード

        Edge->>EdgeDB: DeviceVersion更新<br/>(update_status: "downloading")

        Edge->>Cloud: GET /api/v1/artifacts/startup.sh?version=1.2.3<br/>（クラウドから直接取得）
        Cloud-->>Edge: ファイルデータ

        Edge->>EdgeDB: ローカルキャッシュ保存<br/>(/opt/kugelpos/pending-updates/v1.2.3/startup.sh)

        Edge->>EdgeDB: DeviceVersion更新<br/>(download_status: "completed")

        Edge->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3", is_p2p_seed: true, priority: 0}
        Cloud->>Cloud: シード端末リストに追加<br/>(available_seeds: [{edge_id: "edge-...-001", priority: 0, url: "http://192.168.1.10:8007"}])
        Cloud-->>-Edge: 通知受信確認

        Note over Edge: ✅ Edgeダウンロード完了<br/>他端末へのP2P配信準備完了
    end

    rect rgb(255, 250, 240)
        Note right of POS1: 2. POS端末（非シード）がバージョンチェック
        POS1->>+Cloud: POST /api/v1/version/check<br/>{edge_id: "edge-tenant001-store001-002", device_type: "pos", current_version: "1.2.2"}

        Cloud->>Cloud: 非シード端末検出<br/>is_p2p_seed: false, priority: 99<br/>同一店舗のシード端末検索

        Cloud-->>-POS1: Manifest返却<br/>{<br/>  target_version: "1.2.3",<br/>  available_seeds: [<br/>    {edge_id: "edge-tenant001-store001-001", priority: 0,<br/>     url: "http://192.168.1.10:8007"}<br/>  ],<br/>  artifacts: [{primary_url: "https://cloud...", fallback_url: "https://backup-cloud..."}]<br/>}

        Note over POS1: ✅ available_seeds存在<br/>→ P2P優先、priority順（0から）でアクセス
    end

    rect rgb(240, 255, 240)
        Note right of POS1: 3. POS端末がP2P優先でダウンロード
        POS1->>POS1DB: DeviceVersion更新<br/>(update_status: "downloading")

        POS1->>POS1: priority昇順ソート<br/>（0が最優先）

        loop priority順（0→1→...）
            POS1->>+Edge: GET http://192.168.1.10:8007/api/v1/artifacts/startup.sh?version=1.2.3<br/>（Edge Sync Service API）

            alt P2P成功（Edge端末から取得）
                Edge->>Edge: ローカルキャッシュ確認<br/>(/opt/kugelpos/pending-updates/v1.2.3/startup.sh)
                Edge-->>-POS1: ファイルデータ<br/>（ローカルネットワーク経由、高速）

                Note over POS1,LocalNet: ✅ P2P取得成功<br/>（クラウド比50%以上速度向上）

                POS1->>POS1DB: ローカル保存<br/>(/opt/kugelpos/pending-updates/v1.2.3/startup.sh)
            else P2P失敗（タイムアウト/ネットワークエラー）
                Edge-->>POS1: ❌ 接続失敗

                Note over POS1: 次のpriority（1, 2, ...）を試行<br/>全シード失敗時はクラウドへフォールバック
            end
        end

        alt 全シード失敗
            Note over POS1: ⚠️ 全シードで失敗<br/>→ クラウドへフォールバック

            POS1->>+Cloud: GET /api/v1/artifacts/startup.sh?version=1.2.3<br/>（primary_url）
            Cloud-->>-POS1: ファイルデータ<br/>（クラウドから直接取得）
        end

        POS1->>POS1DB: DeviceVersion更新<br/>(download_status: "completed")

        POS1->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3", download_source: "p2p", p2p_seed_id: "edge-...-001"}
        Cloud-->>-POS1: 通知受信確認

        Note over POS1: ✅ POSダウンロード完了<br/>（P2P経由、高速・帯域削減）
    end

    Note over Cloud,LocalNet: ⏱️ P2P配信完了・ダウンロード時間50%短縮
```

**主要ステップ**:
1. **Edge端末（シード）がクラウドからダウンロード**: available_seeds空、クラウドから直接取得
2. **POS端末（非シード）がバージョンチェック**: available_seedsにEdge端末情報が含まれる
3. **POS端末がP2P優先でダウンロード**: priority順（0→1...）で試行、全失敗時はクラウドへフォールバック

**P2P効果**:
- ダウンロード速度: クラウド比50%以上向上（ローカルネットワーク利用）
- 店舗全体の帯域削減: クラウドからのダウンロードはEdge端末のみ（POS端末3台がP2P利用で75%削減）

### フロー2: パターン2 - POS端末間のP2P配信と優先度制御

POS-001（priority=0）がプライマリシード、POS-002（priority=1）がセカンダリシード、POS-003（priority=99）が非シードの構成でのP2P配信フローです。

```mermaid
sequenceDiagram
    participant Cloud as ☁️ Cloud Sync
    participant POS1 as POS-001<br/>(priority=0, シード)
    participant POS2 as POS-002<br/>(priority=1, シード)
    participant POS3 as POS-003<br/>(priority=99, 非シード)
    participant POS1DB as POS-001 MongoDB
    participant POS2DB as POS-002 MongoDB
    participant POS3DB as POS-003 MongoDB

    Note over Cloud,POS3DB: 🔄 パターン2: POS端末間のP2P配信

    rect rgb(240, 240, 255)
        Note right of POS1: 1. POS-001（priority=0）がクラウドからダウンロード
        POS1->>+Cloud: POST /api/v1/version/check<br/>{edge_id: "edge-tenant001-store001-001", device_type: "pos", is_p2p_seed: true, priority: 0}

        Cloud->>Cloud: プライマリシード検出

        Cloud-->>-POS1: Manifest返却<br/>{target_version: "1.2.3", available_seeds: []}

        POS1->>Cloud: GET /api/v1/artifacts/startup.sh<br/>（クラウドから直接取得）
        Cloud-->>POS1: ファイルデータ

        POS1->>POS1DB: ローカルキャッシュ保存

        POS1->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3", priority: 0}
        Cloud->>Cloud: シード端末リストに追加<br/>(available_seeds: [{edge_id: "...-001", priority: 0, url: "http://192.168.1.11:8007"}])
        Cloud-->>-POS1: 通知受信確認

        Note over POS1: ✅ POS-001ダウンロード完了
    end

    rect rgb(255, 250, 240)
        Note right of POS2: 2. POS-002（priority=1）がバージョンチェック
        POS2->>+Cloud: POST /api/v1/version/check<br/>{edge_id: "edge-tenant001-store001-002", device_type: "pos", is_p2p_seed: true, priority: 1}

        Cloud->>Cloud: セカンダリシード検出<br/>同一店舗の優先度の高いシード検索

        Cloud-->>-POS2: Manifest返却<br/>{<br/>  target_version: "1.2.3",<br/>  available_seeds: [<br/>    {edge_id: "...-001", priority: 0, url: "http://192.168.1.11:8007"}<br/>  ]<br/>}

        Note over POS2: ✅ priority=0のシード存在<br/>→ POS-001からP2P受信試行

        POS2->>+POS1: GET http://192.168.1.11:8007/api/v1/artifacts/startup.sh?version=1.2.3
        POS1-->>-POS2: ファイルデータ<br/>（P2P取得成功）

        POS2->>POS2DB: ローカルキャッシュ保存

        POS2->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3", priority: 1, download_source: "p2p"}
        Cloud->>Cloud: シード端末リストに追加<br/>(available_seeds: [{priority: 0, ...}, {priority: 1, ...}])
        Cloud-->>-POS2: 通知受信確認

        Note over POS2: ✅ POS-002ダウンロード完了<br/>（P2P経由）
    end

    rect rgb(240, 255, 240)
        Note right of POS3: 3. POS-003（priority=99）がバージョンチェック
        POS3->>+Cloud: POST /api/v1/version/check<br/>{edge_id: "edge-tenant001-store001-003", device_type: "pos", is_p2p_seed: false, priority: 99}

        Cloud->>Cloud: 非シード端末検出<br/>同一店舗のシード端末検索

        Cloud-->>-POS3: Manifest返却<br/>{<br/>  target_version: "1.2.3",<br/>  available_seeds: [<br/>    {edge_id: "...-001", priority: 0, url: "http://192.168.1.11:8007"},<br/>    {edge_id: "...-002", priority: 1, url: "http://192.168.1.12:8007"}<br/>  ]<br/>}

        Note over POS3: ✅ 複数シード存在<br/>→ priority順（0→1）でアクセス試行
    end

    rect rgb(255, 240, 240)
        Note right of POS3: 4. P2P優先度制御（priority順でアクセス）

        POS3->>POS3: priority昇順ソート<br/>（0→1）

        POS3->>+POS1: GET http://192.168.1.11:8007/api/v1/artifacts/startup.sh<br/>（priority=0、最優先）

        alt POS-001からP2P成功
            POS1-->>-POS3: ファイルデータ<br/>（P2P取得成功）

            Note over POS3: ✅ priority=0のシードから取得成功
        else POS-001停止中/接続失敗
            POS1-->>POS3: ❌ 接続失敗

            Note over POS3: 次のpriority（1）を試行

            POS3->>+POS2: GET http://192.168.1.12:8007/api/v1/artifacts/startup.sh<br/>（priority=1、セカンダリ）

            alt POS-002からP2P成功
                POS2-->>-POS3: ファイルデータ<br/>（P2P取得成功）

                Note over POS3: ✅ priority=1のシードから取得成功<br/>（フォールバック成功）
            else POS-002も停止中/接続失敗
                POS2-->>POS3: ❌ 接続失敗

                Note over POS3: ⚠️ 全シード失敗<br/>→ クラウドへフォールバック

                POS3->>+Cloud: GET /api/v1/artifacts/startup.sh<br/>（primary_url）
                Cloud-->>-POS3: ファイルデータ<br/>（クラウドから直接取得）

                Note over POS3: ✅ クラウドフォールバック成功
            end
        end

        POS3->>POS3DB: ローカル保存

        POS3->>+Cloud: POST /api/v1/download-complete<br/>{edge_id, version: "1.2.3", download_source: "p2p", p2p_seed_id: "...-001"}
        Cloud-->>-POS3: 通知受信確認

        Note over POS3: ✅ POS-003ダウンロード完了
    end

    Note over Cloud,POS3DB: ⏱️ P2P優先度制御完了・優先度順でフォールバック
```

**主要ステップ**:
1. **POS-001（priority=0）がクラウドからダウンロード**: プライマリシード
2. **POS-002（priority=1）がPOS-001からP2P受信**: セカンダリシード
3. **POS-003（priority=99）がバージョンチェック**: 複数シード情報を受信
4. **P2P優先度制御**: priority順（0→1）でアクセス試行、全失敗時はクラウドへフォールバック

**優先度制御の効果**:
- 最優先（priority=0）のシードが健全な場合、全非シード端末がそこから取得
- primary=0停止時、自動的にpriority=1へフォールバック
- 全シード停止時、自動的にクラウドへフォールバック

### フロー3: コンテナイメージのP2P配信（Docker Registry間）

コンテナイメージをP2P配信する際、シード端末のRegistryから`docker pull`するフローです。

```mermaid
sequenceDiagram
    participant Cloud as ☁️ Cloud Registry
    participant Edge as 🏪 Edge端末<br/>(priority=0, Registry稼働)
    participant POS1 as POS-001<br/>(priority=99)
    participant Docker_POS1 as POS-001 Docker

    Note over Cloud,Docker_POS1: 🐳 コンテナイメージのP2P配信

    rect rgb(240, 240, 255)
        Note right of Edge: 1. Edge端末がクラウドRegistryからpull
        Edge->>+Cloud: docker pull registry.example.com/kugelpos/cart:1.2.3
        Cloud-->>-Edge: イメージレイヤー

        Note over Edge: ✅ Edgeローカルに保存<br/>Edge Registryでも利用可能
    end

    rect rgb(255, 250, 240)
        Note right of POS1: 2. POS端末がバージョンチェック
        POS1->>Cloud: POST /api/v1/version/check

        Cloud-->>POS1: Manifest返却<br/>{<br/>  container_images: [<br/>    {service: "cart", version: "1.2.3",<br/>     primary_registry: "registry.example.com",<br/>     primary_image: "kugelpos/cart:1.2.3",<br/>     fallback_registry: "backup-registry.example.com",<br/>     checksum: "sha256:abc123..."}<br/>  ],<br/>  available_seeds: [<br/>    {edge_id: "edge-...-001", priority: 0,<br/>     url: "http://192.168.1.10:8007",<br/>     registry_url: "http://192.168.1.10:5000"}<br/>  ]<br/>}

        Note over POS1: ✅ available_seeds存在<br/>→ P2P優先（シードのRegistry）
    end

    rect rgb(240, 255, 240)
        Note right of POS1: 3. P2P優先でイメージpull

        POS1->>POS1: priority昇順ソート<br/>（0が最優先）

        loop priority順（0→1→...）
            POS1->>Docker_POS1: docker pull http://192.168.1.10:5000/kugelpos/cart:1.2.3<br/>（Edge Registry）

            alt P2P成功（Edge Registryから取得）
                Docker_POS1->>+Edge: レイヤー要求<br/>（Edge Registry API）
                Edge-->>-Docker_POS1: イメージレイヤー<br/>（ローカルネットワーク経由）

                Note over Docker_POS1: ✅ P2P取得成功<br/>（クラウド比50%以上速度向上）
            else P2P失敗
                Edge-->>Docker_POS1: ❌ 接続失敗

                Note over POS1: 次のpriority試行<br/>全シード失敗時はクラウドへフォールバック
            end
        end

        alt 全シード失敗
            POS1->>Docker_POS1: docker pull registry.example.com/kugelpos/cart:1.2.3<br/>（primary_registry）

            Docker_POS1->>+Cloud: レイヤー要求
            Cloud-->>-Docker_POS1: イメージレイヤー<br/>（クラウドから直接取得）

            Note over Docker_POS1: ✅ クラウドフォールバック成功
        end

        POS1->>Docker_POS1: docker inspect kugelpos/cart:1.2.3
        Docker_POS1-->>POS1: sha256:abc123...

        POS1->>POS1: ダイジェスト検証

        Note over POS1: ✅ イメージpull完了<br/>（P2P経由、高速）
    end

    Note over Cloud,Docker_POS1: ⏱️ コンテナイメージP2P配信完了
```

**主要ステップ**:
1. **Edge端末がクラウドRegistryからpull**: イメージをローカルに保存、Edge Registryで利用可能に
2. **POS端末がバージョンチェック**: available_seedsにEdge Registry URLが含まれる
3. **P2P優先でイメージpull**: priority順にシードのRegistryから試行、全失敗時はクラウドへフォールバック

**Docker Registry間のP2P**:
- Edge端末でDocker Registryを稼働（ポート5000）
- POS端末は`docker pull <edge_registry_url>/image:tag`でローカルネットワーク経由取得
- Dockerレイヤーキャッシュも活用され、さらに帯域削減

## データベース構造

### EdgeTerminal（エッジ端末P2P設定）

```
コレクション: master_edge_terminal

ドキュメント例（パターン1: 専用Edge端末）:
{
  "_id": ObjectId("..."),
  "edge_id": "edge-tenant001-store001-001",
  "tenant_id": "tenant001",
  "store_code": "store001",
  "device_type": "edge",
  "is_p2p_seed": true,
  "p2p_priority": 0,
  "secret": "sha256:...",
  "sync_service_url": "http://192.168.1.10:8007",
  "registry_url": "http://192.168.1.10:5000",
  "created_at": ISODate("2025-10-01T00:00:00Z"),
  "updated_at": ISODate("2025-10-14T00:00:00Z")
}

ドキュメント例（パターン2: POS端末シード）:
{
  "_id": ObjectId("..."),
  "edge_id": "edge-tenant001-store001-001",
  "tenant_id": "tenant001",
  "store_code": "store001",
  "device_type": "pos",
  "is_p2p_seed": true,
  "p2p_priority": 0,
  "secret": "sha256:...",
  "sync_service_url": "http://192.168.1.11:8007",
  "registry_url": "http://192.168.1.11:5000",
  "created_at": ISODate("2025-10-01T00:00:00Z"),
  "updated_at": ISODate("2025-10-14T00:00:00Z")
}

ドキュメント例（非シード端末）:
{
  "_id": ObjectId("..."),
  "edge_id": "edge-tenant001-store001-003",
  "tenant_id": "tenant001",
  "store_code": "store001",
  "device_type": "pos",
  "is_p2p_seed": false,
  "p2p_priority": 99,
  "secret": "sha256:...",
  "sync_service_url": null,
  "registry_url": null,
  "created_at": ISODate("2025-10-01T00:00:00Z"),
  "updated_at": ISODate("2025-10-14T00:00:00Z")
}
```

**インデックス**:
- `{edge_id: 1}` (unique) - エッジ端末IDでの検索
- `{tenant_id: 1, store_code: 1}` - 店舗ごとの端末一覧取得
- `{tenant_id: 1, store_code: 1, is_p2p_seed: 1, p2p_priority: 1}` - 店舗内シード端末検索（priority順）

### Manifest（available_seeds含む）

```json
{
  "manifest_version": "1.0",
  "device_type": "pos",
  "device_id": "edge-tenant001-store001-003",
  "target_version": "1.2.3",
  "artifacts": [
    {
      "type": "script",
      "name": "startup.sh",
      "version": "1.2.3",
      "primary_url": "https://blob.example.com/v1.2.3/startup.sh",
      "fallback_url": "https://backup-blob.example.com/v1.2.3/startup.sh",
      "checksum": "sha256:abc123...",
      "size": 8192,
      "destination": "/opt/kugelpos/startup.sh",
      "permissions": "755"
    }
  ],
  "container_images": [
    {
      "service": "cart",
      "version": "1.2.3",
      "primary_registry": "registry.example.com",
      "primary_image": "kugelpos/cart:1.2.3",
      "fallback_registry": "backup-registry.example.com",
      "fallback_image": "kugelpos/cart:1.2.3",
      "checksum": "sha256:def456..."
    }
  ],
  "available_seeds": [
    {
      "edge_id": "edge-tenant001-store001-001",
      "priority": 0,
      "url": "http://192.168.1.10:8007",
      "registry_url": "http://192.168.1.10:5000"
    },
    {
      "edge_id": "edge-tenant001-store001-002",
      "priority": 1,
      "url": "http://192.168.1.12:8007",
      "registry_url": "http://192.168.1.12:5000"
    }
  ],
  "apply_schedule": {
    "scheduled_at": "2025-10-15T02:00:00Z",
    "maintenance_window": 30
  }
}
```

**available_seedsフィールド**:
- `edge_id`: シード端末ID
- `priority`: 優先度（0-9、0が最優先）
- `url`: Sync Service APIエンドポイントURL（ファイル取得用）
- `registry_url`: Docker Registry URL（コンテナイメージ取得用）

## パフォーマンス指標

| 指標 | 目標値 | 測定方法 |
|------|--------|---------|
| **P2P速度向上率** | 50%以上 | クラウド直接ダウンロードと比較したP2P経由のダウンロード速度向上率 |
| **店舗全体の帯域削減率** | 75%以上（専用Edge + POS 3台の場合） | (クラウドダウンロード総量 - 実際のクラウドダウンロード量) / クラウドダウンロード総量<br/>例: (4台 × 1GB - 1GB) / (4台 × 1GB) = 75% |
| **P2P成功率** | 95%以上 | P2P取得成功回数 / 全P2P試行回数 |
| **フォールバック所要時間** | 10秒以内 | P2P失敗検出 → 次priorityまたはクラウドフォールバック開始までの時間 |
| **シード端末ダウンロード完了通知遅延** | 5秒以内 | ダウンロード完了 → available_seedsに反映されるまでの時間 |

## エラーハンドリング

### P2Pシード端末停止時のフォールバック（FR-015）

```mermaid
graph TD
    A[バージョンチェック] --> B[Manifest受信<br/>available_seeds: priority順]
    B --> C{available_seeds存在?}
    C -->|Yes| D[priority昇順ソート<br/>0→1→2...]
    C -->|No| E[クラウドから直接ダウンロード]
    D --> F[priority=0のシードにアクセス]
    F --> G{P2P成功?}
    G -->|Yes| H[✅ P2P取得完了]
    G -->|No| I{次のpriority存在?}
    I -->|Yes| J[priority=1のシードにアクセス]
    J --> K{P2P成功?}
    K -->|Yes| H
    K -->|No| I
    I -->|No（全シード失敗）| L[⚠️ クラウドへフォールバック]
    L --> E
    E --> M[✅ クラウド取得完了]
```

**フォールバック戦略**:
1. priority昇順（0→1→2...）でシード端末にアクセス試行
2. 各シードでタイムアウト（10秒）設定
3. 全シード失敗時、自動的にクラウドへフォールバック（primary_url → fallback_url）

### 複数シード障害時の動作

```mermaid
sequenceDiagram
    participant POS3 as POS-003<br/>(priority=99)
    participant POS1 as POS-001<br/>(priority=0, 停止中)
    participant POS2 as POS-002<br/>(priority=1, 停止中)
    participant Cloud as ☁️ Cloud Sync

    Note over POS3,Cloud: ⚠️ 複数シード障害時の動作

    POS3->>+POS1: GET /api/v1/artifacts/startup.sh<br/>（priority=0）
    POS1-->>-POS3: ❌ 接続タイムアウト（10秒）

    Note over POS3: 次のpriority試行

    POS3->>+POS2: GET /api/v1/artifacts/startup.sh<br/>（priority=1）
    POS2-->>-POS3: ❌ 接続タイムアウト（10秒）

    Note over POS3: ⚠️ 全シード失敗<br/>→ クラウドへフォールバック

    POS3->>+Cloud: GET /api/v1/artifacts/startup.sh<br/>（primary_url）
    Cloud-->>-POS3: ✅ ファイルデータ

    Note over POS3: ✅ クラウドフォールバック成功<br/>ダウンロード完了
```

**全シード障害時の保証**:
- すべての端末（シード・非シード問わず）がクラウドへフォールバック可能
- primary_url失敗時はfallback_urlも試行
- 業務継続性を保証

## 受入シナリオの検証

### シナリオ1: パターン1の店舗でP2P配信

```
Given: パターン1の店舗で専用Edge端末（priority=0）がv1.2.3をクラウドからダウンロード完了
When: POS端末（priority=99）がバージョンチェック
Then:
  1. Manifestにpriority=0のシード端末URL（例: http://192.168.1.10:8007）が含まれる
  2. POS端末がpriority=0のシード端末にリクエスト送信
  3. ローカルネットワーク経由でP2P取得（クラウド比50%以上速度向上）

検証方法:
1. Edge端末でバージョンチェック → ダウンロード完了
2. Cloud側でEdge端末をavailable_seedsに追加
3. POS端末でバージョンチェック
4. Manifestにavailable_seeds含まれることを確認
5. POS端末がEdge端末（http://192.168.1.10:8007）にアクセスすることを確認
6. ダウンロード速度を測定（クラウド比50%以上向上を確認）
7. DeviceVersion.download_source: "p2p" を確認
```

### シナリオ2: パターン2でpriority順フォールバック

```
Given: パターン2の店舗でPOS-001（priority=0）がダウンロード完了
When: POS-002（priority=1）とPOS-003（priority=99）がバージョンチェック
Then:
  1. ManifestにPOS-001のURLが含まれる
  2. 両端末がPOS-001からP2P取得
  3. POS-001停止中の場合、POS-003はpriority=1のPOS-002へ自動フォールバック

検証方法:
1. POS-001でダウンロード完了
2. POS-002, POS-003でバージョンチェック
3. ManifestにPOS-001（priority=0）が含まれることを確認
4. POS-002, POS-003がPOS-001からP2P取得することを確認
5. POS-001を意図的に停止
6. POS-003（priority=99, 非シード）が再度バージョンチェック
7. POS-003がpriority=0へのアクセス失敗を検出
8. 自動的にpriority=1のPOS-002へフォールバックすることを確認
9. 全シード停止時はクラウドへフォールバックすることを確認
```

### シナリオ3: コンテナイメージのP2P配信

```
Given: コンテナイメージのダウンロード
When: シード端末（is_p2p_seed=true）が取得
Then: priority順に他のシード端末のRegistryからdocker pullを試行、全シードで失敗時はクラウドRegistryへフォールバック

検証方法:
1. Edge端末（priority=0）でコンテナイメージpull完了
2. POS端末（priority=99）でバージョンチェック
3. Manifestにavailable_seeds（registry_url含む）が含まれることを確認
4. POS端末が docker pull <edge_registry_url>/image:tag 実行
5. Edge Registry（http://192.168.1.10:5000）からレイヤー取得することを確認
6. Dockerレイヤーキャッシュも活用されることを確認
7. Edge Registry停止時、クラウドRegistryへフォールバックすることを確認
```

### シナリオ4: 全シード障害時のクラウドフォールバック

```
Given: パターン1の店舗で専用Edge端末（priority=0）が停止中
When: 非シードPOS端末（priority=99）がシード端末へのアクセス失敗
Then: クラウドへ直接フォールバックしてダウンロード

検証方法:
1. Edge端末を意図的に停止
2. POS端末でバージョンチェック
3. ManifestにEdge端末（priority=0）が含まれることを確認
4. POS端末がEdge端末へのアクセス試行
5. 接続失敗を検出（タイムアウト10秒）
6. 自動的にクラウド（primary_url）へフォールバックすることを確認
7. クラウドからダウンロード完了することを確認
8. DeviceVersion.download_source: "cloud_fallback" を確認
```

## 関連ドキュメント

- [spec.md](../spec.md) - 機能仕様書
- [plan.md](../plan.md) - 実装計画
- [data-model.md](../data-model.md) - データモデル設計
- [contracts/sync-api.yaml](../contracts/sync-api.yaml) - Sync API仕様

---

**ドキュメントバージョン**: 1.0.0
**最終更新日**: 2025-10-14
**ステータス**: 完成

# Sync Service Architecture

## 2. Data Flow Patterns

このセクションでは、クラウドとエッジ環境間でのデータフローパターンを示しています。データの種類と特性に応じて、3つの異なる同期パターンを採用しています。

**重要**: Syncサービスは自身が管理するデータベースのみ直接アクセス可能です。他サービスが管理するデータについては、それぞれのサービスのAPIを通じてアクセスします。これにより、サービス間の責任境界を明確にし、データの整合性を保証します。

### クラウド → エッジ（マスターデータ）
マスターデータは通常クラウドで管理され、エッジ環境に配信されます：

- **Products（商品情報）**: 商品マスター、価格、在庫情報
- **Payment Methods（決済方法）**: 利用可能な決済手段の設定
- **Tax Rules（税制ルール）**: 税率、税計算ロジック
- **Staff（スタッフ情報）**: 従業員マスター、権限設定

これらのデータは定期的にクラウドからエッジに同期され、各店舗で最新の情報を保持します。

```mermaid
flowchart TB
    subgraph Cloud["Cloud Environment"]
        direction LR
        CMD2[Cloud Master Data] --> CS2[Cloud Sync]
    end

    subgraph Edge["Edge Environment"]
        direction LR
        ES2[Edge Sync] --> EMD2[Edge Master Data]
    end

    CS2 -->|Master Data<br/>Products, Payment Methods<br/>Tax Rules, Staff| ES2

    style Cloud fill:#e1f5fe
    style Edge fill:#fff3e0
```

### エッジ → クラウド（トランザクションデータ）
店舗で発生したトランザクションデータはエッジからクラウドへ送信されます：

- **Transactions（取引データ）**: 売上、返品、取消などの取引情報
- **Open/Close Logs（開設精算ログ）**: 開店・閉店処理、精算情報
- **Cash In/Out Logs（入出金ログ）**: 現金の入出金記録

これらのデータは、リアルタイムまたはバッチで集約され、クラウドで分析・保管されます。

```mermaid
flowchart BT
    subgraph Edge["Edge Environment"]
        direction LR
        ECA2[Edge Cart] --> ES3[Edge Sync]
        ET3[Edge Terminal] --> ES3
    end

    subgraph Cloud["Cloud Environment"]
        direction LR
        CS3[Cloud Sync] --> CCA2[Cloud Cart]
        CS3 --> CT3[Cloud Terminal]
    end

    ES3 -->|Transaction Data<br/>Transactions from Cart<br/>Open/Close Logs, Cash In/Out Logs from Terminal| CS3

    style Cloud fill:#e1f5fe
    style Edge fill:#fff3e0
```

### エッジ → クラウド（ジャーナルデータ）
店舗で記録されたジャーナルデータはエッジからクラウドへ送信されます：

- **Electronic Journals（電子ジャーナル）**: 取引の詳細な記録
- **Audit Logs（監査ログ）**: 監査用の操作履歴

これらのデータは、コンプライアンスと監査要件を満たすために、確実にクラウドに保管されます。

```mermaid
flowchart BT
    subgraph Edge["Edge Environment"]
        direction LR
        EJ2[Edge Journal] --> ES5[Edge Sync]
    end

    subgraph Cloud["Cloud Environment"]
        direction LR
        CS5[Cloud Sync] --> CJ2[Cloud Journal]
    end

    ES5 -->|Journal Data<br/>Electronic Journals<br/>Audit Logs| CS5

    style Cloud fill:#e1f5fe
    style Edge fill:#fff3e0
```

### エッジ → クラウド（アプリケーションログ）
各サービスから生成されるログデータはエッジからクラウドへ送信されます：

- **App Logs（アプリログ）**: 各サービスのアプリケーションログ（システムイベント、エラー、デバッグ情報）
- **Request Logs（リクエストログ）**: 各サービスのAPIリクエスト/レスポンスログ

これらのログは、account、terminal、master-data、cart、report、journal、stock、syncの各サービスごとに生成され、システムの監視、トラブルシューティング、パフォーマンス分析に使用されます。

```mermaid
flowchart BT
    subgraph Edge["Edge Environment"]
        direction LR
        EA2[Edge Services<br/>All Services] --> ES6[Edge Sync]
    end

    subgraph Cloud["Cloud Environment"]
        direction LR
        CS6[Cloud Sync] --> CJ3[Cloud Journal ※仮]
    end

    ES6 -->|Application Logs<br/>App Logs, Request Logs<br/>per service| CS6

    style Cloud fill:#e1f5fe
    style Edge fill:#fff3e0
```

### 双方向同期（ターミナルデータ）
ターミナル関連のデータは双方向で同期される必要があります：

- **Tenant Info（テナント情報）**: 企業・組織の設定情報
- **Store Info（店舗情報）**: 店舗設定、営業時間
- **Terminal Info（端末情報）**: POS端末の設定、状態
- **Terminal Status（端末ステータス）**: オンライン/オフライン状態、稼働状況

これらのデータは、管理と運用の両面から双方向の同期が必要となります。

```mermaid
flowchart TB
    subgraph Cloud["Cloud Environment"]
        direction LR
        CT2[Cloud Terminal] <--> CS4[Cloud Sync]
    end

    subgraph Edge["Edge Environment"]
        direction LR
        ES4[Edge Sync] <--> ET2[Edge Terminal]
    end

    CS4 <-->|Terminal Data<br/>Tenant Info, Store Info<br/>Terminal Info, Terminal Status| ES4

    style Cloud fill:#e1f5fe
    style Edge fill:#fff3e0
```
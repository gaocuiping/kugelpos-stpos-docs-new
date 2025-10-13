# 実装計画書: アプリケーション更新管理機能

**Branch**: `002-notes-2-upgrade` | **Date**: 2025-10-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-notes-2-upgrade/spec.md`

## サマリー

本機能は、クラウドからエッジ端末（Edge/POS）へのアプリケーション更新を自動化し、店舗業務の継続性を保ちながらセキュアかつ効率的に配信するシステムです。

**主要要件**:
- エッジ端末の自動更新とオフライン耐性（P1）
- コンテナイメージの差分更新による帯域削減85%以上（P1）
- P2P優先度制御による店舗内高速配信（P2）
- 2段階更新による業務影響最小化（ダウンタイム1-3分）（P1）
- デバイス認証とセキュアな配信（P1）

**技術アプローチ**:
- Azure Container Registry + Harbor for Edge (P2P配信で90%帯域削減)
- Azure Blob Storage（バージョンフォルダ構造、3世代保持）
- 優先度ベースシード選択（priority: 0-99、フォールバック機構）
- Phase-based Update with Maintenance Window Control（Phase 1-9）
- JWT認証 + SHA256チェックサム（改ざん検出99.99999%）

## 技術コンテキスト

**Language/Version**: Python 3.12+
**Primary Dependencies**: FastAPI 0.104+, Motor 3.3+ (async MongoDB driver), Pydantic 2.5+, httpx 0.25+
**Storage**: MongoDB 7.0+ (テナント分離: `sync_{tenant_id}` データベース), Azure Blob Storage
**Testing**: pytest 7.4+, pytest-asyncio 0.21+
**Target Platform**:
  - Cloud: Azure Container Apps (Linux, auto-scaling 2-10 replicas)
  - Edge: Ubuntu 22.04 LTS (Docker + Docker Compose)
  - POS: Ubuntu 22.04 LTS (Docker + Docker Compose)

**Project Type**: マイクロサービス（既存のKugelpos POSシステムに新規サービス追加）

**Performance Goals**:
  - バージョンチェックAPI応答: p95 < 500ms
  - ファイルダウンロード: 400MB/10分以内（全サービス更新時）
  - 同時接続: 1,000台のエッジ端末
  - P2P配信速度向上: クラウド直接比50%以上高速化

**Constraints**:
  - ダウンタイム: 1-3分（Phase 6-8のみ）
  - チェックサム検証成功率: 99.9%以上
  - 自動ロールバック: 失敗検出から3分以内
  - JWTトークン有効期限: 1時間
  - リトライ上限: 3回（指数バックオフ: 1秒→2秒→4秒）

**Scale/Scope**:
  - 初期: エッジ端末100台、POS端末500台
  - 1年後: エッジ端末500台、POS端末5,000台
  - 3年後: エッジ端末1,000台、POS端末20,000台
  - サービス数: 8サービス（account, terminal, master-data, cart, report, journal, stock, sync）
  - イメージサイズ: 100-200MB/サービス

## 憲章チェック

*GATE: Phase 0開始前に必須。Phase 1設計後に再チェック。*

### Phase 0開始前チェック

| 憲章原則 | チェック項目 | ステータス | 備考 |
|---------|------------|---------|------|
| **I. マイクロサービス独立性** | 独立したデータベース | ✅ PASS | `sync_{tenant_id}` で完全分離 |
| | サービス間通信はDapr経由 | ✅ PASS | Cloud Sync ServiceがDapr Pub/Sub経由で更新イベント配信。Edge Sync ServiceはHTTP APIのみでDapr Pub/Sub不使用（P2P配信特化の軽量サービス） |
| | 共通ライブラリは純粋ユーティリティのみ | ✅ PASS | HttpClientHelper、DaprClientHelperを活用 |
| **II. 非同期優先** | すべてのI/O操作が非同期 | ✅ PASS | Motor (async MongoDB), httpx (async HTTP) |
| **III. テスト駆動開発** | Red-Green-Refactorサイクル | ✅ PASS | TDDで開発予定、カバレッジ目標80%以上 |
| **IV. イベント駆動アーキテクチャ** | Dapr Pub/Sub使用 | ✅ PASS | Cloud Sync Serviceが`update_complete`, `update_failed`トピックでイベント配信。Edge Sync ServiceはP2P配信のみでイベント配信不要 |
| **V. 回復力とエラーハンドリング** | Circuit Breaker実装 | ✅ PASS | HttpClientHelper、DaprClientHelperで実装済み |
| | Retry Pattern（指数バックオフ） | ✅ PASS | 最大3回、1秒→2秒→4秒 |
| | エラーコード体系（XXYYZZ） | ✅ PASS | XX=80（Syncサービス）、YY=機能、ZZ=エラー番号 |
| **VI. マルチテナンシー** | データベースレベル分離 | ✅ PASS | `sync_{tenant_id}` で厳格分離 |
| **VII. 可観測性** | 構造化ロギング（JSON） | ✅ PASS | correlation_id、tenant_code、edge_id含む |
| | 分散トレーシング | ✅ PASS | Daprの分散トレーシング活用 |
| **VIII. セキュリティファースト** | JWT認証 | ✅ PASS | edge_id + secret で認証、有効期限1時間 |
| | 機密データ環境変数管理 | ✅ PASS | .envファイル（.gitignore登録） |
| | SHA256チェックサム検証 | ✅ PASS | すべてのファイルとイメージで検証 |

**結果**: ✅ **全項目PASS - Phase 0開始可能**

### Phase 1設計後チェック

| 憲章原則 | チェック項目 | ステータス | 備考 |
|---------|------------|---------|------|
| **Repository Pattern** | AbstractRepository継承 | ✅ PASS | DeviceVersionRepository, UpdateHistoryRepository等（実装詳細: 既存commonsのAbstractRepositoryを継承し、データアクセス層を抽象化） |
| **State Machine Pattern** | 状態遷移管理 | ✅ PASS | DeviceVersionの update_status, download_status, apply_status |
| **コード品質基準** | Type Hints | ✅ PASS | すべての関数にtype hints追加 |
| | PEP 8準拠 | ✅ PASS | ruff format で自動整形 |

**結果**: ✅ **全項目PASS - Phase 2（tasks.md作成）へ進行可能**

**実装パターンの補足**:
- **Repository Pattern**: データアクセス層の抽象化。既存のKugelpos commonsライブラリの`AbstractRepository`を継承し、MongoDB操作を標準化します。spec.mdでは機能要件として記載せず、実装詳細として本plan.mdで管理します。
- **State Machine Pattern**: DeviceVersionエンティティの状態遷移（update_status, download_status, apply_status）を管理します。これもspec.mdの機能要件（FR-007～FR-011等）を実現するための実装手法です。

## プロジェクト構造

### ドキュメント（本機能）

```
specs/002-notes-2-upgrade/
├── spec.md              # 機能仕様書（完成）
├── plan.md              # 本ファイル（実装計画書）
├── research.md          # Phase 0成果物（技術調査報告書、完成）
├── data-model.md        # Phase 1成果物（データモデル設計、完成）
├── quickstart.md        # Phase 1成果物（クイックスタートガイド、完成）
├── contracts/           # Phase 1成果物（API契約、完成）
│   ├── version-management-api.yaml
│   ├── artifact-management-api.yaml
│   └── edge-sync-service-api.yaml
└── tasks.md             # Phase 2成果物（/speckit.tasks コマンドで生成）
```

### ソースコード（リポジトリルート）

既存のKugelposマイクロサービスアーキテクチャに新規サービス追加。

```
services/
├── sync/                # 新規追加: Sync Service
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── version_management.py    # バージョン管理API
│   │   │   │   ├── artifact_management.py   # アーティファクト管理API
│   │   │   │   └── sync.py                  # Edge Sync Service API
│   │   ├── models/
│   │   │   ├── device_version.py            # DeviceVersion モデル
│   │   │   ├── update_history.py            # UpdateHistory モデル
│   │   │   ├── edge_terminal.py             # EdgeTerminal モデル
│   │   │   └── manifest.py                  # Manifest モデル
│   │   ├── repositories/
│   │   │   ├── device_version_repository.py
│   │   │   ├── update_history_repository.py
│   │   │   └── edge_terminal_repository.py
│   │   ├── services/
│   │   │   ├── version_service.py           # バージョン管理ロジック
│   │   │   ├── artifact_service.py          # アーティファクト配信ロジック
│   │   │   ├── manifest_generator.py        # Manifest生成ロジック
│   │   │   ├── p2p_coordinator.py           # P2P優先度制御
│   │   │   └── auth_service.py              # JWT認証
│   │   ├── schemas/
│   │   │   ├── requests.py                  # APIリクエストスキーマ
│   │   │   └── responses.py                 # APIレスポンススキーマ
│   │   ├── config/
│   │   │   └── settings.py                  # 環境変数設定
│   │   ├── utils/
│   │   │   ├── checksum.py                  # SHA256チェックサム
│   │   │   └── blob_storage.py              # Azure Blob Storage操作
│   │   └── main.py                          # FastAPI アプリケーション
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_version_service.py
│   │   │   ├── test_manifest_generator.py
│   │   │   └── test_p2p_coordinator.py
│   │   ├── integration/
│   │   │   ├── test_version_management_api.py
│   │   │   └── test_artifact_management_api.py
│   │   └── e2e/
│   │       └── test_update_workflow.py
│   ├── Pipfile
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── account/             # 既存サービス（認証）
├── terminal/            # 既存サービス（ターミナル管理）
├── master-data/         # 既存サービス（マスタデータ）
├── cart/                # 既存サービス（カート）
├── report/              # 既存サービス（レポート）
├── journal/             # 既存サービス（ジャーナル）
└── stock/               # 既存サービス（在庫）

scripts/
├── edge-startup.sh      # 新規追加: Edge端末用起動スクリプト
└── pos-startup.sh       # 新規追加: POS端末用起動スクリプト
```

**構造決定**:
- **単一マイクロサービス追加**: 既存のKugelposアーキテクチャにSyncサービスを追加
- **クライアントスクリプト**: エッジ端末とPOS端末で実行される起動スクリプト（Bash）
- **API契約**: OpenAPI 3.0形式で定義（contracts/）
- **テスト構造**: ユニット、統合、E2Eの3層構造

## 複雑性トラッキング

本機能は憲章違反なし。すべての原則に準拠した設計。

| 違反項目 | 必要な理由 | 却下された代替案とその理由 |
|---------|-----------|------------------------|
| なし | - | - |

## Phase 0: 技術調査（完了）

✅ **完了**: research.md作成済み

**成果物**:
- Container Registry選択: Azure Container Registry Premium + Harbor for Edge
- Blob Storage構造: バージョンフォルダ構造（v1.2.3形式）
- P2P配信実装: 優先度ベースシード選択（priority: 0-99）
- 2段階更新: Phase-based Update with Maintenance Window Control
- 自動ロールバック: 直前のバージョンへの自動復旧
- セキュリティ: JWT認証 + SHA256チェックサム
- スケーラビリティ: 水平スケーリング + テナント分離

## Phase 1: 設計とAPI契約（完了）

✅ **完了**: data-model.md、contracts/、quickstart.md作成済み

**成果物**:

1. **data-model.md** (992行)
   - 5つの主要エンティティのMongoDBスキーマ定義
   - インデックス設計（クエリパターン最適化）
   - Pydanticバリデーションルール
   - 状態遷移図（DeviceVersion）
   - リレーションシップ図

2. **contracts/** (OpenAPI 3.0 YAML形式)
   - version-management-api.yaml (865行): 5エンドポイント
   - artifact-management-api.yaml (453行): 3エンドポイント
   - edge-sync-service-api.yaml (254行): 3エンドポイント

3. **quickstart.md** (746行)
   - ローカル開発環境セットアップ
   - サービス起動手順
   - API動作確認
   - テスト実行
   - トラブルシューティング

**エージェントコンテキスト更新**:
✅ 完了: CLAUDE.mdにデータベース情報追加

## Phase 2: タスク生成（次のステップ）

**実行コマンド**: `/speckit.tasks`

**期待される成果物**: tasks.md（実装タスクの依存関係順リスト）

**推奨タスク構造**:

1. **Phase 2.1: 基盤構築** (優先度P1)
   - Syncサービスの骨格作成（FastAPI、ディレクトリ構造）
   - MongoDBスキーマ実装（DeviceVersion、UpdateHistory、EdgeTerminal）
   - Repository実装（AbstractRepository継承）
   - 環境変数設定（settings.py）

2. **Phase 2.2: 認証機能** (優先度P1)
   - JWT認証サービス実装
   - edge_idとsecret検証
   - トークン発行・検証
   - ユニットテスト（TDD）

3. **Phase 2.3: バージョン管理API** (優先度P1)
   - バージョンチェックAPI実装
   - Manifest生成ロジック
   - P2P優先度制御
   - 統合テスト

4. **Phase 2.4: アーティファクト管理API** (優先度P1)
   - ファイルダウンロードAPI実装
   - Azure Blob Storage連携
   - SHA256チェックサム検証
   - ダウンロード完了・適用完了通知

5. **Phase 2.5: Edge Sync Service API** (優先度P2)
   - P2P配信API実装
   - ローカルキャッシュ管理
   - フォールバック機構

6. **Phase 2.6: クライアントスクリプト** (優先度P1)
   - edge-startup.sh実装（2段階更新ロジック）
   - pos-startup.sh実装
   - 自動ロールバック機構
   - ヘルスチェック

7. **Phase 2.7: E2Eテスト** (優先度P1)
   - 全体ワークフローテスト
   - P2P配信テスト
   - 自動ロールバックテスト

8. **Phase 2.8: デプロイ準備** (優先度P2)
   - Dockerfile作成
   - docker-compose.yml作成
   - Azure Bicep（Infrastructure as Code）
   - CI/CDパイプライン

## 実装順序の推奨

1. **TDD原則**: テストファーストで開発（Red-Green-Refactor）
2. **優先度順**: P1機能から実装（自動更新、認証、バージョン管理）
3. **段階的統合**: 各Phase完了後に統合テスト実行
4. **継続的デプロイ**: 各Phaseで動作する最小機能を確保

## リスクと軽減策

| リスク | 影響度 | 軽減策 |
|-------|-------|-------|
| P2P配信の複雑性 | 高 | 段階的実装（まずクラウド直接配信、後にP2P追加） |
| 大規模同時接続 | 中 | 負荷テスト実施、Auto-scaling設定 |
| Azure Blob Storageコスト | 中 | 古いバージョンの自動削除（3世代保持） |
| 自動ロールバック失敗 | 高 | 手動ロールバック手順のドキュメント化 |

## 次のステップ

1. ✅ **Phase 0完了**: research.md作成済み
2. ✅ **Phase 1完了**: data-model.md、contracts/、quickstart.md作成済み
3. 🔄 **Phase 2開始**: `/speckit.tasks` コマンドでtasks.md生成
4. 🔄 **実装開始**: TDD原則に従い、Phase 2.1から着手

---

**作成日**: 2025-10-13
**最終更新**: 2025-10-13
**ステータス**: Phase 1完了、Phase 2準備完了

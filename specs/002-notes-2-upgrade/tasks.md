---
description: "アプリケーション更新管理機能のタスクリスト"
---

# Tasks: アプリケーション更新管理機能

**Input**: `/specs/002-notes-2-upgrade/`の設計ドキュメント
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: TDD原則に従い、各ユーザーストーリーにテストタスクを含めます（プロジェクト憲章およびplan.mdでカバレッジ目標80%以上を明示）

**Organization**: タスクはユーザーストーリーごとにグループ化され、各ストーリーの独立した実装とテストを可能にします

## Format: `[ID] [P?] [Story] Description`
- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: タスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明に正確なファイルパスを含める

## パス規則
- **Syncサービス**: `services/sync/app/`
- **テスト**: `services/sync/tests/`
- **クライアントスクリプト**: `scripts/`

---

## Phase 1: セットアップ（共有インフラ）

**目的**: プロジェクト初期化と基本構造

- [ ] T001 [P] services/sync/ディレクトリ構造を作成（app/, tests/, config/）
- [ ] T002 [P] services/sync/Pipfileを作成し依存関係を定義（FastAPI 0.104+, Motor 3.3+, Pydantic 2.5+, httpx 0.25+, pytest 7.4+, pytest-asyncio 0.21+）
- [ ] T003 [P] services/sync/Dockerfileを作成
- [ ] T004 [P] services/sync/docker-compose.ymlを作成
- [ ] T005 [P] services/sync/.env.sampleを作成（MongoDB URI, Redis URI, Azure Blob Storage接続文字列等）
- [ ] T006 [P] ruff設定ファイル（pyproject.toml）を作成してコード品質基準を設定

---

## Phase 2: 基盤（ブロッキング前提条件）

**目的**: すべてのユーザーストーリーを実装する前に完了する必要があるコアインフラ

**⚠️ CRITICAL**: このフェーズが完了するまで、ユーザーストーリー作業は開始できません

- [ ] T007 services/sync/app/config/settings.pyに環境変数設定クラスを実装
- [ ] T008 services/sync/app/main.pyにFastAPIアプリケーションの骨格を作成（起動、ヘルスチェックエンドポイント）
- [ ] T009 [P] services/sync/app/models/base.pyにBaseDocumentModel（commons継承）を実装
- [ ] T010 [P] services/sync/app/repositories/base.pyにAbstractRepository継承の基底クラスを作成
- [ ] T011 [P] services/sync/app/utils/database.pyにMongoDB接続マネージャーを実装（Motor async、テナント分離: `sync_{tenant_id}`）
- [ ] T012 [P] services/sync/app/utils/logger.pyに構造化ロギング（JSON、correlation_id、tenant_code、edge_id）を実装
- [ ] T013 [P] services/sync/app/schemas/error.pyにエラーレスポンススキーマ（エラーコードXXYYZZ、XX=80）を実装
- [ ] T014 [P] services/sync/app/middleware/request_logging.pyにリクエストロギングミドルウェアを実装
- [ ] T015 [P] services/sync/app/middleware/error_handler.pyにグローバルエラーハンドラーを実装
- [ ] T016 services/sync/tests/conftest.pyにpytestフィクスチャ（テストDB、モックデータ）を作成

**Checkpoint**: 基盤準備完了 - ユーザーストーリー実装を並列開始可能

---

## Phase 3: ユーザーストーリー 6 - デバイス認証とセキュアな配信 (優先度: P1) 🎯

**Goal**: エッジ端末がedge_idとsecretで認証し、JWTトークンを取得してセキュアにAPIアクセスできるようにする

**Independent Test**: エッジ端末が有効なedge_idとsecretで認証してJWTトークンを取得し、バージョンチェックAPIにアクセスできることを確認。無効なsecretでは401エラーが返されることを検証

### Tests for US6

**NOTE: これらのテストを最初に記述し、実装前に失敗することを確認**

- [ ] T017 [P] [US6] services/sync/tests/unit/test_auth_service.pyにJWT認証サービスのユニットテストを作成（トークン生成・検証、edge_id/secret検証）
- [ ] T018 [P] [US6] services/sync/tests/integration/test_auth_api.pyに認証APIの統合テストを作成（/auth エンドポイント、成功/失敗ケース）

### Implementation for US6

- [ ] T019 [P] [US6] services/sync/app/models/edge_terminal.pyにEdgeTerminalモデルを実装（edge_id, tenant_id, store_code, device_type, is_p2p_seed, p2p_priority, secret）
- [ ] T020 [US6] services/sync/app/repositories/edge_terminal_repository.pyにEdgeTerminalRepositoryを実装（find_by_edge_id, verify_secret）
- [ ] T021 [US6] services/sync/app/services/auth_service.pyにJWT認証サービスを実装（authenticate_device, generate_token, verify_token、有効期限1時間）
- [ ] T022 [US6] services/sync/app/schemas/auth.pyに認証リクエスト/レスポンススキーマを実装（AuthRequest, AuthResponse）
- [ ] T023 [US6] services/sync/app/api/v1/version_management.pyに /version-management/auth エンドポイントを実装
- [ ] T024 [US6] services/sync/app/middleware/jwt_auth.pyにJWT認証ミドルウェアを実装（Bearer token検証、401エラー）
- [ ] T025 [US6] services/sync/app/utils/checksum.pyにSHA256チェックサム検証ユーティリティを実装

**Checkpoint**: デバイス認証機能が完全に動作し、独立してテスト可能

---

## Phase 4: ユーザーストーリー 1 - エッジ端末の自動更新とオフライン耐性 (優先度: P1) 🎯 MVP

**Goal**: エッジ端末が15分ごとにバージョンチェックを実行し、新バージョンをダウンロード・適用できるようにする（ネットワーク障害時でも業務継続）

**Independent Test**: クラウドに新バージョンを登録し、エッジ端末がバージョンチェックを実行して更新を検知、ダウンロード完了後に指定時刻に自動適用され、サービスが正常起動することを確認。ネットワーク切断時でも現在バージョンで動作継続することを検証

### Tests for US1

- [ ] T026 [P] [US1] services/sync/tests/unit/test_version_service.pyにバージョン管理サービスのユニットテストを作成（バージョンチェック、更新判定）
- [ ] T027 [P] [US1] services/sync/tests/unit/test_manifest_generator.pyにManifest生成ロジックのユニットテストを作成
- [ ] T028 [P] [US1] services/sync/tests/integration/test_version_check_api.pyにバージョンチェックAPIの統合テストを作成（/version-management/check エンドポイント）
- [ ] T029 [P] [US1] services/sync/tests/integration/test_download_api.pyにダウンロードAPIの統合テストを作成（/artifact-management/download エンドポイント）
- [ ] T030 [P] [US1] services/sync/tests/e2e/test_update_workflow.pyにエンドツーエンドテストを作成（バージョンチェック→ダウンロード→適用完了通知の全フロー）

### Implementation for US1

- [ ] T031 [P] [US1] services/sync/app/models/device_version.pyにDeviceVersionモデルを実装（edge_id, device_type, current_version, target_version, update_status, download_status, apply_status等）
- [ ] T032 [P] [US1] services/sync/app/models/update_history.pyにUpdateHistoryモデルを実装（update_id, edge_id, from_version, to_version, status等）
- [ ] T033 [P] [US1] services/sync/app/models/manifest.pyにManifestモデルを実装（manifest_version, device_type, target_version, artifacts, container_images, apply_schedule）
- [ ] T034 [P] [US1] services/sync/app/repositories/device_version_repository.pyにDeviceVersionRepositoryを実装（find_by_edge_id, update_status, save等）
- [ ] T035 [P] [US1] services/sync/app/repositories/update_history_repository.pyにUpdateHistoryRepositoryを実装（create, find_by_edge_id等）
- [ ] T036 [US1] services/sync/app/services/version_service.pyにバージョン管理サービスを実装（check_version, determine_update_needed）
- [ ] T037 [US1] services/sync/app/services/manifest_generator.pyにManifest生成ロジックを実装（generate_manifest, resolve_artifacts）
- [ ] T038 [US1] services/sync/app/utils/blob_storage.pyにAzure Blob Storage操作ユーティリティを実装（get_artifact_url, verify_artifact_exists）
- [ ] T039 [US1] services/sync/app/schemas/version.pyにバージョン管理スキーマを実装（VersionCheckRequest, VersionCheckResponse）
- [ ] T040 [US1] services/sync/app/api/v1/version_management.pyに /version-management/check エンドポイントを実装
- [ ] T041 [US1] services/sync/app/schemas/artifact.pyにアーティファクト管理スキーマを実装（DownloadRequest, DownloadCompleteRequest, ApplyCompleteRequest）
- [ ] T042 [US1] services/sync/app/api/v1/artifact_management.pyに /artifact-management/download, /download-complete, /apply-complete エンドポイントを実装
- [ ] T043 [US1] services/sync/app/services/artifact_service.pyにアーティファクト配信ロジックを実装（get_download_url, record_download_complete, record_apply_complete）
- [ ] T044 [US1] services/sync/app/services/pubsub_manager.pyにDapr Pub/Sub通知サービスを実装（publish_update_complete, publish_update_failed）
- [ ] T045 [US1] scripts/edge-startup.shにエッジ端末用起動スクリプトを実装（バージョンチェック、ダウンロード、適用の2段階更新ロジック）
- [ ] T046 [US1] scripts/common/update-utils.shに共通更新ユーティリティ関数を実装（チェックサム検証、バックアップ、ロールバック）

**Checkpoint**: エッジ端末の自動更新機能が完全に動作し、独立してテスト可能（MVPとして機能）

---

## Phase 5: ユーザーストーリー 7 - 2段階更新による業務影響最小化 (優先度: P1)

**Goal**: ダウンロードフェーズと適用フェーズを分離し、営業時間中はダウンロードのみ実行、メンテナンスウィンドウ内に適用を自動実行

**Independent Test**: 営業時間中にダウンロードがサービス停止なしで完了し、scheduled_at時刻（深夜2:00）のメンテナンスウィンドウ内にのみ適用フェーズが実行され、1-3分でサービスが再起動することを検証

### Tests for US7

- [ ] T047 [P] [US7] services/sync/tests/unit/test_phase_manager.pyに2段階更新ロジックのユニットテストを作成（Phase 1-3: ダウンロード、Phase 4-9: 適用）
- [ ] T048 [P] [US7] services/sync/tests/integration/test_maintenance_window.pyにメンテナンスウィンドウ制御の統合テストを作成

### Implementation for US7

- [ ] T049 [P] [US7] services/sync/app/models/pending_update.pyにPendingUpdateモデルを実装（version, download_status, download_completed_at, verification_status, ready_to_apply等）
- [ ] T050 [US7] services/sync/app/services/phase_manager.pyに2段階更新管理サービスを実装（execute_download_phase, execute_apply_phase、メンテナンスウィンドウ判定）
- [ ] T051 [US7] scripts/edge-startup.shにメンテナンスウィンドウ制御ロジックを追加（scheduled_at時刻判定、maintenance_window期間内の適用実行）
- [ ] T052 [US7] scripts/common/phase-executor.shにPhase 1-9実行スクリプトを実装（ダウンロードフェーズ、適用フェーズの分離実行、FR-006: 設定ファイル・画像・ドキュメントの指定パス配置を含む。Manifest内のartifactsのdestinationフィールドに従い、docker-compose.yml、.conf、.yaml、.json、画像ファイル、ドキュメントを適切なパスに配置）
- [ ] T053 [US7] scripts/common/rollback.shに自動ロールバックスクリプトを実装（適用失敗時の直前バージョン復元）
- [ ] T054 [US7] scripts/common/health-check.shにヘルスチェックスクリプトを実装（/healthエンドポイント、最大3回リトライ、10秒間隔）

**Checkpoint**: 2段階更新機能が完全に動作し、営業時間中の業務への影響が最小化されることを確認

---

## Phase 6: ユーザーストーリー 2 - コンテナイメージの差分更新 (優先度: P1)

**Goal**: 変更されたマイクロサービスのコンテナイメージのみをダウンロードし、Dockerレイヤーキャッシュを活用して帯域を削減

**Independent Test**: 8つのサービスのうち1つ（例: cart）のみを更新し、変更されたイメージのみがダウンロードされることを確認。Dockerレイヤーの再利用により、ダウンロードサイズが大幅に削減されることを検証（帯域削減率85%以上）

### Tests for US2

- [ ] T055 [P] [US2] services/sync/tests/unit/test_container_diff_service.pyにコンテナ差分判定ロジックのユニットテストを作成
- [ ] T056 [P] [US2] services/sync/tests/integration/test_container_download.pyにコンテナイメージダウンロードの統合テストを作成（差分更新、全サービス更新の比較）

### Implementation for US2

- [ ] T057 [US2] services/sync/app/services/container_service.pyにコンテナイメージ管理サービスを実装（detect_changed_services, generate_container_manifest、8サービス: account, terminal, master-data, cart, report, journal, stock, sync）
- [ ] T058 [US2] services/sync/app/services/registry_service.pyにContainer Registry操作サービスを実装（Azure Container Registry連携、イメージダイジェスト取得）
- [ ] T059 [US2] scripts/common/docker-pull.shにDockerイメージプルスクリプトを実装（レイヤーキャッシュ活用、プログレス表示）
- [ ] T060 [US2] scripts/common/docker-verify.shにイメージダイジェスト検証スクリプトを実装（SHA256チェックサム）

**Checkpoint**: コンテナイメージの差分更新機能が完全に動作し、帯域削減効果を確認

---

## Phase 7: ユーザーストーリー 3 - スクリプトとモジュールの自己更新 (優先度: P2)

**Goal**: 起動スクリプト（startup.sh）自身やPythonライブラリ（.whl）、システムパッケージ（.deb）を安全に更新

**Independent Test**: startup.shのバグ修正版を配信し、エッジ端末がダウンロード・適用後、次回起動時に新スクリプトで起動することを確認。Pythonライブラリ（.whl）の更新により、Manifestパーサーが新機能を使用できることを検証

### Tests for US3

- [ ] T061 [P] [US3] services/sync/tests/unit/test_script_updater.pyにスクリプト更新ロジックのユニットテストを作成
- [ ] T062 [P] [US3] services/sync/tests/integration/test_module_install.pyにモジュールインストールの統合テストを作成（.whl、.deb）

### Implementation for US3

- [ ] T063 [US3] services/sync/app/services/script_service.pyにスクリプト更新サービスを実装（manage_script_artifacts, validate_script_integrity）
- [ ] T064 [US3] scripts/common/script-update.shにスクリプト自己更新ロジックを実装（バックアップ、置換、実行権限755設定）
- [ ] T065 [US3] scripts/common/module-install.shにモジュールインストールスクリプトを実装（pip install .whl、apt install .deb）
- [ ] T066 [US3] scripts/common/verify-executable.shに実行可能性検証スクリプトを実装（構文チェック、依存関係確認）

**Checkpoint**: スクリプトとモジュールの自己更新機能が完全に動作し、安全に更新可能

---

## Phase 8: ユーザーストーリー 4 - P2P優先度制御による店舗内高速ダウンロード (優先度: P2)

**Goal**: 同一店舗内の複数エッジ端末間でP2P優先度制御を用いてファイルとコンテナイメージを効率的に配信し、インターネット帯域を削減

**Independent Test**: 専用Edge端末（priority=0）とPOS端末2台（priority=99）の店舗で、専用Edge端末がクラウドからダウンロード完了後、POS端末が専用Edge端末から取得し、ダウンロード時間が50%短縮されることを確認。POS-001停止時はPOS-002がクラウドへフォールバックすることを検証

### Tests for US4

- [ ] T067 [P] [US4] services/sync/tests/unit/test_p2p_coordinator.pyにP2P優先度制御ロジックのユニットテストを作成（シード選択、フォールバック）
- [ ] T068 [P] [US4] services/sync/tests/integration/test_p2p_distribution.pyにP2P配信の統合テストを作成（パターン1: 専用Edge、パターン2: POS-only）
- [ ] T069 [P] [US4] services/sync/tests/integration/test_seed_failover.pyにシード障害時フォールバックの統合テストを作成

### Implementation for US4

- [ ] T070 [US4] services/sync/app/services/p2p_coordinator.pyにP2P優先度制御サービスを実装（select_seed_by_priority, generate_seed_list、priority: 0-99、フォールバック機構）
- [ ] T071 [US4] services/sync/app/api/v1/sync.pyにEdge Sync Service APIを実装（/sync/version, /sync/artifacts/{artifact_name}, /sync/health エンドポイント）
- [ ] T072 [US4] services/sync/app/services/cache_manager.pyにローカルキャッシュ管理サービスを実装（store_artifact, get_artifact、ファイルとコンテナイメージ）
- [ ] T073 [US4] scripts/common/p2p-download.shにP2P優先度制御ダウンロードスクリプトを実装（priority昇順試行: 0→1→2...、全シード失敗時クラウドフォールバック）
- [ ] T074 [US4] scripts/common/registry-proxy.shにシード端末Registry代理スクリプトを実装（Harbor for Edge、docker pull代理）
- [ ] T075 [US4] scripts/pos-startup.shにPOS端末用起動スクリプトを実装（P2P優先、Edge Sync Service APIアクセス）

**Checkpoint**: P2P配信機能が完全に動作し、店舗内ダウンロード速度が50%以上向上することを確認

---

## Phase 9: ユーザーストーリー 5 - 更新履歴とバージョン状態の取得API (優先度: P3)

**Goal**: 管理者向けシステムがAPIを通じて全エッジ端末のバージョン状態、更新履歴を取得できるようにする

**Independent Test**: 10台のエッジ端末に対して更新を配信し、APIを通じてダウンロード状態（完了/進行中/失敗）、適用状態、更新履歴を取得できることを検証

### Tests for US5

- [ ] T076 [P] [US5] services/sync/tests/integration/test_device_list_api.pyにデバイス一覧取得APIの統合テストを作成（/devices エンドポイント、フィルタパラメータ）
- [ ] T077 [P] [US5] services/sync/tests/integration/test_device_detail_api.pyにデバイス詳細取得APIの統合テストを作成（/devices/{edge_id} エンドポイント）
- [ ] T078 [P] [US5] services/sync/tests/integration/test_history_api.pyに更新履歴取得APIの統合テストを作成（/devices/{edge_id}/history エンドポイント）

### Implementation for US5

- [ ] T079 [P] [US5] services/sync/app/schemas/device.pyにデバイス管理スキーマを実装（DeviceListResponse, DeviceDetailResponse, DeviceHistoryResponse）
- [ ] T080 [US5] services/sync/app/services/device_service.pyにデバイス管理サービスを実装（list_devices, get_device_detail, get_device_history、フィルタ機能）
- [ ] T081 [US5] services/sync/app/api/v1/version_management.pyに /devices, /devices/{edge_id}, /devices/{edge_id}/history エンドポイントを実装
- [ ] T082 [US5] services/sync/app/utils/pagination.pyにページネーションユーティリティを実装（limit, offset、デフォルト100件）

**Checkpoint**: 管理者向けAPI機能が完全に動作し、全エッジ端末の状態を一元管理可能

---

## Phase 10: Polish & Cross-Cutting Concerns

**目的**: 複数のユーザーストーリーに影響する改善

- [ ] T083 [P] services/sync/app/utils/retry.pyにリトライ機構を実装（指数バックオフ: 1秒→2秒→4秒、最大3回）
- [ ] T084 [P] services/sync/app/utils/circuit_breaker.pyにCircuit Breaker実装を追加（HttpClientHelper、DaprClientHelper活用）
- [ ] T085 [P] services/sync/README.mdにサービスドキュメントを作成（概要、セットアップ、API仕様へのリンク）
- [ ] T086 [P] scripts/README.mdにクライアントスクリプトドキュメントを作成（edge-startup.sh、pos-startup.shの使用方法）
- [ ] T087 コードクリーンアップとリファクタリング（重複コード削除、変数名改善）
- [ ] T088 [P] services/sync/tests/performance/test_concurrent_requests.pyに負荷テストを作成（1,000台同時接続、応答時間p95 < 500ms、SC-004帯域削減率85%以上の検証を含む。測定方法: 全サービス更新時（8サービス×400MB=3200MB）と差分更新時（1サービス=400MB未満、Dockerレイヤーキャッシュでさらに削減）のダウンロードサイズを比較、削減率=(全体-差分)/全体×100）
- [ ] T089 [P] services/sync/app/utils/metrics.pyにメトリクス収集ユーティリティを実装（API応答時間、ダウンロードサイズ、エラー率）
- [ ] T090 セキュリティ強化（入力バリデーション、SQLインジェクション対策、CORS設定）
- [ ] T091 quickstart.md検証を実行（ローカル開発環境セットアップ、サービス起動、API動作確認）
- [ ] T092 [P] services/sync/.dockerignoreを作成
- [ ] T093 [P] services/sync/.gitignoreを作成（.env、__pycache__、.pytest_cache等）
- [ ] T094 services/sync/tests/unit/配下の残りのユニットテストを追加（各サービス、リポジトリ、ユーティリティ）
- [ ] T095 カバレッジレポートを生成（pytest --cov=app tests/、目標80%以上）

---

## 依存関係と実行順序

### フェーズ依存関係

- **Setup (Phase 1)**: 依存関係なし - 即座に開始可能
- **Foundational (Phase 2)**: Setupの完了に依存 - すべてのユーザーストーリーをブロック
- **User Stories (Phase 3-9)**: すべてFoundationalフェーズの完了に依存
  - リソースがあれば並列実行可能
  - または優先度順に順次実行（P1 → P2 → P3）
- **Polish (Phase 10)**: 完了させたいすべてのユーザーストーリーの完了に依存

### ユーザーストーリー依存関係

- **US6 (P1) - デバイス認証**: Foundational完了後に開始可能 - 他ストーリーへの依存なし（他のすべてのストーリーがこれに依存）
- **US1 (P1) - 自動更新**: US6完了後に開始可能（認証が必要）
- **US7 (P1) - 2段階更新**: US1完了後に開始可能（US1の拡張）
- **US2 (P1) - コンテナ差分更新**: US1完了後に開始可能（US1の拡張）
- **US3 (P2) - スクリプト自己更新**: US1完了後に開始可能（US1の拡張）
- **US4 (P2) - P2P配信**: US1完了後に開始可能（US1と統合するが独立してテスト可能）
- **US5 (P3) - 管理者API**: US1完了後に開始可能（US1のデータを参照するが独立）

### 各ユーザーストーリー内

- Tests（含まれる場合）は実装前に記述し、失敗することを確認
- Models → Services → Endpoints
- コア実装 → 統合
- ストーリー完了後、次の優先度に移行

### 並列実行機会

- Setup内のすべての[P]タスクは並列実行可能
- Foundational内のすべての[P]タスク（Phase 2内）は並列実行可能
- Foundationalフェーズ完了後、US6を最初に実装（他のストーリーがUS6に依存）
- US6完了後、US1, US2, US3, US4, US5を並列実行可能（チーム容量がある場合）
- ユーザーストーリー内の[P]マークされたテストは並列実行可能
- ストーリー内の[P]マークされたモデルは並列実行可能
- 異なるユーザーストーリーは異なるチームメンバーが並列作業可能

---

## 並列実行例: ユーザーストーリー 1

```bash
# US1のすべてのテストを一緒に起動:
Task: "services/sync/tests/unit/test_version_service.pyにバージョン管理サービスのユニットテストを作成"
Task: "services/sync/tests/unit/test_manifest_generator.pyにManifest生成ロジックのユニットテストを作成"
Task: "services/sync/tests/integration/test_version_check_api.pyにバージョンチェックAPIの統合テストを作成"
Task: "services/sync/tests/integration/test_download_api.pyにダウンロードAPIの統合テストを作成"
Task: "services/sync/tests/e2e/test_update_workflow.pyにエンドツーエンドテストを作成"

# US1のすべてのモデルを一緒に起動:
Task: "services/sync/app/models/device_version.pyにDeviceVersionモデルを実装"
Task: "services/sync/app/models/update_history.pyにUpdateHistoryモデルを実装"
Task: "services/sync/app/models/manifest.pyにManifestモデルを実装"

# US1のすべてのリポジトリを一緒に起動:
Task: "services/sync/app/repositories/device_version_repository.pyにDeviceVersionRepositoryを実装"
Task: "services/sync/app/repositories/update_history_repository.pyにUpdateHistoryRepositoryを実装"
```

---

## 実装戦略

### MVP First (ユーザーストーリー 6 と 1 のみ)

1. Phase 1: Setup を完了
2. Phase 2: Foundational を完了（重要 - すべてのストーリーをブロック）
3. Phase 3: ユーザーストーリー 6 を完了（認証 - 他のストーリーの前提条件）
4. Phase 4: ユーザーストーリー 1 を完了（自動更新のコア機能）
5. **STOP and VALIDATE**: ユーザーストーリー 6 と 1 を独立してテスト
6. 準備ができればデプロイ/デモ

### 段階的デリバリー

1. Setup + Foundational を完了 → 基盤準備完了
2. US6 を追加 → 独立してテスト → デプロイ/デモ（認証基盤）
3. US1 を追加 → 独立してテスト → デプロイ/デモ（MVP！）
4. US7 を追加 → 独立してテスト → デプロイ/デモ（2段階更新）
5. US2 を追加 → 独立してテスト → デプロイ/デモ（帯域削減）
6. US3 を追加 → 独立してテスト → デプロイ/デモ（スクリプト更新）
7. US4 を追加 → 独立してテスト → デプロイ/デモ（P2P配信）
8. US5 を追加 → 独立してテスト → デプロイ/デモ（管理者API）
9. 各ストーリーは以前のストーリーを壊すことなく価値を追加

### 並列チーム戦略

複数の開発者がいる場合:

1. チームで一緒にSetup + Foundationalを完了
2. Foundational完了後:
   - 全員でUS6を完了（他のストーリーの前提条件）
   - その後:
     - Developer A: ユーザーストーリー 1
     - Developer B: ユーザーストーリー 2
     - Developer C: ユーザーストーリー 3
     - Developer D: ユーザーストーリー 4
     - Developer E: ユーザーストーリー 5
3. ストーリーは独立して完了し、統合

---

## Notes

- [P]タスク = 異なるファイル、依存関係なし
- [Story]ラベルはタスクを特定のユーザーストーリーにマッピングし、トレーサビリティを確保
- 各ユーザーストーリーは独立して完了およびテスト可能であるべき
- 実装前にテストが失敗することを確認
- 各タスクまたは論理グループの後にコミット
- 任意のチェックポイントで停止してストーリーを独立して検証
- 避けるべき: 曖昧なタスク、同じファイルの競合、独立性を壊すストーリー間依存関係
- TDD原則に従い、Red-Green-Refactorサイクルで開発
- カバレッジ目標80%以上を維持
- すべてのコードはruff formatで整形
- すべての関数にtype hintsを追加
- エラーコードはXXYYZZ形式（XX=80: Syncサービス）
- すべてのI/O操作は非同期（async/await）
- 憲章の8つのコアプリンシプルに準拠

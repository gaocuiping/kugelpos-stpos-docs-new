# Terminal サービス プロフェッショナルテストケース設計書

本ドキュメントは、Terminal サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルな测试用例群です。

### 状態 (Status) の定義
| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB/API）を Mock し、各モジュールの純粋なロジック、状態遷移、および例外処理を検証する。

### 1.1 状態管理 & サービスフロー (`TerminalService`)
| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **TM-U-001** | `TerminalService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_check_terminal_status_matrix` <br> *(待追加：状態遷移マトリクスの網羅検証)* | 現在の状態（Closed/Opened等）に対し、許可されない FunctionMode 変更が全て拒否されること。 |
| **TM-U-002** | `TerminalService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_open_terminal_date_rollover` <br> *(待追加：営業日付更新ロジック)* | 前回の営業日と現在日付が異なる場合、`open_counter` が 1 にリセットされ日付が更新されること。 |
| **TM-U-003** | `TerminalService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_sign_in_already_signed_in` | すでにサインイン済みの端末に対し、別の StaffID でサインインを試みた際に `TerminalAlreadySignedInException` が送出されること。 |

### 1.2 通信レジリエンス (`PubsubManager`)
| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **TM-U-101** | `PubsubManager` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_pubsub_circuit_breaker` <br> *(待追加：サーキットブレーカー検証)* | Dapr 側がエラーを返却した際、非ブロッキングでエラーが処理され、後続の業務プロセスが中断されないこと。 |

---

## 2. 結合测试 (Integration Tests)
**目的**: データベース（MongoDB）、Dapr サービス、およびリポジトリ間のデータ連携を検証する。

| ID | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **TM-I-001** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_terminal_operations` <br> *(# Test create Terminal with token)* | 登録された端末情報（MAC/ID）が DB に正しく永続化され、API Key が発行されること。 |
| **TM-I-002** | `Staff Repo` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_terminal_operations` <br> *(# Test Terminal Sign In with API key)* | 実在する StaffID を用いたサインイン時に、スタッフ名等の詳細が正常にマージされること。 |
| **TM-I-003** | `Log Repo` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_terminal_operations` <br> *(# Test Cash In with API key)* | 入出金ログが生成され、レシート/ジャーナル用テキストが正しく構築されること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、複雑な業務フローをエンドツーエンドで検証する。

| ID | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|
| **TM-S-001** | 端末ライフサイクル | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. 端末登録<br>2. 状態確認 (X-API-KEY)<br>3. `Sign-in`<br>4. プロパティ更新 | `test_terminal_operations` | 認可・認証（Bearer / API Key）の切り替えが正常に機能すること。 |
| **TM-S-002** | 営業開始・終了 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `OpenTerminal` モード変更<br>2. `Open` (準備金入力)<br>3. `Close` (精算入力) | `test_terminal_operations` | 営業日単位のカウンタ、および物理金額との整合性チェック。 |
| **TM-S-003** | 入出金管理 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. `CashInOut` モード変更<br>2. `Cash In` 実行<br>3. `Cash Out` 実行 | `test_terminal_operations` | 取引種別に応じた正負金額の記録、ジャーナル出力の完整性。 |

---

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: テスト環境のセットアップおよび共通クレンジングを共通化する。

| 関数名 (Helper Function) | 役割 (Responsibility) | 备注 (Notes) |
|:---|:---|:---|
| `test_setup_data` | テナント/店舗の初期マスター投入 | テスト実行前の環境構築 |
| `test_clean_data` | 全データ物理削除 | 冪等性確保のための後処理 |
| `conftest.http_client` | FastAPI AsyncClient 提供 | 非同期 HTTP 通信の基盤 |

> [!NOTE]
> 自动化同步脚本在扫描 Terminal 服务代码时，将重点匹配 `test_terminal.py` 中的子步骤注释。

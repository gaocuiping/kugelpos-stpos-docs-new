---
layout: default
title: Terminal サービス テストケース
parent: テスト
nav_order: 107
---

# Terminal サービス プロフェッショナルテストケース設計書

本ドキュメントは、Terminal サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルな测试用例群です。

## 📊 現在のテストカバレッジ概況

以下の表は、各テスト階層における設計済ケース数と現在の実装状況（スクリプト自動同期結果）を示しています。

| テスト階層 | 総ケース数 | 実装済 (Implemented) | 未実装 (Missing) | カバレッジ (進捗率) |
|:---|:---:|:---:|:---:|:---:|
| **単体テスト (Unit)** | 4 | 0 | 4 | **0.0%** |
| **結合テスト (Integration)** | 3 | 3 | 0 | **100.0%** |
| **シナリオテスト (Scenario)** | 3 | 3 | 0 | **100.0%** |
| **全体合計 (Total)** | **10** | **6** | **4** | **60.0%** |


### 状態 (Status) の定義

| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB/API）を Mock し、各モジュールの純粋なロジック、状態遷移、および例外処理を検証する。

### 1.1 状態管理 & サービスフロー (`TerminalService`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **TM-U-001** | **TerminalServiceの検証** | `TerminalService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_check_terminal_status_matrix` <br> *(待追加：状態遷移マトリクスの網羅検証)* | 現在の状態（Closed/Opened等）に対し、許可されない FunctionMode 変更が全て拒否されること。 |
| **TM-U-002** | **TerminalServiceの検証** | `TerminalService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_open_terminal_date_rollover` <br> *(待追加：営業日付更新ロジック)* | 前回の営業日と現在日付が異なる場合、`open_counter` が 1 にリセットされ日付が更新されること。 |
| **TM-U-003** | **TerminalServiceの検証** | `TerminalService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_sign_in_already_signed_in` | すでにサインイン済みの端末に対し、別の StaffID でサインインを試みた際に `TerminalAlreadySignedInException` が送出されること。 |

### 1.2 通信レジリエンス (`PubsubManager`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **TM-U-101** | **PubSub通信の検証** | `PubsubManager` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_pubsub_circuit_breaker` <br> *(待追加：サーキットブレーカー検証)* | Dapr 側がエラーを返却した際、非ブロッキングでエラーが処理され、後続の業務プロセスが中断されないこと。 |
| **TM-U-301** | **ヘルスチェックと基盤検証** | `Health & System` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_health_endpoint` (ヘルスチェック経由)<br>`test_health_endpoint_background_jobs_details` (バックグラウンドジョブの詳細確認) | APIの生存確認やバックグラウンドジョブのステータス詳細など、本線以外の健全性確認が網羅されていること。 |

---

## 2. 結合测试 (Integration Tests)
**目的**: データベース（MongoDB）、Dapr サービス、およびリポジトリ間のデータ連携を検証する。

| ID | テストタイトル | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **TM-I-001** | **MongoDBデータ永続化検証** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_terminal_operations` <br> *(# Test create Terminal with token)* | 登録された端末情報（MAC/ID）が DB に正しく永続化され、API Key が発行されること。 |
| **TM-I-002** | **Staff Repoの検証** | `Staff Repo` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_terminal_operations` <br> *(# Test Terminal Sign In with API key)* | 実在する StaffID を用いたサインイン時に、スタッフ名等の詳細が正常にマージされること。 |
| **TM-I-003** | **Log Repoの検証** | `Log Repo` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_terminal_operations` <br> *(# Test Cash In with API key)* | 入出金ログが生成され、レシート/ジャーナル用テキストが正しく構築されること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、複雑な業務フローをエンドツーエンドで検証する。

| ID | テストタイトル | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|:---|
| **TM-S-001** | **端末マスター CRUD ライフサイクルの検証** | 端末マスター CRUD ライフサイクル | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. **Tenant**: 作成、取得、更新、削除<br>2. **Store**: 追加、重複チェック、取得、更新、削除<br>3. **Terminal**: 作成(Token利用)、重複チェック、取得、更新、削除 | `test_terminal_operations` | JWT Token を用いた管理 API を通じて、テナント・店舗・端末マスターの CRUD ライフサイクルが正常に機能すること。 |
| **TM-S-002** | **端末ステータス・業務遷移フローの検証** | 端末ステータス・業務遷移フロー | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_terminal_operations` 後半の実行：<br>1. **Sign-In**: API Key でサインイン<br>2. **Open**: 準備金入力による営業開始<br>3. **Close**: 精算入力による営業終了<br>4. **Sign-Out**: 端末からのサインアウト | `test_terminal_operations` | 端末側の API Key を用いた認証と、業務モード(Function Mode)の切り替え・整合性チェックが機能すること。 |
| **TM-S-003** | **入出金 (Cash In/Out) 管理の検証** | 入出金 (Cash In/Out) 管理 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. Terminal が `Opened` 状態で入出金モードへ遷移<br>2. `Cash In` (理由あり/なし) 実行<br>3. `Cash Out` (理由あり/なし) 実行 | `test_terminal_operations` | 端末内での入出金ログの生成と、正負金額の記録が正しく行われること。 |

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

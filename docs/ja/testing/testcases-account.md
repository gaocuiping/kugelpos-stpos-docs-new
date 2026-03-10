---
layout: default
title: Account サービス テストケース
parent: テスト
nav_order: 101
---

# Account サービス プロフェッショナルテストケース設計書

本ドキュメントは、Account サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

## 📊 現在のテストカバレッジ概況

以下の表は、各テスト階層における設計済ケース数と現在の実装状況（スクリプト自動同期結果）を示しています。

| テスト階層 | 総ケース数 | 実装済 (Implemented) | 未実装 (Missing) | カバレッジ (進捗率) |
|:---|:---:|:---:|:---:|:---:|
| **単体テスト (Unit)** | 3 | 0 | 3 | **0.0%** |
| **結合テスト (Integration)** | 2 | 2 | 0 | **100.0%** |
| **シナリオテスト (Scenario)** | 2 | 1 | 1 | **50.0%** |
| **全体合計 (Total)** | **7** | **3** | **4** | **42.9%** |


### 状態 (Status) の定義

| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB/Slack）を Mock し、認証ロジック、パスワードハッシュ化、およびパスワード要件バリデーションを検証する。

### 1.1 認証 & 認可ロジック (`auth.py` / `account.py`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **AC-U-001** | **JWT認証・認可の検証** | `auth.py` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_password_hashing_consistency` <br> *(待追加：ハッシュ整合性)* | 生成されたハッシュが、同一パスワードに対して正しく `verify` され、異なるパスワードでは拒否されること。 |
| **AC-U-002** | **JWT認証・認可の検証** | `auth.py` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_jwt_payload_contents` <br> *(待追加：Token内容検証)* | 発行された JWT の `sub`, `tenant_id`, `is_superuser` クレームが期待通り設定されていること。 |
| **AC-U-003** | **アカウントライフサイクルの検証** | `account.py` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_register_user_order_integrity` <br> *(待追加：登録順序の整合性)* | `register_super_user` において、DB セットアップが完了した後にユーザー挿入が行われるフローであること。 |
| **AC-U-301** | **ヘルスチェックと基盤検証** | `Health & System` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_health_endpoint` (ヘルスチェック経由)<br>`test_health_endpoint_response_time` (応答時間確認) | APIの生存確認やレイテンシ保証など、本線以外の健全性確認が含まれていること。 |
| **AC-A-LOG** | **Authenticate user and provide a JWT access token** | `API / POST` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `login_for_access_token` | システムが自動追加したAPIインターフェーステスト |
| **AC-A-REG** | **Register a new superuser and create a new tenant** | `API / POST` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `register_super_user` | システムが自動追加したAPIインターフェーステスト |
| **AC-A-REG** | **Register a new regular user in the tenant by a superuser** | `API / POST` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `register_user_by_superuser` | システムが自動追加したAPIインターフェーステスト |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）への永続化、および Slack 通知連携の動作を検証する。

| ID | テストタイトル | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **AC-I-001** | **MongoDBデータ永続化検証** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_operations` <br> *(# register a superuser)* | 登録されたユーザー情報が DB に永続化され、次回ログイン時に認証可能であること。 |
|**AC-I-002**|**Register a new superuser and create a new tenant**|`Slack API`|![Implemented](https://img.shields.io/badge/Status-Implemented-green)|`register_super_user` <br> *(# Send notification to Slack)*|⚠️ コードインターフェースが変更されました：新規テナント登録時に、専用チャンネルへ通知が送信されること（Mock 経由での呼び出し検証）。| |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、ユーザー登録から認証までのライフサイクルをエンドツーエンドで検証する。

| ID | テストタイトル | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|:---|
| **AC-S-001** | **テナントオンボーディングと分離 (Isolation)の検証** | テナントオンボーディングと分離 (Isolation) | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. **Superuser 登録**: `tenant_id` 有り/無し、および既存 `tenant_id` 被り時の新規動的生成確認<br>2. **DB 分離確認**: 新規生成されたテナント用の専用 DB が物理的に作成されることの確認<br>3. **Login**: Token エンドポイント経由での JWT (Bearer) 取得<br>4. **User 登録**: 取得した Token を用いて特定テナント傘下の一般ユーザーを登録 | `test_operations` | 新規テナントが正常にプロビジョニングされ、別テナントとの DB 物理隔離が担保された状態で管理者と一般ユーザーが作成・ログイン可能であること。 |
| **AC-S-002** | **マルチテナント隔離の検証** | マルチテナント隔離 | ![Missing](https://img.shields.io/badge/Status-Missing-red) | 1. テナントAでログイン<br>2. テナントBのクレデンシャルで試行 | `test_cross_tenant_login_isolation` | あるテナントの ID で、別のテナントのユーザーとしてログインすることが不可能であること。 |

---

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: テスト環境のセットアップおよび共通クレンジングを共通化する。

| 関数名 (Helper Function) | 役割 (Responsibility) | 備考 (Notes) |
|:---|:---|:---|
| `test_setup_data` | システム管理者アカウントの事前作成 | 認可が必要なテスト用のベースライン |
| `test_clean_data` | `users` コレクションの物理削除 | 冪等性確保のための後処理 |
| `conftest.http_client` | FastAPI AsyncClient 提供 | 認可・通信基盤 |

> [!CAUTION]
> Account サービスはシステムの最上流であるため、ログイン失敗時のメッセージからユーザーの存在を推測させない (Enumeration) 対策の検証も重要です。

---
layout: default
title: Master Data サービス テストケース
parent: テスト
nav_order: 104
---

# Master Data サービス プロフェッショナルテストケース設計書

本ドキュメントは、Master Data サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

### 状態 (Status) の定義

| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB）を Mock し、マスタデータの検索ロジック、有効期間バリデーション、および継承モデルを検証する。

### 1.1 商品・カテゴリロジック (`ItemBookMasterService` / `CategoryMasterService`)

| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **MD-U-001** | `ItemBookMasterService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_item_fallback_to_common` <br> *(待追加：店舗個別情報なし時のCommon取得)* | 店舗個別の商品情報が存在しない場合、自動的に共通 (Common) マスタの情報が補完されて返却されること。 |
| **MD-U-002** | `CategoryMasterService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_category_operations` <br> *(# Test category CRUD)* | カテゴリの親子階層構造（ParentID）が正確に維持・パースされること。 |

### 1.2 税率・決済設定 (`TaxMasterService` / `PaymentMasterService`)

| ID | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **MD-U-101** | `TaxMasterService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_tax_period_overlap_validation` <br> *(待追加：期間重複バリデーション)* | 同一の税区分に対し、重複する有効期間を持つ複数の税率を登録しようとした際にエラーが送出されること。 |
| **MD-U-102** | `PaymentMasterService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_payment_method_operations` | 決済方法ごとに設定された種別（Cash, Credit, QR等）が正確にモデル化されていること。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）への永続化、および Dapr Redis によるマスタキャッシュの整合性を検証する。

| ID | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|
| **MD-I-001** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_staff_operations` <br> *(# Test staff CRUD)* | 作成・更新されたマスタレコードが DB に正確に反映され、検索可能であること。 |
| **MD-I-002** | `Dapr Cache` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_settings_operations` | 店舗設定（Settings）の変更が、キャッシュレイヤーを介して即座に反映されること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、マスターデータのメンテナンスフローをエンドツーエンドで検証する。

| ID | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|
| **MD-S-001** | 商品構成セットアップ | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. カテゴリ作成<br>2. 共通商品登録<br>3. 店舗個別価格設定 | `test_operations.py` (Item tests) | 最小構成の商品マスタが API 経由で完結し、POS で利用可能な状態になること。 |
| **MD-S-002** | スタッフ・権限管理 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. スタッフ登録<br>2. ロール(Role)付与<br>3. ログイン試行 | `test_staff_operations` | 登録されたスタッフ情報が認証認可サービスで正しく参照できること。 |

---

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: テスト環境のセットアップおよび共通クレンジングを共通化する。

| 関数名 (Helper Function) | 役割 (Responsibility) | 备注 (Notes) |
|:---|:---|:---|
| `test_setup_data` | テスト用マスターシートの流し込み | 全マスタの初期状態構築 |
| `test_clean_data` | 全マスターコレクションの物理削除 | 冪等性確保のための後処理 |
| `conftest.http_client` | FastAPI AsyncClient 提供 | 認可・通信基盤 |

> [!TIP]
> Master Data サービスは「影響範囲」が広いため、税率計算などの境界値テストを優先的に補充することが推奨されます。

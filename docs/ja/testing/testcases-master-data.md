---
layout: default
title: Master Data サービス テストケース
parent: テスト
nav_order: 104
---

# Master Data サービス プロフェッショナルテストケース設計書

本ドキュメントは、Master Data サービスのソースコード（`app/`）を詳細に解析した結果に基づき、**単体 (Unit)**、**結合 (Integration)**、**シナリオ (Scenario)** の 3 階層に定義されたプロフェッショナルなテストケース群です。

## 📊 現在のテストカバレッジ概況

以下の表は、各テスト階層における設計済ケース数と現在の実装状況（スクリプト自動同期結果）を示しています。

| テスト階層 | 総ケース数 | 実装済 (Implemented) | 未実装 (Missing) | カバレッジ (進捗率) |
|:---|:---:|:---:|:---:|:---:|
| **単体テスト (Unit)** | 54 | 52 | 2 | **96.3%** |
| **結合テスト (Integration)** | 2 | 2 | 0 | **100.0%** |
| **シナリオテスト (Scenario)** | 2 | 2 | 0 | **100.0%** |
| **全体合計 (Total)** | **58** | **56** | **2** | **96.6%** |


### 状態 (Status) の定義

| アイコン | 状态 | 内容 |
|:---:|:---:|:---|
| ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | **Implemented** | 実際のテストコード（関数名またはコメント）から実装が確認されている。 |
| ![Missing](https://img.shields.io/badge/Status-Missing-red) | **Missing** | 現状のテストコードには存在しないが、カバレッジ向上（85%以上）のために必要な項目。 |

---

## 1. 単体テスト (Unit Tests)
**目的**: 外部依存（DB）を Mock し、マスタデータの検索ロジック、有効期間バリデーション、および継承モデルを検証する。

### 1.1 商品・カテゴリロジック (`ItemBookMasterService` / `CategoryMasterService`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **MD-U-001** | **ItemBookMasterServiceの検証** | `ItemBookMasterService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_item_fallback_to_common` <br> *(待追加：店舗個別情報なし時のCommon取得)* | 店舗個別の商品情報が存在しない場合、自動的に共通 (Common) マスタの情報が補完されて返却されること。 |
| **MD-U-002** | **CategoryMasterServiceの検証** | `CategoryMasterService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_category_operations` <br> *(# Test category CRUD)* | カテゴリの親子階層構造（ParentID）が正確に維持・パースされること。 |
| **MD-A-CRE** | **Create a new product category record.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_category` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve all product categories for a tenant.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_categories` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve a specific product category by its code.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_category` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update an existing product category.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_category` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete a product category.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_category` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-CRE** | **Create a new item master record.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_item_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve a specific store-specific item record by its code.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_item_store_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve all store-specific item records for a specific store.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_item_store_master_all_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update an existing store-specific item record.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_item_store_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete a store-specific item record.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_item_store_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve detailed item information combining common and store-specific data.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_item_store_master_detail_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-CRE** | **Create a new payment method record.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_payment` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve all payment methods for a tenant.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_all_payments` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve a specific payment method by its code.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_payment` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update an existing payment method.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_payment` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete a payment method.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_payment` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve all tax records for a tenant.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_taxes` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve a specific tax record by its code.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_tax` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve a specific item master record by its code.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_item_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve all item master records for a tenant.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_item_master_all_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update an existing item master record.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_item_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete an item master record.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_item_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-CRE** | **Setup the database for the tenant. This will create the required collections and indexes.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_tenant` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-CRE** | **Create a new item book record.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve an item book record by its ID.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_item_book_by_id` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve detailed information of an item book by its ID.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_item_book_detail_by_id` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve all item book records for a tenant.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_all_item_books` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update an existing item book record.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete an item book record.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-ADD** | **Add a category to an item book.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `add_category_to_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update a category in an item book.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_category_in_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete a category from an item book.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_category_from_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-ADD** | **Add a tab to a category in an item book.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `add_tab_to_category_in_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update a tab in a category in an item book.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_tab_in_category_in_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete a tab from a category in an item book.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_tab_from_category_in_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-ADD** | **Add a button to a tab in a category in an item book.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `add_button_to_tab_in_category_in_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update a button in a tab in a category in an item book.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_button_in_tab_in_category_in_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete a button from a tab in a category in an item book.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_button_from_tab_in_category_in_item_book` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-CRE** | **Create a new system settings record.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_settings_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve all system settings for a tenant.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_settings_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve a specific system setting by its name.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_settings_master_by_name_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve the effective value of a setting for a specific store and terminal.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_settings_value_by_name_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update an existing system setting.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_settings_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete a system setting.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_settings_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-CRE** | **Create a new staff record in the master data.** | `API / POST` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `create_staff_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve a specific staff record by their ID.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_staff_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-GET** | **Retrieve all staff records for a tenant.** | `API / GET` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `get_staff_master_all_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-UPD** | **Update an existing staff record.** | `API / PUT` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `update_staff_master_async` | システムが自動追加したAPIインターフェーステスト |
| **MD-A-DEL** | **Delete a staff record.** | `API / DELETE` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `delete_staff_master_async` | システムが自動追加したAPIインターフェーステスト |

### 1.2 税率・決済設定 (`TaxMasterService` / `PaymentMasterService`)

| ID | テストタイトル | テスト対象 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **MD-U-101** | **税マスタ構成の検証** | `TaxMasterService` | ![Missing](https://img.shields.io/badge/Status-Missing-red) | `test_tax_period_overlap_validation` <br> *(待追加：期間重複バリデーション)* | 同一の税区分に対し、重複する有効期間を持つ複数の税率を登録しようとした際にエラーが送出されること。 |
| **MD-U-102** | **決済マスタ構成の検証** | `PaymentMasterService` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_payment_method_operations` | 決済方法ごとに設定された種別（Cash, Credit, QR等）が正確にモデル化されていること。 |
| **MD-U-301** | **ヘルスチェックと基盤検証** | `Health & System` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_health_endpoint` (ヘルスチェック経由)<br>`test_health_endpoint_response_time` (応答時間確認) | APIの生存確認やレイテンシ保証など、本線以外の健全性確認が網羅されていること。 |

---

## 2. 結合テスト (Integration Tests)
**目的**: データベース（MongoDB）への永続化、および Dapr Redis によるマスタキャッシュの整合性を検証する。

| ID | テストタイトル | 連携先 | 状态 (Status) | 匹配规则 (Function & Comments) | 期待される結果 |
|:---|:---|:---|:---|:---|:---|
| **MD-I-001** | **MongoDBデータ永続化検証** | `MongoDB` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_staff_operations` <br> *(# Test staff CRUD)* | 作成・更新されたマスタレコードが DB に正確に反映され、検索可能であること。 |
| **MD-I-002** | **Dapr Cacheの検証** | `Dapr Cache` | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_settings_operations` | 店舗設定（Settings）の変更が、キャッシュレイヤーを介して即座に反映されること。 |

---

## 3. シナリオテスト (Scenario Tests)
**目的**: 実際の API エンドポイントを介して、マスターデータのメンテナンスフローをエンドツーエンドで検証する。

| ID | テストタイトル | シナリオ名 | 状态 (Status) | 业务步骤 (Business Steps) | 匹配规则 (Function & Comments) | 期待される検証点 |
|:---|:---|:---|:---|:---|:---|:---|
| **MD-S-001** | **マスター統合 CRUD ライフサイクルの検証** | マスター統合 CRUD ライフサイクル | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | `test_operations` 関数による一連の統合シナリオ：<br>1. **Tenant**: 新規作成と異常系(無効ID)<br>2. **Staff**: 登録、全件取得、更新、論理/物理削除<br>3. **Category**: 作成、取得、コード更新エラー、削除<br>4. **ItemCommon**: 作成、更新、論理削除、物理削除<br>5. **ItemStore**: 構成適用、複数端末更新、異常系<br>6. **Payment**: 決済マスターのCRUD<br>7. **Settings**: 端末別設定のCRUDと重複チェック<br>8. **ItemBook**: メニューブック・カテゴリ・タブ・ボタンの階層的作成<br>9. **Tax**: 税・ページネーション検証 | `def test_operations` | 全ての主要マスタエンティティ（Tenant, Staff, Category, Item, Payment, Settings, ItemBook, Tax）に対する包括的な CRUD ライフサイクルとページネーションが完全に機能すること。 |
| **MD-S-002** | **スタッフ・権限管理の検証** | スタッフ・権限管理 | ![Implemented](https://img.shields.io/badge/Status-Implemented-green) | 1. スタッフ登録<br>2. ロール(Role)付与<br>3. ログイン試行 | `test_staff_operations` | 登録されたスタッフ情報が認証認可サービスで正しく参照できること。 |

---

## 4. テストインフラストラクチャ & ヘルパー関数 (Test Infrastructure & Helpers)
**目的**: テスト環境のセットアップおよび共通クレンジングを共通化する。

| 関数名 (Helper Function) | 役割 (Responsibility) | 備考 (Notes) |
|:---|:---|:---|
| `test_setup_data` | テスト用マスターシートの流し込み | 全マスタの初期状態構築 |
| `test_clean_data` | 全マスターコレクションの物理削除 | 冪等性確保のための後処理 |
| `conftest.http_client` | FastAPI AsyncClient 提供 | 認可・通信基盤 |

> [!TIP]
> Master Data サービスは「影響範囲」が広いため、税率計算などの境界値テストを優先的に補充することが推奨されます。

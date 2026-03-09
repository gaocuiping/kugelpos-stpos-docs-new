---
title: "自動化テスト機構 分析レポート"
parent: テスト
grand_parent: 日本語
nav_order: 3
layout: default
---

# 自動化テスト機構 分析レポート

> 分析日：2026-03-09  
> 対象リポジトリ：[kugel-masa/kugelpos-backend](https://github.com/kugel-masa/kugelpos-backend)

---

## 一、公開リポジトリと本ドキュメントの比較

| 比較項目 | 本ドキュメントの記述 | 公開リポジトリの実態 | 判定 |
|---------|-----------------|------------------|------|
| テストフレームワーク | pytest | pytest（pipenv run pytest） | ✅ 一致 |
| 全サービス一括テスト | `pytest services/<service>/tests/` | `./scripts/run_all_tests_with_progress.sh` | ⬆️ **リポジトリがより完全** |
| 単サービス独立テスト | `pytest services/<service>/tests/unit/` | `services/<service>/run_all_tests.sh` | ⬆️ **リポジトリがより完全** |
| CI/CD | GitHub Actions 記述あり | `.github/workflows/` **なし** | ❌ ドキュメントが先行、未実装 |
| テスト実行順序制御 | 記述なし | clean → setup → 統合 → ユニット | ⬆️ **新規追加** |
| カバレッジ強制 | 85% 必須 | `--cov-fail-under` 未設定 | ❌ ドキュメントが先行、未実装 |
| 環境変数 | `.env.test` | `.env.test.sample`（ローカル・リモート切替対応） | ⬆️ **リモートテスト対応が新規追加** |
| 進捗表示 | 記述なし | プログレスバー（カラー表示） | ⬆️ **新規追加** |

---

## 二、自動化テスト機構の全体像

### ディレクトリ構成

```
kugelpos-backend/
├── scripts/
│   ├── run_all_tests.sh                 # モード①：全サービス一括（シンプル版）
│   └── run_all_tests_with_progress.sh   # モード①：全サービス一括（進捗バー版）
└── services/
    ├── account/run_all_tests.sh         # モード②：単サービス独立テスト
    ├── terminal/run_all_tests.sh
    ├── cart/run_all_tests.sh
    ├── master-data/run_all_tests.sh
    ├── journal/run_all_tests.sh
    ├── report/run_all_tests.sh
    └── stock/run_all_tests.sh
```

---

## 三、モード①：全サービス一括テスト

**用途**：リリース前の総合検証、CI環境での一括実行。

### 方式 A：シンプル版

```bash
./scripts/run_all_tests.sh
```

**実行フロー：**
1. テスト用環境変数を自動設定（`SECRET_KEY`、`PUBSUB_NOTIFY_API_KEY`）
2. `.env.test` が存在しない場合、`.env.test.sample` から自動生成
3. 7サービスを順番にループ実行：`account → master-data → journal → report → stock → terminal → cart`
4. 各サービスの `services/<service>/run_all_tests.sh` を呼び出す

### 方式 B：進捗バー版（推奨）

```bash
./scripts/run_all_tests_with_progress.sh
```

**追加機能：**
- カラーの進捗バー（`█░░ 57% (4/7)`）
- 各サービスのリアルタイム結果表示（✓ PASSED / ✗ FAILED）
- 全体サマリーレポート
- 失敗時に `exit 1` でCI捕捉可能

---

## 四、モード②：単サービス独立テスト

**用途**：特定のサービス開発中に素早くフィードバックを得る。

```bash
# 例：Cart サービスのテストのみ実行
cd services/cart
./run_all_tests.sh
```

### Cart サービスのテストファイル実行順序（例）

| 順序 | ファイル | 種別 | 説明 |
|------|---------|------|------|
| 1 | `test_clean_data.py` | 前処理 | DBデータをクリーン |
| 2 | `test_setup_data.py` | 前処理 | テストデータを投入 |
| 3 | `test_health.py` | 統合 | ヘルスチェック |
| 4 | `test_cart.py` | 統合 | 購入フロー |
| 5 | `test_category_promo.py` | 統合 | カテゴリプロモーション |
| 6 | `test_void_return.py` | 統合 | 取消・返品 |
| 7 | `test_payment_cashless_error.py` | 統合 | キャッシュレス決済エラー |
| 8 | `test_resume_item_entry.py` | 統合 | 商品入力再開 |
| 9 | `test_calc_subtotal_logic.py` | ユニット | 小計計算ロジック |
| 10 | `test_terminal_cache.py` | ユニット | 端末キャッシュ |
| 11 | `test_text_helper.py` | ユニット | テキストユーティリティ |
| 12 | `test_tran_service_status.py` | ユニット | トランザクション状態 |
| 13 | `test_tran_service_unit_simple.py` | ユニット | トランザクションサービス |
| 14 | `test_transaction_status_repository.py` | ユニット | リポジトリ層 |

> **設計ポイント**：clean → setup を必ず先に実行することで、テスト環境の冪等性（繰り返し実行可能）を保証している。

### Account / Terminal サービス（シンプル構成）

```
test_clean_data.py → test_setup_data.py → test_health.py → test_operations.py/test_terminal.py
```

---

## 五、環境設定：`.env.test.sample`

```ini
# ローカルテストモード（デフォルト）
LOCAL_TEST="True"
MONGODB_URI=mongodb://localhost:27017/?replicaSet=rs0&directConnection=true

# リモートテストモード（新追加）
# LOCAL_TEST="False"
# REMOTE_URL="{your_server}.japaneast.azurecontainerapps.io"

# テナントID
TENANT_ID="{your_tenant_id}"
```

> **ポイント**：`LOCAL_TEST=False` + `REMOTE_URL` を設定すれば、本番環境に対してAPIテストを実行できる。

---

## 六、結論と課題

### ✅ 実装済み
- 全サービス一括テスト（2つのスクリプト）
- 単サービス独立テスト（各サービスに `run_all_tests.sh`）
- テスト実行順序の固定化（clean → setup → 統合 → ユニット）
- `.env.test` 自動生成
- リモートテスト対応

### ❌ 未実装（ドキュメントが先行）
- **CI/CD自動トリガー**（`.github/workflows/` が存在しない）
- **カバレッジ85%門控**（`--cov-fail-under=85` 未設定）

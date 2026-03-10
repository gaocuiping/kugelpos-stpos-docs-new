---
title: "自動化テスト機構 分析レポート (2026-03-10)"
parent: テスト
grand_parent: 日本語
nav_order: 3
layout: default
---

# 自動化テスト機構 分析レポート

> 分析日：2026-03-10  
> 対象リポジトリ：[kugel-masa/kugelpos-backend](https://github.com/kugel-masa/kugelpos-backend)

---

## 一、公開リポジトリと本ドキュメントの比較

現在のプロジェクトでは、「Docs-as-Code」の理念に基づき大幅な自動化基盤の改修が行われました。

| 比較項目 | 本ドキュメントの記述 | 公開リポジトリの実態 | 判定 |
|---------|-----------------|------------------|------|
| テストフレームワーク | pytest | pytest | ✅ 一致 |
| 全サービス一括テスト | `pytest services/<service>/tests/` | `./scripts/run_all_tests_with_progress.sh` | ⬆️ **リポジトリがより完全** |
| 単サービス独立テスト | `pytest services/<service>/tests/unit/` | `services/<service>/run_all_tests.sh` | ⬆️ **リポジトリがより完全** |
| テスト自動生成機構 | 記述なし | `auto_append_tests.py` | ⬆️ **完全新規追加**（API更新時の自動追従） |
| ドキュメント同期 | 手動管理 | `sync_testcases.py` | ⬆️ **完全新規追加**（マークダウン自動緑化） |
| CI/CD パイプライン | GitHub Actions 記述あり | `.github/workflows/` (auto-append-tests.yml等) | ✅ **実装完了**（ドキュメントに追いついた） |
| カバレッジ強制 | 85% 必須 | `--cov-fail-under` 未設定 | ❌ 次期フェーズの課題 |
| 環境変数 | `.env.test` | `.env.test.sample`（ローカル・リモート切替対応） | ⬆️ リモートテスト対応済み |

---

## 二、最新の自動化テスト機構の全体像 (2026-03-10更新)

### 1. ディレクトリ構成の進化

テストファイルが単なるフラットな配置から、明確な責任分離へと進化しました。

```text
kugelpos-backend/
├── scripts/
│   ├── auto_append_tests.py             # 🆕 新規APIのテスト骨格自動生成
│   ├── sync_testcases.py                # 🆕 実装状態をDocs(Markdown)へ双方向同期
│   └── run_all_tests_with_progress.sh   # 全サービス一括実行（進捗バー版）
└── services/
    └── <service_name>/
        └── tests/
            ├── conftest.py              # 共通 Fixture
            ├── unit/                    # 外部依存をモック化した高速単体テスト
            │   └── test_*_unit_auto.py  # 🆕 自動生成スケルトン
            └── scenario/                # 実DBやAPIを通じたE2Eシナリオテスト
                └── test_*_scenario_auto.py # 🆕 自動生成スケルトン
```

---

## 三、🆕 ゼロ・エフォート型テスト生成パイプライン (Docs-as-Code)

今回のアーキテクチャ刷新の目玉は、開発者がテストを作成・管理するコストを極限まで下げる仕組みです。

### 1. API を書けばテストスケルトンが生まれる
開発者が `app/api/**/*.py` に新しい FastAPI ルーターを追加し push すると、GitHub Actions (`auto-append-tests.yml`) がそれを検知します。
システムは未カバーの API を特定し、`tests/unit/` と `tests/scenario/` に **実行可能なレベルのテストコード (Happy Path, 404, 401 検証等)** を自動で生成してコミットします。

### 2. アサーションを書けばドキュメントが青信号になる
生成されたテストから `pytest.skip()` を一つ削除し、実際の業務アサーションを記載して push すると、今度は `sync-test-docs.yml` が作動します。
スクリプトがコード状態を解析し、`docs/ja/testing/testcases-*.md` の ❌ Missing ステータスを ✅ Implemented に自動更新します。

---

## 四、テスト実行モード（継続利用）

**用途**：リリース前の総合検証、CI環境での一括実行。

### モード①：全サービス一括テスト（進捗バー版）

```bash
./scripts/run_all_tests_with_progress.sh
```
- カラーの進捗バー（`█░░ 57% (4/7)`）とリアルタイム結果表示（✓ PASSED / ✗ FAILED）
- `SECRET_KEY` 等の環境変数を自動補完し、7サービスを順次実行

### モード②：単サービス独立テスト

```bash
cd services/cart
./run_all_tests.sh
```
- `test_clean_data.py` → `test_setup_data.py` の前処理を通じて、DBの冪等性を確保。

---

## 五、結論と課題

### ✅ 実装済みの強力な機能
- **API変更の自動検知とテスト生成 (`auto_append_tests.py`)** による機能漏れ防止。
- **ドキュメントとコードの乖離を完全になくす同期機構 (`sync_testcases.py`)**。
- GitHub Actions を用いたシームレスな CI/CD エコシステムの確立。
- 全サービスの `unit/`, `scenario/` レイヤリングの統一化。

### 🚀 今後の課題 (Next Steps)
1.  **カバレッジゲートの有効化**: 現在は生成と管理が自動化されましたが、CI 実行時に `pytest --cov --cov-fail-under=85` を強制する設定がまだ有効化されていません。
2.  **インテリジェントなアサーション生成**: Pydantic スキーマを解析し、レスポンスの特定フィールドまでアサーションするコードの自動生成機能の強化。

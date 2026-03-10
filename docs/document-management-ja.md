---
title: "ドキュメント管理と自動化"
layout: default
nav_order: 5
---

# ドキュメント管理 — Jekyll + GitHub Pages 自動化体系

本プロジェクトのドキュメントセンター（本サイト）は、**"Docs-as-Code"（コードとしてのドキュメント）** という深度統合ソリューションを採用しています。Jekyll 静的サイト生成器と GitHub Actions 自動化スクリプトを組み合わせることで、技術ドキュメントと業務コードのリアルタイム同期を実現しています。

---

## 🏗️ 技術アーキテクチャ概要

| 次元 | 技術スタック / 設定 | 説明 |
| :--- | :--- | :--- |
| **コア** | [Jekyll](https://jekyllrb.com/) | Markdown をネイティブで高性能な HTML サイトに変換します。 |
| **ホスティング** | [GitHub Pages](https://pages.github.com/) | サーバー不要で、GitHub Actions を通じて直接ビルド・公開されます。 |
| **テーマ** | `just-the-docs` | モダンなドキュメント UI。検索機能、多階層サイドバー、多言語対応を内蔵。 |
| **ビジュアルカスタマイズ** | [custom.scss](_sass/custom/custom.scss) | **Sky-Breeze グラデーションシステム**（スカイブルーからミントグリーン）を採用し、グラスモーフィズム効果を統合。 |

---

## ⚡ 核心自動化メカニズム

メンテナンスの負担を大幅に軽減するため、システムには 2 つの主要な自動化同期エンジンが内蔵されています：

### 1. API インターフェースドキュメント自動生成 (`generate_docs.sh`)
`services/` ディレクトリ内の各マイクロサービスの FastAPI ルートコード（`app/api/`）とデータモデル（`schemas.py`）を自動的にスキャンします。
- **トリガーロジック**：ルートデコレータ（例：`@router.get`）や Pydantic クラス定義を検出するたびに、スクリプトがパス、メソッド、関数名、およびソースコードの位置を自動的に抽出します。
- **出力結果**：`docs/ja/<service>/` ディレクトリに `api-overview-generated.md` を自動生成し、インターフェースドキュメントが常にコードと一致することを保証します。

### 2. テストケース双方向同期と自動発見 (`sync_testcases.py`)
これはシステムで最もインテリジェントな部分であり、ステータスの同期だけでなく、**コード構造の変化を感知**することも可能です：
- **自動追加 (Auto-Discovery)**：`services/*/app/api/` に新しい API インターフェース（例：`@router.post`）を追加した場合、スクリプトを実行すると、そのインターフェースが新しいテストケースとしてドキュメントに自動的に追加されます。
- **変更感知 (Modification Detection)**：コード内の Docstring（インターフェース説明）を変更したり、HTTP メソッドを変更した場合、スクリプトは競合を自動的に識別し、Markdown テーブル内の「テストタイトル」と「テスト対象」を更新します。
- **品質ゲート (Quality Gate)**：`sync_testcases.py` は、テスト関数内に `pytest.skip()` が含まれているかをチェックします。**実際に実装された**テスト（skip なし）のみが ❌ `Missing` から ✅ `Implemented` に変わり、空のスケルトンは完了済みにカウントされません。

### 3. 🆕 テストコードの自動生成 (`auto_append_tests.py`)
API コードが変更された際、システムは単なるスケルトンを生成するだけでなく、すべての**未網羅の新規インターフェース**に対して**機能完備の初期テストコード**を自動生成します：

| 生成ファイル | 対象ディレクトリ | 生成内容 |
| :--- | :--- | :--- |
| `test_<func>_scenario_auto.py` | `tests/scenario/` | **全自動実装**：Happy Path (200/201)、404 (GET)、および 401/403 権限検証を含みます。 |
| `test_<func>_unit_auto.py` | `tests/unit/` | **構造化コード**：`async_client` に基づくルーティング構造の検証。 |

**カバレッジ検出（3段階マッチング）**：
1. 既存の `# AUTO-GENERATED` マークがある → スキップ
2. 既存の `test_<func_name>` 関数名が一致する → スキップ
3. 既存の該当インターフェースの URL パスを呼び出す HTTP リクエストがある → スキップ

生成されたファイルには、パスパラメータに基づく汎用的な変数定義が含まれており、push 後すぐに実行可能です。開発者は具体的な業務要件に応じてアサーションを微調整するだけで、ドキュメントを「緑色」にすることができます。

```bash
# 手動実行（全サービス対象）
python3 scripts/auto_append_tests.py --all

# 特定のサービスを指定の場合
python3 scripts/auto_append_tests.py --service terminal
```

---

## 🔄 自動化パイプライン (CI/CD)

プロジェクトには、体系全体を駆動する 4 つの主要な GitHub Workflows が構成されています：

| Workflow ファイル | トリガー条件 | 機能 |
| :--- | :--- | :--- |
| `generate-docs.yml` | API ルートコード変更時 | FastAPI ルートをスキャンし、API 概要ドキュメントを生成して自動 commit |
| **`auto-append-tests.yml`** | `services/*/app/api/**/*.py` 変更時 | 🆕 変更されたサービスを検出し、テストスケルトンを生成して `tests/unit/` + `tests/scenario/` に commit |
| `sync-test-docs.yml` | `services/**/tests/**/*.py` 変更時 | テストの実装状況をスキャンし、testcases-*.md のアイコン状態を自動更新（skip のない関数のみ緑になる） |
| `jekyll-gh-pages.yml` | 上記いずれかの commit | すべての Markdown を HTML にコンパイルし、GitHub Pages に公開 |

### 完全な自動化フロー

```
開発者が API ルートコードを変更/追加 (services/*/app/api/**/*.py)
  │
  ├─→ [generate-docs.yml]    → API インターフェースドキュメント自動更新
  │
  └─→ [auto-append-tests.yml]
        │  変更されたサービスを検出
        │  auto_append_tests.py --service <svc> を実行
        │  機能テストを直接生成：
        │    tests/unit/*_unit_auto.py
        │    tests/scenario/*_scenario_auto.py
        └─→ git commit [skip ci] & push
              │
              └─→ [sync-test-docs.yml]   → 新規テストを自動スキャン
                    生成されたテストは基本ロジックを備え skip がないため、
                    push 後にドキュメントが直接 ✅ Implemented になる可能性があります。
                    開発者は必要に応じてアサーションを最適化 → サイトに同期公開
```

---

## ⚠️ 開発者操作ガイド

### テストの進捗を同期するには？
ドキュメント内のテスト項目を ✅ `Implemented` と表示させるために、Markdown を編集する必要は**ありません**。以下を行うだけです：

1. `tests/unit/` または `tests/scenario/` 内の該当する `_auto.py` ファイルを探す
2. `pytest.skip(...)` の行を削除する
3. 実際のアサーションロジックを記述する
4. `main` ブランチに push する → ドキュメントが自動的に緑（Implemented）に変わる

### テストディレクトリ構造の規約

```
services/<service>/tests/
├── conftest.py          ← グローバル fixture（http_client 等）、すべての子ディレクトリに適用
├── unit/                ← 単体テスト（外部サービスに依存せず、AsyncMock を使用）
│   ├── test_*_unit_auto.py   ← 自動生成された P0 スケルトン
│   ├── repositories/
│   └── utils/
└── scenario/            ← シナリオ/結合テスト（HTTP 経由で本番または Mock サービスを呼び出し）
    └── test_*_scenario_auto.py  ← 自動生成された P1+P1-5 スケルトン
```

### スタイルカスタマイズについて
ドキュメントスタイルは [custom.scss](_sass/custom/custom.scss) で統一管理されています。
- **列幅制御**：CSS により「業務手順」などの長文列を強制的に **450px** に設定しています。テーブル作成時に手動で HTML の `<div>` タグを追加する必要はありません。
- **背景の最適化**：高輝度のグラデーションデザインを採用しています。清潔感を保つため、暗い背景の使用は禁止されています。

---

## 📦 新規プロジェクトへの導入ステップ
このドキュメント基盤を新しいプロジェクトに移植する場合、以下の核心ファイルを必ず含めてください：
1. `docs/` ディレクトリとその構造。
2. `scripts/` 下のすべての自動同期スクリプト（`auto_append_tests.py`、`sync_testcases.py`）。
3. `.github/workflows/` 下の yml 定義。
4. ルートディレクトリの `Gemfile` と `_config.yml`。

> [!IMPORTANT]
> 移植後、GitHub リポジトリの設定で **Pages** の Source を **GitHub Actions** に設定することを忘れないでください。

---
*最終更新日：{{ "now" | date: "%Y-%m-%d" }}*

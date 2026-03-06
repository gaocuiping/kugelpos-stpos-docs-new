---
title: "ドキュメント管理"
layout: default
nav_order: 5
---

# ドキュメント管理 — Jekyll + GitHub Pages

本プロジェクトの公式ドキュメント（当サイト）は、**「Jekyll による静的サイト自動構築」** と **「Docs-as-Code（文書即コード）による自動同期」** という2つの強力な自動化基盤によって運用されています。

このページでは、サイトの基本構成と、開発チームが日常的に活用する「自動化フロー」の仕組み、および新たなプロジェクトへの設定移植手順を解説します。

---

## 🏗️ サイトの基本構成

| 項目 | 設定・利用技術 | 説明 |
|------|-------------|------|
| **ビルダー** | [Jekyll](https://jekyllrb.com/) | Markdown ファイル群を高速に HTML サイトへ変換する静的サイトジェネレーター |
| **ホスティング** | [GitHub Pages](https://pages.github.com/) | サーバー構築不要で GitHub リポジトリから直接 Web サイトを公開 |
| **テーマ** | `just-the-docs` | 検索機能つき・多階層サイドバー付きのモダンなドキュメントUI（ダークモード対応） |
| **多言語対応** | Collections 活用 | `docs/ja/` (日本語) と `docs/en/` (英語) の言語切り替え構造を実装 |

---

## ⚡ 2つのコア自動化機能（Docs-as-Code）

本サイトは手動でのドキュメント保守作業を極限まで減らすため、以下の **2大自動化システム** を組み込んでいます。

### 柱1：API 仕様書の自動生成 (FastAPI → Markdown)
開発者が `services/` 配下の **Python (FastAPI) コード**や Pydantic モデルを変更して Push すると、スクリプトがコードをスキャンし、各サービスの API エンドポイントやデータモデルの Markdown ドキュメントを全自動で生成します。

### 柱2：テスト仕様書の自動同期 (Test Code → Markdown)
開発者が `tests/` 配下に **Python テストコード**を作成して Push すると、スクリプトが Docstring の特定タグを解析し、事前に定義されたテスト要件一覧表（Markdown）のステータスを自動で「実装済」に更新します。

---

## 🔄 詳細な実装フローと仕組み

これら2つの自動化は、いずれも `main` ブランチへの **Push** をトリガーとして、GitHub Actions が背後で全てのスクリプト実行・Commit・デプロイを代行します。

### Flow A : API ドキュメントの自動生成フロー

* **設定ファイル**: `.github/workflows/generate-docs.yml`
* **実行スクリプト**: `scripts/generate_docs.sh`

```mermaid
graph TD;
    A[開発者が API の Python コードを修正・Push] --> B[GitHub Action: generate-docs.yml 起動]
    B --> C[generate_docs.sh 実行]
    C --> D[各サービスの @router などを解析]
    D --> E[api-overview-generated.md 14ファイル出力]
    E --> F[自動 Commit & Push]
    F --> G[Flow C: サイト公開フローへ連携]
```

### Flow B : テスト仕様書の自動同期フロー

* **設定ファイル**: `.github/workflows/sync-test-docs.yml`
* **実行スクリプト**: `scripts/sync_testcases.py`

```mermaid
graph TD;
    A[開発者が Python テストコードを修正・Push] --> B[GitHub Action: sync-test-docs.yml 起動]
    B --> C[sync_testcases.py 実行]
    C --> D[テスト関数の @TestCaseID: 〇〇 タグを ast 解析]
    D --> E[テスト表 md の該当行 ❌ を ✅ にマーク]
    E --> F[自動 Commit & Push]
    F --> G[Flow C: サイト公開フローへ連携]
```

### Flow C : サイトビルド＆公開フロー

* **設定ファイル**: `.github/workflows/jekyll-gh-pages.yml`

```text
Flow A / Flow B によるドキュメントの自動更新
⬇
GitHub Action `jekyll-gh-pages.yml` 起動
⬇
Ruby / Jekyll 環境セットアップ ＆ `bundle exec jekyll build`
⬇
生成された HTML の Artifacts を GitHub Pages 環境へデプロイ
⬇
🌐 https://<org>.github.io/<repo>/ で公開完了（数分で反映）
```

---

## ⚠️ 【重要】テストコード実装時の必須ルール（Flow B 関連）

テストドキュメントの自動同期（Flow B）を正常に稼働させるため、機能テスト（単体・結合・総合）を作成・修正する際は、**必ず関数（またはクラス）の Docstring に `@TestCaseID: [ID]` を記述してください。**

```python
def test_calc_subtotal_discount():
    """
    カートの小計金額割引計算ロジックをテスト
    
    @TestCaseID: CT-U-011  <-- 🎯 必須：この1行がないと仕様書が自動更新されません
    """
    assert result == 900
```

* **このタグがある場合**：Push 後に自動で Markdown 仕様書の「❌ 補充」が「✅ 実装済」に置き換わります（要件との完全なトレースバック）。
* **このタグがない場合**：スクリプトは無視してスキップし、テスト自体は成功しても仕様書には反映されません（補助的・一時的なデバッグ用テスト等として扱われます）。

---

## 📦 新規プロジェクトへの全サイト基盤（Docs + Automation）の移植手順

この Jekyll ドキュメントサイト、API自動生成、およびテスト仕様書自動更新の強力な基盤を別プロジェクト全体に適用するには、以下の 5 ステップを実行します。

| 移植レイヤー | 対象ファイル/ディレクトリ | 説明 |
| :--- | :--- | :--- |
| **1. Jekyll 基盤** | `docs/` (コンテンツ除く), `Gemfile`, `_config.yml` | サイトのデザイン、検索機能、多言語構造を移植します。 |
| **2. 自動化スクリプト** | `scripts/generate_docs.sh`, `scripts/sync_testcases.py` | API 抽出エンジンとテスト ID 解析エンジンを移植します。 |
| **3. CI/CD (GitHub)** | `.github/workflows/` 配下の全 `.yml` | 自動デプロイ、自動生成、自動同期のワークフローを移植します。 |
| **4. テンプレート** | `docs/ja/index.md`, `testcases-*.md` 等 | プロジェクト構成合わせたナビゲーションとテスト表の雛形を移植します。 |
| **5. 基本設定** | `_config.yml` | 移植先プロジェクトの `baseurl` やリポジトリ名を設定に合わせて微調整します。 |

### 移行後の運用イメージ
1. **通常ドキュメント**: `docs/` 配下にマークダウンを追加するだけで、1分後にサイトに反映されます。
2. **API 仕様**: ソースコードに新しいエンドポイントを書く（`@router.xxx`）だけで、仕様書が自動生成されます。
3. **テスト進捗**: テストコードに `@TestCaseID: xxx` を書き込むだけで、仕様書の表が「✅ 実装済」に自動更新されます。


---

## � 初回セットアップ・手動デプロイ手順

サイトの初回立ち上げ時のみ、以下の GitHub リポジトリ設定が必要です。

1. `git push origin main` で全てのリポジトリ内容を Push
2. GitHub Web 画面の **Settings** → **Pages** → **Source** を「**GitHub Actions**」に変更
3. **Settings** → **Actions** → Workflow permissions を「**Read and write**」に設定（これにより Actions ボットが自動 Commit できるようになります）

以降、すべてのサイト更新は自動化されます。

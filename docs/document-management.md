---
title: "ドキュメント管理"
layout: default
nav_order: 5
---

# ドキュメント管理 — Jekyll + GitHub Pages

## Jekyll とは

**Jekyll** は静的サイトジェネレーターです。Markdown で書いたドキュメントを HTML サイトに自動変換します。

| 特徴 | 説明 |
|------|------|
| Markdown 対応 | `.md` ファイルをそのまま Web ページに変換 |
| テーマシステム | `just-the-docs` 等のテーマでプロフェッショナルな見た目を実現 |
| 検索機能 | サイト内全文検索を標準搭載 |
| ナビゲーション | Front Matter でサイドバーの階層構造を自動生成 |
| ローカルプレビュー | `bundle exec jekyll serve` で即座にプレビュー可能 |

## GitHub Pages とは

**GitHub Pages** は GitHub リポジトリから直接 Web サイトをホスティングするサービスです。

| 特徴 | 説明 |
|------|------|
| 無料ホスティング | パブリックリポジトリは無料で公開可能 |
| 自動デプロイ | push するだけでサイトが自動更新 |
| カスタムドメイン | 独自ドメインの設定に対応 |
| HTTPS 対応 | SSL 証明書を自動提供 |
| アクセス制御 | プライベートリポジトリで閲覧制限可能（Enterprise） |

---

## 本プロジェクトでの活用

### 🔧 サイト構成

| 項目 | 設定 |
|------|------|
| テーマ | `just-the-docs`（ダークモード） |
| 多言語対応 | English / 日本語 |
| 検索 | サイト内全文検索有効 |
| 構成ファイル | `docs/_config.yml` |

### 📁 ディレクトリ構成

```
docs/
├── _config.yml          # Jekyll 設定
├── Gemfile              # Ruby 依存関係
├── index.md             # トップページ
├── en/                  # 英語ドキュメント
│   ├── index.md
│   ├── account/         # サービス別ドキュメント
│   ├── terminal/
│   ├── master-data/
│   ├── cart/
│   ├── report/
│   ├── journal/
│   ├── stock/
│   └── commons/
└── ja/                  # 日本語ドキュメント
    ├── index.md
    └── ...（同上）
```

---

## ✅ 自動化機能

### 1. 仕様ドキュメント自動生成（ソースベース）

| 構成要素 | ファイル | 役割 |
|---------|---------|------|
| 生成スクリプト | `scripts/generate_docs.sh` | FastAPI ソースコードから API 概要を抽出・生成 |
| 解析スクリプト | `scripts/sync_testcases.py` | Pythonの `ast` でテストコードの `@TestCaseID: XXX` Docstringを解析し、Markdown表を自動更新 |
| GitHub Actions | `.github/workflows/generate-docs.yml` | APIソース変更時に自動化APIドキュメント生成をトリガー |
| GitHub Actions | `.github/workflows/sync-test-docs.yml` | テスト用Pythonコード変更時にテスト仕様書の Markdown 状態（`❌ 補充` → `✅ 実装済`）を自動更新 |

```
ソースコード変更 → push → 自動スキャン → ドキュメント生成 → 自動コミット
```

### 2. サイト自動公開・更新

| 構成要素 | ファイル | 役割 |
|---------|---------|------|
| ビルド＆デプロイ | `.github/workflows/jekyll-gh-pages.yml` | docs/ 変更時に自動ビルド＆デプロイ |

```
ドキュメント変更 → push → Jekyll ビルド → GitHub Pages 自動デプロイ
```

### 3. エンドツーエンド自動化フロー

```
ソースコード変更 → 自動ドキュメント生成 → 自動コミット → 自動ビルド → 自動デプロイ
```

---

## � 詳細実装フロー

### フロー 1: ドキュメント自動生成（generate_docs.sh）

```
┌─ 開発者が services/ 配下のソースコードを修正 ─┐
│                                              │
│  例: services/account/app/api/v1/auth.py     │
│      @router.post("/login") を追加            │
└──────────────────┬───────────────────────────┘
                   ↓
┌─ generate_docs.sh 実行 ─────────────────────┐
│                                              │
│  Step 1: サービスディレクトリをスキャン         │
│    services/* を走査し、各サービスを検出        │
│    → account, terminal, master-data, ...     │
│                                              │
│  Step 2: API エンドポイント抽出               │
│    app/api/ 配下の .py ファイルから            │
│    @router.get/post/put/delete を grep        │
│    → メソッド、パス、関数名、ソースファイルを取得 │
│                                              │
│  Step 3: データモデル抽出                     │
│    app/schemas/ と app/models/ から           │
│    class XxxModel(BaseModel) を grep          │
│    → クラス名、親クラス、ソースファイルを取得    │
│                                              │
│  Step 4: 環境変数抽出                         │
│    app/config/settings.py から               │
│    変数名 = デフォルト値 を抽出                │
│                                              │
│  Step 5: Markdown ファイル生成                │
│    docs/en/<service>/api-overview-generated.md │
│    docs/ja/<service>/api-overview-generated.md │
│    Jekyll Front Matter 付きで出力             │
└──────────────────┬───────────────────────────┘
                   ↓
          14 ファイル生成完了
```

### フロー 2: テスト仕様書自動同期（Docs-as-Code）

```
┌─ 開発者が tests/ 配下のテストコードを作成・修正 ─┐
│                                              │
│  例: services/cart/tests/test_cart.py         │
│  def test_subtotal():                        │
│      \"\"\"                                    │
│      @TestCaseID: CT-U-011                   │
│      \"\"\"                                    │
│      assert ...                              │
└──────────────────┬───────────────────────────┘
                   ↓
┌─ GitHub Action: sync-test-docs.yml 自動起動 ──┐
│                                              │
│  Step 1: check out repository                 │
│                                              │
│  Step 2: scripts/sync_testcases.py 実行       │
│    - Python ast モジュールで全 test_*.py を解析 │
│    - Docstring から @TestCaseID を全て抽出      │
│    - docs/ja/testing/ および docs/en/testing/  │
│      配下の testcases-*.md を走査し、            │
│      一致する ID 行の「❌ 補充」を「✅ 実装済」に  │
│      自動で置換                                │
│                                              │
│  Step 3: 自動コミット＆プッシュ                 │
│    git commit -m "docs: auto-sync testcase"  │
│    git push                                  │
└──────────────────┬───────────────────────────┘
                   ↓
        Markdown テスト仕様書が自動更新
        → フロー 4（Jekyllビルド）が自動トリガー
```

### フロー 3: GitHub Actions — ドキュメント自動生成ワークフロー

**ファイル:** `.github/workflows/generate-docs.yml`

```
┌─ トリガー条件 ──────────────────────────────┐
│  push to main ブランチで以下のパスが変更された場合: │
│    - services/**/app/api/**                  │
│    - services/**/app/schemas/**              │
│    - services/**/app/models/**               │
│    - services/**/app/config/settings.py      │
│    - services/**/app/main.py                 │
└──────────────────┬───────────────────────────┘
                   ↓
┌─ ワークフロー実行 ──────────────────────────┐
│                                              │
│  Job: generate-docs                          │
│  Runner: ubuntu-latest                       │
│                                              │
│  Step 1: actions/checkout@v4                 │
│    → リポジトリをチェックアウト               │
│                                              │
│  Step 2: scripts/generate_docs.sh 実行       │
│    → 全サービスの API 概要ドキュメントを生成    │
│                                              │
│  Step 3: 変更チェック                         │
│    git diff --quiet docs/ で変更有無を確認     │
│    → 変更なし: ワークフロー終了               │
│    → 変更あり: 次のステップへ                  │
│                                              │
│  Step 4: 自動コミット＆プッシュ               │
│    git config user.name "github-actions[bot]" │
│    git add docs/                             │
│    git commit -m "docs: auto-update API docs" │
│    git push                                  │
└──────────────────┬───────────────────────────┘
                   ↓
        docs/ 変更がリポジトリに反映
        → フロー 4 が自動トリガー
```

### フロー 4: GitHub Actions — Jekyll ビルド＆デプロイワークフロー

**ファイル:** `.github/workflows/jekyll-gh-pages.yml`

```
┌─ トリガー条件 ──────────────────────────────┐
│  push to main ブランチで以下のパスが変更された場合: │
│    - docs/**                                 │
│  または workflow_dispatch（手動トリガー）       │
└──────────────────┬───────────────────────────┘
                   ↓
┌─ Job 1: build ──────────────────────────────┐
│  Runner: ubuntu-latest                       │
│                                              │
│  Step 1: actions/checkout@v4                 │
│    → リポジトリをチェックアウト               │
│                                              │
│  Step 2: actions/configure-pages@v5          │
│    → GitHub Pages の設定を取得               │
│                                              │
│  Step 3: ruby/setup-ruby@v1                  │
│    → Ruby 環境セットアップ                    │
│    → bundler-cache: true でキャッシュ有効     │
│                                              │
│  Step 4: Jekyll ビルド                       │
│    working-directory: docs/                  │
│    bundle exec jekyll build                  │
│    → _site/ ディレクトリに HTML を生成        │
│                                              │
│  Step 5: actions/upload-pages-artifact@v3    │
│    → ビルド成果物を Artifact としてアップロード │
└──────────────────┬───────────────────────────┘
                   ↓
┌─ Job 2: deploy（build 完了後に実行）──────────┐
│  environment: github-pages                   │
│                                              │
│  Step 1: actions/deploy-pages@v4             │
│    → Artifact を GitHub Pages にデプロイ      │
│    → https://<org>.github.io/<repo>/ で公開   │
│                                              │
│  並行制御:                                    │
│    concurrency: "pages" グループで             │
│    同時に1つのデプロイのみ実行                  │
└──────────────────┬───────────────────────────┘
                   ↓
       ドキュメントサイト公開完了 ✅
       （push から約 1-2 分で反映）
```

### 全体フロー図

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌───────────┐
│ 開発者が  │     │ generate-docs│     │ jekyll-gh-   │     │ ユーザーが │
│ ソース   │────→│ .yml         │────→│ pages.yml    │────→│ ブラウザで │
│ コード修正│ push│ ドキュメント  │commit│ Jekyll ビルド│deploy│ ドキュメント│
│          │     │ 自動生成      │     │ ＆デプロイ    │     │ を閲覧     │
└──────────┘     └──────────────┘     └──────────────┘     └───────────┘
                      ↑                     ↑
                 services/**           docs/**
                 変更時トリガー         変更時トリガー
```

### Docs-as-Code（他プロジェクトへの設定移植手順）

新しいプロジェクトでこの「テストドキュメントの自動更新基盤」を再現するには、以下の4ステップを実行します：

1. **解析スクリプトの移植**：`scripts/sync_testcases.py` ファイルをコピー
2. **CI/CD の移植**：`.github/workflows/sync-test-docs.yml` ファイルをコピー
3. **Markdownの移植**：`docs/ja/testing/` および `docs/en/testing/` 配下の `testcases-*.md` テンプレートをコピー
4. **プッシュ**：全ファイルをコミット＆プッシュ

開発チームは、テストの Python コード内の docstring に `@TestCaseID: [ID]` を記述するだけで、以後のドキュメント更新はすべて GitHub Actions が全自動で行います。

---

## �📋 デプロイ手順（初回のみ）

1. `git push origin main` でリポジトリに Push
2. Settings → Pages → Source を **「GitHub Actions」** に変更
3. Settings → Actions → Workflow permissions を **「Read and write」** に設定

以降、すべての更新が自動化されます。

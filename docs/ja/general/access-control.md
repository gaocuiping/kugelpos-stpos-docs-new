---
title: "アクセス制御ガイド"
parent: 共通
grand_parent: 日本語
nav_order: 7
layout: default
---

# アクセス制御・権限管理

GitHub の機能を利用した Kugelpos ドキュメントサイトのアクセス制御方法について説明します。

---

## 1. リポジトリの可視性設定

| 設定 | GitHub Pages への影響 |
|------|---------------------|
| **Public** | ドキュメントはインターネット上の誰でもアクセス可能 |
| **Private** | リポジトリの共同作業者のみアクセス可能（GitHub Enterprise が必要） |
| **Internal**（Enterprise） | 組織内のメンバーのみアクセス可能 |

### 変更方法

1. **Repository Settings** → **General** を開く
2. **Danger Zone** → **Change repository visibility** をクリック

---

## 2. GitHub Pages のアクセス制御

### パブリックリポジトリ
- Pages は常に公開アクセス可能
- 追加のアクセス制御は不可

### プライベートリポジトリ（GitHub Enterprise Cloud）
- 組織メンバーのみにアクセスを制限可能
- Settings → **Pages** → **Access control** → **Private** を選択

### 推奨設定

| 環境 | 可視性 | Pages アクセス |
|------|--------|---------------|
| 開発 | Private | チームメンバーのみ |
| 本番 | Public または Internal | 組織全体 |

---

## 3. ブランチ保護ルール

`main` ブランチを保護してドキュメントの品質を確保します。

### 推奨ルール

1. **プルリクエストレビューの必須化**
   - 最低1名の承認レビュー
   - 古い承認を無効化

2. **ステータスチェックの必須化**
   - Jekyll ビルドチェックの成功を必須に

3. **プッシュ制限**
   - 指定されたメンテナーのみが直接プッシュ可能

### 設定方法

1. **Repository Settings** → **Branches** を開く
2. `main` ブランチの **Add rule** をクリック
3. 必要な保護設定を有効化

---

## 4. CODEOWNERS によるドキュメントレビュー

`CODEOWNERS` ファイルを作成して、ドキュメント変更のレビューを必須化します：

```
# .github/CODEOWNERS

# ドキュメント変更はドキュメントチームのレビューが必要
/docs/ @org-name/docs-team

# GitHub Actions ワークフローは DevOps チームのレビューが必要
/.github/workflows/ @org-name/devops-team

# サービス別ドキュメントは各チームのレビューが必要
/docs/ja/account/ @org-name/account-team
/docs/ja/cart/ @org-name/cart-team
/docs/ja/terminal/ @org-name/terminal-team
/docs/ja/master-data/ @org-name/masterdata-team
/docs/ja/report/ @org-name/report-team
/docs/ja/journal/ @org-name/journal-team
/docs/ja/stock/ @org-name/stock-team
```

---

## 5. GitHub Teams と権限

### 推奨チーム構成

| チーム | リポジトリ権限 | 説明 |
|--------|--------------|------|
| `docs-admin` | Admin | 全権限、設定管理 |
| `docs-maintainer` | Maintain | Issue・PR 管理、マージ |
| `docs-writer` | Write | フィーチャーブランチへのプッシュ、PR 作成 |
| `docs-reader` | Read | ドキュメント閲覧のみ |

### 権限一覧

| アクション | Read | Write | Maintain | Admin |
|-----------|------|-------|----------|-------|
| ドキュメント閲覧 | ✅ | ✅ | ✅ | ✅ |
| PR 作成 | ❌ | ✅ | ✅ | ✅ |
| PR マージ | ❌ | ❌ | ✅ | ✅ |
| 設定管理 | ❌ | ❌ | ❌ | ✅ |
| Pages デプロイ | ❌ | ❌ | ✅ | ✅ |

---

## 6. ワークフロー権限設定

GitHub Actions ワークフローは最小限の権限を使用しています：

```yaml
# jekyll-gh-pages.yml
permissions:
  contents: read    # リポジトリ読み取り
  pages: write      # Pages デプロイ
  id-token: write   # デプロイ用 OIDC トークン

# generate-docs.yml
permissions:
  contents: write   # 生成ドキュメントのコミット
```

### セキュリティのベストプラクティス

1. **`GITHUB_TOKEN` を使用** - リポジトリ範囲に自動的にスコープされます
2. **シークレットの保存は最小限に** - 不要なシークレットは保存しない
3. **サードパーティ Actions のレビュー** - 使用前に必ず確認
4. **アクションバージョンの固定** - 本番環境では SHA ハッシュでバージョンを固定

---

## 7. セットアップチェックリスト

- [ ] リポジトリの可視性を設定（Public/Private）
- [ ] GitHub Pages を有効化（Settings → Pages → Source: GitHub Actions）
- [ ] `main` ブランチの保護ルールを設定
- [ ] `CODEOWNERS` ファイルを作成
- [ ] GitHub Teams に適切な権限を設定
- [ ] ワークフロー権限を確認
- [ ] デプロイパイプラインのテスト

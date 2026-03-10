import os

base = '/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs'

content_ja = """---
title: "日本語"
nav_order: 3
has_children: true
permalink: /ja/
---

# 日本語ドキュメント

Kugelpos POS バックエンドのドキュメントへようこそ。

## セクション一覧

| セクション | 説明 |
|-----------|------|
| [共通](general/) | アーキテクチャ、設計パターン、エラーコード、Dapr コンポーネント |
| [アカウント](account/) | ユーザー認証・JWT 管理 (port: 8000) |
| [ターミナル](terminal/) | ターミナル・店舗管理 (port: 8001) |
| [マスターデータ](master-data/) | マスターデータ管理 (port: 8002) |
| [カート](cart/) | 商品登録・取引処理 (port: 8003) |
| [レポート](report/) | 売上レポート生成 (port: 8004) |
| [ジャーナル](journal/) | 電子ジャーナル検索 (port: 8005) |
| [在庫](stock/) | 在庫管理 (port: 8006) |
| [共通ライブラリ](commons/) | 共通ライブラリ・共通関数 |
"""

content_en = """---
title: "English"
nav_order: 2
has_children: true
permalink: /en/
---

# English Documentation

Welcome to the Kugelpos POS Backend documentation.

## Sections

| Section | Description |
|---------|-------------|
| [General](general/) | Architecture, design patterns, error codes, Dapr components |
| [Account](account/) | User authentication and JWT management (port: 8000) |
| [Terminal](terminal/) | Terminal and store management (port: 8001) |
| [Master Data](master-data/) | Master data management (port: 8002) |
| [Cart](cart/) | Product registration and transactions (port: 8003) |
| [Report](report/) | Sales report generation (port: 8004) |
| [Journal](journal/) | Electronic journal search (port: 8005) |
| [Stock](stock/) | Inventory management (port: 8006) |
| [Commons](commons/) | Shared library and common functions |
"""

with open(os.path.join(base, 'ja', 'index.md'), 'w') as f:
    f.write(content_ja)
print('Wrote ja/index.md')

with open(os.path.join(base, 'en', 'index.md'), 'w') as f:
    f.write(content_en)
print('Wrote en/index.md')

# Verify
for lang in ['ja', 'en']:
    path = os.path.join(base, lang, 'index.md')
    with open(path) as f:
        lines = f.readlines()
    print(f'{lang}/index.md: {len(lines)} lines, first content line: {lines[8].strip() if len(lines) > 8 else "N/A"}')

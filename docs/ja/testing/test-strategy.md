---
title: "テスト戦略"
parent: テスト
grand_parent: 日本語
nav_order: 2
layout: default
---

# テスト戦略

## 概要

| 項目 | 内容 |
|------|------|
| フレームワーク | pytest |
| カバレッジツール | pytest-cov |
| 目標カバレッジ | サービスごとに 80% |
| CI/CD | GitHub Actions |

## テストレベル

| レベル | ツール | スコープ |
|-------|-------|---------|
| ユニット | pytest + unittest.mock | 個別の関数・クラス |
| 統合 | pytest + Dapr テストクライアント | サービス間連携・pub/sub イベント |
| シナリオ/E2E | pytest | エンドツーエンドのビジネスフロー |

## テスト命名規則

```python
# test_<モジュール>_<関数>_<条件>.py
def test_login_with_valid_credentials_returns_token():
    ...

def test_login_with_invalid_password_raises_401():
    ...
```

## テスト実行コマンド

```bash
# 全テスト実行
pytest services/<service>/tests/

# カバレッジ付きで実行
pytest --cov=app --cov-report=html services/<service>/tests/

# テスト種別ごとに実行
pytest services/<service>/tests/unit/
pytest services/<service>/tests/integration/
```

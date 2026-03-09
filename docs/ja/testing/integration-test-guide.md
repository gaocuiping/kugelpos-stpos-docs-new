---
title: "統合テストガイド"
parent: テスト
grand_parent: 日本語
nav_order: 4
layout: default
---

# 統合テストガイド

## スコープ

統合テストは以下のサービス間連携を検証します：
- Dapr pub/sub イベントフロー
- MongoDB 実際の読み書き
- Redis キャッシュ統合
- サービス間 HTTP 通信

## ディレクトリ構成

```
services/<service>/
└── tests/
    └── integration/
        ├── test_dapr_pubsub.py
        ├── test_db_operations.py
        └── conftest.py
```

## Dapr Pub/Sub テストサンプル

```python
import pytest
from dapr.clients import DaprClient

@pytest.mark.integration
async def test_publish_journal_event():
    async with DaprClient() as client:
        # イベント発行
        await client.publish_event(
            pubsub_name="messagebus",
            topic_name="journal",
            data={"transaction_id": "txn-001", "amount": 1000}
        )
        # サブスクライバーがイベントを受信したことを確認
        # （DB またはモックサブスクライバーエンドポイントで確認）
        ...
```

## 前提条件

| 条件 | 備考 |
|------|------|
| Dapr サイドカー起動済み | `dapr run` または docker-compose |
| MongoDB 起動済み | 本番ではなくテスト用 DB を使用 |
| Redis 起動済み | テスト用インスタンスを使用 |
| 環境変数設定 | `TEST_MODE=true` を設定 |

## 統合テスト実行コマンド

```bash
# 依存サービスを先に起動
docker-compose -f docker-compose.test.yml up -d

# 統合テスト実行
pytest services/<service>/tests/integration/ -m integration

# 終了処理
docker-compose -f docker-compose.test.yml down
```

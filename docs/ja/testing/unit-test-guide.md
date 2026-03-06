---
title: "ユニットテストガイド"
parent: テスト
grand_parent: 日本語
nav_order: 3
layout: default
---

# ユニットテストガイド

## ディレクトリ構成

```
services/<service>/
└── tests/
    └── unit/
        ├── test_api_<endpoint>.py
        ├── test_service_<module>.py
        └── conftest.py
```

## 基本テンプレート

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.your_service import YourService

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def service(mock_repo):
    return YourService(repository=mock_repo)

class TestYourService:
    async def test_create_success(self, service, mock_repo):
        mock_repo.insert.return_value = {"id": "123"}
        result = await service.create({"name": "test"})
        assert result["id"] == "123"

    async def test_create_duplicate_raises_error(self, service, mock_repo):
        mock_repo.insert.side_effect = DuplicateKeyError("duplicate")
        with pytest.raises(AppException) as exc:
            await service.create({"name": "test"})
        assert exc.value.status_code == 409
```

## 基本ルール

| ルール | 説明 |
|-------|------|
| 外部依存はすべてモック化 | DB、Redis、Dapr、HTTP 呼び出し |
| エラーパスもテスト | 必ず失敗・例外シナリオをテスト |
| 1テスト1アサーション | 各テストは1つの動作を検証 |
| フィクスチャ活用 | `conftest.py` でセットアップを共有 |
| カバレッジ閾値 | モジュールごとに最低 80% |

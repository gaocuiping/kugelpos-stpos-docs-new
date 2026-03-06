---
title: "Unit Test Guide"
parent: Testing
grand_parent: English
nav_order: 3
layout: default
---

# Unit Test Guide

## Directory Structure

```
services/<service>/
└── tests/
    └── unit/
        ├── test_api_<endpoint>.py
        ├── test_service_<module>.py
        └── conftest.py
```

## Basic Template

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

## Key Rules

| Rule | Description |
|------|-------------|
| Mock all external dependencies | DB, Redis, Dapr, HTTP calls |
| Test error paths | Always test failure/exception scenarios |
| One assertion focus | Each test should verify one behavior |
| Use fixtures | Share setup via `conftest.py` |
| Coverage threshold | Minimum 80% per module |

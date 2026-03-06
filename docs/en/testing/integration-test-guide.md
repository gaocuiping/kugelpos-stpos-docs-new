---
title: "Integration Test Guide"
parent: Testing
grand_parent: English
nav_order: 4
layout: default
---

# Integration Test Guide

## Scope

Integration tests verify interactions between services, including:
- Dapr pub/sub event flows
- MongoDB actual read/write
- Redis cache integration
- Inter-service HTTP communication

## Directory Structure

```
services/<service>/
└── tests/
    └── integration/
        ├── test_dapr_pubsub.py
        ├── test_db_operations.py
        └── conftest.py
```

## Dapr Pub/Sub Test Example

```python
import pytest
from dapr.clients import DaprClient

@pytest.mark.integration
async def test_publish_journal_event():
    async with DaprClient() as client:
        # Publish event
        await client.publish_event(
            pubsub_name="messagebus",
            topic_name="journal",
            data={"transaction_id": "txn-001", "amount": 1000}
        )
        # Verify subscriber received the event
        # (check DB or mock subscriber endpoint)
        ...
```

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Dapr sidecar running | `dapr run` or docker-compose |
| MongoDB running | Use test database, not production |
| Redis running | Use test instance |
| Environment variables | Set `TEST_MODE=true` |

## Running Integration Tests

```bash
# Start dependencies first
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
pytest services/<service>/tests/integration/ -m integration

# Teardown
docker-compose -f docker-compose.test.yml down
```

---
title: "Test Strategy"
parent: Testing
grand_parent: English
nav_order: 2
layout: default
---

# Test Strategy

## Overview

| Item | Value |
|------|-------|
| Framework | pytest |
| Coverage Tool | pytest-cov |
| Target Coverage | 80% per service |
| CI/CD | GitHub Actions |

## Test Levels

| Level | Tool | Scope |
|-------|------|-------|
| Unit | pytest + unittest.mock | Individual functions and classes |
| Integration | pytest + Dapr test client | Service interactions and pub/sub events |
| Scenario/E2E | pytest | End-to-end business flows |

## Test Naming Convention

```python
# test_<module>_<function>_<condition>.py
def test_login_with_valid_credentials_returns_token():
    ...

def test_login_with_invalid_password_raises_401():
    ...
```

## Running Tests

```bash
# Run all tests
pytest services/<service>/tests/

# Run with coverage
pytest --cov=app --cov-report=html services/<service>/tests/

# Run specific test type
pytest services/<service>/tests/unit/
pytest services/<service>/tests/integration/
```

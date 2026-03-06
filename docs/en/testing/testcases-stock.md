---
title: "Stock Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 16
layout: default
---

# Stock Service Test Cases

Covers inventory management, snapshot scheduler, and WebSocket alerts.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| SK-U-01 | Stock retrieval, update, and history verification | Basic | 🔴 High | ✅ Implemented |
| SK-U-02 | Reorder alert verification (conditions, triggers, min stock) | Alert | 🔴 High | ✅ Implemented |
| SK-U-03 | Snapshot scheduler verification (CRON settings, tenant updates) | Schedule | 🟠 High | ✅ Implemented |
| SK-U-04 | Snapshot retrieval by date range verification | Snapshot | 🟠 High | ✅ Implemented |
| SK-U-05 | Negative stock allowed flag behavior | Edge | 🟡 Med | ✅ Implemented |
| SK-U-06 | Multi-store stock list retrieval | Store | 🟡 Med | ✅ Implemented |
| SK-U-07 | WebSocket connection and alert reception | WS | 🔴 High | ✅ Implemented |
| SK-U-08 | WebSocket multi-client and unauthorized access | WS | 🟠 High | ✅ Implemented |
| SK-U-09 | Manual stock adjustment validation | CRUD | 🔴 High | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| SK-I-01 | Processing inventory allocation requests from other services via Dapr Subscribe | Integration | 🔴 High | ✅ Implemented |
| SK-I-02 | MongoDB atomic operation verification for stock updates | Integration | 🔴 High | ❌ Recommended |
| SK-S-01 | Stock update → reorder alert trigger → WebSocket notification E2E flow | Scenario | 🔴 High | ❌ Recommended |

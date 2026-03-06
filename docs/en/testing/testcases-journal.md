---
title: "Journal Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 17
layout: default
---

# Journal Service Test Cases

Tested mainly around journal saving and transaction type conversions.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| JN-U-01 | Health check API normal operation | Health | 🟡 Med | ✅ Implemented |
| JN-U-02 | Journal report operations verification | Basic | 🟡 Med | ✅ Implemented |
| JN-U-03 | Transaction log reception of normal sales (not cancelled) | Log | 🔴 High | ✅ Implemented |
| JN-U-04 | Transaction log reception and type conversion of cancelled sales | Log | 🔴 High | ✅ Implemented |
| JN-U-05 | Transaction rollback process on error | Error | 🟠 High | ✅ Implemented |
| JN-U-06 | Transaction type conversion logic (normal, cancelled, negative types) | Conversion | 🔴 High | ✅ Implemented |
| JN-U-07 | Journal date range search and pagination | Search | 🟠 High | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| JN-I-01 | Receiving journal from Report service via Pub/Sub | Integration | 🔴 High | ❌ Recommended |
| JN-I-02 | Synchronization with search indexes like Elasticsearch/MongoDB | Integration | 🟠 High | ❌ Recommended |
| JN-S-01 | Transaction complete → Journal saved → Searched via API E2E | Scenario | 🟠 High | ❌ Recommended |

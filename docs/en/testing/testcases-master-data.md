---
title: "Master Data Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 13
layout: default
---

# Master Data Service Test Cases

List of test cases extracted from current test code and missing recommended scenarios.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| MD-U-01 | Health check API and response time validation | Health | 🟡 Med | ✅ Implemented |
| MD-U-02 | Verify basic operations | Basic | 🟡 Med | ✅ Implemented |
| MD-U-03 | Item master retrieval (all/individual) | Item | 🔴 High | ❌ Recommended |
| MD-U-04 | Category master retrieval and hierarchy validation | Category | 🟠 High | ❌ Recommended |
| MD-U-05 | Tax master retrieval validation | Tax | 🔴 High | ❌ Recommended |
| MD-U-06 | Payment method master retrieval validation | Payment | 🟠 High | ❌ Recommended |
| MD-U-07 | Master cache retrieval from Dapr Statestore (Redis) | Cache | 🔴 High | ❌ Recommended |
| MD-U-08 | 404 error handling when requesting non-existent master data | Error | 🟡 Med | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| MD-I-01 | Cache invalidation notification via Dapr pub/sub on master data update | Integration | 🔴 High | ❌ Recommended |
| MD-I-02 | Loading item data from MongoDB and saving cache to Redis | Integration | 🔴 High | ❌ Recommended |
| MD-S-01 | Item info retrieval flow via gRPC from other services like Cart | Scenario | 🟠 High | ❌ Recommended |

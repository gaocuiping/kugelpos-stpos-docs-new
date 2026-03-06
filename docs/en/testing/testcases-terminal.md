---
title: "Terminal Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 12
layout: default
---

# Terminal Service Test Cases

List of test cases extracted from current test code and missing recommended scenarios. Currently, business logic tests are significantly lacking.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| TM-U-01 | Health check API normal operation (including background job details) | Health | 🟡 Med | ✅ Implemented |
| TM-U-02 | Verify basic terminal operations | Basic | 🟡 Med | ✅ Implemented |
| TM-U-03 | New terminal registration succeeds | CRUD | 🔴 High | ❌ Recommended |
| TM-U-04 | Registering existing terminal ID returns 409 | CRUD | 🔴 High | ❌ Recommended |
| TM-U-05 | Terminal information update succeeds | CRUD | 🟠 High | ❌ Recommended |
| TM-U-06 | Fetching non-existent terminal ID returns 404 | CRUD | 🟠 High | ❌ Recommended |
| TM-U-07 | Terminal heartbeat (last access time update) functions | Status | 🔴 High | ❌ Recommended |
| TM-U-08 | Terminal status (active/inactive) change process validation | Status | 🟠 High | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| TM-I-01 | Persistence of terminal/store information to MongoDB | Integration | 🔴 High | ❌ Recommended |
| TM-I-02 | Terminal info retrieval acceleration via Redis cache | Integration | 🟠 High | ❌ Recommended |
| TM-S-01 | Terminal boot → registration → heartbeat end-to-end flow | Scenario | 🟠 High | ❌ Recommended |

---
title: "Cart Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 14
layout: default
---

# Cart Service Test Cases

Rich business logic with many tests already implemented.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| CT-U-01 | Health check API normal operation | Health | 🟡 Med | ✅ Implemented |
| CT-U-02 | Item Entry resume function | Main | 🔴 High | ✅ Implemented |
| CT-U-03 | Error handling during cashless payment | Payment | 🔴 High | ✅ Implemented |
| CT-U-04 | Subtotal logic calculation accuracy validation | Calc | 🔴 High | ✅ Implemented |
| CT-U-05 | Terminal cache retrieval and update | Cache | 🟡 Med | ✅ Implemented |
| CT-U-06 | Transaction status validation | Status | 🟠 High | ✅ Implemented |
| CT-U-07 | Prevention of double void on already voided transactions | Void | 🔴 High | ✅ Implemented |
| CT-U-08 | Prevention of double return on already returned transactions | Return | 🔴 High | ✅ Implemented |
| CT-U-09 | List status and single retrieval consistency with double void/return prevention | Void/Return | 🔴 High | ✅ Implemented |
| CT-U-10 | Dapr Statestore session creation, reuse, timeout | Session | 🟠 High | ✅ Implemented |
| CT-U-11 | gRPC channel creation and reuse | gRPC | 🟠 High | ✅ Implemented |
| CT-U-12 | Single/multiple item tax calculation (mixed internal/external tax) | Tax | 🔴 High | ❌ Recommended |
| CT-U-13 | Discount calculation (single item, whole cart) | Discount | 🟠 High | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| CT-I-01 | Item info retrieval via direct gRPC from Cart to Master-data | Integration | 🔴 High | ✅ Implemented |
| CT-I-02 | Inventory allocation to Stock service on purchase completion (Pub/Sub) | Integration | 🔴 High | ❌ Recommended |
| CT-I-03 | History saving to Journal service on transaction completion (Pub/Sub) | Integration | 🔴 High | ❌ Recommended |
| CT-S-01 | item-book scenario (item scan → qty change → discount → payment) | Scenario | 🔴 High | ❌ Recommended |

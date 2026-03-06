---
title: "Report Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 15
layout: default
---

# Report Service Test Cases

Extensively tested, especially around aggregation logic.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| RP-U-01 | Basic report operations verification | Basic | 🟡 Med | ✅ Implemented |
| RP-U-02 | Validation of cancelled transaction exclusion flag | Cancel | 🔴 High | ✅ Implemented |
| RP-U-03 | Category report formatting and date calculation | Category | 🔴 High | ✅ Implemented |
| RP-U-04 | Unique identification across multiple stores and terminals | Multi | 🟠 High | ✅ Implemented |
| RP-U-05 | Aggregation logic validation for Return transactions | Return | 🔴 High | ✅ Implemented |
| RP-U-06 | Cartesian product bug prevention for mixed multiple tax rates | Tax | 🔴 High | ✅ Implemented |
| RP-U-07 | Mixed payment methods (split payment) verification | Payment | 🔴 High | ✅ Implemented |
| RP-U-08 | Data integrity: payment amount always equals sales + tax | Integrity | 🔴 High | ✅ Implemented |
| RP-U-09 | Edge cases: 0 yen transaction, empty tax array | Edge | 🟡 Med | ✅ Implemented |
| RP-U-10 | Flash report date validation (Store/Terminal) | Flash | 🟠 High | ✅ Implemented |
| RP-U-11 | Item report date calculation verification | Item | 🟠 High | ✅ Implemented |
| RP-U-12 | Journal integration (Flash/Daily report transmission) | Journal | 🔴 High | ✅ Implemented |
| RP-U-13 | Payment report error handling and date validation | Payment | 🟠 High | ✅ Implemented |
| RP-U-14 | Internal/external mixed tax rates display and breakdown | Tax | 🔴 High | ✅ Implemented |
| RP-U-15 | Complex scenarios of voided sales and returns | Void | 🔴 High | ✅ Implemented |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| RP-I-01 | Dapr StateStore saving verification on report creation | Integration | 🔴 High | ❌ Recommended |
| RP-I-02 | Dapr Pub/Sub report publishing test to Journal service | Integration | 🔴 High | ❌ Recommended |

---
title: "Account Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 11
layout: default
---

# Account Service Test Cases

List of test cases extracted from current test code and missing recommended scenarios.

## Unit Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| AC-U-01 | Health check API works normally, even without Dapr | Health | 🟡 Med | ✅ Implemented |
| AC-U-02 | Verify basic system operations | Basic | 🟡 Med | ✅ Implemented |
| AC-U-03 | Login with valid credentials issues JWT token | Auth | 🔴 High | ❌ Recommended |
| AC-U-04 | Login with invalid password returns 401 | Auth | 🔴 High | ❌ Recommended |
| AC-U-05 | Login with non-existent user returns 401 | Auth | 🔴 High | ❌ Recommended |
| AC-U-06 | Expired token access returns 401 | Auth | 🔴 High | ❌ Recommended |
| AC-U-07 | Refresh token successfully gets new access token | Auth | 🟠 High | ❌ Recommended |
| AC-U-08 | Missing tenant ID header is rejected | Tenant | 🔴 High | ❌ Recommended |
| AC-U-09 | Get user profile API returns correct data | Profile | 🟡 Med | ❌ Recommended |
| AC-U-10 | Password change is processed correctly | Profile | 🟡 Med | ❌ Recommended |

## Integration & Scenario Tests

| ID | Test Case | Type | Priority | Status |
|----|-----------|------|----------|--------|
| AC-I-01 | End-to-end API call flow with JWT authentication | Scenario | 🔴 High | ❌ Recommended |
| AC-I-02 | Complete flow of user creation, saving, and retrieval in MongoDB | Integration | 🟠 High | ❌ Recommended |
| AC-I-03 | Data isolation verification in multi-tenant environment | Integration | 🔴 High | ❌ Recommended |

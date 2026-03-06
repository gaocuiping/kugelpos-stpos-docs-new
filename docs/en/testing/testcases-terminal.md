---
title: "Terminal サービス テストケース"
parent: Testing
grand_parent: English
nav_order: 12
layout: default
---

# Terminal サービス テスト設計書

This document is a restructured test case design based on the Test Review Report.
It cleanly separates existing implemented tests and recommended supplementary tests (edge cases, negative flows) into three distinct levels: Unit, Integration, and Scenario/E2E.

---

## 1. サービスの概要とテスト戦略 (Overview & Strategy)
Overall policy regarding specific business logic, dependencies, and main test focuses for this service.

---

## 2. 単体テスト (Unit / ロジック単位)
Validates functions and classes in Service/Model layers isolated from external I/O using Mocks.

### 2.1 既存のテストケース (test-review.md より抽出実装済)

| Test File | Coverage Target | Status |
|---|---|---|
| - | No unit tests currently implemented | ❌ |

### 2.2 推奨・補充テストケース (不足分の強化対象)

| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| **TM-U-010** | `POST /terminals` | Register unregistered MAC | DB insert data built | ❌ Missing Unit |
| **TM-U-011** | `POST /terminals` | Register MAC already bound | 409 Conflict raised | ❌ Missing Unit |
| **TM-U-020** | `POST /heartbeat` | Heartbeat reception logic | last_active_at updated | ❌ Missing Unit |
| **TM-E-002** | `Concurrency` | Concurrent registration requested at once | Tx lock applies, one 409 | ❌ Missing Unit |

---

## 3. 結合テスト (Integration / サービス間連携)
Validates component combinations, including actual Redis/DB access and Pub/Sub message chains between microservices.

### 3.1 既存のテストケース (実装済)

| Test File | Coverage Target | Status |
|---|---|---|
| - | No integration tests currently implemented | ❌ |

### 3.2 推奨・補充テストケース (不足分の連携強化)

| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| **TM-E-001** | `Resilience` | Dapr Redis down during heartbeat | 503 Fail-safe, no crash | ❌ Missing Int |

---

## 4. 総合テスト (Scenario & E2E / API横断フロー)
End-to-end validation of business workflows (e.g. entry -> discount -> cancel -> payment) acting via HTTP clients.

### 4.1 既存のテストケース (実装済)

| Test File | Coverage Target | Status |
|---|---|---|
| test_terminal.py | Tenant/Store/Terminal CRUD, Open/Close, Cash | ✅ 91% |

### 4.2 推奨・補充テストケース (巨大過付加・長期セッション等)

| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| - | - | No recommended scenario tests at the moment | - | - |

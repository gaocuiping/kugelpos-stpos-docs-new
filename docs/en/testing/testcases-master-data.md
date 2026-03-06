---
title: "Master Data サービス テストケース"
parent: Testing
grand_parent: English
nav_order: 13
layout: default
---

# Master Data サービス テスト設計書

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
| **MD-U-010** | `GET /items` | Valid JAN code search logic | Fields correctly parsed | ❌ Missing Unit |
| **MD-U-012** | `PUT /items` | Cache purge on price update logic | Purge invoked | ❌ Missing Unit |
| **MD-U-020** | `GET /taxes` | Tax date filtering logic | Only active tax filtered | ❌ Missing Unit |

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
| **MD-E-002** | `Integrity` | Network failure during Dapr state update | Self-healing triggers | ❌ Missing Int |

---

## 4. 総合テスト (Scenario & E2E / API横断フロー)
End-to-end validation of business workflows (e.g. entry -> discount -> cancel -> payment) acting via HTTP clients.

### 4.1 既存のテストケース (実装済)

| Test File | Coverage Target | Status |
|---|---|---|
| 複数ファイル | Staff/Category/Item/Payment/Settings CRUD operations | ⚠️ 63% |

### 4.2 推奨・補充テストケース (巨大過付加・長期セッション等)

| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| **MD-E-001** | `Performance` | Bulk refresh 100K records | Completes w/o OOM | ❌ Missing Scenario |

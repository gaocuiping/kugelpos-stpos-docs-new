---
title: "Report サービス テストケース"
parent: Testing
grand_parent: English
nav_order: 15
layout: default
---

# Report サービス テスト設計書

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
| test_journal_integration.py | Report aggregation logic (mocked) | ✅ Med |
| test_terminal_id_parsing.py | Terminal ID parsing | ✅ Med |

### 2.2 推奨・補充テストケース (不足分の強化対象)

| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| **RP-E-001** | `Boundary` | Leap year (Feb 29) aggregation logic | Feb 29 correctly aggregated | ❌ Missing Unit |
| **RP-E-002** | `Timezone` | Tx at 23:59:59 in UTC+9 | Aggregated into same day | ❌ Missing Unit |

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
| **RP-I-001** | `Report → Journal` | Z-report transmit via Pub/Sub | Message built correctly | ❌ Missing Int |

---

## 4. 総合テスト (Scenario & E2E / API横断フロー)
End-to-end validation of business workflows (e.g. entry -> discount -> cancel -> payment) acting via HTTP clients.

### 4.1 既存のテストケース (実装済)

| Test File | Coverage Target | Status |
|---|---|---|
| test_report.py | Sales report by Store/Terminal | ✅ High |
| test_category_report.py | Sales report by Category | ✅ High |
| test_item_report.py | Sales report by Item | ✅ High |
| test_payment_report_all.py | Sales report by Payment Method | ✅ High |
| test_cancelled_transactions.py | Aggregating Cancelled tx | ✅ High |
| test_void_transactions.py | Aggregating Void tx | ✅ High |
| test_return_transactions.py | Aggregating Return tx | ✅ High |
| test_split_payment_bug.py | Aggregating Split payments | ✅ High |
| test_critical_issue_78.py | Bug regression | ✅ High |
| test_issue_90_internal_tax_not_deducted.py | Inclusive tax regression | ✅ High |

### 4.2 推奨・補充テストケース (巨大過付加・長期セッション等)

| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| - | - | No recommended scenario tests at the moment | - | - |

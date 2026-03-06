---
title: "Cart サービス テストケース"
parent: Testing
grand_parent: English
nav_order: 14
layout: default
---

# Cart サービス テスト設計書

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
| test_calc_subtotal_logic.py | Subtotal calculation logic (Inclusive/Exclusive Tax) | ✅ High |
| test_tran_service_unit_simple.py | Pre-validation for Void/Return | ✅ Med |
| test_tran_service_status.py | Transaction status management | ✅ Med |
| test_terminal_cache.py | Terminal cache management | ✅ Med |
| test_text_helper.py | Text utility helpers | ✅ Med |
| repositories/test_item_master_grpc_repository.py | gRPC Repository | ✅ Med |
| utils/test_grpc_channel_helper.py | gRPC channel | ✅ Med |
| utils/test_dapr_statestore_session_helper.py | Dapr statestore | ✅ Med |

### 2.2 推奨・補充テストケース (不足分の強化対象)
| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| **CT-U-003** | `DELETE /entry/{id}` | Cancel part of cart item | Specific line deleted, subtotal recalculated | ❌ Missing Unit |
| **CT-U-011** | `tax_engine` | Multiple tax rates on a single item | Tax prorated and calculated correctly | ❌ Missing Unit |
| **CT-U-012** | `discount_engine` | Compound discounts (Item -100 & Cart -10%) | Applied in correct sequence | ❌ Missing Unit |
| **CT-U-013** | `calc_subtotal` | Discount results in negative subtotal | Handled as error or floored at 0 | ❌ Missing Unit |
| **CT-E-003** | `Security` | Send invalid discount rate (150%) | Validation 422 triggers | ❌ Missing Boundary |

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
| **CT-I-002** | `Cart → Dapr (Stock)` | Inventory deduction via Dapr Pub/Sub | Message correctly sent | ❌ Missing Int |
| **CT-I-003** | `Cart → Dapr (Journal)` | Journal generation via Dapr Pub/Sub | Message correctly sent | ❌ Missing Int |

---

## 4. 総合テスト (Scenario & E2E / API横断フロー)
End-to-end validation of business workflows (e.g. entry -> discount -> cancel -> payment) acting via HTTP clients.

### 4.1 既存のテストケース (実装済)
| Test File | Coverage Target | Status |
|---|---|---|
| test_cart.py | Normal sales, discounts, quantity | ✅ 86% |
| test_void_return.py | Void & Return flow | ✅ High |
| test_payment_cashless_error.py | Cashless error scenario | ⚠️ Partial |
| test_resume_item_entry.py | Resume item entry | ✅ Med |

### 4.2 推奨・補充テストケース (巨大過付加・長期セッション等)
| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| **CT-E-001** | `Boundary` | Qty = 9999 | Overflow prevented | ❌ Missing Scenario |
| **CT-E-002** | `State Ttl` | Cart idle for 72hr | Collected via TTL | ❌ Missing Scenario |

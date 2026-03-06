---
title: "Stock サービス テストケース"
parent: Testing
grand_parent: English
nav_order: 17
layout: default
---

# Stock サービス テスト設計書

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
| test_snapshot_scheduler.py | Snapshot Scheduler | ✅ Med |

### 2.2 推奨・補充テストケース (不足分の強化対象)
| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| **SK-U-013** | `Concurrency` | Concurrent deduction on same item | Atomic subtraction applied | ❌ Missing Unit |

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
| - | - | No recommended integration tests at the moment | - | - |

---

## 4. 総合テスト (Scenario & E2E / API横断フロー)
End-to-end validation of business workflows (e.g. entry -> discount -> cancel -> payment) acting via HTTP clients.

### 4.1 既存のテストケース (実装済)
| Test File | Coverage Target | Status |
|---|---|---|
| test_stock.py | Stock CRUD, tranlog reception, Snapshot | ✅ High |
| test_reorder_alerts.py | Reorder Alerts | ✅ High |
| test_snapshot_date_range.py | Snapshot boundary | ✅ High |
| test_snapshot_schedule_api.py | Schedule Management API | ✅ Med |
| test_websocket_alerts.py | WebSocket Notifications | ✅ Med |
| test_websocket_reorder_new.py | WebSocket new design | ✅ Med |

### 4.2 推奨・補充テストケース (巨大過付加・長期セッション等)
| ID | Target | Test Scenario | Expected Outcome | Status |
|---|---|---|---|---|
| **SK-E-001** | `Resilience` | WS disconnect during alert trigger | Queued & re-sent on connect | ❌ Missing Scenario |
| **SK-E-002** | `Concurrency` | 10 registers deduct stock=1 perfectly concurrently | 1 success, 9 failure replies | ❌ Missing Scenario |

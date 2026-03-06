---
title: "Stock Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 17
layout: default
---

# Stock Service Test Specification

Focuses on real-time inventory allocation and asynchronous WebSocket notifications for reorder alerts.

## 1. Overview and Test Strategy

Accurately manages inventory increments/decrements from Cart (purchases) and Admin Panel (receiving).
Crucially, tests behavior of real-time alerts (WebSocket) pushed to the frontend when inventory falls below appropriate levels.

---

## 2. Unit Tests (API & Logic)

### 2.1 Stock Adjustment & Concurrency Control

| ID | Target API | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|------------|---------------------------|------------------|--------|
| **SK-U-010** | `GET /stock/{item}` | Stock list retrieval across multiple warehouses/stores | Stock quantity for each location returned as array | ✅ Implemented |
| **SK-U-011** | `POST /stock/adjust`| Minus adjustment processing due to sales | Stock count decreased, stock history log appended | ✅ Implemented |
| **SK-U-012** | `Logic` | Negative Stock Allowed flag verification | If OFF, allocations dropping stock below 0 raise exception (400) and are blocked | ✅ Implemented |
| **SK-U-013** | `Concurrency` | Two concurrent allocation requests for same item (race condition) | Stock accurately adjusted via atomic operations | ❌ Recommended |

### 2.2 Alerts & WebSocket Notifications

| ID | Target Flow | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|-------------|---------------------------|------------------|--------|
| **SK-U-020** | `Reorder Logic` | Stock drops below "reorder point" after deduction | Reorder Alert flag on Database updated to True | ✅ Implemented |
| **SK-U-021** | `WebSocket` | Execute alert-triggering deduction while WS client connected | Alert message in JSON format pushed immediately to connected client | ✅ Implemented |
| **SK-U-022** | `WebSocket` | WebSocket connection attempt from unauthorized client without token | Connection rejected (Close/401) | ✅ Implemented |

## 3. Integration & Scheduled Tests

| ID | Component Integration | Scenario | Check Point | Status |
|----|-----------------------|----------|-------------|--------|
| **SK-I-001** | `CRON Scheduler` | Auto-generation of end-of-month "Inventory Snapshot" via Dapr CRON binding | Schedule trigger fires at designated time, stock counts copied to history table | ✅ Implemented |

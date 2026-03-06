---
title: "Terminal Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 12
layout: default
---

# Terminal Service Test Specification

This document details the test cases for the Terminal service, which manages the startup and configuration of POS registers.
Key areas include preventing terminal registration conflicts and monitoring operational status (heartbeat).

## 1. Overview and Test Strategy

**Prerequisites & Test Data**:
- **DB**: MongoDB `terminals` and `stores` collections
- **Cache**: Heartbeat management utilizing Dapr StateStore (Redis)

---

## 2. Unit Tests (API & Logic)

### 2.1 Terminal Registration & Management (Terminal CRUD)

| ID | Target API | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|------------|---------------------------|------------------|--------|
| **TM-U-010** | `POST /terminals` | New registration with unregistered MAC and Store ID | `201 Created`, initial settings saved to DB | ❌ Recommended |
| **TM-U-011** | `POST /terminals` | Registration attempt with MAC already bound to another store | `409 Conflict`, double registration blocked | ❌ Recommended |
| **TM-U-012** | `GET /terminals/{id}` | Fetch configuration for existing terminal ID | `200 OK`, configuration returned | ❌ Recommended |
| **TM-U-013** | `PUT /terminals/{id}` | Update terminal device settings | `200 OK`, DB updated and changes reflected | ❌ Recommended |

### 2.2 Heartbeat Monitoring

| ID | Target API | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|------------|---------------------------|------------------|--------|
| **TM-U-020** | `POST /heartbeat` | Periodic transmission from active terminal | `200 OK`, `last_active_at` updated in Redis | ❌ Recommended |
| **TM-U-021** | `GET /status` | Fetching terminal statuses from admin panel | Accurately returns Online/Offline based on last heartbeat | ❌ Recommended |

## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **TM-E-001** | `Resilience` | Dapr Redis connection failure (timeout) during `POST /heartbeat` | Does not crash; logs error and handles gracefully (e.g. `503 Service Unavailable` or degraded mode) | ❌ Recommended |
| **TM-E-002** | `Concurrency` | Sending "terminal initial registration" to the same store at the exact same millisecond | DB unique index/locking ensures only one succeeds, the other returns `409` | ❌ Recommended |

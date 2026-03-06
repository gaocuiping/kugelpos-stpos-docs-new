---
title: "Master Data Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 13
layout: default
---

# Master Data Service Test Specification

Focuses on master data integrity and rapid provisioning (caching) to other services (especially Cart).

## 1. Overview and Test Strategy

Manages static data fundamental to transactions: item prices, taxes, categories, and payment methods.
The most critical test point is **cache invalidation** upon master data updates.

---

## 2. Unit Tests (API & Logic)

### 2.1 Item Master

| ID | Target API | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|------------|---------------------------|------------------|--------|
| **MD-U-010** | `GET /items/{jan}` | Item lookup with existing JAN code | `200 OK`, correct price, tax class, and department returned | ❌ Recommended |
| **MD-U-011** | `GET /items/{jan}` | Invalid JAN code or deleted item | `404 Not Found` returned | ❌ Recommended |
| **MD-U-012** | `PUT /items/{jan}` | Item price revision (unit price update) | After DB update, cache entry in Dapr StateStore is deleted (invalidated) | ❌ Recommended |

### 2.2 Tax & Payment Master

| ID | Target Module | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|---------------|---------------------------|------------------|--------|
| **MD-U-020** | `GET /taxes` | Fetch list of currently valid tax rates (standard, reduced) | `200 OK`, returns only tax info within valid date ranges | ❌ Recommended |
| **MD-U-021** | `GET /payments` | Fetch available payment methods (Cash, CC, QR) | `200 OK`, returns valid payment methods based on store config | ❌ Recommended |

## 3. End-to-End Inter-System Scenarios

| ID | Scenario Flow (Cache Invalidation) | Expected Result & Assertions | Status |
|----|----------------------------------|------------------------------|--------|
| **MD-S-001** | **Immediate Master Reflection Flow** <br>1. Update Item A from 100 to 120 yen in MasterData<br>2. Scan Item A in Cart service | Cart cache is invalidated by MasterData update Pub/Sub event, scanned as 120 yen | ❌ Recommended |

## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **MD-E-001** | `Performance`| Bulk cache refresh batch execution for 100,000 item records | Completes within target time (e.g. 5 min) without causing memory leaks (OOM) | ❌ Recommended |
| **MD-E-002** | `Integrity` | Network error during saving to Cache (Dapr Redis) (Split-brain) | Distributed retry or Self-Healing functions correctly to prevent MongoDB-Redis data inconsistency | ❌ Recommended |

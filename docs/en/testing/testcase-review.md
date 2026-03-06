---
title: "Test Case Design Review & Improvements"
parent: Testing
grand_parent: English
nav_order: 18
layout: default
---

# Test Case Design Review & Improvements

This document contains the review results for the test case designs of each microservice, analyzing missing perspectives (edge cases, negative cases, and non-functional requirements).

## 1. Evaluation Summary

The initial test cases provided high coverage for happy-path business logic and basic error control.
However, it was identified that tests for **extreme loads (performance)**, **distributed system failures (network partitions)**, and **malicious inputs (security)** were lacking.

## 2. Shortcomings and Improvement Strategy per Service

We define the specific issues and requirements to be added for each service.

### 2.1 Account Service
- **Status**: Authentication flows and tenant management are covered.
- **Missing Perspectives**:
  - [Security] Rate limiting verification against brute-force attacks.
  - [Security] Prevention tests for JWT replay attacks.

### 2.2 Terminal Service
- **Status**: Basic CRUD and heartbeat operations using DB and Redis are good.
- **Missing Perspectives**:
  - [Fault Tolerance] Fallback behavior when Dapr StateStore (Redis) is down.
  - [Edge Case] Race conditions when multiple terminals concurrently access the same store within milliseconds.

### 2.3 Master Data Service
- **Status**: The approach to cache invalidation is appropriate.
- **Missing Perspectives**:
  - [Performance] Processing time and memory leak verification during bulk sync/cache updates of production-equivalent data (100,000 items).
  - [Negative Case] Preventing "split-brain" states where only the cache is updated but the DB fails.

### 2.4 Cart Service (Critical)
- **Status**: Strong coverage for complex tax, discount, and double-submission prevention logic.
- **Missing Perspectives**:
  - [Boundary] Tests for cart item limits (e.g., 9999 items) or total amount overflows (e.g., exceeding 100M yen).
  - [Non-functional/State] Verification of garbage collection/discarding for cart sessions abandoned for several days due to browser/terminal power drops mid-payment.

### 2.5 Report Service
- **Status**: Avoidance of Cartesian product bugs and complex aggregations are perfect.
- **Missing Perspectives**:
  - [Edge Case] Boundary testing for transactions occurring around midnight across different timezones (e.g., UTC vs JST) to ensure proper daily aggregation.
  - [Boundary] Monthly report aggregation tests during leap years (Feb 29).

### 2.6 Journal Service
- **Status**: Transaction type conversions are appropriately defined.
- **Missing Perspectives**:
  - [Performance/Security] Defensive programming tests to protect the DB when the Search API is hit with extreme pagination like `limit=10,000,000`.
  - [Negative Case] Processing of an extremely massive JSON payload (multi-MB receipt data).

### 2.7 Stock Service
- **Status**: Coordination between stock adjustment and WebSocket alerts is excellent.
- **Missing Perspectives**:
  - [Fault Tolerance] Verification of alert resending ("missed alerts") upon reconnection after a momentary network drop between the WebSocket server and client.
  - [Concurrency] Transaction lock verification when 10 registers simultaneously attempt to purchase the last 1 remaining item.

---

## 3. Action Plan

Based on the above analysis, a "**Section 4: Supplementary & Edge Cases**" has been appended to the end of each service's test specification (`testcases-*.md`) containing these specific, advanced test scenarios.

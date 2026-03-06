---
title: "Journal Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 16
layout: default
---

# Journal Service Test Specification

Aims to guarantee the persistence and search performance of "Electronic Journals" which carry legal requirements.

## 1. Overview and Test Strategy

Receives transaction completion events from Cart and settlement events from Report, saving them as immutable logs.
Tests focus primarily on preventing data loss (message lost countermeasures) and high-speed full-text/conditional search.

---

## 2. Unit Tests (Log Reception & Conversion)

| ID | Target Process | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|----------------|---------------------------|------------------|--------|
| **JN-U-010** | `Transaction Type` | Interpretation and saving of Normal Sales log | Status accurately mapped and saved to Journal DB | ✅ Implemented |
| **JN-U-011** | `Transaction Type` | Reception of Cancelled (immediate void) sales log | Transformed internally as a cancellation (negative transaction) and saved | ✅ Implemented |
| **JN-U-012** | `Search API` | Search parameters by Date Range and Terminal ID | Only matching logs returned with correct pagination | ❌ Recommended |
| **JN-U-013** | `Search API` | Search when no data exists within target period | Empty list and total pages 0 returned with `200 OK` | ❌ Recommended |

## 3. Integration Tests (Async & Messaging)

| ID | Component Flow | Scenario | Check Point | Status |
|----|----------------|----------|-------------|--------|
| **JN-I-001** | Pub/Sub Fault Tolerance | DB connection lost during message receiving thread | Transaction rolled back on DB error, Dapr performs retry | ✅ Implemented |
| **JN-I-002** | Elasticsearch Sync | Syncing to full-text search engine after saving journal to RDBMS | Free-word text search within transaction details returns hits | ❌ Recommended |

## 4. Supplementary & Edge Cases

| ID | Target | Scenario (Non-functional/Negative) | Expected Outcome | Status |
|----|--------|------------------------------------|------------------|--------|
| **JN-E-001** | `Security` | Requesting catastrophic pagination size via `GET /search?limit=10000000` | Defended at app-level; `400 Bad Request` or forced hard-limit (e.g. 100) applied | ❌ Recommended |
| **JN-E-002** | `Edge Case`| Receiving ultra-long receipt data > 5MB payload from message queue | Parses JSON without OOM, streams/saves appropriately to DB (or Blob) | ❌ Recommended |

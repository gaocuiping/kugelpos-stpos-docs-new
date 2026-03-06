---
title: "Report Service Test Cases"
parent: Testing
grand_parent: English
nav_order: 15
layout: default
---

# Report Service Test Specification

Test specifications aimed at complex aggregation logic and preventing Cartesian product bugs.

## 1. Overview and Test Strategy

Aggregates payment histories (Journal) to generate settlement and sales reports.
Already possesses extremely high coverage for calculation logic. Continuous monitoring of integrity is required.

---

## 2. Unit Tests (API & Logic)

### 2.1 Aggregation Engine Accuracy

| ID | Target Analysis | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|-----------------|---------------------------|------------------|--------|
| **RP-U-010** | `Category Report` | Aggregate sales by department (category) over period | Cancelled transactions accurately excluded from aggregation | ✅ Implemented |
| **RP-U-011** | `Item Report` | Aggregate sales quantity/amount for specific items | Negative amounts from return transactions correctly factored | ✅ Implemented |
| **RP-U-012** | `Payment Report`| Split payments (e.g., Cash + CC) | Amounts per payment method correctly prorated without double counting | ✅ Implemented |

### 2.2 Data Integrity & Edge Cases

| ID | Risk Area | Scenario (Before/When/Then) | Expected Outcome | Status |
|----|-----------|---------------------------|------------------|--------|
| **RP-U-020** | Integrity | Calculate "Total Payments == Total Sales + Total Tax" | The equation is always True without exception | ✅ Implemented |
| **RP-U-021** | Cartesian Bug | Slip with [Item A & Item B] × [3-way split payment] | No Cartesian product bug from SQL joins; only actual amounts aggregated | ✅ Implemented |
| **RP-U-022** | Rounding Error | Sub-yen rounding when calculating internal tax kickbacks | No multi-yen discrepancies based on legal rounding rules | ✅ Implemented |

## 3. Integration Tests

| ID | Component Integration | Scenario | Check Point | Status |
|----|-----------------------|----------|-------------|--------|
| **RP-I-001** | Report → Journal | Sending report to Journal upon Z-closing | Issued settlement report reliably ingested into E-Journal via Dapr Pub/Sub | ❌ Recommended |

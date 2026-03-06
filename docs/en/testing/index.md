---
title: "Testing"
parent: English
nav_order: 10
has_children: true
layout: default
---

# Testing

This section covers all test-related documentation for the Kugelpos POS Backend system.

## Documents

| Document | Description |
|----------|-------------|
| [Test Review](test-review.html) | Overall test review — current status, metrics, and improvement proposals |
| [Test Strategy](test-strategy.html) | Test strategy and policy across all services |
| [Unit Test Guide](unit-test-guide.html) | Guidelines for writing unit tests |
| [Integration Test Guide](integration-test-guide.html) | Guidelines for Dapr and inter-service integration tests |

## Test Coverage Summary

| Service | Unit Tests | Integration Tests | Scenario Tests |
|---------|-----------|------------------|---------------|
| Account | ✅ | ⚠️ Partial | ❌ |
| Terminal | ⚠️ Partial | ❌ | ❌ |
| Master-data | ⚠️ Partial | ❌ | ❌ |
| Cart | ✅ | ⚠️ Partial | ⚠️ Partial |
| Report | ✅ | ❌ | ❌ |
| Journal | ✅ | ❌ | ❌ |
| Stock | ✅ | ⚠️ Partial | ❌ |
| Commons | ✅ | N/A | N/A |

## Service Test Cases

| Document | Description |
|----------|-------------|
| [Account](testcases-account.html) | Account Service Test Cases |
| [Terminal](testcases-terminal.html) | Terminal Service Test Cases |
| [Master Data](testcases-master-data.html) | Master Data Service Test Cases |
| [Cart](testcases-cart.html) | Cart Service Test Cases |
| [Report](testcases-report.html) | Report Service Test Cases |
| [Journal](testcases-journal.html) | Journal Service Test Cases |
| [Stock](testcases-stock.html) | Stock Service Test Cases |

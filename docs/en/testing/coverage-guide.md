---
title: "Test Coverage Guidelines"
parent: Testing
grand_parent: English
nav_order: 5
layout: default
---

# Test Coverage Guidelines

To ensure the high reliability and stability of the Kugelpos POS Backend, we enforce strict minimum test coverage requirements across all microservices.

## 1. Coverage Target: 85% Minimum

**The absolute minimum acceptable test coverage for any service codebase is 85%.**

This metric applies specifically to **Line Coverage** and **Branch Coverage** within the core business logic (services, use cases, models, and utility functions).

### 1.1 Why 85%?
An 85% coverage rate provides a strong safety net against regressions without falling into the diminishing returns of chasing 100% coverage (which often leads to brittle, low-value tests for boilerplate code).

- **< 70%**: High risk of undetected bugs, especially in edge cases. Unacceptable for production.
- **70% - 84%**: Acceptable for initial development of new, non-critical features, but blocking for production release.
- **85%+**: The required standard. Indicates robust testing of both happy paths and identified negative/edge cases.

## 2. Coverage Enforcement in CI/CD

The 85% requirement is automatically enforced via our GitHub Actions pipeline (`pytest-cov`).

1. **Pull Request Validation**: Any PR that drops the overall coverage below 85%, or introduces new files with less than 85% coverage, will fail the CI check.
2. **Coverage Reports**: Detailed `coverage.xml` reports are generated on every build. These can be visualized in the PR comments or SonarQube.

## 3. Strategies to Achieve and Maintain 85%

If a service is currently below the 85% threshold, use the following strategies:

1. **Focus on Branches, Not Just Lines**: Ensure you are testing both the `if` and `else` conditions, especially for error handling (`try/except` blocks).
2. **Parameterize Tests**: `pytest.mark.parametrize` is the most efficient way to achieve high coverage over different inputs (boundary values, null checks) with minimal code.
3. **Mock I/O Aggressively**: Low coverage often stems from hard-to-reach database or external API failure states. Use `unittest.mock` to simulate these failures.
4. **Exclude Boilerplate (Pragmatically)**: Use `.coveragerc` to exclude purely declarative code (e.g., Pydantic model definitions without custom logic, or configuration constants) if they unfairly drag down the coverage percentage without adding risk.

### 3.1 Example `pytest.ini` Configuration

```ini
[pytest]
addopts = --cov=app --cov-report=term-missing --cov-fail-under=85
```

#!/bin/bash
export PIPENV_IGNORE_VIRTUALENVS=1


test_files=(
    "tests/scenario/test_clean_data.py"
    "tests/scenario/test_setup_data.py"
    "tests/scenario/test_health.py"
    "tests/scenario/test_report.py"
    "tests/scenario/test_tax_display.py"
    "tests/scenario/test_category_report.py"
    "tests/scenario/test_item_report.py"
    "tests/scenario/test_payment_report_all.py"
    "tests/scenario/test_flash_date_range_validation.py"
    "tests/scenario/test_critical_issue_78.py"  # Issue #78 critical bug verification
    "tests/scenario/test_comprehensive_aggregation.py"  # Comprehensive aggregation tests
    "tests/scenario/test_data_integrity.py"  # Data integrity tests
    "tests/scenario/test_return_transactions.py"  # Return transaction tests
    "tests/scenario/test_void_transactions.py"  # Void transaction tests
    "tests/scenario/test_edge_cases.py"  # Edge case tests (empty arrays, rounding, etc.)
    "tests/scenario/test_cancelled_transactions.py"  # Cancelled transaction handling tests
    "tests/scenario/test_split_payment_bug.py"  # Run last to avoid affecting other tests
)

for test_file in "${test_files[@]}"; do
    ~/.local/bin/pipenv run pytest "$test_file"
done

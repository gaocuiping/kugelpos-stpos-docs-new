#!/bin/bash
export PIPENV_IGNORE_VIRTUALENVS=1

for test_file in \
    tests/scenario/test_clean_data.py \
    tests/scenario/test_setup_data.py \
    tests/scenario/test_health.py \
    tests/scenario/test_operations.py \
    tests/scenario/test_isolation.py \
    tests/unit/test_account_logic.py \
    tests/unit/test_auth_logic.py
do
    ~/.local/bin/pipenv run pytest $test_file -s -v
done

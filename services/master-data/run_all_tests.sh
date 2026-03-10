#!/bin/bash
export PIPENV_IGNORE_VIRTUALENVS=1


tests=(
    "tests/scenario/test_clean_data.py"
    "tests/scenario/test_setup_data.py"
    "tests/scenario/test_health.py"
    "tests/scenario/test_operations.py"
)

for test in "${tests[@]}"; do
    ~/.local/bin/pipenv run pytest "$test"
done

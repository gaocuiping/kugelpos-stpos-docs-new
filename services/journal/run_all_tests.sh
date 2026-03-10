#!/bin/bash
export PIPENV_IGNORE_VIRTUALENVS=1


test_files=(
    "tests/scenario/test_clean_data.py" #HACK: Commented out to avoid running this test
    "tests/scenario/test_setup_data.py"
    "tests/scenario/test_health.py"
    "tests/scenario/test_journal.py"
)

for test_file in "${test_files[@]}"; do
    ~/.local/bin/pipenv run pytest "$test_file"
done

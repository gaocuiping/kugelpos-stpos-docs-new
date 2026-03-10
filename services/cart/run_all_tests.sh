#!/bin/bash
export PIPENV_IGNORE_VIRTUALENVS=1

# ── 単元テスト（外部サービス不要）────────────────────────────
for test_file in \
    tests/unit/test_transaction_status_repository.py \
    tests/unit/test_tran_service_status.py \
    tests/unit/test_tran_service_unit.py \
    tests/unit/test_tran_service_unit_simple.py \
    tests/unit/test_calc_subtotal_logic.py \
    tests/unit/test_terminal_cache.py \
    tests/unit/test_text_helper.py
do
    ~/.local/bin/pipenv run pytest $test_file
done

# ── シナリオテスト（外部サービス必要・順序依存あり）──────────
for test_file in \
    tests/scenario/test_clean_data.py \
    tests/scenario/test_setup_data.py \
    tests/scenario/test_health.py \
    tests/scenario/test_cart.py \
    tests/scenario/test_void_return.py \
    tests/scenario/test_payment_cashless_error.py \
    tests/scenario/test_resume_item_entry.py
do
    ~/.local/bin/pipenv run pytest $test_file
done

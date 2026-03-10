"""
reorganize_all_services_tests.py
把各服务 tests/ 下的文件按单元/场景分类移动到 unit/ 和 scenario/ 子目录。
对 terminal / master-data 这类已有空子目录的服务，只移动根目录残余文件。
"""
import os
import shutil

BASE = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/services"

# ── 各服务的分类规则 ─────────────────────────────────────────
# 格式:  service -> {"unit": [...], "scenario": [...]}
# 没有明确列出的文件：
#   - test_setup_data.py / test_clean_data.py / test_health.py → scenario
#   - 含 "unit" 或 "logic" 或 "service" 的文件名 → unit
#   - 其余以 test_ 开头 → scenario（默认）
SERVICES_RULES = {
    "account": {
        "unit":     [],
        "scenario": ["test_operations.py", "test_health.py",
                     "test_setup_data.py", "test_clean_data.py"],
    },
    "terminal": {
        "unit":     [],
        "scenario": ["test_terminal.py", "test_health.py",
                     "test_setup_data.py", "test_clean_data.py"],
    },
    "master-data": {
        "unit":     [],
        "scenario": ["test_operations.py", "test_health.py",
                     "test_setup_data.py", "test_clean_data.py"],
    },
    "report": {
        "unit":     [],
        "scenario": [
            "test_report.py", "test_cancelled_transactions.py",
            "test_category_report.py", "test_comprehensive_aggregation.py",
            "test_critical_issue_78.py", "test_data_integrity.py",
            "test_edge_cases.py", "test_flash_date_range_validation.py",
            "test_item_report.py", "test_journal_integration.py",
            "test_journal_integration_simple.py", "test_payment_report_all.py",
            "test_return_transactions.py", "test_split_payment_bug.py",
            "test_tax_display.py", "test_void_transactions.py",
            "test_health.py", "test_setup_data.py", "test_clean_data.py",
        ],
    },
    "stock": {
        "unit":     [],
        "scenario": [
            "test_stock.py", "test_reorder_alerts.py",
            "test_snapshot_date_range.py", "test_snapshot_schedule_api.py",
            "test_snapshot_scheduler.py", "test_websocket_alerts.py",
            "test_websocket_reorder_new.py",
            "test_health.py", "test_setup_data.py", "test_clean_data.py",
        ],
    },
    "journal": {
        # test_log_service.py は mock 使用の可能性 → unit 候補
        "unit":     ["test_log_service.py", "test_transaction_type_conversion.py"],
        "scenario": [
            "test_journal.py", "test_health.py",
            "test_setup_data.py", "test_clean_data.py",
        ],
    },
}


def ensure_subdir(path: str):
    os.makedirs(path, exist_ok=True)
    init = os.path.join(path, "__init__.py")
    if not os.path.exists(init):
        open(init, "w").close()


def move(src: str, dst_dir: str, label: str):
    if not os.path.exists(src):
        return
    dst = os.path.join(dst_dir, os.path.basename(src))
    if os.path.exists(dst):
        print(f"  [SKIP ] 既存: {os.path.basename(src)} (in {os.path.basename(dst_dir)}/)")
        return
    shutil.move(src, dst)
    print(f"  [{label}] {os.path.basename(src)} → {os.path.basename(dst_dir)}/")


def reorganize_service(svc: str, rules: dict):
    tests_dir = os.path.join(BASE, svc, "tests")
    if not os.path.isdir(tests_dir):
        print(f"\n[SKIP ] {svc}: tests/ ディレクトリが見つかりません")
        return

    unit_dir     = os.path.join(tests_dir, "unit")
    scenario_dir = os.path.join(tests_dir, "scenario")
    ensure_subdir(unit_dir)
    ensure_subdir(scenario_dir)

    print(f"\n{'='*55}")
    print(f"  サービス: {svc}")
    print(f"{'='*55}")

    unit_files     = set(rules.get("unit", []))
    scenario_files = set(rules.get("scenario", []))

    for fname in sorted(os.listdir(tests_dir)):
        fpath = os.path.join(tests_dir, fname)
        if not os.path.isfile(fpath):
            continue
        if not fname.startswith("test_") or not fname.endswith(".py"):
            continue  # conftest.py / __init__.py / log_maker.py など除外

        if fname in unit_files:
            move(fpath, unit_dir, "UNIT  ")
        elif fname in scenario_files:
            move(fpath, scenario_dir, "SCEN  ")
        else:
            # デフォルト: scenario に
            move(fpath, scenario_dir, "SCEN* ")

    print(f"  unit/     : {len(os.listdir(unit_dir))} 項目")
    print(f"  scenario/ : {len(os.listdir(scenario_dir))} 項目")


def main():
    print("全サービステスト再編成 開始...\n")
    for svc, rules in SERVICES_RULES.items():
        reorganize_service(svc, rules)
    print("\n\n完了！ 次は auto_append_tests.py --all を実行します。")


if __name__ == "__main__":
    main()

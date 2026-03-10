"""
reorganize_cart_tests.py
把 services/cart/tests/ 下的测试文件
按类型移动到 unit/ 和 scenario/ 子目录。
"""
import os
import shutil

TESTS_DIR = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/services/cart/tests"

# ── 单元测试（不依赖外部服务，使用 Mock）──────────────────────
UNIT_FILES = [
    "test_calc_subtotal_logic.py",
    "test_tran_service_unit.py",
    "test_tran_service_unit_simple.py",
    "test_tran_service_status.py",
    "test_terminal_cache.py",
    "test_text_helper.py",
    "test_transaction_status_repository.py",
]

# ── 场景/综合测试（通过 HTTP 请求真实服务）───────────────────
SCENARIO_FILES = [
    "test_cart.py",
    "test_void_return.py",
    "test_payment_cashless_error.py",
    "test_resume_item_entry.py",
    "test_health.py",
    "test_setup_data.py",
    "test_clean_data.py",
]


def move(src, dst_dir, label):
    if os.path.exists(src):
        dst = os.path.join(dst_dir, os.path.basename(src))
        shutil.move(src, dst)
        print(f"  [{label}] {os.path.basename(src)}")
    else:
        print(f"  [SKIP ] {os.path.basename(src)} (不存在，跳过)")


def main():
    unit_dir     = os.path.join(TESTS_DIR, "unit")
    scenario_dir = os.path.join(TESTS_DIR, "scenario")

    os.makedirs(unit_dir,     exist_ok=True)
    os.makedirs(scenario_dir, exist_ok=True)

    # __init__.py（pytest 子目录识别用）
    for d in [unit_dir, scenario_dir]:
        p = os.path.join(d, "__init__.py")
        if not os.path.exists(p):
            open(p, "w").close()

    print("\n── 单元测试 → unit/ ───────────────────────")
    for f in UNIT_FILES:
        move(os.path.join(TESTS_DIR, f), unit_dir, "UNIT")

    # _unit_auto.py も unit/ へ
    for f in os.listdir(TESTS_DIR):
        if f.endswith("_unit_auto.py"):
            move(os.path.join(TESTS_DIR, f), unit_dir, "UNIT")

    # repositories/ と utils/ サブディレクトリを unit/ へ
    for sub in ["repositories", "utils"]:
        src = os.path.join(TESTS_DIR, sub)
        dst = os.path.join(unit_dir, sub)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.move(src, dst)
            print(f"  [UNIT ] {sub}/")

    print("\n── 场景测试 → scenario/ ──────────────────")
    for f in SCENARIO_FILES:
        move(os.path.join(TESTS_DIR, f), scenario_dir, "SCEN")

    # _scenario_auto.py も scenario/ へ
    for f in os.listdir(TESTS_DIR):
        if f.endswith("_scenario_auto.py"):
            move(os.path.join(TESTS_DIR, f), scenario_dir, "SCEN")

    print("\n── 完成 ──────────────────────────────────")
    print(f"  unit/     : {len(os.listdir(unit_dir))} 项")
    print(f"  scenario/ : {len(os.listdir(scenario_dir))} 项")
    print()
    print("  tests/ 剩余文件:")
    remaining = [f for f in os.listdir(TESTS_DIR)
                 if os.path.isfile(os.path.join(TESTS_DIR, f))]
    for f in remaining:
        print(f"    {f}")


if __name__ == "__main__":
    main()

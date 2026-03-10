"""
fix_chinese_in_ja_docs.py
把 docs/ja/testing/testcases-*.md 中混入的中文替换为日语。
"""
import os

TESTING_DIR = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs/ja/testing"

# 替换映射表：中文 → 日語
REPLACEMENTS = [
    # ── 通用自动追加说明 ─────────────────────────────────
    ("系统自动追加的代码接口测试",         "システムが自動追加したAPIインターフェーステスト"),
    ("系统が自动追加した",               "システムが自動追加した"),
    ("APIインターフェース测试",           "APIインターフェーステスト"),
    ("⚠️ 代码接口已变更：",             "⚠️ コードインターフェースが変更されました："),
    ("⚠️ 代码接口已变更",              "⚠️ コードインターフェースが変更されました"),

    # ── testcases-cart.md 的中文期待値 ────────────────────
    ("保存前后的对象属性一致。",          "保存前後のオブジェクト属性が一致すること。"),
    ("通信成功且二次请求使用缓存。",       "通信が成功し、2回目のリクエストはキャッシュを使用すること。"),
    ("`transaction_completed` 消息正确发送。", "`transaction_completed` メッセージが正しく送信されること。"),

    # ── testcases-*.md の表頭「备注」→「備考」 ─────────────
    ("备注 (Notes)",                  "備考 (Notes)"),

    # ── testcases-terminal.md ────────────────────────────
    ("結合测试",                      "結合テスト"),
    ("自动化同步脚本在扫描 Terminal 服务代码时，将重点匹配 `test_terminal.py` 中的子步骤注释。",
     "自動同期スクリプトが Terminal サービスのコードをスキャンする際、`test_terminal.py` のサブステップコメントを優先的にマッチングします。"),

    # ── testcases-stock.md ───────────────────────────────
    ("文档现已覆盖 Stock 服务相关的 11 个测试文件，单体测试层级的 GAP 已作为后续优先补全项。",
     "このドキュメントは Stock サービス関連の 11 個のテストファイルをカバーしています。単体テスト層のギャップは今後の優先補完項目として記録されています。"),

    # ── testcases-cart.md 末尾の NOTE ────────────────────
    ("自动化同步脚本在扫描代码时，会优先识别这些 Helper 函数的存在，以确保测试环境初始化逻辑的鲁棒性。",
     "自動同期スクリプトがコードをスキャンする際、これらのHelper関数の存在を優先的に識別し、テスト環境初期化ロジックの堅牢性を確保します。"),
]


def fix_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    for zh, ja in REPLACEMENTS:
        content = content.replace(zh, ja)

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  [FIXED] {os.path.basename(path)}")
    else:
        print(f"  [OK   ] {os.path.basename(path)} — 変更なし")


def main():
    print(f"\n日语文档中文修复开始...\n")
    for fname in sorted(os.listdir(TESTING_DIR)):
        if fname.startswith("testcases-") and fname.endswith(".md"):
            fix_file(os.path.join(TESTING_DIR, fname))
    print("\n完了！")


if __name__ == "__main__":
    main()

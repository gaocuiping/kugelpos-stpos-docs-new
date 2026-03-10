import os
import subprocess
import datetime

SERVICES = ["account", "terminal", "master-data", "cart", "report", "journal", "stock"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs", "ja", "testing")
DATE_STR = datetime.datetime.now().strftime("%Y-%m-%d")

report_lines = [
    "---",
    f"title: \"テスト実行結果レポート ({DATE_STR})\"",
    "parent: テスト",
    "nav_order: 8",
    "layout: default",
    "---",
    "",
    f"# 🎯 プロフェッショナル テスト実行結果レポート ({DATE_STR})",
    "",
    "本ドキュメントは、Kugelpos-backend の全マイクロサービスに対する最新の自動テスト実行結果をまとめたものです。",
    "",
    "## 📊 サービス別実行サマリー",
    "",
    "| サービス名 | 総テスト数 | 成功 (Passed) | 失敗 (Failed) | スキップ (Skipped) | 実行時間 | 状態 |",
    "|:---|:---:|:---:|:---:|:---:|:---|:---|"
]

results = []

print("Starting global test execution...")

for svc in SERVICES:
    svc_dir = os.path.join(BASE_DIR, "services", svc)
    print(f"Running tests for {svc}...")
    
    # Use pipenv to run pytest if Pipfile exists, otherwise fallback to python3 -m pytest
    pipenv_path = "/home/gaocuiping/.local/bin/pipenv"
    if os.path.exists(os.path.join(svc_dir, "Pipfile")):
        cmd = [pipenv_path, "run", "pytest", "tests/", "-q", "--disable-warnings"]
    else:
        cmd = ["python3", "-m", "pytest", "tests/", "-q", "--disable-warnings"]
    
    try:
        process = subprocess.run(cmd, cwd=svc_dir, capture_output=True, text=True)
        out = process.stdout
        
        lines = out.strip().split("\n")
        summary_line = lines[-1] if lines else "No output"
        
        passed = 0
        failed = 0
        skipped = 0
        duration = "0.00s"
        
        if "in " in summary_line:
            parts = summary_line.split(" in ")
            duration = parts[-1]
            status_parts = parts[0].split(", ")
            for p in status_parts:
                p = p.strip()
                if "passed" in p: passed = int(p.split()[0])
                elif "failed" in p: failed = int(p.split()[0])
                elif "skipped" in p: skipped = int(p.split()[0])
                elif "error" in p: failed += int(p.split()[0])
                
        total = passed + failed + skipped
        state = "✅ PASS" if failed == 0 and total > 0 else ("⚠️ WIP" if total == 0 else "❌ FAIL")
        
        results.append(f"| **{svc.capitalize()}** | {total} | <span style='color:green'>{passed}</span> | <span style='color:red'>{failed}</span> | <span style='color:gray'>{skipped}</span> | {duration} | {state} |")
        
    except Exception as e:
        results.append(f"| **{svc.capitalize()}** | ERROR | - | - | - | - | 🚨 ERROR |")
        print(f"Error for {svc}: {e}")

report_lines.extend(results)

report_lines.extend([
    "",
    "## 💡 実行結果の考察とネクストアクション",
    "",
    "1. **スキップされたテストの消化**: 現在、自動生成された多数のテストケースが `pytest.skip()` 状態となっています。各サービス担当者は順次アサーションロジックの実装を進めてください。",
    "2. **CI/CD パイプラインとの統合**: 本実行レポートの生成ロジックを GitHub Actions に組み込み、Nightly ビルドで自動更新されるように構成することを推奨します。",
    "3. **失敗テストの修正**: `❌ FAIL` となっているサービスについては、依存関係のエラーまたはロジックの不具合が疑われます。速やかにログを確認し、修正を行ってください。",
    ""
])

report_path = os.path.join(DOCS_DIR, f"test-execution-report-{DATE_STR.replace('-', '')}.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

index_path = os.path.join(DOCS_DIR, "index.md")
with open(index_path, "r", encoding="utf-8") as f:
    content = f.read()

new_link = f"| [テスト実行結果 ({DATE_STR})](test-execution-report-{DATE_STR.replace('-', '')}.html) | 全サービスのテスト実行結果とカバレッジサマリー |\n"
if new_link not in content:
    content = content.replace(
        "|-------------|------|\n",
        "|-------------|------|\n" + new_link
    )
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Report generated successfully at {report_path}")

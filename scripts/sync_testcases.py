import os
import ast
import re

print("Starting Professional Docs-as-Code synchronization...")

# Configuration for the new environment
BASE_DIR = "/home/gaocuiping/myself/kugelpos-stpos-docs-new"
docs_dir = os.path.join(BASE_DIR, "docs")
services_dir = os.path.join(BASE_DIR, "services")

# Regex for status badges
MISSING_BADGE = r'!\[Missing\]\(https://img\.shields\.io/badge/Status-Missing-red\)'
IMPLEMENTED_BADGE = '![Implemented](https://img.shields.io/badge/Status-Implemented-green)'

# 1. Component: Code Scanner
# Focus on extracting function names and relevant comments from test files
implemented_functions = set()
implemented_comments = set()

def _has_pytest_skip(func_node) -> bool:
    """
    函数体内是否含有 pytest.skip() 调用。
    自动生成的骨架文件里会有 pytest.skip(...)，视为"未实现"。
    接受 ast.FunctionDef 或 ast.AsyncFunctionDef。
    """
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            func = node.func
            # pytest.skip(...)
            if isinstance(func, ast.Attribute):
                val = func.value
                if isinstance(val, ast.Name) and val.id == "pytest" and func.attr == "skip":
                    return True
            # skip(...) —— 直接 from pytest import skip 的情况
            if isinstance(func, ast.Name) and func.id == "skip":
                return True
    return False


def scan_test_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = "".join(lines)
            
            # Extract basic function/method names using AST
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # ── 新增：跳过含有 pytest.skip() 的函数 ──────────────
                    # 这表示该测试是自动生成的骨架，尚未真正实现
                    if node.name.startswith("test_") and _has_pytest_skip(node):
                        continue  # 不计入 implemented_functions
                    implemented_functions.add(node.name)
            
            # Extract comments (especially those following '#' in the doc cases)
            for line in lines:
                match = re.search(r'#\s*(.*)', line)
                if match:
                    implemented_comments.add(match.group(1).strip())
                    
    except Exception as e:
        print(f"Failed to scan {file_path}: {e}")

print("Scanning services directory for implementation proof...")
scan_count = 0
for root, dirs, files in os.walk(services_dir):
    if 'tests' in root.split(os.sep):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                scan_test_file(os.path.join(root, file))
                scan_count += 1

print(f"Scanned {scan_count} test files.")
print(f"Captured {len(implemented_functions)} functions and {len(implemented_comments)} comments.")

# 2. Component: Markdown Updater
# Update tables based on "Matching Rules" (匹配规则) column
def update_professional_doc(file_path):
    if not os.path.exists(file_path):
        return False

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    header_indices = {}

    for line in lines:
        stripped = line.strip()
        
        # Detect table headers to find column indices
        if stripped.startswith('|') and ('ID' in stripped):
            parts = [p.strip() for p in stripped.split('|')]
            for i, part in enumerate(parts):
                if not part: continue
                # Match Japanese or English headers
                if 'ID' in part.upper(): header_indices['id'] = i
                elif '状态' in part or 'Status' in part: header_indices['status'] = i
                elif any(word in part for word in ['匹配规则', 'Matching', 'Mapping', 'Function']): 
                    header_indices['rules'] = i

        # Process data rows with Missing status
        if stripped.startswith('|') and re.search(MISSING_BADGE, line):
            parts = line.split('|')
            if 'rules' in header_indices and 'status' in header_indices:
                idx_rules = header_indices['rules']
                idx_status = header_indices['status']
                
                # Extract rules (function names or comment fragments)
                # Supports multiple entries like `test_func` <br> `comment text`
                rule_text = parts[idx_rules].replace('`', '').replace('<br>', '\n')
                rules = [r.strip() for r in rule_text.split('\n') if r.strip()]
                
                is_implemented = False
                for rule in rules:
                    # Clean rule from specific markers if any
                    clean_rule = rule.replace('*(待追加：', '').replace(')*', '').strip()
                    if not clean_rule: continue
                    
                    # Match against code
                    if clean_rule in implemented_functions:
                        is_implemented = True
                        break
                    
                    if clean_rule in implemented_comments:
                        is_implemented = True
                        break
                    
                    # Fuzzy match for comments (partially contained)
                    for comment in implemented_comments:
                        if clean_rule and clean_rule in comment:
                            is_implemented = True
                            break
                    if is_implemented: break
                
                if is_implemented:
                    parts[idx_status] = f" {IMPLEMENTED_BADGE} "
                    line = '|'.join(parts)
                    updated = True

        new_lines.append(line)

    if updated:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

# Main synchronization loop
print("Updating professional test case documents...")
update_count = 0
ja_docs_path = os.path.join(docs_dir, "ja", "testing")
if os.path.exists(ja_docs_path):
    for filename in os.listdir(ja_docs_path):
        if filename.startswith("testcases-") and filename.endswith(".md"):
            if update_professional_doc(os.path.join(ja_docs_path, filename)):
                update_count += 1

print(f"\nFinal Summary:")
print(f"Total documents updated: {update_count}")
print("Synchronization process completed.")

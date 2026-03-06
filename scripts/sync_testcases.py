import os
import ast
import re

print("Starting Docs-as-Code synchronization process...")

docs_dir = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs"
services_dir = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/services"

# 1. Parse AST to find implemented Test Case IDs
implemented_test_ids = set()

def scan_test_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
            
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    # Look for @TestCaseID: XX-X-000
                    match = re.search(r'@TestCaseID:\s*([A-Za-z0-9-]+)', docstring)
                    if match:
                        implemented_test_ids.add(match.group(1).upper())
    except Exception as e:
        print(f"Failed to parse {file_path}: {e}")

print("Scanning for test files...")
count = 0
if os.path.exists(services_dir):
    for root, dirs, files in os.walk(services_dir):
        if 'tests' in root.split(os.sep):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    scan_test_file(os.path.join(root, file))
                    count += 1
else:
    print(f"Warning: Services directory {services_dir} not found.")

print(f"Scanned {count} test files. Found {len(implemented_test_ids)} implemented TestCaseIDs: {implemented_test_ids}")

# 2. Update Markdown Tables
def update_markdown(file_path, lang):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    
    # We look for markdown table rows that start with | and might contain the ID.
    # Ex: | **CT-U-012** | ... | ❌ 補充(単体) |
    
    for line in lines:
        if line.strip().startswith('|') and '❌' in line:
            # Check if this line contains one of the implemented IDs
            for test_id in implemented_test_ids:
                if f"**{test_id}**" in line or f"`{test_id}`" in line or test_id in line.split('|')[1]:
                    # Build the updated status
                    status_str = "✅ 実装済" if lang == 'ja' else "✅ Implemented"
                    
                    # Split line into parts
                    parts = line.split('|')
                    if len(parts) > 2:
                        # Replace the last cell (status)
                        old_status = parts[-2]
                        parts[-2] = f" {status_str} "
                        line = '|'.join(parts)
                        modified = True
                        print(f"Updated {test_id} to implemented in {os.path.basename(file_path)}")
        new_lines.append(line)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

update_count = 0
for lang in ['ja', 'en']:
    test_docs_dir = os.path.join(docs_dir, lang, 'testing')
    if os.path.exists(test_docs_dir):
        for file in os.listdir(test_docs_dir):
            if file.startswith('testcases-') and file.endswith('.md'):
                if update_markdown(os.path.join(test_docs_dir, file), lang):
                    update_count += 1

print(f"Synchronization complete. Updated {update_count} document files.")

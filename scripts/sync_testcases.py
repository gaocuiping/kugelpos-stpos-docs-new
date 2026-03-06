import os
import ast
import re

print("Starting Docs-as-Code synchronization process...")

docs_dir = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs"
services_dir = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/services"

# 1. Parse AST to find implemented Test Case IDs and Scenario Descriptions
implemented_test_ids = set()
implemented_scenarios = set()

def scan_test_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = "".join(lines)
            tree = ast.parse(content)
            
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                func_name = node.name
                implemented_scenarios.add(func_name) # Always add function name
                
                # Method 1: Look for explicit @TestCaseID: XX-X-000 or scenario in Docstring
                docstring = ast.get_docstring(node)
                if docstring:
                    match = re.search(r'@TestCaseID:\s*([A-Za-z0-9-]+)', docstring)
                    if match:
                        implemented_test_ids.add(match.group(1).upper())
                    
                    first_line = docstring.strip().split('\n')[0].strip()
                    if first_line:
                        implemented_scenarios.add(first_line)
                
                # Method 2: Look for comments immediately above the function
                idx = node.lineno - 2 # 0-indexed, and line before lineno
                while idx >= 0:
                    line = lines[idx].strip()
                    if line.startswith('#'):
                        comment = line.lstrip('#').strip()
                        if comment and not comment.startswith('pytest'): # Ignore pytest markers
                            implemented_scenarios.add(comment)
                        idx -= 1
                    elif line.startswith('@'): # Skip decorators
                        idx -= 1
                    else:
                        break
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

print(f"Scanned {count} test files.")
print(f"Found {len(implemented_test_ids)} explicit TestCaseIDs.")
print(f"Found {len(implemented_scenarios)} scenario descriptions.")

# 2. Update Markdown Tables
def update_markdown(file_path, lang):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    new_lines = []
    header_indices = {}
    
    for line in lines:
        stripped_line = line.strip()
        
        # Identify table header to find column indices
        if stripped_line.startswith('|') and ('ID' in stripped_line or 'ID' in stripped_line.upper()):
            parts = [p.strip() for p in stripped_line.split('|')]
            for i, part in enumerate(parts):
                if not part: continue
                if 'ID' in part.upper(): header_indices['id'] = i
                elif 'ターゲット' in part or 'Target' in part: header_indices['target'] = i
                elif 'テストシナリオ' in part or 'Scenario' in part: header_indices['scenario'] = i
                elif '状態' in part or 'Status' in part: header_indices['status'] = i

        if stripped_line.startswith('|') and '❌' in line:
            parts = line.split('|')
            # Minimum required columns: ID, Target, Scenario, Status
            if len(parts) > 4 and 'status' in header_indices:
                idx_id = header_indices.get('id', 1)
                idx_target = header_indices.get('target', 2)
                idx_scenario = header_indices.get('scenario', 3)
                idx_status = header_indices['status']

                row_id = parts[idx_id].replace('*', '').replace('`', '').strip().upper()
                row_target = parts[idx_target].replace('*', '').replace('`', '').strip()
                row_scenario = parts[idx_scenario].replace('*', '').replace('`', '').strip()
                
                is_matched = False
                # 1. Check ID match
                if row_id and row_id in implemented_test_ids:
                    is_matched = True
                    print(f"Matched by ID: {row_id} in {os.path.basename(file_path)}")
                
                # 2. Check Scenario or Target match
                if not is_matched:
                    for key in implemented_scenarios:
                        if key == row_target or key in row_target or row_target in key:
                            is_matched = True
                            print(f"Matched by Target key: '{key}' (matches '{row_target}')")
                            break
                        if key == row_scenario or key in row_scenario or row_scenario in key:
                            is_matched = True
                            print(f"Matched by Scenario key: '{key}' (matches '{row_scenario}')")
                            break
                
                if is_matched:
                    status_str = "✅ 実装済" if lang == 'ja' else "✅ Implemented"
                    # Handle " ❌ 補充(単体) " style status preservation if needed, or overwrite
                    parts[idx_status] = f" {status_str} "
                    line = '|'.join(parts)
                    modified = True
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

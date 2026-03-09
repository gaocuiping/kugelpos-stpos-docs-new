import os
import re

# Configurations
PROJECT_ROOT = "/home/gaocuiping/myself/kugelpos-stpos-docs-new"
JA_TESTING_DIR = os.path.join(PROJECT_ROOT, "docs/ja/testing")

# Service Configuration Mapping
SERVICES_CONFIG = {
    "account": {"api": "services/account/app/api/v1", "doc": "testcases-account.md", "id": "AC"},
    "cart": {"api": "services/cart/app/api/v1", "doc": "testcases-cart.md", "id": "CT"},
    "journal": {"api": "services/journal/app/api/v1", "doc": "testcases-journal.md", "id": "JN"},
    "master-data": {"api": "services/master-data/app/api/v1", "doc": "testcases-master-data.md", "id": "MD"},
    "report": {"api": "services/report/app/api/v1", "doc": "testcases-report.md", "id": "RP"},
    "stock": {"api": "services/stock/app/api/v1", "doc": "testcases-stock.md", "id": "SK"},
    "terminal": {"api": "services/terminal/app/api/v1", "doc": "testcases-terminal.md", "id": "TM"},
}

# Icon constants
ICON_IMPLEMENTED = "![Implemented](https://img.shields.io/badge/Status-Implemented-green)"
ICON_MISSING = "![Missing](https://img.shields.io/badge/Status-Missing-red)"
ICON_MODIFIED = "![Modified](https://img.shields.io/badge/Status-Modified-orange)"

def extract_api_info(api_dir_rel):
    """Extracts API metadata from Python files in the given directory."""
    api_dir = os.path.join(PROJECT_ROOT, api_dir_rel)
    api_data = {}
    
    if not os.path.exists(api_dir):
        print(f"Warning: API directory not found: {api_dir}")
        return api_data

    for filename in os.listdir(api_dir):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue
        
        path = os.path.join(api_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Regex to find router methods and their docstrings
            pattern = re.compile(
                r'@router\.(?P<method>post|get|put|delete|patch)\(\s*"(?P<path>[^"]+)"' # Match decorator
                r'.*?async def (?P<func_name>\w+)\(.*?:\s*"""(?P<docstring>.*?)"""', # Match function and docstring
                re.DOTALL
            )
            
            for match in pattern.finditer(content):
                func_name = match.group('func_name')
                docstring_raw = match.group('docstring').strip()
                docstring = docstring_raw.split('\n')[0] if docstring_raw else ""
                api_data[func_name] = {
                    'method': match.group('method').upper(),
                    'path': match.group('path'),
                    'title': docstring or f"Test for {func_name}",
                    'file': filename
                }
        except Exception as e:
            print(f"Error reading {path}: {e}")
            
    return api_data

def sync_service_doc(service_name, config):
    """Syncs the extracted API info for a specific service."""
    doc_path = os.path.join(JA_TESTING_DIR, config['doc'])
    if not os.path.exists(doc_path):
        print(f"Warning: Doc not found for {service_name} at {doc_path}")
        return

    print(f"--- Synchronizing Service: {service_name} ---")
    api_metadata = extract_api_info(config['api'])
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    in_table = False
    table_updated = False
    existing_funcs = set()
    
    for line in lines:
        stripped = line.strip()
        
        # Table Header Detection
        if stripped.startswith('|') and 'ID' in stripped and ('匹配规则' in stripped or 'Mapping Rules' in stripped):
            in_table = True
            new_lines.append(line)
            continue
            
        if in_table and stripped.startswith('|') and ('|:---|' in stripped or '|----|' in stripped):
            new_lines.append(line)
            continue

        if in_table and stripped.startswith('|'):
            # Data Row Processing
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 6:
                # Column 5 or last column is usually the Mapping Rule
                mapping_rule = parts[5] if len(parts) > 5 else parts[-1]
                func_match = re.search(r'`(\w+)`', mapping_rule)
                
                if func_match:
                    func_name = func_match.group(1)
                    existing_funcs.add(func_name)
                    
                    if func_name in api_metadata:
                        code_info = api_metadata[func_name]
                        # Change Detection: Title (Column 2) or Target API (Column 3)
                        current_title = parts[2].replace('**', '') if len(parts) > 2 else ""
                        
                        # Check for modifications
                        is_modified = False
                        if current_title and current_title != code_info['title']:
                            print(f"  [MOD] Detected title change for {func_name}")
                            parts[2] = f"**{code_info['title']}**"
                            is_modified = True
                        
                        # Sync Target API (Column 3)
                        if len(parts) > 3:
                            current_api_info = parts[3].replace('`', '')
                            new_api_info = f"API / {code_info['method']}"
                            if current_api_info != new_api_info and ("API /" in current_api_info or current_api_info == ""):
                                print(f"  [MOD] Detected method change for {func_name}")
                                parts[3] = f"`{new_api_info}`"
                                is_modified = True
                        
                        if is_modified:
                            # Update status to MODIFIED if it was Implementation/Missing
                            # But only if it's not already Implemented
                            if ICON_IMPLEMENTED not in parts[4]:
                                parts[4] = f" {ICON_MODIFIED} "
                            
                            # Add alert to notes (Column 6+)
                            if len(parts) > 6:
                                parts[6] = f"⚠️ 代码接口已变更：{parts[6]}"
                            else:
                                parts.append("⚠️ 代码接口已变更")
                                
                            line = "|".join(parts).strip() + " |\n"
                            table_updated = True
            
            new_lines.append(line)
            continue
            
        if in_table and not stripped.startswith('|'):
            # Append missing APIs to the end of the current table block
            for func, info in api_metadata.items():
                if func not in existing_funcs:
                    print(f"  [NEW] Found missing API: {func}")
                    short_id = func[:3].upper()
                    new_row = f"| **{config['id']}-A-{short_id}** | **{info['title']}** | `API / {info['method']}` | {ICON_MISSING} | `{func}` | 系统自动追加的代码接口测试 |\n"
                    new_lines.append(new_row)
                    existing_funcs.add(func)
                    table_updated = True
            
            in_table = False
            new_lines.append(line)
            continue
            
        new_lines.append(line)

    if table_updated:
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  -> {config['doc']} updated.")
    else:
        print(f"  -> No changes needed for {service_name}.")

def main():
    print("Starting Universal Test Case Synchronization...")
    for service, config in SERVICES_CONFIG.items():
        try:
            sync_service_doc(service, config)
        except Exception as e:
            print(f"Critical error syncing {service}: {e}")
    print("\nAll services synchronization process completed.")

if __name__ == "__main__":
    main()

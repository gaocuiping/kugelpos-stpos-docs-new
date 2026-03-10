import os
import re

base = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs"

def fix_table_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace em-dashes with simple hyphens in table separators
    # Example broken line: |---|---|---|
    # Except they might look like |—|—|—|
    
    lines = content.split('\n')
    new_lines = []
    modified = False
    
    for line in lines:
        if line.strip().startswith('|') and line.strip().endswith('|') and '—' in line:
            # Check if it's a separator line containing only pipes, spaces, dashes
            clean_line = line.replace('|', '').replace(' ', '').replace('—', '').replace('-', '').replace(':', '')
            if len(clean_line) == 0:
                line = line.replace('—', '-')
                modified = True
        new_lines.append(line)
        
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    return False

fixed_count = 0
for lang in ['ja', 'en']:
    test_dir = os.path.join(base, lang, 'testing')
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            if file.endswith('.md'):
                if fix_table_markdown(os.path.join(test_dir, file)):
                    fixed_count += 1

print(f"Fixed table syntax in {fixed_count} files.")

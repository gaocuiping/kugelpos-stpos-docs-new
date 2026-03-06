import os
from html.parser import HTMLParser

base = '/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs/_site'
broken = []
checked = 0

class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, val in attrs:
                if name == 'href' and val:
                    self.links.append(val)

for root, dirs, files in os.walk(base):
    for fname in files:
        if not fname.endswith('.html'):
            continue
        fpath = os.path.join(root, fname)
        rel_page = os.path.relpath(fpath, base)
        with open(fpath, 'r', errors='ignore') as f:
            content = f.read()
        parser = LinkExtractor()
        parser.feed(content)
        for href in parser.links:
            if href.startswith(('http://', 'https://', '#', 'mailto:', 'javascript:')):
                continue
            page_dir = os.path.dirname(fpath)
            if href.startswith('/'):
                target = href.replace('/kugelpos-stpos-docs-new/', '')
                target_path = os.path.join(base, target)
            else:
                target_path = os.path.normpath(os.path.join(page_dir, href.split('#')[0]))
            exists = (os.path.isfile(target_path) or
                     (os.path.isdir(target_path) and os.path.isfile(os.path.join(target_path, 'index.html'))) or
                     os.path.isfile(target_path + '.html'))
            checked += 1
            if not exists:
                broken.append((rel_page, href))

print(f'Checked {checked} links')
print(f'Broken: {len(broken)}')
seen = set()
for page, href in broken:
    if (page, href) not in seen:
        seen.add((page, href))
        print(f'  [{page}] -> {href}')
if not broken:
    print('All links OK! OK')

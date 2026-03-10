import os

source_file = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs/ja/testing/test_comprehensive_review_ja_20260305.md"
target_file = "/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs/ja/testing/test-review.md"

with open(source_file, "r", encoding="utf-8") as f:
    content = f.read()

frontmatter = """---
title: "テスト評審"
parent: テスト
grand_parent: 日本語
nav_order: 1
layout: default
---

"""

with open(target_file, "w", encoding="utf-8") as f:
    f.write(frontmatter + content)
print("Updated test-review.md successfully.")

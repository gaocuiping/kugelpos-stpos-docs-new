#!/bin/bash
# Script to add Jekyll front matter to all documentation files
# This script adds navigation metadata to existing markdown files

DOCS_DIR="/home/gaocuiping/myself/kugelpos-stpos-docs-new/docs"

add_front_matter() {
    local file="$1"
    local title="$2"
    local parent="$3"
    local grand_parent="$4"
    local nav_order="$5"
    local has_children="${6:-false}"
    local permalink="$7"

    # Check if file already has front matter
    if head -1 "$file" | grep -q "^---"; then
        echo "  SKIP (already has front matter): $file"
        return
    fi

    local tmp_file
    tmp_file=$(mktemp)
    
    echo "---" > "$tmp_file"
    echo "title: \"$title\"" >> "$tmp_file"
    if [ -n "$parent" ]; then
        echo "parent: $parent" >> "$tmp_file"
    fi
    if [ -n "$grand_parent" ]; then
        echo "grand_parent: $grand_parent" >> "$tmp_file"
    fi
    echo "nav_order: $nav_order" >> "$tmp_file"
    if [ "$has_children" = "true" ]; then
        echo "has_children: true" >> "$tmp_file"
    fi
    if [ -n "$permalink" ]; then
        echo "permalink: $permalink" >> "$tmp_file"
    fi
    echo "---" >> "$tmp_file"
    echo "" >> "$tmp_file"
    
    cat "$file" >> "$tmp_file"
    mv "$tmp_file" "$file"
    echo "  DONE: $file"
}

# Create index pages for en and ja sections
create_section_index() {
    local lang="$1"
    local lang_label="$2"
    local nav_order="$3"

    local index_file="$DOCS_DIR/$lang/index.md"
    
    cat > "$index_file" << EOF
---
title: "$lang_label"
nav_order: $nav_order
has_children: true
permalink: /$lang/
---

# $lang_label
EOF
    echo "  CREATED: $index_file"
}

# Create service parent index pages
create_service_index() {
    local lang="$1"
    local service="$2"
    local title="$3"
    local grand_parent="$4"
    local nav_order="$5"
    
    local index_file="$DOCS_DIR/$lang/$service/index.md"
    
    cat > "$index_file" << EOF
---
title: "$title"
parent: $grand_parent
nav_order: $nav_order
has_children: true
---

# $title
EOF
    echo "  CREATED: $index_file"
}

echo "=== Creating section index pages ==="
create_section_index "en" "English" 2
create_section_index "ja" "日本語" 3

echo ""
echo "=== Creating service index pages (English) ==="
create_service_index "en" "general"     "General"     "English" 1
create_service_index "en" "account"     "Account"     "English" 2
create_service_index "en" "terminal"    "Terminal"    "English" 3
create_service_index "en" "master-data" "Master Data" "English" 4
create_service_index "en" "cart"        "Cart"        "English" 5
create_service_index "en" "report"      "Report"      "English" 6
create_service_index "en" "journal"     "Journal"     "English" 7
create_service_index "en" "stock"       "Stock"       "English" 8
create_service_index "en" "commons"     "Commons"     "English" 9

echo ""
echo "=== Creating service index pages (Japanese) ==="
create_service_index "ja" "general"     "共通"         "日本語" 1
create_service_index "ja" "account"     "アカウント"    "日本語" 2
create_service_index "ja" "terminal"    "ターミナル"    "日本語" 3
create_service_index "ja" "master-data" "マスターデータ" "日本語" 4
create_service_index "ja" "cart"        "カート"        "日本語" 5
create_service_index "ja" "report"      "レポート"      "日本語" 6
create_service_index "ja" "journal"     "ジャーナル"    "日本語" 7
create_service_index "ja" "stock"       "在庫"          "日本語" 8
create_service_index "ja" "commons"     "共通ライブラリ" "日本語" 9

echo ""
echo "=== Adding front matter to English docs ==="

# English README
add_front_matter "$DOCS_DIR/en/README.md" \
    "Overview" "English" "" 1 "false" ""

# English General
add_front_matter "$DOCS_DIR/en/general/architecture.md" \
    "Architecture" "General" "English" 1
add_front_matter "$DOCS_DIR/en/general/design_patterns.md" \
    "Design Patterns" "General" "English" 2
add_front_matter "$DOCS_DIR/en/general/error_code_spec.md" \
    "Error Code Specification" "General" "English" 3
add_front_matter "$DOCS_DIR/en/general/configuration-priority.md" \
    "Configuration Priority" "General" "English" 4
add_front_matter "$DOCS_DIR/en/general/dapr_components.md" \
    "Dapr Components" "General" "English" 5
add_front_matter "$DOCS_DIR/en/general/http_communication.md" \
    "HTTP Communication" "General" "English" 6

# English Service Docs
for service in account terminal cart report journal; do
    title_case=$(echo "$service" | sed 's/\b\(.\)/\u\1/g')
    add_front_matter "$DOCS_DIR/en/$service/api-specification.md" \
        "API Specification" "$title_case" "English" 1
    add_front_matter "$DOCS_DIR/en/$service/model-specification.md" \
        "Model Specification" "$title_case" "English" 2
done

# master-data special case
add_front_matter "$DOCS_DIR/en/master-data/api-specification.md" \
    "API Specification" "Master Data" "English" 1
add_front_matter "$DOCS_DIR/en/master-data/model-specification.md" \
    "Model Specification" "Master Data" "English" 2

# stock service
add_front_matter "$DOCS_DIR/en/stock/api-specification.md" \
    "API Specification" "Stock" "English" 1
add_front_matter "$DOCS_DIR/en/stock/model-specification.md" \
    "Model Specification" "Stock" "English" 2
add_front_matter "$DOCS_DIR/en/stock/snapshot-specification.md" \
    "Snapshot Specification" "Stock" "English" 3
add_front_matter "$DOCS_DIR/en/stock/websocket-specification.md" \
    "WebSocket Specification" "Stock" "English" 4

# English Commons
add_front_matter "$DOCS_DIR/en/commons/common-function-spec.md" \
    "Common Functions" "Commons" "English" 1

echo ""
echo "=== Adding front matter to Japanese docs ==="

# Japanese README
add_front_matter "$DOCS_DIR/ja/README.md" \
    "概要" "日本語" "" 1 "false" ""

# Japanese General
add_front_matter "$DOCS_DIR/ja/general/architecture.md" \
    "アーキテクチャ" "共通" "日本語" 1
add_front_matter "$DOCS_DIR/ja/general/design_patterns.md" \
    "設計パターン" "共通" "日本語" 2
add_front_matter "$DOCS_DIR/ja/general/error_code_spec.md" \
    "エラーコード仕様" "共通" "日本語" 3
add_front_matter "$DOCS_DIR/ja/general/configuration-priority.md" \
    "設定優先度" "共通" "日本語" 4
add_front_matter "$DOCS_DIR/ja/general/dapr_components.md" \
    "Dapr コンポーネント" "共通" "日本語" 5
add_front_matter "$DOCS_DIR/ja/general/http_communication.md" \
    "HTTP 通信" "共通" "日本語" 6

# Japanese Service Docs
declare -A ja_names
ja_names=(
    [account]="アカウント"
    [terminal]="ターミナル"
    [cart]="カート"
    [report]="レポート"
    [journal]="ジャーナル"
)

for service in account terminal cart report journal; do
    parent="${ja_names[$service]}"
    add_front_matter "$DOCS_DIR/ja/$service/api-specification.md" \
        "API 仕様" "$parent" "日本語" 1
    add_front_matter "$DOCS_DIR/ja/$service/model-specification.md" \
        "モデル仕様" "$parent" "日本語" 2
done

# master-data special case
add_front_matter "$DOCS_DIR/ja/master-data/api-specification.md" \
    "API 仕様" "マスターデータ" "日本語" 1
add_front_matter "$DOCS_DIR/ja/master-data/model-specification.md" \
    "モデル仕様" "マスターデータ" "日本語" 2

# stock service
add_front_matter "$DOCS_DIR/ja/stock/api-specification.md" \
    "API 仕様" "在庫" "日本語" 1
add_front_matter "$DOCS_DIR/ja/stock/model-specification.md" \
    "モデル仕様" "在庫" "日本語" 2
add_front_matter "$DOCS_DIR/ja/stock/snapshot-specification.md" \
    "スナップショット仕様" "在庫" "日本語" 3
add_front_matter "$DOCS_DIR/ja/stock/websocket-specification.md" \
    "WebSocket 仕様" "在庫" "日本語" 4

# Japanese Commons
add_front_matter "$DOCS_DIR/ja/commons/common-function-spec.md" \
    "共通関数" "共通ライブラリ" "日本語" 1

echo ""
echo "=== Front matter addition complete ==="

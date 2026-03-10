#!/bin/bash
# =============================================================================
# generate_docs.sh - Auto-generate API specification documents from source code
# =============================================================================
# This script scans FastAPI service source code and generates/updates
# API specification documents in the docs/ directory.
#
# Usage:
#   ./scripts/generate_docs.sh              # Generate docs for all services
#   ./scripts/generate_docs.sh account      # Generate docs for specific service
#   ./scripts/generate_docs.sh --check      # Check if docs are up to date
# =============================================================================

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SERVICES_DIR="$PROJECT_ROOT/services"
DOCS_DIR="$PROJECT_ROOT/docs"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Service definitions: service_name|port|en_parent|ja_parent
SERVICES=(
    "account|8000|Account|アカウント"
    "terminal|8001|Terminal|ターミナル"
    "master-data|8002|Master Data|マスターデータ"
    "cart|8003|Cart|カート"
    "report|8004|Report|レポート"
    "journal|8005|Journal|ジャーナル"
    "stock|8006|Stock|在庫"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# =============================================================================
# Extract API endpoints from FastAPI router files
# =============================================================================
extract_endpoints() {
    local service_dir="$1"
    local api_dir="$service_dir/app/api"
    
    if [ ! -d "$api_dir" ]; then
        log_warn "API directory not found: $api_dir"
        return
    fi

    # Find all Python files in api directory
    find "$api_dir" -name "*.py" -not -name "__init__.py" -not -name "schemas.py" | sort | while read -r file; do
        local rel_path="${file#$service_dir/}"
        
        # Extract route decorators and function signatures (ignoring commented out lines)
        grep -n '^[[:space:]]*@router\.\|^[[:space:]]*@app\.' "$file" 2>/dev/null || true | while read -r line; do
            local line_num=$(echo "$line" | cut -d: -f1)
            local content=$(echo "$line" | cut -d: -f2-)
            
            # Extract HTTP method and path
            local method=$(echo "$content" | grep -oP '(get|post|put|delete|patch)' | head -1 | tr '[:lower:]' '[:upper:]')
            local path=$(echo "$content" | grep -oP '"[^"]*"' | head -1 | tr -d '"')
            
            if [ -n "$method" ] && [ -n "$path" ]; then
                # Get the function name from the next few lines
                local func_name=$(sed -n "$((line_num+1)),$((line_num+5))p" "$file" | grep -oP 'async def \K\w+|def \K\w+' | head -1)
                echo "ENDPOINT|$method|$path|$func_name|$rel_path:$line_num"
            fi
        done
    done
}

# =============================================================================
# Extract data models from schema files
# =============================================================================
extract_models() {
    local service_dir="$1"
    
    # Find schema files
    find "$service_dir/app" -name "schemas.py" -o -name "models.py" 2>/dev/null | sort | while read -r file; do
        local rel_path="${file#$service_dir/}"
        
        # Extract class definitions (Pydantic models)
        grep -n 'class \w\+' "$file" 2>/dev/null || true | while read -r line; do
            local line_num=$(echo "$line" | cut -d: -f1)
            local class_name=$(echo "$line" | grep -oP 'class \K\w+')
            local parent_class=$(echo "$line" | grep -oP '\(\K[^)]+' | head -1)
            
            if [ -n "$class_name" ]; then
                echo "MODEL|$class_name|$parent_class|$rel_path:$line_num"
            fi
        done
    done
}

# =============================================================================
# Extract environment variables / settings
# =============================================================================
extract_settings() {
    local service_dir="$1"
    local settings_file="$service_dir/app/config/settings.py"
    
    if [ ! -f "$settings_file" ]; then
        return
    fi
    
    grep -n '^\w\+\s*=' "$settings_file" 2>/dev/null || true | while read -r line; do
        local var_name=$(echo "$line" | cut -d: -f2- | grep -oP '^\w+')
        local value=$(echo "$line" | cut -d= -f2- | sed 's/^ *//')
        echo "SETTING|$var_name|$value"
    done
}

# =============================================================================
# Generate API overview document for a service
# =============================================================================
generate_api_overview() {
    local service_name="$1"
    local port="$2"
    local en_parent="$3"
    local ja_parent="$4"
    local service_dir="$SERVICES_DIR/$service_name"
    
    if [ ! -d "$service_dir" ]; then
        log_warn "Service directory not found: $service_dir"
        return
    fi

    log_info "Scanning service: $service_name (port: $port)"

    # --- Generate English version ---
    local en_file="$DOCS_DIR/en/$service_name/api-overview-generated.md"
    mkdir -p "$(dirname "$en_file")"

    cat > "$en_file" << EOF
---
title: "API Overview (Auto-generated)"
parent: $en_parent
grand_parent: English
nav_exclude: true
---

# $en_parent Service - API Overview

> **Auto-generated** from source code on $TIMESTAMP
> 
> This document is automatically generated. Do not edit manually.

## Service Information

| Property | Value |
|----------|-------|
| **Port** | $port |
| **Base URL** | \`http://localhost:$port\` |
| **API Docs** | \`http://localhost:$port/docs\` |

## Endpoints

| Method | Path | Function | Source |
|--------|------|----------|--------|
EOF

    # Extract and write endpoints
    extract_endpoints "$service_dir" | while IFS='|' read -r type method path func source; do
        if [ "$type" = "ENDPOINT" ]; then
            echo "| \`$method\` | \`$path\` | \`$func\` | \`$source\` |" >> "$en_file"
        fi
    done

    cat >> "$en_file" << EOF

## Data Models

| Model | Parent Class | Source |
|-------|-------------|--------|
EOF

    extract_models "$service_dir" | while IFS='|' read -r type class_name parent source; do
        if [ "$type" = "MODEL" ]; then
            echo "| \`$class_name\` | \`$parent\` | \`$source\` |" >> "$en_file"
        fi
    done

    # Environment variables section
    local settings=$(extract_settings "$service_dir")
    if [ -n "$settings" ]; then
        cat >> "$en_file" << EOF

## Environment Variables

| Variable | Default Value |
|----------|---------------|
EOF
        echo "$settings" | while IFS='|' read -r type var value; do
            if [ "$type" = "SETTING" ]; then
                echo "| \`$var\` | \`$value\` |" >> "$en_file"
            fi
        done
    fi

    log_success "Generated: $en_file"

    # --- Generate Japanese version ---
    local ja_file="$DOCS_DIR/ja/$service_name/api-overview-generated.md"
    mkdir -p "$(dirname "$ja_file")"

    cat > "$ja_file" << EOF
---
title: "API 概要 (自動生成)"
parent: $ja_parent
grand_parent: 日本語
nav_exclude: true
---

# ${ja_parent}サービス - API 概要

> **自動生成**: ソースコードから $TIMESTAMP に生成
>
> このドキュメントは自動生成されています。手動で編集しないでください。

## サービス情報

| 項目 | 値 |
|------|-----|
| **ポート** | $port |
| **ベースURL** | \`http://localhost:$port\` |
| **APIドキュメント** | \`http://localhost:$port/docs\` |

## エンドポイント一覧

| メソッド | パス | 関数 | ソース |
|----------|------|------|--------|
EOF

    extract_endpoints "$service_dir" | while IFS='|' read -r type method path func source; do
        if [ "$type" = "ENDPOINT" ]; then
            echo "| \`$method\` | \`$path\` | \`$func\` | \`$source\` |" >> "$ja_file"
        fi
    done

    cat >> "$ja_file" << EOF

## データモデル

| モデル | 親クラス | ソース |
|--------|---------|--------|
EOF

    extract_models "$service_dir" | while IFS='|' read -r type class_name parent source; do
        if [ "$type" = "MODEL" ]; then
            echo "| \`$class_name\` | \`$parent\` | \`$source\` |" >> "$ja_file"
        fi
    done

    if [ -n "$settings" ]; then
        cat >> "$ja_file" << EOF

## 環境変数

| 変数名 | デフォルト値 |
|--------|-------------|
EOF
        echo "$settings" | while IFS='|' read -r type var value; do
            if [ "$type" = "SETTING" ]; then
                echo "| \`$var\` | \`$value\` |" >> "$ja_file"
            fi
        done
    fi

    log_success "Generated: $ja_file"
}

# =============================================================================
# Main
# =============================================================================
main() {
    log_info "============================================"
    log_info "Kugelpos API Documentation Generator"
    log_info "============================================"
    log_info "Project root: $PROJECT_ROOT"
    log_info "Timestamp: $TIMESTAMP"
    echo ""

    local target_service="${1:-}"

    if [ "$target_service" = "--check" ]; then
        log_info "Running in check mode (not implemented yet)"
        exit 0
    fi

    for entry in "${SERVICES[@]}"; do
        IFS='|' read -r name port en_parent ja_parent <<< "$entry"
        
        if [ -n "$target_service" ] && [ "$target_service" != "$name" ]; then
            continue
        fi
        
        generate_api_overview "$name" "$port" "$en_parent" "$ja_parent"
        echo ""
    done

    log_success "============================================"
    log_success "Documentation generation complete!"
    log_success "============================================"
}

main "$@"

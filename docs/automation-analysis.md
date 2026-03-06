---
title: "自动化文档管理分析"
nav_order: 99
nav_exclude: true
---

# Jekyll + GitHub Pages 自动化文档管理方案分析

## 🟢 自动化式样资料作成・更新（ソースベース）

**现状：已实现基础框架，可以自动化。**

| 功能 | 实现状态 | 说明 |
|------|---------|------|
| 自动生成脚本 | ✅ 已实装 | `scripts/generate_docs.sh` 扫描 FastAPI 服务源代码 |
| 提取 API 端点 | ✅ 已实装 | 从 `@router.get/post/put/delete` 装饰器提取 |
| 提取数据模型 | ✅ 已实装 | 从 Pydantic schemas/models 提取类定义 |
| 提取环境变量 | ✅ 已实装 | 从 `settings.py` 提取配置项 |
| GitHub Actions 触发 | ✅ 已实装 | `generate-docs.yml` 监听 `services/**/app/api/**` 变更 |
| 自动 Commit 回仓库 | ✅ 已实装 | Bot 自动提交更新后的文档 |

**工作流程：**

```
开发者修改服务源代码 → push 到 main 分支
    → GitHub Actions 检测到 services/ 下文件变更
    → 自动运行 generate_docs.sh
    → 生成/更新 API 概要文档（en + ja）
    → 自动 commit 回仓库
```

**⚠️ 当前限制：**
- 脚本使用 `grep` + `sed` 解析 Python 源码，对于复杂的路由定义（如动态路由、嵌套路由）提取精度有限
- 如果需要更精确的提取，可以升级为使用 Python AST 解析器或直接调用 FastAPI 的 OpenAPI 生成功能

---

## 🟢 自动公开・更新

**现状：完全实现。**

| 功能 | 实现状态 | 说明 |
|------|---------|------|
| Jekyll 自动构建 | ✅ 已实装 | `jekyll-gh-pages.yml` 监听 `docs/` 变更 |
| GitHub Pages 部署 | ✅ 已实装 | 使用 `actions/deploy-pages@v4` 自动部署 |
| 路径触发 | ✅ 已实装 | 仅 `docs/**` 变更时触发（避免不必要的构建）|
| 手动触发 | ✅ 已实装 | 支持 `workflow_dispatch` 手动触发部署 |
| 并发控制 | ✅ 已实装 | 同一时间只允许一个部署任务 |

**工作流程：**

```
docs/ 下文件变更 → push 到 main 分支
    → GitHub Actions 自动触发 Jekyll 构建
    → 构建成功后自动部署到 GitHub Pages
    → 网站自动更新（通常 1-2 分钟内完成）
```

---

## 🔄 完整的端到端自动化流程

```
┌─────────────────────────────────────────────────────────┐
│ 开发者修改 services/ 下的 API 源代码                       │
│                    ↓ push to main                       │
│ generate-docs.yml 触发                                   │
│   → generate_docs.sh 扫描源代码                           │
│   → 自动生成/更新 docs/ 下的 API 概要文档                   │
│   → 自动 commit 更新                                     │
│                    ↓ docs/ 变更被检测到                    │
│ jekyll-gh-pages.yml 触发                                 │
│   → Jekyll 构建整个文档网站                                │
│   → 自动部署到 GitHub Pages                               │
│                    ↓                                     │
│ 文档网站自动更新完成 ✅                                     │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 部署前需要做的事

1. **Push 到 GitHub** — `git push origin main`
2. **启用 GitHub Pages** — Repository Settings → Pages → Source 选择 **"GitHub Actions"**
3. **确认 Actions 权限** — Settings → Actions → General → 确认 Workflow permissions 为 **"Read and write permissions"**

完成后，每次修改源代码或文档，网站都会自动更新。

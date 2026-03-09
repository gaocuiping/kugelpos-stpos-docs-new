---
title: "文档管理与自动化"
layout: default
nav_order: 5
---

# 文档管理 — Jekyll + GitHub Pages 自动化体系

本项目的文档中心（本站）采用了 **"Docs-as-Code"（文档即代码）** 的深度集成方案。通过 Jekyll 静态站点生成器与 GitHub Actions 自动化脚本，实现了技术文档与业务代码的实时同步。

---

## 🏗️ 技术架构综述

| 维度 | 技术栈 / 配置 | 说明 |
| :--- | :--- | :--- |
| **内核** | [Jekyll](https://jekyllrb.com/) | 将 Markdown 原生转换为高性能 HTML 站点。 |
| **托管** | [GitHub Pages](https://pages.github.com/) | 无需服务器，直接通过 GitHub Actions 构建并发布。 |
| **主题** | `just-the-docs` | 现代化的文档 UI，内置搜索、多层级侧边栏及多语言支持。 |
| **视觉定制** | [custom.scss](_sass/custom/custom.scss) | 采用 **Sky-Breeze 渐变系统**（天蓝至薄荷绿），结合毛玻璃效果。 |

---

## ⚡ 核心自动化机制

为了极大地减轻维护负担，系统内置了两大自动化同步引擎：

### 1. API 接口文档自动生成 (`generate_docs.sh`)
系统会自动扫描 `services/` 目录下各微服务的 FastAPI 路由代码（`app/api/`）和数据模型（`schemas.py`）。
- **触发逻辑**：每当检测到路由装饰器（如 `@router.get`）或 Pydantic 类定义时，脚本会自动提取路径、方法、函数名及源码位置。
- **输出结果**：自动在 `docs/ja/<service>/` 目录下生成 `api-overview-generated.md`，确保接口文档永远与代码保持一致。

### 2. 测试用例双向同步与自动发现 (`sync_testcase_definitions.py`)
这是系统最智能的部分，它不仅能同步状态，还能**感知代码结构的变化**：
- **自动追加 (Auto-Discovery)**：当您在 `services/cart/app/api/` 中新增一个 API 接口（如 `@router.post`）时，运行脚本会自动将该接口作为新的测试用例追加到文档中。
- **改动感知 (Modification Detection)**：如果您修改了代码里的 Docstring（接口说明）或变更了 HTTP 方法，脚本会自动识别冲突并更新 Markdown 表格中的“测试标题”和“测试对象”。
- **规则导向**：脚本以代码中的**函数名**作为唯一标识符与文档中的“匹配规则”进行绑定。

---

## 🔄 自动化流水线 (CI/CD)

项目配置了三个关键的 GitHub Workflows 来驱动整个体系：

1. **`generate-docs.yml`**：负责运行 API 扫描脚本，并将更新后的 Markdown 自动 commit 回仓库。
2. **`sync-test-docs.yml`**：在代码提交后扫描测试实现情况，自动更新测试用例表格的图标状态。
3. **`jekyll-gh-pages.yml`**：最终的构建流水线，负责将所有 Markdown 文件（包括自动生成的）编译为 HTML 并发布到在线环境。

---

## ⚠️ 开发者操作指南

### 如何同步您的测试进度？
要让文档中的某项测试显示为 ✅ `Implemented`，您**不需要**修改 Markdown。只需确保您的 Python 测试代码中包含 Mapping Rules 中定义的特征。

**示例**：
- 如果 Markdown 里的 Mapping Rule 是 `test_cart_operations`。
- **做法 A**：将测试函数命名为 `def test_cart_operations(): ...`。
- **做法 B**：在函数内添加一行注释 `# test_cart_operations`。

### 样式定制说明
文档样式由 [custom.scss](_sass/custom/custom.scss) 统一控制。
- **变宽控制**：系统已通过 CSS 强制将“业务步骤”等长文本列设为 **450px**，您在编写表格时无需再手动添加任何 HTML `<div>` 标签。
- **背景优化**：采用了高亮的渐变设计，禁止使用暗色背景以保持清爽。

---

## 📦 开启新项目的步骤
如果您需要将这套文档基盘移植到新项目，请确保带上以下核心文件：
1. `docs/` 目录及其结构。
2. `scripts/` 下的所有自动同步脚本。
3. `.github/workflows/` 下的 yml 定义。
4. 根目录的 `Gemfile` 和 `_config.yml`。

> [!IMPORTANT]
> 移植后请务必在 GitHub 仓库设置中，将 **Pages** 的 Source 设置为 **GitHub Actions**。

---
*上次更新于：{{ "now" | date: "%Y-%m-%d" }}*

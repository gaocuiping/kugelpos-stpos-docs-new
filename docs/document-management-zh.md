---
title: "文档管理与自动化"
layout: default
nav_order: 4
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

## ⚡ 核心自动化机制（三大引擎）

为了极大地减轻维护负担，系统内置了三大自动化同步引擎：

### 1. API 接口文档自动生成 (`generate_docs.sh`)
系统会自动扫描 `services/` 目录下各微服务的 FastAPI 路由代码（`app/api/`）和数据模型（`schemas.py`）。
- **触发逻辑**：每当检测到路由装饰器（如 `@router.get`）或 Pydantic 类定义时，脚本会自动提取路径、方法、函数名及源码位置。
- **输出结果**：自动在 `docs/ja/<service>/` 目录下生成 `api-overview-generated.md`，确保接口文档永远与代码保持一致。

### 2. 测试用例文档双向同步 (`sync_testcase_definitions.py` / `sync_testcases.py`)
这是系统最智能的部分，它不仅能同步状态，还能**感知代码结构的变化**：
- **自动追加 (Auto-Discovery)**：当您在 `services/*/app/api/` 中新增一个 API 接口时，脚本会自动将该接口追加到 `docs/ja/testing/testcases-*.md` 文档表格中。
- **改动感知 (Modification Detection)**：如果您修改了代码里的 Docstring 或 HTTP 方法，脚本会自动识别冲突并更新 Markdown 中的标题和对象列。
- **质量门控 (Quality Gate)**：`sync_testcases.py` 会检查测试函数体内是否含有 `pytest.skip()`。只有**真正实现**的测试（无 skip）才会从 ❌ `Missing` 变为 ✅ `Implemented`，空骨架不会计入已完成。

### 3. 🆕 测试骨架自动追加 (`auto_append_tests.py`)
当 API 代码发生变更时，自动为所有**未覆盖的新接口**生成 Python 测试骨架文件，直接对应 `test-review.md` 的改善方案：

| 生成文件 | 目标目录 | 对应改善优先级 |
| :--- | :--- | :--- |
| `test_<func>_scenario_auto.py` | `tests/scenario/` | **P1**：场景测试 + 4xx/5xx 异常系 |
| `test_<func>_unit_auto.py` | `tests/unit/` | **P0**：Service 层 AsyncMock 单体测试 |

**覆盖检测（三级匹配）**：
1. 已有 `# AUTO-GENERATED: func_name=xxx` 标记 → 跳过
2. 已有 `def test_<func_name>` 函数 → 跳过
3. 已有调用该接口的 URL 路径的 HTTP 请求 → 跳过

生成文件中统一使用 `pytest.skip()` 占位，不影响现有 CI——等开发者实现后，文档会自动变绿。

```bash
# 手动运行（全服务）
python3 scripts/auto_append_tests.py --all

# 仅针对某个服务
python3 scripts/auto_append_tests.py --service terminal
```

---

## 🔄 自动化流水线 (CI/CD)

项目配置了四个关键的 GitHub Workflows 来驱动整个体系：

| Workflow 文件 | 触发条件 | 功能 |
| :--- | :--- | :--- |
| `generate-docs.yml` | API 路由代码变更 | 扫描 FastAPI 路由，生成 API 概览文档并自动 commit |
| **`auto-append-tests.yml`** | `services/*/app/api/**/*.py` 变更 | 🆕 自动检测变更服务，生成测试骨架并 commit 到 `tests/unit/` + `tests/scenario/` |
| `sync-test-docs.yml` | `services/**/tests/**/*.py` 变更 | 扫描测试实现情况，自动更新 testcases-*.md 的图标状态（仅无 skip 的函数才变绿）|
| `jekyll-gh-pages.yml` | 上述任一 commit | 将所有 Markdown 编译为 HTML 并发布到 GitHub Pages |

### 完整自动化流程

```
开发者修改/新增 API 路由代码 (services/*/app/api/**/*.py)
  │
  ├─→ [generate-docs.yml]    → API 接口文档自动更新
  │
  └─→ [auto-append-tests.yml]
        │  检测变更的服务
        │  运行 auto_append_tests.py --service <svc>
        │  生成 tests/unit/*_unit_auto.py
        │       tests/scenario/*_scenario_auto.py
        └─→ git commit [skip ci] & push
              │
              └─→ [sync-test-docs.yml]   → testcases-*.md ❌ 保持 Missing
                    开发者实现测试（删除 pytest.skip）
                    push → testcases-*.md ✅ 变为 Implemented
                    └─→ [jekyll-gh-pages.yml] → 网站更新发布
```

---

## ⚠️ 开发者操作指南

### 如何同步您的测试进度？
要让文档中的某项测试显示为 ✅ `Implemented`，您**不需要**修改 Markdown。只需：

1. 找到 `tests/unit/` 或 `tests/scenario/` 里对应的 `_auto.py` 文件
2. 删除 `pytest.skip(...)` 那行
3. 编写真实的断言逻辑
4. push 到 `main` → 文档自动变绿

### 测试目录结构约定

```
services/<service>/tests/
├── conftest.py          ← 全局 fixture（http_client 等），对所有子目录生效
├── unit/                ← 单体测试（不依赖外部服务，使用 AsyncMock）
│   ├── test_*_unit_auto.py   ← 自动生成的 P0 骨架
│   ├── repositories/
│   └── utils/
└── scenario/            ← 场景/集成测试（通过 HTTP 调用真实或模拟服务）
    └── test_*_scenario_auto.py  ← 自动生成的 P1+P1-5 骨架
```

### 样式定制说明
文档样式由 [custom.scss](_sass/custom/custom.scss) 统一控制。
- **变宽控制**：系统已通过 CSS 强制将"业务步骤"等长文本列设为 **450px**，您在编写表格时无需再手动添加任何 HTML `<div>` 标签。
- **背景优化**：采用了高亮的渐变设计，禁止使用暗色背景以保持清爽。

---

## 📦 开启新项目的步骤
如果您需要将这套文档基盘移植到新项目，请确保带上以下核心文件：
1. `docs/` 目录及其结构。
2. `scripts/` 下的所有自动同步脚本（`auto_append_tests.py`、`sync_testcase_definitions.py`、`sync_testcases.py`）。
3. `.github/workflows/` 下的全部 yml 定义（含 `auto-append-tests.yml`）。
4. 根目录的 `Gemfile` 和 `_config.yml`。

> [!IMPORTANT]
> 移植后请务必在 GitHub 仓库设置中，将 **Pages** 的 Source 设置为 **GitHub Actions**。

---
*上次更新于：{{ "now" | date: "%Y-%m-%d" }}*

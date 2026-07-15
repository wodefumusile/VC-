# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

微信公众号AI智能运营系统 V2.2 — 从选题、AI写作、排版、配图、质量检测到一键发布草稿的完整流水线。提供 Web UI（FastAPI 内嵌 SPA）和 n8n 工作流两种运行模式。

## 常用命令

### 本地开发

```bash
# 安装依赖
pip install -r app/requirements.txt
playwright install chromium

# 启动服务（开发模式，热重载）
cd app && python -m backend.main

# 生产模式（设置环境变量 APP_ENV=production）
cd app && python -m backend.main
```

- 服务启动后访问 `http://localhost:8000`（Web UI），API 文档在 `/docs`
- 健康检查：`GET /health`
- 依赖：Python 3.12+、Chrome/Chromium

### Docker (n8n 工作流模式)

```bash
# 启动 n8n 容器
docker-compose up -d                # 基础版（主 docker-compose.yml）
docker-compose -f v4/docker-compose.v4.yml up -d  # V4 完整版（含 PostgreSQL）

# 导入工作流
docker exec n8n n8n import:workflow --input=/path/to/workflow.json
```

### Windows 用户

- 双击 `一键安装.bat` → 安装 Python 依赖 + Chromium
- 双击 `一键启动.bat` → 启动服务并打开浏览器
- 双击 `一键停止.bat` → 关闭服务

### 配置

- 配置文件：`app/.env`（从 `app/.env.example` 复制）
- 必须配置：`AI_API_KEY`（DeepSeek API Key）
- 可选配置：`IMAGE_API_KEY`（火山方舟，AI 生图）、`OBSIDIAN_PATH`（知识库路径）、`ADMIN_TOKEN`
- 所有配置通过 `backend.config.settings` 单例访问，支持热重载（`POST /api/v2/config`）

## 架构

```
app/
├── backend/                     # FastAPI 后端
│   ├── main.py                  # 应用入口，lifespan 管理 Playwright + 任务队列生命周期
│   ├── web_ui.py                # 内嵌 SPA (单文件 HTML，注入 ADMIN_TOKEN)
│   ├── config/settings.py        # 配置管理（.env → Settings 单例）
│   ├── database/models.py        # SQLite (articles, task_logs, article_images)
│   ├── api/
│   │   ├── article.py           # /api/article/* (AI生成、SEO、质检、链接分析)
│   │   ├── publish.py           # /api/publish/draft (提交到发布队列)
│   │   ├── tasks.py             # /api/tasks/* (一键流水线 + 任务状态查询)
│   │   └── v2/routes.py        # /api/v2/* (图片生成、排版、质检V2、知识库、配置管理)
│   └── services/
│       ├── ai/                   # AI 模型客户端 (OpenAI 兼容) + Prompt 管理 + 文章生成
│       ├── content_analyzer/     # 公众号/抖音链接解析 → 选题分析
│       ├── content_optimizer/    # SEO 优化、质量检测、合规检查
│       ├── content_formatter/    # V1 格式化器
│       ├── formatter_engine/     # V2 格式化引擎 (section+span 模板)
│       ├── image_agent/          # 图片规划 Agent（根据文章内容规划配图）
│       ├── image_provider/       # 图片生成 Provider（即梦/OpenAI 兼容）
│       ├── knowledge_engine/     # Obsidian 知识库检索（Jaccard 关键词匹配）
│       ├── quality_checker_v2.py # V2 质检（含图片检查）
│       ├── workflow_orchestrator.py    # V1 一键流水线
│       ├── workflow_v2_orchestrator.py # V2.1 流水线（含知识增强+配图）
│       └── task_queue.py         # 异步发布队列（串行化 Playwright 操作）
├── publish_engine/              # Playwright 浏览器自动化
│   ├── core/playwright_service.py # 单例浏览器服务（线程安全）
│   ├── browser/                  # 浏览器配置 + 管理器
│   ├── auth/                     # 微信扫码登录 + 会话检测/持久化
│   ├── pages/wechat_page.py     # 公众号后台页面导航
│   ├── wechat/                   # 文章编辑器 + 选择器 + Article 模型
│   └── services/draft_publisher.py # 草稿上传
└── templates/wechat/            # 排版模板 (technology/business/knowledge/personal)
```

### 两条流水线

1. **V1 一键任务** (`/api/tasks/create`): AI生成 → 格式化 → SEO → 质检 → 发布队列 → 微信草稿箱
2. **V2.1 全流程** (`/api/v2/pipeline/run`): 知识检索 → AI生成 → 图片规划 → AI生图 → V2格式化 → SEO+合规 → V2质检 → 发布队列

### 关键设计决策

- **Playwright 线程安全**：所有 Playwright Sync API 调用通过 `playwright_service.run_with_page()` 在单一线程内执行，通过 `PublishQueue`（asyncio.Queue）串行化
- **V1/V2 独立共存**：V2 pipeline 完全独立于 V1，各自的路由和编排器互不依赖
- **AI 客户端**：`ModelClient` 使用 OpenAI 兼容接口，默认指向 DeepSeek，可通过 `AI_BASE_URL` 切换
- **数据库**：SQLite WAL 模式，`articles` + `task_logs` + `article_images` 三表
- **模块开关**：`ENABLE_AI_GENERATE`、`ENABLE_KNOWLEDGE`、`ENABLE_IMAGE` 可独立控制，`IMAGE_API_KEY` 或 `OBSIDIAN_PATH` 为空时对应功能自动跳过
- **Web UI**：单文件 HTML 内嵌在 `web_ui.py`，使用原生 JS + Fetch API，模板语法 `{variable}` 在服务端注入 `ADMIN_TOKEN` 后替换
